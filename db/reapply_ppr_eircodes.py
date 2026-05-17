#!/usr/bin/env python3
"""Re-apply eircodes from PPR source CSV to the properties table."""

import csv
import os
import re
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SOURCE_CSV   = os.path.join(os.path.dirname(__file__), "..", "source data", "PPR-ALL.csv")
BATCH_SIZE   = 500


def parse_price(raw):
    cleaned = re.sub(r"[^\d.]", "", raw or "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(raw):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def run():
    print("Reading PPR source...")
    rows = []
    with open(SOURCE_CSV, encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            eircode = row.get("Eircode", "").strip()
            if not eircode:
                continue
            sale_date = parse_date(row.get("Date of Sale (dd/mm/yyyy)", ""))
            address   = row.get("Address", "").strip()
            price_raw = next((v for k, v in row.items() if k.startswith("Price")), "")
            price     = parse_price(price_raw)
            if sale_date and address and price is not None:
                rows.append((sale_date, address, price, eircode))

    print(f"PPR eircodes to re-apply: {len(rows):,}")

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()

    updated = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        execute_values(cur, """
            UPDATE properties p
            SET eircode = src.eircode
            FROM (VALUES %s) AS src(sale_date, address, price, eircode)
            WHERE p.sale_date = src.sale_date::date
              AND p.address   = src.address
              AND p.price     = src.price::numeric
        """, chunk, template="(%s, %s, %s, %s)")
        updated += cur.rowcount
        conn.commit()
        if (i + BATCH_SIZE) % 10000 < BATCH_SIZE:
            print(f"  {updated:,} rows updated so far...")

    print(f"Done. Re-applied eircodes to {updated:,} rows.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
