#!/usr/bin/env python3
"""
Batch geocode properties using Mapbox Geocoding API.

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
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from county_validator import validate_county

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
        SELECT id, address, address_normalized, county, price, sale_date
        FROM properties
        WHERE {where}
        ORDER BY
            sale_date DESC,
            price DESC
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


def validate_coordinates(lat: float, lon: float, county: str, feature_type: str, precision: Optional[str]) -> Tuple[bool, str, int]:
    """
    Validate Mapbox coordinates.

    Returns: (is_valid, reason, quality_score)
    - quality_score: 100=rooftop, 90=parcel, 80=point, 70=locality, <70=rejected
    """

    # Validation 1: Ireland bounds (CRITICAL)
    min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return False, f"out_of_bounds({lat:.2f},{lon:.2f})", 0

    # Validation 2: Feature type and precision level
    quality_score = 70  # Default for locality/place without precision

    if feature_type == 'address' and precision:
        # Address results with precision info
        if precision not in ACCEPTABLE_PRECISION:
            return False, f"precision_{precision}", 0

        quality_map = {
            'rooftop': 100,
            'parcel': 90,
            'point': 80
        }
        quality_score = quality_map.get(precision, 70)

    elif feature_type in ('locality', 'place'):
        # Rural areas without street addresses - acceptable but lower quality
        quality_score = 70

    elif feature_type == 'street':
        # Street-level results - acceptable for properties without Eircodes
        # Better than nothing, especially with improved Mapbox Irish coverage
        quality_score = 75

    else:
        # Other feature types (postcode, etc.) - may be too imprecise
        return False, f"feature_type_{feature_type}", 0

    # Validation 3: County boundary (optional, downgrades quality but doesn't reject)
    if county:
        is_valid, reason = validate_county(lat, lon, county)
        if not is_valid:
            quality_score = min(quality_score, 70)  # Downgrade for county mismatch

    return True, "validated", quality_score


async def batch_geocode_mapbox(properties: List[Dict], pool: asyncpg.Pool,
                                client: httpx.AsyncClient) -> List[Tuple[int, Optional[float], Optional[float], int]]:
    """
    Batch geocode using Mapbox API (up to 1,000 at a time).

    Returns list of (property_id, lat, lon, quality_score)
    """
    if not MAPBOX_TOKEN:
        print("❌ MAPBOX_TOKEN not set in backend/.env")
        return []

    results = []
    batch_size = 1000  # Mapbox max

    for batch_start in range(0, len(properties), batch_size):
        batch = properties[batch_start:batch_start + batch_size]

        print(f"\nBatch {batch_start//batch_size + 1}: Processing {len(batch)} properties...")

        # Build batch request
        queries = []
        for prop in batch:
            # Use normalized address if available, fallback to original
            address = prop.get('address_normalized') or prop['address']
            query_text = f"{address}, {prop['county']}, Ireland" if prop['county'] else f"{address}, Ireland"
            queries.append({
                "q": query_text,
                "country": "ie"  # Limit to Ireland
            })

        try:
            response = await client.post(
                MAPBOX_BATCH_URL,
                params={"access_token": MAPBOX_TOKEN},
                json=queries,
                timeout=60.0
            )

            if response.status_code != 200:
                print(f"  ❌ Mapbox API error: HTTP {response.status_code}")
                print(f"     {response.text[:200]}")
                continue

            data = response.json()
            batch_results = data.get("batch", [])

            # Process results
            for i, result_wrapper in enumerate(batch_results):
                prop = batch[i]
                features = result_wrapper.get("features", [])

                if not features:
                    results.append((prop['id'], None, None, 0))
                    continue

                # Take first result
                feature = features[0]
                coords = feature.get("geometry", {}).get("coordinates", [])

                if len(coords) != 2:
                    results.append((prop['id'], None, None, 0))
                    continue

                lon, lat = coords  # Mapbox returns [lon, lat]
                properties_obj = feature.get("properties", {})
                feature_type = properties_obj.get("feature_type", "unknown")
                precision = properties_obj.get("coordinates", {}).get("accuracy")

                # Validate
                is_valid, reason, quality_score = validate_coordinates(lat, lon, prop['county'], feature_type, precision)

                if is_valid and quality_score >= 70:
                    results.append((prop['id'], lat, lon, quality_score))
                else:
                    if i < 5:  # Log first few failures
                        print(f"  ⚠️  Rejected {prop['address'][:40]}: {reason}")
                    results.append((prop['id'], None, None, 0))

        except Exception as e:
            print(f"  ❌ Batch geocoding error: {e}")
            # Mark all in batch as failed
            for prop in batch:
                results.append((prop['id'], None, None, 0))

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

        async with httpx.AsyncClient() as client:
            results = await batch_geocode_mapbox(properties, pool, client)

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
                            needs_geocoding = FALSE
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
        await pool.close()


async def main():
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
