#!/usr/bin/env python3
"""
Reconcile the PPR source CSV against the database and import ONLY the rows
that are genuinely missing.

WHY THIS EXISTS
    scripts/sync_ppr_updates.py imports rows whose sale_date is strictly newer
    than the newest sale_date already in the DB, and it finds them by scanning
    the CSV backwards until it hits an older date. That assumes the CSV is
    append-only and strictly date-sorted. It is NOT: the PPR back-fills sales
    retroactively (a sale dated in May can be filed into the CSV months later,
    appearing AFTER July rows). The backward scan stops at the first old date
    and never sees those rows, so recent months accumulate a permanent deficit.

    This script does a full multiset set-difference instead — robust to
    retroactive filing and re-ordering, and idempotent (re-running imports 0).

NATURAL KEY  (sale_date, price, county)
    NOT address. The PPR revises address SPELLING between snapshots (fadas
    added, "No." dropped, punctuation changed), so the same sale appears with
    different address text over time. Keying on address would treat every such
    edit as a brand-new sale and import a false duplicate — verified: an
    address-level difference flags ~2,068 rows spread evenly back to 2010,
    where months are known to net-match. Coarse (date, price, county) keying
    absorbs that drift and isolates the ~6.7k genuinely-missing sales (96%
    dated 2026 — the retroactively-filed rows the sync's backward scan skips).

    The properties table has NO unique constraint (only id PK), so ON CONFLICT
    cannot dedupe — we dedupe here by COUNTS per key. PPR legitimately contains
    repeat filings (multi-unit / portfolio sales) sharing a key, so for each
    key we import max(0, source_count - db_count) rows. This preserves genuine
    duplicates and never re-imports rows already present. See CLAUDE.md +
    memory: PPR source rows must never be deleted, and genuine source
    duplicates are expected.

IMPORTED ROWS
    Inserted with latitude/longitude NULL and needs_geocoding = TRUE, matching
    the --skip-geocoding import path. After this runs, geocode + propagate:
        python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
        python3 scripts/propagate_eircodes.py --apply

USAGE
    python3 scripts/reconcile_ppr_import.py                 # dry-run (default)
    python3 scripts/reconcile_ppr_import.py --apply         # commit inserts
    python3 scripts/reconcile_ppr_import.py --csv PATH      # override source CSV
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CSV = PROJECT_ROOT / "source data" / "PPR-ALL.csv"
CSV_ENCODING = "cp1252"  # PPR CSVs are cp1252/latin-1, NOT utf-8

# Reuse the exact same normalization the importer uses, so address_normalized
# is byte-for-byte consistent with existing rows.
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.sync_ppr_updates import (  # noqa: E402
    parse_date,
    parse_price,
    parse_bool,
    normalize_address,
)


def key_of(sale_date, price, county):
    """Coarse natural key for a PPR sale, robust to address-spelling drift.

    price rounded to cents to avoid float noise; county stripped for
    consistency between source text and DB text.
    """
    return (
        sale_date,
        None if price is None else round(price, 2),
        county,
    )


def load_source(csv_path):
    """Return {key: [full_row_dict, ...]} for all valid source rows."""
    groups = defaultdict(list)
    invalid = 0
    with open(csv_path, encoding=CSV_ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sale_date = parse_date(row.get("Date of Sale (dd/mm/yyyy)"))
            price_raw = (
                row.get("Price (€)")
                or row.get("Price (�)")
                or row.get("Price (EUR)")
                or row.get("Price")
            )
            price = parse_price(price_raw)
            if not sale_date or price is None:
                invalid += 1
                continue
            address = (row.get("Address") or "").strip()
            county = (row.get("County") or "").strip()
            eircode_raw = row.get("Postal Code") or row.get("Eircode")
            rec = {
                "sale_date": sale_date,
                "address": address,
                "address_normalized": normalize_address(address),
                "eircode": (eircode_raw or "").strip() or None,
                "county": county,
                "price": price,
                "not_full_market_price": parse_bool(
                    row.get("Not Full Market Price", "No")
                ),
                "vat_exclusive": parse_bool(row.get("VAT Exclusive", "No")),
                "description": (row.get("Description of Property") or "").strip(),
                "size_description": (row.get("Property Size Description") or "").strip()
                or None,
            }
            groups[key_of(sale_date, price, county)].append(rec)
    return groups, invalid


def load_db_counts(conn):
    """Return {key: count} for every row in the DB (server-side cursor)."""
    counts = defaultdict(int)
    cur = conn.cursor(name="db_keys")  # named -> server-side, streams
    cur.itersize = 50_000
    cur.execute("SELECT sale_date, price, county FROM properties")
    for sale_date, price, county in cur:
        counts[
            key_of(
                sale_date,
                None if price is None else float(price),
                (county or "").strip(),
            )
        ] += 1
    cur.close()
    return counts


INSERT_SQL = """
    INSERT INTO properties (
        sale_date, address, address_normalized, county, eircode, price,
        not_full_market_price, vat_exclusive, description, size_description,
        latitude, longitude, geog, needs_geocoding
    ) VALUES %s
