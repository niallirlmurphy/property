# HomeIQ.ie — Technical Architecture

## Overview

HomeIQ.ie is a property price intelligence platform for the Irish market. It ingests the
national Property Price Register (PPR), geocodes every sale record, stores the results in
a spatially-enabled database, and serves them through a search and analytics web application.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                            │
│                     (runs locally / ad-hoc)                     │
│                                                                 │
│  source data/PPR-ALL.csv                                        │
│         │                                                       │
│         ▼                                                       │
│   ┌──────────────┐   geocode_cache.db (SQLite)                  │
│   │  geocode.py  │ ◄────────────────────────── resumable        │
│   └──────────────┘                                              │
│    Nominatim (local)  ──► primary geocoder                      │
│    Photon (komoot)    ──► fallback for non-Eircode queries       │
│    Mapbox API         ──► fix scripts (routing key corrections)  │
│         │                                                       │
│         ▼                                                       │
│   PPR-ALL-geocoded.csv  (781,501 rows + lat/lon)                │
│         │                                                       │
│         ▼                                                       │
│   ┌──────────────┐                                              │
│   │ db/import.py │──► Supabase (PostgreSQL + PostGIS)           │
│   └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION SERVICES                         │
│                                                                 │
│   Browser                                                       │
│      │                                                          │
│      │  HTTPS                                                   │
│      ▼                                                          │
│   ┌──────────────────────────────┐                             │
│   │   Vercel (Frontend)          │                             │
│   │   React + TypeScript + Vite  │                             │
│   │   homeiq.ie                  │                             │
│   └──────────────────────────────┘                             │
│      │                                                          │
│      │  HTTPS / REST (CORS)                                     │
│      ▼                                                          │
│   ┌──────────────────────────────┐                             │
│   │   Railway (Backend)          │                             │
│   │   FastAPI + asyncpg          │                             │
│   │   Python 3.11                │                             │
│   └──────────────────────────────┘                             │
│      │                          │                              │
│      │  asyncpg (PostgreSQL      │  httpx                      │
│      │  wire protocol)           │  (geocoding)                │
│      ▼                          ▼                              │
│   ┌──────────────────┐   ┌─────────────────┐                  │
│   │ Supabase         │   │  Mapbox API     │                  │
│   │ PostgreSQL 15    │   │  (geocoding)    │                  │
│   │ + PostGIS        │   └─────────────────┘                  │
│   │                  │                                         │
│   │  properties      │                                         │
│   │  submissions     │                                         │
│   └──────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Pipeline

### Source Data
- **Property Price Register (PPR)**: `source data/PPR-ALL.csv`
  - ~781,501 residential sales in Ireland from 2010 to present
  - Fields: date, address, county, eircode, price, property type, VAT flag, market price flag

### Step 1 — Geocoding (`geocode.py`)
Adds latitude/longitude to every PPR row. Resumable — progress saved to `geocode_cache.db` (SQLite).

**Resolution strategy per row:**
```
Has Eircode?
  ├─ Yes → Query Nominatim with routing key (e.g. "D14, Ireland")
  └─ No  → Query Nominatim with full address + county
               │
               └─ No result → Photon (komoot) fuzzy fallback
                                  │
                                  └─ No result → cached as NOT_FOUND sentinel
```

- Local Nominatim instance (Docker) used for bulk throughput — no rate limits
- Photon used as fallback for fuzzy/non-standard addresses
- NOT_FOUND rows are cached so they are never retried
- Final coverage: ~620,849 geocoded (79%), ~161k ungeocodable (rural/non-standard)

### Fix Scripts (post-geocoding corrections)
Run once after initial geocoding to correct known classes of error:

| Script | Purpose |
|--------|---------|
| `geocode_fix_eircode.py` | Re-geocodes full Eircodes for better precision |
| `geocode_fix_ambiguous.py` | Resolves ambiguous town names |
| `geocode_fix_county.py` | Fixes routing key / county mismatches |
| `geocode_fix_routing.py` | Corrects out-of-bounds (NI) coordinates |
| `geocode_fix_bt.py` | Fixes BT (Northern Ireland) eircode misclassifications |
| `geocode_retry.py` | Retries previously-failed addresses |
| `geocode_mapbox.py` | Mapbox-based re-geocoding for hard cases |

