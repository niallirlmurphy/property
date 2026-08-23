import os
import sys

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
