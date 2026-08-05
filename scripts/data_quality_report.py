#!/usr/bin/env python3
"""
Repeatable data quality report for the PPR `properties` table.

Runs a suite of read-only checks (completeness, geocoding quality, price/date
sanity, duplicates, distribution, taxonomy, referential consistency) and prints
a ranked report. Nothing is mutated.

Usage:
    # Human-readable report (default)
    python3 scripts/data_quality_report.py

    # Machine-readable output (for CI / dashboards / diffing over time)
    python3 scripts/data_quality_report.py --json

    # Exit non-zero if any check breaches a threshold (for cron / CI gating)
    python3 scripts/data_quality_report.py --fail-on-warn

    # Write a JSON snapshot to disk for trend tracking
    python3 scripts/data_quality_report.py --json --out logs/dq_$(date +%F).json

Environment:
    DATABASE_URL   (required) Supabase/Postgres connection string.
                   Loaded from backend/.env if not already in the environment.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv

# Ireland bounding box (matches geocoding validation in CLAUDE.md).
IE_BOUNDS = dict(min_lat=51.4, max_lat=55.5, min_lon=-10.7, max_lon=-5.4)

# Thresholds that flag a check as WARN. Tune as data quality improves.
THRESHOLDS = {
    "centroid_pct": 5.0,          # % of rows stuck on generic centroids
    "needs_geocoding": 5000,      # count flagged needs_geocoding
    "recent_geocode_pct": 98.0,   # min % geocoded for current-year sales
    "duplicate_rows": 2000,       # same-key rows above this => possible import bug
                                  #   (~1,172 is the legit PPR-source baseline)
    "county_count": 26,           # expected distinct counties (exact)
    "oob_coords": 0,              # out-of-Ireland coordinates (must be 0)
    "unflagged_outliers": 2000,   # price outliers not flagged not_full_market_price
}

# Key columns whose completeness we report.
COMPLETENESS_COLS = [
    "latitude", "longitude", "eircode", "address", "address_normalized",
    "sale_date", "price", "county", "property_type", "bedrooms", "routing_key",
]


class DQ:
    def __init__(self, conn):
        self.cur = conn.cursor()
        self.conn = conn
        self.checks = []  # list of dicts: {name, status, detail, metrics}

    def q(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self.cur.fetchall()

    def scalar(self, sql, params=None):
        return self.q(sql, params)[0][0]

    def add(self, name, status, detail, **metrics):
        self.checks.append(
            {"name": name, "status": status, "detail": detail, "metrics": metrics}
        )

    def column_exists(self, col):
        return self.scalar(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name='properties' AND column_name=%s)", (col,)
        )

    # --- individual checks -------------------------------------------------

    def run_all(self):
        self.total = self.scalar("SELECT COUNT(*) FROM properties")
        self.completeness()
        self.geocoding_quality()
        self.price_sanity()
        self.date_sanity()
        self.duplicates()
        self.county_distribution()
        self.property_type_provenance()
        self.eircode_consistency()
        self.recent_geocode_coverage()
        return self.checks

    def completeness(self):
        cols = {}
        for c in COMPLETENESS_COLS:
            if not self.column_exists(c):
                cols[c] = None
                continue
            nulls = self.scalar(f"SELECT COUNT(*) FROM properties WHERE {c} IS NULL")
            cols[c] = {
                "null": nulls,
                "present": self.total - nulls,
                "pct_present": round(100 * (self.total - nulls) / self.total, 1) if self.total else 0,
            }
        self.add("completeness", "info", "NULL/present counts per key column", columns=cols, total_rows=self.total)

    def geocoding_quality(self):
        b = IE_BOUNDS
        oob = self.scalar(
            "SELECT COUNT(*) FROM properties WHERE latitude IS NOT NULL AND "
            "(latitude < %(min_lat)s OR latitude > %(max_lat)s OR "
            " longitude < %(min_lon)s OR longitude > %(max_lon)s)", b)
        centroids = self.scalar("""
            WITH c AS (
                SELECT latitude, longitude FROM properties
                WHERE latitude IS NOT NULL
                GROUP BY latitude, longitude
                HAVING COUNT(DISTINCT address) >= 100
            )
            SELECT COUNT(*) FROM properties p JOIN c
              ON ABS(p.latitude - c.latitude) < 1e-6
             AND ABS(p.longitude - c.longitude) < 1e-6
        """)
        centroid_pct = round(100 * centroids / self.total, 2) if self.total else 0
        needs_geo = None
        if self.column_exists("needs_geocoding"):
            needs_geo = self.scalar("SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE")

        status = "ok"
        if oob > THRESHOLDS["oob_coords"]:
            status = "fail"
        elif centroid_pct > THRESHOLDS["centroid_pct"] or (needs_geo or 0) > THRESHOLDS["needs_geocoding"]:
            status = "warn"
        self.add(
            "geocoding_quality", status,
            f"{oob:,} out-of-bounds; {centroids:,} at centroids ({centroid_pct}%); "
            f"needs_geocoding={needs_geo if needs_geo is not None else 'n/a'}",
            out_of_bounds=oob, centroid_rows=centroids, centroid_pct=centroid_pct,
            needs_geocoding=needs_geo,
        )

    def price_sanity(self):
        mn, mx, avg, med = self.q(
            "SELECT MIN(price), MAX(price), AVG(price), "
            "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) FROM properties")[0]
        lo = self.scalar("SELECT COUNT(*) FROM properties WHERE price < 10000")
        hi = self.scalar("SELECT COUNT(*) FROM properties WHERE price > 20000000")
        unflagged = None
        if self.column_exists("not_full_market_price"):
            unflagged = self.scalar(
                "SELECT COUNT(*) FROM properties WHERE (price < 10000 OR price > 20000000) "
                "AND not_full_market_price = FALSE")
        status = "ok"
        if unflagged is not None and unflagged > THRESHOLDS["unflagged_outliers"]:
            status = "warn"
        self.add(
            "price_sanity", status,
            f"min={mn:,.0f} max={mx:,.0f} avg={avg:,.0f} median={med:,.0f}; "
            f"<10k={lo:,} >20M={hi:,}; unflagged_outliers={unflagged}",
            min=float(mn), max=float(mx), avg=float(avg), median=float(med),
            below_10k=lo, above_20m=hi, unflagged_outliers=unflagged,
        )

    def date_sanity(self):
        mn, mx = self.q("SELECT MIN(sale_date), MAX(sale_date) FROM properties")[0]
        fut = self.scalar("SELECT COUNT(*) FROM properties WHERE sale_date > CURRENT_DATE")
        old = self.scalar("SELECT COUNT(*) FROM properties WHERE sale_date < '2010-01-01'")
        status = "warn" if (fut or old) else "ok"
        self.add(
            "date_sanity", status,
            f"range {mn} -> {mx}; future={fut:,}; pre-2010={old:,}",
            min_date=str(mn), max_date=str(mx), future_dated=fut, before_2010=old,
        )

    def duplicates(self):
        # NOTE: same (address, sale_date, price) rows are NOT necessarily defects.
        # The PPR source CSV genuinely contains them — multi-unit sales are filed
        # once per unit at a shared address/price (e.g. "26 27 Popes Quay" ×8), and
        # the register also records same-day repeat filings verbatim. Verified
        # 2026-08-05: source has 1,181 redundant rows, DB has 1,172 — they match, so
        # these are real PPR records, not import artifacts. DO NOT delete them.
        # This check is INFORMATIONAL. It only warns if the DB has substantially
        # MORE such rows than the source snapshot, which would indicate a genuine
        # import-side duplication bug worth investigating against source data.
        redundant = self.scalar("""
            SELECT COALESCE(SUM(c - 1), 0) FROM (
                SELECT COUNT(*) c FROM properties
                GROUP BY address_normalized, sale_date, price
                HAVING COUNT(*) > 1
            ) t
        """)
        groups = self.scalar("""
            SELECT COUNT(*) FROM (
                SELECT 1 FROM properties
                GROUP BY address_normalized, sale_date, price
                HAVING COUNT(*) > 1
            ) t
        """)
        # Warn only on a large deviation from the known-good source baseline,
        # which flags an import bug rather than legitimate PPR repeat records.
        status = "warn" if redundant > THRESHOLDS["duplicate_rows"] else "info"
        self.add(
            "duplicates", status,
            f"{groups:,} same-key groups; {redundant:,} redundant rows "
            f"(address_normalized+sale_date+price). Expected — PPR source contains "
            f"these (multi-unit/repeat filings); not deletable. Warns only if far "
            f"above the ~1,172 source baseline (import-bug signal).",
            duplicate_groups=groups, redundant_rows=int(redundant),
        )

    def county_distribution(self):
        distinct = self.scalar("SELECT COUNT(DISTINCT county) FROM properties")
        top = self.q("SELECT county, COUNT(*) FROM properties GROUP BY county ORDER BY 2 DESC LIMIT 8")
        status = "ok" if distinct == THRESHOLDS["county_count"] else "warn"
        self.add(
            "county_distribution", status,
            f"{distinct} distinct counties (expected {THRESHOLDS['county_count']})",
            distinct_counties=distinct, top={c: n for c, n in top},
        )

    def property_type_provenance(self):
        populated = self.scalar("SELECT COUNT(*) FROM properties WHERE property_type IS NOT NULL")
        prov = None
        if self.column_exists("property_type_source"):
            prov = {
                str(src): n for src, n in self.q(
                    "SELECT property_type_source, COUNT(*) FROM properties "
                    "WHERE property_type IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
            }
        self.add(
            "property_type_provenance", "info",
            f"{populated:,} rows have property_type; provenance="
            f"{'available' if prov else 'n/a'}",
            populated=populated, provenance=prov,
        )

    def eircode_consistency(self):
        if not self.column_exists("routing_key"):
            self.add("eircode_consistency", "info", "no routing_key column", skipped=True)
            return
        mismatch = self.scalar(
            "SELECT COUNT(*) FROM properties WHERE eircode IS NOT NULL "
            "AND routing_key IS NOT NULL AND UPPER(LEFT(eircode,3)) != routing_key")
        malformed = self.scalar(
            r"SELECT COUNT(*) FROM properties WHERE eircode IS NOT NULL "
            r"AND eircode !~ '^[A-Za-z][0-9][0-9Ww]'")
        status = "warn" if (mismatch or malformed) else "ok"
        self.add(
            "eircode_consistency", status,
            f"routing_key mismatches={mismatch:,}; malformed eircodes={malformed:,}",
            routing_key_mismatch=mismatch, malformed_eircode=malformed,
        )

    def recent_geocode_coverage(self):
        current_year = self.scalar("SELECT EXTRACT(YEAR FROM MAX(sale_date))::int FROM properties")
        rows = self.q("""
            SELECT EXTRACT(YEAR FROM sale_date)::int yr, COUNT(*) tot, COUNT(latitude) geo
            FROM properties WHERE sale_date >= '2021-01-01'
            GROUP BY 1 ORDER BY 1
        """)
        by_year = {}
        worst_recent = 100.0
        for yr, tot, geo in rows:
            pct = round(100 * geo / tot, 1) if tot else 0
            by_year[yr] = {"total": tot, "geocoded": geo, "pct": pct}
            if yr == current_year:
                worst_recent = pct
        status = "warn" if worst_recent < THRESHOLDS["recent_geocode_pct"] else "ok"
        self.add(
            "recent_geocode_coverage", status,
            f"{current_year} geocoded {worst_recent}% "
            f"(threshold {THRESHOLDS['recent_geocode_pct']}%)",
            current_year=current_year, current_year_pct=worst_recent, by_year=by_year,
        )


STATUS_ICON = {"ok": "🟢", "warn": "🟡", "fail": "🔴", "info": "ℹ️ "}


def print_report(checks, total):
    print("=" * 72)
    print(f"DATA QUALITY REPORT — properties ({total:,} rows)")
    print("=" * 72)
    for c in checks:
        print(f"\n{STATUS_ICON.get(c['status'], '  ')} [{c['status'].upper():4s}] {c['name']}")
        print(f"    {c['detail']}")
    # Summary line
    warns = [c for c in checks if c["status"] == "warn"]
    fails = [c for c in checks if c["status"] == "fail"]
    print("\n" + "-" * 72)
    print(f"SUMMARY: {len(fails)} fail, {len(warns)} warn, "
          f"{len(checks) - len(warns) - len(fails)} ok/info")
    if fails:
        print("  FAIL: " + ", ".join(c["name"] for c in fails))
    if warns:
        print("  WARN: " + ", ".join(c["name"] for c in warns))


def main():
    ap = argparse.ArgumentParser(description="Data quality report for the properties table.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    ap.add_argument("--out", metavar="PATH", help="Write JSON snapshot to this file.")
    ap.add_argument("--fail-on-warn", action="store_true",
                    help="Exit non-zero if any check is warn/fail (for CI/cron gating).")
    args = ap.parse_args()

    if not os.getenv("DATABASE_URL"):
        load_dotenv("backend/.env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL not set (checked env and backend/.env).")

    conn = psycopg2.connect(db_url)
    conn.set_session(readonly=True, autocommit=True)
    try:
        dq = DQ(conn)
        checks = dq.run_all()
    finally:
        conn.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_rows": dq.total,
        "thresholds": THRESHOLDS,
        "checks": checks,
    }

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"Wrote snapshot to {args.out}", file=sys.stderr)

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print_report(checks, dq.total)

    has_issue = any(c["status"] in ("warn", "fail") for c in checks)
    if args.fail_on_warn and has_issue:
        sys.exit(1)
    if any(c["status"] == "fail" for c in checks):
        sys.exit(2)


if __name__ == "__main__":
    main()
