#!/usr/bin/env python3
"""Micro-benchmark the valuation engine end-to-end, in-process, per stage.

Replicates backend/valuation/api.py's pipeline (geocode -> comparables ->
temporal adjust -> ceiling -> ladder/calc/validate) against the real DB and
times each stage, so we can see where the wall-clock goes. Read-only.
"""
import asyncio
import os
import sys
import time
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from valuation.geocoder import ValuationGeocoder  # noqa: E402
from valuation.comparable_search import ComparableSearcher  # noqa: E402
from valuation.adjustments import MVPAdjuster, trim_price_outliers, property_bucket  # noqa: E402
from valuation.calculator import ValuationCalculator  # noqa: E402
from valuation.validator import MVPValidator  # noqa: E402
from valuation.nearby_amenities import get_nearby_amenities  # noqa: E402

load_dotenv("backend/.env")

# (label, address, eircode, county) — a spread of density profiles.
CASES = [
    ("Dublin 2 (dense city)", "Grand Canal Square, Dublin 2", "D02XY00", "Dublin"),
    ("Dublin 11 (suburb)", "St Margarets Road, Dublin 11", "D11XY00", "Dublin"),
    ("Sandyford D18", "Blackthorn Avenue, Sandyford, Dublin 18", "D18XY00", "Dublin"),
    ("Terenure D6W", "Terenure Road West, Dublin 6W", "D6WXY00", "Dublin"),
    ("Cork city", "Patrick Street, Cork", "T12XY00", "Cork"),
    ("Nobber (rural Meath)", "Main Street, Nobber, Co Meath", "A82XY00", "Meath"),
]


class Timer:
    def __init__(self):
        self.marks = {}

    async def run(self, label, coro):
        t = time.perf_counter()
        result = await coro
        self.marks[label] = (time.perf_counter() - t) * 1000
        return result

    def sync(self, label, fn):
        t = time.perf_counter()
        result = fn()
        self.marks[label] = (time.perf_counter() - t) * 1000
        return result


async def value_one(geocoder, searcher, adjuster, calculator, validator, pool, case):
    label, address, eircode, county = case
    tm = Timer()
    total0 = time.perf_counter()

    loc = await tm.run("geocode", geocoder.geocode_address(address=address, eircode=eircode, county=county))
    lat, lon = loc.latitude, loc.longitude

    comps = await tm.run("find_comparables",
                         searcher.find_comparables(latitude=lat, longitude=lon, min_count=5, max_count=30))

    target_date = datetime.now()

    async def _adjust_all():
        for c in comps:
            adj = await adjuster.adjust_temporal(sale_price=c["price"], sale_date=c["sale_date"],
                                                 target_date=target_date, county=c["county"])
            c["adjusted_price"] = adj["adjusted_price"]
            c["adjustment_factor"] = adj["adjustment_factor"]
    await tm.run("temporal_adjust", _adjust_all())

    kept = tm.sync("outlier_trim", lambda: trim_price_outliers(comps))

    subj_type = getattr(loc, "property_type", None) or "apartment"
    subj_beds = getattr(loc, "bedrooms", None) or 2

    apt_ceiling = None
    if property_bucket(subj_type) == "apartment":
        apt_ceiling = await tm.run("apartment_ceiling", adjuster.apartment_price_ceiling(lat, lon))

    ladder = tm.sync("ladder", lambda: adjuster.bedroom_ladder_valuation(
        kept, subj_beds, subj_type, max_2bed_equiv=apt_ceiling))
    weights = ladder["weights"] if ladder else adjuster.calculate_all_weights(kept, subj_beds, subj_type)

    val = tm.sync("calculate", lambda: calculator.calculate_valuation(kept, weights))
    if ladder:
        val["estimate"] = ladder["estimate"]
    tm.sync("validate", lambda: validator.validate(val, kept))

    await tm.run("amenities", get_nearby_amenities(pool, lat, lon))

    total = (time.perf_counter() - total0) * 1000
    return label, len(comps), val["estimate"], total, tm.marks


async def main():
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"), min_size=2, max_size=8)
    geocoder = ValuationGeocoder(pool)
    searcher = ComparableSearcher(pool)
    adjuster = MVPAdjuster(pool)
    calculator = ValuationCalculator()
    validator = MVPValidator()

    # Warm up the pool + amenities cache so the first case isn't penalised by
    # connection setup we wouldn't see on a live, already-serving backend.
    await pool.fetchval("SELECT 1")
    await get_nearby_amenities(pool, 53.34, -6.25)

    stages = ["geocode", "find_comparables", "temporal_adjust", "outlier_trim",
              "apartment_ceiling", "ladder", "calculate", "validate", "amenities"]

    print(f"{'case':26} {'n':>3} {'total_ms':>9}  " + "  ".join(f"{s[:9]:>9}" for s in stages))
    print("-" * 150)
    totals = []
    stage_sums = {s: 0.0 for s in stages}
    for case in CASES:
        label, n, est, total, marks = await value_one(
            geocoder, searcher, adjuster, calculator, validator, pool, case)
        totals.append(total)
        row = f"{label:26} {n:>3} {total:9.1f}  "
        for s in stages:
            v = marks.get(s, 0.0)
            stage_sums[s] += v
            row += f"{v:9.1f}  "
        print(row)

    print("-" * 150)
    avg = sum(totals) / len(totals)
    avgrow = f"{'AVERAGE':26} {'':>3} {avg:9.1f}  "
    for s in stages:
        avgrow += f"{stage_sums[s]/len(CASES):9.1f}  "
    print(avgrow)
    print(f"\nAverage total: {avg:.0f} ms  (min {min(totals):.0f}, max {max(totals):.0f})")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
