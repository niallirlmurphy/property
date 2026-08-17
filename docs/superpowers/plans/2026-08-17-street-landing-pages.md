# Street Landing Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build 50 fully-static SEO landing pages (`/street/:slug`) for Ireland's highest-value and highest-volume streets, with data baked into the build (no runtime DB calls).

**Architecture:** A hand-authored registry JSON is the single source of truth. A Python generator reads it, queries Supabase once, and writes one static JSON per street (stats + yearly trends + recent transactions) under `frontend/src/data/streets/`. A new `StreetPage` React component imports those JSONs via an eager `import.meta.glob`, so `vite-react-ssg` inlines the data into prerendered HTML. No backend changes.

**Tech Stack:** Python 3.10+ (psycopg2), React 18 + TypeScript, Vite + `vite-react-ssg`, react-router-dom v6, Recharts, pytest.

**Spec:** `docs/superpowers/specs/2026-08-17-street-landing-pages-design.md`

## Global Constraints

- **No LIKE queries** on the DB; the generator groups in Python via the shared `street_key` helper (matches `scripts/analyze_top_streets.py`). Filters: `address_normalized IS NOT NULL AND not_full_market_price = FALSE AND price > 0 AND county IS NOT NULL`.
- **DATABASE_URL** is loaded from `backend/.env`: `export $(grep '^DATABASE_URL=' backend/.env | xargs)` before running generator/tests that hit the DB.
- **Single source of truth:** `frontend/src/data/streets_registry.json`. `streets.ts`, `vite.config.ts`, `generate_street_data.py`, and `generate_sitemap.py` all read it — never hardcode the street list anywhere else.
- **Generated data lives under `frontend/src/data/streets/`** (committed to git; the top-level `data/` dir is gitignored).
- **`normalizedKey` format** (must match the generator exactly): `"<street>|<area>|<county>"` where each part is `.strip().lower()` with internal whitespace collapsed to single spaces. Street/area come from the analysis, county is the DB county lowercased.
- **Display-name fixes** (the `St→Street` normalization artifact): registry `name` is hand-corrected but `normalizedKey` keeps the raw normalized value so it still matches DB rows.
- **URL path:** `/street/:slug`, singular. Slug = slugify(`"<name> <area>"`); append `-<countySlug>` only on collision.
- **TrendPoint shape** (consumed by `TrendsChart`): `{ year, count, median_price, avg_price, min_price, max_price }` — the generator's per-year objects must include all six fields.

---

## File Structure

**Create:**
- `scripts/street_key.py` — shared street-key extraction (factored out of `analyze_top_streets.py`).
- `tests/test_street_key.py` — pytest for the helper.
- `scripts/build_street_registry.py` — one-time authoring aid: CSV + overrides → `streets_registry.json`.
- `frontend/src/data/streets_registry.json` — the 50-street registry (source of truth).
- `scripts/generate_street_data.py` — biweekly generator: registry + DB → per-street JSON.
- `tests/test_generate_street_data.py` — pytest verifying generated output.
- `frontend/src/data/streets/<slug>.json` × 50 — generated per-street data.
- `frontend/src/streets.ts` — typed registry wrapper (`STREETS`, `streetFromSlug`).
- `frontend/src/pages/StreetPage.tsx` — the street page.
- `frontend/src/pages/StreetsIndexPage.tsx` — `/streets` index.

**Modify:**
- `scripts/analyze_top_streets.py` — import `street_key` from the shared module.
- `frontend/src/types.ts` — add `StreetData`, `StreetTransaction` interfaces.
- `frontend/src/main.tsx` — add `/street/:slug` and `/streets` routes.
- `frontend/vite.config.ts` — add street routes to `includedRoutes`.
- `frontend/src/pages/CountyPage.tsx` — add a "Notable streets" links section.
- `scripts/generate_sitemap.py` — emit `/street/<slug>` + `/streets` URLs from the registry.
- `CLAUDE.md` — document the generator as the final biweekly step.

---

## Task 1: Shared `street_key` helper

**Files:**
- Create: `scripts/street_key.py`
- Create: `tests/test_street_key.py`
- Modify: `scripts/analyze_top_streets.py` (replace inline logic with an import)

**Interfaces:**
- Produces: `street_key(addr: str, county: str) -> tuple | None` returning `((street_norm, area_norm, county_norm), (street_disp, area_disp, county_disp), apt_flag)` — identical semantics to the current inline function in `analyze_top_streets.py`. Also `normalize(s: str) -> str` and `normalized_key_string(street, area, county) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_street_key.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from street_key import street_key, normalize, normalized_key_string


def test_strips_house_number_and_builds_key():
    r = street_key("30 HAMPTON GREEN, NAVAN RD, DUBLIN 7", "Dublin")
    assert r is not None
    key, disp, apt = r
    assert key == ("hampton green", "navan road", "dublin")
    assert disp[0] == "Hampton Green"
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_street_key.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'street_key'`.

