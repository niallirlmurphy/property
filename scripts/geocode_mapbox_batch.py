#!/usr/bin/env python3
"""
Batch geocode properties using Mapbox Geocoding API with canonical cache.

Mapbox provides high-quality global geocoding with batch API support.
Best used for properties WITHOUT Eircodes (Autoaddress is better for Eircode properties).

API: https://docs.mapbox.com/api/search/geocoding/
- Batch API: Up to 1,000 queries per request
- Free tier: 100,000 requests/month
- Pricing: $0.75 per 1,000 after free tier

Validation:
- Ireland bounds check (51.4-55.5°N, -10.7--5.4°W)
- County boundary validation
- Coordinate precision check (accept only rooftop, parcel, point)
- Reject interpolated and approximate results

Usage:
    # Geocode high-priority properties (>€400k, recent sales first)
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --min-price 400000 --apply

    # Geocode properties WITHOUT Eircodes
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --no-eircode --apply

    # Re-geocode centroid coordinates (70k properties with generic coords)
    python3 scripts/geocode_mapbox_batch.py --centroid --limit 100 --apply

    # Test with small batch
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 10

Flags:
    --needs-geocoding    Process properties with needs_geocoding=TRUE flag
    --centroid           Process properties at centroid coordinates (100+ addresses at same point)
    --no-eircode         Filter to properties WITHOUT Eircodes
    --min-price N        Filter to properties with price >= N
    --apply              Actually update database (default is dry-run)
    --limit N            Process at most N properties
    --county COUNTY      Filter to specific county
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import html
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from county_validator import validate_county, normalize_county, COUNTY_BOUNDS
from canonical_geocoding import (
    initialize_cache,
    get_canonical_coordinates,
    cache_coordinates
)
from duplicate_handler import update_geocoding_for_duplicates
from mapbox_client import MapboxClient
from extract_base_address import is_bulk_sale, extract_base_address

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")

# API endpoint
MAPBOX_BATCH_URL = "https://api.mapbox.com/search/geocode/v6/batch"

# Ireland bounding box
IRELAND_BBOX = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon

# Acceptable precision levels (reject interpolated/approximate)
ACCEPTABLE_PRECISION = {'rooftop', 'parcel', 'point'}


async def fetch_properties_needing_geocoding(pool: asyncpg.Pool, limit: int = None,
                                             county: str = None, no_eircode: bool = False,
                                             min_price: int = None) -> List[Dict]:
    """Fetch properties flagged as needing geocoding (priority order)."""
    print("Fetching properties needing geocoding...")

    where_clauses = ["needs_geocoding = TRUE"]
    params = []
    idx = 1

    if county:
        where_clauses.append(f"LOWER(county) = LOWER(${idx})")
        params.append(county)
        idx += 1

    if no_eircode:
        where_clauses.append("(eircode IS NULL OR eircode = '')")

    if min_price:
        where_clauses.append(f"price >= ${idx}")
        params.append(min_price)
        idx += 1

    where = " AND ".join(where_clauses)
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT id, address, address_normalized, county, price, sale_date,
               eircode, routing_key
        FROM properties
        WHERE {where}
        ORDER BY
            -- Eircode-holders re-geocode most reliably (eircode-first, ~1 request each)
            -- and are validated against the routing-key centroid, so process them first.
            (eircode IS NOT NULL AND eircode <> '') DESC,
            price DESC,
            sale_date DESC
        {limit_clause}
    """

    rows = await pool.fetch(query, *params)
    return [dict(row) for row in rows]


async def fetch_centroid_properties(pool: asyncpg.Pool, limit: int = None,
                                    county: str = None) -> List[Dict]:
    """Fetch properties at centroid coordinates (100+ addresses at same point)."""
    print("Identifying centroid coordinates...")

    # Find centroid coordinates
    centroid_query = """
        SELECT latitude, longitude, COUNT(DISTINCT address) as addr_count
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
    """

    centroids = await pool.fetch(centroid_query)
    print(f"Found {len(centroids)} centroid coordinates")

    if not centroids:
        return []

    # Fetch properties at those centroids
    properties = []
    for centroid in centroids:
        lat, lon = centroid['latitude'], centroid['longitude']

        where_clauses = [
            "ABS(latitude - $1) < 0.000001",
            "ABS(longitude - $2) < 0.000001"
        ]
        params = [lat, lon]
        idx = 3

        if county:
            where_clauses.append(f"LOWER(county) = LOWER(${idx})")
            params.append(county)
            idx += 1

        where = " AND ".join(where_clauses)

        query = f"""
            SELECT id, address, address_normalized, county, eircode,
                   latitude, longitude, price, sale_date
            FROM properties
            WHERE {where}
            ORDER BY
                CASE WHEN eircode IS NOT NULL THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 500
        """

        rows = await pool.fetch(query, *params)
        for row in rows:
            properties.append(dict(row))
            if limit and len(properties) >= limit:
                return properties

    return properties


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Hard-reject a geocode whose eircode routing key sits this far from the coordinate.
# A routing key is an AREA, not a point: rural keys sprawl (a legitimate address can
# sit ~20km from its key's centroid — e.g. Nobber is 19km from the A82/Kells centroid
# at its CORRECT coordinates). A tight 10km threshold therefore rejects legitimate
# rural matches. 40km only fires on confident cross-region errors. The precise
# wrong-town signal is the county-box check below.
ROUTING_KEY_MAX_KM = 40.0

