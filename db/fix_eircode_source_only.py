#!/usr/bin/env python3
"""
Correct eircodes in the DB so only PPR-sourced eircodes are kept.

Strategy:
  1. NULL all eircodes in the DB (batched by ID to avoid timeout)
  2. Re-apply only the eircodes that appeared in the original PPR source CSV

Usage:
    DATABASE_URL=<url> python3 db/fix_eircode_source_only.py [--dry-run]
"""

import csv
import os
import re
import sys
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SOURCE_CSV   = os.path.join(os.path.dirname(__file__), "..", "source data", "PPR-ALL.csv")
DRY_RUN      = "--dry-run" in sys.argv
BATCH_SIZE   = 200


def parse_price(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    cleaned = re.sub(r"[^\d.]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def connect():
    return psycopg2.connect(DATABASE_URL)


def run():
    print(f"Reading PPR source: {SOURCE_CSV}")
    ppr_eircodes: list[tuple] = []   # (sale_date, address, eircode) for rows WITH a PPR eircode

    with open(SOURCE_CSV, encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            eircode = row.get("Eircode", "").strip()
            if not eircode:
                continue
            sale_date = parse_date(row.get("Date of Sale (dd/mm/yyyy)", "").strip())
            address   = row.get("Address", "").strip()
            price_raw = next((v for k, v in row.items() if k.startswith("Price")), "")
            price     = parse_price(price_raw.strip())
            if sale_date and address and price is not None:
                ppr_eircodes.append((sale_date, address, price, eircode))

    print(f"PPR rows with eircode to preserve: {len(ppr_eircodes):,}")

    conn = connect()
    cur  = conn.cursor()
    cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE")
    cur.execute("SET statement_timeout = 0")
    conn.commit()

    # Step 1: NULL all eircodes, batched by ID range to avoid long-running statements
    cur.execute("SELECT MIN(id), MAX(id) FROM properties WHERE eircode IS NOT NULL")
    row = cur.fetchone()
    if not row or row[0] is None:
        print("No eircodes to clear — nothing to do.")
        cur.close()
        conn.close()
        return

    min_id, max_id = row
    print(f"Step 1: Nulling all eircodes (IDs {min_id}–{max_id})...")
    nulled = 0
    batch_start = min_id
    while batch_start <= max_id:
        batch_end = batch_start + 5000
        if not DRY_RUN:
            cur.execute("""
                UPDATE properties SET eircode = NULL
                WHERE id BETWEEN %s AND %s AND eircode IS NOT NULL
            """, (batch_start, batch_end))
            nulled += cur.rowcount
            conn.commit()
        batch_start = batch_end + 1
        if batch_start % 50001 < 5001:
            print(f"  Nulled {nulled:,} rows so far...")

    print(f"Step 1 done: {'would null' if DRY_RUN else 'nulled'} {nulled:,} rows")

    # Step 2: Re-apply PPR-sourced eircodes
    print(f"Step 2: Re-applying {len(ppr_eircodes):,} PPR eircodes...")
    reapplied = 0
    for i in range(0, len(ppr_eircodes), BATCH_SIZE):
        chunk = ppr_eircodes[i:i + BATCH_SIZE]
        if not DRY_RUN:
            execute_values(cur, """
                UPDATE properties p
                SET eircode = src.eircode
                FROM (VALUES %s) AS src(sale_date, address, price, eircode)
                WHERE p.sale_date = src.sale_date::date
                  AND p.address   = src.address
                  AND p.price     = src.price::numeric
            """, chunk, template="(%s, %s, %s, %s)")
            reapplied += cur.rowcount
            conn.commit()
        if (i + BATCH_SIZE) % 10000 < BATCH_SIZE:
            print(f"  Re-applied {reapplied:,} rows so far...")

    print(f"Step 2 done: {'would re-apply' if DRY_RUN else 're-applied'} {reapplied:,} eircodes")

    if DRY_RUN:
        print("\n[DRY RUN] No changes made. Remove --dry-run to apply.")
        conn.rollback()
    else:
        print("\nDone.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    if DRY_RUN:
        print("--- DRY RUN (pass no args to apply) ---")
    run()
