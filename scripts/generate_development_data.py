#!/usr/bin/env python3
"""Generate static JSON for the development landing pages (/development/:slug).

Reads frontend/src/data/developments_registry.json. Each entry names a pin in
development_pins (scripts/development_pins.py), and the pin's full-text match rule
decides which sales belong to the development. Nearby schools and transport come
from the amenities table. Writes frontend/src/data/developments/{slug}.json with
stats, yearly trends, bedroom and type breakdowns, bulk sales, the latest 50 sales
and nearby amenities.

Runs at most once per calendar month (see page_data_schedule.py):
    python3 scripts/generate_development_data.py [--force]
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from statistics import median
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from page_data_schedule import record_generated, skip_if_generated_this_month

ROOT = os.path.join(os.path.dirname(__file__), "..")
REGISTRY = os.path.join(ROOT, "frontend", "src", "data", "developments_registry.json")
OUTDIR = os.path.join(ROOT, "frontend", "src", "data", "developments")

# A sale above this multiple of the development's median is a multi-unit/portfolio
# sale filed at one price (e.g. Elm Park's €9.2m in 2016), not a single home.
BULK_MULTIPLE = 5
MIN_BREAKDOWN_SALES = 5   # bedroom/type rows need this many sales to be shown
RECENT_DAYS = 730         # "recent median" window
TRANSPORT_RADIUS_M = 3000
SCHOOL_RADIUS_M = 4000
MAX_TRANSPORT = 6
MAX_SCHOOLS = 8

_HOUSE_TYPES = {"house", "semi-detached", "detached", "terraced", "bungalow",
                "end of terrace", "townhouse", "cottage"}
_APARTMENT_TYPES = {"apartment", "flat", "duplex", "studio"}


def _haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return round(2 * r * math.asin(math.sqrt(a)))


def split_bulk(sales: list) -> tuple:
    """(individual sales, bulk sales). Bulk = stats_excluded (> €20m etc.) or more
    than BULK_MULTIPLE x the median of the rest."""
    kept = [s for s in sales if not s["stats_excluded"]]
    bulk = [s for s in sales if s["stats_excluded"]]
    if kept:
        ceiling = BULK_MULTIPLE * median(s["price"] for s in kept)
        bulk += [s for s in kept if s["price"] > ceiling]
        kept = [s for s in kept if s["price"] <= ceiling]
    return kept, bulk


def _summary(prices: list) -> dict:
    return {"count": len(prices), "median": round(median(prices)),
            "avg": round(sum(prices) / len(prices))}


def bedroom_breakdown(rows: list) -> list:
    by_beds = defaultdict(list)
    for s in rows:
        if s["bedrooms"] is not None:
            by_beds[s["bedrooms"]].append(s["price"])
    return [{"bedrooms": b, **_summary(p)} for b, p in sorted(by_beds.items())
            if len(p) >= MIN_BREAKDOWN_SALES]


def _type_label(ptype: Optional[str]) -> Optional[str]:
    t = (ptype or "").strip().lower()
    if t in _APARTMENT_TYPES:
        return "Apartment"
    if t in _HOUSE_TYPES:
        return "House"
    return None


def type_breakdown(rows: list) -> list:
    by_type = defaultdict(list)
    for s in rows:
        label = _type_label(s["propertyType"])
        if label:
            by_type[label].append(s["price"])
    return [{"type": t, **_summary(p)} for t, p in sorted(by_type.items())
            if len(p) >= MIN_BREAKDOWN_SALES]


def _transport_mode(category: str) -> Optional[str]:
    if "Luas" in category:
        line = "Green Line" if "Green" in category else "Red Line" if "Red" in category else None
        return f"Luas ({line})" if line else "Luas"
    if "DART" in category:
        return "DART"
    if "Train" in category or "Commuter" in category or "Rail" in category:
        return "Rail"
    return None


def nearest_amenities(amenities: list, lat: float, lon: float) -> dict:
    """Nearest rail/Luas stops and schools to the pin, from the amenities table."""
    transport, schools = [], []
    for a in amenities:
        d = _haversine_m(lat, lon, a["latitude"], a["longitude"])
        if a["amenity_type"] == "transport":
            mode = _transport_mode(a["category"] or "")
            if mode and d <= TRANSPORT_RADIUS_M:
                transport.append({"name": a["name"], "mode": mode, "distance_m": d})
        elif a["amenity_type"] == "school" and a["level"] and d <= SCHOOL_RADIUS_M:
            schools.append({"name": a["name"], "level": a["level"], "distance_m": d})
    transport.sort(key=lambda t: t["distance_m"])
    schools.sort(key=lambda s: s["distance_m"])
    return {"transport": transport[:MAX_TRANSPORT], "schools": schools[:MAX_SCHOOLS]}


def build_page(slug: str, sales: list, amenities: list, lat: float, lon: float,
               today: Optional[date] = None) -> dict:
    today = today or date.today()
    rows, bulk = split_bulk(sales)
    rows.sort(key=lambda s: s["date"], reverse=True)
    prices = [s["price"] for s in rows]
    years = sorted({s["date"].year for s in rows})
    recent = [s["price"] for s in rows if s["date"] >= today - timedelta(days=RECENT_DAYS)]

    by_year = defaultdict(list)
    for s in rows:
        by_year[s["date"].year].append(s["price"])
    trends = [{"year": y, "count": len(p), "median_price": round(median(p)),
               "avg_price": round(sum(p) / len(p)),
               "min_price": round(min(p)), "max_price": round(max(p))}
              for y, p in sorted(by_year.items())]

    new_homes = [s for s in rows if (s["description"] or "").lower().startswith("new")]
    stats = {
        "count": len(rows),
        "median": round(median(prices)) if prices else 0,
        "avg": round(sum(prices) / len(prices)) if prices else 0,
        "min": round(min(prices)) if prices else 0,
        "max": round(max(prices)) if prices else 0,
        "firstYear": years[0] if years else None,
        "lastYear": years[-1] if years else None,
        "recentMedian": round(median(recent)) if len(recent) >= MIN_BREAKDOWN_SALES else None,
        "recentCount": len(recent),
    }

    def tx(s):
        return {"date": s["date"].isoformat(), "address": s["address"],
                "price": round(s["price"]), "bedrooms": s["bedrooms"],
                "propertyType": s["propertyType"],
                "newHome": (s["description"] or "").lower().startswith("new")}

    return {
        "slug": slug,
        "stats": stats,
        "trends": trends,
        "bedrooms": bedroom_breakdown(rows),
        "types": type_breakdown(rows),
        "development": {
            "firstSaleYear": years[0] if years else None,
            "newHomeSales": len(new_homes),
            "resales": len(rows) - len(new_homes),
            "bedroomsKnown": sum(1 for s in rows if s["bedrooms"] is not None),
        },
        "bulkSales": [tx(s) for s in sorted(bulk, key=lambda s: s["date"])],
        "amenities": nearest_amenities(amenities, lat, lon),
        "transactions": [tx(s) for s in rows[:50]],
        "totalTransactions": len(rows),
    }


def _fetch(cur, pin_name: str) -> list:
    from development_pins import PIN_MATCH
    cur.execute(f"""
        SELECT p.sale_date, p.address, p.price, p.bedrooms, p.property_type,
               p.description, p.stats_excluded
        FROM properties p JOIN development_pins d ON {PIN_MATCH}
        WHERE d.name = %s AND p.not_full_market_price = FALSE AND p.price > 0
    """, (pin_name,))
    return [{"date": r[0], "address": r[1], "price": float(r[2]), "bedrooms": r[3],
             "propertyType": r[4], "description": r[5], "stats_excluded": bool(r[6])}
            for r in cur.fetchall()]


def main():
    ap = argparse.ArgumentParser(description="Generate static development page JSON.")
    ap.add_argument("--force", action="store_true", help="ignore the once-per-month limit")
    if skip_if_generated_this_month("developments", force=ap.parse_args().force):
        return
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, "backend", ".env"))

    registry = json.load(open(REGISTRY, encoding="utf-8"))
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '120s'")
    cur.execute("""SELECT amenity_type, name, category, level, latitude, longitude
                   FROM amenities WHERE latitude IS NOT NULL AND longitude IS NOT NULL""")
    amenities = [dict(zip(("amenity_type", "name", "category", "level", "latitude", "longitude"), r))
                 for r in cur.fetchall()]

    os.makedirs(OUTDIR, exist_ok=True)
    for entry in registry:
        cur.execute("SELECT latitude, longitude FROM development_pins WHERE name = %s",
                    (entry["pinName"],))
        pin = cur.fetchone()
        if not pin:
            print(f"❌ No pin named {entry['pinName']!r}; skipping {entry['slug']}")
            continue
        page = build_page(entry["slug"], _fetch(cur, entry["pinName"]), amenities, *pin)
        with open(os.path.join(OUTDIR, entry["slug"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(page, fh, indent=2, ensure_ascii=False)
        s = page["stats"]
        print(f"  {entry['slug']}: {s['count']} sales, median €{s['median']:,}, "
              f"{len(page['bulkSales'])} bulk, {len(page['bedrooms'])} bedroom rows, "
              f"{len(page['amenities']['transport'])} stops, {len(page['amenities']['schools'])} schools")
    conn.close()
    print(f"wrote {len(registry)} development data files to {OUTDIR}")
    record_generated("developments")


if __name__ == "__main__":
    main()
