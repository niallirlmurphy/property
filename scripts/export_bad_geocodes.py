#!/usr/bin/env python3
"""
Export properties with geocoding quality issues for bulk re-geocoding.

Properties are flagged when:
- Coordinates are >5km from routing key centroid
- Indicates bad geocoding data needing correction

Output CSV can be sent to:
- Mapbox Geocoding API (batch)
- Autoaddress reverse geocoding
- Salesforce Maps geocoding
- Manual review

Priority order:
1. High-value properties (>€500k)
2. Recent sales
3. Properties with routing keys (can validate results)
"""

import asyncpg
import asyncio
import csv
import os
from datetime import datetime


async def export_bad_geocodes(output_file: str = "bad_geocodes.csv", limit: int = None):
    """Export flagged properties to CSV for re-geocoding."""

    DATABASE_URL = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Get flagged properties with priority sorting
        query = """
            SELECT
                id,
                address,
                county,
                eircode,
                routing_key,
                latitude as bad_latitude,
                longitude as bad_longitude,
                sale_date,
                price,
                distance_from_centroid_km
            FROM properties_needing_regeocode
        """

        if limit:
            query += f" LIMIT {limit}"

        rows = await conn.fetch(query)

        if not rows:
            print("✓ No properties flagged for re-geocoding")
            return

        # Export to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'address', 'county', 'eircode', 'routing_key',
                'bad_latitude', 'bad_longitude',
                'sale_date', 'price', 'distance_from_centroid_km',
                'new_latitude', 'new_longitude', 'geocode_source'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    'id': row['id'],
                    'address': row['address'],
                    'county': row['county'],
                    'eircode': row['eircode'],
                    'routing_key': row['routing_key'],
                    'bad_latitude': row['bad_latitude'],
                    'bad_longitude': row['bad_longitude'],
                    'sale_date': row['sale_date'],
                    'price': row['price'],
                    'distance_from_centroid_km': f"{row['distance_from_centroid_km']:.2f}" if row['distance_from_centroid_km'] else '',
                    'new_latitude': '',  # To be filled by re-geocoding service
                    'new_longitude': '',
                    'geocode_source': ''
                })

        print(f"✓ Exported {len(rows)} properties to {output_file}")
        print()
        print("Summary:")

        # Statistics
        high_value = sum(1 for r in rows if r['price'] > 500000)
        recent = sum(1 for r in rows if r['sale_date'] and r['sale_date'].year >= 2024)
        with_routing_key = sum(1 for r in rows if r['routing_key'])

        print(f"  High-value (>€500k): {high_value}")
        print(f"  Recent sales (2024+): {recent}")
        print(f"  With routing key: {with_routing_key}")
        print()
        print(f"Next steps:")
        print(f"  1. Send {output_file} to re-geocoding service")
        print(f"  2. Fill new_latitude, new_longitude, geocode_source columns")
        print(f"  3. Run: python3 scripts/import_corrected_geocodes.py {output_file}")

    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export properties with bad geocoding for correction")
    parser.add_argument("--output", default="bad_geocodes.csv", help="Output CSV file")
    parser.add_argument("--limit", type=int, help="Limit number of properties to export")

    args = parser.parse_args()

    asyncio.run(export_bad_geocodes(args.output, args.limit))
