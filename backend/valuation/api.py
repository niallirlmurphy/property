"""
FastAPI endpoints for property valuation.

Phase 1: POST /api/valuation/estimate
"""

import os
import re
import asyncpg
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from datetime import datetime
from typing import Optional

from .models import (
    ValuationRequest,
    ValuationResponse,
    ComparableProperty,
    ConfidenceInterval,
    ValuationStatistics,
    NearbyAmenity
)
from .geocoder import ValuationGeocoder, _normalize_address
from .comparable_search import ComparableSearcher
from .adjustments import (
    MVPAdjuster, property_bucket, property_type_from_address, trim_price_outliers,
)
from .calculator import ValuationCalculator
from .validator import MVPValidator
from .nearby_amenities import get_nearby_amenities


# Router
router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.get("/health")
async def valuation_health_check():
    """
    Health check for valuation service.

    Returns:
        dict: Service status and configuration info
    """
    import os
    pool = get_db_pool()

    return {
        "status": "ok",
        "service": "valuation",
        "database_connected": pool is not None,
        "config": {
            "has_mapbox_token": bool(os.getenv('MAPBOX_TOKEN')),
            "has_autoaddress_key": bool(os.getenv('AUTOADDRESS_KEY'))
        }
    }


# Database connection pool - imported from main
# Note: db_pool is initialized in main.py's lifespan context
db_pool = None

def get_db_pool():
    """Get database connection pool from main app."""
    # Import here to avoid circular dependency
    import sys
    if 'main' in sys.modules:
        from main import db_pool as main_db_pool
        return main_db_pool
    return db_pool