- [ ] **Step 3: Create the shared module**

Copy the constants (`LEAD_RE`, `GENERIC_FIRST`, `APT_PREFIX_RE`, `APT_NAME_RE`) and the `street_key` body from `scripts/analyze_top_streets.py` into a new file, adjusting the return to include the normalized-key string helper. `normalized_key_string` takes the three normalized parts and joins with `|`.

```python
# scripts/street_key.py
"""Shared street-name extraction, used by analyze_top_streets.py and
generate_street_data.py so the two can never diverge."""
import re

LEAD_RE = re.compile(
    r"^(?:(?:apartment|apt|unit|no\.?|flat|site)\s*)?\d+[a-z]?\s*(?:-\s*\d+[a-z]?\s*)?",
    re.IGNORECASE,
)
GENERIC_FIRST = re.compile(
    r"^(the\s+)?(apartment|apartments|penthouse|ground floor|first floor|second floor|"
    r"third floor|top floor|floor)\b",
    re.IGNORECASE,
)
APT_PREFIX_RE = re.compile(
    r"^(?:the\s+)?(apartment|apt|penthouse|ground floor|first floor|second floor|"
    r"third floor|top floor|floor|flat)\b",
    re.IGNORECASE,
)
APT_NAME_RE = re.compile(r"\b(block|building|apartments?)\b", re.IGNORECASE)


def normalize(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def normalized_key_string(street_norm, area_norm, county_norm):
    return f"{street_norm}|{area_norm}|{county_norm}"


def street_key(addr, county):
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    if len(parts) < 2:
        return None
    first = parts[0]
    apt_flag = bool(APT_PREFIX_RE.match(first))
    stripped = LEAD_RE.sub("", first).strip()
    idx = 0
    if not stripped or GENERIC_FIRST.match(stripped) or len(stripped) < 3:
        if len(parts) >= 3:
            stripped = parts[1]
            idx = 1
        else:
            return None
    street = stripped
    if not re.search(r"[a-zA-Z]{3,}", street):
        return None
    area = parts[idx + 1] if len(parts) > idx + 1 else county
    return (
        (normalize(street), normalize(area), county.strip().lower()),
        (street.strip(), area.strip(), county.strip()),
        apt_flag,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_street_key.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Refactor `analyze_top_streets.py` to import the helper**

In `scripts/analyze_top_streets.py`, delete the inline `LEAD_RE`, `GENERIC_FIRST`, `APT_PREFIX_RE`, `APT_NAME_RE` definitions and the `street_key`/`norm` inner logic, and instead add at the top:

```python
from street_key import street_key, APT_NAME_RE
```

(Keep `APT_FRACTION_THRESHOLD`, `MIN_TX_*`, `N_VALUE`, `N_VOLUME` local. The `street_key` call sites already unpack `(key, disp, apt_flag)`, which matches the shared signature.) Add `sys.path` insert if needed, or run from `scripts/`.

- [ ] **Step 6: Verify the analysis still runs identically**

Run: `cd "/Users/nmurphy/claude/property price project" && export $(grep '^DATABASE_URL=' backend/.env | xargs) && python3 scripts/analyze_top_streets.py | head -5`
Expected: same header line "processed 757,308 sales ... excluded 2,631 apartment-complex groups" (counts may drift slightly if the DB changed; structure identical).

- [ ] **Step 7: Commit**

```bash
git add scripts/street_key.py tests/test_street_key.py scripts/analyze_top_streets.py
git commit -m "refactor: extract shared street_key helper"
```

---

## Task 2: Build the street registry JSON

**Files:**
- Create: `scripts/build_street_registry.py`
- Create: `frontend/src/data/streets_registry.json` (script output, committed)

**Interfaces:**
- Produces: `frontend/src/data/streets_registry.json` — a JSON array of 50 objects with keys: `slug, name, area, county, countySlug, areaSlug (optional), category ("value"|"volume"), rank (int), normalizedKey, description, info (optional), image (optional), imageAlt (optional)`.
- Consumes: `data/top_streets_analysis.csv` (from Task's analysis run) and `scripts/street_key.py`'s `normalize`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_street_registry.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_street_registry.py -v`
Expected: FAIL — registry file does not exist yet (`FileNotFoundError`).

- [ ] **Step 3: Write the registry builder**

