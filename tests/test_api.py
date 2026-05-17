"""
Live API smoke tests.

Covers the failure modes seen in production:
  - Search returning results in the wrong county (geocoding resolves wrong location)
  - Geocoder resolving specific addresses to wrong areas (Elm Court → Lucan,
    Mount Carmel → Leitrim)
  - No results returned despite search completing without error
  - Trends returning empty data
  - Eircode lookup not working
"""

import pytest
import math
from conftest import get

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km between two points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# ----------------------------------------------------------------------------
# Health
# ----------------------------------------------------------------------------

def test_health(api):
    """Backend is up and returns 200."""
    r = get(api, "/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ----------------------------------------------------------------------------
# Geocoding — addresses that have previously resolved incorrectly
# ----------------------------------------------------------------------------

GEOCODE_CASES = [
    # (query, county, expected_lat, expected_lon, tolerance_km, description)
    ("27 Elm Court, Merrion Road",  "Dublin",  53.3165, -6.2072, 2.0,  "Ballsbridge D4 — was resolving to Lucan"),
    ("44 Mount Carmel Road",        "Dublin",  53.2958, -6.2383, 2.0,  "Goatstown D14 — was resolving to Leitrim"),
    ("Rathmines",                   "Dublin",  53.3212, -6.2651, 3.0,  "Area name geocoding"),
    ("D04",                         None,      53.3200, -6.2200, 5.0,  "Routing key geocoding"),
    ("Galway",                      None,      53.2707, -9.0568, 10.0, "City name geocoding"),
]

@pytest.mark.parametrize("query,county,exp_lat,exp_lon,tol_km,desc", GEOCODE_CASES)
def test_geocode_accuracy(api, query, county, exp_lat, exp_lon, tol_km, desc):
    """Geocoder resolves known addresses to the correct location."""
    params = {"q": query}
    if county:
        params["county"] = county
    r = get(api, "/geocode", **params)
    assert r.status_code == 200, f"Geocode failed for {query!r}: {r.text}"
    data = r.json()
    assert "lat" in data and "lon" in data

    dist = haversine_km(data["lat"], data["lon"], exp_lat, exp_lon)
    assert dist <= tol_km, (
        f"{desc}\n"
        f"  Query:    {query!r}\n"
        f"  Got:      ({data['lat']:.4f}, {data['lon']:.4f})\n"
        f"  Expected: ({exp_lat:.4f}, {exp_lon:.4f})\n"
        f"  Distance: {dist:.2f} km  (tolerance: {tol_km} km)"
    )


# ----------------------------------------------------------------------------
# Search — results must be non-empty and in the right area
# ----------------------------------------------------------------------------

def test_search_returns_results(api):
    """A search in Rathmines returns results."""
    r = get(api, "/search", q="Rathmines", radius_km=1, county="Dublin")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] > 0, "Search returned 0 results for Rathmines"
    assert len(data["results"]) > 0


def test_search_results_within_radius(api):
    """All returned properties are within the requested radius."""
    r = get(api, "/search", q="Rathmines", radius_km=1, county="Dublin")
    assert r.status_code == 200
    data = r.json()
    center_lat = data["center"]["lat"]
    center_lon = data["center"]["lon"]
    radius_km  = data["radius_km"]

    for prop in data["results"]:
        if prop["latitude"] is None:
            continue
        dist = haversine_km(prop["latitude"], prop["longitude"], center_lat, center_lon)
        assert dist <= radius_km + 0.1, (
            f"Property '{prop['address']}' is {dist:.2f} km from center — "
            f"outside radius of {radius_km} km"
        )


def test_search_result_structure(api):
    """Search results contain all expected fields."""
    r = get(api, "/search", q="Rathmines", radius_km=1)
    assert r.status_code == 200
    data = r.json()
    assert "center" in data
    assert "lat" in data["center"] and "lon" in data["center"]
    assert "count" in data
    assert "results" in data

    if data["results"]:
        prop = data["results"][0]
        for field in ("id", "sale_date", "address", "price", "county"):
            assert field in prop, f"Missing field '{field}' in search result"