@router.post("/estimate", response_model=ValuationResponse)
async def estimate_property_value(
    request: ValuationRequest,
    background_tasks: BackgroundTasks
):
    """
    Estimate property value using comparable sales analysis.

    Algorithm (Phase 1 MVP):
    1. Geocode address → (lat, lon)
    2. Find comparable sales within adaptive radius (1-20km)
    3. Adjust comparable prices for time difference (county price indices)
    4. Calculate weighted average (distance + recency weights)
    5. Validate quality and assign confidence level

    Args:
        request: ValuationRequest with address, eircode, valuation_date

    Returns:
        ValuationResponse with estimate, confidence interval, comparables

    Raises:
        HTTPException 400: Invalid request (bad address, geocoding failed)
        HTTPException 404: No comparable sales found
        HTTPException 500: Internal error
    """

    start_time = datetime.now()

    # Log incoming request for debugging
    print(f"[Valuation] Request: address='{request.address}', eircode={request.eircode}, county={request.county}, bedrooms={request.bedrooms}, ber={request.ber_rating}")

    # Get database pool
    pool = get_db_pool()

    if not pool:
        print("[Valuation] ERROR: Database pool is None!")
        raise HTTPException(
            status_code=500,
            detail="Database connection not available. Please try again later."
        )

    # Initialize subject attributes (bedrooms/type determined after geocoding)
    subject_bedrooms = request.bedrooms
    subject_property_type = request.property_type

    try:
        # Step 1: Geocode address
        geocoder = ValuationGeocoder(pool)

        try:
            print(f"[Valuation] Geocoding address: '{request.address}', county: {request.county or 'Dublin (default)'}")
            location = await geocoder.geocode_address(
                address=request.address,
                eircode=request.eircode,
                county=request.county
            )
            print(f"[Valuation] Geocoded: lat={location.latitude}, lon={location.longitude}, method={location.method}, confidence={location.confidence}")

            # Determine subject property bedroom count
            # Priority: user input > database match
            if subject_bedrooms is None and hasattr(location, 'bedrooms'):
                subject_bedrooms = location.bedrooms
                if subject_bedrooms is not None:
                    print(f"[Valuation] Using bedrooms from database: {subject_bedrooms}")
            elif subject_bedrooms is not None:
                print(f"[Valuation] Using bedrooms from user input: {subject_bedrooms}")

            # Determine subject property type (apartment vs house).
            # Priority: user input > database match. Used to weight comparables
            # of the same type far more heavily (separate markets).
            if subject_property_type is None and hasattr(location, 'property_type'):
                subject_property_type = location.property_type
                if subject_property_type is not None:
                    print(f"[Valuation] Using property_type from database: {subject_property_type}")
            elif subject_property_type is not None:
                print(f"[Valuation] Using property_type from user input: {subject_property_type}")
            # Last resort: the address itself ("Apartment 21, The Oak, ..."). A
            # development-level match has no single stored type, and without one
            # the bedroom ladder is skipped.
            if subject_property_type is None:
                subject_property_type = property_type_from_address(request.address)
                if subject_property_type is not None:
                    print(f"[Valuation] Using property_type from address: {subject_property_type}")
        except ValueError as e:
            print(f"[Valuation] Geocoding failed: {str(e)}")
            # Log geocoding failures to Sentry
            try:
                import sentry_sdk
                sentry_sdk.set_context("geocoding_failure", {
                    "address": request.address,
                    "eircode": request.eircode,
                    "error": str(e)
                })
                sentry_sdk.set_tag("error_type", "geocoding_failed")
                sentry_sdk.capture_message(f"Geocoding failed: {str(e)}", level="warning")
            except ImportError:
                pass

            raise HTTPException(
                status_code=400,
                detail=f"Could not geocode address: {str(e)}"
            )

        # Step 2: Find comparable sales
        searcher = ComparableSearcher(pool)

        try:
            print(f"[Valuation] Searching for comparables at ({location.latitude}, {location.longitude})")
            comparables = await searcher.find_comparables(
                latitude=location.latitude,
                longitude=location.longitude,
                min_count=5,
                max_count=30
            )
            print(f"[Valuation] Found {len(comparables)} comparables")
        except ValueError as e:
            print(f"[Valuation] Comparable search failed: {str(e)}")
            # Log comparable search failures to Sentry
            try:
                import sentry_sdk
                sentry_sdk.set_context("comparable_search_failure", {
                    "address": request.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "error": str(e)
                })
                sentry_sdk.set_tag("error_type", "no_comparables")
                sentry_sdk.capture_message(f"No comparables found: {str(e)}", level="info")
            except ImportError:
                pass

            raise HTTPException(
                status_code=404,
                detail=f"No comparable sales found: {str(e)}"
            )

        if len(comparables) < 3:
            # Log insufficient comparables
            try:
                import sentry_sdk
                sentry_sdk.set_context("insufficient_comparables", {
                    "address": request.address,
                    "count": len(comparables),
                    "latitude": location.latitude,
                    "longitude": location.longitude
                })
                sentry_sdk.set_tag("error_type", "insufficient_comparables")
                sentry_sdk.capture_message(
                    f"Insufficient comparables: {len(comparables)} found",
                    level="info"
                )
            except ImportError:
                pass

            raise HTTPException(
                status_code=404,
                detail=f"Insufficient comparable sales found ({len(comparables)}). "
                       "Need at least 3 comparables for valuation."
            )

        # Step 3: Adjust prices for time difference
        adjuster = MVPAdjuster(pool)
        target_date = request.valuation_date or datetime.now()

        for comp in comparables:
            # Temporal adjustment
            temporal_adj = await adjuster.adjust_temporal(
                sale_price=comp['price'],
                sale_date=comp['sale_date'],
                target_date=target_date,
                county=comp['county']
            )

            comp['adjusted_price'] = temporal_adj['adjusted_price']
            comp['adjustment_factor'] = temporal_adj['adjustment_factor']
            comp['temporal_adjustment'] = temporal_adj

        # Remove local price outliers (e.g. a lone multi-million sale amid a
        # cluster of ordinary ones) before weighting — otherwise they dominate
        # the average and inflate the estimate. See trim_price_outliers.
        comparables = trim_price_outliers(comparables)
        print(f"[Valuation] {len(comparables)} comparables after outlier trim")

        # Apartment-price ceiling: for apartment subjects, learn what an apartment
        # actually costs in this locality (from confirmed apartment sales) and use
        # it to drop house-priced comparables the type filter can't catch — the
        # unlabelled pricey houses that dominate house-heavy areas. See
        # MVPAdjuster.apartment_price_ceiling. None (skipped) for houses or where
        # local apartment data is too thin to trust.
        apt_ceiling = None
        if property_bucket(subject_property_type) == "apartment":
            apt_ceiling = await adjuster.apartment_price_ceiling(
                location.latitude, location.longitude
            )
            if apt_ceiling is not None:
                print(f"[Valuation] Apartment price ceiling (2-bed-equiv): €{apt_ceiling:,.0f}")

        # Bedroom-ladder valuation for apartments: normalise every comparable to a
        # 2-bed-equivalent, then re-expand to the subject's bedroom count. This
        # guarantees larger units are never valued below smaller ones and grounds
        # thin-data bedroom types in the wider local pool. Returns None for houses
        # or unknown bedroom counts, in which case we fall back to the plain
        # weighted average. See MVPAdjuster.bedroom_ladder_valuation.
        ladder = adjuster.bedroom_ladder_valuation(
            comparables, subject_bedrooms, subject_property_type,
            max_2bed_equiv=apt_ceiling,
        )

        # Calculate weights (ladder weights when it applies; otherwise bedroom +
        # property-type matching)
        if ladder is not None:
            weights = ladder['weights']
            print(f"[Valuation] Bedroom ladder applied: 2-bed base €{ladder['base_2bed']:,}")
        else:
            weights = adjuster.calculate_all_weights(
                comparables, subject_bedrooms, subject_property_type
            )

        # Log bedroom matching info
        if subject_bedrooms is not None:
            matching_beds = sum(1 for c in comparables if c.get('bedrooms') == subject_bedrooms)
            print(f"[Valuation] Bedroom matching: {matching_beds}/{len(comparables)} comparables match {subject_bedrooms} bedrooms")

        # Log property-type matching info
        if subject_property_type is not None:
            subj_bucket = property_bucket(subject_property_type)
            matching_type = sum(1 for c in comparables if property_bucket(c.get('property_type')) == subj_bucket)
            print(f"[Valuation] Type matching: {matching_type}/{len(comparables)} comparables match bucket '{subj_bucket}'")

        # Add weights to comparables
        for comp, weight in zip(comparables, weights):
            comp['weight'] = weight

        # Step 4: Calculate valuation
        calculator = ValuationCalculator()
        valuation = calculator.calculate_valuation(comparables, weights)

        if ladder is not None:
            # Override the raw weighted average with the bedroom-ladder estimate
            # and recentre the confidence interval on it (keep the half-width).
            new_est = ladder['estimate']
            ci = valuation['confidence_interval']
            half = (ci['upper'] - ci['lower']) / 2
            ci['lower'] = int(max(0, new_est - half))
            ci['upper'] = int(new_est + half)
            ci['width_pct'] = (
                round((ci['upper'] - ci['lower']) / new_est * 100, 1) if new_est > 0 else 0.0
            )
            valuation['estimate'] = new_est

        # Step 5: Validate and assign confidence
        validator = MVPValidator()
        validation = validator.validate(valuation, comparables)

        # Nearest amenities (Dublin only; None elsewhere or on any error).
        # Uses an in-memory cache of the small amenities table, so this adds no
        # per-request database round-trip after the first lookup.
        amenity_rows = await get_nearby_amenities(
            pool, location.latitude, location.longitude
        )
        nearby_amenities = (
            [NearbyAmenity(**a) for a in amenity_rows] if amenity_rows else None
        )

        # Calculate processing time
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Build response
        response = ValuationResponse(
            estimate=valuation['estimate'],
            confidence_interval=ConfidenceInterval(**valuation['confidence_interval']),
            validation=validation,
            comparables=[
                ComparableProperty(
                    id=c['id'],
                    address=c['address'],
                    price=c['price'],
                    adjusted_price=c['adjusted_price'],
                    sale_date=c['sale_date'],
                    distance_m=c['distance_m'],
                    weight=c['weight'],
                    bedrooms=c.get('bedrooms'),
                    property_type=c.get('property_type'),
                    temporal_adjustment_factor=c.get('adjustment_factor'),
                    recency_score=c.get('recency_score')
                )
                for c in comparables
            ],
            statistics=ValuationStatistics(**valuation['statistics']),
            nearby_amenities=nearby_amenities,
            metadata={
                'geocoded_location': {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'confidence': location.confidence,
                    'method': location.method,
                    'address_matched': location.address_matched
                },
                'valuation_date': target_date.isoformat(),
                'algorithm_version': '1.2.1-ladder-bedmatch',
                'processing_time_ms': processing_time_ms,
                'bedroom_ladder': {
                    'applied': ladder is not None,
                    'base_2bed': ladder['base_2bed'] if ladder is not None else None
                },
                'bedroom_matching': {
                    'enabled': subject_bedrooms is not None,
                    'subject_bedrooms': subject_bedrooms,
                    'matching_comparables': sum(1 for c in comparables if c.get('bedrooms') == subject_bedrooms) if subject_bedrooms is not None else 0
                },
                'property_type_matching': {
                    'enabled': subject_property_type is not None,
                    'subject_property_type': subject_property_type,
                    'subject_bucket': property_bucket(subject_property_type) if subject_property_type is not None else None
                }
            }
        )

        # Background task: log request to database
        background_tasks.add_task(
            log_valuation_request,
            db_pool=pool,
            request=request,
            location=location,
            response=response
        )

        # Log successful valuation to Sentry for monitoring
        try:
            import sentry_sdk
            sentry_sdk.set_context("valuation_success", {
                "address": request.address,
                "estimate": response.estimate,
                "confidence_level": response.validation.confidence_level.value,
                "n_comparables": response.validation.n_comparables,
                "processing_time_ms": processing_time_ms
            })
            sentry_sdk.set_tag("valuation_confidence", response.validation.confidence_level.value)
            sentry_sdk.set_measurement("processing_time_ms", processing_time_ms)
            sentry_sdk.set_measurement("n_comparables", response.validation.n_comparables)
        except ImportError:
            pass

        print(f"[Valuation] ✅ Success: estimate={response.estimate}, confidence={response.validation.confidence_level.value}, comparables={response.validation.n_comparables}")
        return response

    except HTTPException as e:
        # Re-raise HTTP exceptions with enhanced logging
        print(f"[Valuation] ❌ HTTP Error {e.status_code}: {e.detail}")
        raise

    except Exception as e:
        # Log unexpected errors with full context
        import traceback
        error_details = traceback.format_exc()
        print(f"[Valuation] ❌ Unexpected error: {e}")
        print(f"[Valuation] Request context: address='{request.address}', eircode={request.eircode}")
        print(error_details)

        # Log to Sentry (if configured)
        try:
            import sentry_sdk
            sentry_sdk.set_context("valuation_request", {
                "address": request.address,
                "eircode": request.eircode,
                "valuation_date": str(request.valuation_date) if request.valuation_date else None
            })
            sentry_sdk.set_tag("error_type", "valuation_calculation")
            sentry_sdk.capture_exception(e)
        except ImportError:
            pass

        # Return generic error to user
        raise HTTPException(
            status_code=500,
            detail="Valuation calculation failed. Please try again later."
        )