```python
# scripts/build_street_registry.py
"""One-time authoring aid: read data/top_streets_analysis.csv, apply display
overrides, compute slugs + normalizedKey, and write the registry JSON.
Re-runnable and deterministic. After this, streets_registry.json is the
hand-maintained source of truth."""
import csv, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from street_key import normalize, normalized_key_string

ROOT = os.path.join(os.path.dirname(__file__), "..")
CSV = os.path.join(ROOT, "data", "top_streets_analysis.csv")
OUT = os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")

COUNTY_SLUG = lambda c: c.strip().lower().replace(" ", "-")

# Hand-corrected display names, keyed by (raw street, area) from the CSV.
NAME_FIX = {
    ("Street Kevins Park", "Dartry"): "St Kevin's Park",
    ("Street Marys Road", "Ballsbridge"): "St Mary's Road",
    ("the Burbidge", "Lansdowne Place"): "The Burbidge",
    ("the Links", "Elm Park"): "The Links",
}

# Optional 2-3 sentence factual commentary, keyed by slug. Only verifiable facts.
INFO = {
    "ailesbury-road-ballsbridge": "Ailesbury Road is a wide, tree-lined Victorian road in Ballsbridge, Dublin 4, long regarded as one of Dublin's most prestigious residential addresses. Its large detached red-brick and stucco houses date largely from the 1860s to 1880s, and a number serve as embassies and diplomatic residences.",
    "fitzwilliam-square-dublin-2": "Fitzwilliam Square is one of the last and best-preserved of Dublin's great Georgian squares, laid out in the early 19th century in Dublin 2. Its four terraces of red-brick townhouses surround a private garden that remains accessible only to residents and keyholders.",
    "herbert-park-ballsbridge": "Herbert Park is a residential road in Ballsbridge, Dublin 4, running alongside the public park of the same name, which was laid out for the 1907 Irish International Exhibition. The road is lined with substantial Edwardian red-brick houses.",
    "longford-terrace-monkstown": "Longford Terrace is a seafront Victorian terrace in Monkstown, south County Dublin, overlooking Dublin Bay. Its tall, stucco-fronted houses form one of the best-known 19th-century terraces on the coast.",
    "palmerston-road-rathmines": "Palmerston Road is a broad, tree-lined Victorian avenue in Rathmines, Dublin 6, developed largely in the second half of the 19th century. It is known for its large red-brick and granite houses set back behind mature front gardens.",
    "clyde-road-ballsbridge": "Clyde Road is a Victorian residential road in Ballsbridge, Dublin 4, close to the River Dodder. It is characterised by large detached and semi-detached red-brick houses dating mainly from the 1860s and 1870s.",
}

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

def main():
    rows = list(csv.DictReader(open(CSV)))
    # base slug from name+area; resolve collisions by appending county slug
    base = []
    for r in rows:
        raw_name, area, county = r["street"], r["area"], r["county"]
        name = NAME_FIX.get((raw_name, area), raw_name)
        # title-case a leading lowercase "the"
        name = re.sub(r"^the\b", "The", name)
        base.append({"raw_name": raw_name, "name": name, "area": area, "county": county, "row": r})
    slug_counts = {}
    for b in base:
        s = slugify(f"{b['name']} {b['area']}")
        slug_counts[s] = slug_counts.get(s, 0) + 1
    out = []
    for b in base:
        r = b["row"]
        s = slugify(f"{b['name']} {b['area']}")
        if slug_counts[s] > 1:
            s = slugify(f"{b['name']} {b['area']} {b['county']}")
        median = int(r["median_price"]); count = int(r["tx_count"])
        cat = r["rank_type"]
        if cat == "value":
            desc = (f"One of Ireland's highest-value streets, with a median sale price of "
                    f"€{median:,} across {count} recorded sales on the Property Price Register.")
        else:
            desc = (f"One of Ireland's most active streets, with {count} recorded sales on the "
                    f"Property Price Register and a median price of €{median:,}.")
        entry = {
            "slug": s,
            "name": b["name"],
            "area": b["area"],
            "county": b["county"],
            "countySlug": COUNTY_SLUG(b["county"]),
            "category": cat,
            "rank": int(r["rank"]),
            "normalizedKey": normalized_key_string(
                normalize(b["raw_name"]), normalize(b["area"]), b["county"].strip().lower()),
            "description": desc,
        }
        if s in INFO:
            entry["info"] = INFO[s]
        out.append(entry)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"wrote {OUT} with {len(out)} streets")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the builder** (regenerate the analysis CSV first if it is stale)

Run:
```bash
cd "/Users/nmurphy/claude/property price project" && export $(grep '^DATABASE_URL=' backend/.env | xargs) \
  && python3 scripts/analyze_top_streets.py >/dev/null \
  && python3 scripts/build_street_registry.py
```
Expected: `wrote .../streets_registry.json with 50 streets`.

- [ ] **Step 5: Run the registry test to verify it passes**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_street_registry.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add scripts/build_street_registry.py tests/test_street_registry.py frontend/src/data/streets_registry.json
git commit -m "feat: add street registry (source of truth) + builder"
```

---

## Task 3: Per-street data generator

**Files:**
- Create: `scripts/generate_street_data.py`
- Create: `tests/test_generate_street_data.py`
- Creates at runtime: `frontend/src/data/streets/<slug>.json` × 50

