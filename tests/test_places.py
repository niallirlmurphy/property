"""Tests for the place-name lookup (backend/places.py, scripts/build_places.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from places import address_place_names, is_bare_place, normalize_place, parse_localities, parse_query, pick_dominant_place, pick_place  # noqa: E402
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


def test_parse_query_strips_trailing_county():
    assert parse_query("Redhills Co Cavan") == (["redhills"], "Cavan")
    assert parse_query("Drumlaney, Redhills Co. Cavan") == (["drumlaney"], "Cavan")
    assert parse_query("Carlow") == (["carlow"], None)
    assert parse_query("Co Cavan") == (["co cavan"], None)


def test_parse_localities_uses_later_parts():
    assert parse_localities("Drumlaney, Redhills") == (["redhills"], None)
    assert parse_localities("Drumlaney, Redhills, Co Cavan") == (["redhills"], "Cavan")
    assert parse_localities("5 Main Street, Tuam", "Galway") == (["tuam"], "Galway")
    assert parse_localities("Achill") == ([], None)
    assert parse_localities("Apt 4, 12 Main St, Dublin 8") == (["dublin 8"], None)


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


def test_cluster_centre_keeps_postal_town_with_rural_hinterland():
    # Mallow: a busy centre, but most sales are "Townland, Mallow" up to 20km+ out.
    town = [(52.137 + (i % 20) * 1e-4, -8.642) for i in range(300)]
    rural = [(51.9 + i * 0.001, -8.2 - i * 0.001) for i in range(400)]
    lat, lon, n = cluster_centre(town + rural)
    assert abs(lat - 52.138) < 0.002 and n == 700
    # A county name ending addresses county-wide isn't a place at that town.
    assert cluster_centre(town + rural, core_ok=False) is None


def test_cluster_centre_tied_cells_pick_the_densest_neighbourhood():
    # Achill Island: three cells of 7; only one has neighbours within 5km.
    lone_a = [(53.90, -9.80)] * 7
    lone_b = [(53.70, -9.50)] * 7
    village = [(53.98, -10.067)] * 7 + [(53.99, -10.03)] * 6 + [(53.975, -10.0)] * 3
    for pts in (lone_a + lone_b + village, village + lone_b + lone_a):
        lat, lon, n = cluster_centre(pts)
        assert abs(lat - 53.98) < 0.02 and abs(lon + 10.06) < 0.04


def test_pick_dominant_place_finds_a_town_outside_the_county_filter():
    """"Ballinasloe" with the Dublin default: its only row is Galway's (counties=2, so
    the no-hint rule refuses it). Athlone's Westmeath row holds 77% of its sales."""
    rows = [_row("ballinasloe", "Galway", 53.33, -8.22, sales=1871, counties=2),
            _row("athlone", "Westmeath", 53.42, -7.94, sales=3601, counties=3),
            _row("athlone", "Roscommon", 53.43, -7.96, sales=1105, counties=3)]
    assert pick_place(rows, ["ballinasloe"], "Dublin") is None
    assert pick_dominant_place(rows, ["ballinasloe"]) == (53.33, -8.22)
    assert pick_dominant_place(rows, ["athlone"]) == (53.42, -7.94)


def test_pick_dominant_place_refuses_names_spread_across_counties():
    rows = [_row("kilmore", "Wexford", 52.2, -6.6, sales=144, counties=4),
            _row("kilmore", "Dublin", 53.4, -6.2, sales=81, counties=4),
            _row("kilmore", "Roscommon", 53.8, -8.1, sales=36, counties=4)]
    assert pick_dominant_place(rows, ["kilmore"]) is None
    # Only Meath's "Main Street" clusters, but 25 counties have one.
    rows = [_row("main street", "Meath", 53.6, -6.7, sales=135, counties=25)]
    assert pick_dominant_place(rows, ["main street"]) is None


