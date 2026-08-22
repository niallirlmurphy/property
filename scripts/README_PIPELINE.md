# PPR Data Pipeline - Enhanced 2026-07-09

Complete pipeline for importing, geocoding, and enriching Ireland's Property Price Register data.

## Quick Start

### Full Pipeline (Recommended)
```bash
# Import new sales + geocode + enrich
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"

# Preview without making changes
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv" --dry-run

# Just geocode and enrich (skip import)
python3 scripts/ppr_full_pipeline.py --skip-import
```

### Individual Steps
```bash
# 1. Import new sales
python3 scripts/sync_ppr_updates.py --skip-geocoding

# 2. Geocode addresses
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply

# 3. Enrich properties
python3 scripts/enrich_batch6_2026.py --batch-size 100 --rate-limit 5
```

## What's New (2026-07-09)

### 1. HTML Entity Cleaning
**Problem:** Addresses with HTML entities fail geocoding
```
Before: "Tandy&#039;s Lane" → No results
After:  "Tandy's Lane" → Success
```

**Implementation:** `html.unescape()` in all geocoding paths

### 2. Eircode-First Strategy
**Problem:** Address-only geocoding is less accurate
```
Before: Search by full address → 70-80% success
After:  Try Eircode first, fallback to address → 98% success
```

**Implementation:** `MapboxClient.geocode()` with eircode parameter

### 3. Bulk Sale Extraction
**Problem:** Multi-unit sales have generic addresses
```
Before: "Units 1-76, Bridge Hall, Dublin" → Generic centroid
After:  "Bridge Hall, Dublin" → Specific location
```

**Implementation:** `extract_base_address()` removes unit ranges

### 4. Improved DuckDuckGo Scraping
**Problem:** HTML class selectors broke after DuckDuckGo updates
```
Before: Look for .result__snippet class → 2% success (class changed)
After:  Extract all page text → 90% success
```

**Implementation:** `soup.get_text()` instead of class-based selectors

### 5. MapboxClient Wrapper
**Features:**
- Automatic usage tracking to database
- 50k/month limit enforcement (safety margin from 100k free tier)
- Pre-flight quota checks
- Per-source attribution for analytics

## Pipeline Components

### Import (`sync_ppr_updates.py`)
**What it does:**
- Reads PPR CSV backward (most recent first)
- Imports only new sales since last sale_date
- Normalizes addresses (title case, abbreviations, punctuation)
- Flags properties for geocoding (`needs_geocoding = TRUE`)

**Performance:**
- 100-1,000 properties: ~10 seconds
- 1,000-5,000 properties: ~30 seconds
- Skips 700k+ existing rows efficiently

**Output:**
```
Found 390 new sales
Imported 390/390 properties
✓ Import complete
```

### Geocoding (`geocode_mapbox_batch.py`)
**What it does:**
- Fetches properties with `needs_geocoding = TRUE`
- Cleans HTML entities from addresses
- Extracts base address from bulk sales
- Tries Eircode first, falls back to address
- Validates: Ireland bounds + county + precision
- Updates database with coordinates

**Performance:**
- 100 properties: ~30 seconds (0.3s per property)
- 1,000 properties: ~5 minutes
- 2,871 properties: ~14 minutes

**Success rate:**
- With Eircode: ~98%
- Without Eircode: ~85-90%
- Overall: ~95%

**Quality scores:**
- Postcode/Eircode: 85/100
- Address: 80/100
- POI: 75/100
- Locality: 70/100

**Mapbox usage:**
- 1 request per property
- Tracked automatically in `mapbox_usage` table
- Monthly limit: 50k (enforced by wrapper)

**Output:**
```
Processing 2,871 properties...
Progress: 100/2871 properties...
...
✓ Success: 2,814 (98.0%)
✗ Failed: 57 (2.0%)
Quality Score Average: 78/100
```

### Enrichment (`enrich_batch6_2026.py`)
**What it does:**
- Fetches 2026 properties missing bedrooms/property_type
- Prioritizes recent, high-value properties
- Searches DuckDuckGo for property listings
- Extracts bedroom counts (1-10)
- Extracts property types (detached, semi-detached, terraced, apartment, bungalow)
- Updates database with enrichment data
- Rate limits to avoid blocking (5-10s between requests)

**Performance:**
- 100 properties: ~8-16 minutes (5-10s per property)
- Rate limiting: configurable (default 5s)

**Success rate:**
- Recent properties (2025-2026): ~90%
- Older properties: ~60-70%
- High-value properties: ~95%

**Output:**
```
[1/100] GLENSIDE, 267 NORTH CIRCULAR RD, DUBLIN 7
  📅 04 Jun 2026 | €445,000
  ✅ Fully enriched: 5 bed, terraced

[2/100] 19 TULLY ROAD, CHERRYWOOD, DUBLIN 18
  📅 03 Jun 2026 | €425,000
  ✅ Fully enriched: N/A, apartment
...
```

