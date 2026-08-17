import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from street_key import street_key, normalize, normalized_key_string


def test_strips_house_number_and_builds_key():
    r = street_key("30 HAMPTON GREEN, NAVAN RD, DUBLIN 7", "Dublin")
    assert r is not None
    key, disp, apt = r
    assert key == ("hampton green", "navan rd", "dublin")
    assert disp[0] == "HAMPTON GREEN"
    assert apt is False


def test_apartment_prefix_flagged_and_uses_next_component():
    r = street_key("Apartment 5, Neptune Block, Honeypark", "Dublin")
    assert r is not None
    key, disp, apt = r
    assert apt is True
    assert key[0] == "neptune block"


def test_too_few_components_returns_none():
    assert street_key("Cullen Cottage", "Meath") is None


def test_normalized_key_string_matches_key():
    key, _disp, _apt = street_key("28 SLANE ROAD, CRUMLIN, DUBLIN 12", "Dublin")
    assert normalized_key_string(*key) == "slane road|crumlin|dublin"


def test_normalize_collapses_whitespace_and_lowercases():
    assert normalize("  Ailesbury   Road ") == "ailesbury road"