def test_is_bare_place_only_for_a_lone_town_name():
    """"Kenmare" alone is the Kerry town even with the Dublin default; a street,
    house number or county in the query keeps the normal order."""
    assert is_bare_place("Kenmare")
    assert is_bare_place("  kenmare ")
    assert not is_bare_place("Kenmare, Kerry")
    assert not is_bare_place("Kenmare Parade, Dublin 3")
    assert not is_bare_place("12 Main Street")
    assert not is_bare_place("Co. Kerry")


from places import dominant_cluster, query_windows, street_groups, strip_house_number  # noqa: E402


def _sale(county, lat, lon, address="x"):
    return {"county": county, "latitude": lat, "longitude": lon, "address_normalized": address}


def test_dominant_cluster_places_a_street_with_a_few_stray_geocodes():
    rows = [_sale("Kildare", 53.2189, -6.6395)] * 20 + [_sale("Kildare", 53.25, -6.59), _sale("Kildare", 53.2364, -6.6191)]
    lat, lon = dominant_cluster(rows)
    assert abs(lat - 53.2189) < 0.001 and abs(lon + 6.6395) < 0.001


def test_dominant_cluster_refuses_spread_or_shared_names():
    spread = [_sale("Dublin", 53.27 + i * 0.03, -6.2) for i in range(10)]
    assert dominant_cluster(spread) is None
    shared = [_sale("Cork", 51.9, -8.47)] * 5 + [_sale("Galway", 53.27, -9.05)] * 5
    assert dominant_cluster(shared) is None
    assert dominant_cluster([]) is None


def test_strip_house_number():
    assert strip_house_number("6 Arkle Square") == "Arkle Square"
    assert strip_house_number("Apt 10 Wellington Place") == "Wellington Place"
    assert strip_house_number("12a Main Street") == "Main Street"
    assert strip_house_number("Stoneleigh") == "Stoneleigh"


def test_street_groups_lists_each_place_a_name_could_mean():
    rows = [
        _sale("Dublin", 53.2612, -6.12, "1 Stoneleigh, Saint George's Avenue, Killiney"),
        _sale("Dublin", 53.2613, -6.12, "4 Saint George's Avenue, Killiney, Co Dublin"),
        _sale("Dublin", 53.39, -6.30, "28 North Great Charles Street, Parish of Saint George, City of Dublin"),
        _sale("Cork", None, None, "Fort Saint George, Charleville, Co Cork"),
        _sale("Dublin", 53.29, -6.13, "4 Saint Helens Court, Lower Georges Street, Dun Laoghaire"),
    ]
    groups = street_groups(rows, ["saint", "george"])
    assert [g["label"] for g in groups] == ["Saint George's Avenue, Killiney", "Parish of Saint George, City of Dublin"]
    assert groups[0]["sales"] == 2 and groups[0]["county"] == "Dublin"


def test_street_groups_drop_house_and_block_numbers():
    rows = [_sale("Dublin", 53.2735, -6.1995, "6 Arkle Square, the Chase, Leopardstown"),
            _sale("Dublin", 53.2738, -6.1994, "5 Sir Ivor Mall, the Chase, Brewery Road Leopardstown Dublin 18")]
    labels = {g["label"] for g in street_groups(rows, ["chase"])}
    assert labels == {"the Chase, Leopardstown", "the Chase, Brewery Road Leopardstown"}


def test_query_windows():
    w = query_windows("the chase lepperdstown")
    assert w[:3] == ["the chase lepperdstown", "the chase", "chase lepperdstown"]
    assert "lepperdstown" in w and "the" not in w
    assert "chase" not in w
    assert query_windows("6 the chase") == ["the chase"]
    assert query_windows("st george") == ["st george", "george"]
    assert query_windows("1 wellington place, trim, county meath") == ["wellington place", "wellington", "trim"]


def test_parse_word_runs_finds_an_estate_inside_a_longer_query():
    from places import parse_word_runs
    assert parse_word_runs("6 the chase") == (["the chase"], None)
    names, hint = parse_word_runs("the chase stillorgan")
    assert "the chase" in names and "stillorgan" not in names and hint is None
    assert parse_word_runs("Saint George") == (["saint george"], None)
    assert parse_word_runs("Main Street, Tuam, Co Galway")[1] == "Galway"
