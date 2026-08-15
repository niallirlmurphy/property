#!/usr/bin/env python3
"""
Analyze whether Dublin property prices carry a premium for proximity (<1km) to
transport infrastructure, with attention to Luas Green Line, Luas Red Line, and
DART.

Method:
  1. For each usable Dublin sale, compute nearest-distance (metres) to each
     transport type via PostGIS KNN.
  2. Raw comparison: median price near (<1km) vs far (>=1km) per type.
  3. Distance dose-response bands (0-250m, 250-500m, 500-1km, 1-2km, >2km).
  4. Hedonic OLS on log(price) with neighbourhood (routing_key) + year fixed
     effects, so the premium is estimated WITHIN the same Eircode area and year
     -- controlling for the fact that lines run through richer/poorer areas.
     Property type included where available (subsample model).

Outlier handling: drops non-full-market-price sales and trims price to the
1st-99th percentile within Dublin to remove bulk/commercial records.

Usage:
    python3 scripts/analyze_transport_premium.py
Requires: pandas, numpy, statsmodels, psycopg2-binary, python-dotenv
"""

import os
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))
load_dotenv(os.path.join(os.getcwd(), "backend/.env"))

import statsmodels.formula.api as smf

TYPES = {
    "green": "a.category LIKE '%Green Line%'",
    "red": "a.category LIKE '%Red Line%'",
    "dart": "a.category LIKE '%DART%'",
    "any_rail": "a.amenity_type='transport' AND a.category NOT LIKE '%Bus%' "
                "AND a.category NOT LIKE '%Ferry%' AND a.category NOT LIKE '%Airport%'",
}


def fetch(conn):
    """One row per usable Dublin sale with nearest-distance (m) to each type."""
    subqueries = ",\n".join(
        f"""(SELECT ST_Distance(p.geog, a.geog) FROM amenities a
             WHERE {cond} ORDER BY p.geog <-> a.geog LIMIT 1) AS d_{key}"""
        for key, cond in TYPES.items()
    )
    sql = f"""
        SELECT p.id, p.price, p.routing_key,
               EXTRACT(YEAR FROM p.sale_date)::int AS year,
               p.property_type,
               {subqueries}
        FROM properties p
        WHERE p.county ILIKE 'Dublin'
          AND p.geog IS NOT NULL
          AND NOT COALESCE(p.not_full_market_price, FALSE)
          AND p.price > 0
    """
    return pd.read_sql(sql, conn)


def trim_outliers(df):
    lo, hi = df["price"].quantile([0.01, 0.99])
    n0 = len(df)
    df = df[(df["price"] >= lo) & (df["price"] <= hi)].copy()
    print(f"Outlier trim: kept {len(df):,}/{n0:,} sales "
          f"(price €{lo:,.0f}–€{hi:,.0f})")
    return df


def raw_near_far(df):
    print("\n" + "=" * 70)
    print("RAW: median price  <1km  vs  >=1km  (NOT adjusted for area/year)")
    print("=" * 70)
    for key in TYPES:
        col = f"d_{key}"
        near = df[df[col] < 1000]["price"]
        far = df[df[col] >= 1000]["price"]
        if len(near) == 0 or len(far) == 0:
            continue
        gap = near.median() / far.median() - 1
        print(f"  {key:9s} near n={len(near):>6,} med €{near.median():>9,.0f} | "
              f"far n={len(far):>6,} med €{far.median():>9,.0f} | "
              f"raw gap {gap:+6.1%}")


def dose_response(df):
    print("\n" + "=" * 70)
    print("DISTANCE BANDS: median price by nearest-distance (raw)")
    print("=" * 70)
    bands = [(0, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 1e9)]
    labels = ["0-250m", "250-500m", "500m-1km", "1-2km", ">2km"]
    for key in TYPES:
        col = f"d_{key}"
        print(f"\n  {key}:")
        for (lo, hi), lab in zip(bands, labels):
            seg = df[(df[col] >= lo) & (df[col] < hi)]["price"]
            if len(seg):
                print(f"    {lab:9s} n={len(seg):>6,}  median €{seg.median():>9,.0f}")


def hedonic(df):
    print("\n" + "=" * 70)
    print("HEDONIC OLS: log(price) ~ near_<type> + C(routing_key) + C(year)")
    print("Coefficient ≈ % price premium for a sale <1km from that line,")
    print("compared to a sale in the SAME Eircode area and year that is not.")
    print("=" * 70)

    d = df[df["routing_key"].notna()].copy()
    d["log_price"] = np.log(d["price"])
    d["year"] = d["year"].astype("category")
    for key in TYPES:
        d[f"near_{key}"] = (d[f"d_{key}"] < 1000).astype(int)

    # Keep routing_keys with enough sales for stable fixed effects
    vc = d["routing_key"].value_counts()
    keep = vc[vc >= 50].index
    d = d[d["routing_key"].isin(keep)]
    print(f"\nModel sample: {len(d):,} sales across {d['routing_key'].nunique()} "
          f"Eircode areas with >=50 sales.")

    # Combined model: Green, Red, DART together (+ area + year FE)
    terms = " + ".join(f"near_{k}" for k in ["green", "red", "dart"])
    model = smf.ols(f"log_price ~ {terms} + C(routing_key) + C(year)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["routing_key"]}
    )
    print("\n--- Adjusted premium for <1km proximity (within area & year) ---")
    print(f"{'line':10s} {'premium':>9s} {'95% CI':>20s} {'p':>8s}")
    for k in ["green", "red", "dart"]:
        b = model.params[f"near_{k}"]
        ci = model.conf_int().loc[f"near_{k}"]
        p = model.pvalues[f"near_{k}"]
        prem = np.exp(b) - 1
        lo, hi = np.exp(ci[0]) - 1, np.exp(ci[1]) - 1
        print(f"{k:10s} {prem:>+8.1%} [{lo:>+6.1%}, {hi:>+6.1%}] {p:>8.3f}")
    print(f"\nR² = {model.rsquared:.3f}, n = {int(model.nobs):,}")

    # Property-type-controlled subsample (where property_type known)
    sub = d[d["property_type"].notna()].copy()
    if len(sub) > 5000:
        vc2 = sub["routing_key"].value_counts()
        sub = sub[sub["routing_key"].isin(vc2[vc2 >= 30].index)]
        m2 = smf.ols(
            f"log_price ~ {terms} + C(property_type) + C(routing_key) + C(year)",
            data=sub,
        ).fit(cov_type="cluster", cov_kwds={"groups": sub["routing_key"]})
        print("\n--- Robustness: same model + property_type control "
              f"(subsample n={len(sub):,}) ---")
        for k in ["green", "red", "dart"]:
            prem = np.exp(m2.params[f"near_{k}"]) - 1
            p = m2.pvalues[f"near_{k}"]
            print(f"{k:10s} {prem:>+8.1%}  p={p:.3f}")


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        print("Fetching Dublin sales + transport distances (one-time spatial join)…")
        df = fetch(conn)
    finally:
        conn.close()
    print(f"Fetched {len(df):,} usable Dublin sales.")
    df = trim_outliers(df)
    raw_near_far(df)
    dose_response(df)
    hedonic(df)
    print("\nDone.")


if __name__ == "__main__":
    main()