async def log_valuation_request(
    db_pool,
    request: ValuationRequest,
    location,
    response: ValuationResponse
):
    """
    Background task: Log valuation request to database.

    Stores request details for analytics and quality monitoring.

    Args:
        db_pool: Database connection pool
        request: Original request
        location: Geocoding result
        response: Valuation response
    """

    try:
        query = """
            INSERT INTO valuation_requests (
                address,
                eircode,
                latitude,
                longitude,
                valuation_date,
                estimate,
                estimate_lower,
                estimate_upper,
                confidence_level,
                n_comparables,
                quality_score,
                algorithm_version,
                processing_time_ms,
                bedrooms
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING request_id;
        """

        # Convert valuation_date string back to datetime for database
        valuation_datetime = datetime.fromisoformat(response.metadata['valuation_date'])

        request_id = await db_pool.fetchval(
            query,
            request.address,
            request.eircode,
            location.latitude,
            location.longitude,
            valuation_datetime,
            response.estimate,
            response.confidence_interval.lower,
            response.confidence_interval.upper,
            response.validation.confidence_level.value,
            response.validation.n_comparables,
            response.validation.quality_score,
            response.metadata['algorithm_version'],
            response.metadata['processing_time_ms'],
            request.bedrooms
        )

        # Log comparables used (for detailed analysis)
        for comp in response.comparables:
            await db_pool.execute(
                """
                INSERT INTO valuation_comparables (
                    request_id,
                    property_id,
                    distance_m,
                    weight,
                    original_price,
                    adjusted_price,
                    adjustment_factor,
                    sale_date,
                    days_since_sale,
                    recency_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                """,
                request_id,
                comp.id,
                comp.distance_m,
                comp.weight,
                comp.price,
                comp.adjusted_price,
                comp.temporal_adjustment_factor or 1.0,
                comp.sale_date,
                (datetime.now() - comp.sale_date).days,
                comp.recency_score
            )

    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Failed to log valuation request: {e}")
        request_id = None

    # Enrich property data with crowdsourced information
    await enrich_property_from_request(db_pool, request, request_id)