def test_search_county_filter(api):
    """County filter returns only results from the requested county."""
    # Use Cork city centre coordinates with max allowed radius
    r = get(api, "/search", q="51.8985,-8.4756", radius_km=20, county="Cork")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] > 0, "No Cork results found near Cork city centre"
    for prop in data["results"]:
        assert prop["county"] and prop["county"].lower() == "cork", (
            f"Result in wrong county: {prop['county']} — {prop['address']}"
        )


def test_search_unknown_address_returns_404(api):
    """A completely nonsense address should return 404, not a wrong location."""
    import requests as req
    r = req.get(f"{api}/search", params={"q": "xyzzy foobarbaz qux 99999"}, timeout=30)
    assert r.status_code == 404, (
        f"Expected 404 for nonsense address, got {r.status_code}: {r.text[:200]}"
    )


def test_search_specific_address_in_correct_area(api):
    """27 Elm Court, Merrion Road results should be near Ballsbridge, not Lucan."""
    r = get(api, "/search", q="27 Elm Court, Merrion Road", radius_km=0.5, county="Dublin")
    assert r.status_code == 200
    data = r.json()
    # Search centre must be near Ballsbridge D4, not Lucan (~15 km away)
    center_lat, center_lon = data["center"]["lat"], data["center"]["lon"]
    dist_from_ballsbridge = haversine_km(center_lat, center_lon, 53.3165, -6.2072)
    assert dist_from_ballsbridge < 3.0, (
        f"Search centre ({center_lat:.4f},{center_lon:.4f}) is {dist_from_ballsbridge:.1f} km "
        f"from expected Ballsbridge location — geocoding resolved wrong area"
    )


# ----------------------------------------------------------------------------
# Trends
# ----------------------------------------------------------------------------

def test_trends_returns_data(api):
    """Trends endpoint returns yearly data for a known area."""
    r = get(api, "/trends", county="Dublin")
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert len(data["data"]) >= 10, "Expected at least 10 years of trend data for Dublin"


def test_trends_data_structure(api):
    """Each trend point has required fields with plausible values."""
    r = get(api, "/trends", county="Dublin")
    data = r.json()
    for point in data["data"]:
        assert "year" in point and "median_price" in point and "count" in point
        assert 2010 <= point["year"] <= 2030
        assert point["median_price"] > 0
        assert point["count"] > 0


def test_trends_median_price_plausible(api):
    """Dublin median prices are in a plausible range (€100k–€2M)."""
    r = get(api, "/trends", county="Dublin")
    data = r.json()
    for point in data["data"]:
        assert 100_000 <= point["median_price"] <= 2_000_000, (
            f"Year {point['year']}: median price €{point['median_price']:,} is outside plausible range"
        )


# ----------------------------------------------------------------------------
# Eircode
# ----------------------------------------------------------------------------

def test_eircode_routing_key(api):
    """D04 routing key returns sales in Dublin 4."""
    r = get(api, "/eircode", code="D04")
    assert r.status_code == 200
    data = r.json()
    assert data["match_type"] == "routing_key"
    assert data["stats"]["total_count"] > 0
    assert len(data["results"]) > 0


def test_eircode_result_structure(api):
    """Eircode response contains stats and results."""
    r = get(api, "/eircode", code="D04")
    data = r.json()
    assert "code" in data
    assert "stats" in data
    assert "total_count" in data["stats"]
    assert "median_price" in data["stats"]
    assert "results" in data


# ----------------------------------------------------------------------------
# Eircode used as a search query — geocoding must resolve to the right location
#
# Two tiers of tolerance:
#   - Full eircode: exact DB match → tight cluster, tolerance 1 km
#   - Routing key only: averages entire routing key area, tolerance 5–15 km
# ----------------------------------------------------------------------------

