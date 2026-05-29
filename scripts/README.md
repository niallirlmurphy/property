# Geocoding Quality Scripts

This directory contains tools for assessing and fixing geocoding quality issues in the property database.

## Problem Overview

During bulk geocoding, when the geocoder can't find a specific address, it falls back to county or town centroids. This results in hundreds or thousands of distinct addresses sharing identical coordinates, making radius-based searches unreliable.

**Impact**: ~150,000+ property sales affected by centroid fallback geocoding.

## Scripts

### 1. Assessment: `assess_geocode_quality.py`

Comprehensive quality assessment of all geocoded data.

**Checks performed:**
- Out-of-bounds coordinates (outside Ireland)
- Suspicious precision (rounded coordinates)
- Duplicate coordinates (centroid detection)
- Place-name clustering consistency
- County boundary mismatches (optional, slow)

**Usage:**
```bash
python3 scripts/assess_geocode_quality.py
python3 scripts/assess_geocode_quality.py --check-counties  # Enable slow county check
```

**Output:**
```
=== Overall Geocoding Statistics ===
Total properties: 781,501
Geocoded: 620,849 (79.4%)

=== Duplicate geocode / centroid detection ===
Coordinates with 100+ distinct addresses: 50

Top 10 worst offenders:
(52.684256, -8.577379)  7,867 addresses  8,351 sales  (Limerick)
(53.341954, -8.944242)  6,836 addresses  7,215 sales  (Galway)
...
```

### 2. Fix Specific Issues: `fix_nobber_coordinates.py`

Fixes known bad coordinates for Nobber, Meath properties.

**Problem**: 27 Nobber properties geocoded to wrong location (near Crossakeel/Edgeworthstown)
- Wrong: (53.717143, -7.062706) 
- Correct: (53.8217, -6.7479)

**Usage:**
```bash
# Dry-run (shows what would be changed)
python3 scripts/fix_nobber_coordinates.py

# Apply changes
python3 scripts/fix_nobber_coordinates.py --apply

# Verbose output
python3 scripts/fix_nobber_coordinates.py --apply --verbose
```

### 3. Identify Centroids: `identify_centroid_coordinates.py`

Identifies and marks properties at centroid coordinates.

**Detection threshold**: Coordinates with 100+ distinct addresses (default)

**Modes:**

**a) Report only** (default):
```bash
python3 scripts/identify_centroid_coordinates.py
python3 scripts/identify_centroid_coordinates.py --threshold 50  # More sensitive
```

**b) Mark in database** (adds `geocode_quality` column):
```bash
# Dry-run
python3 scripts/identify_centroid_coordinates.py --mark

# Apply
python3 scripts/identify_centroid_coordinates.py --mark --apply
```

**c) Export for re-geocoding**:
```bash
python3 scripts/identify_centroid_coordinates.py --export
python3 scripts/identify_centroid_coordinates.py --export centroid_props.csv --threshold 50
```

### 4. Generate Re-geocoding Report: `generate_regeocoding_report.py`

Creates a prioritized CSV of all properties needing re-geocoding.

**Priorities:**
- **HIGH**: Centroid coordinates (100+ addresses at same point)
- **MEDIUM**: Suspicious clusters (10-99 addresses at same point)
- **LOW**: Missing coordinates but has eircode
- **VERIFY**: Recent sales in problematic areas

**Usage:**
```bash
# Full report
python3 scripts/generate_regeocoding_report.py

# Custom output filename
python3 scripts/generate_regeocoding_report.py --output my_report.csv

# Limit total properties
python3 scripts/generate_regeocoding_report.py --limit 5000
```

**Output:**
```
=== RE-GEOCODING REPORT SUMMARY ===
Total properties needing attention: 21,000
  HIGH priority (centroids):         10,000
  MEDIUM priority (clusters):         5,000
  LOW priority (missing coords):      5,000
  VERIFY priority (recent/suspect):   1,000
```

## Test Suite

### Data Quality Test: `test_duplicate_geocodes_centroid_detection`

Automated test that fails if too many centroid coordinates are detected.

**Threshold**: Maximum 50 coordinates with 100+ distinct addresses

