#!/usr/bin/env python3
"""
Analyze properties without coordinates to understand what needs geocoding.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print('='*70)
    print('ANALYZING 102,260 PROPERTIES WITHOUT COORDINATES')
    print('='*70)
    print()

    # 1. Breakdown by county
    print('1. BREAKDOWN BY COUNTY:')
    print()
    cur.execute('''
        SELECT
            county,
            COUNT(*) as missing_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM properties
        WHERE latitude IS NULL
        AND county IS NOT NULL
        GROUP BY county
        ORDER BY missing_count DESC
        LIMIT 15
    ''')

    print(f"{'County':<20} {'Missing':<12} {'% of Missing':>12}")
    print('-'*50)
    for county, count, pct in cur.fetchall():
        print(f'{county:<20} {count:>10,}   {pct:>10.1f}%')

    print()

    # 2. Properties with/without Eircode
    print('2. EIRCODE COVERAGE:')
    print()
    cur.execute('''
        SELECT
            CASE WHEN eircode IS NOT NULL THEN 'Has Eircode' ELSE 'No Eircode' END as status,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM properties
        WHERE latitude IS NULL
        GROUP BY CASE WHEN eircode IS NOT NULL THEN 'Has Eircode' ELSE 'No Eircode' END
    ''')

    for status, count, pct in cur.fetchall():
        print(f'  {status:<20} {count:>10,}   ({pct:.1f}%)')

    print()

    # 3. Sample addresses to see patterns
    print('3. SAMPLE ADDRESSES (to identify patterns):')
    print()
    cur.execute('''
        SELECT address, county, eircode
        FROM properties
        WHERE latitude IS NULL
        ORDER BY RANDOM()
        LIMIT 20
    ''')

    print(f"{'Address':<60} {'County':<15} {'Eircode'}")
    print('-'*90)
    for addr, county, eircode in cur.fetchall():
        addr_short = addr[:57] + '...' if len(addr) > 60 else addr
        print(f'{addr_short:<60} {county or "":<15} {eircode or ""}')

    print()

    # 4. Sale date distribution
    print('4. SALE DATE DISTRIBUTION:')
    print()
    cur.execute('''
        SELECT
            EXTRACT(YEAR FROM sale_date) as year,
            COUNT(*) as missing_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM properties
        WHERE latitude IS NULL
        GROUP BY EXTRACT(YEAR FROM sale_date)
        ORDER BY year DESC
        LIMIT 10
    ''')

    print(f"{'Year':<8} {'Missing':<12} {'% of Missing':>12}")
    print('-'*35)
    for year, count, pct in cur.fetchall():
        print(f'{int(year):<8} {count:>10,}   {pct:>10.1f}%')

    print()

    # 5. Address length analysis
    print('5. ADDRESS LENGTH ANALYSIS:')
    print()
    cur.execute('''
        SELECT
            CASE
                WHEN LENGTH(address) < 20 THEN 'Very short (<20 chars)'
                WHEN LENGTH(address) < 40 THEN 'Short (20-40 chars)'
                WHEN LENGTH(address) < 60 THEN 'Medium (40-60 chars)'
                ELSE 'Long (60+ chars)'
            END as length_category,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM properties
        WHERE latitude IS NULL
        GROUP BY length_category
        ORDER BY
            CASE
                WHEN LENGTH(address) < 20 THEN 1
                WHEN LENGTH(address) < 40 THEN 2
                WHEN LENGTH(address) < 60 THEN 3
                ELSE 4
            END
    ''')

    for category, count, pct in cur.fetchall():
        print(f'  {category:<25} {count:>10,}   ({pct:.1f}%)')

    print()

    # 6. Check for apartment/unit properties
    print('6. PROPERTY TYPE INDICATORS:')
    print()
    cur.execute('''
        SELECT
            CASE
                WHEN LOWER(address) LIKE '%apartment%' OR LOWER(address) LIKE '%apt%' THEN 'Apartments'
                WHEN LOWER(address) LIKE '%unit%' THEN 'Units'
                WHEN LOWER(address) LIKE '%house%' THEN 'Houses'
                WHEN address ~ '[0-9]+ [A-Z]' THEN 'Has number (likely house)'
                ELSE 'Other/Unknown'
            END as type_indicator,
            COUNT(*) as count
        FROM properties
        WHERE latitude IS NULL
        GROUP BY type_indicator
        ORDER BY count DESC
    ''')

    for type_ind, count in cur.fetchall():
        print(f'  {type_ind:<30} {count:>10,}')

    print()

    # 7. Check if needs_geocoding flag is set
    print('7. NEEDS_GEOCODING FLAG STATUS:')
    print()
    cur.execute('''
        SELECT
            needs_geocoding,
            COUNT(*) as count
        FROM properties
        WHERE latitude IS NULL
        GROUP BY needs_geocoding
        ORDER BY needs_geocoding
    ''')

    for flag, count in cur.fetchall():
        status = 'TRUE' if flag else 'FALSE'
        print(f'  needs_geocoding = {status:<10} {count:>10,}')

    conn.close()

if __name__ == "__main__":
    main()