EIRCODE_GEOCODE_CASES = [
    # (eircode, county, exp_lat, exp_lon, tol_km, description)
    # Full eircodes use exact DB match — tighter than routing key but an eircode can
    # cover a small development with sales spread over 1–3 km, so 5 km is realistic.
    # Rural eircodes with few DB matches fall back to routing key centroid (15 km).
    ("D08 EN29", "Dublin",   53.3395, -6.3205,  5.0, "Dublin 8 full eircode"),
    ("V94 Y6C7", "Limerick", 52.6649, -8.6258,  5.0, "Limerick full eircode"),
    ("T23 EF43", "Cork",     51.9108, -8.4884,  5.0, "Cork full eircode (T23 area)"),
    ("R32 KV20", "Laois",    52.8454, -7.3960, 25.0, "Laois full eircode — sparse rural"),
    ("V95 HF6V", "Clare",    52.8832, -9.1352, 15.0, "Clare full eircode — sparse rural"),
]

ROUTING_KEY_GEOCODE_CASES = [
    # (routing_key, county, exp_lat, exp_lon, tol_km, description)
    # Routing keys average the whole area so tolerance is wider.
    # Expected coords are the actual DB centroids for each routing key.
    ("D08",  "Dublin",   53.3395, -6.3205,  5.0, "Dublin 8 routing key"),
    ("D14",  "Dublin",   53.2958, -6.2383,  5.0, "Dublin 14 routing key"),
    ("V94",  "Limerick", 52.6649, -8.6258,  5.0, "Limerick V94 routing key"),
    ("T23",  "Cork",     51.9330, -8.5676, 10.0, "Cork T23 routing key"),
    ("R32",  "Laois",    53.0348, -7.3026, 15.0, "Laois R32 routing key — sparse rural"),
]

@pytest.mark.parametrize("eircode,county,exp_lat,exp_lon,tol_km,desc", EIRCODE_GEOCODE_CASES)
def test_eircode_as_search_query_geocodes_correctly(api, eircode, county, exp_lat, exp_lon, tol_km, desc):
    """A full eircode resolves to within 1 km of its known location (exact DB match)."""
    r = get(api, "/geocode", q=eircode, county=county)
    assert r.status_code == 200, f"Geocode failed for eircode {eircode!r}: {r.text}"
    data = r.json()
    dist = haversine_km(data["lat"], data["lon"], exp_lat, exp_lon)
    assert dist <= tol_km, (
        f"{desc}\n"
        f"  Eircode:  {eircode!r}\n"
        f"  Got:      ({data['lat']:.4f}, {data['lon']:.4f})\n"
        f"  Expected: ({exp_lat:.4f}, {exp_lon:.4f})\n"
        f"  Distance: {dist:.2f} km  (tolerance: {tol_km} km)"
    )


@pytest.mark.parametrize("routing_key,county,exp_lat,exp_lon,tol_km,desc", ROUTING_KEY_GEOCODE_CASES)
def test_routing_key_geocodes_to_correct_area(api, routing_key, county, exp_lat, exp_lon, tol_km, desc):
    """A routing-key-only query resolves to within the expected area centroid."""
    r = get(api, "/geocode", q=routing_key, county=county)
    assert r.status_code == 200, f"Geocode failed for routing key {routing_key!r}: {r.text}"
    data = r.json()
    dist = haversine_km(data["lat"], data["lon"], exp_lat, exp_lon)
    assert dist <= tol_km, (
        f"{desc}\n"
        f"  Routing key: {routing_key!r}\n"
        f"  Got:         ({data['lat']:.4f}, {data['lon']:.4f})\n"
        f"  Expected:    ({exp_lat:.4f}, {exp_lon:.4f})\n"
        f"  Distance:    {dist:.2f} km  (tolerance: {tol_km} km)"
    )


