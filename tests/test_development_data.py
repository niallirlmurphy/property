"""Tests for the pure parts of scripts/generate_development_data.py."""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_development_data import (  # noqa: E402
    bedroom_breakdown, build_page, nearest_amenities, split_bulk, type_breakdown,
)


def _sale(price, beds=None, ptype=None, d=date(2024, 5, 1), excluded=False,
          desc="Second-Hand Dwelling house /Apartment", addr="1 The Oak"):
    return {"date": d, "address": addr, "price": price, "bedrooms": beds,
            "propertyType": ptype, "description": desc, "stats_excluded": excluded}


def test_split_bulk_moves_portfolio_sales_out():
    sales = [_sale(400000) for _ in range(10)]
    sales += [_sale(9_170_000, addr="Units 1-30"), _sale(99_760_000, excluded=True)]
    kept, bulk = split_bulk(sales)
    assert len(kept) == 10
    assert sorted(b["price"] for b in bulk) == [9_170_000, 99_760_000]


def test_bedroom_breakdown_needs_five_sales():
    rows = [_sale(400000, 2) for _ in range(5)] + [_sale(300000, 1) for _ in range(4)]
    out = bedroom_breakdown(rows)
    assert [(b["bedrooms"], b["count"], b["median"]) for b in out] == [(2, 5, 400000)]


def test_bedroom_breakdown_dropped_when_it_breaks_the_ladder():
    rows = [_sale(810000, 2) for _ in range(7)] + [_sale(645000, 3) for _ in range(20)]
    assert bedroom_breakdown(rows) == []
    rows = [_sale(300000, 1) for _ in range(5)] + [_sale(400000, 2) for _ in range(5)]
    assert [b["bedrooms"] for b in bedroom_breakdown(rows)] == [1, 2]


def test_type_breakdown_buckets_houses_and_apartments():
    rows = ([_sale(400000, ptype="apartment") for _ in range(5)]
            + [_sale(800000, ptype=t) for t in ("semi-detached", "terraced", "house", "detached", "bungalow")]
            + [_sale(500000) for _ in range(3)])
    out = {t["type"]: t["count"] for t in type_breakdown(rows)}
    assert out == {"Apartment": 5, "House": 5}


def test_nearest_amenities_sorted_and_capped():
    pin = (53.2860, -6.2355)
    amenities = [
        {"amenity_type": "transport", "name": "Balally", "category": "Luas Station (Green Line)",
         "level": None, "latitude": 53.2865, "longitude": -6.2365},
        {"amenity_type": "transport", "name": "Far Away", "category": "DART Station",
         "level": None, "latitude": 53.40, "longitude": -6.10},
        {"amenity_type": "school", "name": "Wesley College", "category": "School",
         "level": "Secondary", "latitude": 53.2900, "longitude": -6.2450},
        {"amenity_type": "school", "name": "UCD", "category": "University",
         "level": "Tertiary", "latitude": 53.3080, "longitude": -6.2230},
    ]
    out = nearest_amenities(amenities, *pin)
    assert [t["name"] for t in out["transport"]] == ["Balally"]
    assert out["transport"][0]["mode"] == "Luas (Green Line)"
    assert [s["name"] for s in out["schools"]] == ["Wesley College", "UCD"]
    assert out["schools"][0]["distance_m"] < out["schools"][1]["distance_m"]


def test_build_page_stats_exclude_bulk_and_count_new_homes():
    sales = [_sale(400000, 2, "apartment", d=date(2015 + i % 3, 3, 1),
                   desc="New Dwelling house /Apartment" if i < 4 else "Second-Hand Dwelling house /Apartment")
             for i in range(10)]
    sales.append(_sale(114_400_000, excluded=True, d=date(2020, 2, 27), addr="Apartment 1 - 197 Neptune Block"))
    page = build_page("honeypark", sales, [], 53.28, -6.15, today=date(2026, 10, 18))
    assert page["stats"]["count"] == 10
    assert page["stats"]["median"] == 400000
    assert page["development"]["newHomeSales"] == 4
    assert page["development"]["firstSaleYear"] == 2015
    assert page["bulkSales"][0]["price"] == 114_400_000
    assert [t["year"] for t in page["trends"]] == [2015, 2016, 2017]
    assert page["transactions"][0]["date"] == "2017-03-01"
