# Static Area / Eircode / County Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve `/area/:slug`, `/eircode/:code`, and `/county/:slug` pages from static JSON baked into the build (like `/street/:slug`), regenerated after each PPR import, with a live-API fallback.

**Architecture:** A Python generator (`scripts/generate_page_data.py`) calls the *existing* backend endpoints — the same calls the three pages' `fetch*` functions make today — and writes one JSON file per page under `frontend/src/data/{areas,eircodes,counties}/`. Each page loads its JSON via `import.meta.glob(..., { eager: true })` at build time (inlined into prerendered HTML for SEO); on a cache miss it falls back to the current live fetch. Generation is wired into `scripts/ppr_full_pipeline.py`.

**Tech Stack:** Python 3.10+ (stdlib `urllib`, `argparse`, `re`), React + TypeScript, vite-react-ssg, pytest.

**Spec:** `docs/superpowers/specs/2026-08-23-static-area-eircode-county-pages-design.md`

## Global Constraints

- **Parity over cleverness:** the generator must reproduce the exact object shape each page already consumes (`AreaSummary`, `CountySummary`, and `{ eircode: EircodeResponse; trends: TrendPoint[] }`). Do not re-implement backend filtering in SQL — always go through the API.
- **Recent-sales limit = 10 for all three types** (matches the current live `fetch*` limits in `frontend/src/api.ts`; the spec's "area 20" was an error — use 10 so `avg_price`, computed from the fetched sample, matches current behavior exactly).
- **No LIKE queries, no client-side filtering, Dublin-default golden rule** — all unchanged; this work touches no backend query logic.
- **Fallback is mandatory:** a missing JSON file must never break a page — it falls through to the existing live `fetch*` call.
- **Generator failure per target = WARNING + skip**, leaving any prior JSON intact (same behavior as `scripts/generate_street_data.py`).
- Backend base URL for the generator: `--api-url`, default `http://localhost:8000`.
- Commit messages end with the repo's `Co-Authored-By` trailer.
- The pre-commit hook runs security + search regression checks; expect it to pass (no backend/search changes). Committing generated JSON does not trip it.

---

### Task 1: Generator — parse page targets from `areas.ts`

Pure parsing, no network. This is the flagged soft-spot (§2 of spec); it gets its own task and its own tests.

**Files:**
- Create: `scripts/generate_page_data.py`
- Test: `tests/test_generate_page_data.py`

**Interfaces:**
- Produces:
  - `area_targets() -> list[dict]` — each `{"slug": str, "query": str, "radius_km": float, "match": list[str], "routing_keys": list[str]}`
  - `eircode_targets() -> list[str]` — uppercase routing keys, e.g. `["D01", ..., "D6W", ...]`
  - `county_targets() -> list[str]` — county display names, e.g. `["Carlow", ..., "Cork", ...]`
  - `county_slug(name: str) -> str` — mirrors the TS `countySlug` (`name.lower()`, whitespace → `-`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_generate_page_data.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_generate_page_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_page_data'` (or `AttributeError` once the file exists but functions don't).

- [ ] **Step 3: Write minimal implementation**

Create `scripts/generate_page_data.py`:

```python
"""Generate static JSON for area / eircode / county landing pages by calling the
backend API (parity with the frontend's fetchAreaSummary / fetchEircode /
fetchCountySummary). Run after the PPR sync, then rebuild + redeploy the frontend.

Usage:
  python3 scripts/generate_page_data.py [--api-url http://localhost:8000] \
                                        [--only areas,eircodes,counties]

Targets are parsed from frontend/src/areas.ts so they cannot drift from the
routes the frontend prerenders. If that parsing ever breaks, fall back to a
committed frontend/src/data/page_targets.json (see spec).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
AREAS_TS = os.path.join(ROOT, "frontend", "src", "areas.ts")
DATA_DIR = os.path.join(ROOT, "frontend", "src", "data")


def _areas_src():
    with open(AREAS_TS, encoding="utf-8") as fh:
        return fh.read()


def _split_top_level_objects(array_body):
    """Yield each top-level {...} object string from a JS array body.
    Relies on the fact that field VALUES in areas.ts contain no braces."""
    depth, buf = 0, []
    for ch in array_body:
        if ch == "{":
            depth += 1
        if depth > 0:
            buf.append(ch)
        if ch == "}":
            depth -= 1
            if depth == 0:
                yield "".join(buf)
                buf = []


def area_targets():
    src = _areas_src()
    start = src.index("[", src.index("export const AREAS"))
    depth = 0
    end = start
    for i in range(start, len(src)):
        if src[i] == "[":
            depth += 1
        elif src[i] == "]":
            depth -= 1
            if depth == 0:
                end = i
                break
    body = src[start + 1:end]

    targets = []
    for obj in _split_top_level_objects(body):
        slug = re.search(r'slug:\s*"([^"]+)"', obj).group(1)
        query = re.search(r'query:\s*"([^"]+)"', obj).group(1)
        radius = float(re.search(r"radius_km:\s*([\d.]+)", obj).group(1))
        match = re.findall(r'"([^"]+)"', re.search(r"match:\s*\[([^\]]*)\]", obj).group(1))
        rk = re.search(r"routing_keys:\s*\[([^\]]*)\]", obj)
        routing_keys = re.findall(r'"([^"]+)"', rk.group(1)) if rk else []
        targets.append({
            "slug": slug, "query": query, "radius_km": radius,
            "match": match, "routing_keys": routing_keys,
        })
    return targets


def eircode_targets():
    src = _areas_src()
    block = re.search(r"DUBLIN_EIRCODE_AREAS[^=]*=\s*\{([^}]*)\}", src).group(1)
    return re.findall(r'(\w+):\s*"', block)


def county_targets():
    src = _areas_src()
    block = re.search(r"export const COUNTIES\s*=\s*\[([^\]]*)\]", src).group(1)
    return re.findall(r'"([^"]+)"', block)


def county_slug(name):
    return re.sub(r"\s+", "-", name.lower())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_generate_page_data.py -v`
Expected: PASS (all 3 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_page_data.py tests/test_generate_page_data.py
git commit -m "feat: parse area/eircode/county page targets from areas.ts

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Generator — API builders, main, file writing

Adds the API calls that assemble each page's JSON and the CLI. Tested with a stubbed HTTP getter (no live backend needed).

**Files:**
- Modify: `scripts/generate_page_data.py`
- Test: `tests/test_generate_page_data.py`

**Interfaces:**
- Consumes: `area_targets`, `eircode_targets`, `county_targets`, `county_slug` (Task 1).
- Produces:
  - `_get(api_url: str, path: str, params: dict) -> dict` — GET + JSON decode (monkeypatched in tests).
  - `build_area(api_url, target: dict) -> dict` — an `AreaSummary`-shaped dict.
  - `build_eircode(api_url, code: str) -> dict` — `{"eircode": <EircodeResponse>, "trends": [...]}`.
  - `build_county(api_url, name: str, counties: list[dict]) -> dict` — a `CountySummary`-shaped dict.
  - `main()` — CLI entry.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_generate_page_data.py`:

```python
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
        if path == "/search":
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_generate_page_data.py -v`
Expected: FAIL — `AttributeError: module 'generate_page_data' has no attribute 'build_area'`.

- [ ] **Step 3: Write minimal implementation**

Append to `scripts/generate_page_data.py`:

```python
def _get(api_url, path, params):
    clean = {k: v for k, v in params.items() if v is not None}
    url = api_url.rstrip("/") + path + "?" + urllib.parse.urlencode(clean)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


RECENT_LIMIT = 10  # matches the live fetch* limits in frontend/src/api.ts


def build_area(api_url, target):
    locality = ",".join(target["match"]) if target["match"] else None
    routing_keys = ",".join(target["routing_keys"]) if target["routing_keys"] else None
    search = _get(api_url, "/search", {
        "q": target["query"], "radius_km": target["radius_km"],
        "limit": RECENT_LIMIT, "locality": locality, "routing_keys": routing_keys,
    })
    trends = _get(api_url, "/trends", {
        "q": target["query"], "radius_km": target["radius_km"],
        "locality": locality, "routing_keys": routing_keys,
    }).get("data", [])

    prices = [r["price"] for r in search["results"]]
    years = [t["year"] for t in trends]
    return {
        "name": target["query"],
        "slug": target["slug"],
        "center": search["center"],
        "radius_km": target["radius_km"],
        "total_count": search["count"],
        "median_price": trends[-1]["median_price"] if trends else None,
        "avg_price": round(sum(prices) / len(prices)) if prices else None,
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
        "recent": search["results"],
        "trends": trends,
    }


def build_eircode(api_url, code):
    eircode = _get(api_url, "/eircode", {"code": code, "limit": RECENT_LIMIT})
    county = eircode["results"][0]["county"] if eircode["results"] else None
    trends = _get(api_url, "/trends", {"radius_km": 5, "county": county}).get("data", []) if county else []
    return {"eircode": eircode, "trends": trends}


def build_county(api_url, name, counties):
    trends = _get(api_url, "/trends", {"county": name}).get("data", [])
    search = _get(api_url, "/search", {
        "q": "53.5,-7.5", "radius_km": 200, "county": name, "limit": RECENT_LIMIT,
    })
    row = next((c for c in counties if c["county"].lower() == name.lower()), None)
    latest = trends[-1] if trends else None
    return {
        "county": name,
        "total_count": row["count"] if row else 0,
        "median_price": latest["median_price"] if latest else None,
        "avg_price": latest["avg_price"] if latest else None,
        "trends": trends,
        "recent": search["results"],
    }


def _write(subdir, slug, obj):
    out_dir = os.path.join(DATA_DIR, subdir)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, slug + ".json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description="Generate static area/eircode/county page JSON.")
    ap.add_argument("--api-url", default=os.getenv("PAGE_DATA_API_URL", "http://localhost:8000"))
    ap.add_argument("--only", help="comma list of: areas,eircodes,counties")
    args = ap.parse_args()
    only = set(s.strip() for s in args.only.split(",")) if args.only else {"areas", "eircodes", "counties"}

    written = 0
    if "areas" in only:
        for t in area_targets():
            try:
                _write("areas", t["slug"], build_area(args.api_url, t))
                written += 1
            except Exception as e:  # noqa: BLE001 - per-target isolation
                print(f"WARNING: area {t['slug']} failed: {e}")

    if "eircodes" in only:
        for code in eircode_targets():
            try:
                _write("eircodes", code, build_eircode(args.api_url, code))
                written += 1
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: eircode {code} failed: {e}")

    if "counties" in only:
        try:
            counties = _get(args.api_url, "/counties", {})
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: could not fetch /counties from {args.api_url}: {e}")
            return 1
        for name in county_targets():
            try:
                _write("counties", county_slug(name), build_county(args.api_url, name, counties))
                written += 1
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: county {name} failed: {e}")

    print(f"wrote {written} page data files under {DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_generate_page_data.py -v`
Expected: PASS (all 6 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_page_data.py tests/test_generate_page_data.py
git commit -m "feat: build area/eircode/county page JSON from backend API

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Generate and commit the initial JSON data

Operational task — runs the generator against a live backend and commits the output. No unit test (the generator's logic is already tested); verification is by file count and spot-check.

**Files:**
- Create: `frontend/src/data/areas/*.json`, `frontend/src/data/eircodes/*.json`, `frontend/src/data/counties/*.json`

- [ ] **Step 1: Start the backend against the live DB**

In a separate terminal:
```bash
cd backend
export $(grep '^DATABASE_URL=' .env | xargs)
uvicorn main:app --port 8000
```
Confirm: `curl -s http://localhost:8000/health` returns `{"status":"ok"}`.

- [ ] **Step 2: Run the generator**

```bash
python3 scripts/generate_page_data.py --api-url http://localhost:8000
```
Expected: prints `wrote N page data files ...` with N ≈ 83 and **no** `WARNING:`/`ERROR:` lines. If any target warns, investigate that endpoint before continuing (do not commit a partial set silently).

- [ ] **Step 3: Verify file counts and a sample**

```bash
ls frontend/src/data/areas | wc -l       # expect ~35
ls frontend/src/data/eircodes | wc -l     # expect 22
ls frontend/src/data/counties | wc -l     # expect 26
python3 -c "import json;d=json.load(open('frontend/src/data/areas/rathmines.json'));print(sorted(d));assert d['slug']=='rathmines' and d['trends'] and d['center']"
python3 -c "import json;d=json.load(open('frontend/src/data/eircodes/D02.json'));assert d['eircode']['code']=='D02' and 'stats' in d['eircode']"
python3 -c "import json;d=json.load(open('frontend/src/data/counties/cork.json'));assert d['county']=='Cork' and d['total_count']>0"
```
Expected: all three counts match; all three asserts pass with no output/error.

- [ ] **Step 4: Commit the data**

```bash
git add frontend/src/data/areas frontend/src/data/eircodes frontend/src/data/counties
git commit -m "chore: generate static area/eircode/county page data

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: AreaPage — load baked JSON with live fallback

**Files:**
- Modify: `frontend/src/pages/AreaPage.tsx:1-35`

**Interfaces:**
- Consumes: `frontend/src/data/areas/<slug>.json` (Task 3), shape `AreaSummary`.

- [ ] **Step 1: Add the eager glob + lookup helper**

In `frontend/src/pages/AreaPage.tsx`, after the imports (below line 11) and before `formatPrice`, add:

```tsx
// Eager glob: area data is bundled so the correct file is available synchronously
// at SSG prerender time (inlined into HTML for SEO). Missing file → live fallback.
const AREA_DATA = import.meta.glob<{ default: AreaSummary }>("../data/areas/*.json", { eager: true });

function bakedArea(slug: string): AreaSummary | undefined {
  return AREA_DATA[`../data/areas/${slug}.json`]?.default;
}
```

- [ ] **Step 2: Read baked data synchronously; fetch only as fallback**

**Why synchronous (not in the effect):** React effects do NOT run during SSG
prerender, so baked data set via `useEffect` would be absent from the
prerendered HTML — defeating the SEO goal. `StreetPage.tsx:28` reads its baked
data in the render body for exactly this reason. Mirror that: `baked` is
computed each render (available at prerender), and the live fetch populates a
separate `fetched` state only when there is no baked file.

Replace the state declarations + effect (lines 23-35):

```tsx
  const [data, setData] = useState<AreaSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTrends, setShowTrends] = useState(true);

  useEffect(() => {
    if (!config) return;
    setLoading(true);
    fetchAreaSummary(config.slug, config.query, config.radius_km)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);
```

with:

```tsx
  const baked = config ? bakedArea(config.slug) : undefined;
  const [fetched, setFetched] = useState<AreaSummary | null>(null);
  const data = baked ?? fetched;
  const [loading, setLoading] = useState(!baked);
  const [error, setError] = useState<string | null>(null);
  const [showTrends, setShowTrends] = useState(true);

  useEffect(() => {
    if (!config || baked) return;   // baked data is already rendered; no fetch needed
    setLoading(true);
    fetchAreaSummary(config.slug, config.query, config.radius_km)
      .then(setFetched)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);
```

Leave the rest of the component unchanged — it already reads `data`, `loading`,
`error`, and `showTrends`; only the source of `data` changed. There must be no
remaining references to `setData` (it is gone).

- [ ] **Step 3: Type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Build and verify baking**

Run: `cd frontend && npm run build`
Expected: build succeeds. Then confirm the baked **data** (not just the static
heading) is inlined into the prerendered HTML — the `stats-grid` block only
renders when `data` is present at render time, so its presence proves the
synchronous baked read worked at prerender:
```bash
grep -q 'stats-grid' frontend/dist/area/rathmines/index.html \
  && ! grep -q 'Loading data' frontend/dist/area/rathmines/index.html \
  && echo "OK: area data baked into HTML"
```
Expected: `OK: area data baked into HTML`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/AreaPage.tsx
git commit -m "feat: serve area pages from baked JSON with live fallback

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: EircodePage — load baked JSON with live fallback

**Files:**
- Modify: `frontend/src/types.ts` (add `EircodePageData`)
- Modify: `frontend/src/pages/EircodePage.tsx:1-53`

**Interfaces:**
- Consumes: `frontend/src/data/eircodes/<CODE>.json` (Task 3), shape `{ eircode: EircodeResponse; trends: TrendPoint[] }`.
- Produces: `EircodePageData` interface in `types.ts`.

- [ ] **Step 1: Add the baked-data type**

In `frontend/src/types.ts`, after the `EircodeResponse` interface (after line 80), add:

```ts
export interface EircodePageData {
  eircode: EircodeResponse;
  trends: TrendPoint[];
}
```

- [ ] **Step 2: Add the eager glob + lookup helper**

In `frontend/src/pages/EircodePage.tsx`, update the type import on line 7 to include the new type:

```tsx
import type { EircodeResponse, TrendPoint, EircodePageData } from "../types";
```

Then, after the imports (below line 10) and before `formatPrice`, add:

```tsx
// Eager glob: eircode data is bundled for synchronous access at SSG prerender time.
const EIRCODE_DATA = import.meta.glob<{ default: EircodePageData }>("../data/eircodes/*.json", { eager: true });

function bakedEircode(code: string): EircodePageData | undefined {
  return EIRCODE_DATA[`../data/eircodes/${code}.json`]?.default;
}
```

- [ ] **Step 3: Read baked data synchronously; fetch only as fallback**

**Why synchronous:** same reason as AreaPage — effects don't run at SSG
prerender, so baked data must be read in the render body to be inlined into the
HTML.

Replace the state declarations + effect (lines 33-53):

```tsx
  const [data, setData] = useState<EircodeResponse | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!upperCode) return;
    setLoading(true);
    Promise.all([
      fetchEircode(upperCode, { limit: 10 }),
      fetchTrends(undefined, 5, data?.results[0]?.county ?? undefined),
    ])
      .then(([eircodeData, trendData]) => {
        setData(eircodeData);
        // Fetch county trends once we have the county
        const county = eircodeData.results[0]?.county;
        if (county) return fetchTrends(undefined, 5, county).then(setTrends);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [upperCode]);
```

with:

```tsx
  const baked = bakedEircode(upperCode);
  const [fetchedData, setFetchedData] = useState<EircodeResponse | null>(null);
  const [fetchedTrends, setFetchedTrends] = useState<TrendPoint[]>([]);
  const data = baked?.eircode ?? fetchedData;
  const trends = baked?.trends ?? fetchedTrends;
  const [loading, setLoading] = useState(!baked);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!upperCode || baked) return;   // baked data already rendered; no fetch
    setLoading(true);
    fetchEircode(upperCode, { limit: 10 })
      .then(eircodeData => {
        setFetchedData(eircodeData);
        const county = eircodeData.results[0]?.county;
        if (county) return fetchTrends(undefined, 5, county).then(setFetchedTrends);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [upperCode]);
```

`data` and `trends` remain the names the rest of the component reads — only
their source changed. This also removes the pre-existing bug where the live
path read `data?.results[0]` before `data` was set: the fallback now fetches the
eircode first, then its county trends. There must be no remaining references to
`setData` or `setTrends`.

- [ ] **Step 4: Type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Build and verify baking**

Run: `cd frontend && npm run build`
Expected: build succeeds. Confirm baked data is inlined (stats-grid renders only
when `data` is present at prerender):
```bash
grep -q 'stats-grid' frontend/dist/eircode/D02/index.html \
  && ! grep -q 'Loading data' frontend/dist/eircode/D02/index.html \
  && echo "OK: eircode data baked into HTML"
```
Expected: `OK: eircode data baked into HTML`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types.ts frontend/src/pages/EircodePage.tsx
git commit -m "feat: serve eircode pages from baked JSON with live fallback

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: CountyPage — load baked JSON with live fallback

Only the **default dynamic** county branch is changed. Counties with a custom template (`getCountyContent` → `CountyPageTemplate`, i.e. Cork/Galway/Dublin) return early and are untouched.

**Files:**
- Modify: `frontend/src/pages/CountyPage.tsx:1-131`

**Interfaces:**
- Consumes: `frontend/src/data/counties/<slug>.json` (Task 3), shape `CountySummary`.

- [ ] **Step 1: Add the eager glob + lookup helper**

In `frontend/src/pages/CountyPage.tsx`, after the imports (below line 18) and before `formatPrice`, add:

```tsx
// Eager glob: county data is bundled for synchronous access at SSG prerender time.
const COUNTY_DATA = import.meta.glob<{ default: CountySummary }>("../data/counties/*.json", { eager: true });

function bakedCounty(slug: string): CountySummary | undefined {
  return COUNTY_DATA[`../data/counties/${slug}.json`]?.default;
}
```

- [ ] **Step 2: Read baked data synchronously; cache/fetch only as fallback**

**Why synchronous:** same reason as AreaPage — effects don't run at SSG
prerender. Baked static data comes first (built from the PPR import), then the
existing localStorage cache, then the live API fallback.

Replace the state declarations + effect (lines 108-131):

```tsx
  const [data, setData] = useState<CountySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!county) return;

    // Try cache first
    const cached = getCachedCountyData(county);

    if (cached) {
      setData(cached);
      setLoading(false);
    } else {
      setLoading(true);
      fetchCountySummary(county)
        .then((freshData) => {
          setData(freshData);
          setCachedCountyData(county, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [county, slug]);
```

with:

```tsx
  const baked = slug ? bakedCounty(slug) : undefined;
  const [fetched, setFetched] = useState<CountySummary | null>(null);
  const data = baked ?? fetched;
  const [loading, setLoading] = useState(!baked);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!county || baked) return;   // baked data already rendered; no cache/fetch

    // localStorage cache, then a live API fallback.
    const cached = getCachedCountyData(county);
    if (cached) {
      setFetched(cached);
      setLoading(false);
    } else {
      setLoading(true);
      fetchCountySummary(county)
        .then((freshData) => {
          setFetched(freshData);
          setCachedCountyData(county, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [county, slug]);
```

`data` remains the name the rest of the component reads. There must be no
remaining references to `setData`.

- [ ] **Step 3: Type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Build and verify baking**

Run: `cd frontend && npm run build`
Expected: build succeeds. Verify a default (non-custom-template) county — e.g.
Meath — has its baked data inlined:
```bash
grep -q 'stats-grid' frontend/dist/county/meath/index.html \
  && echo "OK: county data baked into HTML"
```
Expected: `OK: county data baked into HTML`. (Cork/Galway/Dublin use the custom
`CountyPageTemplate` and are intentionally not converted.)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/CountyPage.tsx
git commit -m "feat: serve default county pages from baked JSON with live fallback

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Wire generation into the pipeline + document

**Files:**
- Modify: `scripts/ppr_full_pipeline.py:77-84` (add flag), `scripts/ppr_full_pipeline.py:145-166` (add Step 4)
- Modify: `CLAUDE.md` (biweekly workflow, step 4 block)
- Verify only (no edit expected): `frontend/vite.config.ts`

- [ ] **Step 1: Verify SSG routes already cover all three page types**

Run:
```bash
grep -n "county\|/area/\|/eircode/" frontend/vite.config.ts
```
Expected: `includedRoutes` already maps `COUNTIES`→`/county/*`, `AREAS`→`/area/*`, and `DUBLIN_EIRCODE_AREAS`→`/eircode/*` (lines ~21-28). No change needed. If any of the three is missing, add it mirroring the existing `areas`/`eircodes` lines. (This step is verification; there is no commit for it on its own.)

- [ ] **Step 2: Add the `--skip-page-data` flag**

In `scripts/ppr_full_pipeline.py`, after the `--skip-enrichment` argument (line 80), add:

```python
    parser.add_argument('--skip-page-data', action='store_true', help='Skip static page-data generation step')
```

- [ ] **Step 3: Add Step 4 (page-data generation) after enrichment**

In `scripts/ppr_full_pipeline.py`, immediately after the enrichment block (after line 160, before the `# Summary` block at line 162), add:

```python
    # Step 4: Regenerate static area/eircode/county page data (calls the backend API)
    if not args.skip_page_data:
        success = run_command(
            ['python3', 'scripts/generate_page_data.py'],
            "STEP 4: Generate static page data (area / eircode / county)",
            dry_run=args.dry_run
        )

        if not success:
            print("\n⚠️  Warning: Page-data generation had errors")
```

- [ ] **Step 4: Update the pipeline summary line**

In `scripts/ppr_full_pipeline.py`, after the existing `print(f"  3. Enrich: ...")` line (line 107), add:

```python
    print(f"  4. Page data:  {'SKIP' if args.skip_page_data else 'YES'}")
```

- [ ] **Step 5: Verify the pipeline parses and dry-runs**

Run:
```bash
python3 scripts/ppr_full_pipeline.py --skip-import --skip-geocoding --skip-enrichment --dry-run
```
Expected: prints the plan including `4. Page data: YES` and `[DRY RUN] Would run: STEP 4: Generate static page data ...`, exits 0.

- [ ] **Step 6: Document in CLAUDE.md**

In `CLAUDE.md`, in the "Biweekly Updates" section, update the step-4 regeneration block (the one starting `4. **Regenerate street landing-page data (after sync):**`) to also run the page-data generator. Add, alongside the existing `generate_street_data.py` / `generate_sitemap.py` commands:

```bash
python3 scripts/generate_page_data.py        # writes frontend/src/data/{areas,eircodes,counties}/*.json
git add frontend/src/data/areas frontend/src/data/eircodes frontend/src/data/counties
```
Add a sentence noting it requires the backend reachable (defaults to `http://localhost:8000`, override with `--api-url`) and that it is run automatically as Step 4 of `scripts/ppr_full_pipeline.py`.

- [ ] **Step 7: Commit**

```bash
git add scripts/ppr_full_pipeline.py CLAUDE.md
git commit -m "feat: regenerate static page data as pipeline step 4 + docs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Deployment (after all tasks)

- [ ] Push `main`: `git push origin main` — triggers Vercel (frontend, now serving baked pages) and Railway (backend, unchanged) deploys.
- [ ] Spot-check in production devtools: `/area/rathmines`, `/eircode/D02`, `/county/meath` render with **no** XHR to `/search`/`/trends`/`/eircode` (data came from the bundle).
- [ ] Fallback check: navigate to an area/eircode/county whose JSON is absent (or temporarily rename one locally) and confirm it still loads via the live API.