## Usage Examples

### Regular Biweekly Update
```bash
# Download latest PPR CSV from gov.ie
# Place in: source data/PPR-ALL.csv

# Run full pipeline
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"
```

### Backfill Missing Geocodes
```bash
# Geocode all properties flagged as needing it
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply

# Limit to 500 properties (stay under Mapbox quota)
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 500 --apply
```

### Backfill Missing Enrichment
```bash
# Enrich 500 recent properties
python3 scripts/enrich_batch6_2026.py --batch-size 500 --rate-limit 5

# Faster (but higher risk of blocking)
python3 scripts/enrich_batch6_2026.py --batch-size 500 --rate-limit 3
```

### Test Before Running
```bash
# Dry run - see what would happen
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv" --dry-run

# Test geocoding with 10 properties
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 10

# Test enrichment with 5 properties
python3 scripts/enrich_batch6_2026.py --batch-size 5 --rate-limit 3
```

## Monitoring & Troubleshooting

### Check Mapbox Usage
```bash
# Current month summary
python3 scripts/mapbox_usage_tracker.py --current-month

# Output:
# Month:           July 2026
# Total Requests:  2,871
# Remaining:       47,129 (94.3% available)
```

### Check Database Status
```bash
# Properties needing geocoding
psql $DATABASE_URL -c "SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE"

# Properties needing enrichment
psql $DATABASE_URL -c "SELECT COUNT(*) FROM properties WHERE bedrooms IS NULL AND sale_date >= '2026-01-01'"

# Recent imports
psql $DATABASE_URL -c "SELECT COUNT(*), MIN(sale_date), MAX(sale_date) FROM properties WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'"
```

### Common Issues

**Geocoding fails with "No route to host"**
- Database connection timeout (long-running operations)
- Solution: Run in smaller batches with `--limit`

**Enrichment gets 0% success rate**
- DuckDuckGo blocking requests
- Solution: Increase `--rate-limit` to 10-15 seconds

**Mapbox limit exceeded**
- Used 50k requests this month
- Solution: Wait for next month or increase limit in `mapbox_client.py`

**HTML entities in addresses**
- Should be cleaned automatically in all new imports
- Old data: Re-import with `sync_ppr_updates.py`

## Files & Logs

**Scripts:**
- `ppr_full_pipeline.py` - Complete pipeline orchestrator
- `sync_ppr_updates.py` - Import step
- `geocode_mapbox_batch.py` - Geocoding step
- `enrich_batch6_2026.py` - Enrichment step
- `mapbox_client.py` - MapboxClient wrapper
- `mapbox_usage_tracker.py` - Usage monitoring

**Logs:**
- `logs/ppr_sync.log` - Import logs
- `logs/enrichment_batch6_*.log` - Enrichment logs
- Database: `mapbox_usage` table for API tracking

**Helper Scripts:**
- `extract_base_address.py` - Bulk sale extraction logic
- `normalize_addresses.py` - Address normalization
- `county_validator.py` - County boundary validation

## Performance Benchmarks

**Import (sync_ppr_updates.py):**
- 100 sales: 5-10 seconds
- 1,000 sales: 20-30 seconds
- 5,000 sales: 1-2 minutes

**Geocoding (geocode_mapbox_batch.py):**
- 100 properties: 30 seconds
- 1,000 properties: 5 minutes
- 10,000 properties: 50 minutes
- API limit: 50k properties/month

**Enrichment (enrich_batch6_2026.py):**
- 100 properties @ 5s rate limit: 8-10 minutes
- 100 properties @ 10s rate limit: 16-18 minutes
- Recommended: 100-200 properties per run

**Full Pipeline:**
- 100 new sales: ~10-15 minutes
- 500 new sales: ~40-50 minutes
- 1,000 new sales: ~1.5 hours

## Automation

### Cron Job (Biweekly)
```bash
# Add to crontab (1st and 15th of month at 2:47 AM)
47 2 1,15 * * cd /path/to/project && python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv" >> logs/cron_pipeline.log 2>&1
```

### GitHub Actions (Example)
```yaml
name: PPR Pipeline
on:
  schedule:
    - cron: '47 2 1,15 * *'  # 1st and 15th at 2:47 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r backend/requirements.txt
      - run: python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          MAPBOX_TOKEN: ${{ secrets.MAPBOX_TOKEN }}
```

## Further Reading

- `CLAUDE.md` - Full project documentation
- `docs/MAPBOX_USAGE_TRACKING.md` - Mapbox quota management
- `docs/GEOCODING_IMPROVEMENTS_2026-07-09.md` - Enhancement details
- `scripts/README_MAPBOX.md` - Mapbox client usage
