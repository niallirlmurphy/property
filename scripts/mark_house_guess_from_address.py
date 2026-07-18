#!/usr/bin/env python3
"""
Mark likely houses from address (low-confidence heuristic).

For older sales (2010-2020) that have no property_type, a bare place-name /
townland address with no leading house number and no apartment/unit token is
~81% likely to be a house (validated against ~91k already-labelled rows).

This is a LOW-CONFIDENCE guess: it is stamped property_type_source =
'address_house_guess' so that:
  - it is distinguishable from verified data, and
  - the web-enrichment scraper re-visits and overwrites it when real listing
    data becomes available (see enrich_batch6_2026.py).

Scope is deliberately limited to 2010-2020 (older, lower-traffic years where
the enrichment backlog is deepest). Recent years are left for the scraper.

Usage:
    python3 scripts/mark_house_guess_from_address.py            # dry run
    python3 scripts/mark_house_guess_from_address.py --apply     # write
"""

import os
import sys
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Exclude any apartment/unit indicators (whole-word, case-insensitive).
APT_TOKENS = r'\m(APT|APTS|APARTMENT|APARTMENTS|FLAT|BLOCK|UNIT|UNITS|DUPLEX)\M'

# The validated house signal: address begins with a letter (a place name),
# i.e. NO leading house number. Combined with the apartment exclusion this
# scores ~81% house precision on labelled data.
PLACE_NAME_ONLY = r'^\s*[A-Za-z]'

# Deliberately limited to the older backlog years.
START_DATE = '2010-01-01'
END_DATE = '2021-01-01'  # exclusive -> through 2020


def build_where():
    return (
        "sale_date >= %s AND sale_date < %s "
        "AND property_type IS NULL "
        "AND address !~* %s "
        "AND address ~* %s",
        [START_DATE, END_DATE, APT_TOKENS, PLACE_NAME_ONLY],
    )


def main():
    parser = argparse.ArgumentParser(description="Mark likely houses (low-confidence) from address")
    parser.add_argument('--apply', action='store_true', help='Perform the update (default: dry run)')
    args = parser.parse_args()

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set (backend/.env)")
        sys.exit(1)

    where_sql, params = build_where()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM properties WHERE {where_sql}", params)
    total = cur.fetchone()[0]

    print("=" * 70)
    print("MARK HOUSE GUESS FROM ADDRESS (low confidence, ~81%)")
    print("=" * 70)
    print(f"Scope        : sale_date {START_DATE} .. {END_DATE} (exclusive)")
    print(f"Signal       : place-name-only address, no apartment/unit token")
    print(f"Sets         : property_type='house', source='address_house_guess'")
    print(f"Rows to mark : {total:,}")
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
        f"""UPDATE properties
            SET property_type = 'house', property_type_source = 'address_house_guess'
            WHERE {where_sql}""",
        params,
    )
    updated = cur.rowcount
    conn.commit()
    print(f"✅ Marked {updated:,} rows as house (source=address_house_guess)")
    conn.close()


if __name__ == '__main__':
    main()
