#!/usr/bin/env python3
"""
Re-geocode HIGH priority properties (those at centroid coordinates).

Strategy:
1. Identify properties at centroid coordinates (100+ addresses per point)
2. Prioritize those with eircodes (easiest to geocode accurately)
3. Use appropriate geocoder per address type:
   - Eircodes: Nominatim (good OSM eircode coverage)
   - Street addresses: Mapbox with county context
   - Fallback: Database token matching
4. Update database with new coordinates
5. Track progress, errors, and success rate

Features:
- Resumable (tracks progress in SQLite)
- Rate-limited (respects API limits)
- Batched by county (efficient processing)
- Dry-run mode (safe testing)

Usage:
    python3 scripts/regeocode_high_priority.py [--apply] [--limit N] [--county COUNTY]
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import time
import sqlite3
import re
from datetime import datetime
from collections import defaultdict
from typing import Optional, Tuple
from dotenv import load_dotenv
from county_validator import validate_county

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")
PROGRESS_DB = "regeocode_progress.db"
USER_AGENT = "PPR-regeocode/1.0 (data quality improvement)"

# Rate limits (requests per second)
NOMINATIM_RATE = 1.0  # 1 request per second (OSM policy)
MAPBOX_RATE = 10.0    # Mapbox allows higher rates

# Geocoding result cache (in-memory, per session)
_geocode_cache = {}


class ProgressTracker:
    """Track re-geocoding progress in SQLite."""

    def __init__(self, db_path: str = PROGRESS_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS regeocode_log (
                property_id INTEGER PRIMARY KEY,
                old_lat REAL,
                old_lon REAL,
                new_lat REAL,
                new_lon REAL,
                method TEXT,
                status TEXT,  -- 'success' | 'failed' | 'skipped'
                error TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                started_at TEXT,
                last_update TEXT,
                processed INTEGER DEFAULT 0,
                succeeded INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0
            )
        """)
        # Initialize or update session
        conn.execute("""
            INSERT INTO session_stats (id, started_at, last_update)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_update = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def is_processed(self, property_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "SELECT 1 FROM regeocode_log WHERE property_id = ?",
            (property_id,)
        ).fetchone()
        conn.close()
        return result is not None

    def log_result(self, property_id: int, old_coords: Tuple[float, float],
                   new_coords: Optional[Tuple[float, float]], method: str,
                   status: str, error: str = None):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO regeocode_log
            (property_id, old_lat, old_lon, new_lat, new_lon, method, status, error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            property_id,
            old_coords[0], old_coords[1],
            new_coords[0] if new_coords else None,
            new_coords[1] if new_coords else None,
            method, status, error,
            datetime.now().isoformat()
        ))

        # Update session stats
        if status == 'success':
            conn.execute("UPDATE session_stats SET succeeded = succeeded + 1, processed = processed + 1")
        elif status == 'failed':
            conn.execute("UPDATE session_stats SET failed = failed + 1, processed = processed + 1")
        elif status == 'skipped':
            conn.execute("UPDATE session_stats SET skipped = skipped + 1, processed = processed + 1")

        conn.execute("UPDATE session_stats SET last_update = ?", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()

    def get_stats(self):
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("""
            SELECT processed, succeeded, failed, skipped, started_at, last_update
            FROM session_stats WHERE id = 1
        """).fetchone()
        conn.close()
        return {
            'processed': result[0],
            'succeeded': result[1],
            'failed': result[2],
            'skipped': result[3],
            'started_at': result[4],
            'last_update': result[5]
        }


async def geocode_nominatim(address: str, county: str, eircode: str,
                            client: httpx.AsyncClient) -> Optional[Tuple[float, float]]:
    """Geocode using Nominatim (best for eircodes and Irish addresses)."""
    # Ireland bounding box for filtering
    IRELAND_BBOX = "-10.7,51.4,-5.4,55.5"  # west, south, east, north

    # Try eircode first if available
    queries = []
    if eircode:
        queries.append(f"{eircode} Ireland")
    queries.append(f"{address}, {county}, Ireland")

    for query in queries:
        # Check cache
        cache_key = f"nominatim:{query}"
        if cache_key in _geocode_cache:
            return _geocode_cache[cache_key]

        try:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 0,
                    "countrycodes": "ie",  # Restrict to Ireland
                    "viewbox": IRELAND_BBOX,
                    "bounded": 1  # Strict bounding box
                },
                headers={"User-Agent": USER_AGENT},
                timeout=10.0
            )
            await asyncio.sleep(NOMINATIM_RATE)  # Rate limit

            if resp.status_code == 200:
                results = resp.json()
                if results:
                    lat, lon = float(results[0]["lat"]), float(results[0]["lon"])

                    # Double-check coordinates are in Ireland
                    if 51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4:
                        # Validate county boundary
                        is_valid, reason = validate_county(lat, lon, county)
                        if is_valid:
                            _geocode_cache[cache_key] = (lat, lon)
                            return (lat, lon)
                        else:
                            print(f"  ⚠️  County validation failed: {reason}")
        except Exception as e:
            print(f"  Nominatim error for {query}: {e}")
            continue

    _geocode_cache[cache_key] = None
    return None


async def geocode_mapbox(address: str, county: str, client: httpx.AsyncClient) -> Optional[Tuple[float, float]]:
    """Geocode using Mapbox (good for street addresses)."""
    if not MAPBOX_TOKEN:
        return None

    query = f"{address}, {county}, Ireland"
    cache_key = f"mapbox:{query}"

    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        resp = await client.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json",
            params={
                "access_token": MAPBOX_TOKEN,
                "country": "ie",
                "limit": 1,
                "types": "address,place,locality"
            },
            timeout=10.0
        )
        await asyncio.sleep(1.0 / MAPBOX_RATE)  # Rate limit

        if resp.status_code == 200:
            data = resp.json()
            if data.get("features"):
                lon, lat = data["features"][0]["center"]
                # Validate county boundary
                is_valid, reason = validate_county(lat, lon, county)
                if is_valid:
                    _geocode_cache[cache_key] = (lat, lon)
                    return (lat, lon)
                else:
                    print(f"  ⚠️  County validation failed: {reason}")
    except Exception as e:
        print(f"  Mapbox error for {query}: {e}")

    _geocode_cache[cache_key] = None
    return None


async def regeocode_property(prop: dict, client: httpx.AsyncClient) -> Optional[Tuple[float, float, str]]:
    """
    Attempt to re-geocode a single property.
    Returns (lat, lon, method) on success, None on failure.
    """
    address = prop["address"]
    county = prop["county"] or ""
    eircode = prop["eircode"] or ""

    # Strategy 1: Nominatim (prioritize if eircode available)
    result = await geocode_nominatim(address, county, eircode, client)
    if result:
        return (*result, "nominatim")

    # Strategy 2: Mapbox (if available)
    if MAPBOX_TOKEN:
        result = await geocode_mapbox(address, county, client)
        if result:
            return (*result, "mapbox")

    return None


async def fetch_high_priority_properties(pool: asyncpg.Pool, limit: int = None,
                                         county: str = None) -> list[dict]:
    """Fetch properties at centroid coordinates (100+ addresses per point)."""
    print("Fetching HIGH priority properties (centroid coordinates)...")

    # Find centroid coordinates
    centroid_coords = await pool.fetch("""
        SELECT latitude, longitude, COUNT(DISTINCT address) as addr_count
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
    """)

    print(f"Found {len(centroid_coords)} centroid coordinates")

    # Fetch properties at those coordinates, prioritizing those with eircodes
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
            idx += 1

        where = " AND ".join(where_clauses)

        rows = await pool.fetch(f"""
            SELECT id, address, county, eircode, latitude, longitude, price, sale_date
            FROM properties
            WHERE {where}
            ORDER BY
                CASE WHEN eircode IS NOT NULL AND eircode != '' THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 1000
        """, *params)

        for row in rows:
            properties.append(dict(row))
            if limit and len(properties) >= limit:
                return properties

    return properties


async def update_property_coordinates(pool: asyncpg.Pool, property_id: int,
                                     new_coords: Tuple[float, float], dry_run: bool = True) -> bool:
    """Update property coordinates in database."""
    if dry_run:
        return True

    try:
        await pool.execute("""
            UPDATE properties
            SET latitude = $1,
                longitude = $2,
                geog = ST_MakePoint($2, $1)::geography
            WHERE id = $3
        """, new_coords[0], new_coords[1], property_id)
        return True
    except Exception as e:
        print(f"  DB update error for property {property_id}: {e}")
        return False


async def regeocode_high_priority(limit: int = None, dry_run: bool = True,
                                  county: str = None):
    """Main re-geocoding function."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
    tracker = ProgressTracker()

    try:
        # Fetch properties needing re-geocoding
        properties = await fetch_high_priority_properties(pool, limit=limit, county=county)

        print(f"\n{'='*70}")
        print(f"RE-GEOCODING HIGH PRIORITY PROPERTIES")
        print(f"{'='*70}")
        print(f"Total properties to process: {len(properties):,}")
        print(f"Mode: {'DRY RUN (no database changes)' if dry_run else 'APPLY (will update database)'}")
        if county:
            print(f"County filter: {county}")
        print()

        # Group by county for reporting
        by_county = defaultdict(int)
        for prop in properties:
            by_county[prop["county"] or "Unknown"] += 1

        print("Properties by county:")
        for cnty, count in sorted(by_county.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {cnty:<20} {count:>6,}")
        print()

        if dry_run:
            print("⚠️  This is a DRY RUN. No changes will be made to the database.")
            print("Add --apply flag to execute updates.\n")

        # Process properties
        success_count = 0
        failed_count = 0
        skipped_count = 0

        async with httpx.AsyncClient() as client:
            for i, prop in enumerate(properties, 1):
                prop_id = prop["id"]
                old_coords = (prop["latitude"], prop["longitude"])

                # Skip if already processed in a previous run
                if tracker.is_processed(prop_id):
                    skipped_count += 1
                    continue

                # Show progress every 10 properties
                if i % 10 == 0:
                    stats = tracker.get_stats()
                    print(f"Progress: {i:,}/{len(properties):,} | "
                          f"Success: {success_count:,} | Failed: {failed_count:,} | "
                          f"Skipped: {skipped_count:,}")

                # Attempt re-geocoding
                result = await regeocode_property(prop, client)

                if result:
                    lat, lon, method = result
                    new_coords = (lat, lon)

                    # Update database
                    if await update_property_coordinates(pool, prop_id, new_coords, dry_run):
                        success_count += 1
                        tracker.log_result(prop_id, old_coords, new_coords, method, 'success')

                        if i <= 5 or (i % 50 == 0):  # Show first few and periodic updates
                            print(f"  ✓ [{method}] {prop['address'][:50]}")
                            print(f"    {old_coords[0]:.6f}, {old_coords[1]:.6f} → {lat:.6f}, {lon:.6f}")
                    else:
                        failed_count += 1
                        tracker.log_result(prop_id, old_coords, None, method, 'failed', 'DB update failed')
                else:
                    failed_count += 1
                    tracker.log_result(prop_id, old_coords, None, 'none', 'failed', 'No geocoder found result')

        # Final summary
        print(f"\n{'='*70}")
        print(f"RE-GEOCODING COMPLETE")
        print(f"{'='*70}")
        print(f"Total processed: {i:,}")
        print(f"✓ Successfully re-geocoded: {success_count:,} ({100*success_count/i:.1f}%)")
        print(f"✗ Failed to geocode: {failed_count:,} ({100*failed_count/i:.1f}%)")
        print(f"⊘ Skipped (already processed): {skipped_count:,}")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes were made to the database")
            print(f"Run with --apply to commit these changes")
        else:
            print(f"\n✓ Database updated with new coordinates")

        print(f"\nProgress log saved to: {PROGRESS_DB}")
        print(f"Query log: sqlite3 {PROGRESS_DB} 'SELECT * FROM regeocode_log LIMIT 10'")

    finally:
        await pool.close()


async def show_stats():
    """Show statistics from previous runs."""
    if not os.path.exists(PROGRESS_DB):
        print("No previous re-geocoding runs found")
        return

    tracker = ProgressTracker()
    stats = tracker.get_stats()

    print(f"\n{'='*70}")
    print(f"RE-GEOCODING STATISTICS")
    print(f"{'='*70}")
    print(f"Started: {stats['started_at']}")
    print(f"Last update: {stats['last_update']}")
    print(f"\nTotal processed: {stats['processed']:,}")
    print(f"  ✓ Succeeded: {stats['succeeded']:,} ({100*stats['succeeded']/max(stats['processed'],1):.1f}%)")
    print(f"  ✗ Failed: {stats['failed']:,} ({100*stats['failed']/max(stats['processed'],1):.1f}%)")
    print(f"  ⊘ Skipped: {stats['skipped']:,}")

    # Show method breakdown
    conn = sqlite3.connect(PROGRESS_DB)
    methods = conn.execute("""
        SELECT method, COUNT(*) as count
        FROM regeocode_log
        WHERE status = 'success'
        GROUP BY method
        ORDER BY count DESC
    """).fetchall()

    if methods:
        print(f"\nSuccess by method:")
        for method, count in methods:
            print(f"  {method}: {count:,}")

    conn.close()


async def main():
    if "--stats" in sys.argv:
        await show_stats()
        return

    dry_run = "--apply" not in sys.argv
    limit = None
    county = None

    # Parse arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]

    if not dry_run:
        print("⚠️  WARNING: This will modify the database!")
        print("Press Ctrl+C within 5 seconds to cancel...")
        try:
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nCancelled")
            return

    await regeocode_high_priority(limit=limit, dry_run=dry_run, county=county)


if __name__ == "__main__":
    asyncio.run(main())
