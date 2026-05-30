# Geocoding Queue

**Priority geocoding system for properties imported without coordinates**

---

## Overview

Properties imported via PPR sync without coordinates are automatically flagged with `needs_geocoding = TRUE` for later high-quality geocoding.

**Current queue:** 2,963 properties (as of 2026-05-21)

---

## How It Works

### Automatic Flagging

When properties are imported with `--skip-geocoding`:

```sql
INSERT INTO properties (..., needs_geocoding)
VALUES (..., latitude IS NULL OR longitude IS NULL)
```

Properties with NULL coordinates are automatically flagged.

### Priority Scoring

The `properties_needing_geocoding` view prioritizes by:

1. **High-value properties** (>€500k) - Priority tier 1
2. **Mid-value properties** (€300k-500k) - Priority tier 2  
3. **Other properties** (<€300k) - Priority tier 3
4. Within each tier: **Recent sales first** (newest → oldest)

```sql
SELECT * FROM properties_needing_geocoding LIMIT 10;
```

---

## Geocoding Strategies

### Option 1: Autoaddress API (Recommended)

**Best for: Properties with Eircodes**

```bash
cd /path/to/project
python3 scripts/geocode_from_autoaddress.py --limit 500
```

- Uses existing Autoaddress API key
- High accuracy for Irish addresses
- Same API used for Eircode enrichment
- Process 500/day to stay within rate limits

### Option 2: Mapbox Geocoding API

**Best for: Addresses without Eircodes**

```bash
# Export queue
python3 scripts/export_geocoding_queue.py --output geocode_queue.csv

# Upload to Mapbox batch geocoding
# https://docs.mapbox.com/api/search/geocoding/#forward-geocoding

# Import results
python3 scripts/import_geocoded_results.py geocode_queue_geocoded.csv
```

- High-quality international geocoding
- Batch processing available
- Good for rural addresses

### Option 3: Manual Geocoding

**Best for: High-value properties (>€1M)**

```bash
# Export high-value properties
python3 scripts/export_geocoding_queue.py --min-price 1000000

# Manually geocode using:
# - Google Maps
# - Eircode Finder (https://finder.eircode.ie)
# - Property Price Register listings

# Import via CSV
python3 scripts/import_geocoded_results.py manual_geocodes.csv
```

---

## Validation After Geocoding

All imported coordinates are validated:

1. **Ireland bounds check** (51.4-55.5°N, -10.7--5.4°W)
2. **Routing key distance** (Eircodes within 5km of centroid)
3. **County boundary validation**

Failed validation → coordinates set to NULL, property stays in queue.

---

## Monitoring

### Check Queue Status

```sql
-- Total needing geocoding
SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE;

-- By priority tier
SELECT 
    CASE
        WHEN price > 500000 THEN 'High-value (>€500k)'
        WHEN price > 300000 THEN 'Mid-value (€300-500k)'
        ELSE 'Other (<€300k)'
    END as tier,
    COUNT(*) as count
FROM properties
WHERE needs_geocoding = TRUE
GROUP BY tier
ORDER BY tier;

-- Properties with Eircodes (easier to geocode)
SELECT COUNT(*) 
FROM properties 
WHERE needs_geocoding = TRUE AND eircode IS NOT NULL;
```

### Track Progress Over Time

```sql
-- Geocoding progress (week over week)
SELECT 
    DATE_TRUNC('week', sale_date) as week,
    COUNT(*) FILTER (WHERE needs_geocoding = TRUE) as needs_geo,
    COUNT(*) FILTER (WHERE latitude IS NOT NULL) as has_coords,
    COUNT(*) as total
FROM properties
WHERE sale_date >= '2024-01-01'
GROUP BY week
ORDER BY week DESC
LIMIT 10;
```

---

## Scripts

### Export Queue

```bash
# Export all properties needing geocoding
python3 scripts/export_geocoding_queue.py

# Export high-priority only
python3 scripts/export_geocoding_queue.py --limit 500 --min-price 300000

# Export with Eircodes (for Autoaddress)
python3 scripts/export_geocoding_queue.py --with-eircode
```

**Output:** `geocode_queue.csv` with columns:
- id, address, county, eircode, routing_key
- price, sale_date, description
- priority_tier

### Import Geocoded Results

```bash
# Import from CSV with new coordinates
python3 scripts/import_geocoded_results.py results.csv
```

**Expected CSV format:**
- id (required)
- latitude, longitude (required)
- geocode_source (e.g., 'autoaddress', 'mapbox', 'manual')

Script will:
1. Validate coordinates
2. Update latitude/longitude
3. Set `needs_geocoding = FALSE`
4. Log geocode_source for analytics

---

## Integration with Daily Eircode Enrichment

The existing Eircode enrichment cron job can be extended to also geocode:

```python
# In db/eircode_enrich.py
# After enriching Eircode:
if enriched_eircode:
    # Also geocode using Autoaddress
    lat, lon = geocode_from_autoaddress(address, eircode)
    if lat and lon:
        update_coordinates(property_id, lat, lon, 'autoaddress')
```

This would gradually clear the queue over time as part of routine data maintenance.

---

## Future Enhancements

### 1. Automatic Queue Processing

Add to daily cron:
```bash
# Geocode 100 properties per day
python3 scripts/geocode_from_autoaddress.py --limit 100
```

At 100/day, current queue cleared in ~30 days.

### 2. Confidence Scoring

Track geocoding confidence:
```sql
ALTER TABLE properties ADD COLUMN geocode_confidence INTEGER;
-- 0-100 score, reject if < 70
```

### 3. Source Tracking

```sql
ALTER TABLE properties ADD COLUMN geocode_source TEXT;
-- 'autoaddress' | 'mapbox' | 'nominatim' | 'manual' | 'salesforce'
```

Track which sources produce best results.

### 4. Re-geocoding Schedule

Properties with low-confidence scores get re-geocoded quarterly:
```sql
-- Flag for re-geocoding if confidence < 70
UPDATE properties
SET needs_geocoding = TRUE
WHERE geocode_confidence < 70
  AND latitude IS NOT NULL;
```

---

## Summary

**Automatic flagging** + **priority queue** + **high-quality geocoding sources** = **systematic data quality improvement**

Properties are:
1. ✅ Imported immediately (no geocoding delay)
2. ✅ Flagged automatically for geocoding
3. ✅ Prioritized by value and recency
4. ✅ Geocoded with high-quality sources
5. ✅ Validated before coordinates applied

**Result:** Fresh sales data available immediately, coordinates added later with better quality than bulk import geocoding.
