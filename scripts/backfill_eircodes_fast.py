#!/usr/bin/env python3
"""
Fast Eircode backfill using direct UPDATE statement.

Uses a single SQL UPDATE with subquery instead of Python loops.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fast Eircode backfill')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--apply', action='store_true', help='Apply changes to database')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print('❌ Error: Must specify --dry-run or --apply')
        sys.exit(1)

    load_dotenv('backend/.env')
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    print('=' * 70)
    print('FAST EIRCODE BACKFILL')
    print('=' * 70)
    print(f'Mode: {"DRY RUN" if args.dry_run else "APPLY CHANGES"}')
    print()

    if args.dry_run:
        # Count how many would be updated
        print('📊 Analyzing backfill opportunity...')
        cur.execute('''
            WITH address_eircodes AS (
                -- Addresses with single unique Eircode from 2022+
                SELECT
                    address_normalized,
                    eircode
                FROM properties
                WHERE eircode IS NOT NULL
                  AND sale_date >= '2022-01-01'
                GROUP BY address_normalized, eircode
            ),
            single_eircode_addresses AS (
                -- Only addresses where all recent sales have same Eircode
                SELECT address_normalized, eircode
                FROM address_eircodes
                GROUP BY address_normalized, eircode
                HAVING COUNT(*) = (
                    SELECT COUNT(DISTINCT eircode)
                    FROM address_eircodes ae2
                    WHERE ae2.address_normalized = address_eircodes.address_normalized
                )
            )
            SELECT COUNT(*)
            FROM properties p
            JOIN single_eircode_addresses sea
                ON p.address_normalized = sea.address_normalized
            WHERE p.eircode IS NULL
        ''')

        count = cur.fetchone()[0]
        print(f'   Would update: {count:,} properties')
        print()
        print('✅ Dry run complete. Use --apply to make changes.')

    else:
        # Perform the update
        print('📊 Starting backfill...')
        print('   (This may take 1-2 minutes for the full dataset)')
        print()

        cur.execute('''
            WITH address_eircodes AS (
                -- Addresses with Eircodes from 2022+ sales
                SELECT
                    address_normalized,
                    eircode,
                    COUNT(*) as sale_count
                FROM properties
                WHERE eircode IS NOT NULL
                  AND sale_date >= '2022-01-01'
                GROUP BY address_normalized, eircode
            ),
            single_eircode_addresses AS (
                -- Addresses with exactly one unique Eircode
                SELECT
                    ae.address_normalized,
                    ae.eircode
                FROM address_eircodes ae
                WHERE (
                    SELECT COUNT(DISTINCT eircode)
                    FROM address_eircodes ae2
                    WHERE ae2.address_normalized = ae.address_normalized
                ) = 1
            )
            UPDATE properties
            SET eircode = sea.eircode
            FROM single_eircode_addresses sea
            WHERE properties.address_normalized = sea.address_normalized
              AND properties.eircode IS NULL
        ''')

        updated_count = cur.rowcount
        conn.commit()

        print(f'✅ SUCCESS: Updated {updated_count:,} properties')
        print()

        # Show updated stats
        cur.execute('''
            SELECT
                COUNT(*) as total,
                COUNT(eircode) as with_eircode,
                ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct
            FROM properties
        ''')
        total, with_eircode, pct = cur.fetchone()
        print(f'📊 Overall Eircode coverage: {with_eircode:,} / {total:,} ({pct}%)')

        cur.execute('''
            SELECT
                EXTRACT(YEAR FROM sale_date) as year,
                COUNT(*) as total,
                COUNT(eircode) as with_eircode,
                ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct
            FROM properties
            WHERE sale_date >= '2020-01-01'
            GROUP BY year
            ORDER BY year DESC
        ''')
        print(f'\nCoverage by year:')
        for year, total, with_eircode, pct in cur.fetchall():
            print(f'  {int(year)}: {with_eircode:,} / {total:,} ({pct}%)')

    conn.close()
    print()
    print('=' * 70)

if __name__ == '__main__':
    main()