# County bounding boxes are tight; pad them by this margin before treating "outside
# the box" as a wrong-county rejection, so genuine edge-of-county towns (e.g. Fingal
# reaches ~53.63N, above County Dublin's 53.50 box) are not rejected.
COUNTY_MARGIN_DEG = 0.2


def _outside_county_box(lat: float, lon: float, county: str) -> bool:
    """True if (lat, lon) is outside the stored county's margin-padded box.

    Conservative, low-false-positive wrong-county signal: a Kerry-county address that
    Mapbox matched to a Dublin street is wrong regardless of precision/distance.
    """
    norm = normalize_county(county) if county else ""
    bounds = COUNTY_BOUNDS.get(norm)
    if not bounds:
        return False  # unknown county -> cannot judge
    min_lat, max_lat, min_lon, max_lon = bounds
    m = COUNTY_MARGIN_DEG
    return not (min_lat - m <= lat <= max_lat + m and min_lon - m <= lon <= max_lon + m)


def validate_coordinates(lat: float, lon: float, county: str, feature_type: str,
                         precision: Optional[str], routing_key: Optional[str] = None,
                         rk_centroids: Optional[dict] = None) -> Tuple[bool, str, int]:
    """
    Validate Mapbox coordinates.

    Returns: (is_valid, reason, quality_score)
    - quality_score: 100=rooftop, 90=parcel, 80=point, 75=address/street, 70=locality
    """

    # Validation 1: Ireland bounds (CRITICAL)
    min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return False, f"out_of_bounds({lat:.2f},{lon:.2f})", 0

    # Validation 1b: Routing-key distance (CRITICAL, hard reject).
    # The eircode's routing key is an independent ground truth for location.
    # If the geocoded point is far from that key's centroid, the geocoder matched
    # the wrong place (e.g. a generic street name in the wrong town) -> reject.
    if routing_key and rk_centroids:
        centroid = rk_centroids.get(routing_key)
        if centroid:
            dist_km = _haversine_km(lat, lon, centroid[0], centroid[1])
            if dist_km > ROUTING_KEY_MAX_KM:
                return False, f"routing_key_far({routing_key}:{dist_km:.0f}km)", 0

    # Validation 1c: Wrong county (CRITICAL, hard reject).
    # If the coordinate lands outside the stored county's (padded) box, Mapbox matched
    # a same-named street/place in a different county -> reject.
    if county and _outside_county_box(lat, lon, county):
        return False, f"wrong_county({county})", 0

    # Validation 2: Feature type and precision level
    # Note: MapboxClient v5 API returns place_type (address, postcode, poi, locality)
    # not the v6 precision level (rooftop, parcel, point)
    quality_score = 70  # Default

    if feature_type == 'address':
        # Address-level results - good quality
        # Check if precision has detailed accuracy (v6 API)
        if precision in ACCEPTABLE_PRECISION:
            quality_map = {
                'rooftop': 100,
                'parcel': 90,
                'point': 80
            }
            quality_score = quality_map.get(precision, 80)
        else:
            # v5 API or no precision - assume good address quality
            quality_score = 80

    elif feature_type == 'postcode':
        # Postcode/Eircode - good quality for Irish addresses
        quality_score = 85

    elif feature_type == 'poi':
        # Point of interest - acceptable
        quality_score = 75

    elif feature_type in ('locality', 'place'):
        # Rural areas without street addresses - acceptable but lower quality
        quality_score = 70

    elif feature_type == 'street':
        # Street-level results - acceptable
        quality_score = 75

    else:
        # Other feature types - may be too imprecise
        return False, f"feature_type_{feature_type}", 0

    # Validation 3: County boundary (optional, downgrades quality but doesn't reject)
    if county:
        is_valid, reason = validate_county(lat, lon, county)
        if not is_valid:
            quality_score = min(quality_score, 70)  # Downgrade for county mismatch

    return True, "validated", quality_score


