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
  create_hybrid_geocoding.py          # Merge best coordinates from multiple sources
  enable_rls_security.py              # Enable Row-Level Security on database
  analyze_salesforce_geocoding_quality.py  # Quality analysis tools
  county_validator.py                 # County boundary validation

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
  vite.config.ts        # Dev proxy: /api → localhost:8000
  vercel.json           # SPA rewrite rule for Vercel

tests/
  test_production_suite.py  # Comprehensive production tests (backend, frontend, security)
```

## Environment variables
Canonical variables used across scripts/services:
- `DATABASE_URL` (required for all database operations; Supabase connection string)
- `VITE_API_URL` (frontend; points to Railway backend in production)
- `NOMINATIM_URL` (backend geocoding endpoint; defaults to public endpoint)
- `AUTOADDRESS_KEY` (for Eircode enrichment; pub_xxx format)
- `SENTRY_DSN` (optional; error tracking and performance monitoring)

`backend/.env.example`:
```
DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
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
1. `python3 geocode.py` — geocode (resumable; can take hours on full dataset)
2. `python3 geocode.py --export` — write `PPR-ALL-geocoded.csv`
3. `python3 db/import.py` — import into Postgres/Supabase (requires `DATABASE_URL`)

## Running the geocoder
```bash
python3 geocode.py            # resume from last saved position
python3 geocode.py --status   # show progress percentage and ETA
python3 geocode.py --export   # write PPR-ALL-geocoded.csv and exit
```

## Running the backend locally
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL (and optional NOMINATIM_URL)
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
After backend starts:
- `GET /health` should return 200 (`/health` endpoint is defined in `backend/main.py`).
- Run a sample search request and confirm non-empty results for known populated areas.
- Run trends endpoint for the same area and confirm median/average series return.

After frontend starts:
- Search by a known address, confirm map marker/list render.
- Change radius and verify result count changes.
- Open trends chart and confirm yearly series updates.

## Deploying
**Database (Supabase/Postgres)**
1. Create project/instance and copy connection string.
2. `DATABASE_URL=<url> python3 db/import.py` — runs `schema.sql` then bulk-imports.

**Backend (Railway)**
- Connect the `backend/` directory to a Railway service.
- Set `DATABASE_URL` (and optionally `NOMINATIM_URL`) in Railway.
- Deploy config is in `backend/railway.toml` (start: `uvicorn main:app --host 0.0.0.0 --port $PORT`).

**Frontend (Vercel)**
- Connect the `frontend/` directory to a Vercel project.
- Set `VITE_API_URL` to the backend URL.
- `vercel.json` handles SPA routing.

## Architecture notes

### Data Quality & Geocoding
- **Hybrid geocoding strategy**: Coordinates sourced from multiple providers (Nominatim, Mapbox, Salesforce Maps) and scored for quality (0-100). Best source chosen per property; low-quality coordinates rejected entirely (set to NULL). Philosophy: "Better to have no data than bad data."
- **Address normalization**: All addresses stored in both original and normalized forms. `address_normalized` column applies consistent formatting (title case, whitespace cleanup, abbreviation standardization) for better API matching. Improves geocoding success rate by ~15-20% and Eircode enrichment from 24% to 40%+.
- **Quality scoring criteria**: Out-of-bounds check (Ireland bbox), county boundary validation, centroid detection (>50 properties at same coordinate), coordinate precision analysis.
- **Eircode enrichment**: Daily cron job processes 500 properties via Autoaddress API. Prioritizes urban addresses with house numbers (highest success rate). Enrichment enables Eircode-based search and improves address matching.
- **County validation**: Approximate bounding boxes for all 26 Irish counties validate that coordinates fall within expected geographic boundaries. Flags mismatches that indicate geocoding errors.

### Search & Performance
- **Radius search**: `ST_DWithin(geom::geography, ...)` on GIST-indexed PostGIS geometry column. Results ordered by `ST_Distance` ascending. Auto-expands radius (2x, 3x, 5x, 10x up to 20km) if fewer than 5 results found.
- **Geocoding at search time**: Backend calls Nominatim (`NOMINATIM_URL`) to resolve user queries to (lat, lon). Supports addresses, Eircodes, and coordinate pairs.
- **Trends query**: Uses `PERCENTILE_CONT(0.5)` for median price, filtered to `not_full_market_price = FALSE`.
- **Caching**: In-memory TTL cache for counties (1h), trends (1h), Eircodes (1h), geocode results (24h), search results (5min).

### Security
- **Row-Level Security (RLS)**: Enabled on properties table. Public has SELECT-only access; writes blocked by default. Protects against unauthorized data modification while keeping PPR data publicly readable.
- **CORS**: Restricted to homeiq.ie and www.homeiq.ie in production. localhost:5173 allowed in development.
- **Monitoring**: Sentry integration for error tracking and performance monitoring. Search analytics tracked for observability.

### Infrastructure
- **Database**: Supabase (PostgreSQL + PostGIS). 781,501 properties, ~620,000 with coordinates after hybrid quality update.
- **Backend**: FastAPI on Railway (https://eloquent-optimism-production-350a.up.railway.app).
- **Frontend**: React + TypeScript on Vercel (https://homeiq.ie).
- **Rate limiting (geocoder)**: Local Nominatim configured for high throughput; external fallback slower to respect public service limits.

## Troubleshooting
- **`DATABASE_URL` errors**: verify `.env` value format and DB reachability; confirm PostGIS extension is enabled.
- **Few/no radius results**: confirm imported rows have non-NULL geometry and that search coordinates are valid.
- **Geocoder seems stalled**: use `python3 geocode.py --status`; verify local Nominatim is reachable at `http://localhost:8080/search` and check `geocode.py` logs for retry/backoff errors.
- **HTTP 429 / throttling**: reduce request rate, retry later, or switch to local/self-hosted Nominatim.
- **Frontend can’t reach API**: verify `VITE_API_URL`, CORS settings, and backend URL/health.

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

The bulk geocoder (`geocode.py`) is configured to call local Nominatim at `http://localhost:8080/search`; if that service is down, geocoding requests fail and retry with backoff (Photon fallback is only used when Nominatim returns no result for non-Eircode queries). The backend API separately defaults to the public Nominatim endpoint unless `NOMINATIM_URL` is set.

## Data freshness and licensing
- PPR source snapshots can change over time; record snapshot date/version when regenerating outputs.
- OSM/Nominatim data and usage must respect ODbL and Nominatim usage policy (especially for public endpoints).
- Treat row counts in docs as snapshot-specific, not permanent constants.
