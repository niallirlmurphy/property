"""
FastAPI endpoints for property valuation.

Phase 1: POST /api/valuation/estimate
"""

import os
import asyncpg
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from datetime import datetime
from typing import Optional

from .models import (
    ValuationRequest,
    ValuationResponse,
    ComparableProperty,
    ConfidenceInterval,
    ValuationStatistics
)
from .geocoder import ValuationGeocoder
from .comparable_search import ComparableSearcher
from .adjustments import MVPAdjuster
from .calculator import ValuationCalculator
from .validator import MVPValidator


# Router
router = APIRouter(prefix="/api/valuation", tags=["valuation"])


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

    # Get database pool
    pool = get_db_pool()

    try:
        # Step 1: Geocode address
        geocoder = ValuationGeocoder(pool)

        try:
            location = await geocoder.geocode_address(
                address=request.address,
                eircode=request.eircode
            )
        except ValueError as e:
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
            comparables = await searcher.find_comparables(
                latitude=location.latitude,
                longitude=location.longitude,
                min_count=5,
                max_count=30
            )
        except ValueError as e:
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

        # Calculate weights
        weights = adjuster.calculate_all_weights(comparables)

        # Add weights to comparables
        for comp, weight in zip(comparables, weights):
            comp['weight'] = weight

        # Step 4: Calculate valuation
        calculator = ValuationCalculator()
        valuation = calculator.calculate_valuation(comparables, weights)

        # Step 5: Validate and assign confidence
        validator = MVPValidator()
        validation = validator.validate(valuation, comparables)

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
            metadata={
                'geocoded_location': {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'confidence': location.confidence,
                    'method': location.method,
                    'address_matched': location.address_matched
                },
                'valuation_date': target_date.isoformat(),
                'algorithm_version': '1.0.0-mvp',
                'processing_time_ms': processing_time_ms
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

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Log unexpected errors to Sentry (if configured)
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
                processing_time_ms
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING request_id;
        """

        request_id = await db_pool.fetchval(
            query,
            request.address,
            request.eircode,
            location.latitude,
            location.longitude,
            response.metadata['valuation_date'],
            response.estimate,
            response.confidence_interval.lower,
            response.confidence_interval.upper,
            response.validation.confidence_level.value,
            response.validation.n_comparables,
            response.validation.quality_score,
            response.metadata['algorithm_version'],
            response.metadata['processing_time_ms']
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