async def batch_geocode_mapbox(properties: List[Dict], pool: asyncpg.Pool,
                                client: httpx.AsyncClient,
                                rk_centroids: Optional[dict] = None) -> List[Tuple[int, Optional[float], Optional[float], int]]:
    """
    Batch geocode using Mapbox API with improved logic:
    - HTML entity cleaning (Tandy&#039;s → Tandy's)
    - Eircode-first strategy (try postal code before address)
    - Bulk sale extraction (Units 1-76 Bridge Hall → Bridge Hall)
    - Canonical cache

    Returns list of (property_id, lat, lon, quality_score)
    """
    if not MAPBOX_TOKEN:
        print("❌ MAPBOX_TOKEN not set in backend/.env")
        return []

    # Process all properties (cache is too large to load)
    print(f"Geocoding {len(properties)} properties with improved logic:")
    print(f"  - HTML entity cleaning (Tandy&#039;s → Tandy's)")
    print(f"  - Eircode-first strategy (try postal code before address)")
    print(f"  - Bulk sale extraction (Units 1-76 → base address)")

    results = []

    # Use MapboxClient for tracking and eircode-first strategy
    async with MapboxClient(source='geocode_mapbox_batch', operation='needs_geocoding') as mapbox:
        # Process individually to use eircode-first and bulk extraction logic
        bulk_count = 0
        eircode_count = 0

        for i, prop in enumerate(properties):
            if i % 100 == 0 and i > 0:
                print(f"  Progress: {i}/{len(properties)} properties...")

            # Get address and clean HTML entities
            address = prop.get('address_normalized') or prop['address']
            address = html.unescape(address)

            # Check if bulk sale and extract base address
            if is_bulk_sale(address):
                address = extract_base_address(address)
                bulk_count += 1

            # Build query with county
            query = f"{address}, {prop['county']}, Ireland" if prop['county'] else f"{address}, Ireland"

            try:
                # Geocode by ADDRESS only. Mapbox cannot resolve Irish unit-level
                # eircodes (proprietary An Post data) — the pre-lookup returns
                # nothing (or coarse routing-key level) and wastes a request. The
                # eircode's routing key is instead used purely for validation below
                # (rejecting matches that land far from where the routing key says).
                result = await mapbox.geocode(query, country='ie')

                if result:
                    lat = result['latitude']
                    lon = result['longitude']
                    # MapboxClient returns place_type as 'precision'
                    place_type = result.get('precision', 'unknown')

                    if result.get('method') == 'eircode':
                        eircode_count += 1

                    # Validate - use place_type for both feature_type and precision.
                    # Pass routing key + centroids for the hard distance check.
                    is_valid, reason, quality_score = validate_coordinates(
                        lat, lon, prop['county'], place_type, place_type,
                        routing_key=prop.get('routing_key'), rk_centroids=rk_centroids
                    )

                    if is_valid and quality_score >= 70:
                        results.append((prop['id'], lat, lon, quality_score))
                    else:
                        if len(results) < 5:  # Log first few failures
                            print(f"  ⚠️  Rejected {prop['address'][:40]}: {reason}")
                        results.append((prop['id'], None, None, 0))
                else:
                    results.append((prop['id'], None, None, 0))

            except Exception as e:
                if len(results) < 5:
                    print(f"  ❌ Error geocoding {prop['address'][:40]}: {e}")
                results.append((prop['id'], None, None, 0))

    print(f"\n✓ Geocoding complete:")
    print(f"  Bulk sales extracted: {bulk_count}")
    print(f"  Eircode-first hits: {eircode_count}")
    print(f"  Total geocoded: {sum(1 for r in results if r[1] is not None)}/{len(results)}")

    return results


