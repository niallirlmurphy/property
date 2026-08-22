#!/usr/bin/env python3
"""
Export recent properties from Supabase to CSV.

Usage:
    python3 scripts/export_recent_properties.py --months 3
    python3 scripts/export_recent_properties.py --months 6 --output recent_6m.csv
    python3 scripts/export_recent_properties.py --since 2026-03-01
"""

import asyncpg
import asyncio
import csv
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')


async def export_recent_properties(
    output_file: str,
    months: Optional[int] = None,
    since_date: Optional[str] = None,
    limit: Optional[int] = None
):
    """Export recent properties to CSV."""

    DATABASE_URL = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Calculate date filter
        if since_date:
            date_filter = since_date
        elif months:
            cutoff = datetime.now() - timedelta(days=30 * months)
            date_filter = cutoff.strftime('%Y-%m-%d')
        else:
            # Default to last 3 months
            cutoff = datetime.now() - timedelta(days=90)
            date_filter = cutoff.strftime('%Y-%m-%d')

        print(f"Exporting properties with sale_date >= {date_filter}...")

        # Query properties
        query = """
            SELECT
                id,
                address,
                address_normalized,
                county,
                eircode,
                routing_key,
                sale_date,
                price,
                not_full_market_price,
                vat_exclusive,
                description_of_property,
                property_size_description,
                latitude,
                longitude,
                geocode_quality,
                geocode_source,
                needs_geocoding,
                bedrooms,
                property_type
            FROM properties
            WHERE sale_date >= $1
            ORDER BY sale_date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        rows = await conn.fetch(query, date_filter)

        if not rows:
            print(f"✗ No properties found since {date_filter}")
            return

        print(f"Found {len(rows):,} properties")

        # Export to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'address', 'address_normalized', 'county', 'eircode', 'routing_key',
                'sale_date', 'price', 'not_full_market_price', 'vat_exclusive',
                'description_of_property', 'property_size_description',
                'latitude', 'longitude', 'geocode_quality', 'geocode_source',
                'needs_geocoding', 'bedrooms', 'property_type'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                writer.writerow(dict(row))

        print(f"✓ Exported {len(rows):,} properties to {output_file}")
        print()

        # Statistics
        geocoded = sum(1 for r in rows if r['latitude'] is not None)
        needs_geocoding = sum(1 for r in rows if r['needs_geocoding'])
        with_bedrooms = sum(1 for r in rows if r['bedrooms'] is not None)
        with_type = sum(1 for r in rows if r['property_type'] is not None)
        high_value = sum(1 for r in rows if r['price'] and r['price'] > 500000)

        print("Summary:")
        print(f"  Total properties: {len(rows):,}")
        print(f"  Geocoded: {geocoded:,} ({geocoded/len(rows)*100:.1f}%)")
        print(f"  Needs geocoding: {needs_geocoding:,}")
        print(f"  With bedrooms: {with_bedrooms:,} ({with_bedrooms/len(rows)*100:.1f}%)")
        print(f"  With property type: {with_type:,} ({with_type/len(rows)*100:.1f}%)")
        print(f"  High-value (>€500k): {high_value:,}")
        print()
        print(f"Date range:")
        if rows:
            dates = [r['sale_date'] for r in rows if r['sale_date']]
            if dates:
                print(f"  Earliest: {min(dates)}")
                print(f"  Latest: {max(dates)}")

    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export recent properties to CSV")
    parser.add_argument("--output", default="recent_properties.csv", help="Output CSV file")
    parser.add_argument("--months", type=int, help="Export last N months")
    parser.add_argument("--since", help="Export since date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, help="Limit number of properties")

    args = parser.parse_args()

    asyncio.run(export_recent_properties(
        output_file=args.output,
        months=args.months,
        since_date=args.since,
        limit=args.limit
    ))
