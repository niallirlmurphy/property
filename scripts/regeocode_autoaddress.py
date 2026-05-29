#!/usr/bin/env python3
"""
Geocode properties using AutoAddress API with comprehensive validation.

AutoAddress is an Irish geocoding service with excellent Irish address coverage,
including Eircodes and precise coordinates.

API: https://www.autoaddress.com/
- Autocomplete: Search for addresses
- Lookup: Get full address details including coordinates

Validation:
- Ireland bounds check (51.4-55.5°N, -10.7--5.4°W)
- County boundary validation
- Routing key distance validation (Eircodes within 5km of centroid)
- Quality scoring (100 = perfect, 70 = acceptable minimum)

Usage:
    # Geocode properties flagged as needs_geocoding (from PPR sync)
    python3 scripts/regeocode_autoaddress.py --needs-geocoding --with-eircode --apply --limit 2215

    # Re-geocode centroid properties (legacy mode)
    python3 scripts/regeocode_autoaddress.py --apply --limit 100 [--county DUBLIN]

Flags:
    --needs-geocoding    Process properties with needs_geocoding=TRUE flag
    --with-eircode       Filter to properties with Eircodes (requires --needs-geocoding)
    --apply              Actually update database (default is dry-run)
    --limit N            Process at most N properties
    --county COUNTY      Filter to specific county
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import sqlite3
from datetime import datetime
from typing import Optional, Tuple
from dotenv import load_dotenv

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from county_validator import validate_county

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
AUTOADDRESS_KEY = os.environ.get("AUTOADDRESS_KEY", "")
PROGRESS_DB = "regeocode_autoaddress_progress.db"

# API endpoints
AA_AUTOCOMPLETE = "https://api.autoaddress.com/3.0/autocomplete"
AA_LOOKUP = "https://api.autoaddress.com/3.0/lookup"

# Rate limiting
AA_RATE_LIMIT = 1.0  # 1 request per second (conservative)

# Ireland bounding box
IRELAND_BBOX = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon


class ProgressTracker:
    """Track AutoAddress re-geocoding progress."""

    def __init__(self, db_path: str = PROGRESS_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS autoaddress_log (
                property_id INTEGER PRIMARY KEY,
                old_lat REAL,
                old_lon REAL,
                new_lat REAL,
                new_lon REAL,
                eircode TEXT,
                status TEXT,
                error TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS autoaddress_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                started_at TEXT,
                last_update TEXT,
                processed INTEGER DEFAULT 0,
                succeeded INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                county_validation_rejected INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            INSERT INTO autoaddress_stats (id, started_at, last_update)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_update = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def is_processed(self, property_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "SELECT 1 FROM autoaddress_log WHERE property_id = ?",
            (property_id,)
        ).fetchone()
        conn.close()
        return result is not None

    def log_result(self, property_id: int, old_coords: Tuple[float, float],
                   new_coords: Optional[Tuple[float, float]],
                   eircode: Optional[str],
                   status: str, error: str = None, county_validation_failed: bool = False):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO autoaddress_log
            (property_id, old_lat, old_lon, new_lat, new_lon, eircode, status, error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            property_id,
            old_coords[0], old_coords[1],
            new_coords[0] if new_coords else None,
            new_coords[1] if new_coords else None,
            eircode,
            status, error,
            datetime.now().isoformat()
        ))

        if status == 'success':
            conn.execute("UPDATE autoaddress_stats SET succeeded = succeeded + 1, processed = processed + 1")
        elif status == 'failed':
            conn.execute("UPDATE autoaddress_stats SET failed = failed + 1, processed = processed + 1")
            if county_validation_failed:
                conn.execute("UPDATE autoaddress_stats SET county_validation_rejected = county_validation_rejected + 1")

        conn.execute("UPDATE autoaddress_stats SET last_update = ?", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()

    def get_stats(self):
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("""
            SELECT processed, succeeded, failed, county_validation_rejected, started_at, last_update
            FROM autoaddress_stats WHERE id = 1
        """).fetchone()
        conn.close()
        return {
            'processed': result[0],
            'succeeded': result[1],
            'failed': result[2],
            'county_validation_rejected': result[3],
            'started_at': result[4],
            'last_update': result[5]
        }


async def validate_routing_key_distance(pool: asyncpg.Pool, lat: float, lon: float,
                                        eircode: str) -> Tuple[bool, str]:
    """
    Validate coordinates against routing key centroid.
    Returns (is_valid, reason)
    """
    if not eircode or len(eircode.replace(' ', '')) < 3:
        return True, "no_eircode"  # Can't validate without routing key

    routing_key = eircode.replace(' ', '').upper()[:3]

    row = await pool.fetchrow("""
        SELECT lat, lon, property_count
        FROM routing_key_stats
        WHERE routing_key = $1
    """, routing_key)

    if not row or row['property_count'] < 5:
        return True, "routing_key_too_small"  # Not enough data to validate

    centroid_lat, centroid_lon = float(row['lat']), float(row['lon'])
    lat_diff = abs(lat - centroid_lat)
    lon_diff = abs(lon - centroid_lon)

    # ~5km threshold (0.05° lat ≈ 5.5km, 0.08° lon ≈ 5.6km at Ireland latitude)
    if lat_diff < 0.05 and lon_diff < 0.08:
        return True, "routing_key_valid"
    else:
        distance_km = ((lat_diff * 111)**2 + (lon_diff * 85)**2)**0.5
        return False, f"routing_key_distance_{distance_km:.1f}km"


async def geocode_autoaddress(address: str, county: str, eircode: Optional[str],
                              pool: asyncpg.Pool, client: httpx.AsyncClient) -> Optional[Tuple[float, float, str, int]]:
    """
    Geocode using AutoAddress API with comprehensive validation.
    Returns (lat, lon, eircode, quality_score) or None.

    Quality score:
    - 100: Perfect (Ireland + county + routing key validated)
    - 90: Excellent (Ireland + county validated)
    - 80: Good (Ireland validated, no county to check)
    - 70: Acceptable (Ireland validated, county check failed)
    - <70: Rejected
    """
    if not AUTOADDRESS_KEY:
        return None

    query = f"{address}, {county}, Ireland" if county else f"{address}, Ireland"

    try:
        # Step 1: Autocomplete to get candidates
        resp = await client.get(
            AA_AUTOCOMPLETE,
            params={
                "key": AUTOADDRESS_KEY,
                "address": query,
                "limit": 3  # AutoAddress requires 3-30 for autocomplete
            },
            headers={
                "Authorization": f"Bearer {AUTOADDRESS_KEY}",
                "User-Agent": "PPR-regeocode/1.0"
            },
            timeout=10.0
        )
        await asyncio.sleep(1.0 / AA_RATE_LIMIT)  # Rate limit

        if resp.status_code != 200:
            return None

        data = resp.json()
        options = data.get("options", [])

        if not options:
            return None

        # Step 2: Lookup using the best match
        lookup_href = options[0]["link"]["href"]

        resp2 = await client.get(
            lookup_href,
            headers={
                "Authorization": f"Bearer {AUTOADDRESS_KEY}",
                "User-Agent": "PPR-regeocode/1.0"
            },
            timeout=10.0
        )
        await asyncio.sleep(1.0 / AA_RATE_LIMIT)  # Rate limit

        if resp2.status_code != 200:
            return None

        result = resp2.json()

        # Extract coordinates and eircode
        location = result.get("address", {}).get("location", {})
        lat = location.get("latitude")
        lon = location.get("longitude")
        returned_eircode = result.get("address", {}).get("postcode", {}).get("value", "")

        if not lat or not lon:
            return None

        lat, lon = float(lat), float(lon)
        quality_score = 100  # Start with perfect score

        # Validation 1: Ireland bounding box (CRITICAL)
        min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            print(f"  ⚠️  Coordinates outside Ireland: ({lat:.6f}, {lon:.6f})")
            return None  # Hard reject

        # Validation 2: County boundary (if county provided)
        if county:
            is_valid, reason = validate_county(lat, lon, county)
            if not is_valid:
                print(f"  ⚠️  County validation failed: {reason}")
                quality_score = 70  # Downgrade but don't reject

        # Validation 3: Routing key distance (if Eircode available)
        eircode_to_use = returned_eircode or eircode
        if eircode_to_use:
            is_valid, reason = await validate_routing_key_distance(pool, lat, lon, eircode_to_use)
            if not is_valid:
                print(f"  ⚠️  Routing key validation failed: {reason}")
                return None  # Hard reject - Eircode geocodes must be within routing key
            elif reason == "routing_key_valid":
                quality_score = 100  # Perfect validation

        # Return coordinates with quality score
        return (lat, lon, returned_eircode.strip() if returned_eircode else None, quality_score)

    except Exception as e:
        print(f"  AutoAddress error for {query}: {e}")

    return None


async def fetch_properties_needing_geocoding(pool: asyncpg.Pool, limit: int = None,
                                             county: str = None, with_eircode: bool = False) -> list[dict]:
    """Fetch properties flagged as needing geocoding (priority order)."""
    print("Fetching properties needing geocoding...")

    where_clauses = ["needs_geocoding = TRUE"]
    params = []
    idx = 1

    if county:
        where_clauses.append(f"LOWER(county) = LOWER(${idx})")
        params.append(county)
        idx += 1

    if with_eircode:
        where_clauses.append("eircode IS NOT NULL AND eircode != ''")

    where = " AND ".join(where_clauses)
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT id, address, county, eircode, routing_key, price, sale_date
        FROM properties
        WHERE {where}
        ORDER BY
            CASE
                WHEN price > 500000 THEN 1
                WHEN price > 300000 THEN 2
                ELSE 3
            END,
            sale_date DESC,
            price DESC
        {limit_clause}
    """

    rows = await pool.fetch(query, *params)
    return [dict(row) for row in rows]


