#!/usr/bin/env python3
"""
Mark apartments by address indicator.

Many Property Price Register addresses explicitly identify an apartment/flat
(e.g. "APT 3 The Moorings", "Apartment 25, ...", "FLAT 1, ..."). The address
is a more reliable signal for these than the web-enrichment scraper, which
sometimes mis-types them as terraced/detached/semi-detached.

This script sets property_type = 'apartment' for every 2010+ property whose
address contains a whole-word apartment token. By default it overwrites any
existing (mis-scraped) property_type; pass --only-null to fill blanks only.

Usage:
    python3 scripts/mark_apartments_from_address.py            # dry run (no writes)
    python3 scripts/mark_apartments_from_address.py --apply    # perform the update
    python3 scripts/mark_apartments_from_address.py --apply --only-null
"""

import os
import sys
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Whole-word apartment indicators (Postgres word boundaries are \m ... \M).
# Case-insensitive match via the ~* operator.
INDICATOR = r'\m(APT|APTS|APARTMENT|APARTMENTS|FLAT)\M'

# Only touch rows from the PPR era we serve.
MIN_SALE_DATE = '2010-01-01'


def main():
    parser = argparse.ArgumentParser(description="Mark apartments from address indicators")
    parser.add_argument('--apply', action='store_true',
                        help='Perform the update (default is a dry run)')
    parser.add_argument('--only-null', action='store_true',
                        help='Only set property_type where it is currently NULL '
                             '(do not overwrite existing values)')
    args = parser.parse_args()

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set (backend/.env)")
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Base predicate shared by preview and update.
    where = ["sale_date >= %s", "address ~* %s", "property_type IS DISTINCT FROM 'apartment'"]
    params = [MIN_SALE_DATE, INDICATOR]
    if args.only_null:
        where.append("property_type IS NULL")
    where_sql = " AND ".join(where)

    # Preview: how many rows, and how many are overwrites vs fresh.
    cur.execute(f"SELECT COUNT(*) FROM properties WHERE {where_sql}", params)
    total = cur.fetchone()[0]

    cur.execute(
        f"SELECT COUNT(*) FROM properties WHERE {where_sql} AND property_type IS NOT NULL",
        params)
    overwrites = cur.fetchone()[0]

    print("=" * 70)
    print("MARK APARTMENTS FROM ADDRESS")
    print("=" * 70)
    print(f"Indicator      : {INDICATOR}")
    print(f"Sale date      : >= {MIN_SALE_DATE}")
    print(f"Mode           : {'only NULL' if args.only_null else 'overwrite existing'}")
    print(f"Rows to update : {total:,}")
    print(f"  fresh (NULL) : {total - overwrites:,}")
    print(f"  overwrites   : {overwrites:,}")
    print()

    if total == 0:
        print("Nothing to do.")
        conn.close()
        return

    if not args.apply:
        print("DRY RUN — no changes written. Re-run with --apply to perform the update.")
        conn.close()
        return

    cur.execute(
        f"UPDATE properties SET property_type = 'apartment' WHERE {where_sql}", params)
    updated = cur.rowcount
    conn.commit()
    print(f"✅ Updated {updated:,} rows -> property_type = 'apartment'")
    conn.close()


if __name__ == '__main__':
    main()
