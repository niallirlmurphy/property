#!/usr/bin/env python3
"""
Backfill Eircodes from recent sales to older sales of the same property.

Strategy:
1. Find properties with Eircodes from 2022+ (Eircode adoption era)
2. Match by normalized address
3. Copy Eircode to older sales of same property that lack Eircodes
4. Validate: Only copy if single unique Eircode per address (no conflicts)
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Backfill Eircodes from recent sales')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--limit', type=int, help='Limit number of updates (for testing)')
    parser.add_argument('--apply', action='store_true', help='Apply changes to database')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print('❌ Error: Must specify --dry-run or --apply')
        sys.exit(1)

    load_dotenv('backend/.env')
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    print('=' * 70)
    print('EIRCODE BACKFILL SCRIPT')
    print('=' * 70)
    print(f'Mode: {"DRY RUN" if args.dry_run else "APPLY CHANGES"}')
    print(f'Limit: {args.limit if args.limit else "None"}')
    print()

    # Single optimized query: Find all properties that can be backfilled
    print('📊 Finding properties to backfill...')
    cur.execute('''
        WITH recent_eircodes AS (
            -- Find addresses with a single unique Eircode from 2022+
            SELECT
                address_normalized,
                eircode,
                COUNT(*) as source_sale_count,
                MIN(sale_date) as source_earliest,
                MAX(sale_date) as source_latest
            FROM properties
            WHERE eircode IS NOT NULL
              AND sale_date >= '2022-01-01'
            GROUP BY address_normalized, eircode
        ),
        single_eircode_addresses AS (
            -- Only addresses with exactly one unique Eircode
            SELECT address_normalized
            FROM recent_eircodes
            GROUP BY address_normalized
            HAVING COUNT(DISTINCT eircode) = 1
        )
        SELECT
            p.id,
            p.address,
            p.address_normalized,
            p.sale_date,
            p.price,
            re.eircode,
            re.source_sale_count,
            re.source_earliest,
            re.source_latest
        FROM properties p
        JOIN recent_eircodes re ON p.address_normalized = re.address_normalized
        JOIN single_eircode_addresses sea ON p.address_normalized = sea.address_normalized
        WHERE p.eircode IS NULL
        ORDER BY p.price DESC, p.sale_date
    ''' + (f' LIMIT {args.limit}' if args.limit else ''))

    updates_raw = cur.fetchall()
    total_properties = len(updates_raw)

    # Group by address for display
    from collections import defaultdict
    updates_by_addr = defaultdict(list)
    for prop_id, addr, addr_norm, sale_date, price, eircode, src_count, src_earliest, src_latest in updates_raw:
        updates_by_addr[addr_norm].append({
            'id': prop_id,
            'address': addr,
            'sale_date': sale_date,
            'price': price,
            'eircode': eircode,
            'source_count': src_count,
            'source_earliest': src_earliest,
            'source_latest': src_latest
        })

    unique_addresses = len(updates_by_addr)
    print(f'   Found {total_properties:,} properties to update across {unique_addresses:,} addresses')

    # Step 3: Preview or apply changes
    if args.dry_run:
        print(f'\n📋 DRY RUN: Would update {total_properties:,} properties')
        print(f'\nShowing first 20 examples:')

        shown = 0
        for addr_norm, props in list(updates_by_addr.items())[:20]:
            prop = props[0]  # Show first property from this address
            if shown >= 20:
                break

            print(f'\n  Property ID {prop["id"]}:')
            print(f'    Address: {prop["address"][:70]}')
            print(f'    Sold: {prop["sale_date"]} for €{prop["price"]:,}')
            print(f'    Would add Eircode: {prop["eircode"]}')
            print(f'    (verified from {prop["source_count"]} sales {prop["source_earliest"]} to {prop["source_latest"]})')
            if len(props) > 1:
                print(f'    + {len(props)-1} more sale(s) of this property')
            shown += 1

        print(f'\n✅ Dry run complete. Use --apply to make changes.')

    else:
        print(f'\n✏️  APPLYING CHANGES to {total_properties:,} properties...')

        # Batch update by Eircode for efficiency
        eircode_to_ids = defaultdict(list)
        for props in updates_by_addr.values():
            eircode = props[0]['eircode']
            for prop in props:
                eircode_to_ids[eircode].append(prop['id'])

        updated_count = 0
        error_count = 0

        for i, (eircode, property_ids) in enumerate(eircode_to_ids.items(), 1):
            try:
                cur.execute('''
                    UPDATE properties
                    SET eircode = %s
                    WHERE id = ANY(%s)
                      AND eircode IS NULL
                ''', (eircode, property_ids))

                affected = cur.rowcount
                updated_count += affected

                if i % 100 == 0:
                    print(f'   Progress: {updated_count:,} / {total_properties:,} properties updated ({i:,} Eircodes)')

            except Exception as e:
                error_count += 1
                print(f'   ⚠️  Error updating {len(property_ids)} properties for {eircode}: {e}')

        if error_count == 0:
            conn.commit()
            print(f'\n✅ SUCCESS: Updated {updated_count:,} properties')

            # Show updated coverage stats
            cur.execute('''
                SELECT
                    COUNT(*) as total,
                    COUNT(eircode) as with_eircode,
                    ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct
                FROM properties
            ''')
            total, with_eircode, pct = cur.fetchone()
            print(f'\n📊 New Eircode coverage: {with_eircode:,} / {total:,} ({pct}%)')

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
        else:
            conn.rollback()
            print(f'\n❌ ROLLED BACK: {error_count} errors occurred')

    conn.close()
    print('\n' + '=' * 70)

if __name__ == '__main__':
    main()
