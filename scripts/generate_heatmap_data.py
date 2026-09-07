#!/usr/bin/env python3
"""Bake the property-price heat-map dataset to static JSON.

Bins geocoded, full-market sales into a lat/lon grid and computes the median
sale price per cell (dropping sparse cells for stable medians and privacy).
The output is a small static file rendered by the /heatmap page — no per-visitor
database load. Regenerate after each PPR sync, like the other page data.

Usage:
    export $(grep '^DATABASE_URL=' backend/.env | xargs)
    python3 scripts/generate_heatmap_data.py                 # defaults
    python3 scripts/generate_heatmap_data.py --since-year 2022 --cell 0.012 --min-count 8

Output: frontend/public/data/heatmap.json
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

# 7-class ColorBrewer YlOrRd (light/cheap -> dark/expensive). The frontend reads
# this palette + the computed breaks from the JSON so the map and legend agree.
PALETTE = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"]

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


def compute_breaks(medians):
    """Six interior breakpoints -> seven quantile buckets across the cells.

    Quantile (rather than equal-interval) breaks give the map good contrast even
    though prices are heavily right-skewed."""
    s = sorted(medians)
    n_buckets = len(PALETTE)
    return [round(quantile(s, i / n_buckets)) for i in range(1, n_buckets)]


def main():
    ap = argparse.ArgumentParser(description="Bake the heat-map dataset to static JSON")
    ap.add_argument("--since-year", type=int, default=datetime.now().year - 5,
                    help="Only include sales from this year onward (default: last 5 years, for current values)")
    ap.add_argument("--cell", type=float, default=0.01,
                    help="Grid cell size in degrees (~1.1km lat; default 0.01)")
    ap.add_argument("--min-count", type=int, default=5,
                    help="Minimum sales per cell to include it (stability + privacy; default 5)")
    ap.add_argument("--out", type=str, default=str(OUT_PATH), help="Output JSON path")
    args = ap.parse_args()

    conn = psycopg2.connect(load_database_url())
    cur = conn.cursor()
    # Median price per grid cell, pushed down to Postgres. floor(coord/cell) keys
    # the cell; the cell centre is (key + 0.5) * cell.
    cur.execute(
        """
        SELECT
            floor(latitude / %(cell)s)  AS gy,
            floor(longitude / %(cell)s) AS gx,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
            COUNT(*) AS n
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND not_full_market_price = FALSE
          AND price > 0
          AND sale_date >= %(start)s
          AND latitude  BETWEEN %(lat_min)s AND %(lat_max)s
          AND longitude BETWEEN %(lon_min)s AND %(lon_max)s
        GROUP BY gy, gx
        HAVING COUNT(*) >= %(min_count)s
        """,
        {
            "cell": args.cell,
            "start": f"{args.since_year}-01-01",
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
    medians = []
    for gy, gx, median_price, n in rows:
        lat = round((float(gy) + 0.5) * args.cell, 5)
        lon = round((float(gx) + 0.5) * args.cell, 5)
        m = int(round(median_price / 1000.0) * 1000)  # round to nearest €1k
        cells.append([lat, lon, m, int(n)])
        medians.append(m)

    breaks = compute_breaks(medians)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "since_year": args.since_year,
        "cell_deg": args.cell,
        "cell_half_deg": half,
        "min_count": args.min_count,
        "count": len(cells),
        "total_sales": sum(c[3] for c in cells),
        "palette": PALETTE,
        "breaks": breaks,     # 6 interior breakpoints -> 7 buckets
        "cells": cells,       # [lat, lon, median_price, sale_count]
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))

    size_kb = out.stat().st_size / 1024
    print(f"Wrote {len(cells):,} cells ({payload['total_sales']:,} sales) to {out} ({size_kb:.0f} KB)")
    print(f"  Window: {args.since_year}+  cell={args.cell}°  min_count={args.min_count}")
    print(f"  Median-price buckets (€): {breaks}")


if __name__ == "__main__":
    main()
