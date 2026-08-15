#!/usr/bin/env python3
"""
Import non-property amenities (transport infrastructure + schools) into the
`amenities` table. Idempotent: upserts on (amenity_type, name), so re-running
updates rows in place rather than duplicating.

Usage (set DATABASE_URL in the environment or backend/.env first):
    python3 scripts/import_amenities.py                 # applies schema + imports both files
    python3 scripts/import_amenities.py --dry-run       # parse + validate, no DB writes
    python3 scripts/import_amenities.py --skip-schema   # assume table already exists
    python3 scripts/import_amenities.py \
        --transport "data/amenities/Dublin Key Transport Infrastructure Geocodes V2.xlsx" \
        --schools   "data/amenities/Dublin Key Educational Institutions and Schools.xlsx"

Requires: pip install pandas openpyxl psycopg2-binary python-dotenv

Both source files share the same shape (name, category, lat, lon, description);
schools additionally carry a Level column. Coordinates are validated against
Ireland bounds before load.
"""

import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
load_dotenv("backend/.env")

# Repo-relative defaults so imports are reproducible from a committed copy.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRANSPORT = os.path.join(
    REPO_ROOT, "data", "amenities",
    "Dublin Key Transport Infrastructure Geocodes V2.xlsx",
)
DEFAULT_SCHOOLS = os.path.join(
    REPO_ROOT, "data", "amenities",
    "Dublin Key Educational Institutions and Schools.xlsx",
)

# Ireland bounds — same convention as the geocoding validation framework.
LAT_MIN, LAT_MAX = 51.4, 55.5
LON_MIN, LON_MAX = -10.7, -5.4


def in_ireland(lat, lon):
    return (lat is not None and lon is not None
            and LAT_MIN <= lat <= LAT_MAX
            and LON_MIN <= lon <= LON_MAX)


def clean_str(val):
    """Trim to a clean string, or None for blanks/NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s or None


def load_transport(path):
    """Read the transport xlsx into normalized amenity dicts.

    Reconciles the one known ingest artifact: a description containing commas
    (Luas Dawson) that spilled into trailing 'Unnamed' columns. We rejoin any
    such spill back into a single description string.
    """
    df = pd.read_excel(path, engine="openpyxl")
    spill_cols = [c for c in df.columns if str(c).startswith("Unnamed")]
    source = os.path.basename(path)
    records = []
    for _, row in df.iterrows():
        desc_parts = [clean_str(row.get("Description"))]
        for c in spill_cols:
            desc_parts.append(clean_str(row.get(c)))
        description = ", ".join(p for p in desc_parts if p) or None

        records.append({
            "amenity_type": "transport",
            "name": clean_str(row.get("Infrastructure Name")),
            "category": clean_str(row.get("Category")),
            "level": None,
            "description": description,
            "latitude": row.get("Latitude"),
            "longitude": row.get("Longitude"),
            "source": source,
        })
    return records


def load_schools(path):
    """Read the schools xlsx into normalized amenity dicts."""
    df = pd.read_excel(path, engine="openpyxl")
    source = os.path.basename(path)
    records = []
    for _, row in df.iterrows():
        records.append({
            "amenity_type": "school",
            "name": clean_str(row.get("School Name")),
            "category": clean_str(row.get("Category")),
            "level": clean_str(row.get("Level")),
            "description": clean_str(row.get("Description")),
            "latitude": row.get("Latitude"),
            "longitude": row.get("Longitude"),
            "source": source,
        })
    return records


def validate(records):
    """Split records into (valid, skipped) on name + Ireland-bounds coords."""
    valid, skipped = [], []
    for r in records:
        try:
            lat = float(r["latitude"])
            lon = float(r["longitude"])
        except (TypeError, ValueError):
            lat = lon = None
        if not r["name"] or not in_ireland(lat, lon):
            skipped.append(r)
            continue
        r["latitude"], r["longitude"] = lat, lon
        valid.append(r)
    return valid, skipped


def apply_schema(cur):
    schema_path = os.path.join(REPO_ROOT, "db", "amenities_schema.sql")
    with open(schema_path) as f:
        cur.execute(f.read())


def upsert(cur, records):
    """Idempotent upsert on (amenity_type, name); bumps updated_at on change."""
    rows = [(
        r["amenity_type"], r["name"], r["category"], r["level"],
        r["description"], r["latitude"], r["longitude"],
        f"SRID=4326;POINT({r['longitude']} {r['latitude']})",
        r["source"],
    ) for r in records]

    execute_values(cur, """
        INSERT INTO amenities
            (amenity_type, name, category, level, description,
             latitude, longitude, geog, source)
        VALUES %s
        ON CONFLICT (amenity_type, name) DO UPDATE SET
            category    = EXCLUDED.category,
            level       = EXCLUDED.level,
            description = EXCLUDED.description,
            latitude    = EXCLUDED.latitude,
            longitude   = EXCLUDED.longitude,
            geog        = EXCLUDED.geog,
            source      = EXCLUDED.source,
            updated_at  = NOW()
    """, rows)


def main():
    ap = argparse.ArgumentParser(description="Import amenities (transport + schools).")
    ap.add_argument("--transport", default=DEFAULT_TRANSPORT)
    ap.add_argument("--schools", default=DEFAULT_SCHOOLS)
    ap.add_argument("--skip-schema", action="store_true",
                    help="Do not (re)apply amenities_schema.sql")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse and validate only; no DB connection or writes")
    args = ap.parse_args()

    records = load_transport(args.transport) + load_schools(args.schools)
    valid, skipped = validate(records)

    n_transport = sum(1 for r in valid if r["amenity_type"] == "transport")
    n_school = sum(1 for r in valid if r["amenity_type"] == "school")
    print(f"Parsed {len(records)} rows → {len(valid)} valid "
          f"({n_transport} transport, {n_school} school), {len(skipped)} skipped")
    for r in skipped:
        print(f"  SKIP [{r['amenity_type']}] {r['name']!r} "
              f"lat={r['latitude']} lon={r['longitude']}")

    if args.dry_run:
        print("Dry run — no database writes.")
        return

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("✗ DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    try:
        cur = conn.cursor()
        if not args.skip_schema:
            apply_schema(cur)
        upsert(cur, valid)
        conn.commit()

        cur.execute("""
            SELECT amenity_type, COUNT(*)
            FROM amenities GROUP BY amenity_type ORDER BY amenity_type
        """)
        print("Table totals after import:")
        for atype, count in cur.fetchall():
            print(f"  {atype}: {count}")
    finally:
        conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