# The address must name one property: a house number or unit ("42 …", "Apt 3, …").
_SPECIFIC_ADDRESS_RE = re.compile(r"^(\d+[a-z]?\s|(apt|unit|flat)\s)", re.IGNORECASE)
# Bulk sales ("Units 1-76 …") are not one property.
_RANGE_ADDRESS_RE = re.compile(r"[0-9]+ *(-|to) *[0-9]+", re.IGNORECASE)
# Different spellings of one house count as the same property if this close (~100m).
_SAME_PROPERTY_DEG = 0.001
# The valuation page's top option is "6+": only 1-5 are exact counts.
_MAX_EXACT_BEDROOMS = 5


async def find_subject_property_ids(db_pool, address: str, county: Optional[str]) -> list:
    """Ids of the properties rows (one per sale) for exactly the house a valuation is
    for, or [] when the address doesn't pin down a single property.

    Independent of how the valuation was geocoded: a house with no coordinates, or a
    flagged geocode, is still the right row to fill in. Prefix match on
    address_normalized (index-backed, as the S1 page), within the county (Dublin
    when none is given). No full-text fallback: a near-match is the wrong house.
    """
    norm = _normalize_address(address)
    if not _SPECIFIC_ADDRESS_RE.match(norm) or _RANGE_ADDRESS_RE.search(norm):
        return []
    rows = await db_pool.fetch("""
        SELECT id, address_normalized, latitude, longitude
        FROM properties
        WHERE address_normalized ^@ $1
          AND LOWER(county) = LOWER($2)
        LIMIT 50
    """, norm, county or "Dublin")
    # "4 Main Street" is also a prefix of "4 Main Streetside": the match must end the
    # address or a comma part of it.
    rows = [r for r in rows
            if r["address_normalized"] == norm or r["address_normalized"].startswith(norm + ",")]
    if not rows or any(_RANGE_ADDRESS_RE.search(r["address_normalized"]) for r in rows):
        return []
    if len({r["address_normalized"] for r in rows}) > 1:
        # "42 Mount Carmel Road, Goatstown" and "…, Dundrum" are one house only if
        # every sale is geocoded to the same spot.
        if any(r["latitude"] is None for r in rows):
            return []
        lats = [r["latitude"] for r in rows]
        lons = [r["longitude"] for r in rows]
        if max(lats) - min(lats) > _SAME_PROPERTY_DEG or max(lons) - min(lons) > _SAME_PROPERTY_DEG * 1.5:
            return []
    return [r["id"] for r in rows]


