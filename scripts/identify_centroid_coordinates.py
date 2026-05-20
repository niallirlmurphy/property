#!/usr/bin/env python3
"""
Identify properties geocoded to county/town centroids rather than actual addresses.

These are coordinates shared by 100+ distinct addresses, indicating geocoding
fell back to a generic location rather than finding the specific address.

Marks suspect properties by setting a flag or exports a list for re-geocoding.

Usage:
    python3 scripts/identify_centroid_coordinates.py [--mark] [--export CSV] [--threshold N]
"""

import asyncio
import asyncpg
import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]

# Default: coordinates with 100+ distinct addresses are likely centroids
DEFAULT_THRESHOLD = 100


async def identify_centroid_coordinates(threshold: int = DEFAULT_THRESHOLD):
    """Find coordinates that are likely county/town centroids."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    try:
        print(f"Searching for coordinates with {threshold}+ distinct addresses...")

        rows = await pool.fetch("""
            SELECT
                latitude,
                longitude,
                COUNT(DISTINCT address) as distinct_addresses,
                COUNT(*) as total_sales,
                COUNT(DISTINCT county) as counties,
                ARRAY_AGG(DISTINCT county) FILTER (WHERE county IS NOT NULL) as county_list,
                MIN(sale_date) as earliest_sale,
                MAX(sale_date) as latest_sale
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= $1
            ORDER BY COUNT(DISTINCT address) DESC
        """, threshold)

        if not rows:
            print(f"✓ No coordinates found with {threshold}+ distinct addresses")
            return []

        print(f"\nFound {len(rows)} centroid coordinates:")
        print(f"{'Coordinate':<30} {'Addresses':<12} {'Sales':<10} {'Counties':<10}")
        print("=" * 65)

        total_addresses = 0
        total_sales = 0

        for r in rows[:20]:  # Show top 20
            coord = f"({r['latitude']:.6f}, {r['longitude']:.6f})"
            counties_str = ", ".join(r['county_list'][:3]) if r['county_list'] else "None"
            if r['counties'] > 3:
                counties_str += f" +{r['counties'] - 3}"

            print(f"{coord:<30} {r['distinct_addresses']:<12} {r['total_sales']:<10} {counties_str}")
            total_addresses += r['distinct_addresses']
            total_sales += r['total_sales']

        if len(rows) > 20:
            print(f"... and {len(rows) - 20} more centroid coordinates")

        print(f"\n{'='*65}")
        print(f"TOTAL: {len(rows)} centroid coordinates")
        print(f"       {total_addresses:,} distinct addresses affected")
        print(f"       {total_sales:,} total sales with centroid coordinates")

        return rows

    finally:
        await pool.close()


async def mark_centroid_properties(threshold: int = DEFAULT_THRESHOLD, dry_run: bool = True):
    """
    Add a quality flag column to mark properties with centroid coordinates.

    Creates a 'geocode_quality' column if it doesn't exist:
    - 'ok': normal geocoding
    - 'centroid': likely county/town centroid, needs re-geocoding
    """
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    try:
        # Check if column exists
        column_exists = await pool.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'properties'
                  AND column_name = 'geocode_quality'
            )
        """)

        if not column_exists:
            print("Creating geocode_quality column...")
            if not dry_run:
                await pool.execute("""
                    ALTER TABLE properties
                    ADD COLUMN geocode_quality TEXT DEFAULT 'ok'
                """)
                await pool.execute("""
                    CREATE INDEX idx_properties_geocode_quality
                    ON properties(geocode_quality)
                    WHERE geocode_quality != 'ok'
                """)
                print("✓ Column created with index")
            else:
                print("[DRY RUN] Would create geocode_quality column")

        # Find centroid coordinates
        print(f"\nFinding coordinates with {threshold}+ distinct addresses...")

        centroid_coords = await pool.fetch("""
            SELECT latitude, longitude, COUNT(DISTINCT address) as addr_count
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= $1
        """, threshold)

        print(f"Found {len(centroid_coords)} centroid coordinates")

        if dry_run:
            # Count affected properties
            total = 0
            for coord in centroid_coords[:5]:
                count = await pool.fetchval("""
                    SELECT COUNT(*)
                    FROM properties
                    WHERE ABS(latitude - $1) < 0.000001
                      AND ABS(longitude - $2) < 0.000001
                """, coord['latitude'], coord['longitude'])
                total += count

            print(f"\n[DRY RUN] Would mark ~{total:,}+ properties as 'centroid' quality")
            print("Run with --apply to execute the update")
            return

        # Mark properties at centroid coordinates
        print("\nMarking properties with centroid coordinates...")
        marked = 0

        for coord in centroid_coords:
            result = await pool.execute("""
                UPDATE properties
                SET geocode_quality = 'centroid'
                WHERE ABS(latitude - $1) < 0.000001
                  AND ABS(longitude - $2) < 0.000001
                  AND (geocode_quality IS NULL OR geocode_quality = 'ok')
            """, coord['latitude'], coord['longitude'])
            count = int(result.split()[-1])
            marked += count

        print(f"✓ Marked {marked:,} properties with 'centroid' quality flag")

        # Summary stats
        summary = await pool.fetchrow("""
            SELECT
                geocode_quality,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY geocode_quality
            ORDER BY count DESC
        """)

        print("\nGeocoding quality distribution:")
        rows = await pool.fetch("""
            SELECT
                COALESCE(geocode_quality, 'ok') as quality,
                COUNT(*) as count
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY geocode_quality
            ORDER BY count DESC
        """)
        for r in rows:
            print(f"  {r['quality']}: {r['count']:,}")

    finally:
        await pool.close()


