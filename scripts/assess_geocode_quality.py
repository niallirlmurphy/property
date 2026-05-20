#!/usr/bin/env python3
"""
Assess geocoding quality in the property database.

Checks:
1. Duplicate coordinates - multiple distinct addresses with identical coordinates
2. County mismatches - coordinates outside the stated county boundaries
3. Clustering anomalies - addresses in same area with wildly different coordinates
4. Coordinate precision - suspiciously rounded coordinates
5. Out-of-bounds - coordinates outside Ireland

Usage:
    python3 scripts/assess_geocode_quality.py [--fix] [--limit N]
"""

import asyncio
import asyncpg
import os
import sys
import httpx
from collections import defaultdict
from typing import Optional
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
USER_AGENT = "PPR-geocode-quality/1.0"

# Approximate Ireland bounding box
IRELAND_BOUNDS = {
    "min_lat": 51.4,
    "max_lat": 55.5,
    "min_lon": -10.7,
    "max_lon": -5.4,
}


async def check_duplicate_coordinates(pool: asyncpg.Pool):
    """Find suspiciously many distinct addresses sharing identical coordinates."""
    print("\n=== Checking for duplicate coordinates ===")

    rows = await pool.fetch("""
        SELECT latitude, longitude, COUNT(DISTINCT address) as addr_count,
               COUNT(*) as total_sales,
               ARRAY_AGG(DISTINCT address ORDER BY address) FILTER (WHERE latitude IS NOT NULL) as addresses
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 5
        ORDER BY addr_count DESC
        LIMIT 50
    """)

    if not rows:
        print("✓ No significant duplicate coordinate issues found")
        return []

    issues = []
    for r in rows:
        issues.append({
            "type": "duplicate_coords",
            "lat": r["latitude"],
            "lon": r["longitude"],
            "addr_count": r["addr_count"],
            "total_sales": r["total_sales"],
            "sample_addresses": r["addresses"][:5],
        })
        print(f"\n⚠️  {r['addr_count']} distinct addresses at ({r['latitude']:.6f}, {r['longitude']:.6f})")
        print(f"   Total sales: {r['total_sales']}")
        print(f"   Sample addresses:")
        for addr in r["addresses"][:3]:
            print(f"     - {addr}")

    return issues


async def check_out_of_bounds(pool: asyncpg.Pool):
    """Find coordinates outside Ireland."""
    print("\n=== Checking for out-of-bounds coordinates ===")

    row = await pool.fetchrow(f"""
        SELECT COUNT(*) as count,
               ARRAY_AGG(DISTINCT address ORDER BY address) FILTER (WHERE latitude IS NOT NULL) as addresses
        FROM properties
        WHERE latitude IS NOT NULL
          AND (latitude < {IRELAND_BOUNDS['min_lat']} OR latitude > {IRELAND_BOUNDS['max_lat']}
               OR longitude < {IRELAND_BOUNDS['min_lon']} OR longitude > {IRELAND_BOUNDS['max_lon']})
        LIMIT 100
    """)

    if row["count"] == 0:
        print("✓ All coordinates within Ireland bounds")
        return []

    print(f"\n⚠️  {row['count']} properties with coordinates outside Ireland")
    print("   Sample addresses:")
    for addr in (row["addresses"] or [])[:5]:
        print(f"     - {addr}")

    return [{"type": "out_of_bounds", "count": row["count"]}]


async def check_suspicious_precision(pool: asyncpg.Pool):
    """Find coordinates with suspiciously low precision (exactly 0.0, or rounded)."""
    print("\n=== Checking for suspicious coordinate precision ===")

    # Coordinates that are exactly 0.0 or have only 1-2 decimal places
    row = await pool.fetchrow("""
        SELECT COUNT(*) as count,
               ARRAY_AGG(DISTINCT address ORDER BY address) FILTER (WHERE latitude IS NOT NULL) as addresses
        FROM (
            SELECT address, latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
              AND (latitude = 0 OR longitude = 0
                   OR (latitude * 100 = FLOOR(latitude * 100)
                       AND longitude * 100 = FLOOR(longitude * 100)))
            LIMIT 10
        ) sub
    """)

    if row["count"] == 0:
        print("✓ No suspicious precision issues found")
        return []

    print(f"\n⚠️  {row['count']} properties with suspiciously rounded coordinates")
    print("   Sample addresses:")
    for addr in (row["addresses"] or [])[:5]:
        print(f"     - {addr}")

    return [{"type": "low_precision", "count": row["count"]}]