**Interfaces:**
- Consumes: `frontend/src/data/streets_registry.json`, `scripts/street_key.py`, `DATABASE_URL`.
- Produces: one JSON per street: `{ slug, stats: {count, median, avg, min, max, firstYear, lastYear}, trends: TrendPoint[], transactions: StreetTransaction[], totalTransactions }`. `TrendPoint = {year, count, median_price, avg_price, min_price, max_price}`. `StreetTransaction = {date (YYYY-MM-DD), address, price, bedrooms|null, propertyType|null, eircode|null}` (latest 50, newest first).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generate_street_data.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_generate_street_data.py -v`
Expected: FAIL — data files do not exist.

- [ ] **Step 3: Write the generator**

```python
# scripts/generate_street_data.py
"""Biweekly generator: read the street registry, query Supabase once, and write
one static JSON per street (stats + yearly trends + latest 50 transactions).
Run after the PPR sync, then rebuild/redeploy the frontend."""
import json, os, sys
import psycopg2
from collections import defaultdict
from statistics import median as _median
sys.path.insert(0, os.path.dirname(__file__))
from street_key import street_key, normalized_key_string

ROOT = os.path.join(os.path.dirname(__file__), "..")
REG = os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")
OUTDIR = os.path.join(ROOT, "frontend", "src", "data", "streets")

