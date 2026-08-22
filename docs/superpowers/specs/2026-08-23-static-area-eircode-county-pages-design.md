# Design: Static Area / Eircode / County Pages

**Date:** 2026-08-23
**Status:** Approved (pending spec review)
**Author:** Claude Code + Niall Murphy

## Problem

Three landing-page types make live backend/DB calls on every visit:

- `/area/:slug` (~35 areas) — `AreaPage.tsx` → `fetchAreaSummary` → `/search` + `/trends`
- `/eircode/:code` (22 Dublin postcodes) — `EircodePage.tsx` → `fetchEircode` + `/trends`
- `/county/:slug` (26 counties) — `CountyPage.tsx` → `fetchCountySummary` → `/counties` + `/trends` + `/search`

These pages change only when new PPR data is imported (biweekly). Serving them
via live calls adds latency and DB load for content that is effectively static
between imports. The `/street/:slug` pages already solved this: a generator
writes one JSON per page, the build bakes it in via `import.meta.glob`, and the
page renders with zero runtime calls.

## Goal

Convert area, eircode, and county pages to the same static-data pattern as
street pages, regenerated as part of the PPR import workflow. Keep a live-API
fallback so a page still works if its JSON is missing (e.g. a newly-added area
before the next regeneration).

## Non-Goals (YAGNI)

- No new backend endpoints.
- No DB schema changes.
- No changes to `api.ts` function signatures (they become fallback-only).
- No new page types beyond the three above.
- No change to search / valuation / other pages.

## Approach (chosen: API-driven generator)

The generator calls the **existing** backend endpoints — the same calls the
three pages make today — and dumps the responses to JSON. This guarantees
parity with live behavior and avoids re-implementing the area radius +
`locality` full-text + `routing_keys` filter (which lives in `backend/main.py`
`_append_area_filter` and the radius/trends queries) in SQL.

Rejected alternatives:

- **Direct-SQL generator** (street-data style): fastest and no backend
  dependency, but must duplicate the backend's area-filter + geocoding-center
  logic in Python/SQL, which will drift from `main.py`. The duplication is the
  maintenance trap we want to avoid.
- **Hybrid** (SQL for eircode/county, API for area): splits the generator into
  two mechanisms for little gain.

## Data Flow

```
PPR sync → DB updated
        → scripts/generate_page_data.py  (calls backend API per page)
        → frontend/src/data/{areas,eircodes,counties}/*.json  (committed)
        → vite-ssg build bakes JSON into prerendered HTML
        → Vercel deploy
```

At runtime each page loads its JSON from the bundle. On a miss, it falls back
to the existing live `fetch*` call.

## Components

### 1. Generator — `scripts/generate_page_data.py`

Single script. Reads its target lists from the frontend source of truth so it
cannot drift:

- **Areas:** parse `frontend/src/areas.ts` `AREAS` array (fields: `slug`,
  `query`, `radius_km`, `match` → `locality`, `routing_keys`).
- **Eircodes:** the 22 keys of `DUBLIN_EIRCODE_AREAS` in `frontend/src/areas.ts`.
- **Counties:** the 26-county list already used by `fetchCountySummary`
  (source: `/counties` endpoint response, or the province lists in `areas.ts`).

**Targets source-of-truth:** parse the `areas.ts` literals with a focused
regex first. `AREAS` and `DUBLIN_EIRCODE_AREAS` are plain object/array literals,
so this is tractable. If parsing proves brittle during implementation, fall
back to a committed `frontend/src/data/page_targets.json` kept in sync. Decide
this during implementation before committing the approach.

For each target the generator calls the backend (base URL from `--api-url`,
default `http://localhost:8000`) with the **same params** the frontend uses
today, assembles the exact object shape the page expects, and writes
`frontend/src/data/<type>/<slug>.json`.

- Area params: `/search?q=<query>&radius_km=<radius>&locality=<...>&routing_keys=<...>`
  and matching `/trends`. Assemble into `AreaSummary`.
- Eircode: `fetchEircode`-equivalent call + county-level `/trends`. Assemble into
  `{ eircode: EircodeResponse, trends: TrendPoint[] }`.
- County: `/counties` + `/trends?county=<c>` + `/search` (as `fetchCountySummary`).
  Assemble into `CountySummary`.

On any HTTP error for a target, log a `WARNING` and skip it (leave prior JSON
intact) — same failure behavior as `generate_street_data.py`.

CLI flags: `--api-url <url>`, `--only {areas,eircodes,counties}` (optional, for
partial regeneration), consistent with existing script conventions.

### 2. JSON schemas (reuse existing TS interfaces verbatim)

- `frontend/src/data/areas/<slug>.json` → `AreaSummary`
- `frontend/src/data/counties/<slug>.json` → `CountySummary`
- `frontend/src/data/eircodes/<CODE>.json` → `{ eircode: EircodeResponse; trends: TrendPoint[] }`

Recent-sales counts baked per page (match current live limits so pages look
identical): **area 20, county 10, eircode 10**.

No `types.ts` changes required.

### 3. Frontend consumers

Each page gets the glob lookup + fallback. Example (`AreaPage.tsx`):

```ts
const AREA_DATA = import.meta.glob<{ default: AreaSummary }>(
  "../data/areas/*.json", { eager: true }
);
// in effect:
const baked = AREA_DATA[`../data/areas/${slug}.json`]?.default;
if (baked) setData(baked);
else fetchAreaSummary(config.slug, config.query, config.radius_km).then(setData);
```

Same shape for `CountyPage` (fallback `fetchCountySummary`) and `EircodePage`
(fallback `fetchEircode` + `fetchTrends`). The `fetch*` functions in `api.ts`
remain unchanged and become fallback-only.

### 4. SSG routes

`vite.config.ts` `ssgOptions.includedRoutes` already enumerates `/area/*`,
`/eircode/*`, `/street/*`. Confirm `/county/*` is enumerated for the 26 county
slugs; add if missing so all three prerender with baked data.

### 5. Pipeline integration

- Add a step to `scripts/ppr_full_pipeline.py` after sync/geocode/enrich that
  runs `generate_page_data.py`, guarded by a `--skip-page-data` flag.
- Document the manual command in `CLAUDE.md`'s biweekly workflow, next to the
  existing `generate_street_data.py` / `generate_sitemap.py` block.

## Error Handling

- Missing JSON at runtime → live-API fallback (existing behavior preserved).
- Generator HTTP error per target → WARNING + skip (prior JSON retained).
- Generator run against an unreachable backend → fail fast with a clear message.

## Testing

- **Generator smoke test:** run against localhost backend; assert each output
  dir receives the expected file count and that a sample file validates against
  the expected keys of its interface.
- **Frontend:** a known slug loads from baked JSON with no network call; an
  unknown slug still falls back to the live fetch. Existing page rendering
  unchanged.
- **Regression:** pre-commit search regression suite unaffected (no backend
  logic changed).

## Rollout

1. Land generator + frontend consumers + JSON (committed).
2. Wire pipeline step + CLAUDE.md docs.
3. Deploy; verify the three page types render from baked data (no network in
   devtools) and fallback still works for a fabricated missing slug.
