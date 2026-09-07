#!/usr/bin/env python3
"""Bake the property-price *growth* heat-map dataset to static JSON.

Bins geocoded, full-market sales into a lat/lon grid and computes the median
sale price in an EARLY window and a LATE window per cell, then the percentage
change between them (price appreciation). Absolute price just restates the
obvious (Dublin is dear); appreciation shows where the market is heating up or
cooling — the non-obvious insight buyers/investors actually want.

Cells need enough sales in BOTH windows (min-count each) so the two medians are
stable, which naturally restricts the map to areas with real transaction volume.
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
import sys
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

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "frontend" / "public" / "data" / "heatmap.json"


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
          AND price > 0
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
        },
    )
    rows = cur.fetchall()
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
        "count": len(cells),
        "total_sales": sum(c[5] for c in cells),
        "palette": PALETTE,
        "breaks": breaks,     # 6 interior breakpoints (% change) -> 7 buckets
        "cells": cells,       # [lat, lon, pct_change, early_median_k, late_median_k, late_sale_count]
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))

    size_kb = out.stat().st_size / 1024
    print(f"Wrote {len(cells):,} cells ({payload['total_sales']:,} late-window sales) to {out} ({size_kb:.0f} KB)")
    print(f"  Early: {payload['early_window']}  Late: {payload['late_window']}  "
          f"cell={args.cell}°  min_count={args.min_count} each window")
    print(f"  Growth buckets (%): {breaks}")


if __name__ == "__main__":
    main()
