#!/usr/bin/env python3
"""Populate the PostGIS `geog` column for any row that has latitude/longitude
but a NULL `geog`.

Radius and polygon search match on `properties.geog` (a GEOGRAPHY(Point,4326)
column, GIST-indexed) via ST_DWithin / ST_Within. `geog` is a plain column, so
every write path must set it explicitly alongside latitude/longitude — and if an
ad-hoc geocode/repair script updates the coordinates without it, the row keeps a
correct lat/lon yet becomes invisible to search (it still plots on a lat/lon
map). This step self-heals that: after geocoding, any lat/lon-without-geog row is
brought back into the spatial index.

Run standalone or as a step in scripts/ppr_full_pipeline.py.

Usage:
    python3 scripts/backfill_geog.py            # apply
    python3 scripts/backfill_geog.py --dry-run  # count only, no writes
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")

STALE_SQL = """
    SELECT COUNT(*) FROM properties
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND geog IS NULL
"""

BACKFILL_SQL = """
    UPDATE properties
    SET geog = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND geog IS NULL
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill NULL geog from lat/lon")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report how many rows need backfilling without writing")
    args = parser.parse_args()

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("❌ DATABASE_URL not set")
        return 1

    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        cur.execute(STALE_SQL)
        stale = cur.fetchone()[0]

        if args.dry_run:
            print(f"[DRY RUN] {stale:,} rows have lat/lon but NULL geog (would backfill)")
            return 0

        if stale == 0:
            print("✅ geog is fully populated — nothing to backfill")
            return 0

        cur.execute(BACKFILL_SQL)
        conn.commit()
        print(f"✅ Backfilled geog for {cur.rowcount:,} rows (now searchable)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
