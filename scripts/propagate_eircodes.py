#!/usr/bin/env python3
"""
Propagate Eircode data across sales that share the same address.

When one sale of an address has an Eircode and its sibling sales (same
address_normalized) do not, copy the Eircode to the siblings that are missing it.

SAFETY GUARD (matches commit 7d902ea rationale):
    Two sales can share identical address TEXT but be DIFFERENT dwellings — e.g.
    townland addresses like 'RAMPARK, JENKINSTOWN, DUNDALK' span 8+ distinct
    Eircodes. We must never assign one dwelling's Eircode to another.

    Therefore we ONLY propagate for addresses where every sale that has an
    Eircode agrees on a SINGLE distinct value (COUNT(DISTINCT eircode) = 1).
    Addresses with 2+ distinct Eircodes are ambiguous and left untouched.
    We only ever fill NULL Eircodes; we never overwrite an existing one.

    routing_key is a generated column (first 3 chars of eircode) so it updates
    automatically — we do not set it here.

Usage:
    python3 scripts/propagate_eircodes.py            # dry-run (default, no writes)
    python3 scripts/propagate_eircodes.py --apply    # commit changes
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

# Addresses where all present Eircodes agree on one value; fill the NULL siblings.
PROPAGATE_SQL = """
WITH single_eircode_addr AS (
    SELECT address_normalized, MAX(eircode) AS eircode
    FROM properties
    WHERE address_normalized IS NOT NULL AND address_normalized <> ''
    GROUP BY address_normalized
    HAVING COUNT(*) FILTER (WHERE eircode IS NOT NULL) > 0   -- at least one source
       AND COUNT(*) FILTER (WHERE eircode IS NULL)     > 0   -- at least one target
       AND COUNT(DISTINCT eircode)                     = 1   -- unambiguous
)
UPDATE properties p
SET eircode = s.eircode
FROM single_eircode_addr s
WHERE p.address_normalized = s.address_normalized
  AND p.eircode IS NULL
"""

COUNT_SQL = PROPAGATE_SQL.replace(
    "UPDATE properties p\nSET eircode = s.eircode\nFROM single_eircode_addr s\n"
    "WHERE p.address_normalized = s.address_normalized\n  AND p.eircode IS NULL",
    "SELECT COUNT(*) FROM properties p\n"
    "JOIN single_eircode_addr s ON p.address_normalized = s.address_normalized\n"
    "WHERE p.eircode IS NULL",
)


def main():
    apply = "--apply" in sys.argv
    if not os.getenv("DATABASE_URL"):
        load_dotenv("backend/.env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL not set (checked env and backend/.env).")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute(COUNT_SQL)
    to_update = cur.fetchone()[0]
    print(f"Rows missing an Eircode that would be filled (single-eircode "
          f"addresses only): {to_update:,}")

    if not apply:
        print("\nDRY RUN — no changes made. Re-run with --apply to commit.")
        conn.close()
        return

    cur.execute(PROPAGATE_SQL)
    updated = cur.rowcount
    conn.commit()
    print(f"\n✓ Applied. Eircodes propagated to {updated:,} rows.")
    conn.close()


if __name__ == "__main__":
    main()
