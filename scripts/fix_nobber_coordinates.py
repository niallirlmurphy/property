#!/usr/bin/env python3
"""
Fix Nobber property coordinates that were geocoded to the wrong location.

Wrong: 53.717143, -7.062706 (near Crossakeel/Edgeworthstown)
Correct: 53.8217, -6.7479 (actual Nobber location)

Usage:
    python3 scripts/fix_nobber_coordinates.py [--dry-run] [--verbose]
"""

import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]

# Wrong coordinate (near Crossakeel)
WRONG_LAT = 53.717143
WRONG_LON = -7.062706

# Correct Nobber coordinates (from Nominatim)
CORRECT_LAT = 53.8217
CORRECT_LON = -6.7479


async def fix_nobber_coordinates(dry_run: bool = True, verbose: bool = False):
    """Fix Nobber properties with wrong coordinates."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    try:
        # Find all properties with wrong coordinates that have "Nobber" in address
        print("Searching for Nobber properties with incorrect coordinates...")

        rows = await pool.fetch("""
            SELECT id, address, county, sale_date, latitude, longitude
            FROM properties
            WHERE address ILIKE '%nobber%'
              AND latitude IS NOT NULL
              AND ABS(latitude - $1) < 0.001
              AND ABS(longitude - $2) < 0.001
            ORDER BY sale_date DESC
        """, WRONG_LAT, WRONG_LON)

        if not rows:
            print("✓ No Nobber properties found with incorrect coordinates")
            return

        print(f"\nFound {len(rows)} Nobber properties with incorrect coordinates:")
        if verbose:
            for r in rows[:10]:
                print(f"  {r['sale_date']}: {r['address']}, {r['county']}")
            if len(rows) > 10:
                print(f"  ... and {len(rows) - 10} more")

        if dry_run:
            print(f"\n[DRY RUN] Would update {len(rows)} properties from:")
            print(f"  ({WRONG_LAT}, {WRONG_LON}) -> ({CORRECT_LAT}, {CORRECT_LON})")
            print("\nRun with --apply to execute the update")
            return

        # Apply the fix
        print(f"\nUpdating {len(rows)} properties to correct coordinates...")

        updated = await pool.execute("""
            UPDATE properties
            SET latitude = $1,
                longitude = $2,
                geog = ST_MakePoint($2, $1)::geography
            WHERE address ILIKE '%nobber%'
              AND latitude IS NOT NULL
              AND ABS(latitude - $3) < 0.001
              AND ABS(longitude - $4) < 0.001
        """, CORRECT_LAT, CORRECT_LON, WRONG_LAT, WRONG_LON)

        count = int(updated.split()[-1])
        print(f"✓ Updated {count} properties to correct Nobber coordinates")

        # Verify the fix
        remaining = await pool.fetchval("""
            SELECT COUNT(*)
            FROM properties
            WHERE address ILIKE '%nobber%'
              AND latitude IS NOT NULL
              AND ABS(latitude - $1) < 0.001
              AND ABS(longitude - $2) < 0.001
        """, WRONG_LAT, WRONG_LON)

        if remaining == 0:
            print("✓ All Nobber properties now have correct coordinates")
        else:
            print(f"⚠️  {remaining} Nobber properties still have incorrect coordinates")

        # Show updated distribution
        print("\nNobber coordinate distribution after fix:")
        coords = await pool.fetch("""
            SELECT
                ROUND(latitude::numeric, 4) as lat,
                ROUND(longitude::numeric, 4) as lon,
                COUNT(*) as count
            FROM properties
            WHERE address ILIKE '%nobber%'
              AND latitude IS NOT NULL
            GROUP BY ROUND(latitude::numeric, 4), ROUND(longitude::numeric, 4)
            ORDER BY count DESC
        """)
        for c in coords:
            marker = "✓" if abs(c['lat'] - CORRECT_LAT) < 0.01 else "✗"
            print(f"  {marker} ({c['lat']}, {c['lon']}): {c['count']} properties")

    finally:
        await pool.close()


async def main():
    dry_run = "--apply" not in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    if dry_run:
        print("Running in DRY RUN mode (no changes will be made)")
        print("Add --apply flag to execute the update\n")
    else:
        print("⚠️  APPLYING CHANGES TO DATABASE\n")

    await fix_nobber_coordinates(dry_run=dry_run, verbose=verbose)


if __name__ == "__main__":
    asyncio.run(main())