**Run test:**
```bash
# Requires DATABASE_URL in tests/.env.test
cd tests
cp .env.test.example .env.test
# Edit .env.test and add your DATABASE_URL

cd ..
pytest tests/test_data_quality.py::test_duplicate_geocodes_centroid_detection -v
```

**Test output:**
```
--- Duplicate geocode / centroid detection ---
Coordinates with 100+ distinct addresses: 50

Top 10 worst offenders:
(52.684256, -8.577379)  7,867        8,351      Limerick
...

Total impact:
  Affected properties: 150,000
  Affected addresses:  45,000

PASSED  [if count <= 50]
FAILED  [if count > 50]
```

## Workflow

### Initial Assessment
```bash
# 1. Run full assessment
python3 scripts/assess_geocode_quality.py

# 2. Generate prioritized re-geocoding report
python3 scripts/generate_regeocoding_report.py --output regeocode_plan.csv
```

### Quick Fixes
```bash
# Fix known issues (like Nobber)
python3 scripts/fix_nobber_coordinates.py --apply
```

### Mark for Future Re-geocoding
```bash
# Add quality flags to database
python3 scripts/identify_centroid_coordinates.py --mark --apply
```

### Ongoing Monitoring
```bash
# Run data quality tests regularly
pytest tests/test_data_quality.py -v

# Alert fires if centroid count exceeds 50
```

## Database Schema Changes

The `identify_centroid_coordinates.py --mark` command creates:

```sql
ALTER TABLE properties
ADD COLUMN geocode_quality TEXT DEFAULT 'ok';

CREATE INDEX idx_properties_geocode_quality
ON properties(geocode_quality)
WHERE geocode_quality != 'ok';
```

**Values:**
- `'ok'`: Normal geocoding quality (default)
- `'centroid'`: Likely county/town centroid, needs re-geocoding

**Query properties needing re-geocoding:**
```sql
SELECT * FROM properties WHERE geocode_quality = 'centroid';
```

## Re-geocoding Strategy

Once you have the report, you can:

1. **Prioritize by eircode**: Properties with eircodes are easiest to fix
2. **Batch by county**: Re-geocode county by county
3. **Use better geocoder**: 
   - For addresses with eircodes: use Nominatim (good eircode coverage)
   - For street addresses: use Mapbox with county context
   - For townlands: use OSM/Nominatim with county filter

4. **Update database**:
```python
# After re-geocoding
UPDATE properties 
SET latitude = $1, 
    longitude = $2,
    geog = ST_MakePoint($2, $1)::geography,
    geocode_quality = 'ok'
WHERE id = $3;
```

## Common Centroid Coordinates

Top coordinates to investigate (from May 2025 assessment):

| Coordinate | Addresses | Location |
|-----------|-----------|----------|
| (52.684256, -8.577379) | 7,867 | Limerick city/county |
| (53.341954, -8.944242) | 6,836 | Galway city/county |
| (51.895201, -8.465737) | 6,369 | Cork city/county |
| (53.363060, -6.258540) | 6,264 | Dublin West |
| (52.246963, -7.145223) | 5,057 | Waterford city/county |

These are likely county or major city centroids where the geocoder gave up.

## Performance Notes

- **assess_geocode_quality.py**: ~30-60 seconds (skips county check by default)
- **identify_centroid_coordinates.py**: ~10-20 seconds
- **generate_regeocoding_report.py**: ~60-120 seconds (queries multiple tables)
- **fix_nobber_coordinates.py**: <5 seconds

All scripts use connection pooling and are safe to run on production (with dry-run defaults).

## Troubleshooting

**"DATABASE_URL not set"**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
# Or create backend/.env with DATABASE_URL
```

**"Connection timeout"**
- Check database is accessible
- Verify DATABASE_URL format
- Ensure PostGIS extension is enabled

**Test is skipped**
- Create `tests/.env.test` with DATABASE_URL
- Copy from `tests/.env.test.example`

**"Too many centroids" test failure**
- Expected on first run with existing data
- Run fixes, then test should pass
- Adjust MAX_CENTROID_COORDS threshold if needed
