#!/usr/bin/env python3
"""
Value the IRES REIT portfolio using our valuation pipeline IN-PROCESS
(ComparableSearcher -> MVPAdjuster -> ValuationCalculator -> MVPValidator),
exactly as backend/valuation/api.py does, but driven by an explicit coordinate
per development so we never depend on Nominatim.

Coordinate resolution per development:
  1. GEOCODE_OVERRIDES[name]  (curated, authoritative — e.g. Richmond Gardens)
  2. ValuationGeocoder: DB street/prefix match -> Eircode routing-key centroid

For each development we value each bedroom type present (per-unit estimate,
re-weighted to matching bedrooms) and multiply by IRES-owned units of that type.
Outputs docs/ires_valuation_raw.json.
"""
import asyncio
import json
import os
import sys
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from valuation.geocoder import ValuationGeocoder  # noqa: E402
from valuation.comparable_search import ComparableSearcher  # noqa: E402
from valuation.adjustments import MVPAdjuster, trim_price_outliers  # noqa: E402
from valuation.calculator import ValuationCalculator  # noqa: E402
from valuation.validator import MVPValidator  # noqa: E402

load_dotenv("backend/.env")

# Authoritative coordinate overrides (development name -> (lat, lon)).
# Used verbatim for every bedroom lookup of that development.
GEOCODE_OVERRIDES = {
    "Richmond Gardens": (53.3643046, -6.2450984),
    # "Castleknock, Dublin 15" geocodes ~1.3km west into Castleknock's pricey
    # detached-house core, not the racecourse-grounds apartment complex. Pinned to
    # the median of the development's own PPR sales (Phoenix Park Avenue / Orby /
    # Danehill / Cedarhurst), where its 2-bed apartments actually sold ~€435–520k.
    "Phoenix Park Racecourse": (53.3737, -6.3440),
    # Coordinate audit (own-sales centroid + Mapbox verification) found the DB
    # street/routing-key match had drifted several schemes into the wrong district
    # — three of them to shared geocoder-fallback points. Corrected below.
    # User-confirmed exact coordinates:
    "Kings Court": (53.3500544, -6.2756032),          # North King St, Dublin 7
    "Rockbrook South Central": (53.2793323, -6.2129697),   # Sandyford, Dublin 18
    "Rockbrook Grande Central": (53.2793323, -6.2129697),  # Sandyford, Dublin 18
    "Grande Central": (53.2793323, -6.2129697),            # Sandyford, Dublin 18
    "Time Place": (53.2764544, -6.2146378),           # Corrig Rd, Sandyford, D18
    # Own-sales centroids, corroborated by Mapbox forward-geocode:
    "Carrington Park": (53.4037, -6.2529),   # Northwood, Santry, Dublin 9
    "Heywood Court": (53.4013, -6.2580),     # Northwood, Santry, Dublin 9
    "Coldcut Park": (53.3461, -6.3845),      # Coldcut Rd, Clondalkin, Dublin 22
    "Northern Cross": (53.3790, -6.2145),    # Burnell Sq, Malahide Rd, Dublin 17
}

# IRES is overwhelmingly an apartment landlord; only two schemes are traditional
# houses. Everything else (including duplexes) is valued as "apartment" so the
# type-aware weighting matches each unit against apartment sales, not the far
# pricier nearby houses. Developments not listed here default to "apartment".
HOUSE_DEVELOPMENTS = {"Taylor Hill", "Semple Woods"}

