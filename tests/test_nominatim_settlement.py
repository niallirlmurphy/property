"""_geocode_nominatim must prefer the town over same-named roads ("Swords, Dublin")."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import main  # noqa: E402

TOWN = [{"lat": "53.4594799", "lon": "-6.2191750"}]          # Swords (place=town)
ROAD = [{"lat": "53.3782205", "lon": "-6.2472466"}]          # Swords Road AGI, Whitehall


class FakeResp:
    status_code = 200

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, settlement, freetext):
        self.settlement, self.freetext, self.calls = settlement, freetext, []

    async def get(self, url, params=None, **kw):
        self.calls.append(params)
        return FakeResp(self.settlement if params.get("featureType") == "settlement" else self.freetext)


def _run(query, client):
    return asyncio.run(main._geocode_nominatim(query, client))


def test_place_name_uses_settlement_result():
    assert _run("Swords, Dublin", FakeClient(TOWN, ROAD)) == (53.4594799, -6.219175)


def test_road_name_falls_through_to_free_text():
    assert _run("Swords Road, Dublin", FakeClient([], ROAD)) == (53.3782205, -6.2472466)


def test_numbered_address_skips_settlement_search():
    client = FakeClient(TOWN, ROAD)
    assert _run("12 Main Street, Swords", client) == (53.3782205, -6.2472466)
    assert all(c.get("featureType") is None for c in client.calls)
