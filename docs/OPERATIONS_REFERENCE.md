# Operations reference

Moved out of CLAUDE.md on 2026-11-02 to keep the always-loaded context small. CLAUDE.md links here.

## Centroid cleanup

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


## Publishing new content


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


## Verifying RLS configuration

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

## Security monitor (manual)

```bash
# Quick check
python3 scripts/security_monitor.py

# Check and auto-fix
python3 scripts/security_monitor.py --fix
```

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