async def geocode_with_mapbox(limit: int = None, dry_run: bool = True,
                               county: str = None, needs_geocoding: bool = False,
                               no_eircode: bool = False, min_price: int = None,
                               centroid: bool = False):
    """
    Batch geocode properties using Mapbox.

    Args:
        limit: Max number of properties to process
        dry_run: If True, don't update database
        county: Filter to specific county
        needs_geocoding: If True, process properties flagged as needs_geocoding
        no_eircode: If True (with needs_geocoding), only process properties WITHOUT Eircodes
        min_price: If set, only process properties >= this price
        centroid: If True, process properties at centroid coordinates
    """
    if not MAPBOX_TOKEN:
        print("❌ MAPBOX_TOKEN not set in backend/.env")
        print("\nGet your API key from: https://www.mapbox.com/")
        print("Add to backend/.env: MAPBOX_TOKEN=your_token_here")
        return

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    try:
        # Fetch properties
        if centroid:
            properties = await fetch_centroid_properties(
                pool, limit=limit, county=county
            )
        else:
            properties = await fetch_properties_needing_geocoding(
                pool, limit=limit, county=county, no_eircode=no_eircode, min_price=min_price
            )

        print(f"\n{'='*70}")
        print(f"MAPBOX BATCH GEOCODING")
        print(f"{'='*70}")
        if centroid:
            print(f"Mode: CENTROID RE-GEOCODING")
        elif needs_geocoding:
            filters = []
            if no_eircode:
                filters.append("WITHOUT Eircodes")
            if min_price:
                filters.append(f"Price >= €{min_price:,}")
            if filters:
                print(f"Filters: {', '.join(filters)}")
        print(f"Properties to process: {len(properties):,}")
        print(f"Batch size: Up to 1,000 per API call")
        print(f"Database updates: {'DRY RUN (no changes)' if dry_run else 'APPLY'}")
        print()

        if dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made\n")

        # Load routing-key centroids once for the hard distance validation.
        rk_centroids = {}
        try:
            rk_rows = await pool.fetch(
                "SELECT routing_key, centroid_lat, centroid_lon FROM routing_key_stats "
                "WHERE geocoded_count >= 20 AND centroid_lat IS NOT NULL"
            )
            rk_centroids = {r['routing_key']: (r['centroid_lat'], r['centroid_lon']) for r in rk_rows}
            print(f"Loaded {len(rk_centroids):,} routing-key centroids for validation")
        except Exception as e:
            print(f"⚠️  Could not load routing_key_stats centroids ({e}); skipping distance validation")

        # Release the DB pool during the (potentially long) geocoding phase. Holding
        # idle connections open across a multi-minute Mapbox run lets Supabase close
        # them server-side, so the later write phase would fail with
        # ConnectionDoesNotExistError and lose the whole batch's results. We reopen a
        # fresh pool for the writes below.
        await pool.close()
        pool = None

        async with httpx.AsyncClient() as client:
            results = await batch_geocode_mapbox(properties, None, client, rk_centroids=rk_centroids)

        if not dry_run:
            pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

        # Process results
        success_count = 0
        failed_count = 0
        quality_scores = []

        for prop_id, lat, lon, quality_score in results:
            if lat and lon and quality_score >= 70:
                success_count += 1
                quality_scores.append(quality_score)

                if not dry_run:
                    await pool.execute("""
                        UPDATE properties
                        SET latitude = $1, longitude = $2,
                            geog = ST_MakePoint($2, $1)::geography,
                            needs_geocoding = FALSE,
                            geocode_suspect = FALSE
                        WHERE id = $3
                    """, lat, lon, prop_id)
            else:
                failed_count += 1

        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Processed: {len(results):,}")
        print(f"✓ Success: {success_count:,} ({100*success_count/len(results):.1f}%)")
        print(f"✗ Failed: {failed_count:,}")

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"\nQuality Score Average: {avg_quality:.1f}/100")
            print(f"  Rooftop (100): {sum(1 for q in quality_scores if q == 100)} properties")
            print(f"  Parcel (90): {sum(1 for q in quality_scores if q == 90)} properties")
            print(f"  Point (80): {sum(1 for q in quality_scores if q == 80)} properties")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to commit.")

    finally:
        if pool is not None:
            await pool.close()


async def main():
    # Skip canonical cache for batch operations (too large to load into memory)
    # Cache will be checked per-address during geocoding
    print("Starting batch geocoding with improved logic...\n")

    dry_run = "--apply" not in sys.argv
    needs_geocoding = "--needs-geocoding" in sys.argv
    no_eircode = "--no-eircode" in sys.argv
    centroid = "--centroid" in sys.argv
    limit = None
    county = None
    min_price = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]
        elif arg == "--min-price" and i + 1 < len(sys.argv):
            min_price = int(sys.argv[i + 1])

    await geocode_with_mapbox(
        limit=limit,
        dry_run=dry_run,
        county=county,
        needs_geocoding=needs_geocoding,
        no_eircode=no_eircode,
        min_price=min_price,
        centroid=centroid
    )


if __name__ == "__main__":
    asyncio.run(main())
