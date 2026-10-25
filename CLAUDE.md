# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does
Geocodes Ireland's Property Price Register (PPR) residential sales from 2010 onward and serves results via a web app with radius-based search and price trend charts.

## Prerequisites
- Python 3.10+ (for geocoder/import/backend scripts)
- Node.js 18+ and npm 9+ (for frontend)
- PostgreSQL 15+ with PostGIS extension enabled (or Supabase/Postgres with PostGIS support)
- Optional but recommended for bulk geocoding: local Nominatim instance

For full-dataset runs, expect long execution times (hours), substantial disk usage for caches/exports, and network/API dependency during geocoding.

## Project structure
```
geocode.py              # Step 1: geocode source data → geocode_cache.db
source data/PPR-ALL.csv # Raw PPR data
PPR-ALL-geocoded.csv    # Step 2 output: source CSV + Latitude/Longitude columns

nominatim/
  ireland.osm.pbf       # OSM data for local Nominatim geocoding instance

db/
  schema.sql            # PostgreSQL/PostGIS table + indexes
  import.py             # Step 3: import geocoded CSV into Supabase/Postgres
  eircode_enrich.py     # Daily Eircode enrichment via Autoaddress API

scripts/
  normalize_addresses.py              # Address normalization for better geocoding
  sync_ppr_updates.py                 # Biweekly PPR sync (automated import + geocoding)
  geocode_mapbox_batch.py             # Mapbox batch geocoding with validation
  regeocode_autoaddress.py            # Autoaddress geocoding (address validation)
  export_bad_geocodes.py              # Export properties with geocoding quality issues
  county_validator.py                 # County boundary validation
  create_hybrid_geocoding.py          # Merge best coordinates from multiple sources
  enable_rls_security.py              # Enable Row-Level Security on database

backend/
  main.py               # FastAPI app (search, trends, counties endpoints)
  requirements.txt
  railway.toml          # Railway deployment config

frontend/
  src/
    App.tsx             # Root: map + sidebar layout, state orchestration
    api.ts              # Typed fetch wrappers for all backend endpoints
    types.ts            # Shared TypeScript interfaces
    components/
      SearchPanel.tsx   # Address input, radius selector, optional filters
      ResultsList.tsx   # Scrollable sidebar list of results
      TrendsChart.tsx   # Recharts median/avg price by year overlay
    pages/
      PolygonSearchPage.tsx  # Map-based search with drawing tools (polygon, rectangle, circle)
      CountyPage.tsx         # County overview pages
      AreaPage.tsx           # Area-specific pages
      [other pages...]
  vite.config.ts        # Dev proxy: /api → localhost:8000
  vercel.json           # SPA rewrite rule for Vercel

tests/
  test_production_suite.py  # Comprehensive production tests (backend, frontend, security)
```

## Environment variables
Canonical variables used across scripts/services:
- `DATABASE_URL` (required for all database operations; Supabase connection string)
- `MAPBOX_TOKEN` (required for geocoding; Mapbox API token pk.xxx format)
- `VITE_API_URL` (frontend; points to Railway backend in production)
- `AUTOADDRESS_KEY` (for Eircode enrichment; pub_xxx format)
- `SENTRY_DSN` (optional; error tracking and performance monitoring)

`backend/.env.example`:
```
DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
MAPBOX_TOKEN=pk.xxxxxxxxxxxxxxxxxxxxx
AUTOADDRESS_KEY=pub_xxxxxxxxxx
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
# NOMINATIM_URL=http://localhost:8080/search
```

`frontend/.env.example`:
```
VITE_API_URL=https://eloquent-optimism-production-350a.up.railway.app
# VITE_API_URL=http://localhost:8000  # for local development
```

Keep local secrets in `.env`/`.env.local`; never commit filled secret files.

## Pipeline order

### Initial Import (One-time)
1. `python3 geocode.py` — geocode (resumable; can take hours on full dataset)
2. `python3 geocode.py --export` — write `PPR-ALL-geocoded.csv`
3. `python3 db/import.py` — import into Postgres/Supabase (requires `DATABASE_URL`)

### Biweekly Updates - Streamlined Pipeline (2026-07-09 Enhanced)
**Recommended approach:** Use the complete pipeline script that includes all 2026-07-09 enhancements:

```bash
# Full pipeline (import → geocode → enrich)
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"

# Or run individual steps:
python3 scripts/ppr_full_pipeline.py --skip-import        # Just geocode + enrich
python3 scripts/ppr_full_pipeline.py --skip-enrichment    # Just import + geocode
python3 scripts/ppr_full_pipeline.py --dry-run            # Preview without changes
```

**Pipeline enhancements (2026-07-09):**
1. **HTML entity cleaning** - Fixes malformed addresses (Tandy&#039;s → Tandy's)
2. **Eircode-first geocoding** - Tries postal codes before addresses (more accurate)
3. **Bulk sale extraction** - Extracts base address (Units 1-76 Bridge Hall → Bridge Hall)
4. **Address normalization** - Consistent formatting for reliable searches
5. **Improved DuckDuckGo scraping** - Full-page text extraction (not just snippets)
6. **MapboxClient wrapper** - Automatic usage tracking with 50k/month limit enforcement

**Expected results:**
- Import: All new sales from CSV with address normalization
- Geocoding: ~98% success rate (was 70-80%)
- Enrichment: ~90% success rate for recent properties (was 2% with old method)
- Processing time: ~10-20 minutes per 100 properties

**Manual step-by-step (if needed):**

1. **Import new sales:**
```bash
python3 scripts/sync_ppr_updates.py --skip-geocoding
```
- Imports new sales since most recent sale_date in database
- Flags properties with `needs_geocoding = TRUE`
- Optimized: backward CSV scanning (only reads new rows)
- Logs to `logs/ppr_sync.log`

2. **Geocode new imports:**
```bash
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
```
- Uses MapboxClient with HTML cleaning, Eircode-first, bulk extraction
- Expected success: ~98% with quality 78-80/100
- Mapbox usage tracked automatically (50k/month limit enforced)
- Then re-flag wrong-town results (a Mapbox success clears `geocode_suspect`, so wrong answers would otherwise go live):
```bash
python3 scripts/flag_bad_geocodes.py --apply --add-only
```
  `--add-only` never clears existing flags. Run it after *every* geocoding sweep (batch, centroid, `--ids-file`). The full pipeline does this automatically as Step 2c.
  For a run of back-to-back 500-row `--ids-file` batches, flag every 5th batch and after the last one, not after each: every flagger run reads the whole table (~0.8 GB), and flagging each batch drained the Supabase Disk IO budget (2026-10-23). For the same reason `geocode_query_prep.py` caches its town gazetteer, locality centroids and routing-key extents in `logs/geocode_prep_cache/` for 24h, and the batch geocoder and flagger raise `work_mem` (32MB/64MB) per session so their sorts don't spill to temp files (Supabase's default is 2MB).