# name, region, street address, routing_key (district fallback), county, types
# types: (label, bedrooms_int_for_weighting, owned_units)
PORTFOLIO = [
    ("The Marker", "City Centre", "Grand Canal Square, Dublin 2", "D02", "Dublin",
        [("2-bed", 2, 85)]),
    ("Xavier Court", "City Centre", "Sherrard Street Upper, Dublin 1", "D01", "Dublin",
        [("1-bed", 1, 18), ("2-bed", 2, 21), ("3-bed", 3, 2)]),
    ("Richmond Gardens", "City Centre", "Richmond Avenue, Dublin 3", "D03", "Dublin",
        [("1-bed", 1, 23), ("2-bed", 2, 54), ("3-bed", 3, 22)]),
    ("Bakers Yard", "City Centre", "Portland Street North, Dublin 1", "D01", "Dublin",
        [("1-bed", 1, 10), ("2-bed", 2, 59), ("3-bed", 3, 12)]),
    ("Kings Court", "City Centre", "North King Street, Dublin 7", "D07", "Dublin",
        [("1-bed", 1, 25), ("2-bed", 2, 54), ("3-bed", 3, 4)]),
    ("City Square", "City Centre", "Gloucester Street, Dublin 2", "D02", "Dublin",
        [("1-bed", 1, 15), ("2-bed", 2, 9)]),
    ("The School Yard", "City Centre", "North Circular Road, Dublin 1", "D01", "Dublin",
        [("studio", 1, 5), ("1-bed", 1, 14), ("2-bed", 2, 42)]),
    ("Rockbrook South Central", "South Dublin", "Rockbrook, Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 33), ("2-bed", 2, 138), ("3-bed", 3, 18)]),
    ("Tara View", "South Dublin", "Merrion Road, Dublin 4", "D04", "Dublin",
        [("studio", 1, 2), ("1-bed", 1, 10), ("2-bed", 2, 33), ("2-bed duplex", 2, 10), ("3-bed", 3, 9)]),
    ("The Maple", "South Dublin", "Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 4), ("2-bed", 2, 55), ("3-bed", 3, 9)]),
    ("The Forum", "South Dublin", "Ballymoss Road, Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 1), ("2-bed", 2, 6)]),
    ("Rockbrook Grande Central", "South Dublin", "Rockbrook, Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 13), ("2-bed", 2, 65), ("3-bed", 3, 3)]),
    ("Grande Central", "South Dublin", "Rockbrook, Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 10), ("2-bed", 2, 34), ("3-bed", 3, 21)]),
    ("Elmpark Green", "South Dublin", "Merrion Road, Dublin 4", "D04", "Dublin",
        [("1-bed", 1, 98), ("2-bed", 2, 92), ("3-bed", 3, 4)]),
    ("Beacon South Quarter", "South Dublin", "Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 23), ("2-bed", 2, 170), ("3-bed", 3, 20)]),
    ("Bessboro", "South Dublin", "Terenure Road West, Dublin 6W", "D6W", "Dublin",
        [("1-bed", 1, 6), ("2-bed", 2, 32), ("3-bed", 3, 2)]),
    ("Belville Court", "South Dublin", "Johnstown Road, Cabinteely, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 3), ("2-bed", 2, 14), ("3-bed", 3, 2)]),
    ("Beechwood Court", "South Dublin", "Stillorgan, Co Dublin", "A94", "Dublin",
        [("1-bed", 1, 7), ("2-bed", 2, 70), ("3-bed", 3, 2)]),
    ("Time Place", "South Dublin", "Corrig Road, Sandyford, Dublin 18", "D18", "Dublin",
        [("1-bed", 1, 9), ("2-bed", 2, 57), ("3-bed", 3, 1)]),
    ("The Coast", "North Dublin", "Baldoyle, Dublin 13", "D13", "Dublin",
        [("1-bed", 1, 9), ("2-bed", 2, 10), ("3-bed", 3, 9), ("4-bed", 4, 6)]),
    ("Carrington Park", "North Dublin", "Santry, Dublin 9", "D09", "Dublin",
        [("1-bed", 1, 25), ("2-bed", 2, 93), ("3-bed", 3, 24)]),
    ("Taylor Hill", "North Dublin", "Taylor Hill, Balbriggan, Co Dublin", "K32", "Dublin",
        [("2-bed", 2, 30), ("3-bed", 3, 40), ("4-bed", 4, 8)]),
    ("Northern Cross", "North Dublin", "Malahide Road, Dublin 17", "D17", "Dublin",
        [("1-bed", 1, 31), ("2-bed", 2, 79), ("3-bed", 3, 5)]),
    ("Heywood Court", "North Dublin", "Santry, Dublin 9", "D09", "Dublin",
        [("1-bed", 1, 4), ("2-bed", 2, 35)]),
    ("Charlestown", "North Dublin", "St Margarets Road, Dublin 11", "D11", "Dublin",
        [("1-bed", 1, 38), ("2-bed", 2, 164), ("3-bed", 3, 35)]),
    ("Ashbrook", "North Dublin", "Clontarf, Dublin 3", "D03", "Dublin",
        [("1-bed", 1, 39), ("2-bed", 2, 58), ("2-bed duplex", 2, 8), ("3-bed", 3, 3)]),
    ("Waterside", "North Dublin", "Malahide, Co Dublin", "K36", "Dublin",
        [("1-bed", 1, 3), ("2-bed", 2, 30), ("3-bed", 3, 7), ("3-bed duplex", 3, 15)]),
    ("Semple Woods", "North Dublin", "Donabate, Co Dublin", "K36", "Dublin",
        [("3-bed", 3, 23), ("4-bed", 4, 10)]),
    ("Coldcut Park", "West Dublin", "Clondalkin, Dublin 22", "D22", "Dublin",
        [("1-bed", 1, 18), ("2-bed", 2, 23), ("3-bed", 3, 33), ("4-bed", 4, 17)]),
    ("Tallaght Cross West", "West Dublin", "Belgard Square West, Tallaght, Dublin 24", "D24", "Dublin",
        [("1-bed", 1, 166), ("2-bed", 2, 245), ("3-bed", 3, 49)]),
    ("Priorsgate", "West Dublin", "Greenhills Road, Tallaght, Dublin 24", "D24", "Dublin",
        [("1-bed", 1, 49), ("2-bed", 2, 51), ("3-bed", 3, 7), ("4-bed", 4, 1)]),
    ("Phoenix Park Racecourse", "West Dublin", "Castleknock, Dublin 15", "D15", "Dublin",
        [("1-bed", 1, 20), ("2-bed", 2, 113), ("3-bed", 3, 13)]),
    ("Lansdowne Gate", "West City", "Long Mile Road, Drimnagh, Dublin 12", "D12", "Dublin",
        [("1-bed", 1, 23), ("2-bed", 2, 146), ("3-bed", 3, 55)]),
    ("Tyrone Court", "West City", "Inchicore, Dublin 8", "D08", "Dublin",
        [("1-bed", 1, 24), ("2-bed", 2, 64), ("3-bed", 3, 7)]),
    ("Camac Crescent", "West City", "Turvey Avenue, Inchicore, Dublin 8", "D08", "Dublin",
        [("1-bed", 1, 21), ("2-bed", 2, 49), ("3-bed", 3, 20)]),
]


async def resolve_coord(geocoder, name, address, routing_key, county):
    """Return (lat, lon, method). Override wins; else DB match / routing key."""
    if name in GEOCODE_OVERRIDES:
        lat, lon = GEOCODE_OVERRIDES[name]
        return lat, lon, "override"
    ecode = (routing_key + "0AA0")[:7]
    # Coordinate-first: query the STREET address only (never the marketing
    # scheme name). PPR rows don't carry development names — "The Marker" was
    # sold as "Forbes Quay / Gallery Quay / Grand Canal Residences" — so a
    # name-prefixed query only forces the precise matcher to miss. The street
    # address lets the geocoder's exact-prefix / plainto_tsquery path land on
    # the real street; if it can't, it falls back to the Eircode routing-key
    # centroid (correct district) rather than a wrong same-named street.
    loc = await geocoder.geocode_address(address=address, eircode=ecode, county=county)
    return loc.latitude, loc.longitude, loc.method


async def value_at(searcher, adjuster, calculator, validator, lat, lon, beds,
                   target_date, property_type):
    comps = await searcher.find_comparables(latitude=lat, longitude=lon,
                                            min_count=5, max_count=30)
    if len(comps) < 3:
        return None
    for c in comps:
        adj = await adjuster.adjust_temporal(sale_price=c["price"], sale_date=c["sale_date"],
                                             target_date=target_date, county=c["county"])
        c["adjusted_price"] = adj["adjusted_price"]
        c["adjustment_factor"] = adj["adjustment_factor"]
    # Match backend/valuation/api.py: trim local price outliers, then use the
    # bedroom ladder for apartments (falls back to the weighted average for
    # houses / unknown bedroom counts).
    comps = trim_price_outliers(comps)
    if len(comps) < 3:
        return None
    apt_ceiling = None
    if property_type == "apartment":
        apt_ceiling = await adjuster.apartment_price_ceiling(lat, lon)
    ladder = adjuster.bedroom_ladder_valuation(comps, beds, property_type,
                                               max_2bed_equiv=apt_ceiling)
    if ladder is not None:
        weights = ladder["weights"]
    else:
        weights = adjuster.calculate_all_weights(comps, beds, property_type)
    val = calculator.calculate_valuation(comps, weights)
    if ladder is not None:
        val["estimate"] = ladder["estimate"]
    validation = validator.validate(val, comps)
    return {
        "estimate": val["estimate"],
        "confidence": validation.confidence_level.value,
        "n_comparables": validation.n_comparables,
        "avg_distance_km": round(validation.avg_distance_km, 2),
    }


async def main():
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"), min_size=1, max_size=4)
    geocoder = ValuationGeocoder(pool)
    searcher = ComparableSearcher(pool)
    adjuster = MVPAdjuster(pool)
    calculator = ValuationCalculator()
    validator = MVPValidator()
    target_date = datetime.now()

    # Speed: _get_price_index only varies by (county, year-month), but the
    # portfolio triggers thousands of temporal adjustments against a remote
    # Supabase (~30s/row uncached). Memoize it so each (county, month) index is
    # fetched once. Script-only wrapper — the backend module is untouched.
    _orig_get_index = adjuster._get_price_index
    _index_cache: dict = {}

    async def _cached_get_price_index(county, when):
        key = (county, when.year, when.month)
        if key not in _index_cache:
            _index_cache[key] = await _orig_get_index(county, when)
        return _index_cache[key]

    adjuster._get_price_index = _cached_get_price_index

    results = []
    for name, region, address, rk, county, types in PORTFOLIO:
        try:
            lat, lon, gmethod = await resolve_coord(geocoder, name, address, rk, county)
        except Exception as e:
            print(f"{name:26} GEOCODE FAILED: {e}")
            for label, beds, count in types:
                results.append({"development": name, "region": region, "type": label,
                                "bedrooms": beds, "units": count, "unit_estimate": None,
                                "total_value": None, "geocode": f"FAIL: {e}"})
            continue

        property_type = "house" if name in HOUSE_DEVELOPMENTS else "apartment"
        per_bed = {}
        for label, beds, count in types:
            if beds not in per_bed:
                try:
                    per_bed[beds] = await value_at(searcher, adjuster, calculator,
                                                   validator, lat, lon, beds,
                                                   target_date, property_type)
                except Exception as e:
                    per_bed[beds] = None
                    print(f"  {name} {beds}-bed error: {e}")
            v = per_bed[beds]
            est = v["estimate"] if v else None
            row = {
                "development": name, "region": region, "address": address,
                "lat": lat, "lon": lon, "type": label, "property_type": property_type,
                "bedrooms": beds, "units": count,
                "unit_estimate": est,
                "confidence": v["confidence"] if v else None,
                "n_comparables": v["n_comparables"] if v else None,
                "avg_distance_km": v["avg_distance_km"] if v else None,
                "total_value": (est * count) if est else None,
                "geocode": gmethod,
            }
            results.append(row)
            ue = f"€{est:,}" if est else "n/a"
            print(f"{name:26} {label:14} x{count:>3}  unit={ue:>10}  "
                  f"conf={row['confidence']}  [{gmethod}]")

    with open("docs/ires_valuation_raw.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    ok = [r for r in results if r["total_value"]]
    total = sum(r["total_value"] for r in ok)
    print(f"\nRows valued: {len(ok)}/{len(results)}")
    print(f"PORTFOLIO TOTAL (owned units): €{total:,.0f}")
    print("Wrote docs/ires_valuation_raw.json")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
