import json, os

REG = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "data", "streets_registry.json")


def test_registry_has_50_unique_slugs():
    data = json.load(open(REG))
    assert len(data) == 50
    slugs = [d["slug"] for d in data]
    assert len(set(slugs)) == 50


def test_categories_and_ranks():
    data = json.load(open(REG))
    value = [d for d in data if d["category"] == "value"]
    volume = [d for d in data if d["category"] == "volume"]
    assert len(value) == 30 and len(volume) == 20
    assert sorted(d["rank"] for d in value) == list(range(1, 31))


def test_display_name_fixes_applied():
    data = json.load(open(REG))
    names = {d["slug"]: d["name"] for d in data}
    assert "St Kevin's Park" in names.values()
    assert "St Mary's Road" in names.values()
    assert not any(n.startswith("Street ") for n in names.values())


def test_normalized_key_format():
    data = json.load(open(REG))
    for d in data:
        assert d["normalizedKey"].count("|") == 2
        assert d["normalizedKey"] == d["normalizedKey"].lower()
