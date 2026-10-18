"""Tests for the place-name lookup (backend/places.py, scripts/build_places.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from places import address_place_names, normalize_place, parse_query, pick_place  # noqa: E402
from build_places import cluster_centre  # noqa: E402


def _row(name, county, lat, lon, sales=100, counties=1):
    return {"name": name, "county": county, "latitude": lat, "longitude": lon,
            "sales": sales, "counties": counties}


def test_normalize_folds_fadas_and_punctuation():
    assert normalize_place("Dún Laoghaire") == "dun laoghaire"
    assert normalize_place("Harold's Cross") == "harolds cross"
    assert normalize_place("  Dun-Laoghaire ") == "dun laoghaire"


def test_address_place_names_skip_house_part_and_county():
    assert address_place_names("12 Main St, Swords, Co. Dublin") == {"swords"}
    assert address_place_names("Apt 4, The Oak, Elm Park, Dublin 4") == {"the oak", "elm park", "dublin 4"}


def test_parse_query():
    assert parse_query("Swords, Dublin") == (["swords"], "Dublin")
    assert parse_query("Carlow, County Carlow") == (["carlow"], "Carlow")
    assert parse_query("Limerick City") == (["limerick city", "limerick"], None)
    assert parse_query("Nobber", "Meath") == (["nobber"], "Meath")
    assert parse_query("Dublin 2") == (["dublin 2"], None)
    assert parse_query("36 fairfield road") == ([], None)


def test_pick_place_county_hint():
    rows = [_row("elm park", "Dublin", 53.3, -6.2, 277, 3), _row("elm park", "Limerick", 52.6, -8.5, 80, 3)]
    assert pick_place(rows, ["elm park"], "Limerick") == (52.6, -8.5)
    assert pick_place(rows, ["elm park"], "Cork") is None


def test_pick_place_defaults_to_dublin_then_single_county_names():
    rows = [_row("elm park", "Dublin", 53.3, -6.2, 277, 3), _row("elm park", "Limerick", 52.6, -8.5, 800, 3)]
    assert pick_place(rows, ["elm park"], None) == (53.3, -6.2)
    assert pick_place([_row("tuam", "Galway", 53.5, -8.8)], ["tuam"], None) == (53.5, -8.8)
    # A name shared across counties with no Dublin row is left to Mapbox.
    assert pick_place([_row("main street", "Meath", 53.4, -6.4, 123, 25)], ["main street"], None) is None


def test_pick_place_prefers_earlier_names():
    rows = [_row("limerick city", "Limerick", 52.66, -8.63), _row("limerick", "Limerick", 52.5, -8.7)]
    assert pick_place(rows, ["limerick city", "limerick"], None) == (52.66, -8.63)
    assert pick_place(rows[1:], ["limerick city", "limerick"], None) == (52.5, -8.7)


def test_cluster_centre_ignores_stray_geocodes():
    town = [(53.517 + i * 1e-4, -8.855) for i in range(14)]
    stray = [(53.28, -9.05)] * 6          # wrong-town geocodes in Galway city
    lat, lon, n = cluster_centre(town + stray)
    assert abs(lat - 53.5177) < 0.001 and abs(lon + 8.855) < 0.001 and n == 20


def test_cluster_centre_rejects_spread_and_small_names():
    spread = [(52.0 + i * 0.2, -8.0 - i * 0.1) for i in range(20)]
    assert cluster_centre(spread) is None
    assert cluster_centre([(53.5, -8.8)] * 9) is None
