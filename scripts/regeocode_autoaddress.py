#!/usr/bin/env python3
"""
Re-geocode properties using AutoAddress API.

AutoAddress is an Irish geocoding service with excellent Irish address coverage,
including Eircodes and precise coordinates.

API: https://www.autoaddress.com/
- Autocomplete: Search for addresses
- Lookup: Get full address details including coordinates

Usage:
    python3 scripts/regeocode_autoaddress.py [--apply] [--limit N] [--county COUNTY]
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


async def geocode_autoaddress(address: str, county: str, client: httpx.AsyncClient) -> Optional[Tuple[float, float, str]]:
    """
    Geocode using AutoAddress API.
    Returns (lat, lon, eircode) or None.
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
        eircode = result.get("address", {}).get("postcode", {}).get("value", "")

        if lat and lon:
            lat, lon = float(lat), float(lon)

            # Validate Ireland bounding box
            min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
            if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                print(f"  ⚠️  Coordinates outside Ireland: ({lat:.6f}, {lon:.6f})")
                return None

            # Validate county boundary
            if county:
                is_valid, reason = validate_county(lat, lon, county)
                if not is_valid:
                    print(f"  ⚠️  County validation failed: {reason}")
                    return None

            return (lat, lon, eircode.strip() if eircode else None)

    except Exception as e:
        print(f"  AutoAddress error for {query}: {e}")

    return None


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
                                     county: str = None):
    """Re-geocode properties using AutoAddress."""
    if not AUTOADDRESS_KEY:
        print("❌ AUTOADDRESS_KEY not set in backend/.env")
        print("\nGet your API key from: https://www.autoaddress.com/")
        print("Add to backend/.env: AUTOADDRESS_KEY=your_key_here")
        return

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    tracker = ProgressTracker()

    try:
        properties = await fetch_centroid_properties(pool, limit=limit, county=county)

        print(f"\n{'='*70}")
        print(f"AUTOADDRESS RE-GEOCODING")
        print(f"{'='*70}")
        print(f"Properties to process: {len(properties):,}")
        print(f"Mode: {'DRY RUN' if dry_run else 'APPLY'}")
        print()

        if dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made\n")

        async with httpx.AsyncClient() as client:
            success_count = 0
            failed_count = 0
            county_validation_rejected = 0

            for i, prop in enumerate(properties, 1):
                if tracker.is_processed(prop["id"]):
                    continue

                old_coords = (prop["latitude"], prop["longitude"])

                result = await geocode_autoaddress(
                    prop["address"],
                    prop["county"] or "",
                    client=client
                )

                if result:
                    lat, lon, eircode = result
                    success_count += 1
                    tracker.log_result(prop["id"], old_coords, (lat, lon), eircode, 'success')

                    if not dry_run:
                        # Update coordinates and eircode
                        if eircode and not prop["eircode"]:
                            await pool.execute("""
                                UPDATE properties
                                SET latitude = $1, longitude = $2,
                                    geog = ST_MakePoint($2, $1)::geography,
                                    eircode = $3
                                WHERE id = $4
                            """, lat, lon, eircode, prop["id"])
                        else:
                            await pool.execute("""
                                UPDATE properties
                                SET latitude = $1, longitude = $2,
                                    geog = ST_MakePoint($2, $1)::geography
                                WHERE id = $3
                            """, lat, lon, prop["id"])

                    if i <= 10 or i % 20 == 0:
                        eircode_str = f"| Eircode: {eircode}" if eircode else ""
                        print(f"  ✓ [{i}/{len(properties)}] {prop['address'][:50]}")
                        print(f"    {old_coords[0]:.6f},{old_coords[1]:.6f} → {lat:.6f},{lon:.6f} {eircode_str}")
                else:
                    failed_count += 1
                    tracker.log_result(prop["id"], old_coords, None, None, 'failed', 'No result from AutoAddress')

                if i % 50 == 0:
                    print(f"\nProgress: {i}/{len(properties)} | Success: {success_count} | Failed: {failed_count}\n")

        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Processed: {i:,}")
        print(f"✓ Success: {success_count:,} ({100*success_count/i:.1f}%)")
        print(f"✗ Failed: {failed_count:,}")

        stats = tracker.get_stats()
        if stats['county_validation_rejected'] > 0:
            print(f"⚠️  County validation rejected: {stats['county_validation_rejected']:,}")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to commit.")

    finally:
        await pool.close()


async def main():
    dry_run = "--apply" not in sys.argv
    limit = None
    county = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]

    await regeocode_with_autoaddress(limit=limit, dry_run=dry_run, county=county)


if __name__ == "__main__":
    asyncio.run(main())