### Step 2 — Export
```bash
python3 geocode.py --export   # writes PPR-ALL-geocoded.csv
```

### Step 3 — Database Import (`db/import.py`)
Truncates and re-imports from `PPR-ALL-geocoded.csv` into Supabase.
- Populates `geog` (geography column) directly at insert time
- Runs `db/schema.sql` to ensure tables/indexes exist

---

## Database Schema

**Host:** Supabase (PostgreSQL 15 + PostGIS), `aws-0-eu-west-1`

### `properties` table (781,501 rows, 476 MB total)

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGSERIAL | Primary key |
| `sale_date` | DATE | |
| `address` | TEXT | Original PPR address |
| `county` | TEXT | |
| `eircode` | TEXT | |
| `price` | NUMERIC(12,2) | |
| `not_full_market_price` | BOOLEAN | |
| `vat_exclusive` | BOOLEAN | |
| `description` | TEXT | Property type |
| `size_description` | TEXT | |
| `latitude` | DOUBLE PRECISION | NULL if ungeocodable |
| `longitude` | DOUBLE PRECISION | NULL if ungeocodable |
| `geog` | GEOGRAPHY(Point, 4326) | Used for all spatial queries |

**Indexes:**
- `properties_geog_idx` — GiST spatial index (76 MB) — powers radius search
- `properties_pkey` — 34 MB
- `properties_price_idx` — 43 MB
- `properties_sale_date_idx` — 11 MB
- `properties_county_idx` — 13 MB
- `properties_county_date_idx` — composite, filtered to `not_full_market_price = FALSE`
- `properties_eircode_idx` — 18 MB
- `properties_eircode_norm_idx` — functional index on `REPLACE(UPPER(eircode), ' ', '')`

### `submissions` table

Stores feedback and contact form submissions from the website.

| Column | Type |
|--------|------|
| `id` | BIGSERIAL |
| `kind` | TEXT (`'feedback'` or `'contact'`) |
| `ts` | TIMESTAMPTZ |
| `name` | TEXT |
| `email` | TEXT |
| `datasets` | TEXT |
| `comments` | TEXT |
| `message` | TEXT |
| `price_updates` | BOOLEAN |

---

## Backend API (`backend/main.py`)

**Runtime:** Python 3.11, FastAPI, asyncpg
**Host:** Railway
**URL:** `eloquent-optimism-production-350a.up.railway.app`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/geocode` | Resolve address/eircode to lat/lon |
| GET | `/search` | Radius-based property search |
| GET | `/trends` | Median/avg price by year |
| GET | `/eircode` | All sales for a routing key or full eircode |
| GET | `/counties` | List of counties with sale counts |
| POST | `/feedback` | Save feedback form submission to DB |
| POST | `/contact` | Save contact form submission to DB |

### Geocoding Resolution Order (`resolve_location`)

```
Query
  │
  ├─ 1. Raw coordinates passthrough  ("53.33,-6.26")
  │
  ├─ 2. In-memory cache hit          (TTL: 24 hours)
  │
  ├─ 3. Eircode DB lookup            (AVG lat/lon of matching eircode prefix)
  │
  ├─ 4. Token-based DB match         (all significant words must match;
  │      abbreviation-aware          road↔rd, avenue↔ave, mount↔mt etc;
  │      accepts if stddev < 0.02°)  (~1.4 km cluster radius)
  │
  ├─ 5. Mapbox Geocoding API         (with county hint appended if no
  │                                   county context in query)
  │
  └─ 6. Fuzzy DB ILIKE fallback      (last resort if Mapbox unavailable;
                                      requires ≥3 matching rows)