async def enrich_property_from_request(
    db_pool,
    request: ValuationRequest,
    request_id=None
):
    """
    Enrich property database with crowdsourced data from valuation requests.

    Updates every sale row of the valued house with:
    - Eircode (if missing and provided)
    - Bedrooms (if missing and provided; 1-5 only, since 6 means "6+").
      Marked bedrooms_source = 'valuation_request'.
    - BER rating (if missing and provided)

    Never overwrites an existing value. The rows filled in are recorded on the
    valuation_requests row (enriched_property_ids).

    Args:
        db_pool: Database connection pool
        request: ValuationRequest with potential enrichment data
        request_id: valuation_requests row to record the enriched ids on (if logged)
    """
    bedrooms = request.bedrooms if request.bedrooms and request.bedrooms <= _MAX_EXACT_BEDROOMS else None
    if not (request.eircode or bedrooms or request.ber_rating):
        return

    try:
        ids = await find_subject_property_ids(db_pool, request.address, request.county)
        if not ids:
            print(f"[Valuation] Enrichment skipped: '{request.address}' is not one known property")
            return

        updated = await db_pool.fetch("""
            UPDATE properties
            SET eircode    = COALESCE(eircode, $2),
                bedrooms   = COALESCE(bedrooms, $3),
                bedrooms_source = CASE WHEN bedrooms IS NULL AND $3::int IS NOT NULL
                                       THEN 'valuation_request' ELSE bedrooms_source END,
                ber_rating = COALESCE(ber_rating, $4)
            WHERE id = ANY($1::bigint[])
              AND (($2::text IS NOT NULL AND eircode IS NULL)
                OR ($3::int  IS NOT NULL AND bedrooms IS NULL)
                OR ($4::text IS NOT NULL AND ber_rating IS NULL))
            RETURNING id, address, eircode, bedrooms, ber_rating
        """, ids, request.eircode, bedrooms, request.ber_rating)

        if updated:
            print(f"✅ Enriched {len(updated)} properties with crowdsourced data:")
            for row in updated:
                print(f"   {row['address']}: eircode={row['eircode']}, "
                      f"bedrooms={row['bedrooms']}, ber={row['ber_rating']}")
            if request_id:
                await db_pool.execute(
                    "UPDATE valuation_requests SET enriched_property_ids = $2 WHERE request_id = $1",
                    request_id, [r["id"] for r in updated])

    except Exception as e:
        # Don't fail if enrichment fails
        print(f"Warning: Could not enrich property data: {e}")