async def check_place_name_clusters(pool: asyncpg.Pool):
    """
    For common place names (towns/villages), check if geocoded coordinates
    cluster tightly or are scattered (indicating inconsistent geocoding).
    """
    print("\n=== Checking place-name clustering consistency ===")

    # Extract common place names from addresses (simplified heuristic)
    # Look for patterns like "TOWN_NAME, COUNTY" or "Street, TOWN_NAME"
    rows = await pool.fetch("""
        WITH place_extracts AS (
            SELECT
                -- Extract trailing place name after last comma
                TRIM(SPLIT_PART(address, ',', -1)) as place,
                latitude, longitude,
                address
            FROM properties
            WHERE latitude IS NOT NULL
              AND address ~ ','  -- has at least one comma
        ),
        place_stats AS (
            SELECT
                place,
                COUNT(*) as count,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lon,
                STDDEV(latitude) as std_lat,
                STDDEV(longitude) as std_lon,
                ARRAY_AGG(DISTINCT address ORDER BY address) FILTER (WHERE latitude IS NOT NULL) as addresses
            FROM place_extracts
            WHERE LENGTH(place) >= 4  -- filter out short fragments
            GROUP BY place
            HAVING COUNT(*) >= 10  -- only places with 10+ properties
        )
        SELECT *
        FROM place_stats
        WHERE (COALESCE(std_lat, 0) > 0.05 OR COALESCE(std_lon, 0) > 0.05)  -- ~5km spread
        ORDER BY COALESCE(std_lat, 0) + COALESCE(std_lon, 0) DESC
        LIMIT 30
    """)

    if not rows:
        print("✓ Place names show consistent clustering")
        return []

    issues = []
    for r in rows:
        std_lat = r["std_lat"] or 0
        std_lon = r["std_lon"] or 0
        if std_lat > 0.02 or std_lon > 0.02:  # ~2km threshold
            issues.append({
                "type": "scattered_place",
                "place": r["place"],
                "count": r["count"],
                "std_lat": std_lat,
                "std_lon": std_lon,
            })
            print(f"\n⚠️  '{r['place']}' has scattered coordinates ({r['count']} properties)")
            print(f"   Std dev: lat={std_lat:.4f}, lon={std_lon:.4f} (~{std_lat * 111:.1f}km)")
            print(f"   Average: ({r['avg_lat']:.4f}, {r['avg_lon']:.4f})")
            print(f"   Sample addresses:")
            for addr in (r["addresses"] or [])[:3]:
                print(f"     - {addr}")

    return issues


async def check_county_boundaries(pool: asyncpg.Pool):
    """
    Check if coordinates fall within expected county boundaries by reverse geocoding
    a sample and comparing stated county vs geocoded county.
    """
    print("\n=== Checking county boundary consistency (sampling) ===")
    print("(This uses Nominatim reverse geocoding - may be slow)")

    # Sample properties from each county
    rows = await pool.fetch("""
        WITH ranked AS (
            SELECT
                id, address, county, latitude, longitude,
                ROW_NUMBER() OVER (PARTITION BY county ORDER BY RANDOM()) as rn
            FROM properties
            WHERE latitude IS NOT NULL AND county IS NOT NULL
        )
        SELECT id, address, county, latitude, longitude
        FROM ranked
        WHERE rn <= 3  -- 3 samples per county
        ORDER BY county
        LIMIT 80  -- cap total checks
    """)

    issues = []
    async with httpx.AsyncClient() as client:
        for r in rows:
            try:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": r["latitude"],
                        "lon": r["longitude"],
                        "format": "json",
                        "addressdetails": 1,
                    },
                    headers={"User-Agent": USER_AGENT},
                    timeout=5.0,
                )
                await asyncio.sleep(1.1)  # Respect Nominatim rate limit

                if resp.status_code != 200:
                    continue

                data = resp.json()
                geocoded_county = data.get("address", {}).get("county", "")
                stated_county = r["county"]

                # Normalize county names (remove "County", "Co.", etc.)
                def normalize_county(s):
                    s = s.lower().strip()
                    s = s.replace("county ", "").replace("co. ", "").replace("co ", "")
                    return s

                gc = normalize_county(geocoded_county)
                sc = normalize_county(stated_county)

                if gc and sc and gc != sc:
                    issues.append({
                        "type": "county_mismatch",
                        "address": r["address"],
                        "stated_county": stated_county,
                        "geocoded_county": geocoded_county,
                        "lat": r["latitude"],
                        "lon": r["longitude"],
                    })
                    print(f"\n⚠️  County mismatch: {r['address']}")
                    print(f"   Stated: {stated_county}, Geocoded: {geocoded_county}")
                    print(f"   Coords: ({r['latitude']:.6f}, {r['longitude']:.6f})")

            except Exception as e:
                print(f"   Error checking {r['address']}: {e}")

    if not issues:
        print("✓ Sampled counties match geocoded locations")

    return issues


async def generate_summary_stats(pool: asyncpg.Pool):
    """Generate overall geocoding statistics."""
    print("\n=== Overall Geocoding Statistics ===")

    row = await pool.fetchrow("""
        SELECT
            COUNT(*) as total_properties,
            COUNT(latitude) as geocoded_count,
            ROUND(100.0 * COUNT(latitude) / COUNT(*), 1) as geocoded_pct
        FROM properties
    """)

    print(f"Total properties: {row['total_properties']:,}")
    print(f"Geocoded: {row['geocoded_count']:,} ({row['geocoded_pct']}%)")
    print(f"Missing coordinates: {row['total_properties'] - row['geocoded_count']:,}")


async def main():
    fix = "--fix" in sys.argv
    if fix:
        print("⚠️  Fix mode not yet implemented - running in report-only mode")

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    try:
        await generate_summary_stats(pool)

        all_issues = []
        all_issues.extend(await check_out_of_bounds(pool))
        all_issues.extend(await check_suspicious_precision(pool))
        all_issues.extend(await check_duplicate_coordinates(pool))
        all_issues.extend(await check_place_name_clusters(pool))

        # County boundary check is slow - optional
        if "--check-counties" in sys.argv:
            all_issues.extend(await check_county_boundaries(pool))
        else:
            print("\n(Skipping county boundary check - add --check-counties to enable)")

        print(f"\n{'='*60}")
        print(f"SUMMARY: Found {len(all_issues)} potential geocoding issues")
        print(f"{'='*60}")

        # Group by type
        by_type = defaultdict(int)
        for issue in all_issues:
            by_type[issue["type"]] += 1

        if by_type:
            print("\nIssue breakdown:")
            for itype, count in sorted(by_type.items()):
                print(f"  - {itype}: {count}")
        else:
            print("\n✓ No significant issues detected!")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
