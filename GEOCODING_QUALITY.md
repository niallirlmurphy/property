# Geocoding Quality Assessment & Fixes

**Date**: 2025-05-18  
**Issue**: Nobber, Meath search returns wrong location (Edgeworthstown, Longford area)

## Problem Summary

### Root Cause
During bulk geocoding with `geocode.py`, when the geocoder cannot find a specific address, it falls back to generic county or town centroid coordinates. This causes hundreds or thousands of distinct addresses to be assigned identical coordinates.

### Impact
- **~150,000+ properties** affected (out of 620,849 geocoded properties)
- **50 centroid coordinates** with 100+ distinct addresses each
- Worst case: **7,867 distinct addresses** mapped to a single point in Limerick
- Makes radius-based searches unreliable or return wrong results

### Specific Issue: Nobber, Meath
- **27 Nobber properties** geocoded to (53.717143, -7.062706)
  - This is near Crossakeel, ~9km from actual Nobber
  - Searches for "Nobber, Meath" don't find these properties
- **54 Nobber properties** have correct coordinates (53.8217, -6.7479)
- The issue affects properties from different time periods, suggesting stale cache entries

## Assessment Results

### Overall Statistics
- Total properties: **781,501**
- Geocoded: **620,849** (79.4%)
- Missing coordinates: **160,652** (20.6%)

### Centroid Detection
**50 coordinates** with 100+ distinct addresses (county/city centroids):

| Coordinate | Addresses | Sales | Primary Location |
|-----------|-----------|-------|------------------|
| (52.684256, -8.577379) | 7,867 | 8,351 | Limerick |
| (53.341954, -8.944242) | 6,836 | 7,215 | Galway |
| (51.895201, -8.465737) | 6,369 | 6,614 | Cork |
| (53.363060, -6.258540) | 6,264 | 6,511 | Dublin West |
| (52.246963, -7.145223) | 5,057 | 5,423 | Waterford |
| **...and 45 more** | | | |

### Place-Name Issues
**30 place names** with scattered coordinates (should cluster tightly):
- "Milltown": properties 70km apart
- "Glaslough": properties 133km apart  
- "Waterville": properties 76km apart
- "Holiday Village": properties 105km apart

### Data Quality
- ✓ No out-of-bounds coordinates (all within Ireland)
- ⚠️ 10 properties with suspiciously rounded coordinates
- ⚠️ 50 major centroid coordinates
- ⚠️ Scattered place-name geocoding

## Solutions Implemented

### 1. Fix Nobber Coordinates ✅
**Script**: `scripts/fix_nobber_coordinates.py`

Corrects the 27 Nobber properties with wrong coordinates:
- From: (53.717143, -7.062706) near Crossakeel
- To: (53.8217, -6.7479) actual Nobber location

```bash
# Test (dry-run)
python3 scripts/fix_nobber_coordinates.py

# Apply fix
python3 scripts/fix_nobber_coordinates.py --apply
```

### 2. Identify Centroid Coordinates ✅
**Script**: `scripts/identify_centroid_coordinates.py`

Detects all properties at centroid coordinates (100+ addresses per coordinate).

**Three modes:**
```bash
# Report only
python3 scripts/identify_centroid_coordinates.py

# Mark in database (adds geocode_quality='centroid' flag)
python3 scripts/identify_centroid_coordinates.py --mark --apply

# Export CSV for re-geocoding
python3 scripts/identify_centroid_coordinates.py --export
```

### 3. Generate Re-geocoding Report ✅
**Script**: `scripts/generate_regeocoding_report.py`

Creates prioritized CSV of all properties needing re-geocoding:
- **HIGH**: Centroid coordinates (100+ addresses)
- **MEDIUM**: Suspicious clusters (10-99 addresses)  
- **LOW**: Missing coordinates but has eircode
- **VERIFY**: Recent sales in problematic areas

```bash
python3 scripts/generate_regeocoding_report.py
python3 scripts/generate_regeocoding_report.py --output report.csv --limit 5000
```

### 4. Automated Quality Test ✅
**Test**: `tests/test_data_quality.py::test_duplicate_geocodes_centroid_detection`

Fails CI/CD pipeline if centroid coordinates exceed threshold (50).

```bash
pytest tests/test_data_quality.py::test_duplicate_geocodes_centroid_detection -v
```

## How to Use

### Quick Fix (Nobber)
```bash
cd "/Users/nmurphy/claude/property price project"
python3 scripts/fix_nobber_coordinates.py --apply
```

### Full Assessment
```bash
# 1. Run quality assessment
python3 scripts/assess_geocode_quality.py > assessment_report.txt

# 2. Generate re-geocoding work list
python3 scripts/generate_regeocoding_report.py --output regeocode_plan.csv

# 3. Review the CSV and prioritize
# regeocode_plan.csv contains:
#   - priority (HIGH/MEDIUM/LOW/VERIFY)
#   - reason (why it needs re-geocoding)
#   - address, county, eircode
#   - old coordinates (if any)
```

