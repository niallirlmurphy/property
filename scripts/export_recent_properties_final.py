#!/usr/bin/env python3
"""
Export recent properties from Supabase to CSV.
Uses ONLY columns that actually exist in the properties table.

Usage:
    python3 scripts/export_recent_properties_final.py --months 3
    python3 scripts/export_recent_properties_final.py --months 6 --output recent_6m.csv
    python3 scripts/export_recent_properties_final.py --since 2026-03-01
"""

import psycopg2
import psycopg2.extras
import csv
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')


def export_recent_properties(
    output_file: str,
    months: Optional[int] = None,
    since_date: Optional[str] = None,
    limit: Optional[int] = None
):
    """Export recent properties to CSV."""

    DATABASE_URL = os.environ["DATABASE_URL"]

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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

        # Query properties - ONLY columns that exist in the schema
        # Base schema: id, sale_date, address, county, eircode, price, not_full_market_price,
        #              vat_exclusive, description, size_description, latitude, longitude, geog
        # + address_normalized (from normalize script)
        # + routing_key (generated from eircode)
        # + needs_geocoding (boolean flag)
        # + geocode_quality_issue (boolean flag)
        # + bedrooms, property_type (enrichment columns)
        query = """
            SELECT
                id,
                sale_date,
                address,
                address_normalized,
                county,
                eircode,
                routing_key,
                price,
                not_full_market_price,
                vat_exclusive,
                description,
                size_description,
                latitude,
                longitude,
                needs_geocoding,
                geocode_quality_issue,
                bedrooms,
                property_type
            FROM properties
            WHERE sale_date >= %s
            ORDER BY sale_date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query, (date_filter,))
        rows = cur.fetchall()

        if not rows:
            print(f"✗ No properties found since {date_filter}")
            return

        print(f"Found {len(rows):,} properties")

        # Export to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'sale_date', 'address', 'address_normalized', 'county',
                'eircode', 'routing_key', 'price', 'not_full_market_price',
                'vat_exclusive', 'description', 'size_description',
                'latitude', 'longitude', 'needs_geocoding', 'geocode_quality_issue',
                'bedrooms', 'property_type'
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
        quality_issues = sum(1 for r in rows if r['geocode_quality_issue'])
        with_bedrooms = sum(1 for r in rows if r['bedrooms'] is not None)
        with_type = sum(1 for r in rows if r['property_type'] is not None)
        high_value = sum(1 for r in rows if r['price'] and r['price'] > 500000)
        with_eircode = sum(1 for r in rows if r['eircode'])

        print("Summary:")
        print(f"  Total properties: {len(rows):,}")
        print(f"  Geocoded: {geocoded:,} ({geocoded/len(rows)*100:.1f}%)")
        print(f"  Needs geocoding: {needs_geocoding:,}")
        print(f"  Geocode quality issues: {quality_issues:,}")
        print(f"  With Eircode: {with_eircode:,} ({with_eircode/len(rows)*100:.1f}%)")
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
        cur.close()
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export recent properties to CSV")
    parser.add_argument("--output", default="recent_properties.csv", help="Output CSV file")
    parser.add_argument("--months", type=int, help="Export last N months")
    parser.add_argument("--since", help="Export since date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, help="Limit number of properties")

    args = parser.parse_args()

    export_recent_properties(
        output_file=args.output,
        months=args.months,
        since_date=args.since,
        limit=args.limit
    )