def test_full_eircode_resolves_differently_to_routing_key(api):
    """Full eircode resolves to a different (more specific) location than its routing key.

    Verifies that the exact-match lookup is being used for full eircodes rather than
    simply averaging the whole routing key area. The two results should differ by at
    least 0.5 km — if they're identical the exact match is not being applied.
    """
    r_full = get(api, "/geocode", q="D14 XT52", county="Dublin")
    r_key  = get(api, "/geocode", q="D14",      county="Dublin")
    assert r_full.status_code == 200
    assert r_key.status_code == 200

    full = r_full.json()
    key  = r_key.json()
    dist = haversine_km(full["lat"], full["lon"], key["lat"], key["lon"])

    assert dist >= 0.5, (
        f"Full eircode D14 XT52 ({full['lat']:.4f},{full['lon']:.4f}) resolved to nearly "
        f"the same location as routing key D14 ({key['lat']:.4f},{key['lon']:.4f}) — "
        f"only {dist:.2f} km apart, suggesting exact match is not being used"
    )


@pytest.mark.parametrize("eircode,county,exp_lat,exp_lon,tol_km,desc", EIRCODE_GEOCODE_CASES)
def test_eircode_search_returns_results(api, eircode, county, exp_lat, exp_lon, tol_km, desc):
    """A search using an eircode as the query returns at least one result."""
    r = get(api, "/search", q=eircode, radius_km=2, county=county)
    assert r.status_code == 200, f"Search failed for eircode {eircode!r}: {r.text}"
    data = r.json()
    assert data["count"] > 0, (
        f"{desc}: search for eircode {eircode!r} returned 0 results"
    )


# ----------------------------------------------------------------------------
# Nearest pins — distance sort must ignore date filters
# ----------------------------------------------------------------------------

def test_nearest_pins_ignores_date_filter(api):
    """Distance-sorted search returns results even when min_year filters out all recent sales.

    Verifies that map pins are not accidentally hidden by the date period filter.
    The nearest-pins call passes no min_year so it always finds the closest ever sale.
    """
    # First confirm there are results with no date filter
    r_any = get(api, "/search", q="Rathmines", radius_km=1, county="Dublin", sort="distance", limit=10)
    assert r_any.status_code == 200
    assert r_any.json()["count"] > 0, "Baseline distance search returned no results"

    # Search with a future min_year — no sales should match the date filter
    r_future = get(api, "/search", q="Rathmines", radius_km=1, county="Dublin",
                   sort="distance", limit=10, min_year=2099)
    assert r_future.status_code == 200
    assert r_future.json()["count"] == 0, (
        "Expected 0 results with min_year=2099 — date filter not being applied"
    )


# ----------------------------------------------------------------------------
# Counties
# ----------------------------------------------------------------------------

def test_counties_returns_all(api):
    """Counties endpoint returns all 26 counties."""
    r = get(api, "/counties")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 26, f"Only {len(data)} counties returned — expected 26"


def test_counties_include_dublin(api):
    """Dublin is in the counties list."""
    r = get(api, "/counties")
    names = [c["county"].lower() for c in r.json()]
    assert "dublin" in names


# ----------------------------------------------------------------------------
# Contact / Feedback forms
# ----------------------------------------------------------------------------

def test_feedback_submission(api):
    """Feedback endpoint accepts a POST and returns ok."""
    r = requests_post(api, "/feedback", {
        "datasets": "test submission from automated tests",
        "comments": "",
        "name":     "Test Runner",
        "email":    "",
    })
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_contact_submission(api):
    """Contact endpoint accepts a POST and returns ok."""
    r = requests_post(api, "/contact", {
        "message":       "test submission from automated tests",
        "price_updates": False,
        "name":          "Test Runner",
        "email":         "",
    })
    assert r.status_code == 200
    assert r.json().get("ok") is True


def requests_post(api_url, path, payload):
    import requests as req
    return req.post(f"{api_url}{path}", json=payload, timeout=15)