def main():
    registry = json.load(open(REG))
    targets = {e["normalizedKey"]: e["slug"] for e in registry}
    tx = defaultdict(list)  # normalizedKey -> list of transaction dicts

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(name="stream"); cur.itersize = 20000
    cur.execute("""
        SELECT address_normalized, county, price, sale_date, address,
               bedrooms, property_type, eircode
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND not_full_market_price = FALSE
          AND price > 0 AND county IS NOT NULL
    """)
    for addr, county, price, sale_date, raw_addr, beds, ptype, eircode in cur:
        r = street_key(addr, county)
        if not r:
            continue
        key = normalized_key_string(*r[0])
        if key not in targets:
            continue
        tx[key].append({
            "date": sale_date.isoformat(),
            "address": raw_addr,
            "price": float(price),
            "bedrooms": beds,
            "propertyType": ptype,
            "eircode": eircode,
        })
    conn.close()

    os.makedirs(OUTDIR, exist_ok=True)
    written = 0
    for entry in registry:
        key = entry["normalizedKey"]; slug = entry["slug"]
        rows = tx.get(key, [])
        prices = [t["price"] for t in rows]
        years = sorted({int(t["date"][:4]) for t in rows}) if rows else []
        # per-year trend points
        by_year = defaultdict(list)
        for t in rows:
            by_year[int(t["date"][:4])].append(t["price"])
        trends = []
        for y in years:
            pl = by_year[y]
            trends.append({
                "year": y, "count": len(pl),
                "median_price": round(_median(pl)),
                "avg_price": round(sum(pl) / len(pl)),
                "min_price": round(min(pl)), "max_price": round(max(pl)),
            })
        recent = sorted(rows, key=lambda t: t["date"], reverse=True)[:50]
        for t in recent:
            t["price"] = round(t["price"])
        stats = {
            "count": len(rows),
            "median": round(_median(prices)) if prices else 0,
            "avg": round(sum(prices) / len(prices)) if prices else 0,
            "min": round(min(prices)) if prices else 0,
            "max": round(max(prices)) if prices else 0,
            "firstYear": years[0] if years else None,
            "lastYear": years[-1] if years else None,
        }
        json.dump({"slug": slug, "stats": stats, "trends": trends,
                   "transactions": recent, "totalTransactions": len(rows)},
                  open(os.path.join(OUTDIR, slug + ".json"), "w"),
                  indent=2, ensure_ascii=False)
        written += 1
        if not rows:
            print(f"WARNING: no transactions matched for {slug} ({key})")
    print(f"wrote {written} street data files to {OUTDIR}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the generator**

Run: `cd "/Users/nmurphy/claude/property price project" && export $(grep '^DATABASE_URL=' backend/.env | xargs) && python3 scripts/generate_street_data.py`
Expected: `wrote 50 street data files ...` with no `WARNING:` lines. If any WARNING appears, the registry `normalizedKey` doesn't match the DB — recheck Task 2's `normalize`/`normalized_key_string` usage.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_generate_street_data.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_street_data.py tests/test_generate_street_data.py frontend/src/data/streets/
git commit -m "feat: add per-street static data generator + generated data"
```

---

## Task 4: Types + typed registry wrapper

**Files:**
- Modify: `frontend/src/types.ts` (append interfaces)
- Create: `frontend/src/streets.ts`

**Interfaces:**
- Produces: `StreetData`, `StreetTransaction`, `StreetTrendPoint` in `types.ts`; `StreetConfig`, `STREETS`, `streetFromSlug`, `streetsForCounty` in `streets.ts`.
- Consumes: `frontend/src/data/streets_registry.json` (Task 2), `TrendPoint` (existing in `types.ts`).

- [ ] **Step 1: Add types to `frontend/src/types.ts`**

Append at the end of the file:

```ts
export interface StreetTransaction {
  date: string;            // YYYY-MM-DD
  address: string;
  price: number;
  bedrooms: number | null;
  propertyType: string | null;
  eircode: string | null;
}

export interface StreetData {
  slug: string;
  stats: {
    count: number;
    median: number;
    avg: number;
    min: number;
    max: number;
    firstYear: number | null;
    lastYear: number | null;
  };
  trends: TrendPoint[];         // reuses existing TrendPoint (year, count, median_price, avg_price, min_price, max_price)
  transactions: StreetTransaction[];
  totalTransactions: number;
}
```

- [ ] **Step 2: Create `frontend/src/streets.ts`**

```ts
import registry from "./data/streets_registry.json";

export interface StreetConfig {
  slug: string;
  name: string;
  area: string;
  county: string;
  countySlug: string;
  areaSlug?: string;
  category: "value" | "volume";
  rank: number;
  normalizedKey: string;
  description: string;
  info?: string;
  image?: string;
  imageAlt?: string;
}

export const STREETS: StreetConfig[] = registry as StreetConfig[];

export function streetFromSlug(slug: string): StreetConfig | undefined {
  return STREETS.find(s => s.slug === slug);
}

export function streetsForCounty(countySlug: string): StreetConfig[] {
  return STREETS.filter(s => s.countySlug === countySlug);
}
```

- [ ] **Step 3: Verify JSON module imports type-check**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npx tsc --noEmit`
Expected: no errors. (Vite/TS already allows JSON imports via `resolveJsonModule`; if tsc complains, confirm `"resolveJsonModule": true` in `tsconfig.json` — it should already be set since blog/areas use similar patterns.)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/streets.ts
git commit -m "feat: add StreetData types and typed streets registry"
```

---

## Task 5: StreetPage component

**Files:**
- Create: `frontend/src/pages/StreetPage.tsx`

**Interfaces:**
- Consumes: `streetFromSlug` (Task 4), `StreetData` (Task 4), the generated JSON via eager glob, and existing components `PageHeader`, `Breadcrumbs`, `TrendsChart`, `Footer`, `MapSearchThumb`, `usePageMeta`.
- Produces: default-exported `StreetPage` React component.

- [ ] **Step 1: Create the component**

Mirrors `AreaPage.tsx` but reads static data (no `useEffect` fetch). Loads all street JSONs eagerly so SSG inlines the right one.

```tsx
// frontend/src/pages/StreetPage.tsx
import { useParams, Link } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import MapSearchThumb from "../components/MapSearchThumb";
import { usePageMeta } from "../hooks/usePageMeta";
import { streetFromSlug } from "../streets";
import type { StreetData } from "../types";

// Eager glob: all street data is bundled so the correct file is available
// synchronously at SSG prerender time (inlined into HTML for SEO).
const DATA = import.meta.glob<{ default: StreetData }>("../data/streets/*.json", { eager: true });

function dataForSlug(slug: string): StreetData | undefined {
  const mod = DATA[`../data/streets/${slug}.json`];
  return mod?.default;
}

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

export default function StreetPage() {
  const { slug } = useParams<{ slug: string }>();
  const config = streetFromSlug(slug ?? "");
  const data = config ? dataForSlug(config.slug) : undefined;

  const crumbs = config
    ? [
        { name: `County ${config.county}`, url: `/county/${config.countySlug}` },
        { name: "Notable Streets", url: "/streets" },
        { name: config.name, url: `/street/${config.slug}` },
      ]
    : [];

  const title = config ? `Property Prices on ${config.name}, ${config.area}` : undefined;
  const meta = usePageMeta(
    title,
    config
      ? `${config.description} See recent sales and price trends for ${config.name}, ${config.area}, Co. ${config.county} from Ireland's Property Price Register.`
      : undefined,
    crumbs,
    config?.image,
  );

  if (!config || !data) {
    return (
      <>
        <PageHeader title="Street not found" />
        <div className="content-page"><h1>Street not found</h1></div>
      </>
    );
  }

  const { stats } = data;
  const q = `${config.name}, ${config.area}`;
  const faqs = [
    {
      q: `What is the average price on ${config.name}?`,
      a: `The average sale price recorded on ${config.name}, ${config.area} is ${formatPrice(stats.avg)}, based on ${stats.count} sales on the Property Price Register.`,
    },
    {
      q: `How many properties have sold on ${config.name}?`,
      a: `${stats.count} residential sales on ${config.name}, ${config.area} have been recorded on the Property Price Register${stats.firstYear ? ` since ${stats.firstYear}` : ""}.`,
    },
    {
      q: `What is the median price on ${config.name}?`,
      a: `The median sale price on ${config.name}, ${config.area} is ${formatPrice(stats.median)}, with recorded sales ranging from ${formatPrice(stats.min)} to ${formatPrice(stats.max)}.`,
    },
  ];
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map(f => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  return (
    <>
      {meta}
      <PageHeader title={title!} titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Property Prices on {config.name}, {config.area}</h1>

        {config.image && (
          <img
            className="area-hero"
            src={config.image}
            alt={config.imageAlt ?? config.name}
            width={2000}
            height={1500}
            loading="lazy"
          />
        )}

        {config.info && <p className="area-info">{config.info}</p>}
        <p className="content-intro">{config.description}</p>

        <div className="stats-grid">
          <div className="stat-card"><span>Median price</span><strong>{formatPrice(stats.median)}</strong></div>
          <div className="stat-card"><span>Average price</span><strong>{formatPrice(stats.avg)}</strong></div>
          <div className="stat-card"><span>Sales on record</span><strong>{stats.count.toLocaleString()}</strong></div>
          <div className="stat-card"><span>Price range</span><strong>{formatPrice(stats.min)} – {formatPrice(stats.max)}</strong></div>
        </div>

        {data.trends.length > 0 && (
          <section className="content-section">
            <h2>Price Trends on {config.name}</h2>
            <p>Median and average sale prices by year, {stats.firstYear}–{stats.lastYear}.</p>
            <div style={{ position: "relative", height: 240 }}>
              <TrendsChart data={data.trends} onClose={() => {}} inline />
            </div>
          </section>
        )}

        {data.transactions.length > 0 && (
          <section className="content-section">
            <h2>Recent Sales on {config.name}</h2>
            <table className="sales-table">
              <thead><tr><th>Address</th><th>Date</th><th>Beds</th><th>Type</th><th>Price</th></tr></thead>
              <tbody>
                {data.transactions.map((t, i) => (
                  <tr key={i}>
                    <td>{t.address}</td>
                    <td>{t.date}</td>
                    <td>{t.bedrooms ?? "—"}</td>
                    <td>{t.propertyType ?? "—"}</td>
                    <td>{formatPrice(t.price)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.totalTransactions > data.transactions.length && (
              <p className="content-note">Showing the {data.transactions.length} most recent of {data.totalTransactions} recorded sales.</p>
            )}
          </section>
        )}

        <section className="content-section">
          <h2>Frequently Asked Questions</h2>
          {faqs.map((f, i) => (
            <div key={i} className="faq-item">
              <h3>{f.q}</h3>
              <p>{f.a}</p>
            </div>
          ))}
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
        </section>

        <section className="content-section">
          <h2>Search Nearby Properties</h2>
          <MapSearchThumb
            to={`/?q=${encodeURIComponent(q)}`}
            label={`Search around ${config.name} on the map`}
          />
          <p>
            {config.name} is in <Link to={`/county/${config.countySlug}`}>County {config.county}</Link>.{" "}
            Browse <Link to="/streets">all notable streets</Link>.
          </p>
        </section>

        <Footer />
      </div>
    </>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npx tsc --noEmit`
Expected: no errors. (If `import.meta.glob` generic errors, confirm `vite/client` is in tsconfig `types` — it is, since `import.meta.env` is used in `api.ts`.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/StreetPage.tsx
git commit -m "feat: add StreetPage (static data, no runtime fetch)"
```

---

## Task 6: Streets index page

**Files:**
- Create: `frontend/src/pages/StreetsIndexPage.tsx`

**Interfaces:**
- Consumes: `STREETS` (Task 4), `usePageMeta`, `PageHeader`, `Breadcrumbs`, `Footer`.
- Produces: default-exported `StreetsIndexPage`.

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/pages/StreetsIndexPage.tsx
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import { STREETS } from "../streets";

export default function StreetsIndexPage() {
  const crumbs = [{ name: "Notable Streets", url: "/streets" }];
  const meta = usePageMeta(
    "Notable Streets in Ireland",
    "Property price guides for Ireland's highest-value and most active streets, based on the Property Price Register.",
    crumbs,
  );
  const value = STREETS.filter(s => s.category === "value").sort((a, b) => a.rank - b.rank);
  const volume = STREETS.filter(s => s.category === "volume").sort((a, b) => a.rank - b.rank);

  const list = (items: typeof STREETS) => (
    <ul className="street-index-list">
      {items.map(s => (
        <li key={s.slug}>
          <Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link>
          <span className="street-index-county"> · Co. {s.county}</span>
        </li>
      ))}
    </ul>
  );

  return (
    <>
      {meta}
      <PageHeader title="Notable Streets in Ireland" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Notable Streets in Ireland</h1>
        <p className="content-intro">
          Dedicated property-price guides for Ireland's highest-value and most active
          streets, drawn from the Property Price Register (2010 onwards).
        </p>
        <section className="content-section">
          <h2>Highest-value streets</h2>
          {list(value)}
        </section>
        <section className="content-section">
          <h2>Most active streets</h2>
          {list(volume)}
        </section>
        <Footer />
      </div>
    </>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/StreetsIndexPage.tsx
git commit -m "feat: add /streets index page"
```

---

## Task 7: Wire routes in main.tsx

**Files:**
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Add imports**

After the `import BlogPostPage ...` line (`main.tsx:23`), add:

```tsx
import StreetPage from "./pages/StreetPage";
import StreetsIndexPage from "./pages/StreetsIndexPage";
```

- [ ] **Step 2: Add routes**

In the `routes` array, next to the `/area/:slug` entry, add:

```tsx
  { path: "/streets", element: <StreetsIndexPage /> },
  { path: "/street/:slug", element: <StreetPage /> },
```

(Place `/streets` before `/street/:slug`; both before the catch-all `*`.)

- [ ] **Step 3: Type-check**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/main.tsx
git commit -m "feat: add /street and /streets routes"
```

---

## Task 8: Prerender street routes (SSG)

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Import the registry**

Change the import line (`vite.config.ts:3`) to also pull `STREETS`:

```ts
import { COUNTIES, AREAS, DUBLIN_EIRCODE_AREAS, countySlug } from "./src/areas";
import { STREETS } from "./src/streets";
```

- [ ] **Step 2: Add street routes to `includedRoutes`**

Inside `includedRoutes`, add:

```ts
      const streets = STREETS.map((s) => `/street/${s.slug}`);
```

and include them (plus the index) in the returned array:

```ts
      return [...staticPaths, ...counties, ...areas, ...eircodes, ...posts, ...streets];
```

(`/streets` is a static path with no `:` so it is already kept by the `staticPaths` filter once the route exists in `main.tsx`.)

- [ ] **Step 3: Build and verify prerender**

Run:
```bash
cd "/Users/nmurphy/claude/property price project/frontend" && npm run build \
  && ls dist/street | head && test -f dist/street/ailesbury-road-ballsbridge/index.html && echo PRERENDER_OK \
  && test -f dist/streets/index.html && echo INDEX_OK
```
Expected: `PRERENDER_OK` and `INDEX_OK`; `dist/street/` lists ~50 slug directories.

- [ ] **Step 4: Verify data is inlined into HTML (SEO check)**

Run:
```bash
cd "/Users/nmurphy/claude/property price project/frontend" \
  && grep -q "Ailesbury Road" dist/street/ailesbury-road-ballsbridge/index.html && echo TITLE_OK \
  && grep -q "3,875,000" dist/street/ailesbury-road-ballsbridge/index.html && echo STATS_INLINED_OK
```
Expected: `TITLE_OK` and `STATS_INLINED_OK` (confirms stats are baked into static HTML, not fetched at runtime).

- [ ] **Step 5: Commit**

```bash
git add frontend/vite.config.ts
git commit -m "feat: prerender /street/:slug routes via SSG"
```

---

## Task 9: County-page internal links

**Files:**
- Modify: `frontend/src/pages/CountyPage.tsx`

**Interfaces:**
- Consumes: `streetsForCounty` (Task 4).

- [ ] **Step 1: Import the helper**

Add to the imports in `CountyPage.tsx`:

```tsx
import { streetsForCounty } from "../streets";
```

- [ ] **Step 2: Add a "Notable streets" section**

In the default dynamic page render (after the "Areas in County" grid, near `CountyPage.tsx:263`), add a section that only renders when the county has streets. Use `slug` (the county slug from `useParams`) already in scope:

```tsx
{streetsForCounty(slug ?? "").length > 0 && (
  <section className="content-section">
    <h2>Notable Streets in {countyName}</h2>
    <ul className="street-links">
      {streetsForCounty(slug ?? "").map(s => (
        <li key={s.slug}>
          <Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link>
        </li>
      ))}
    </ul>
    <p><Link to="/streets">Browse all notable streets in Ireland →</Link></p>
  </section>
)}
```

(If the variable holding the county display name is not `countyName`, use whatever `CountyPage.tsx` already uses for the `<h1>` — confirm by reading the file first. `Link` is already imported there.)

- [ ] **Step 3: Type-check and build**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npx tsc --noEmit && npm run build >/dev/null && echo BUILD_OK`
Expected: `BUILD_OK`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/CountyPage.tsx
git commit -m "feat: link notable streets from county pages"
```

---

## Task 10: Sitemap entries

**Files:**
- Modify: `scripts/generate_sitemap.py`

- [ ] **Step 1: Load the registry and emit street URLs**

Near the top of `generate_sitemap.py`, add:

```python
import json
from pathlib import Path
_REG = Path(__file__).parent.parent / "frontend" / "src" / "data" / "streets_registry.json"
STREET_SLUGS = [e["slug"] for e in json.load(open(_REG))]
```

After the "Add area pages" loop (`generate_sitemap.py:~108`), add:

```python
    # Add streets index + individual street pages
    lines.extend([
        "  <url>",
        f"    <loc>{BASE_URL}/streets</loc>",
        f"    <lastmod>{today}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>0.7</priority>",
        "  </url>",
    ])
    for slug in STREET_SLUGS:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}/street/{slug}</loc>",
            f"    <lastmod>{today}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.6</priority>",
            "  </url>",
        ])
```

(Confirm the exact variable names `BASE_URL` and `today` by reading the file; reuse whatever it already defines.)

- [ ] **Step 2: Regenerate and verify**

Run:
```bash
cd "/Users/nmurphy/claude/property price project" && python3 scripts/generate_sitemap.py \
  && grep -c "/street/" frontend/public/sitemap.xml
```
Expected: prints a count of `50` (plus the `/streets` index line matches `/streets` but not `/street/`).

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_sitemap.py frontend/public/sitemap.xml
git commit -m "feat: add street pages to sitemap"
```

---

## Task 11: Document the biweekly step

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add a generation step to the pipeline docs**

In the "Biweekly Updates" section of `CLAUDE.md`, after the enrichment step, add:

```markdown
4. **Regenerate street landing-page data (after sync):**
```bash
export $(grep '^DATABASE_URL=' backend/.env | xargs)
python3 scripts/generate_street_data.py     # writes frontend/src/data/streets/*.json
python3 scripts/generate_sitemap.py          # refresh sitemap
git add frontend/src/data/streets frontend/public/sitemap.xml
git commit -m "chore: refresh street page data" && git push origin main
```
This refreshes the 50 static street pages (`/street/:slug`). Data is baked into
the SSG build, so a redeploy (automatic on push) is required for changes to show.
To change *which* streets get pages, re-run `python3 scripts/analyze_top_streets.py`
then `python3 scripts/build_street_registry.py` and review the registry diff.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document street page data regeneration step"
```

---

## Task 12: Final verification

- [ ] **Step 1: Run the full Python test suite for the new code**

Run: `cd "/Users/nmurphy/claude/property price project" && python3 -m pytest tests/test_street_key.py tests/test_street_registry.py tests/test_generate_street_data.py -v`
Expected: all pass.

- [ ] **Step 2: Full frontend build**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npm run build 2>&1 | tail -20 && ls dist/street | wc -l`
Expected: build succeeds; `ls dist/street | wc -l` prints `50`.

- [ ] **Step 3: Local smoke test one page**

Run: `cd "/Users/nmurphy/claude/property price project/frontend" && npm run preview &` then open `http://localhost:4173/street/ailesbury-road-ballsbridge` and confirm: H1, stats grid, trends chart, transactions table, FAQ all render. Stop the preview server afterward.

- [ ] **Step 4: Confirm no runtime API calls**

In the browser devtools Network tab on the street page, confirm there are **no** requests to the backend `/search` or `/trends` endpoints (data is static). Only static asset + JSON chunk requests are expected.

---

## Self-Review

**Spec coverage:**
- Fully-static data baked at build → Tasks 3, 5, 8 (eager glob + prerender + inlined-HTML check in Task 8 Step 4). ✅
- Registry single source of truth → Tasks 2, 4; consumed by Tasks 3, 8, 10. ✅
- `/street/:slug` + `/streets` → Tasks 6, 7, 8. ✅
- Mirror area pages + templated text + FAQ (JSON-LD) → Task 5. ✅
- `info` commentary + hero image slot → Tasks 2 (INFO/NAME_FIX, optional fields), 4 (StreetConfig), 5 (renders `info`/`image`). ✅
- Generator reuses shared `street_key` → Tasks 1, 3. ✅
- St→Street display fix → Task 2 (NAME_FIX), tested. ✅
- Sitemap + internal linking (county pages, index) → Tasks 6, 9, 10. ✅
- No backend changes → confirmed; no task touches `backend/`. ✅
- Biweekly doc step → Task 11. ✅
- Testing (generator asserts, build prerender, slug uniqueness) → Tasks 2, 3, 8, 12. ✅

**Placeholder scan:** No TBD/TODO; every code step has concrete code. Two spots ask the executor to confirm an existing variable name by reading the file (`countyName` in Task 9, `BASE_URL`/`today` in Task 10) — these are verification instructions, not placeholders, because the surrounding code is provided.

**Type consistency:** `StreetData`/`StreetTransaction` (Task 4) match the generator's JSON keys (Task 3) — `stats.{count,median,avg,min,max,firstYear,lastYear}`, `trends: TrendPoint[]` with all six fields, `transactions` with `{date,address,price,bedrooms,propertyType,eircode}`, `totalTransactions`. `StreetConfig` fields (Task 4) match `build_street_registry.py` output (Task 2). `streetFromSlug`/`streetsForCounty` used consistently in Tasks 5, 6, 9. `normalizedKey` format identical in Task 2 (builder) and Task 3 (generator via `normalized_key_string`).
