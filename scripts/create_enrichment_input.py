#!/usr/bin/env python3
"""
Create input file for offline enrichment from database.
Run this when you have database connectivity.

Usage:
    python3 scripts/create_enrichment_input.py --months 3 --limit 500
"""

import psycopg2
import json
import os
import argparse
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description='Export properties for offline enrichment')
    parser.add_argument('--months', type=int, default=3,
                       help='Properties from last N months (default: 3)')
    parser.add_argument('--limit', type=int, default=500,
                       help='Maximum properties to export (default: 500)')
    parser.add_argument('--output', default='enrichment_input.json',
                       help='Output file (default: enrichment_input.json)')
    parser.add_argument('--min-price', type=int, default=200000,
                       help='Minimum price (default: 200000)')

    args = parser.parse_args()

    load_dotenv('backend/.env')
    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in backend/.env")
        return

    try:
        print(f"Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Get properties needing enrichment
        query = '''
            SELECT id, address, county, price
            FROM properties
            WHERE sale_date >= CURRENT_DATE - INTERVAL '%s months'
              AND (bedrooms IS NULL OR property_type IS NULL)
              AND price >= %s
            ORDER BY price DESC, sale_date DESC
            LIMIT %s
        '''

        print(f"Fetching properties from last {args.months} months (min price: €{args.min_price:,})...")
        cur.execute(query, (args.months, args.min_price, args.limit))

        properties = []
        for row in cur.fetchall():
            properties.append({
                'id': row[0],
                'address': row[1],
                'county': row[2],
                'price': row[3]
            })

        conn.close()

        # Save to file
        with open(args.output, 'w') as f:
            json.dump(properties, f, indent=2, default=str)

        print(f"\n✅ Exported {len(properties)} properties to {args.output}")
        print(f"\nNow run:")
        print(f"  python3 scripts/enrich_offline_batch.py --input {args.output} --batch-size 50 --batch-delay 180")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
