# Geocoding Quality Monitoring & Correction

**Automatic flagging system for properties with bad geocoding data**

---

## Overview

Properties are **automatically flagged** when coordinate validation detects quality issues:
- Coordinates >5km from routing key centroid
- Indicates bad geocoding data from hybrid sources

Flagged properties are **prioritized for re-geocoding** from trusted data sources.

---

## How It Works

### 1. Automatic Flagging

When a user searches for an Eircode (e.g., `D11 W981`):

```
1. Backend fetches exact Eircode coordinates from database
2. Backend calculates routing key (D11) centroid
3. Validates: Are coordinates within 5km of centroid?
   ✗ NO → Flag property, use centroid instead
   ✓ YES → Use exact coordinates
4. Fire-and-forget task: UPDATE properties SET geocode_quality_issue = TRUE
```

**Logs:**
```
WARNING: Eircode D11W981 coordinates (53.39789, -6.12909) too far from 
         routing key D11 centroid (53.38977, -6.28171), using centroid instead
INFO: Flagged Eircode D11W981 for priority re-geocoding
```

### 2. Monitoring

**Check flagged count:**
```sql
SELECT COUNT(*) FROM properties WHERE geocode_quality_issue = TRUE;
```

**View prioritized list:**
```sql
SELECT * FROM properties_needing_regeocode LIMIT 10;
```

Columns:
- `id`, `address`, `county`, `eircode`, `routing_key`
- `latitude`, `longitude` (current bad coordinates)
- `distance_from_centroid_km` (how far off)
- `sale_date`, `price`

**Priority order:**
1. High-value (>€500k)
2. Recent sales (2024+)
3. Has routing key (can validate correction)

---

## Correction Workflow

### Step 1: Export Flagged Properties

```bash
cd /path/to/project
DATABASE_URL=<your-db-url> python3 scripts/export_bad_geocodes.py
```

**Options:**
- `--output bad_geocodes.csv` (default)
- `--limit 100` (export only first 100)

**Output:** `bad_geocodes.csv` with columns:
```
id, address, county, eircode, routing_key,
bad_latitude, bad_longitude,
sale_date, price, distance_from_centroid_km,
new_latitude, new_longitude, geocode_source
```

### Step 2: Re-Geocode Using Trusted Source

**Option A: Mapbox Batch Geocoding API**
```bash
# Upload CSV to Mapbox batch geocoding
# https://docs.mapbox.com/api/search/geocoding/

# Or use mapbox CLI:
cat bad_geocodes.csv | while IFS=, read -r id address county eircode rest; do
  # Query Mapbox for each address
  curl "https://api.mapbox.com/geocoding/v5/mapbox.places/${address}.json?access_token=${MAPBOX_TOKEN}"
done
```

**Option B: Autoaddress Reverse Geocoding**
```bash
# If bad coordinates are close, reverse geocode to get correct Eircode first
# Then forward geocode the Eircode

# For each property with coordinates:
curl "https://api.autoaddress.com/3.0/reverseGeocode?lat=${bad_lat}&lng=${bad_lon}&key=${AUTOADDRESS_KEY}"
```

**Option C: Salesforce Maps Geocoding**
```bash
# Use Salesforce Maps Data Preparation (same as hybrid geocoding source)
# Import CSV to Salesforce, geocode, export
```

**Option D: Manual Review**
- For high-value/high-visibility properties
- Check Google Maps / Eircode Finder
- Verify against Property Price Register listings

### Step 3: Import Corrected Coordinates

Fill in `new_latitude`, `new_longitude`, `geocode_source` columns in CSV.

**Then import:**
```bash
# TODO: Create import_corrected_geocodes.py script
python3 scripts/import_corrected_geocodes.py bad_geocodes.csv
```

Script should:
1. Read CSV with corrections
2. Update `latitude`, `longitude` in database
3. Set `geocode_quality_issue = FALSE`
4. Log corrections for audit trail