```

### Radius Search Query

```sql
SELECT ..., ST_Distance(geog, ST_MakePoint($lon, $lat)::geography) AS distance_m
FROM properties
WHERE ST_DWithin(geog, ST_MakePoint($lon, $lat)::geography, $radius_metres)
  [AND county = ... AND price >= ... AND sale_date >= ...]
ORDER BY sale_date DESC, distance_m
LIMIT 200
```

### Caching

In-memory TTL cache (per-process, resets on redeploy):

| Namespace | TTL |
|-----------|-----|
| `geocode` | 24 hours |
| `search` | 5 minutes |
| `trends` | 1 hour |
| `eircode` | 1 hour |
| `counties` | 1 hour |

### Environment Variables (Railway)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Supabase connection string |
| `MAPBOX_TOKEN` | Mapbox geocoding API key |
| `ENVIRONMENT` | Set to `production` to lock CORS to homeiq.ie |

---

## Frontend (`frontend/`)

**Stack:** React 18, TypeScript, Vite, React Router, Leaflet, Recharts
**Host:** Vercel
**URL:** `homeiq.ie`

### Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `App.tsx` | Main search — map + sidebar + trends chart |
| `/area/:slug` | `AreaPage.tsx` | Neighbourhood summary |
| `/county/:slug` | `CountyPage.tsx` | County price trends |
| `/county/dublin` | `DublinCountyPage.tsx` | Dublin-specific breakdown |
| `/eircode/:code` | `EircodePage.tsx` | Sales by eircode/routing key |
| `/mortgages` | `MortgagePage.tsx` | Mortgage repayment calculator |
| `/energy` | `EnergyPage.tsx` | BER rating analysis (static data) |
| `/about` | `AboutPage.tsx` | About HomeIQ.ie |

### Key Components

| Component | Purpose |
|-----------|---------|
| `SearchPanel.tsx` | Address input, radius, period, county filters |
| `ResultsList.tsx` | Scrollable list with exact-match promotion |
| `TrendsChart.tsx` | Recharts median/avg price overlay by year |
| `EircodePanel.tsx` | Eircode search results and stats |
| `WaffleMenu.tsx` | Site-wide navigation grid |
| `ContactModals.tsx` | Feedback and contact forms (modal) |
| `PageHeader.tsx` | Shared banner for content pages |

### Search Flow

```
User submits address + filters
         │
         ├─ fetchGeocode(q, county)      → GET /geocode    (map fly-to)
         │
         ├─ fetchNearestPins(params, 10) → GET /search?sort=distance&limit=10
         │                                  (map markers)
         ├─ searchProperties(params)     → GET /search?sort=date&limit=200
         │                                  (sidebar list)
         │
         └─ fetchTrends(q, radius, county) → GET /trends
                                              (chart)

Results merged:
  - Exact address matches promoted to top of list
  - Map shows exact matches + 10 nearest pins (deduped)
```

### Environment Variables (Vercel)

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Backend URL (e.g. `https://eloquent-optimism-...railway.app`) |

---

## Deployment

### Backend (Railway)
```bash
cd backend
railway link    # first time only
railway up
```
Railway builds with Nixpacks, runs `uvicorn main:app --host 0.0.0.0 --port $PORT`.

### Frontend (Vercel)
```bash
cd frontend
npm run build
npx vercel --prod
```
`vercel.json` rewrites all routes to `index.html` for SPA routing.

### Database
```bash
# Full re-import (destructive — truncates existing data)
DATABASE_URL=<url> python3 db/import.py

# Post-import: run migrate_perf.sql once if upgrading an existing DB
# (adds geog column, functional eircode index, composite county index)
```

---

## Data Flow Summary

```
PPR CSV  →  geocode.py  →  geocode_cache.db  →  PPR-ALL-geocoded.csv
                                                         │
                                                   db/import.py
                                                         │
                                                         ▼
                                                    Supabase DB
                                                         │
                                                   FastAPI (Railway)
                                                         │
                                                   React (Vercel)
                                                         │
                                                      Browser
```
