"""Write frontend/src/data/cso.json: official CSO property price figures shown
next to our PPR figures on county, area and Eircode pages.

  rppi          RPPI 12-month change for each published series (latest month)
  regions       per RPPI region / county / city: rolling 12-month medians
                (all, existing, new) and volume, plus the last full year's
                medians for houses and apartments
  routing_keys  per Eircode routing key: rolling 12-month medians and volume
  counties      county slug -> the regions shown on its page and its RPPI series

Reads the CSO API only (no database). Monthly like the other page data
(page_data_generated.json, key "cso"); --force to override. See cso_api.py.
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from cso_api import EVENT, load, routing_key_names
from page_data_schedule import record_generated, skip_if_generated_this_month

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "frontend", "src", "data", "cso.json")

# County -> CSO regions shown on its page (first = the whole county where the
# CSO publishes one) and the RPPI series its prices are indexed in. The RPPI
# publishes houses-only indices below Dublin level; Tipperary sits in Mid-West.
SPLIT = {
    "Dublin": ["Dublin", "Dublin City", "Dún Laoghaire-Rathdown", "Fingal", "South Dublin"],
    "Cork": ["Cork City", "Cork County"],
    "Galway": ["Galway City", "Galway County"],
    "Limerick": ["Limerick City", "Limerick County"],
    "Waterford": ["Waterford City", "Waterford County"],
}
RPPI_REGION = {
    "Border": ["Cavan", "Donegal", "Leitrim", "Monaghan", "Sligo"],
    "Midland": ["Laois", "Longford", "Offaly", "Westmeath"],
    "West": ["Galway", "Mayo", "Roscommon"],
    "Mid-East": ["Kildare", "Louth", "Meath", "Wicklow"],
    "Mid-West": ["Clare", "Limerick", "Tipperary"],
    "South-East": ["Carlow", "Kilkenny", "Waterford", "Wexford"],
    "South-West": ["Cork", "Kerry"],
}


def _int(v):
    return None if v is None else int(round(v))


def rolling(cube, vol_cube, geo_dim, geo, months, latest):
    """Rolling 12-month medians to `latest`, the year-earlier median, and the
    12-month volume (sum of monthly volumes)."""
    def med(status, month):
        return _int(cube.get(Statistic="Moving 12 Month Median Sale Price", Month=month,
                             Dwelling_Status=status, Stamp_Duty_Event=EVENT,
                             Type_of_Buyer="All Buyer Types", **{geo_dim: geo}))
    i = months.index(latest)
    vols = [vol_cube.get(Statistic="Volume of Sales", Month=m, Dwelling_Status="All Dwelling Statuses",
                         Stamp_Duty_Event=EVENT, Type_of_Buyer="All Buyer Types", **{geo_dim: geo})
            for m in months[i - 11:i + 1]]
    return {
        "median_12m": med("All Dwelling Statuses", latest),
        "median_12m_prev": med("All Dwelling Statuses", months[i - 12]),
        "existing_12m": med("Existing", latest),
        "new_12m": med("New", latest),
        "volume_12m": _int(sum(v or 0 for v in vols)),
    }


def main():
    ap = argparse.ArgumentParser(description="Generate CSO comparison data for county/area/Eircode pages.")
    ap.add_argument("--force", action="store_true", help="ignore the once-per-month limit")
    ap.add_argument("--refresh", action="store_true", help="re-download instead of using the 24h cache")
    args = ap.parse_args()
    if skip_if_generated_this_month("cso", force=args.force):
        return 0

    rppi, reg12, reg_vol, rk12, rk_vol, annual = (
        load(t, args.refresh) for t in ("HPM09", "HPM07", "HPM03", "HPM08", "HPM04", "HPA05"))

    # Latest month published in every rolling table (they're released together).
    latest = reg12.labels("Month")[-1]
    if rk12.labels("Month")[-1] != latest:
        print("ERROR: HPM07 and HPM08 end in different months; re-run with --refresh")
        return 1
    rppi_month = rppi.labels("Month")[-1]
    year = annual.labels("Year")[-1]

    out = {
        "generated": date.today().isoformat(),
        "source": "Central Statistics Office (CSO), Residential Property Price Index",
        "source_url": "https://www.cso.ie/en/statistics/prices/residentialpropertypriceindex/",
        "licence": "CC BY 4.0",
        "latest_month": latest,
        "rppi_month": rppi_month,
        "annual_year": year,
        "rppi": {},
        "regions": {},
        "routing_keys": {},
        "counties": {},
    }

    for series in rppi.labels("Type of Residential Property"):
        out["rppi"][series] = {
            "index": rppi.get(Statistic="Residential Property Price Index", Month=rppi_month,
                              Type_of_Residential_Property=series),
            "change_12m": rppi.get(Statistic="Percentage Change over 12 months for Residential Property Price Index",
                                   Month=rppi_month, Type_of_Residential_Property=series),
        }

    months = reg12.labels("Month")
    vol_months = reg_vol.labels("Month")
    assert months[-1] == vol_months[-1], "HPM07 and HPM03 end in different months"
    wanted = {r for parts in SPLIT.values() for r in parts} | {
        c for counties in RPPI_REGION.values() for c in counties if c not in SPLIT}
    for region in sorted(wanted):
        figs = rolling(reg12, reg_vol, "RPPI Region", region, months, latest)
        for dwelling, key in (("All Dwelling Types", "all"), ("House", "house"), ("Apartment", "apartment")):
            sel = dict(Year=year, Type_of_Dwelling=dwelling, Dwelling_Status="All Dwelling Statuses",
                       Stamp_Duty_Event=EVENT, RPPI_Region=region)
            figs[key + "_" + year] = {
                "median": _int(annual.get(Statistic="Median Price", **sel)),
                "volume": _int(annual.get(Statistic="Volume of Sales", **sel)),
            }
        out["regions"][region] = figs

    rk_months = rk12.labels("Month")
    assert rk_months[-1] == rk_vol.labels("Month")[-1], "HPM08 and HPM04 end in different months"
    for key, name in sorted(routing_key_names(rk12).items()):
        out["routing_keys"][key] = {"name": name, **rolling(rk12, rk_vol, "Eircode Output", key, rk_months, latest)}

    for region, counties in RPPI_REGION.items():
        for county in counties:
            out["counties"][county.lower()] = {
                "name": county, "regions": SPLIT.get(county, [county]),
                "rppi_series": f"{region} - houses", "rppi_region": region,
            }
    out["counties"]["dublin"] = {
        "name": "Dublin", "regions": SPLIT["Dublin"],
        "rppi_series": "Dublin - all residential properties", "rppi_region": "Dublin",
    }

    missing = [r for r, f in out["regions"].items() if f["median_12m"] is None]
    if missing:
        print(f"WARNING: no rolling median for {missing}")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {OUT}: {len(out['regions'])} regions, {len(out['routing_keys'])} routing keys, "
          f"rolling to {latest}, RPPI {rppi_month}, annual {year}")
    record_generated("cso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
