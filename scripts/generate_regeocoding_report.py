#!/usr/bin/env python3
"""
Generate a prioritized report of addresses that need re-geocoding.

Prioritization criteria:
1. HIGH: Properties at centroid coordinates (100+ addresses same point)
2. MEDIUM: Properties with suspicious clustering (10-99 addresses same point)
3. LOW: Properties with missing coordinates but have eircode
4. VERIFY: Recent sales (last 2 years) that may have wrong coordinates

Usage:
    python3 scripts/generate_regeocoding_report.py [--output REPORT.csv] [--limit N]
"""

import asyncio
import asyncpg
import os
import sys
import csv
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]


class RegeocodingReport:
    def __init__(self):
        self.high_priority = []    # Centroid coordinates
        self.medium_priority = []  # Suspicious clustering
        self.low_priority = []     # Missing coords with eircode
        self.verify_priority = []  # Recent sales, possible errors

    def total_count(self):
        return (len(self.high_priority) + len(self.medium_priority) +
                len(self.low_priority) + len(self.verify_priority))


async def find_centroid_properties(pool: asyncpg.Pool, threshold: int = 100):
    """Find properties at centroid coordinates (HIGH priority)."""
    print(f"Finding centroid properties (threshold={threshold})...")

    # Find coordinates with many distinct addresses
    centroid_coords = await pool.fetch("""
        SELECT
            latitude,
            longitude,
            COUNT(DISTINCT address) as distinct_addresses,
            COUNT(*) as total_sales
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= $1
        ORDER BY COUNT(DISTINCT address) DESC
    """, threshold)

    print(f"  Found {len(centroid_coords)} centroid coordinates")

    properties = []
    for coord in centroid_coords:
        # Get sample of properties at this coordinate
        rows = await pool.fetch("""
            SELECT
                id, address, county, eircode, latitude, longitude,
                sale_date, price
            FROM properties
            WHERE ABS(latitude - $1) < 0.000001
              AND ABS(longitude - $2) < 0.000001
            ORDER BY
                -- Prioritize recent sales and those with eircodes
                CASE WHEN eircode IS NOT NULL AND eircode != '' THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 1000  -- Cap per coordinate to avoid memory issues
        """, coord['latitude'], coord['longitude'])

        for row in rows:
            properties.append({
                'priority': 'HIGH',
                'reason': f"Centroid: {coord['distinct_addresses']} addresses at same point",
                'id': row['id'],
                'address': row['address'],
                'county': row['county'],
                'eircode': row['eircode'] or '',
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'sale_date': row['sale_date'],
                'price': row['price'],
            })

    print(f"  {len(properties):,} HIGH priority properties")
    return properties


async def find_suspicious_clusters(pool: asyncpg.Pool, min_threshold: int = 10, max_threshold: int = 99):
    """Find properties with suspicious clustering (MEDIUM priority)."""
    print(f"Finding suspicious clusters ({min_threshold}-{max_threshold} addresses)...")

    cluster_coords = await pool.fetch("""
        SELECT
            latitude,
            longitude,
            COUNT(DISTINCT address) as distinct_addresses
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) BETWEEN $1 AND $2
        ORDER BY COUNT(DISTINCT address) DESC
        LIMIT 500  -- Cap to avoid too many medium priority items
    """, min_threshold, max_threshold)

    print(f"  Found {len(cluster_coords)} suspicious clusters")

    properties = []
    for coord in cluster_coords[:200]:  # Process top 200 clusters
        rows = await pool.fetch("""
            SELECT
                id, address, county, eircode, latitude, longitude,
                sale_date, price
            FROM properties
            WHERE ABS(latitude - $1) < 0.000001
              AND ABS(longitude - $2) < 0.000001
            ORDER BY
                CASE WHEN eircode IS NOT NULL AND eircode != '' THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 100
        """, coord['latitude'], coord['longitude'])

        for row in rows:
            properties.append({
                'priority': 'MEDIUM',
                'reason': f"Cluster: {coord['distinct_addresses']} addresses at same point",
                'id': row['id'],
                'address': row['address'],
                'county': row['county'],
                'eircode': row['eircode'] or '',
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'sale_date': row['sale_date'],
                'price': row['price'],
            })

    print(f"  {len(properties):,} MEDIUM priority properties")
    return properties


async def find_missing_coordinates(pool: asyncpg.Pool, limit: int = 5000):
    """Find properties with missing coordinates but have eircode (LOW priority)."""
    print("Finding properties with missing coordinates but have eircode...")

    rows = await pool.fetch("""
        SELECT
            id, address, county, eircode, sale_date, price
        FROM properties
        WHERE latitude IS NULL
          AND eircode IS NOT NULL
          AND eircode != ''
        ORDER BY sale_date DESC
        LIMIT $1
    """, limit)

    properties = []
    for row in rows:
        properties.append({
            'priority': 'LOW',
            'reason': 'Missing coordinates (has eircode)',
            'id': row['id'],
            'address': row['address'],
            'county': row['county'],
            'eircode': row['eircode'],
            'latitude': None,
            'longitude': None,
            'sale_date': row['sale_date'],
            'price': row['price'],
        })

    print(f"  {len(properties):,} LOW priority properties")
    return properties


