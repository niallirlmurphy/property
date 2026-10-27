"""Read CSO (Central Statistics Office) PxStat tables.

The CSO's property price tables come from the same Revenue stamp duty returns
as the Property Price Register, matched to BER and GeoDirectory records, and
cover market-based household purchases only. New-home prices include VAT
(PPR shows them ex-VAT). Licence: CC BY 4.0, credit "Central Statistics Office".

Tables used:
  HPM09  RPPI (index + % changes), national / Dublin / regions, monthly
  HPM07  rolling 12-month mean/median by RPPI region (incl. counties, city/county)
  HPM08  rolling 12-month mean/median by Eircode routing key
  HPM03  monthly volumes by RPPI region
  HPM04  monthly volumes/medians by Eircode routing key
  HPA02  annual transactions by county, buyer type and sale type
  HPA04  annual medians by Eircode routing key
  HPA05  annual medians by RPPI region and dwelling type (house/apartment)

Downloads are cached in logs/cso/cache/ for 24h.
"""
import json
import os
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
CACHE_DIR = os.path.join(ROOT, "logs", "cso", "cache")
URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{}/JSON-stat/2.0/en"
CACHE_TTL_S = 24 * 3600

# PPR's date of sale is the deed date, which is the CSO's "Executions".
EVENT = "Executions"


class Cube:
    """A JSON-stat 2.0 dataset; dimensions are addressed by their labels."""

    def __init__(self, data: dict):
        self.data = data
        self.ids = data["id"]
        self.size = data["size"]
        self.values = data["value"]
        self.dims = {}   # dimension label -> (position, {category label -> index})
        for pos, dim_id in enumerate(self.ids):
            dim = data["dimension"][dim_id]
            cat = dim["category"]
            order = list(cat["index"])
            self.dims[dim["label"]] = (pos, {cat["label"][code]: order.index(code) for code in order})

    def labels(self, dim: str) -> list:
        return list(self.dims[dim][1])

    def get(self, **sel):
        """Value for one cell, e.g. get(Statistic="Median Price", Year="2025", ...).
        Keyword names use underscores for spaces ("Dwelling_Status"). Routing keys
        may be given as "D06" for the label "D06: Dublin 6". None if suppressed."""
        sel = {k.replace("_", " "): v for k, v in sel.items()}
        pos = [0] * len(self.ids)
        for dim, (p, cats) in self.dims.items():
            want = sel[dim]
            if want not in cats:
                want = next((c for c in cats if c.startswith(want + ":")), want)
            pos[p] = cats[want]
        idx = 0
        for p, n in zip(pos, self.size):
            idx = idx * n + p
        v = self.values[idx] if isinstance(self.values, list) else self.values.get(str(idx))
        return v


def load(table: str, refresh: bool = False) -> Cube:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, table + ".json")
    if refresh or not os.path.exists(path) or time.time() - os.path.getmtime(path) > CACHE_TTL_S:
        req = urllib.request.Request(URL.format(table), headers={"User-Agent": "homeiq.ie data refresh"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
        json.loads(body)   # fail before overwriting a good cache with a bad response
        with open(path, "wb") as fh:
            fh.write(body)
    with open(path, encoding="utf-8") as fh:
        return Cube(json.load(fh))


def routing_key_names(cube: Cube) -> dict:
    """{"D06": "Dublin 6", ...} from an Eircode Output dimension."""
    out = {}
    for label in cube.labels("Eircode Output"):
        if ":" in label:
            key, name = label.split(":", 1)
            out[key.strip()] = name.strip()
    return out