- **Development pins** (`scripts/development_pins.py`, table `development_pins`): hand-checked coordinates for named schemes Mapbox can't place (e.g. Parkview, Stepaside). `geocode_mapbox_batch.py --apply` places matching sales on their pin before any Mapbox call (0 requests) and never sends pinned rows to Mapbox; the flagger never flags them. Add one with:
```bash
python3 scripts/development_pins.py add --name "Parkview, Stepaside" --county Dublin \
  --match "parkview & (ash | cedar | oak ...) & (stepaside | belarmine | dublin <-> 18) & !belfry" \
  --lat 53.2596962 --lon -6.2247187          # dry run: lists matched addresses; add --apply to save
python3 scripts/development_pins.py list
```
  The match is a `to_tsquery` expression (no LIKE): include misspellings and block names, exclude neighbouring schemes that share a word. For spread-out estates of streets add `--keep-within 800`: visible geocodes already within 800m of the pin are kept, and only missing, hidden or far-off rows move (e.g. Honeypark).

3. **Enrich properties:**
```bash
python3 scripts/enrich_batch6_2026.py --batch-size 100 --rate-limit 5
```
- DuckDuckGo full-page text scraping (not snippet-based)
- Extracts bedroom counts and property types
- 5-second rate limiting to avoid blocking
- Expected success: ~90% for recent high-value properties

4. **Regenerate street landing-page data (after sync):**
```bash
export $(grep '^DATABASE_URL=' backend/.env | xargs)
python3 scripts/generate_street_data.py     # writes frontend/src/data/streets/*.json
python3 scripts/generate_sitemap.py          # refresh sitemap
python3 scripts/generate_page_data.py        # writes frontend/src/data/{areas,eircodes,counties}/*.json
python3 scripts/generate_site_stats.py       # writes frontend/src/data/site_stats.json (homepage trust strip/FAQ figures)
python3 scripts/generate_development_data.py # writes frontend/src/data/developments/*.json (/development/:slug)
git add frontend/src/data/streets frontend/public/sitemap.xml
git add frontend/src/data/areas frontend/src/data/eircodes frontend/src/data/counties frontend/src/data/site_stats.json frontend/src/data/developments frontend/src/data/page_data_generated.json
git commit -m "chore: refresh street page data" && git push origin main
```
**Page data is limited to once per calendar month.** `generate_page_data.py`, `generate_street_data.py`,
`generate_site_stats.py` and `generate_development_data.py` record their last run in `frontend/src/data/page_data_generated.json` and
skip (exit 0) if they already ran this month; pass `--force` to override (or `--force-page-data` to
`ppr_full_pipeline.py`), e.g. for a new page type with no data yet. Commit the stamp file with the data.

**Development pages** (`/development/:slug`, index `/developments`): one per entry in
`frontend/src/data/developments_registry.json`. Each entry's `pinName` names a row in
`development_pins`, whose match rule decides which sales belong (an optional `salesMatch`
tsquery narrows that further when the pin covers more than the page, e.g. Honeypark's page is its
apartment blocks only); schools and transport come from
the `amenities` table. Bulk sales (stats_excluded, or >5x the scheme median) are listed separately
and left out of the stats. To add a development: pin it first, add a registry entry (no figures in
the text; they go stale), then `python3 scripts/generate_development_data.py --force`.

This refreshes the 50 static street pages (`/street/:slug`). Data is baked into
the SSG build, so a redeploy (automatic on push) is required for changes to show.
To change *which* streets get pages, re-run `python3 scripts/analyze_top_streets.py`
then `python3 scripts/build_street_registry.py` and review the registry diff.
`generate_page_data.py` refreshes the baked `/area/:slug`, `/eircode/:code`, and `/county/:slug`
page data by calling the backend API (defaults to `http://localhost:8000`; override with
`--api-url`) — it needs the backend reachable, and it also runs automatically as Step 4 of
`scripts/ppr_full_pipeline.py` (skip with `--skip-page-data`).

**Monitoring:**
```bash
# Check Mapbox usage
python3 scripts/mapbox_usage_tracker.py --current-month

# Check enrichment progress
tail -f logs/enrichment_batch6_*.log
```

## Running the geocoder
```bash
python3 geocode.py            # resume from last saved position
python3 geocode.py --status   # show progress percentage and ETA
python3 geocode.py --export   # write PPR-ALL-geocoded.csv and exit
```