---

## Monitoring Over Time

### Sentry Integration

Validation warnings are logged, so they'll appear in Sentry:
- Monitor frequency of bad geocodes
- Track which routing keys have most issues
- Identify patterns (e.g., specific geocoding source)

### Analytics Queries

**Flagging rate over time:**
```sql
SELECT 
    DATE_TRUNC('month', sale_date) as month,
    COUNT(*) FILTER (WHERE geocode_quality_issue = TRUE) as flagged,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE geocode_quality_issue = TRUE) / COUNT(*), 2) as pct
FROM properties
WHERE sale_date >= '2024-01-01'
GROUP BY month
ORDER BY month DESC;
```

**Most problematic routing keys:**
```sql
SELECT 
    routing_key,
    county,
    COUNT(*) as flagged_count,
    AVG(distance_from_centroid_km) as avg_distance_km
FROM properties_needing_regeocode
GROUP BY routing_key, county
ORDER BY flagged_count DESC
LIMIT 20;
```

**Breakdown by geocoding source** (requires tracking source in DB):
```sql
-- If we add geocode_source column in future:
SELECT 
    geocode_source,
    COUNT(*) as flagged_count
FROM properties
WHERE geocode_quality_issue = TRUE
GROUP BY geocode_source
ORDER BY flagged_count DESC;
```

---

## Expected Impact

### Immediate
- **User experience:** Bad Eircode searches now return routing key centroid (better than wrong location)
- **Visibility:** Know exactly which properties have bad coordinates
- **Prioritization:** Focus re-geocoding effort on high-value/recent properties

### Long-term
- **Data quality improvement:** Systematic correction of bad geocoding over time
- **Validation:** Can compare corrections against original to improve hybrid geocoding logic
- **Observability:** Track which geocoding sources are most reliable

### Metrics to Track
- Number of properties flagged per week
- Re-geocoding correction rate (how many get fixed)
- User search success rate (does it improve?)
- Distance accuracy improvement (average km from centroid)

---

## Future Enhancements

1. **Automatic re-geocoding pipeline**
   - Cron job to export → re-geocode → import
   - Use Mapbox batch API for automated corrections

2. **Geocoding source tracking**
   - Add `geocode_source` column (nominatim, mapbox, salesforce, etc.)
   - Identify which sources produce most errors

3. **Confidence scoring**
   - Add `geocode_confidence` column (0-100)
   - Flag low-confidence coordinates proactively

4. **Real-time validation on import**
   - Run routing key validation during `db/import.py`
   - Flag bad coordinates before they reach production

5. **User reporting**
   - "Report incorrect location" button on frontend
   - Users can flag bad coordinates (crowdsourced QA)

---

## Troubleshooting

### False positives (good coordinates flagged)

**Cause:** Routing key centroid might be skewed if most properties in area are on one side

**Solution:** Adjust threshold in `backend/main.py`:
```python
if lat_diff < 0.05 and lon_diff < 0.08:  # Current: ~5km threshold
```

Increase to `0.08` and `0.12` for ~8km threshold if needed.

### Properties not getting flagged

**Check:**
1. Is validation running? Search for the Eircode to trigger validation
2. Check logs for WARNING messages
3. Verify `geocode_quality_issue` column exists
4. Check routing key has enough properties (min 5 required)

### Export script fails

**Common issues:**
- `DATABASE_URL` not set
- View `properties_needing_regeocode` doesn't exist
- No flagged properties to export

---

## Summary

**Automatic flagging** + **prioritized correction** = **systematic data quality improvement**

Properties with bad geocoding are:
1. ✅ Detected automatically when searched
2. ✅ Flagged in database for correction
3. ✅ Prioritized by value/recency
4. ✅ Exported for bulk re-geocoding
5. ✅ Monitored via logs and analytics

Result: **Better search accuracy, higher user satisfaction, cleaner data over time.**
