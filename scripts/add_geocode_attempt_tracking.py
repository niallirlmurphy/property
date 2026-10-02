#!/usr/bin/env python3
"""Add persistent geocode attempt-tracking columns to the properties table.

Idempotent and re-runnable. Adds two columns so that every Mapbox geocode
attempt is recorded, and a failed address is never re-billed on a later run:

  geocode_attempts     INT NOT NULL DEFAULT 0   -- how many times we've tried this row
  geocode_last_attempt TIMESTAMPTZ              -- when we last tried (NULL = never)

Both use constant defaults / nullable, so ADD COLUMN is metadata-only on
Postgres 11+ (no full-table rewrite on the ~800k-row properties table).

The de-duplication itself lives in geocode_mapbox_batch.py: on failure a row is
set needs_geocoding=FALSE (and geocode_suspect=TRUE), so the --suspect worklist
fetch (which requires needs_geocoding=TRUE) no longer re-selects it. These
columns are the auditable record of *where* we have attempted.

Usage:
    export $(grep '^DATABASE_URL=' backend/.env | xargs)
    python3 scripts/add_geocode_attempt_tracking.py
"""
import os
import sys
import psycopg2


def main() -> int:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        return 1

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        """
        ALTER TABLE properties
            ADD COLUMN IF NOT EXISTS geocode_attempts INT NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS geocode_last_attempt TIMESTAMPTZ
        """
    )
    print("✓ Columns ensured: geocode_attempts, geocode_last_attempt")

    # Partial index to keep the --suspect worklist fetch fast and to make
    # "already attempted" rows cheap to audit.
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_properties_geocode_last_attempt
            ON properties (geocode_last_attempt)
            WHERE geocode_last_attempt IS NOT NULL
        """
    )
    print("✓ Index ensured: idx_properties_geocode_last_attempt")

    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE geocode_last_attempt IS NOT NULL) AS attempted,
            COUNT(*) FILTER (WHERE geocode_attempts > 0)             AS with_attempts
        FROM properties
        """
    )
    attempted, with_attempts = cur.fetchone()
    print(f"  rows with a recorded attempt: {attempted:,} (attempts>0: {with_attempts:,})")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
