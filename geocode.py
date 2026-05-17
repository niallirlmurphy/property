#!/usr/bin/env python3
"""
Geocode PPR-ALL.csv using OpenStreetMap Nominatim with Photon as fallback.

Usage:
    python3 geocode.py            # run geocoding (resumes from last position)
    python3 geocode.py --export   # write enriched CSV and exit
    python3 geocode.py --status   # show progress and exit

Results are stored in geocode_cache.db (SQLite) so the script can be stopped
and restarted safely at any time. Both APIs are free, no key required.

Strategy:
  1. If Eircode present, query Nominatim with routing key (e.g. "D14, Ireland").
  2. Otherwise query Nominatim with address + county (no "Ireland" suffix).
  3. If Nominatim returns nothing, retry with Photon (komoot) — it uses fuzzy
     matching and tolerates typos and non-standard Irish address formatting.
  Both APIs are rate-limited to 1 req/sec (shared counter).
"""

import csv
import sqlite3
import time
import sys
import os
import re
import requests

SOURCE_CSV = os.path.join(os.path.dirname(__file__), "source data", "PPR-ALL.csv")
DB_PATH    = os.path.join(os.path.dirname(__file__), "geocode_cache.db")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "PPR-ALL-geocoded.csv")

NOMINATIM_URL = "http://localhost:8080/search"
PHOTON_URL    = "https://photon.komoot.io/api/"
USER_AGENT    = "PPR-geocoder/1.0 (personal research project)"
RATE_LIMIT    = 0.05  # seconds between requests (local instance — no rate limit)
BATCH_SIZE    = 500   # commit to DB every N geocoded rows
NOT_FOUND     = "NOT_FOUND"  # sentinel stored when genuinely not found
# Ireland bounding box for Photon (lon_min, lat_min, lon_max, lat_max)
IRELAND_BBOX  = "-10.5,51.4,-5.5,55.4"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geocode_cache (
            query      TEXT PRIMARY KEY,
            lat        REAL,
            lon        REAL,
            display    TEXT,
            source     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            last_row   INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO progress (id, last_row) VALUES (1, 0)
    """)
    conn.commit()


def get_last_row(conn):
    return conn.execute("SELECT last_row FROM progress WHERE id=1").fetchone()[0]


def set_last_row(conn, row_num):
    conn.execute("UPDATE progress SET last_row=? WHERE id=1", (row_num,))


def lookup_cache(conn, query):
    row = conn.execute(
        "SELECT lat, lon, display FROM geocode_cache WHERE query=?", (query,)
    ).fetchone()
    return row  # (lat, lon, display) or None


def insert_cache(conn, query, lat, lon, display, source=None):
    conn.execute(
        "INSERT OR REPLACE INTO geocode_cache (query, lat, lon, display, source) VALUES (?,?,?,?,?)",
        (query, lat, lon, display, source)
    )


def cache_stats(conn):
    total   = conn.execute("SELECT COUNT(*) FROM geocode_cache").fetchone()[0]
    found   = conn.execute("SELECT COUNT(*) FROM geocode_cache WHERE lat IS NOT NULL").fetchone()[0]
    missed  = total - found
    return total, found, missed


# ---------------------------------------------------------------------------
# Query building
# ---------------------------------------------------------------------------

def routing_key(eircode):
    """Extract routing key (first 3 chars) from eircode e.g. 'D14XY12' -> 'D14'."""
    eircode = eircode.strip().upper().replace(' ', '')
    return eircode[:3] if len(eircode) >= 3 else eircode


def build_query(address, county, eircode):
    """Return (query_string, query_type) to use for geocoding."""
    ec = eircode.strip()
    if ec:
        rk = routing_key(ec)
        return rk + ", Ireland", "eircode"
    addr = re.sub(r'\s+', ' ', address.strip())
    # Avoid appending county if it already appears in the address string,
    # and drop ", Ireland" suffix — it confuses Nominatim's parser for Irish addresses.
    county_str = county.strip()
    if county_str and county_str.lower() not in addr.lower():
        return f"{addr}, {county_str}", "address"
    return addr, "address"


# ---------------------------------------------------------------------------
# Geocoding — Nominatim primary, Photon fallback
# ---------------------------------------------------------------------------

def geocode_nominatim(query):
    """Call Nominatim. Returns (lat, lon, display_name) or (None, None, None)."""
    params = {
        "q":              query,
        "format":         "json",
        "limit":          1,
        "countrycodes":   "ie",
        "addressdetails": 0,
    }
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    results = resp.json()
    if results:
        r = results[0]
        return float(r["lat"]), float(r["lon"]), r.get("display_name", "")
    return None, None, None


def geocode_photon(query):
    """Call Photon (fuzzy fallback). Returns (lat, lon, display_name) or (None, None, None)."""
    params = {
        "q":    query,
        "limit": 1,
        "lang": "en",
        "bbox": IRELAND_BBOX,
    }
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(PHOTON_URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    features = resp.json().get("features", [])
    if features:
        coords = features[0]["geometry"]["coordinates"]
        props  = features[0]["properties"]
        display = ", ".join(filter(None, [
            props.get("name"), props.get("street"),
            props.get("city"), props.get("county"), props.get("country")
        ]))
        return float(coords[1]), float(coords[0]), display
    return None, None, None


def geocode(query, is_eircode=False):
    """
    Try local Nominatim (no rate limit, ~15ms). If it returns nothing and this
    is a full address query, fall back to Photon (~500ms, external).
    Returns (lat, lon, display_name, source) where source is 'nominatim' or 'photon'.
    """
    time.sleep(RATE_LIMIT)
    lat, lon, display = geocode_nominatim(query)
    if lat is not None:
        return lat, lon, display, "nominatim"

    # No Photon fallback for eircode-only queries — short codes don't work well
    if not is_eircode:
        # Photon is external — respect ~1 req/sec to avoid being blocked
        time.sleep(1.1)
        lat, lon, display = geocode_photon(query)
        if lat is not None:
            return lat, lon, display, "photon"

    return None, None, None, None


# ---------------------------------------------------------------------------
# Main geocoding loop
# ---------------------------------------------------------------------------

def run_geocoding():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    start_row = get_last_row(conn)
    print(f"Resuming from row {start_row:,}")

    total_rows  = 0
    geocoded    = 0
    cache_hits  = 0
    api_calls   = 0
    photon_hits = 0
    errors      = 0
    last_commit_row = start_row

    try:
        with open(SOURCE_CSV, encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=1):
                total_rows = row_num
                if row_num <= start_row:
                    continue

                address = row.get("Address", "")
                county  = row.get("County", "")
                eircode = row.get("Eircode", "")

                query, qtype = build_query(address, county, eircode)
                is_eircode = (qtype == "eircode")

                cached = lookup_cache(conn, query)
                if cached is not None:
                    cache_hits += 1
                else:
                    try:
                        lat, lon, display, source = geocode(query, is_eircode=is_eircode)
                        api_calls += 1
                        if lat is not None:
                            insert_cache(conn, query, lat, lon, display, source)
                            if source == "photon":
                                photon_hits += 1
                        else:
                            insert_cache(conn, query, None, None, NOT_FOUND, None)
                    except Exception as e:
                        errors += 1
                        print(f"\n[row {row_num}] Error geocoding '{query}': {e}")
                        # Exponential backoff: 60s, 120s, 300s, then cap at 300s
                        pause = min(60 * (2 ** (errors - 1)), 300)
                        print(f"Backing off {pause}s (error #{errors})")
                        time.sleep(pause)
                        if errors >= 5:
                            errors = 0  # reset after sustained backoff
                        continue

                geocoded += 1

                # Commit progress every BATCH_SIZE rows
                if geocoded % BATCH_SIZE == 0:
                    set_last_row(conn, row_num)
                    conn.commit()
                    last_commit_row = row_num
                    t, found, missed = cache_stats(conn)
                    print(
                        f"Row {row_num:>7,} | geocoded {geocoded:,} "
                        f"(+{api_calls} API [{photon_hits} via Photon], +{cache_hits} cache) | "
                        f"DB: {found:,} found, {missed:,} not-found"
                    )
                    api_calls   = 0
                    cache_hits  = 0
                    photon_hits = 0

    except KeyboardInterrupt:
        print("\nInterrupted — saving progress...")

    # Final commit
    if last_commit_row < total_rows:
        set_last_row(conn, total_rows if geocoded == total_rows else last_commit_row)
        conn.commit()

    t, found, missed = cache_stats(conn)
    print(f"\nDone. DB has {t:,} unique queries ({found:,} found, {missed:,} not-found).")
    conn.close()


# ---------------------------------------------------------------------------
# Export enriched CSV
# ---------------------------------------------------------------------------

def export_csv():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    last_row = get_last_row(conn)
    t, found, missed = cache_stats(conn)
    print(f"Cache: {t:,} queries, {found:,} geocoded, {missed:,} not found")
    print(f"Progress marker: row {last_row:,}")
    print(f"Writing to {OUTPUT_CSV} ...")

    written = 0
    enriched = 0

    with open(SOURCE_CSV, encoding="utf-8-sig", errors="replace") as fin, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:

        reader  = csv.DictReader(fin)
        fields  = reader.fieldnames + ["Latitude", "Longitude"]
        writer  = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()

        for row in reader:
            address = row.get("Address", "")
            county  = row.get("County", "")
            eircode = row.get("Eircode", "")
            query, _ = build_query(address, county, eircode)

            # Check full 7-char eircode key first — geocode_fix_routing.py stores
            # corrected results there for records whose routing key maps to the wrong county.
            ec_clean = eircode.strip().upper().replace(' ', '')
            cached = None
            if len(ec_clean) >= 7:
                cached = lookup_cache(conn, ec_clean + ", Ireland")

            if not (cached and cached[0] is not None):
                cached = lookup_cache(conn, query)
            # Also check raw address as key (used by BT eircode fix and planning_match.py)
            if not (cached and cached[0] is not None):
                raw_query = re.sub(r'\s+', ' ', address.strip())
                cached = lookup_cache(conn, raw_query)
            if cached and cached[0] is not None:
                row["Latitude"]  = round(cached[0], 6)
                row["Longitude"] = round(cached[1], 6)
                enriched += 1
            else:
                row["Latitude"]  = ""
                row["Longitude"] = ""

            writer.writerow(row)
            written += 1

    conn.close()
    print(f"Exported {written:,} rows, {enriched:,} with coordinates ({written-enriched:,} pending).")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def show_status():
    if not os.path.exists(DB_PATH):
        print("No geocode_cache.db found — geocoding has not started yet.")
        return
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA query_only = ON")
    last_row = conn.execute("SELECT last_row FROM progress WHERE id=1").fetchone()[0]
    t     = conn.execute("SELECT COUNT(*) FROM geocode_cache").fetchone()[0]
    found = conn.execute("SELECT COUNT(*) FROM geocode_cache WHERE lat IS NOT NULL").fetchone()[0]
    missed = t - found
    total_csv = 781501
    pct = last_row / total_csv * 100
    remaining = total_csv - last_row
    eta_hours = remaining * RATE_LIMIT / 3600  # worst case: no cache hits
    print(f"Progress : row {last_row:>7,} / {total_csv:,} ({pct:.1f}%)")
    print(f"Remaining: {remaining:,} rows")
    print(f"ETA (est): {eta_hours:.0f} h if no cache hits (will be faster)")
    print(f"DB cache : {t:,} unique queries — {found:,} found, {missed:,} not found")
    conn.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--export" in sys.argv:
        export_csv()
    elif "--status" in sys.argv:
        show_status()
    else:
        run_geocoding()
