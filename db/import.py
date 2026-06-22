#!/usr/bin/env python3
"""
Import PPR-ALL-geocoded.csv into Supabase (PostgreSQL + PostGIS).

Usage:
    python3 db/import.py

Requires:
    pip install psycopg2-binary python-dotenv

Environment variables (set in .env or shell):
    DATABASE_URL  — Supabase connection string, e.g.
                    postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
"""

import csv
import os
import sys
import re
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SOURCE_CSV   = os.path.join(os.path.dirname(__file__), "..", "PPR-ALL-final.csv")
BATCH_SIZE   = 1000


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


def get_column_value(row, exact_keys, prefix_keys=()):
    for key in exact_keys:
        value = row.get(key)
        if value not in (None, ""):
            return value

    for row_key, value in row.items():
        if row_key is None or value in (None, ""):
            continue
        row_key_normalized = row_key.strip().lower()
        if any(row_key_normalized.startswith(prefix) for prefix in prefix_keys):
            return value

    return ""


def parse_bool(raw: str) -> bool:
    return raw.strip().lower() in ("yes", "true", "1")


def parse_float(raw: str) -> Optional[float]:
    try:
        return float(raw.strip())
    except (ValueError, AttributeError):
        return None


def normalize_address(address: str) -> str:
    """
    Normalize address for better matching (same logic as scripts/normalize_addresses.py).
    Applied automatically during import to ensure all new records have normalized addresses.
    """
    if not address:
        return address

    normalized = address.strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r',\s*,+', ',', normalized)
    normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)
    normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

    # Standardize street types
    street_types = {
        r'\bSt\.?\b': 'Street', r'\bRd\.?\b': 'Road', r'\bAve\.?\b': 'Avenue',
        r'\bDr\.?\b': 'Drive', r'\bCl\.?\b': 'Close', r'\bCt\.?\b': 'Court',
        r'\bPk\.?\b': 'Park', r'\bSq\.?\b': 'Square',
    }
    for abbrev, full in street_types.items():
        normalized = re.sub(abbrev, full, normalized, flags=re.I)

    # Clean punctuation
    normalized = re.sub(r',\s*,', ',', normalized)
    normalized = re.sub(r'\s+,', ',', normalized)
    normalized = re.sub(r',\s+', ', ', normalized)
    normalized = normalized.strip(', ')

    # Title case
    words = normalized.split()
    lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
    upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

    result_words = []
    for i, word in enumerate(words):
        if i == 0:
            result_words.append(word.capitalize())
        elif word in upper_exceptions:
            result_words.append(word)
        elif word.lower() in lower_exceptions:
            result_words.append(word.lower())
        else:
            result_words.append(word.capitalize())

    return ' '.join(result_words).strip()


def run_import():
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()

    # Apply schema
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        cur.execute(f.read())
    conn.commit()

    # Truncate existing data so we don't duplicate on re-import
    print("Truncating existing data...")
    cur.execute("TRUNCATE TABLE properties RESTART IDENTITY;")
    conn.commit()

    print(f"Importing from {SOURCE_CSV} ...")

    batch   = []
    total   = 0
    skipped = 0

    with open(SOURCE_CSV, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sale_date = parse_date(get_column_value(
                row,
                ("Date of Sale (dd/mm/yyyy)", "Date of Sale"),
                ("date of sale",),
            ))
            price = parse_price(get_column_value(
                row,
                ("Price (€)", "Price"),
                ("price",),
            ))

            if sale_date is None or price is None:
                skipped += 1
                continue

            lat = parse_float(row.get("Latitude"))
            lon = parse_float(row.get("Longitude"))
            geog = f"SRID=4326;POINT({lon} {lat})" if lat is not None and lon is not None else None

            address = row.get("Address", "").strip()
            batch.append((
                sale_date,
                address,
                normalize_address(address),  # Automatically normalize on import
                row.get("County", "").strip() or None,
                row.get("Eircode", "").strip() or None,
                price,
                parse_bool(row.get("Not Full Market Price", "")),
                parse_bool(row.get("VAT Exclusive", "")),
                row.get("Description of Property", "").strip() or None,
                row.get("Property Size Description", "").strip() or None,
                lat,
                lon,
                geog,
            ))

            if len(batch) >= BATCH_SIZE:
                _flush(cur, batch)
                conn.commit()
                total += len(batch)
                batch = []
                print(f"  Inserted {total:,} rows...")

    if batch:
        _flush(cur, batch)
        conn.commit()
        total += len(batch)

    print(f"\nDone. Inserted {total:,} rows, skipped {skipped:,}.")
    cur.close()
    conn.close()


def _flush(cur, batch):
    execute_values(cur, """
        INSERT INTO properties
            (sale_date, address, address_normalized, county, eircode, price,
             not_full_market_price, vat_exclusive, description,
             size_description, latitude, longitude, geog)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, batch, template="""(
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s::geography
    )""")


if __name__ == "__main__":
    if not os.path.exists(SOURCE_CSV):
        print(f"ERROR: {SOURCE_CSV} not found. Run `python3 geocode.py --export` first.")
        sys.exit(1)
    run_import()
