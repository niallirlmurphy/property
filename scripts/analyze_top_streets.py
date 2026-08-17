#!/usr/bin/env python3
"""Identify top streets for dedicated landing pages.

Groups full-market-price residential sales into "streets" by extracting the
street/estate name from the first address component (house numbers stripped)
and disambiguating with the area + county. Produces:
  - Top 20 streets by highest value (median sale price)
  - Top 20 streets by highest volume (transaction count)
"""
import os
import sys
import csv
import psycopg2
from collections import defaultdict
from statistics import median

sys.path.insert(0, os.path.dirname(__file__))
from street_key import street_key, APT_NAME_RE

MIN_TX_FOR_VALUE = 8      # streets need enough sales to be a credible "high value" page
MIN_TX_FLOOR = 3          # ignore near-unique addresses entirely
N_VALUE = 30              # top-N by median price
N_VOLUME = 20             # top-N by transaction count

APT_FRACTION_THRESHOLD = 0.5  # >=50% of sales flagged as apartments -> exclude as a block


def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(name="stream")
    cur.itersize = 20000
    cur.execute(
        """SELECT address_normalized, county, price
           FROM properties
           WHERE address_normalized IS NOT NULL
             AND not_full_market_price = FALSE
             AND price > 0 AND county IS NOT NULL"""
    )
    prices = defaultdict(list)
    apt_counts = defaultdict(int)
    display = {}
    n = 0
    for addr, county, price in cur:
        n += 1
        r = street_key(addr, county)
        if not r:
            continue
        key, disp, apt_flag = r
        prices[key].append(float(price))
        if apt_flag:
            apt_counts[key] += 1
        display[key] = disp
    conn.close()
    print(f"processed {n:,} sales into {len(prices):,} street groups")

    stats, excluded_apt = [], 0
    for key, pl in prices.items():
        c = len(pl)
        if c < MIN_TX_FLOOR:
            continue
        st, area, county = display[key]
        # exclude apartment complexes: block-style name OR mostly apartment-prefixed sales
        if APT_NAME_RE.search(st) or (apt_counts[key] / c) >= APT_FRACTION_THRESHOLD:
            excluded_apt += 1
            continue
        stats.append({
            "street": st, "area": area, "county": county,
            "count": c, "median": median(pl),
            "avg": sum(pl) / c, "total": sum(pl),
        })
    print(f"excluded {excluded_apt:,} apartment-complex groups")

    # Top-N by VALUE (median price), requiring enough transactions
    by_value = sorted(
        [s for s in stats if s["count"] >= MIN_TX_FOR_VALUE],
        key=lambda s: s["median"], reverse=True,
    )[:N_VALUE]

    # Top-N by VOLUME (transaction count), excluding ones already in value list
    value_keys = {(s["street"], s["area"], s["county"]) for s in by_value}
    by_volume = sorted(stats, key=lambda s: s["count"], reverse=True)
    top_volume = []
    for s in by_volume:
        k = (s["street"], s["area"], s["county"])
        if k in value_keys:
            continue
        top_volume.append(s)
        if len(top_volume) == N_VOLUME:
            break

    def fmt(rows, label):
        print(f"\n===== {label} =====")
        print(f"{'#':>2}  {'Street, Area, County':<52} {'Tx':>4} {'Median':>10} {'Avg':>10}")
        for i, s in enumerate(rows, 1):
            name = f"{s['street']}, {s['area']}, {s['county']}"[:50]
            print(f"{i:>2}  {name:<52} {s['count']:>4} {s['median']:>10,.0f} {s['avg']:>10,.0f}")

    fmt(by_value, "TOP %d BY VALUE (median price, min %d tx)" % (N_VALUE, MIN_TX_FOR_VALUE))
    fmt(top_volume, "TOP %d BY VOLUME (transaction count)" % N_VOLUME)

    # write CSV for the record
    out = "data/top_streets_analysis.csv"
    os.makedirs("data", exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank_type", "rank", "street", "area", "county", "tx_count", "median_price", "avg_price", "total_value"])
        for i, s in enumerate(by_value, 1):
            w.writerow(["value", i, s["street"], s["area"], s["county"], s["count"], round(s["median"]), round(s["avg"]), round(s["total"])])
        for i, s in enumerate(top_volume, 1):
            w.writerow(["volume", i, s["street"], s["area"], s["county"], s["count"], round(s["median"]), round(s["avg"]), round(s["total"])])
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
