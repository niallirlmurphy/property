"""Biweekly generator: read the street registry, query Supabase once, and write
one static JSON per street (stats + yearly trends + latest 50 transactions).
Run after the PPR sync, then rebuild/redeploy the frontend."""
import json, os, sys
import psycopg2
from collections import defaultdict
from statistics import median as _median
sys.path.insert(0, os.path.dirname(__file__))
from street_key import street_key, normalized_key_string

ROOT = os.path.join(os.path.dirname(__file__), "..")
REG = os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")
OUTDIR = os.path.join(ROOT, "frontend", "src", "data", "streets")

def main():
    registry = json.load(open(REG))
    targets = {e["normalizedKey"]: e["slug"] for e in registry}
    tx = defaultdict(list)  # normalizedKey -> list of transaction dicts

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(name="stream"); cur.itersize = 20000
    cur.execute("""
        SELECT address_normalized, county, price, sale_date, address,
               bedrooms, property_type, eircode
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND not_full_market_price = FALSE
          AND price > 0 AND county IS NOT NULL
    """)
    for addr, county, price, sale_date, raw_addr, beds, ptype, eircode in cur:
        r = street_key(addr, county)
        if not r:
            continue
        key = normalized_key_string(*r[0])
        if key not in targets:
            continue
        tx[key].append({
            "date": sale_date.isoformat(),
            "address": raw_addr,
            "price": float(price),
            "bedrooms": beds,
            "propertyType": ptype,
            "eircode": eircode,
        })
    conn.close()

    os.makedirs(OUTDIR, exist_ok=True)
    written = 0
    for entry in registry:
        key = entry["normalizedKey"]; slug = entry["slug"]
        rows = tx.get(key, [])
        prices = [t["price"] for t in rows]
        years = sorted({int(t["date"][:4]) for t in rows}) if rows else []
        # per-year trend points
        by_year = defaultdict(list)
        for t in rows:
            by_year[int(t["date"][:4])].append(t["price"])
        trends = []
        for y in years:
            pl = by_year[y]
            trends.append({
                "year": y, "count": len(pl),
                "median_price": round(_median(pl)),
                "avg_price": round(sum(pl) / len(pl)),
                "min_price": round(min(pl)), "max_price": round(max(pl)),
            })
        recent = sorted(rows, key=lambda t: t["date"], reverse=True)[:50]
        for t in recent:
            t["price"] = round(t["price"])
        stats = {
            "count": len(rows),
            "median": round(_median(prices)) if prices else 0,
            "avg": round(sum(prices) / len(prices)) if prices else 0,
            "min": round(min(prices)) if prices else 0,
            "max": round(max(prices)) if prices else 0,
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

if __name__ == "__main__":
    main()