### Mark Properties for Future Work
```bash
# Add geocode_quality='centroid' flag to affected properties
python3 scripts/identify_centroid_coordinates.py --mark --apply

# Query marked properties:
# SELECT * FROM properties WHERE geocode_quality = 'centroid';
```

### Continuous Monitoring
```bash
# Add to CI/CD pipeline
pytest tests/test_data_quality.py -v

# Test will FAIL if:
# - Geocoding coverage drops below 75%
# - Centroid coordinates exceed 50
# - Coordinates found outside Ireland
```

## Re-geocoding Strategy

### Priorities
1. **HIGH (10,000 properties)**: Centroid coordinates - most impactful to fix
2. **MEDIUM (5,000 properties)**: Suspicious clusters - may be valid but worth checking
3. **LOW (5,000 properties)**: Missing coords with eircode - easiest to geocode
4. **VERIFY (1,000 properties)**: Recent sales in problematic areas - quality check

### Recommended Approach
1. **Start with HIGH priority properties that have eircodes** (~50% of them)
   - Use Nominatim (good eircode coverage)
   - Fast and accurate
   
2. **Process by county** to batch API requests efficiently
   - Dublin: 6,264 properties
   - Cork: 6,369 properties  
   - Galway: 6,836 properties
   - Limerick: 7,867 properties

3. **Use appropriate geocoder per address type:**
   - **Eircodes**: Nominatim (OSM has eircode data)
   - **Street addresses**: Mapbox with county context
   - **Townlands/rural**: OSM/Nominatim with county filter

4. **Update and validate:**
   ```python
   UPDATE properties 
   SET latitude = $1, 
       longitude = $2,
       geog = ST_MakePoint($2, $1)::geography,
       geocode_quality = 'ok'
   WHERE id = $3;
   ```

5. **Re-run quality tests** to verify improvements

## Database Changes

### New Column (Optional)
If you run `identify_centroid_coordinates.py --mark --apply`:

```sql
ALTER TABLE properties
ADD COLUMN geocode_quality TEXT DEFAULT 'ok';

CREATE INDEX idx_properties_geocode_quality
ON properties(geocode_quality)
WHERE geocode_quality != 'ok';
```

**Values:**
- `'ok'`: Normal geocoding (default)
- `'centroid'`: Needs re-geocoding

**Query flagged properties:**
```sql
-- All properties needing re-geocoding
SELECT * FROM properties WHERE geocode_quality = 'centroid';

-- Count by county
SELECT county, COUNT(*) 
FROM properties 
WHERE geocode_quality = 'centroid'
GROUP BY county
ORDER BY COUNT(*) DESC;

-- Properties with eircodes (easiest to fix)
SELECT * FROM properties 
WHERE geocode_quality = 'centroid' 
  AND eircode IS NOT NULL;
```

## Prevention

### For Future Geocoding Runs

1. **Cache validation**: Before caching a result, check if it's suspiciously common
   ```python
   # In geocode.py, before cache.set():
   existing_at_coord = db.execute(
       "SELECT COUNT(DISTINCT address) FROM cache WHERE lat = ? AND lon = ?",
       (lat, lon)
   )
   if existing_at_coord > 50:
       logger.warning(f"Centroid fallback suspected: {address} -> ({lat}, {lon})")
       # Don't cache, try harder or mark for manual review
   ```

2. **Graduated fallback strategy**:
   - Try exact address first
   - Try address without house number
   - Try street + town + county
   - Only fall back to town centroid if confidence is high
   - **Never** fall back to county centroid

3. **Quality checks during import**:
   ```python
   # In db/import.py:
   if properties_at_this_coord > 100:
       logger.warning(f"Centroid detected: {coord} has {count} addresses")
   ```

4. **Regular monitoring**:
   ```bash
   # Add to cron/scheduled job
   pytest tests/test_data_quality.py --tb=short
   # Alert if fails
   ```

## Files Created

```
scripts/
├── README.md                           # Detailed script documentation
├── assess_geocode_quality.py          # Full quality assessment
├── fix_nobber_coordinates.py          # Fix specific known issues
├── identify_centroid_coordinates.py   # Detect and mark centroids
└── generate_regeocoding_report.py     # Prioritized re-geocoding list

tests/
└── test_data_quality.py               # Added: test_duplicate_geocodes_centroid_detection()

GEOCODING_QUALITY.md                   # This file (executive summary)
```

## Next Steps

1. **Immediate**: Fix Nobber coordinates
   ```bash
   python3 scripts/fix_nobber_coordinates.py --apply
   ```

2. **Short-term**: Generate and review re-geocoding report
   ```bash
   python3 scripts/generate_regeocoding_report.py
   ```

3. **Medium-term**: Re-geocode HIGH priority properties
   - Focus on those with eircodes first (easier)
   - Process by county for efficiency
   - Validate improvements with test suite

4. **Long-term**: Prevent future issues
   - Add validation to geocoding pipeline
   - Run quality tests in CI/CD
   - Monitor centroid count over time

## Questions?

See `scripts/README.md` for detailed usage instructions and troubleshooting.