## Centroid cleanup (ongoing)
Re-geocode properties stuck at generic centroid coordinates:
```bash
# Check current centroid status
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('''
    WITH centroids AS (
        SELECT latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
    )
    SELECT COUNT(DISTINCT p.id)
    FROM properties p
    JOIN centroids c ON ABS(p.latitude - c.latitude) < 0.000001 
                    AND ABS(p.longitude - c.longitude) < 0.000001
''')
print(f'Properties at centroids: {cur.fetchone()[0]:,}')
conn.close()
"

# Test with small batch first
python3 scripts/geocode_mapbox_batch.py --centroid --limit 100

# Run cleanup (uses ~10k Mapbox requests per 10k properties)
python3 scripts/geocode_mapbox_batch.py --centroid --limit 10000 --apply

# Monitor Mapbox usage - reserve 2k/month for PPR sync
# Free tier: 100k requests/month, resets monthly
```

**Progress log:**
- 2026-05-29: Fixed 17,813 properties (92-97% success, 87/100 quality, 50%+ rooftop)
- Remaining: ~57,144 properties at centroids
- Next: Continue monthly with fresh API credits

## Running the backend locally
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL
uvicorn main:app --reload
# API at http://localhost:8000
```

## Running the frontend locally
```bash
cd frontend
npm install
cp .env.example .env.local    # set VITE_API_URL if needed
npm run dev
# App at http://localhost:5173
```

## Verification / smoke checks

### Local development
After backend starts:
- `GET /health` should return 200 (`/health` endpoint is defined in `backend/main.py`).
- Run a sample search request and confirm non-empty results for known populated areas.
- Run trends endpoint for the same area and confirm median/average series return.

After frontend starts:
- Search by a known address, confirm map marker/list render.
- Change radius and verify result count changes.
- Open trends chart and confirm yearly series updates.

### Polygon search page
Interactive map-based search at `/polygon`:
```bash
# Navigate to http://localhost:5173/polygon
```

Features to test:
- Draw polygon, rectangle, or circle on map
- Select region from dropdown (counties or Dublin postcodes)
- Verify results panel shows properties within drawn shape
- Confirm circle searches convert to radius-based queries
- Test delete tool removes shapes and clears results

**Backend endpoint:**
```bash
# Test polygon search API directly
curl -X POST http://localhost:8000/search/polygon \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [
      [53.35, -6.26],
      [53.35, -6.25],
      [53.34, -6.25],
      [53.34, -6.26],
      [53.35, -6.26]
    ],
    "limit": 100
  }'
```

### Production test suite
Comprehensive test suite for production deployment (frontend + backend):
```bash
python3 tests/test_production_suite.py
```

Tests include:
- **Security**: Database RLS, CORS, headers, sensitive paths
- **Backend Health**: /health endpoint
- **Geocoding**: Dublin, Nobber, Cork (coordinates validation)
- **Search**: Address queries, coordinate search, county filter fallback
- **Trends**: Price trends by county with median/average
- **Eircode**: Routing key queries (D02, A82, etc.)
- **Counties**: List all counties with property counts
- **Coordinate Quality**: Nobber centroid validation (fixed issue)
- **Frontend**: Bundle loading, API connectivity
- **Performance**: Response times (<100ms for most endpoints)

**Last run (2026-05-29):** 23/24 tests passed
- ✅ All production endpoints working
- ✅ Nobber coordinates correct (53.8217, -6.7479)
- ✅ Search returning 162 Nobber properties
- ✅ Performance: 82-90ms response times
- ⚠️ Database security test requires DATABASE_URL (expected for local run)

## Publishing New Content

When you create new pages, blog posts, or update existing content, follow these steps for optimal SEO:

### 1. Deploy Changes
```bash
git add .
git commit -m "Add new content: [description]"
git push origin main
# Vercel auto-deploys frontend, Railway auto-deploys backend
```

### 2. Notify Search Engines (IndexNow)
Submit new/updated URLs for instant indexing (Bing, Yandex, Naver):

```bash
# Single URL
./scripts/submit_indexnow.sh https://homeiq.ie/new-page

