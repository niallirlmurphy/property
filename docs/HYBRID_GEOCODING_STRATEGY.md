# Hybrid Geocoding Strategy

**Two-phase approach: Autoaddress for Eircode properties, Mapbox for non-Eircode properties**

---

## Overview

Properties imported via PPR sync without coordinates are geocoded using a hybrid strategy that maximizes accuracy by leveraging the strengths of each service:

1. **Phase 1: Autoaddress** - Properties WITH Eircodes (74.8% of queue)
2. **Phase 2: Mapbox** - Properties WITHOUT Eircodes (25.2% of queue)

---

## Why Hybrid?

### Autoaddress Strengths
✅ Built on authoritative Irish Eircode database  
✅ 20+ years Irish address expertise  
✅ Returns coordinates AND enriches Eircodes  
✅ Highly accurate for properties with Eircodes  

❌ Rate limit: 1 request/second  
❌ No batch API  
❌ Paid service (pricing varies)

### Mapbox Strengths
✅ Batch API: 1,000 queries per request  
✅ 100,000 free requests/month  
✅ Fast: sub-400ms latency  
✅ Good for rural/older addresses without Eircodes  

❌ No Eircode enrichment  
❌ Generic global service (not Ireland-specific)  
❌ Quality varies for rural Irish addresses

---

## Current Queue Stats

**Total needing geocoding:** 2,963 properties (as of 2026-05-21)

**Phase 1 (Autoaddress):**
- Properties WITH Eircodes: **2,215 (74.8%)**
- Estimated time: ~2.5 hours at 1 req/sec
- Expected success rate: 85-95%
- Bonus: 200-300 Eircode enrichments

**Phase 2 (Mapbox):**
- Properties WITHOUT Eircodes: **748 (25.2%)**
- Estimated time: <1 minute (single batch API call)
- Expected success rate: 70-80%
- Cost: FREE (within 100k/month tier)

---

## Validation Framework

### Common Validations (Both Services)

**1. Ireland Bounds Check (CRITICAL - Hard Reject)**
```
Latitude: 51.4° to 55.5°N
Longitude: -10.7° to -5.4°W
```
Rejects coordinates outside Ireland (prevents UK/international false matches).

**2. County Boundary Validation (Soft Reject)**
- Validates coordinates fall within correct county
- Uses approximate county bounding boxes
- Downgrades quality score but doesn't reject (counties have irregular boundaries)

### Autoaddress-Specific Validations

**3. Routing Key Distance Validation (CRITICAL for Eircodes)**
```python
# Eircode coordinates must be within 5km of routing key centroid
lat_diff < 0.05° and lon_diff < 0.08°
# Hard reject if >5km (indicates bad geocoding)
```

**Quality Scoring:**
- **100**: Perfect (Ireland + county + routing key validated)
- **90**: Excellent (Ireland + county validated, no routing key)
- **80**: Good (Ireland validated, no county to check)
- **70**: Acceptable (Ireland validated, county check failed)
- **<70**: Rejected

### Mapbox-Specific Validations

**3. Coordinate Precision Check (CRITICAL)**
```python
ACCEPTABLE_PRECISION = {'rooftop', 'parcel', 'point'}
# Reject: 'interpolated', 'approximate'
```

**Quality Scoring:**
- **100**: Rooftop accuracy
- **90**: Parcel accuracy
- **80**: Point accuracy
- **<70**: Rejected (interpolated/approximate)

---

## Implementation

### Phase 1: Autoaddress (Eircode Properties)

```bash
cd /Users/nmurphy/claude/property\ price\ project

# Dry run first (see what would be geocoded)
python3 scripts/regeocode_autoaddress.py \
  --needs-geocoding \
  --with-eircode \
  --limit 10

# Apply for real (start with small batch)
python3 scripts/regeocode_autoaddress.py \
  --needs-geocoding \
  --with-eircode \
  --apply \
  --limit 100

# Full batch (2,215 properties)
python3 scripts/regeocode_autoaddress.py \
  --needs-geocoding \
  --with-eircode \
  --apply
```

**Progress monitoring:**
```
✓ [1/2215] 5 HATTERSLEY PK, CHURCHTOWN, CARNDONAGH
  53.456789,-7.123456 | Q:100 | Eircode: F93XX12
...
Progress: 100/2215 | Success: 87 | Failed: 13 | Avg Quality: 94.3
```

**Output:**
- `needs_geocoding` flag cleared
- `latitude`, `longitude` updated
- `eircode` enriched (if better Eircode found)
- Quality score logged

### Phase 2: Mapbox (Non-Eircode Properties)

```bash
# Dry run
python3 scripts/geocode_mapbox_batch.py \
  --needs-geocoding \
  --no-eircode \
  --limit 10

# Apply for real
python3 scripts/geocode_mapbox_batch.py \
  --needs-geocoding \
  --no-eircode \
  --apply
```

**Batch processing:**
```
Batch 1: Processing 748 properties...
✓ Success: 563 (75.3%)
✗ Failed: 185

Quality Score Average: 87.2/100
  Rooftop (100): 234 properties
  Parcel (90): 189 properties
  Point (80): 140 properties
```