"""

# Each row imported with NULL coords + needs_geocoding = TRUE.
ROW_TEMPLATE = (
    "(%(sale_date)s, %(address)s, %(address_normalized)s, %(county)s, "
    "%(eircode)s, %(price)s, %(not_full_market_price)s, %(vat_exclusive)s, "
    "%(description)s, %(size_description)s, NULL, NULL, NULL, TRUE)"
)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="commit inserts (default: dry-run)")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="source CSV path")
    args = ap.parse_args()

    if not os.getenv("DATABASE_URL"):
        load_dotenv("backend/.env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL not set (checked env and backend/.env).")
    if not os.path.exists(args.csv):
        sys.exit(f"ERROR: source CSV not found: {args.csv}")

    print("=" * 70)
    print("PPR RECONCILIATION IMPORT")
    print("=" * 70)
    print(f"Source: {args.csv}")
    print(f"Mode:   {'APPLY (writing)' if args.apply else 'DRY RUN (no writes)'}")
    print()

    print("Loading source CSV ...")
    src_groups, src_invalid = load_source(args.csv)
    src_total = sum(len(v) for v in src_groups.values())
    print(f"  valid source rows: {src_total:,}  (invalid skipped: {src_invalid:,})")
    print(f"  distinct keys:     {len(src_groups):,}")

    conn = psycopg2.connect(db_url)
    print("\nLoading DB key counts ...")
    conn.set_session(readonly=True)
    db_counts = load_db_counts(conn)
    db_total = sum(db_counts.values())
    print(f"  DB rows: {db_total:,}  distinct keys: {len(db_counts):,}")
    conn.rollback()  # end read-only txn

    # Multiset difference: for each source key, import (src - db) extra rows.
    to_insert = []
    for key, rows in src_groups.items():
        deficit = len(rows) - db_counts.get(key, 0)
        if deficit > 0:
            to_insert.extend(rows[:deficit])

    print("\n" + "-" * 70)
    print(f"Rows to import (missing from DB): {len(to_insert):,}")
    if to_insert:
        by_year = defaultdict(int)
        for r in to_insert:
            by_year[r["sale_date"].year] += 1
        print("  By sale year:")
        for y in sorted(by_year):
            print(f"    {y}: {by_year[y]:,}")
        print("\n  Sample:")
        for r in to_insert[:5]:
            print(f"    {r['sale_date']} | {r['address'][:45]:45} | "
                  f"€{r['price']:,.0f} | {r['county']}")

    if not to_insert:
        print("\n✓ Database already matches source. Nothing to import.")
        conn.close()
        return

    if not args.apply:
        print("\nDRY RUN — no changes made. Re-run with --apply to import.")
        print("After --apply, geocode + propagate:")
        print("  python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply")
        print("  python3 scripts/propagate_eircodes.py --apply")
        conn.close()
        return

    conn.set_session(readonly=False)
    cur = conn.cursor()
    BATCH = 1000
    imported = 0
    for i in range(0, len(to_insert), BATCH):
        batch = to_insert[i:i + BATCH]
        execute_values(cur, INSERT_SQL, batch, template=ROW_TEMPLATE)
        imported += len(batch)
        print(f"  imported {imported:,}/{len(to_insert):,} ...")
    conn.commit()
    print(f"\n✓ Imported {imported:,} previously-missing rows "
          f"(needs_geocoding=TRUE, NULL coords).")

    # Refresh routing key stats (safe even if no new eircodes).
    print("Refreshing routing_key_stats materialized view ...")
    cur.execute("REFRESH MATERIALIZED VIEW routing_key_stats")
    conn.commit()
    print("✓ Done.")
    conn.close()

    print("\nNext steps:")
    print("  python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply")
    print("  python3 scripts/propagate_eircodes.py --apply")


if __name__ == "__main__":
    main()