async def find_verification_candidates(pool: asyncpg.Pool, limit: int = 1000):
    """
    Find recent sales (last 2 years) that might have wrong coordinates.

    These are properties in place names that show scattered geocoding
    (from the quality assessment).
    """
    print("Finding recent sales for verification...")

    cutoff_date = datetime.now() - timedelta(days=730)  # 2 years ago

    # Known problematic place names from assessment
    problematic_places = [
        'MILTOWN', 'Glaslough', 'Waterville', 'Milltown', 'HOLIDAY VILLAGE',
        'BLACKROCK RD', 'LACKEN', 'Conna', 'CHURCH ST', 'THE GLEN',
        'MAIN ST', 'JOHN ST', 'JAMES ST', 'Robswall', 'MAIN STREET',
        'MILL RD', 'PARKLANDS', 'BRIDGE ST', 'CORK STREET', 'RIVERSTOWN',
    ]

    properties = []
    for place in problematic_places[:10]:  # Check top 10 to avoid too many results
        rows = await pool.fetch("""
            SELECT
                id, address, county, eircode, latitude, longitude,
                sale_date, price
            FROM properties
            WHERE address ILIKE $1
              AND latitude IS NOT NULL
              AND sale_date >= $2
            ORDER BY sale_date DESC
            LIMIT 20
        """, f"%{place}%", cutoff_date)

        for row in rows:
            properties.append({
                'priority': 'VERIFY',
                'reason': f'Recent sale in problematic area: {place}',
                'id': row['id'],
                'address': row['address'],
                'county': row['county'],
                'eircode': row['eircode'] or '',
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'sale_date': row['sale_date'],
                'price': row['price'],
            })

        if len(properties) >= limit:
            break

    print(f"  {len(properties):,} VERIFY priority properties")
    return properties


async def generate_report(output_file: str = None, limit_per_priority: dict = None):
    """Generate comprehensive re-geocoding report."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    if limit_per_priority is None:
        limit_per_priority = {
            'HIGH': 10000,
            'MEDIUM': 5000,
            'LOW': 5000,
            'VERIFY': 1000,
        }

    try:
        report = RegeocodingReport()

        # Gather all priority categories
        report.high_priority = await find_centroid_properties(pool, threshold=100)
        report.high_priority = report.high_priority[:limit_per_priority['HIGH']]

        report.medium_priority = await find_suspicious_clusters(pool, min_threshold=10, max_threshold=99)
        report.medium_priority = report.medium_priority[:limit_per_priority['MEDIUM']]

        report.low_priority = await find_missing_coordinates(pool, limit=limit_per_priority['LOW'])

        report.verify_priority = await find_verification_candidates(pool, limit=limit_per_priority['VERIFY'])

        # Generate output
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"regeocoding_report_{timestamp}.csv"

        print(f"\nGenerating report: {output_file}")

        all_properties = (
            report.high_priority +
            report.medium_priority +
            report.low_priority +
            report.verify_priority
        )

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'priority', 'reason', 'id', 'address', 'county', 'eircode',
                'old_latitude', 'old_longitude', 'sale_date', 'price'
            ])
            writer.writeheader()

            for prop in all_properties:
                writer.writerow({
                    'priority': prop['priority'],
                    'reason': prop['reason'],
                    'id': prop['id'],
                    'address': prop['address'],
                    'county': prop['county'],
                    'eircode': prop['eircode'],
                    'old_latitude': prop['latitude'] if prop['latitude'] is not None else '',
                    'old_longitude': prop['longitude'] if prop['longitude'] is not None else '',
                    'sale_date': prop['sale_date'],
                    'price': prop['price'],
                })

        print(f"✓ Report generated: {output_file}")

        # Summary statistics
        print("\n" + "="*70)
        print("RE-GEOCODING REPORT SUMMARY")
        print("="*70)

        print(f"\nTotal properties needing attention: {len(all_properties):,}")
        print(f"  HIGH priority (centroids):         {len(report.high_priority):,}")
        print(f"  MEDIUM priority (clusters):        {len(report.medium_priority):,}")
        print(f"  LOW priority (missing coords):     {len(report.low_priority):,}")
        print(f"  VERIFY priority (recent/suspect):  {len(report.verify_priority):,}")

        # Break down by county
        print("\nTop counties needing re-geocoding:")
        county_counts = defaultdict(int)
        for prop in all_properties:
            if prop.get('county'):
                county_counts[prop['county']] += 1

        for county, count in sorted(county_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {county:<20} {count:>6,} properties")

        # Break down high priority by reason
        print("\nHigh priority reasons:")
        reason_counts = defaultdict(int)
        for prop in report.high_priority:
            reason_counts[prop['reason']] += 1

        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            # Truncate long reasons
            reason_short = reason[:60] + "..." if len(reason) > 60 else reason
            print(f"  {reason_short:<63} {count:>6,}")

        print("\n" + "="*70)
        print("\nNext steps:")
        print(f"  1. Review {output_file}")
        print("  2. Run: python3 scripts/regeocode_from_csv.py {output_file}")
        print("  3. Re-import geocoded data to database")

        return output_file

    finally:
        await pool.close()


async def main():
    output_file = None
    limit = None

    # Parse arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
        elif arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    print("Generating Re-geocoding Priority Report\n")

    limits = None
    if limit:
        # Distribute limit across priorities
        limits = {
            'HIGH': int(limit * 0.5),
            'MEDIUM': int(limit * 0.25),
            'LOW': int(limit * 0.15),
            'VERIFY': int(limit * 0.1),
        }
        print(f"Limiting to ~{limit} total properties\n")

    await generate_report(output_file, limit_per_priority=limits)


if __name__ == "__main__":
    asyncio.run(main())