---

## Expected Outcomes

### Phase 1 (Autoaddress)
- **~2,000 properties** successfully geocoded (90% success rate)
- **~200 properties** failed (rural, incomplete addresses, API issues)
- **200-300 Eircodes** discovered/enriched
- **Average quality score: 92-95/100**

### Phase 2 (Mapbox)
- **~560 properties** successfully geocoded (75% success rate)
- **~190 properties** failed (very rural, poor address data)
- **Average quality score: 85-90/100**

### Combined Results
- **~2,560 properties geocoded** (86% of queue)
- **~400 properties remaining** in queue (need manual review)
- **Total time: ~3 hours**
- **Total cost: ~€5-15** (depending on Autoaddress pricing)

---

## Monitoring

### Check Queue Progress

```sql
-- Properties still needing geocoding
SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE;

-- Breakdown by Eircode availability
SELECT 
    CASE 
        WHEN eircode IS NOT NULL THEN 'Has Eircode'
        ELSE 'No Eircode'
    END as eircode_status,
    COUNT(*) as count
FROM properties
WHERE needs_geocoding = TRUE
GROUP BY eircode_status;

-- Recent geocoding success rate
SELECT 
    COUNT(*) FILTER (WHERE needs_geocoding = FALSE) as geocoded,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE needs_geocoding = FALSE) / COUNT(*), 1) as pct
FROM properties
WHERE sale_date > '2026-04-17';
```

### Quality Analysis

```sql
-- Properties geocoded in last session
SELECT 
    id, address, county, eircode,
    latitude, longitude,
    ST_AsText(geog) as geog_wkt
FROM properties
WHERE needs_geocoding = FALSE
  AND sale_date > '2026-04-17'
ORDER BY id DESC
LIMIT 10;
```

---

## Troubleshooting

### Autoaddress Issues

**HTTP 429 / Rate Limited:**
```bash
# Reduce rate limit in regeocode_autoaddress.py
AA_RATE_LIMIT = 0.5  # 1 request every 2 seconds
```

**HTTP 401 / Authentication Failed:**
```bash
# Check API key in backend/.env
cat backend/.env | grep AUTOADDRESS_KEY

# Verify key format: pub_xxxxx
```

**County Validation Failures:**
- County boundaries are approximate
- Quality score downgraded but not rejected
- Check `county_validator.py` bounding boxes

**Routing Key Rejections:**
- Indicates coordinates >5km from routing key centroid
- This is GOOD - prevents bad geocodes from being imported
- These properties should be manually reviewed

### Mapbox Issues

**No MAPBOX_TOKEN:**
```bash
# Get token from: https://www.mapbox.com/
# Add to backend/.env
echo "MAPBOX_TOKEN=pk.xxxxx" >> backend/.env
```

**Batch Too Large (>1,000):**
```bash
# Limit batch size
python3 scripts/geocode_mapbox_batch.py --limit 1000 --apply
# Run multiple times to process full queue
```

**Low Precision Results:**
- Mapbox returns 'interpolated' or 'approximate' for rural addresses
- These are automatically rejected (quality <70)
- Remaining properties need manual geocoding or Autoaddress fallback

---

## Manual Review Queue

After both phases, ~400 properties will likely remain in queue:

```sql
-- Export for manual review
SELECT id, address, county, eircode, price, sale_date
FROM properties
WHERE needs_geocoding = TRUE
ORDER BY price DESC
LIMIT 100;
```

**Manual geocoding sources:**
1. Eircode Finder: https://finder.eircode.ie
2. Google Maps
3. Property Price Register listings (verify address)
4. OSI Geohive: https://webapps.geohive.ie/

---

## Future Automation

### Daily Geocoding Cron

```bash
# Add to crontab: Geocode 100 properties per day
0 3 * * * cd /path && python3 scripts/regeocode_autoaddress.py --needs-geocoding --with-eircode --apply --limit 100 >> logs/geocoding.log 2>&1
```

At 100/day, queues cleared within 1 month of each PPR sync.

### Integration with Eircode Enrichment

Extend `db/eircode_enrich.py` to also geocode after Eircode enrichment:

```python
if enriched_eircode and needs_geocoding:
    # Geocode using new Eircode
    lat, lon = await geocode_autoaddress(address, county, enriched_eircode)
    if lat and lon:
        await update_coordinates(property_id, lat, lon)
```

---

## Summary

**Hybrid approach combines best of both services:**

| Service | Use For | Success Rate | Speed | Cost |
|---------|---------|--------------|-------|------|
| Autoaddress | Eircode properties (74.8%) | 90% | 2.5 hours | €5-10 |
| Mapbox | Non-Eircode properties (25.2%) | 75% | <1 minute | FREE |
| **Combined** | **All properties** | **86%** | **~3 hours** | **€5-10** |

**Result:** High-quality coordinates with comprehensive validation, clearing 86% of geocoding queue in ~3 hours.