async def fetch_centroid_properties(pool: asyncpg.Pool, limit: int = None,
                                   county: str = None) -> list[dict]:
    """Fetch properties at centroid coordinates."""
    print("Fetching properties at centroid coordinates...")

    centroid_coords = await pool.fetch("""
        SELECT latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
    """)

    print(f"Found {len(centroid_coords)} centroid coordinates")

    properties = []
    for coord in centroid_coords:
        where_clauses = [
            "ABS(latitude - $1) < 0.000001",
            "ABS(longitude - $2) < 0.000001"
        ]
        params = [coord["latitude"], coord["longitude"]]
        idx = 3

        if county:
            where_clauses.append(f"LOWER(county) = LOWER(${idx})")
            params.append(county)

        where = " AND ".join(where_clauses)

        rows = await pool.fetch(f"""
            SELECT id, address, county, eircode, latitude, longitude
            FROM properties
            WHERE {where}
            ORDER BY
                CASE WHEN eircode IS NOT NULL THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 500
        """, *params)

        for row in rows:
            properties.append(dict(row))
            if limit and len(properties) >= limit:
                return properties

    return properties


async def regeocode_with_autoaddress(limit: int = None, dry_run: bool = True,
                                     county: str = None, needs_geocoding: bool = False,
                                     with_eircode: bool = False):
    """
    Re-geocode properties using AutoAddress.

    Args:
        limit: Max number of properties to process
        dry_run: If True, don't update database
        county: Filter to specific county
        needs_geocoding: If True, process properties flagged as needs_geocoding
        with_eircode: If True (with needs_geocoding), only process properties with Eircodes
    """
    if not AUTOADDRESS_KEY:
        print("❌ AUTOADDRESS_KEY not set in backend/.env")
        print("\nGet your API key from: https://www.autoaddress.com/")
        print("Add to backend/.env: AUTOADDRESS_KEY=your_key_here")
        return

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    tracker = ProgressTracker()

    try:
        # Fetch properties based on mode
        if needs_geocoding:
            properties = await fetch_properties_needing_geocoding(
                pool, limit=limit, county=county, with_eircode=with_eircode
            )
        else:
            properties = await fetch_centroid_properties(pool, limit=limit, county=county)

        print(f"\n{'='*70}")
        print(f"AUTOADDRESS GEOCODING")
        print(f"{'='*70}")
        print(f"Mode: {'NEEDS GEOCODING' if needs_geocoding else 'CENTROID RE-GEOCODE'}")
        if needs_geocoding and with_eircode:
            print(f"Filter: Properties WITH Eircodes only")
        print(f"Properties to process: {len(properties):,}")
        print(f"Database updates: {'DRY RUN (no changes)' if dry_run else 'APPLY'}")
        print()

        if dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made\n")

        async with httpx.AsyncClient() as client:
            success_count = 0
            failed_count = 0
            routing_key_rejected = 0
            quality_scores = []

            for i, prop in enumerate(properties, 1):
                if tracker.is_processed(prop["id"]):
                    continue

                old_coords = (prop.get("latitude"), prop.get("longitude"))

                result = await geocode_autoaddress(
                    prop["address"],
                    prop["county"] or "",
                    prop.get("eircode"),
                    pool=pool,
                    client=client
                )

                if result:
                    lat, lon, eircode, quality_score = result
                    success_count += 1
                    quality_scores.append(quality_score)
                    tracker.log_result(prop["id"], old_coords, (lat, lon), eircode, f'success_q{quality_score}')

                    if not dry_run:
                        # Update coordinates, eircode, and clear needs_geocoding flag
                        if eircode and not prop.get("eircode"):
                            await pool.execute("""
                                UPDATE properties
                                SET latitude = $1, longitude = $2,
                                    geog = ST_MakePoint($2, $1)::geography,
                                    eircode = $3,
                                    needs_geocoding = FALSE
                                WHERE id = $4
                            """, lat, lon, eircode, prop["id"])
                        else:
                            await pool.execute("""
                                UPDATE properties
                                SET latitude = $1, longitude = $2,
                                    geog = ST_MakePoint($2, $1)::geography,
                                    needs_geocoding = FALSE
                                WHERE id = $3
                            """, lat, lon, prop["id"])

                    if i <= 10 or i % 20 == 0:
                        eircode_str = f"| Eircode: {eircode}" if eircode else ""
                        old_str = f"{old_coords[0]:.6f},{old_coords[1]:.6f} → " if old_coords[0] else ""
                        print(f"  ✓ [{i}/{len(properties)}] {prop['address'][:50]}")
                        print(f"    {old_str}{lat:.6f},{lon:.6f} | Q:{quality_score} {eircode_str}")
                else:
                    failed_count += 1
                    # Check if it was routing key rejection
                    if "routing_key" in str(tracker):
                        routing_key_rejected += 1
                    tracker.log_result(prop["id"], old_coords, None, None, 'failed', 'Validation failed or no result')

                if i % 50 == 0:
                    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                    print(f"\nProgress: {i}/{len(properties)} | Success: {success_count} | Failed: {failed_count} | Avg Quality: {avg_quality:.1f}\n")

        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Processed: {i:,}")
        print(f"✓ Success: {success_count:,} ({100*success_count/i:.1f}%)")
        print(f"✗ Failed: {failed_count:,}")
        if routing_key_rejected > 0:
            print(f"⚠️  Routing key rejected: {routing_key_rejected:,}")

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"\nQuality Score Average: {avg_quality:.1f}/100")
            print(f"  Perfect (100): {sum(1 for q in quality_scores if q == 100)} properties")
            print(f"  Excellent (90-99): {sum(1 for q in quality_scores if 90 <= q < 100)} properties")
            print(f"  Good (80-89): {sum(1 for q in quality_scores if 80 <= q < 90)} properties")
            print(f"  Acceptable (70-79): {sum(1 for q in quality_scores if 70 <= q < 80)} properties")

        stats = tracker.get_stats()
        if stats['county_validation_rejected'] > 0:
            print(f"⚠️  County validation issues: {stats['county_validation_rejected']:,}")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to commit.")

    finally:
        await pool.close()


async def main():
    dry_run = "--apply" not in sys.argv
    needs_geocoding = "--needs-geocoding" in sys.argv
    with_eircode = "--with-eircode" in sys.argv
    limit = None
    county = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]

    await regeocode_with_autoaddress(
        limit=limit,
        dry_run=dry_run,
        county=county,
        needs_geocoding=needs_geocoding,
        with_eircode=with_eircode
    )


if __name__ == "__main__":
    asyncio.run(main())
