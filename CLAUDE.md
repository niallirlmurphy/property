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
- `NOMINATIM_URL` (backend geocoding endpoint; defaults to public endpoint)
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

### Biweekly Updates (Automated)
**Schedule:** 1st and 15th of each month at 2:47 AM
```bash
python3 scripts/sync_ppr_updates.py --skip-geocoding
```
- Imports new sales since most recent sale_date in database
- Flags properties with `needs_geocoding = TRUE`
- Optimized: backward CSV scanning (only reads new rows)
- Logs to `logs/ppr_sync.log`

**Then geocode new imports:**
```bash
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
```
- Batch geocoding via Mapbox API (1,000 properties per request)
- Comprehensive validation (Ireland bounds + county + precision)
- Expected success: 70-80% with quality 85-90/100
- Cost: FREE (within 100k/month tier)

**Property enrichment (automatic):**
The sync script automatically enriches new properties with bedroom counts and property types by searching the web. This happens after import and geocoding complete. Properties from the last month are enriched (limit: 100 per run).

**Manual enrichment:**
```bash
python3 scripts/enrich_recent_properties.py --months 3
```
- Searches DuckDuckGo for property details
- Extracts bedroom counts and property types
- 10-second rate limiting to avoid blocking
- Expected success: 60-90% for recent high-value properties

**Result:** Database stays current with 2-week lag, 70-80% of new properties geocoded automatically, and recent properties enriched with bedroom/type data.

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
- **Registrar:** Letshost.ie (Team Blue Internet Services IE Ltd)
- **DNS Management:** https://www.letshost.ie (client login required)
- **Nameservers:** Irish domain registry (.ie TLD servers)
- **Current Setup:** Domain points to Vercel edge network

To modify DNS records (TXT for verification, A/CNAME for routing):
1. Log in to https://www.letshost.ie
2. Navigate to Domain Management → homeiq.ie
3. Access DNS Settings/Records section
4. Add/modify records as needed
5. DNS propagation typically takes 5-15 minutes

**Database (Supabase/Postgres)**
1. Create project/instance and copy connection string.
2. `DATABASE_URL=<url> python3 db/import.py` — runs `schema.sql` then bulk-imports.

**Backend (Railway)**
- Connect the `backend/` directory to a Railway service.
- Set environment variables in Railway:
  - `DATABASE_URL` (required - Supabase connection string)
  - `MAPBOX_TOKEN` (required - for geocoding API)
  - `SENTRY_DSN` (optional - error tracking)
  - `NOMINATIM_URL` (optional - defaults to public endpoint)
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
- **Address normalization**: All addresses stored in both original and normalized forms. `address_normalized` column applies consistent formatting (title case, whitespace cleanup, abbreviation standardization, remove "No." prefix, standardize apartment/unit). Applied to all 784k properties.
- **Routing key indexing**: Generated column extracts first 3 characters of Eircode (e.g., D02, H91). Materialized view `routing_key_stats` provides centroids and statistics for 301 routing keys. Enables validation and fallback geocoding.
- **Geocoding queue**: Properties imported without coordinates flagged with `needs_geocoding = TRUE`. Priority order: price (>€500k first), then recency. View: `properties_needing_geocoding` for processing.
- **Centroid cleanup** (In progress): ~70k properties stuck at generic centroid coordinates (100+ addresses at same point). Mapbox re-geocoding achieving 92-97% success with 50%+ rooftop precision. Progress: 17,813 fixed (2026-05-29), 57,144 remaining. Continue monthly with fresh API credits.
- **Eircode enrichment**: Daily cron job processes properties via Autoaddress API (address validation only, not geocoding). Autoaddress provides address formatting and Eircode data but not coordinates.

### Search & Performance
- **Radius search**: `ST_DWithin(geom::geography, ...)` on GIST-indexed PostGIS geometry column. Results ordered by `ST_Distance` ascending. Auto-expands radius (2x, 3x, 5x, 10x up to 20km) if fewer than 5 results found.
- **Polygon search** (New): `ST_Within(geom::geometry, polygon)` for map-based area selection. Supports drawing tools (polygon, rectangle, circle) at `/polygon`. Accepts custom polygon coordinates via `POST /search/polygon`. Up to 1,000 properties per query.
- **Geocoding at search time**: Backend calls Nominatim (`NOMINATIM_URL`) to resolve user queries to (lat, lon). Supports addresses, Eircodes, and coordinate pairs.
- **Trends query**: Uses `PERCENTILE_CONT(0.5)` for median price, filtered to `not_full_market_price = FALSE`.
- **Caching**: In-memory TTL cache for counties (1h), trends (1h), Eircodes (1h), geocode results (24h), search results (5min).

### Security
- **Row-Level Security (RLS)**: Enabled on properties table. Public has SELECT-only access; writes blocked by default. Protects against unauthorized data modification while keeping PPR data publicly readable.
- **CORS**: Restricted to homeiq.ie and www.homeiq.ie in production. localhost:5173 allowed in development.
- **Monitoring**: Sentry integration for error tracking and performance monitoring. Search analytics tracked for observability.

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
- **Geocoding API**: Mapbox (~100k/100k requests used this month, resets next month). Reserve 2k/month for biweekly PPR sync.

## Troubleshooting
- **`DATABASE_URL` errors**: verify `.env` value format and DB reachability; confirm PostGIS extension is enabled.
- **Few/no radius results**: confirm imported rows have non-NULL geometry and that search coordinates are valid.
- **Geocoder seems stalled**: use `python3 geocode.py --status`; verify local Nominatim is reachable at `http://localhost:8080/search` and check `geocode.py` logs for retry/backoff errors.
- **HTTP 429 / throttling**: reduce request rate, retry later, or switch to local/self-hosted Nominatim.
- **Frontend can’t reach API**: verify `VITE_API_URL`, CORS settings, and backend URL/health.
- **Search shows wrong county results**: County filter defaults to "Dublin" for usability (most populous region). Auto-detection corrects mismatches when search query contains a county name (e.g., searching "Galway City" with "Dublin" filter will auto-switch to Galway). County page links include both `q` and `county` parameters to ensure proper filtering.

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
