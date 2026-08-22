#!/usr/bin/env python3
"""
Create batch 5 enrichment input: 10k highest priority unenriched properties.

Priority: price DESC (highest price first), then sale_date DESC (most recent first)
"""

import os
import json
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    print("Creating Batch 5 Input...")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Fetch 10k highest priority unenriched properties
    cur.execute("""
        SELECT
            id,
            address,
            county,
            price,
            sale_date
        FROM properties
        WHERE (bedrooms IS NULL OR property_type IS NULL)
        AND price >= 500000
        AND sale_date >= '2020-01-01'
        AND address IS NOT NULL
        AND county IS NOT NULL
        ORDER BY price DESC, sale_date DESC
        LIMIT 10000
    """)

    rows = cur.fetchall()

    properties = []
    for row in rows:
        properties.append({
            'id': row[0],
            'address': row[1],
            'county': row[2],
            'price': float(row[3]),
            'sale_date': row[4].isoformat() if row[4] else None
        })

    # Write to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'enrichment_batch5_input_{timestamp}.json'

    with open(output_file, 'w') as f:
        json.dump(properties, f, indent=2)

    print(f"✅ Created {output_file}")
    print(f"   Properties: {len(properties):,}")
    print(f"   Price range: €{properties[-1]['price']:,.0f} - €{properties[0]['price']:,.0f}")
    print(f"   Date range: {properties[-1]['sale_date']} to {properties[0]['sale_date']}")
    print()
    print("Start enrichment with:")
    print(f"  python3 scripts/enrich_offline_batch.py --input {output_file}")

    conn.close()

if __name__ == '__main__':
    main()
