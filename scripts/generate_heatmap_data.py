#!/usr/bin/env python3
"""Bake the property-price *growth* heat-map dataset to static JSON.

Bins geocoded, full-market sales into a lat/lon grid and computes the median
sale price in an EARLY window and a LATE window per cell, then the percentage
change between them (price appreciation). Absolute price just restates the
obvious (Dublin is dear); appreciation shows where the market is heating up or
cooling — the non-obvious insight buyers/investors actually want.

Cells need enough sales in BOTH windows (min-count each) so the two medians are
stable, which naturally restricts the map to areas with real transaction volume.

To measure price movement rather than a change in *what* sold, the query is a
like-for-like RESALE index: new-build sales are excluded (bulk scheme completions
otherwise collapse a small area's median), as are individual price extremes
(parking/share transfers below the floor, trophy homes above the ceiling) and
bulk unit-range sales recorded as one high price. See PRICE_FLOOR / PRICE_CEIL /
BULK_ADDR_RE and the description filter.

The output is a small static file rendered by the /heatmap page — no per-visitor
database load. Regenerate after each PPR sync, like the other page data.

Usage:
    export $(grep '^DATABASE_URL=' backend/.env | xargs)
    python3 scripts/generate_heatmap_data.py                 # defaults
    python3 scripts/generate_heatmap_data.py --cell 0.05 --min-count 12

Output: frontend/public/data/heatmap.json
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

# 7-class diverging palette (ColorBrewer RdBu, reversed): blue = slower growth /
# cooling, near-white = middling, red = fastest appreciation. The frontend reads
# this palette + the computed breaks from the JSON so the map and legend agree.
PALETTE = ["#2166ac", "#67a9cf", "#d1e5f0", "#f7f7f7", "#fddbc7", "#ef8a62", "#b2182b"]

# Ireland bounds (same box used by the geocoder's validation layer).
LAT_MIN, LAT_MAX = 51.4, 55.5
LON_MIN, LON_MAX = -10.7, -5.4

# Row-level sanity band on individual sale prices. Below the floor are parking
# spaces, share/partial-interest transfers and sites masquerading as full-market
# sales; above the ceiling are trophy homes and multi-property deals. Both are
# unrepresentative of the local market and skew a small area's median. Together
# these bounds plus the bulk filter touch ~2% of rows.
PRICE_FLOOR = 50_000
PRICE_CEIL = 3_000_000
# A single row whose address spans a unit range ("Apt 1-10", "Units 1 to 76") is
# a bulk/portfolio sale recorded as one high price — not a single-dwelling sale.
# Postgres POSIX regex (case-insensitive via !~*): digits, dash or "to", digits.
BULK_ADDR_RE = r'[0-9]+ *(-|to) *[0-9]+'

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "frontend" / "public" / "data" / "heatmap.json"

# --- Named-locality ranking (top/bottom price growth) ------------------------
# The grid cells have no names, so for the ranked tables we attribute a place
# name to each sale from its address and aggregate by locality. We only keep
# rows where a real place name can be attributed (user requirement).
COUNTIES = {
    "carlow", "cavan", "clare", "cork", "donegal", "dublin", "galway", "kerry",
    "kildare", "kilkenny", "laois", "leitrim", "limerick", "longford", "louth",
    "mayo", "meath", "monaghan", "offaly", "roscommon", "sligo", "tipperary",
    "waterford", "westmeath", "wexford", "wicklow",
}
DUBLIN_PC = re.compile(r"\bDublin\s+\d{1,2}\b", re.I)
# A candidate whose final word is one of these is a street/estate/feature name,
# not an attributable place — dropped. Single-word places ("Fairhill") survive.
NON_PLACE_SUFFIX = {
    "road", "street", "st", "avenue", "ave", "lane", "ln", "drive", "dr",
    "terrace", "close", "court", "ct", "grove", "crescent", "cres", "way",
    "boulevard", "square", "sq", "row", "walk", "rise", "heights", "height",
    "park", "view", "gardens", "garden", "green", "manor", "wood", "woods",
    "hall", "place", "downs", "meadows", "vale", "quay", "mews", "racecourse",
    "estate", "villas", "cottages", "point", "demesne", "lawn", "lawns", "grange",
}


def _is_county_tok(tok: str) -> bool:
    return tok.replace("Co.", "").replace("County", "").strip().lower() in COUNTIES


def attribute_locality(address: str, county: str):
    """Best-effort place name from an address, or None if not attributable.

    Dublin uses its postal district (clean, high volume); elsewhere the token
    before the county/postcode is the town. Street/estate names are rejected."""
    if not address:
        return None
    if county and county.strip().lower() == "dublin":
        m = DUBLIN_PC.search(address)
        if m:
            return re.sub(r"\s+", " ", m.group(0).title())
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) < 2:
        return None
    idx = len(parts) - 1
    while idx >= 0 and (_is_county_tok(parts[idx]) or DUBLIN_PC.fullmatch(parts[idx] or "")):
        idx -= 1
    if idx < 0:
        return None
    words = parts[idx].split()
    while len(words) > 1 and words[-1].lower().strip(".") in COUNTIES:
        words = words[:-1]  # strip a county glued onto the same comma-part
    loc = " ".join(words)
    if not loc or len(loc) < 3 or re.search(r"\d", loc):
        return None
    if words[-1].lower().strip(".") in NON_PLACE_SUFFIX:
        return None
    return loc


def build_locality_tables(conn, early_start, early_end, late_end, args):
    """Return (top, bottom) lists of [name, county, pct, early_k, late_k, n]."""
    cur = conn.cursor(name="loc_stream")  # server-side cursor to stream
    cur.itersize = 20000
    cur.execute(
        """
        SELECT county, address_normalized, price::float, sale_date
        FROM properties
        WHERE not_full_market_price = FALSE
          AND address_normalized IS NOT NULL
          -- Resale only, matching the map (exclude bulk new-build schemes).
          AND description NOT ILIKE %s AND description NOT ILIKE %s
          AND price BETWEEN %s AND %s              -- drop non-home / trophy extremes
          AND address_normalized !~* %s            -- drop bulk unit-range sales
          AND sale_date >= %s AND sale_date < %s
        """,
        ("%new%", "%nua%", PRICE_FLOOR, PRICE_CEIL, BULK_ADDR_RE, early_start, late_end),
    )
    early_cut = datetime.strptime(early_end, "%Y-%m-%d").date()
    early = defaultdict(list)
    late = defaultdict(list)
    meta = {}
    for county, addr, price, sd in cur:
        loc = attribute_locality(addr, county)
        if not loc:
            continue
        key = (loc.lower(), (county or "").strip())
        meta.setdefault(key, (loc, county))
        (early if sd < early_cut else late)[key].append(price)
    cur.close()

    ranked = []
    for key in set(early) & set(late):
        if len(early[key]) < args.loc_min_count or len(late[key]) < args.loc_min_count:
            continue
        em, lm = statistics.median(early[key]), statistics.median(late[key])
        if em < args.min_median or lm < args.min_median:
            continue
        pct = round((lm - em) / em * 100, 1)
        if pct < args.min_growth or pct > args.max_growth:
            continue
        loc, county = meta[key]
        ranked.append([loc, county, pct, int(round(em / 1000)), int(round(lm / 1000)),
                       len(late[key])])
    ranked.sort(key=lambda r: r[2], reverse=True)
    n = args.loc_top
    return ranked[:n], list(reversed(ranked[-n:]))


def load_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Fall back to backend/.env so the script works without exporting first.
    env_path = REPO / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("DATABASE_URL not set (export it or add it to backend/.env)")


def quantile(sorted_vals, q: float):
    """Linear-interpolated quantile of an already-sorted list."""
    if not sorted_vals:
        return None
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def compute_breaks(values):
    """Six interior breakpoints -> seven quantile buckets across the cells.

    Quantile (rather than equal-interval) breaks self-calibrate the diverging
    scale to the distribution: roughly half the cells fall in the cool buckets
    (below-median growth) and half in the warm buckets (above-median), so the
    map reads as relative out/under-performance rather than 'everything rose'."""
    s = sorted(values)
    n_buckets = len(PALETTE)
    return [round(quantile(s, i / n_buckets), 1) for i in range(1, n_buckets)]


def main():
    now_year = datetime.now().year
    ap = argparse.ArgumentParser(description="Bake the price-growth heat-map dataset to static JSON")
    ap.add_argument("--early-from", type=int, default=now_year - 6,
                    help="First year of the EARLY window (default: 6 years ago)")
    ap.add_argument("--early-to", type=int, default=now_year - 3,
                    help="Exclusive upper year of the EARLY window (default: 3 years ago)")
    ap.add_argument("--late-from", type=int, default=now_year - 3,
                    help="First year of the LATE window (default: 3 years ago)")
    ap.add_argument("--late-to", type=int, default=now_year + 1,
                    help="Exclusive upper year of the LATE window (default: includes current year)")
    ap.add_argument("--cell", type=float, default=0.04,
                    help="Grid cell size in degrees (~4.4km lat; default 0.04 — coarser than "
                         "the price map so two-window medians are stable)")
    ap.add_argument("--min-count", type=int, default=20,
                    help="Minimum sales per cell IN EACH window (stability + privacy; default 20). "
                         "Higher = fewer, more reliable cells; low-volume rural cells whose median "
                         "is driven by which few properties happened to sell are dropped")
    ap.add_argument("--min-growth", type=float, default=-40.0,
                    help="Drop cells with growth below this %% (composition outliers; default -40)")
    ap.add_argument("--max-growth", type=float, default=100.0,
                    help="Drop cells with growth above this %% — a home market does not double its "
                         "median in a few years, so these are property-mix artifacts (default 100)")
    ap.add_argument("--min-median", type=int, default=50000,
                    help="Drop cells whose median in either window is below this (€). Excludes "
                         "cells dominated by non-home sales — sites, derelict, parking, shares — "
                         "whose changing mix otherwise produces absurd growth %% (default 50000)")
    ap.add_argument("--loc-min-count", type=int, default=100,
                    help="Minimum sales per named locality IN EACH window for the ranked tables "
                         "(default 100). Named localities pool far more sales than a grid cell, and "
                         "a high bar is what makes the ranking meaningful: below it the median swings "
                         "on which few properties happened to sell, producing spurious ±extremes")
    ap.add_argument("--loc-top", type=int, default=15,
                    help="How many localities to list in each of the top/bottom tables (default 15)")
    ap.add_argument("--out", type=str, default=str(OUT_PATH), help="Output JSON path")
    args = ap.parse_args()

    early_start = f"{args.early_from}-01-01"
    early_end = f"{args.early_to}-01-01"
    late_start = f"{args.late_from}-01-01"
    late_end = f"{args.late_to}-01-01"

    conn = psycopg2.connect(load_database_url())
    cur = conn.cursor()
    # Early- and late-window median price per grid cell, pushed down to Postgres.
    # floor(coord/cell) keys the cell; the cell centre is (key + 0.5) * cell.
    # FILTER splits the two windows in a single scan; HAVING keeps only cells with
    # enough sales in both so the percentage change is meaningful.
    cur.execute(
        """
        SELECT
            floor(latitude / %(cell)s)  AS gy,
            floor(longitude / %(cell)s) AS gx,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)
                FILTER (WHERE sale_date >= %(early_start)s AND sale_date < %(early_end)s) AS early_median,
            COUNT(*) FILTER (WHERE sale_date >= %(early_start)s AND sale_date < %(early_end)s) AS early_n,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)
                FILTER (WHERE sale_date >= %(late_start)s AND sale_date < %(late_end)s) AS late_median,
            COUNT(*) FILTER (WHERE sale_date >= %(late_start)s AND sale_date < %(late_end)s) AS late_n
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND not_full_market_price = FALSE
          -- Resale market only. New-build schemes complete and sell in bulk in a
          -- single window, swamping a small area with cheaper apartments and
          -- collapsing its median — a composition shift, not a price move. The PPR
          -- 'description' distinguishes New vs Second-Hand ('Nua' = Irish 'new').
          AND description NOT ILIKE '%%new%%' AND description NOT ILIKE '%%nua%%'
          -- Drop non-home/trophy price extremes and bulk unit-range sales that
          -- would skew a cell's median (see PRICE_FLOOR/PRICE_CEIL/BULK_ADDR_RE).
          AND price BETWEEN %(price_floor)s AND %(price_ceil)s
          AND (address_normalized IS NULL OR address_normalized !~* %(bulk_re)s)
          AND sale_date >= %(early_start)s AND sale_date < %(late_end)s
          AND latitude  BETWEEN %(lat_min)s AND %(lat_max)s
          AND longitude BETWEEN %(lon_min)s AND %(lon_max)s
        GROUP BY gy, gx
        HAVING COUNT(*) FILTER (WHERE sale_date >= %(early_start)s AND sale_date < %(early_end)s) >= %(min_count)s
           AND COUNT(*) FILTER (WHERE sale_date >= %(late_start)s AND sale_date < %(late_end)s) >= %(min_count)s
        """,
        {
            "cell": args.cell,
            "early_start": early_start, "early_end": early_end,
            "late_start": late_start, "late_end": late_end,
            "lat_min": LAT_MIN, "lat_max": LAT_MAX,
            "lon_min": LON_MIN, "lon_max": LON_MAX,
            "min_count": args.min_count,
            "price_floor": PRICE_FLOOR, "price_ceil": PRICE_CEIL,
            "bulk_re": BULK_ADDR_RE,
        },
    )
    rows = cur.fetchall()

    # Ranked named-locality tables (top/bottom growth) share the same windows as
    # the map but aggregate by attributed place name rather than by grid cell.
    top_localities, bottom_localities = build_locality_tables(
        conn, early_start, early_end, late_end, args)
    conn.close()

    if not rows:
        sys.exit("No cells produced — check the filters / database connection.")

    half = args.cell / 2.0
    cells = []
    pct_changes = []
    for gy, gx, early_median, early_n, late_median, late_n in rows:
        if not early_median or early_median <= 0 or not late_median:
            continue
        # Skip cells dominated by non-home sales (sites/derelict/parking): their
        # low, mix-driven medians produce nonsense growth figures.
        if float(early_median) < args.min_median or float(late_median) < args.min_median:
            continue
        lat = round((float(gy) + 0.5) * args.cell, 5)
        lon = round((float(gx) + 0.5) * args.cell, 5)
        early_k = int(round(float(early_median) / 1000.0))  # €thousands
        late_k = int(round(float(late_median) / 1000.0))
        pct = round((float(late_median) - float(early_median)) / float(early_median) * 100, 1)
        # Trim implausible growth: at cell scale these are property-mix shifts, not
        # real appreciation, and a wild tooltip figure undermines the whole map.
        if pct < args.min_growth or pct > args.max_growth:
            continue
        # [lat, lon, pct_change, early_median_k, late_median_k, late_sale_count]
        cells.append([lat, lon, pct, early_k, late_k, int(late_n)])
        pct_changes.append(pct)

    breaks = compute_breaks(pct_changes)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metric": "price_growth_pct",
        "early_window": f"{args.early_from}–{args.early_to - 1}",
        "late_window": f"{args.late_from}–{args.late_to - 1}",
        "cell_deg": args.cell,
        "cell_half_deg": half,
        "min_count": args.min_count,
        "price_floor": PRICE_FLOOR,
        "price_ceil": PRICE_CEIL,
        "count": len(cells),
        "total_sales": sum(c[5] for c in cells),
        "palette": PALETTE,
        "breaks": breaks,     # 6 interior breakpoints (% change) -> 7 buckets
        "cells": cells,       # [lat, lon, pct_change, early_median_k, late_median_k, late_sale_count]
        "loc_min_count": args.loc_min_count,
        # [name, county, pct_change, early_median_k, late_median_k, late_sale_count]
        "top_localities": top_localities,
        "bottom_localities": bottom_localities,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))

    size_kb = out.stat().st_size / 1024
    print(f"Wrote {len(cells):,} cells ({payload['total_sales']:,} late-window sales) to {out} ({size_kb:.0f} KB)")
    print(f"  Early: {payload['early_window']}  Late: {payload['late_window']}  "
          f"cell={args.cell}°  min_count={args.min_count} each window")
    print(f"  Growth buckets (%): {breaks}")
    print(f"  Locality tables: {len(top_localities)} top / {len(bottom_localities)} bottom "
          f"(>= {args.loc_min_count}/window)")
    if top_localities:
        t = top_localities[0]
        print(f"    Fastest: {t[0]} ({t[1]}) {t[2]:+.1f}%  €{t[3]}k→€{t[4]}k  n={t[5]}")
    if bottom_localities:
        b = bottom_localities[0]
        print(f"    Slowest: {b[0]} ({b[1]}) {b[2]:+.1f}%  €{b[3]}k→€{b[4]}k  n={b[5]}")


if __name__ == "__main__":
    main()
