import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import generate_page_data as g


def test_area_targets_parse_known_entries():
    targets = g.area_targets()
    by_slug = {t["slug"]: t for t in targets}

    # Parsed from a multi-line object literal in frontend/src/areas.ts
    assert len(targets) >= 30
    rath = by_slug["rathmines"]
    assert rath["query"] == "Rathmines, Dublin"
    assert rath["radius_km"] == 1.5
    assert rath["match"] == ["Rathmines"]
    assert rath["routing_keys"] == ["D06"]

    # Entry with multiple match terms + multiple routing keys
    dl = by_slug["dun-laoghaire"]
    assert dl["match"] == ["Dun Laoghaire", "Glasthule", "Sandycove", "Monkstown"]
    assert dl["routing_keys"] == ["A96", "A94"]

    # The combined West Cork area committed earlier
    assert "skibbereen-baltimore" in by_slug


def test_eircode_targets():
    codes = g.eircode_targets()
    assert len(codes) == 22
    assert "D02" in codes
    assert "D6W" in codes          # non-numeric routing key must survive parsing
    assert all(c == c.upper() for c in codes)


def test_county_targets_and_slug():
    counties = g.county_targets()
    assert len(counties) == 26
    assert "Cork" in counties
    assert g.county_slug("Cork") == "cork"
    assert g.county_slug("Dun Laoghaire") == "dun-laoghaire"


def test_build_area_matches_area_summary_shape(monkeypatch):
    def fake_get(api_url, path, params):
        if path == "/search":
            assert params["locality"] == "Rathmines"
            assert params["routing_keys"] == "D06"
            assert params["limit"] == 10
            return {
                "center": {"lat": 53.32, "lon": -6.26},
                "count": 812,
                "results": [
                    {"id": 1, "price": 500000, "address": "1 A Rd", "sale_date": "2024-01-01", "county": "Dublin"},
                    {"id": 2, "price": 700000, "address": "2 A Rd", "sale_date": "2024-02-01", "county": "Dublin"},
                ],
            }
        if path == "/trends":
            return {"data": [
                {"year": 2022, "count": 5, "median_price": 480000, "avg_price": 490000, "min_price": 400000, "max_price": 600000},
                {"year": 2024, "count": 7, "median_price": 520000, "avg_price": 560000, "min_price": 450000, "max_price": 800000},
            ]}
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    target = {"slug": "rathmines", "query": "Rathmines, Dublin", "radius_km": 1.5,
              "match": ["Rathmines"], "routing_keys": ["D06"]}
    out = g.build_area("http://x", target)

    assert out["slug"] == "rathmines"
    assert out["name"] == "Rathmines, Dublin"
    assert out["center"] == {"lat": 53.32, "lon": -6.26}
    assert out["total_count"] == 812
    assert out["median_price"] == 520000          # last trend
    assert out["avg_price"] == 600000             # mean of the 2 fetched results
    assert out["min_year"] == 2022 and out["max_year"] == 2024
    assert len(out["recent"]) == 2
    assert out["trends"][-1]["year"] == 2024


def test_build_eircode_bakes_county_trends(monkeypatch):
    def fake_get(api_url, path, params):
        if path == "/eircode":
            assert params["code"] == "D02" and params["limit"] == 10
            return {"code": "D02", "match_type": "routing_key",
                    "stats": {"total_count": 900, "median_price": 650000, "avg_price": 700000,
                              "earliest_sale": "2010-01-01", "latest_sale": "2025-06-01"},
                    "count": 10,
                    "results": [{"id": 5, "price": 650000, "address": "x", "sale_date": "2025-01-01", "county": "Dublin"}]}
        if path == "/trends":
            assert params["county"] == "Dublin"
            return {"data": [{"year": 2024, "count": 3, "median_price": 640000, "avg_price": 660000, "min_price": 500000, "max_price": 900000}]}
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    out = g.build_eircode("http://x", "D02")
    assert out["eircode"]["code"] == "D02"
    assert out["trends"][0]["year"] == 2024


def test_build_county_matches_county_summary_shape(monkeypatch):
    counties = [{"county": "Cork", "count": 12345}, {"county": "Dublin", "count": 99999}]

    def fake_get(api_url, path, params):
        if path == "/trends":
            assert params["county"] == "Cork"
            return {"data": [{"year": 2024, "count": 100, "median_price": 300000, "avg_price": 320000, "min_price": 100000, "max_price": 900000}]}
        if path == "/county-recent":
            assert params["county"] == "Cork" and params["limit"] == 10
            return {"results": [{"id": 9, "price": 300000, "address": "y", "sale_date": "2024-03-01", "county": "Cork"}]}
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    out = g.build_county("http://x", "Cork", counties)
    assert out["county"] == "Cork"
    assert out["total_count"] == 12345
    assert out["median_price"] == 300000
    assert out["avg_price"] == 320000
    assert len(out["recent"]) == 1


def test_build_county_raises_on_recent_http_error(monkeypatch):
    # /county-recent is a real endpoint (not the old radius_km=200 hack), so a
    # failure is transient and must raise -> main() warns and skips rather than
    # baking empty recent (the old, permanently-broken behavior).
    counties = [{"county": "Cork", "count": 12345}]

    def fake_get(api_url, path, params):
        if path == "/trends":
            return {"data": [{"year": 2024, "count": 100, "median_price": 300000, "avg_price": 320000, "min_price": 100000, "max_price": 900000}]}
        if path == "/county-recent":
            raise urllib.error.HTTPError(api_url + path, 503, "Service Unavailable", {}, None)
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    with pytest.raises(urllib.error.HTTPError):
        g.build_county("http://x", "Cork", counties)


def test_build_area_raises_on_trends_http_error(monkeypatch):
    def fake_get(api_url, path, params):
        if path == "/search":
            return {"center": {"lat": 1, "lon": 2}, "count": 5,
                    "results": [{"id": 1, "price": 400000, "address": "a", "sale_date": "2024-01-01", "county": "Dublin"}]}
        if path == "/trends":
            raise urllib.error.HTTPError(api_url + path, 422, "Unprocessable Entity", {}, None)
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    target = {"slug": "x", "query": "X", "radius_km": 2, "match": [], "routing_keys": []}
    with pytest.raises(urllib.error.HTTPError):
        g.build_area("http://x", target)


def test_build_county_raises_on_trends_http_error(monkeypatch):
    counties = [{"county": "Cork", "count": 12345}]

    def fake_get(api_url, path, params):
        if path == "/trends":
            raise urllib.error.HTTPError(api_url + path, 503, "Service Unavailable", {}, None)
        if path == "/county-recent":
            return {"results": [{"id": 9, "price": 300000, "address": "y", "sale_date": "2024-03-01", "county": "Cork"}]}
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    with pytest.raises(urllib.error.HTTPError):
        g.build_county("http://x", "Cork", counties)


def test_build_county_raises_when_count_positive_but_trends_empty(monkeypatch):
    counties = [{"county": "Cork", "count": 12345}]

    def fake_get(api_url, path, params):
        if path == "/trends":
            return {"data": []}
        if path == "/county-recent":
            return {"results": [{"id": 9, "price": 300000, "address": "y", "sale_date": "2024-03-01", "county": "Cork"}]}
        raise AssertionError(path)

    monkeypatch.setattr(g, "_get", fake_get)
    with pytest.raises(ValueError):
        g.build_county("http://x", "Cork", counties)
