#!/usr/bin/env python3
"""
Import enrichment results back to database.

Takes the JSON output from enrich_from_csv.py and updates the database.

Usage:
    python3 scripts/import_enrichment_results.py enrichment_results.json
    python3 scripts/import_enrichment_results.py enrichment_results.json --dry-run
"""

import json
import psycopg2
import psycopg2.extras
import argparse
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

def import_results(input_file, dry_run=False):
    """Import enrichment results to database."""

    # Load results
    print(f"Loading results from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"Loaded {len(results):,} properties")

    # Filter to only those with enrichment data
    enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
    print(f"Found {len(enriched):,} enriched properties")

    if not enriched:
        print("No enriched properties to import!")
        return

    if dry_run:
        print("\nDRY RUN - showing first 10 updates:")
        for r in enriched[:10]:
            print(f"  ID {r['id']}: {r.get('bedrooms', '?')} bed, {r.get('property_type', '?')}")
        print("\nRun without --dry-run to apply updates")
        return

    # Connect to database
    DATABASE_URL = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        print("\nUpdating database...")
        updated = 0

        for r in enriched:
            prop_id = r['id']
            bedrooms = r.get('bedrooms')
            property_type = r.get('property_type')

            # Convert string None to actual None
            if bedrooms == 'None':
                bedrooms = None
            if property_type == 'None':
                property_type = None

            # Update database
            cur.execute("""
                UPDATE properties
                SET bedrooms = %s,
                    property_type = %s
                WHERE id = %s
                  AND (bedrooms IS NULL OR property_type IS NULL)
            """, (bedrooms, property_type, prop_id))

            if cur.rowcount > 0:
                updated += 1
                if updated % 100 == 0:
                    print(f"  Updated {updated:,} properties...")

        conn.commit()
        print(f"\n✓ Successfully updated {updated:,} properties")

        # Show statistics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(bedrooms) as with_bedrooms,
                COUNT(property_type) as with_type,
                ROUND(100.0 * COUNT(bedrooms) / COUNT(*), 1) as pct_bedrooms,
                ROUND(100.0 * COUNT(property_type) / COUNT(*), 1) as pct_type
            FROM properties
        """)
        stats = cur.fetchone()

        print(f"\nDatabase statistics:")
        print(f"  Total properties: {stats[0]:,}")
        print(f"  With bedrooms: {stats[1]:,} ({stats[3]}%)")
        print(f"  With property type: {stats[2]:,} ({stats[4]}%)")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Import enrichment results to database")
    parser.add_argument("input_file", help="JSON file with enrichment results")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without changing database")

    args = parser.parse_args()

    import_results(args.input_file, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
