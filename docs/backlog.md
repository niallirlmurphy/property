# Product backlog

Tracked issues and deferred work. Newest first.

## Bugs

### Recent sales invisible to search — lat/lon set but `geog` NULL (HIGH)
- **Status:** FIXED 2026-09-27 — backfilled all 3,442 rows (48 Mount Carmel Rd now
  searchable), and added a self-healing `geog` step (`scripts/backfill_geog.py`,
  wired into `scripts/ppr_full_pipeline.py` as Step 2b) so future workflow runs
  can't leave lat/lon-without-geog rows. Follow-up (optional): identify the ad-hoc
  writer that set coords without geog, or make `geog` a generated column.
- **Symptom:** genuinely nearby, full-market recent sales are missing from radius
  and polygon search. Example: "48 Mount Carmel Rd, Goatstown" (€958k, 25 Jun
  2026) is ~16 m from the searched "44 Mount Carmel Road" but did not appear in a
  0.5 km search.
- **Root cause:** the row has correct `latitude`/`longitude` but its PostGIS
  `geog` column is NULL. Radius/polygon search (`backend/valuation/comparable_search.py`
  and `backend/main.py`) filter `geog IS NOT NULL` and match with
  `ST_DWithin(geog, …)`, so a NULL-`geog` row is silently excluded even though its
  coordinates are valid and would plot on a lat/lon map.
- **Scale:** 3,442 rows have lat/lon but NULL `geog`; **2,483 are 2026 sales** —
  i.e. the newest, most-searched data. So the geocode/import write path is setting
  lat/lon without backfilling `geog`.
- **Fix direction:** (1) one-off backfill —
  `UPDATE properties SET geog = ST_SetSRID(ST_MakePoint(longitude, latitude),4326)::geography
  WHERE latitude IS NOT NULL AND geog IS NULL;` then re-check search;
  (2) patch the geocode/import write path (`scripts/geocode_mapbox_batch.py`,
  `db/import.py`, `scripts/sync_ppr_updates.py`) to always set `geog` alongside
  lat/lon — or make `geog` a generated column derived from lat/lon so it can never
  drift NULL again.

### Search-page "Median sale price by year" trend chart is broken
- **Status:** chart temporarily removed from the search/map page (2026-09-27).
- **Symptom:** on the main search page (`/?q=...&radius_km=...`), the bottom-right
  "Median sale price by year" overlay plotted a near-flat line spanning only the
  latest 1–2 years (e.g. 2025→2026) instead of the full sale-date range of the
  results, despite the caption reading "64 sales (full market price)".
- **Root cause (suspected):** `calculateTrendsFromProperties()` in
  `frontend/src/App.tsx` builds the yearly series client-side from the radius
  search results and produces a degenerate/truncated year range. The radius
  search itself returns sales across many years (verified: a 0.5 km search around
  "44 Mount Carmel Road" returns full-market sales from 2010–2026), so the input
  data is fine — the aggregation/axis logic is at fault.
- **What was removed (re-enable once fixed):** in `frontend/src/App.tsx`, the
  desktop map-overlay `<TrendsChart>` + "Show price trends" toggle, the inline
  `<TrendsChart>` in `.trends-pane`, and the mobile "Trends" tab. The `trends`
  state and `calculateTrendsFromProperties()` were left in place, so re-enabling
  is a localised revert.
- **Fix direction:** rebuild the yearly median/average series to cover the full
  span of returned sale dates (min→max year), or drive it from the backend
  `/trends` endpoint (already used correctly on county/area/eircode pages via
  `TrendsChart`) rather than recomputing client-side.

## Performance

### Valuation engine latency — temporal-adjustment round-trips
- **Finding (2026-09-27, `scripts/bench_valuation.py`):** in-process per-stage
  timing shows the temporal-adjustment loop dominates. Each valuation calls
  `adjust_temporal` per comparable (up to 30), and each does **two**
  `_get_price_index` DB round-trips → up to ~60 sequential remote-Supabase
  queries per valuation, even though the target index is identical for all
  comparables and the sale index only varies by (county, sale-month).
- **Fix direction:** preload `county_monthly_price_indices` for the relevant
  county once per request (or an in-memory TTL cache), then adjust in memory —
  the same memoisation already used in `scripts/value_ires_portfolio.py`.
  Secondary: cache `apartment_price_ceiling` per rounded lat/lon grid cell, and
  cache geocode results per address.