async def export_for_regeocoding(threshold: int = DEFAULT_THRESHOLD, output_file: str = None):
    """Export list of properties with centroid coordinates for re-geocoding."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    try:
        print(f"Exporting properties at centroid coordinates (threshold={threshold})...")

        # Find centroid coordinates
        centroid_coords = await pool.fetch("""
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= $1
        """, threshold)

        print(f"Found {len(centroid_coords)} centroid coordinates")

        # Get all properties at those coordinates
        properties = []
        for coord in centroid_coords:
            rows = await pool.fetch("""
                SELECT id, address, county, eircode, latitude, longitude, sale_date
                FROM properties
                WHERE ABS(latitude - $1) < 0.000001
                  AND ABS(longitude - $2) < 0.000001
                ORDER BY sale_date DESC
            """, coord['latitude'], coord['longitude'])
            properties.extend(rows)

        print(f"Exporting {len(properties):,} properties for re-geocoding...")

        if not output_file:
            output_file = f"centroid_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'address', 'county', 'eircode',
                'old_latitude', 'old_longitude', 'sale_date',
                'geocode_priority'
            ])

            for prop in properties:
                # Priority: properties with eircode are easier to re-geocode
                priority = 'high' if prop['eircode'] else 'medium'
                writer.writerow([
                    prop['id'],
                    prop['address'],
                    prop['county'],
                    prop['eircode'] or '',
                    prop['latitude'],
                    prop['longitude'],
                    prop['sale_date'],
                    priority
                ])

        print(f"✓ Exported to {output_file}")

        # Summary by county
        print("\nProperties needing re-geocoding by county:")
        county_stats = await pool.fetch("""
            WITH centroid_coords AS (
                SELECT latitude, longitude
                FROM properties
                WHERE latitude IS NOT NULL
                GROUP BY latitude, longitude
                HAVING COUNT(DISTINCT address) >= $1
            )
            SELECT
                p.county,
                COUNT(*) as count,
                COUNT(p.eircode) FILTER (WHERE p.eircode IS NOT NULL AND p.eircode != '') as with_eircode
            FROM properties p
            INNER JOIN centroid_coords c
                ON ABS(p.latitude - c.latitude) < 0.000001
                AND ABS(p.longitude - c.longitude) < 0.000001
            WHERE p.county IS NOT NULL
            GROUP BY p.county
            ORDER BY count DESC
            LIMIT 15
        """, threshold)

        for stat in county_stats:
            pct = 100.0 * stat['with_eircode'] / stat['count'] if stat['count'] > 0 else 0
            print(f"  {stat['county']:<20} {stat['count']:>6,} properties ({pct:>4.1f}% with eircode)")

        return output_file

    finally:
        await pool.close()


async def main():
    threshold = DEFAULT_THRESHOLD
    mark = "--mark" in sys.argv
    export = "--export" in sys.argv
    apply = "--apply" in sys.argv

    # Parse threshold
    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = int(sys.argv[i + 1])

    # Parse export filename
    export_file = None
    if export:
        for i, arg in enumerate(sys.argv):
            if arg == "--export" and i + 1 < len(sys.argv):
                next_arg = sys.argv[i + 1]
                if not next_arg.startswith("--"):
                    export_file = next_arg

    print(f"Centroid Coordinate Detection (threshold: {threshold}+ addresses)\n")

    if not mark and not export:
        # Just identify and report
        await identify_centroid_coordinates(threshold)
        print("\nNext steps:")
        print("  --mark    : Add geocode_quality='centroid' flag to these properties")
        print("  --export  : Export CSV for re-geocoding")
        print("  --threshold N : Change detection threshold (default 100)")
    elif mark:
        await mark_centroid_properties(threshold, dry_run=not apply)
    elif export:
        output = await export_for_regeocoding(threshold, export_file)
        print(f"\nUse this file to re-geocode properties:")
        print(f"  python3 scripts/regeocode_from_csv.py {output}")


if __name__ == "__main__":
    asyncio.run(main())
