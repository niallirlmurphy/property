"""Biweekly generator: read the street registry, query Supabase once, and write
one static JSON per street (stats + yearly trends + latest 50 transactions).
Run after the PPR sync, then rebuild/redeploy the frontend."""
import argparse, json, os, sys
import psycopg2
from collections import defaultdict
from statistics import median as _median
sys.path.insert(0, os.path.dirname(__file__))
from street_key import street_key, normalized_key_string
from page_data_schedule import record_generated, skip_if_generated_this_month
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from price_vat import PRICE_INCL_VAT  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
REG = os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")
OUTDIR = os.path.join(ROOT, "frontend", "src", "data", "streets")

def main():
    ap = argparse.ArgumentParser(description="Generate static street page JSON.")
    ap.add_argument("--force", action="store_true", help="ignore the once-per-month limit")
    if skip_if_generated_this_month("streets", force=ap.parse_args().force):
        return
    registry = json.load(open(REG))
    # A page's own key plus any duplicate keys merged into it (build_street_registry MERGE)
    targets = {k: e["slug"] for e in registry for k in [e["normalizedKey"], *e.get("alsoKeys", [])]}
    tx = defaultdict(list)  # slug -> list of transaction dicts

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(name="stream"); cur.itersize = 20000
    cur.execute(f"""
        SELECT address_normalized, county, price, sale_date, address,
               bedrooms, property_type, eircode,
               {PRICE_INCL_VAT}
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND not_full_market_price = FALSE
          AND price > 0 AND county IS NOT NULL
          AND stats_excluded = FALSE   -- keep out-of-band price outliers off street pages
    """)
    for addr, county, price, sale_date, raw_addr, beds, ptype, eircode, price_vat in cur:
        r = street_key(addr, county)
        if not r:
            continue
        key = normalized_key_string(*r[0])
        if key not in targets:
            continue
        tx[targets[key]].append({
            "date": sale_date.isoformat(),
            "address": raw_addr,
            "price": float(price),
            "priceInclVat": float(price_vat),  # for medians/averages; listings show "price"
            "bedrooms": beds,
            "propertyType": ptype,
            "eircode": eircode,
        })
    conn.close()

    os.makedirs(OUTDIR, exist_ok=True)
    written = 0
    for entry in registry:
        key = entry["normalizedKey"]; slug = entry["slug"]
        rows = tx.get(slug, [])
        # New homes are on the register ex-VAT; medians and averages add it back
        # (backend/price_vat.py). Min/max stay register prices.
        prices = [t["priceInclVat"] for t in rows]
        raw_prices = [t["price"] for t in rows]
        years = sorted({int(t["date"][:4]) for t in rows}) if rows else []
        # per-year trend points
        by_year = defaultdict(list)
        for t in rows:
            by_year[int(t["date"][:4])].append(t)
        trends = []
        for y in years:
            pl = [t["priceInclVat"] for t in by_year[y]]
            raw = [t["price"] for t in by_year[y]]
            trends.append({
                "year": y, "count": len(pl),
                "median_price": round(_median(pl)),
                "avg_price": round(sum(pl) / len(pl)),
                "min_price": round(min(raw)), "max_price": round(max(raw)),
            })
        recent = sorted(rows, key=lambda t: t["date"], reverse=True)[:50]
        for t in recent:
            t["price"] = round(t["price"])
        for t in rows:
            t.pop("priceInclVat")
        stats = {
            "count": len(rows),
            "median": round(_median(prices)) if prices else 0,
            "avg": round(sum(prices) / len(prices)) if prices else 0,
            "min": round(min(raw_prices)) if raw_prices else 0,
            "max": round(max(raw_prices)) if raw_prices else 0,
            "firstYear": years[0] if years else None,
            "lastYear": years[-1] if years else None,
        }
        json.dump({"slug": slug, "stats": stats, "trends": trends,
                   "transactions": recent, "totalTransactions": len(rows)},
                  open(os.path.join(OUTDIR, slug + ".json"), "w"),
                  indent=2, ensure_ascii=False)
        written += 1
        if not rows:
            print(f"WARNING: no transactions matched for {slug} ({key})")
    print(f"wrote {written} street data files to {OUTDIR}")
    record_generated("streets")

if __name__ == "__main__":
    main()