# Multiple URLs (edit the script to add more)
./scripts/submit_indexnow.sh https://homeiq.ie/blog/new-post
./scripts/submit_indexnow.sh https://homeiq.ie/county/dublin
```

**IndexNow Key:** `32cfaa418f6f4182aa77505f3f1815de`
- Verification file: https://homeiq.ie/32cfaa418f6f4182aa77505f3f1815de.txt
- Provides instant indexing instead of waiting for crawlers

### 3. Update Sitemap (if needed)
If you add new page types (not just individual pages), regenerate sitemap:

```bash
python3 scripts/generate_sitemap.py
git add frontend/public/sitemap.xml
git commit -m "Update sitemap with new pages"
git push origin main
```

Google Search Console will automatically detect sitemap updates within 24 hours.

### 4. Submit to Google Search Console (Manual - Optional)
For important new pages, manually request indexing:
1. Go to https://search.google.com/search-console
2. Use "URL Inspection" tool
3. Enter the new URL
4. Click "Request Indexing"

**Note:** Google doesn't support IndexNow, so manual requests or waiting for crawl are your options.

### 5. Check Analytics (After 24-48 hours)
Monitor new content performance:
- Google Analytics: Traffic, engagement, conversions
- Search Console: Impressions, clicks, position
- Bing Webmaster: Indexing status, search performance

## Deploying

**Domain & DNS**
- **Domain:** homeiq.ie
- **Registrar:** Letshost.ie (Team Blue Internet Services IE Ltd) — registration only
- **DNS hosting:** Vercel (nameservers `ns1.vercel-dns.com` / `ns2.vercel-dns.com`), *not* Letshost
- `www.homeiq.ie` redirects to the apex `homeiq.ie`, which is canonical

To modify DNS records (TXT for verification, A/CNAME for routing):
1. Vercel dashboard → team/account (not the project) → **Domains** → homeiq.ie
2. Add/edit under **DNS Records** (blank name = apex)
3. Propagation is usually a minute or two
4. Verify with `dig +short TXT homeiq.ie`

**Database (Supabase/Postgres)**
1. Create project/instance and copy connection string.
2. `DATABASE_URL=<url> python3 db/import.py` — runs `schema.sql` then bulk-imports.

**Backend (Railway)**
- Connect the `backend/` directory to a Railway service.
- Set environment variables in Railway:
  - `DATABASE_URL` (required - Supabase connection string)
  - `MAPBOX_TOKEN` (required - for geocoding API)
  - `SENTRY_DSN` (optional - error tracking)
  - `AUTOADDRESS_KEY` (optional - for Eircode enrichment)
- Deploy config is in `backend/railway.toml` (start: `uvicorn main:app --host 0.0.0.0 --port $PORT`).

**Frontend (Vercel)**
- Connect the `frontend/` directory to a Vercel project.
- Set `VITE_API_URL` to the backend URL.
- `vercel.json` handles SPA routing.
- Auto-deploys on push to main branch.

## Architecture notes

### Data Quality & Geocoding
- **Mapbox batch geocoding** (Primary): Main geocoding service. Batch API processes up to 1,000 properties per request with comprehensive validation. With Mapbox's improved Irish coverage (announced 2026), achieving 92-97% success rate with 87/100 average quality. Free tier: 100k requests/month.
- **Validation framework**: Three-layer validation for all geocoded coordinates:
  1. Ireland bounds check (51.4-55.5°N, -10.7--5.4°W) - hard reject for out-of-bounds
  2. County boundary validation - soft reject (downgrades quality score)
  3. Routing key distance validation - hard reject if Eircode >5km from routing key centroid (0.05° lat, 0.08° lon threshold)
- **Quality scoring**: Rooftop (100), Parcel (90), Point (80), Street (75), Locality (70). Minimum acceptable: 70. Rejects interpolated and approximate results.
- **Address normalization**: All addresses stored in both original and normalized forms. `address_normalized` column applies consistent formatting (title case, whitespace cleanup, abbreviation standardization, remove "No." prefix, standardize apartment/unit). **CRITICAL**: Normalization is applied automatically during import (`db/import.py`, `scripts/sync_ppr_updates.py`) and verified by test suite (`tests/test_production_suite.py::test_address_normalization`). This ensures exact address searches work reliably by eliminating punctuation/abbreviation variations.
  - **Normalization rules**: 
    1. Remove "No." prefix from house numbers
    2. Expand abbreviations: Rd→Road, Ave→Avenue, Dr→Drive, Apartment→Apt, Co.→Co. St is Street only at the end of a line or before a qualifier/county/number ("Main St Lower", "Thomas St Dublin 8"); otherwise Saint ("12 St Mobhi Road"), since a number never comes straight before a street type
    3. Title case with exceptions (Dublin, Cork, Co., etc. stay capitalized)
    4. Clean punctuation: normalize commas/spaces, remove leading/trailing
    5. Normalize whitespace (single spaces only)
    6. Fold Irish fadas (Slí→Sli, Cnocán→Cnocan) so input typed with or without them matches. The raw `address` column keeps the fadas for display.
  - **One normalizer**: `backend/address_normalize.py` (in `backend/` because Railway deploys only that directory). Import, sync, `normalize_addresses.py`, `main.py::normalize_for_search` and the tests all import it; never copy it. After changing a rule, run `python3 scripts/normalize_addresses.py --recheck` (dry run; `--apply` to write) and deploy the backend straight after, or search input and stored rows disagree. Last run 2026-10-25: 83,765 rows (St→Saint, Co.→Co).
  - **Source encoding**: `PPR-ALL.csv` is Windows-1252, not UTF-8 ('€' is byte 0x80, Í is 0xCD). `sync_ppr_updates.py` detects the encoding (`detect_csv_encoding`) and `geocode.py` reads it as cp1252. Never read it as UTF-8 with `errors="replace"`, which turns every fada into U+FFFD (1,701 rows were repaired from this on 2026-10-14).
  - **Query pattern**: For exact address matching, ALWAYS query `address_normalized` column directly (NOT LIKE/REGEXP). Example:
    ```python
    # ✅ CORRECT: Use normalized column directly
    WHERE address_normalized LIKE $1 || '%'  # For prefix matching (e.g., "28 Slane Road" → "28 Slane Road, Crumlin, Dublin 12")
    WHERE address_normalized = $1            # For exact match
    
    # ❌ WRONG: LIKE queries on raw address are unreliable
    WHERE UPPER(address) LIKE UPPER($1) || '%'  # Fails on punctuation/abbreviation differences
    WHERE REGEXP_REPLACE(...) LIKE ...          # Expensive, fragile, creates double-spaces
    ```
  - **Maintenance**: Test suite automatically normalizes up to 10k missing addresses per run. For bulk updates: `python3 scripts/normalize_addresses.py` (processes 1k/batch, resumable).
- **Routing key indexing**: Generated column extracts first 3 characters of Eircode (e.g., D02, H91). Materialized view `routing_key_stats` provides centroids and statistics for 301 routing keys. Enables validation and fallback geocoding.
- **Geocoding queue**: Properties imported without coordinates flagged with `needs_geocoding = TRUE`. Priority order: price (>€500k first), then recency. View: `properties_needing_geocoding` for processing.
- **Centroid cleanup** (In progress): ~70k properties stuck at generic centroid coordinates (100+ addresses at same point). Mapbox re-geocoding achieving 92-97% success with 50%+ rooftop precision. Progress: 17,813 fixed (2026-05-29), 57,144 remaining. Continue monthly with fresh API credits.
- **Eircode enrichment**: Daily cron job processes properties via Autoaddress API (address validation only, not geocoding). Autoaddress provides address formatting and Eircode data but not coordinates.

### Search & Performance
- **Radius search**: `ST_DWithin(geom::geography, ...)` on GIST-indexed PostGIS geometry column. Results ordered by `ST_Distance` ascending. Auto-expands radius (2x, 3x, 5x, 10x up to 20km) if fewer than 5 results found.
- **Polygon search** (New): `ST_Within(geom::geometry, polygon)` for map-based area selection. Supports drawing tools (polygon, rectangle, circle) at `/polygon`. Accepts custom polygon coordinates via `POST /search/polygon`. Up to 1,000 properties per query.
- **Exact address search** (`/search/exact`): Matches against `address_normalized` column for reliable results. Handles user input variations (ROAD vs RD, punctuation differences) by normalizing search input with same logic as database. Supports prefix matching to handle missing area suffixes (e.g., "28 Slane Road" matches "28 Slane Road, Crumlin, Dublin 12").
- **Geocoding at search time** (`resolve_location`): coordinates → Eircode/routing key (DB) → exact address (`address_normalized ^@`, as `/search/exact`) → place name (`places` table) → token DB lookup → fuzzy DB. No external geocoder: no Nominatim (it ranked same-named roads above towns: "Swords, Dublin" → Swords Road, Whitehall) and no Mapbox (since 2026-10-18). Queries that still fail are logged to `search_failures` with reason `no_location`; check them with `python3 scripts/failures_report.py [--days 7]` to see whether a geocoder is worth bringing back.
- **Query logs**: successes go to `search_log` (`/search`) and `valuation_requests`; failures to `search_failures` (`no_location`, `no_results` from `/search` and `/search/exact`, `error` for 5xx on `/search*` and `/geocode`) and `valuation_failures` (every 4xx/5xx from `/valuation/estimate`), see `db/migrations/006_failure_logs.sql`. `geocode_misses` is no longer written (its rows were copied into `search_failures`). A pg_cron job (`query-log-retention`, Sundays 04:00 UTC) deletes rows older than 12 months from all four; `search_log` holds IP addresses, so don't extend that without a reason. Per-endpoint request counts go to `api_usage_daily` (migration 008, `backend/usage.py`): kept in memory and flushed every 10 minutes as one upsert per (day, endpoint, status). Only the Railway deployment logs anything (`RAILWAY_ENVIRONMENT` set), so local backends and the pre-commit tests stay out of every query log; `tests/test_production_suite.py` sends `X-HomeIQ-Test: 1` to keep its own requests out too, and its log-analysis section reports usage, popular features and failing searches.
- **Places table**: town/suburb/locality centres built from our own geocoded sales by `python3 scripts/build_places.py --apply` (dry run without `--apply`). A name's centre is the median of sales within 5km of its densest cell, kept if ≥50% of its sales are there. Without a county in the query, Dublin wins, else only names used in a single county ("Tuam" yes, "Main Street" no → Mapbox). Re-run yearly or after big geocoding cleanups; shared logic lives in `backend/places.py`. Places with too few sales to cluster (townlands, "Achill" for Achill Sound) go in `MANUAL_PLACES` in `build_places.py` with user-supplied coordinates (the rebuild truncates the table, so a hand-inserted row alone is lost). When the first part of a query is unknown, search falls back to its later parts as places, after the street-level token lookup ("Drumlaney, Redhills" → Redhills).
- **Trends query**: Uses `PERCENTILE_CONT(0.5)` for median price, filtered to `not_full_market_price = FALSE`.
- **Caching**: In-memory TTL cache for counties (1h), trends (1h), Eircodes (1h), geocode results (24h), search results (5min).

### Query Best Practices
**Disk IO budget (Supabase Micro compute):** the DB has 224MB of shared_buffers against a ~500MB `properties` table, so every full-table read hits disk, and the Disk IO budget has run out more than once. Don't run one-off analysis on prod (exploratory GROUP BYs, percentiles over all rows, temp copies): answer from cached/pre-computed data (`routing_key_stats`, `logs/geocode_prep_cache/`, the generated page data) or a single cheap aggregate with `statement_timeout`. New indexes cost buffer space too: check `pg_stat_user_indexes` before adding one, and drop ones with no scans (unused ones were dropped 2026-10-25, `db/migrations/005_drop_unused_indexes.sql`).

**DO:**
- ✅ Use indexed columns directly: `address_normalized`, `geog`, `routing_key`, `sale_date`
- ✅ Use PostGIS functions for spatial queries: `ST_DWithin`, `ST_Within`, `ST_Distance`
- ✅ Use exact equality or full-text search for address matching: `WHERE address_normalized = $1` or use `to_tsvector`/`to_tsquery`
- ✅ Cache expensive aggregations (trends, county stats) with TTL
- ✅ Normalize user input with same logic as database before querying

**DON'T:**
- ❌ **NEVER use LIKE queries** - they don't use indexes efficiently and create maintenance issues
- ❌ Use LIKE queries on raw `address` column (punctuation/abbreviation mismatches)
- ❌ Use REGEXP_REPLACE in WHERE clauses (expensive, creates whitespace issues)
- ❌ Use UPPER/LOWER for matching when normalized column exists
- ❌ Use `SELECT *` on large result sets (specify needed columns)
- ❌ Query without indexes (always use EXPLAIN to verify index usage)

**Address Matching Strategy:**
- For exact address lookups: Use `WHERE address_normalized = $1` after normalizing user input
- For fuzzy/partial matching: Use PostgreSQL full-text search with `to_tsvector(address_normalized) @@ to_tsquery($1)`
- For geographic search: Use `ST_DWithin` with coordinates from geocoding API

### Security

**DESIGN RULE: No Direct Database Access**
- Anonymous users MUST NEVER have direct access to the Supabase database
- All data access flows through the authenticated Railway backend API
- Architecture: `Frontend → Railway API (authenticated) → Supabase`
- The `anon` role should have ZERO permissions on all tables
- This prevents direct PostgREST API access and ensures all queries go through our controlled backend

**Row-Level Security (RLS) - CONFIGURED 2026-07-07**
- **Status**: ENABLED on properties table
- **Policy**: `backend_full_access_properties` (FOR ALL TO authenticated)
- **Authenticated role**: Full CRUD access via DATABASE_URL connection
- **Anonymous role**: ALL privileges REVOKED (by design)
- **Direct PostgREST access**: BLOCKED

**Verifying RLS Configuration**
If you receive Supabase security alerts about RLS, verify the configuration is correct:

```bash
# Quick verification - should show "ENABLED" and anon access BLOCKED
python3 scripts/enable_rls_security.py

