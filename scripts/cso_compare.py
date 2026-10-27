"""Check our PPR medians against the CSO's for the last full year, by Eircode
routing key and by county, and flag areas that disagree.

Compares SECOND-HAND homes only: they're the like-for-like set. New homes
differ for known reasons (PPR prices are ex-VAT; ~90% of new-home sales on
PPR have no Eircode, so they're missing from our routing-key figures), and
the CSO excludes non-household buyers and non-market sales.

A large gap on second-hand homes usually means bad geocodes or Eircodes,
bulk sales we haven't excluded, or a mis-assigned county.

    python3 scripts/cso_compare.py [--year 2025] [--threshold 10]

Writes logs/cso/compare_<year>.md (+ .json). One aggregate query over a
single year of sales (sale_date index), with a statement timeout.
"""
import argparse
import json
import os
import statistics
import sys

import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from cso_api import EVENT, load, routing_key_names

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(ROOT, "logs", "cso")
MIN_SALES = 30   # both sides need this many second-hand sales to be compared

SQL = """
SELECT GROUPING(routing_key) AS by_county, routing_key, county,
       count(*) FILTER (WHERE second_hand) AS n,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY price) FILTER (WHERE second_hand) AS median
FROM (
    SELECT routing_key, county, price,
           description ~* 'second' AND NOT not_full_market_price AS second_hand
    FROM properties
    WHERE sale_date >= %s AND sale_date < %s
) s
GROUP BY GROUPING SETS ((routing_key), (county))
"""


def ppr_medians(year: int):
    load_dotenv(os.path.join(ROOT, "backend", ".env"))
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 60000")
        cur.execute(SQL, (f"{year}-01-01", f"{year + 1}-01-01"))
        rk, county = {}, {}
        for by_county, key, cty, n, med in cur.fetchall():
            if by_county and key is None and cty:
                county[cty] = (n, med)
            elif not by_county and key:
                rk[key] = (n, med)
        return rk, county
    finally:
        conn.close()


def compare(rows):
    """rows: [(key, name, cso_n, cso_med, ppr_n, ppr_med)] -> rows with % gap."""
    out = []
    for key, name, cn, cm, pn, pm in rows:
        if cm and pm and (cn or 0) >= MIN_SALES and (pn or 0) >= MIN_SALES:
            out.append({"key": key, "name": name, "cso_n": int(cn), "cso_median": cm,
                        "ppr_n": pn, "ppr_median": round(pm), "gap_pct": round((pm - cm) / cm * 100, 1)})
    return out


def summary(rows, threshold):
    gaps = [r["gap_pct"] for r in rows]
    return {
        "compared": len(rows),
        "median_gap_pct": round(statistics.median(gaps), 1) if gaps else None,
        "median_abs_gap_pct": round(statistics.median(abs(g) for g in gaps), 1) if gaps else None,
        "within_5pct": sum(abs(g) <= 5 for g in gaps),
        "flagged": sum(abs(g) > threshold for g in gaps),
    }


def main():
    ap = argparse.ArgumentParser(description="Compare PPR and CSO second-hand medians.")
    ap.add_argument("--year", type=int, help="year to compare (default: the CSO's latest full year)")
    ap.add_argument("--threshold", type=float, default=10.0, help="flag gaps above this %%")
    ap.add_argument("--refresh", action="store_true", help="re-download CSO tables")
    args = ap.parse_args()

    by_rk, by_county = load("HPA04", args.refresh), load("HPA02", args.refresh)
    year = args.year or int(by_rk.labels("Year")[-1])
    ppr_rk, ppr_county = ppr_medians(year)

    def rk_cso(stat, key):
        return by_rk.get(Statistic=stat, Year=str(year), Dwelling_Status="Existing", Eircode_Output=key,
                         Stamp_Duty_Event=EVENT, Type_of_Buyer="All Buyer Types")

    def county_cso(stat, name):
        return by_county.get(Statistic=stat, Year=str(year), County=name, Dwelling_Status="Existing",
                             Stamp_Duty_Event=EVENT, Type_of_Buyer="Household Buyer - All", Type_of_Sale="Market")

    rk_rows = compare([
        (k, n, rk_cso("Volume of Sales", k), rk_cso("Median Price", k), *ppr_rk.get(k, (None, None)))
        for k, n in sorted(routing_key_names(by_rk).items())])
    county_rows = compare([
        (c, c, county_cso("Volume of Sales", c), county_cso("Median Price", c), *ppr_county.get(c, (None, None)))
        for c in by_county.labels("County") if c != "All Counties"])

    result = {"year": year, "threshold_pct": args.threshold,
              "routing_keys": {"summary": summary(rk_rows, args.threshold), "rows": rk_rows},
              "counties": {"summary": summary(county_rows, args.threshold), "rows": county_rows}}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"compare_{year}.json"), "w") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)

    lines = [f"# PPR vs CSO, second-hand homes, {year}", "",
             f"CSO: market-based household purchases, by deed date ({EVENT}). "
             f"PPR: full-market-price second-hand sales. Compared where both have ≥{MIN_SALES} sales.", ""]
    for label, rows in (("Routing keys", rk_rows), ("Counties", county_rows)):
        s = summary(rows, args.threshold)
        lines += [f"## {label}", "",
                  f"{s['compared']} compared; typical gap {s['median_gap_pct']}% "
                  f"(±{s['median_abs_gap_pct']}%); {s['within_5pct']} within 5%; "
                  f"**{s['flagged']} over {args.threshold:g}%**", ""]
        flagged = sorted((r for r in rows if abs(r["gap_pct"]) > args.threshold), key=lambda r: -abs(r["gap_pct"]))
        if flagged:
            lines += ["| Area | CSO sales | CSO median | PPR sales | PPR median | Gap |", "|---|---|---|---|---|---|"]
            lines += [f"| {r['key']} {r['name'] if r['name'] != r['key'] else ''} | {r['cso_n']:,} | €{r['cso_median']:,.0f} "
                      f"| {r['ppr_n']:,} | €{r['ppr_median']:,} | {r['gap_pct']:+.1f}% |" for r in flagged]
            lines.append("")
    path = os.path.join(OUT_DIR, f"compare_{year}.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
