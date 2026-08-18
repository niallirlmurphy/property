import json, os, subprocess, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "frontend", "src", "data", "streets")
REG = json.load(open(os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")))


def test_all_streets_have_data_files():
    for entry in REG:
        p = os.path.join(DATA, entry["slug"] + ".json")
        assert os.path.exists(p), f"missing {p}"


def test_ailesbury_ballsbridge_stats_match_analysis():
    d = json.load(open(os.path.join(DATA, "ailesbury-road-ballsbridge.json")))
    assert d["stats"]["count"] == 28
    assert d["stats"]["median"] == 3875000
    assert len(d["trends"]) > 0
    assert d["trends"][0]["min_price"] <= d["trends"][0]["max_price"]
    assert len(d["transactions"]) <= 50
    assert d["totalTransactions"] == 28