# Manual SQL verification (via Supabase dashboard or psql)
# 1. Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'properties';
-- Result: rowsecurity = true

# 2. Check policy exists
SELECT policyname, cmd, roles::text[] 
FROM pg_policies 
WHERE tablename = 'properties';
-- Result: backend_full_access_properties, ALL, {authenticated}

# 3. Verify anonymous access is blocked
SELECT has_table_privilege('anon', 'properties', 'SELECT');
-- Result: false

# 4. Verify backend can access (via DATABASE_URL connection)
SELECT COUNT(*) FROM properties;
-- Result: ~785,000 rows (should succeed)
```

**Re-enabling RLS After Schema Changes**
If you drop/recreate the properties table, RLS and policies are lost. Re-run:
```bash
export $(grep '^DATABASE_URL=' backend/.env | xargs)
python3 scripts/enable_rls_security.py
```

**What This Prevents**
- ❌ Direct access via Supabase PostgREST API (https://[project].supabase.co/rest/v1/properties)
- ❌ Direct access via Supabase client libraries without authentication
- ❌ Unauthorized reads, writes, updates, or deletes
- ✅ All access controlled through Railway backend with rate limiting and validation

**CORS**
- Restricted to homeiq.ie and www.homeiq.ie in production
- localhost:5173 allowed in development
- Prevents unauthorized frontend origins from calling API

**Admin endpoints - DISABLED (2026-10-22)**
- `GET /geocoding-queue/next`, `POST /geocoding-queue/update`, `POST /geocoding-queue/skip` and `GET /email-alerts/active` all return 404, even with a valid `ADMIN_API_TOKEN`
- Why: nothing uses them, and Railway's 21 Oct 2026 security incident may have leaked every Railway env var, including `ADMIN_API_TOKEN`. They could move geocodes and list subscriber emails
- Switched off by `ADMIN_ENDPOINTS_ENABLED = False` in `backend/main.py` (checked first in `verify_admin_token`). The `/manual-geocode` page calls the queue endpoints and won't work while they're off (it never sent a token anyway)
- To re-enable: set the flag to `True`, put a fresh `ADMIN_API_TOKEN` (`openssl rand -hex 32`) in Railway, and send it as `Authorization: Bearer <token>`
- `/cron/*` endpoints are separate (`CRON_SECRET`) and not affected

**Automated Security Monitoring**
- Daily GitHub Actions check removed 2026-10-21 (it failed on every run connecting to the DB); run the script by hand instead
- Detects RLS configuration drift; `--fix` repairs it
- Script: `scripts/security_monitor.py` (run manually anytime)
- Setup: See [AUTOMATED_SECURITY_SETUP.md](AUTOMATED_SECURITY_SETUP.md)
- **Expected result**: No Supabase security alert emails

**Manual verification** (if needed):
```bash
# Quick check
python3 scripts/security_monitor.py

# Check and auto-fix
python3 scripts/security_monitor.py --fix
```

**Application Monitoring**
- Sentry integration for error tracking and performance monitoring
- Search analytics tracked for observability

### Infrastructure
- **Database**: Supabase (PostgreSQL + PostGIS). 784,464 properties, ~614,200 with coordinates (78.3% coverage as of 2026-05-29).
  - Best coverage: 2022-2024 (89-91% geocoded)
  - Recent: 2025-2026 (77-81% geocoded)
  - Eircode coverage: 29.7% overall (74-79% for 2022+ sales)
  - Spatial indexes: GIST index on `geog` geography column for fast radius/polygon queries
- **Backend**: FastAPI on Railway (https://eloquent-optimism-production-350a.up.railway.app).
  - Endpoints: `/search` (radius), `/search/polygon` (spatial), `/trends`, `/counties`, `/eircode`, `/geocode`
- **Frontend**: React + TypeScript on Vercel (https://homeiq.ie).
  - Pages: Home (text search), `/polygon` (map search), `/county/:slug`, `/area/:slug`, `/eircode/:code`
  - Map library: Leaflet 1.9.4 with Leaflet Draw for drawing tools
- **Geocoding API**: Mapbox with **strict 50k/month limit** (safety margin from 100k free tier).
  - **Usage tracking**: All Mapbox requests tracked in `mapbox_usage` table via `MapboxClient` wrapper
  - **Quota enforcement**: Pre-flight checks prevent exceeding monthly limit
  - **Monitoring**: `python3 scripts/mapbox_usage_tracker.py --current-month`
  - **Monthly allocation**: 2k for PPR sync, 48k for batch operations (the search API no longer calls Mapbox)
  - See [MAPBOX_USAGE_TRACKING.md](docs/MAPBOX_USAGE_TRACKING.md) for complete documentation

## Troubleshooting

### Database & Security
- **`DATABASE_URL` errors**: verify `.env` value format and DB reachability; confirm PostGIS extension is enabled.
- **Supabase security alerts about RLS**: 
  - Check CLAUDE.md Security section for verification steps
  - Run `python3 scripts/enable_rls_security.py` to re-enable RLS
  - Verify with SQL queries in Security section
  - Alert should clear within 24 hours after fixing
  - **Expected configuration**: RLS ENABLED, anon role has NO permissions, authenticated role has full access
- **Backend can’t access database after enabling RLS**: 
  - Verify DATABASE_URL uses the correct postgres/service role credentials (not anon key)
  - Check Railway environment variables match backend/.env
  - Test with: `curl https://eloquent-optimism-production-350a.up.railway.app/health`

### Search & Geocoding
- **Few/no radius results**: confirm imported rows have non-NULL geometry and that search coordinates are valid.
- **Geocoder seems stalled**: use `python3 geocode.py --status`; verify local Nominatim is reachable at `http://localhost:8080/search` and check `geocode.py` logs for retry/backoff errors.
- **HTTP 429 / throttling**: reduce request rate, retry later, or switch to local/self-hosted Nominatim.
- **Search shows wrong county results**: County filter defaults to "Dublin" for usability (most populous region). Auto-detection corrects mismatches when search query contains a county name (e.g., searching "Galway City" with "Dublin" filter will auto-switch to Galway). County page links include both `q` and `county` parameters to ensure proper filtering.

### Frontend & API
- **Frontend can’t reach API**: verify `VITE_API_URL`, CORS settings, and backend URL/health.
- **"Failed to fetch" errors**: 
  - Check VITE_API_URL is set correctly in Vercel environment variables
  - Verify Railway backend is running and healthy
  - Check browser console for CORS errors

## Local Nominatim instance
`nominatim/ireland.osm.pbf` contains OSM data for local geocoding. To start a local Nominatim service using Docker:

```bash
docker run -it --rm \
  -e PBF_PATH=/nominatim/data/ireland.osm.pbf \
  -e REPLICATION_URL="" \
  -v "$(pwd)/nominatim:/nominatim/data" \
  -p 8080:8080 \
  mediagis/nominatim:4.4
```

First run imports the PBF and can take 10–30 minutes. Subsequent runs reuse the data volume if you mount a persistent named volume instead of the local directory.

The bulk geocoder (`geocode.py`) is configured to call local Nominatim at `http://localhost:8080/search`; if that service is down, geocoding requests fail and retry with backoff (Photon fallback is only used when Nominatim returns no result for non-Eircode queries). The backend API doesn't use Nominatim (see `places` table above); this local instance is only for the legacy bulk geocoder.

## SEO Strategy & Traffic Growth

### Current SEO Status
**Domain:** homeiq.ie (production on Vercel)
**Current State:** Low traffic, recently launched
**Target Audience:** Irish property buyers, sellers, investors, estate agents, mortgage advisors

### Implemented SEO Foundation
- ✅ **Meta tags**: All pages use `usePageMeta()` hook for dynamic titles/descriptions
- ✅ **Structured data**: WebApplication and Dataset schema in `index.html`
- ✅ **Open Graph**: Facebook/LinkedIn sharing optimization
- ✅ **Twitter Cards**: Twitter sharing optimization
- ✅ **Sitemap**: Need to generate (see recommendations below)
- ✅ **robots.txt**: Need to create (see recommendations below)
- ✅ **Performance**: Fast loading (Railway + Vercel), mobile-responsive
- ✅ **Security**: HTTPS, CORS configured, RLS enabled

### High-Priority Traffic Growth Recommendations

#### 1. Technical SEO (Quick Wins - Implement First)
**Generate XML sitemap:**
```bash
# Create frontend/public/sitemap.xml with all key pages
# Include: counties (26), major areas (~50), Dublin postcodes (22), main pages
```

**Create robots.txt:**
```
User-agent: *
Allow: /
Sitemap: https://homeiq.ie/sitemap.xml

# Block internal tools
Disallow: /manual-geocode
```

**Submit to search engines:**
- Google Search Console: https://search.google.com/search-console
- Bing Webmaster Tools: https://www.bing.com/webmasters
- Submit sitemap URLs directly
- Monitor indexing status weekly

**Add canonical URLs:** Prevent duplicate content issues
```tsx
// In usePageMeta hook
<link rel="canonical" href={`https://homeiq.ie${window.location.pathname}`} />
```

**Implement breadcrumbs with schema:**
```tsx
// Add to County/Area pages for better crawlability
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [...]
}
</script>
```

#### 2. Content SEO (High Impact)
**Add dedicated landing pages for high-volume searches:**
- `/property-price-register` - Target "property price register ireland"
- `/house-prices-ireland` - Target "house prices ireland"
- `/dublin-house-prices` - Target "dublin house prices"
- `/property-price-trends` - Target "irish property price trends"
- `/mortgage-calculator-ireland` (already exists at `/mortgage`)
- `/eircode-property-search` - Target "eircode property search"

**County pages need more content:**
Current county pages are thin. Add to each:
- Market overview paragraph (200-300 words)
- Key statistics (total sales, median price, YoY change)
- Popular areas within county (link to area pages)
- Recent trends commentary
- FAQs section (3-5 Q&A pairs)

**Blog/Resources section:** `/blog` or `/guides`
Content ideas:
- "How to Use the Property Price Register" (evergreen, high-volume)
- "Understanding Eircode for Property Search"
- "Dublin Property Prices by Postcode - 2025 Guide"
- "Cork vs Galway vs Limerick: Property Price Comparison"
- "First Time Buyer's Guide to Irish Property Prices"
- Monthly market reports: "Irish Property Prices - [Month] 2025"
- County deep-dives: "Complete Guide to [County] Property Prices"

**Internal linking strategy:**
- Link county pages to area pages
- Link area pages to nearby areas
- Add "You might also like" sections
- Create hub pages: "Leinster Property Prices" linking to all Leinster counties

#### 3. Link Building & Authority (Medium-Term)
**Get listed in directories:**
- PropertyPrice.ie mentions
- MyHome.ie (partner/data provider discussions?)
- Daft.ie (competitor but may link to public data)
- Irish property forums (boards.ie, Reddit r/ireland, r/irishpersonalfinance)
- Irish tech/startup directories

**Media outreach:**
- Press release: "New Free Tool for Irish Property Price Search"
- Pitch to TheJournal.ie, BreakingNews.ie, Irish Times property section
- Offer data insights: "Analysis: Where Irish Property Prices Rose Most in 2025"
- Quote property price statistics with "Source: HomeIQ.ie analysis of PPR data"

**Data journalism opportunities:**
- Publish monthly/quarterly market reports
- Create shareable infographics (price heat maps, trend charts)
- Offer API access for journalists/researchers (consideration for future)

**Community engagement:**
- Answer property price questions on boards.ie with links to relevant searches
- Create helpful Reddit posts in r/irishpersonalfinance with tool demonstrations
- Engage on Twitter/X with Irish property hashtags

#### 4. Local SEO
**Google Business Profile:**
- If applicable (depends on business structure)
- Claim and optimize listing

**Local schema markup:**
Already have country-level, expand to county-level:
```json
{
  "@type": "Place",
  "address": {
    "@type": "PostalAddress",
    "addressRegion": "County Dublin",
    "addressCountry": "IE"
  }
}
```

#### 5. User Experience & Engagement (Affects SEO Indirectly)
**Add "Share" functionality:**
- Share search results via social media
- Share specific property listings
- Share price trend charts

**Email newsletter:**
- "Dublin Property Price Digest - Weekly"
- Builds return visitors (positive SEO signal)
- Already have email alert modal - extend it

**Property price alerts:**
- Already implemented in EmailAlertModal.tsx
- Promote this feature prominently (unique value proposition)

**Add more interactive features:**
- Price prediction tool
- Stamp duty calculator (link to revenue.ie)
- Affordability calculator (income vs price)
- Compare areas side-by-side

#### 6. Performance & Mobile SEO
**Already strong, but monitor:**
- Core Web Vitals (use Google PageSpeed Insights)
- Mobile usability in Search Console
- Map loading speed (lazy load if needed)

#### 7. Keyword Optimization
**Primary keywords to target:**
- "property price register ireland" (high volume)
- "house prices ireland" (very high volume)
- "dublin house prices" (high volume)
- "property prices [county name]" (medium volume × 26 counties)
- "eircode property search" (medium volume)
- "[area name] property prices" (long-tail × hundreds of areas)
- "irish property price trends" (medium volume)
- "property price register search" (medium volume)

**Long-tail opportunities:**
- "property prices in [specific area]"
- "average house price [town name]"
- "[eircode] property prices"
- "property sold prices [address]"
- "house price trends [county]"

#### 8. Analytics & Monitoring
**Set up if not already:**
- Google Analytics 4
- Google Search Console
- Track: organic search traffic, top landing pages, bounce rate, search queries

**Monitor weekly:**
- Indexing status (Search Console)
- Top performing pages
- Search queries driving traffic
- Click-through rates from search results

**A/B test meta descriptions:**
- Improve CTR from search results
- Test different value propositions

### Implementation Priority
**Week 1 (Immediate):**
1. Generate sitemap.xml
2. Create robots.txt
3. Submit to Google Search Console & Bing Webmaster
4. Add canonical URLs to usePageMeta hook
5. Fix any meta tag issues found

**Week 2-3 (High Impact):**
1. Expand county pages with more content
2. Create 3-5 landing pages for high-volume keywords
3. Add breadcrumb navigation
4. Improve internal linking

**Month 2 (Content & Authority):**
1. Launch blog section with 5-10 initial articles
2. Publish first market report
3. Start media outreach
4. Begin community engagement

**Ongoing:**
- Publish 2-4 blog posts per month
- Monitor analytics weekly
- Build backlinks through outreach
- Update market reports monthly

### Measuring Success
**3 months:** 
- 500-1000 organic visitors/month
- 50+ pages indexed in Google
- 5-10 quality backlinks

**6 months:**
- 2,000-5,000 organic visitors/month
- Top 10 rankings for 3-5 primary keywords
- 20+ quality backlinks

**12 months:**
- 10,000+ organic visitors/month
- Top 3 rankings for primary keywords
- Established as authoritative Irish property data source

### Content Ideas Bank
Keep a running list of content to create:
- County comparison tools
- Property price FAQs per county
- Historical price analysis pieces
- First-time buyer resources
- Investment property guides
- Market trend commentary

## Working efficiently with Claude Code

### Avoiding "message too long" API errors
This project has some large files and datasets that can trigger Claude's message length limits. Follow these practices:

**When reading files:**
- Use `Read` with `limit` and `offset` parameters for large files (>500 lines)
- Read selectively: identify the specific functions/sections you need before reading
- For very large files (PolygonSearchPage.tsx is 20KB), read in chunks or grep for specific patterns first

**When checking git status:**
- Use `git diff --stat` for overview instead of full diffs
- Use `git diff <file>` for specific files only when needed
- Avoid `git diff` without arguments if many files are changed

**When searching code:**
- Use `grep -l` (files only) before `grep -n` (with line numbers) to narrow scope
- Prefer targeted searches over reading multiple files speculatively
- Use `find` with `-name` patterns to locate files before reading them

**When working with data:**
- Never cat/head large CSV files (`PPR-ALL.csv` is 784k rows)
- Use `wc -l` for row counts, `head -5` for quick peeks
- Query the database directly for data insights instead of exporting

**General practices:**
- Break work into smaller focused tasks
- Complete and commit one feature before starting the next
- If conversation gets long, summarize progress and start fresh

**Frontend file sizes to watch:**
- `PolygonSearchPage.tsx` (20KB) - read specific sections or search for patterns first
- `App.tsx`, `api.ts`, `types.ts` - moderate size, usually fine to read fully
- Component files in `components/` - small, safe to read

## Data freshness and licensing
- PPR source snapshots can change over time; record snapshot date/version when regenerating outputs.
- OSM/Nominatim data and usage must respect ODbL and Nominatim usage policy (especially for public endpoints).
- Treat row counts in docs as snapshot-specific, not permanent constants.
