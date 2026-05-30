# Geocoding Results - May 21, 2026

**Mapbox batch geocoding of 2,963 properties from recent PPR sync**

---

## Summary

**Date:** 2026-05-21  
**Service:** Mapbox Geocoding API (batch)  
**Properties Processed:** 2,963  
**Success Rate:** 70.1% (2,077 properties)  
**Average Quality Score:** 88.8/100

---

## Results Breakdown

### Overall Success
- ✅ **Geocoded:** 2,077 properties (70.1%)
- ❌ **Failed:** 886 properties (29.9%)
- ⏱️ **Time:** ~3 minutes (3 batch API calls)
- 💰 **Cost:** FREE (within 100k/month tier)

### Quality Distribution

| Quality Level | Count | Percentage | Score |
|--------------|-------|------------|-------|
| Rooftop | 1,234 | 59.4% | 100 |
| Point | 203 | 9.8% | 80 |
| Locality | 640 | 30.8% | 70 |

**Quality Score Average:** 88.8/100

### Eircode Analysis

**Properties WITH Eircodes (2,215 total):**
- Geocoded: 1,696 (76.6%)
- Failed: 519 (23.4%)

**Properties WITHOUT Eircodes (748 total):**
- Geocoded: 381 (50.9%)
- Failed: 367 (49.1%)

**Key Insight:** Eircodes improve success rate by 25.7 percentage points (76.6% vs 50.9%)

---

## Validation Applied

All geocoded properties passed the following validations:

### 1. Ireland Bounds Check ✅
```
Latitude: 51.4° to 55.5°N
Longitude: -10.7° to -5.4°W
```
**Result:** 100% within Ireland (0 international false matches)

### 2. Feature Type Validation ✅
**Accepted:**
- `address` with rooftop/parcel/point precision
- `locality` for rural areas
- `place` for townlands

**Rejected:**
- `street` (too imprecise)
- `postcode` (centroid only)
- Interpolated results
- Approximate results

### 3. County Boundary Validation ✅
- Applied to all results
- Downgrades quality score for mismatches
- Does not reject (county boundaries are approximate)

---

## Sample Geocoded Properties

```
SHORNCLIFF, BALLINFULL, SLIGO                      - (54.27133, -8.47331) [Rooftop]
No. 2 Ard Cuan, Ballisodare, Co. Sligo             - (54.21235, -8.51288) [Rooftop]
NO 8, THE MILL TREE, RATOATH                       - (53.50362, -6.46608) [Rooftop]
NEWHAGGARD, TRIM, MEATH                            - (53.54758, -6.83375) [Locality]
MILLTOWNPASS, KINNEGAD, WESTMEATH                  - (53.45480, -7.10131) [Locality]
```

---

## Failure Analysis

### Common Rejection Reasons

**886 properties failed geocoding:**

1. **`feature_type_street`** - Address resolved to street level only (too imprecise)
   - Example: "259 Bothar Mhic Aodh, Magee Quarter"
   - Mapbox returned street coordinates, not building-level

2. **No results returned** - Address not found in Mapbox database
   - Very rural properties
   - Incomplete/malformed addresses
   - New developments not yet in map data

3. **Out of bounds** - Coordinates outside Ireland (rare, ~0%)

### Properties Needing Manual Review

**886 properties remain in queue** (`needs_geocoding = TRUE`)

**Priority order:**
1. High-value (>€500k): ~200 properties
2. Mid-value (€300-500k): ~250 properties  
3. Other (<€300k): ~436 properties

**Recommended action:**
- Export for manual geocoding: `scripts/export_geocoding_queue.py`
- Use Eircode Finder: https://finder.eircode.ie
- Check Property Price Register for address corrections
- Consider Autoaddress validation API for address normalization

---

## Database Impact

### Before Geocoding
- Total recent imports (after 2026-04-17): 2,963
- With coordinates: 0 (0%)
- Without coordinates: 2,963 (100%)

### After Geocoding
- Total recent imports: 2,963
- With coordinates: 2,077 (70.1%)
- Without coordinates: 886 (29.9%)

### Overall Database Stats
- Total properties: 784,464
- With coordinates: ~623,000 (79.4%)
- Properties flagged for geocoding: 886 (down from 2,963)

---

## API Usage

### Mapbox Requests
- **Before:** 67,000/100,000
- **This run:** 2,963 requests
- **After:** 69,963/100,000
- **Remaining:** 30,037 requests

### Cost
- **Free tier:** 100,000 requests/month
- **This batch:** $0 (within free tier)
- **Next month resets to:** 100,000 requests

---

## Next Steps

### 1. Manual Review (Recommended)

Export remaining 886 properties:
```bash
python3 scripts/export_geocoding_queue.py --output manual_review.csv
```

Focus on:
- High-value properties (>€500k) - ~200 properties
- Properties with Eircodes that failed - check for address errors
- Recent sales (more valuable for analytics)

### 2. Retry with Alternative Service

For properties with Eircodes that failed Mapbox:
- Try Nominatim (open-source, different data source)
- Consider paid geocoding services (Google, HERE, TomTom)
- Use Autoaddress validation API to normalize addresses first

### 3. Address Normalization

Run address normalization on failed properties:
```bash
python3 scripts/normalize_addresses.py --needs-geocoding
```

Then retry geocoding with cleaned addresses.

### 4. Monitor Future Syncs

For next PPR sync (biweekly):
- Run Mapbox batch immediately after import
- Expected ~300-500 new properties per sync
- Should maintain 70-80% success rate
- Remaining queue stays manageable (<1,000)

---

## Performance Metrics

### Speed
- **Total time:** ~3 minutes
- **Properties/second:** ~16.5
- **Batch size:** 1,000 per API call
- **Total batches:** 3

### Accuracy
- **Rooftop precision:** 1,234 properties (59.4%)
- **Building-level precision:** 1,437 properties (69.2%)
- **Locality precision:** 640 properties (30.8%)

### Reliability
- **API errors:** 0
- **Validation rejections:** 886 (29.9%)
- **Ireland bounds violations:** 0
- **Database update errors:** 0

---

## Comparison to Original Geocoding

### Original Import (Nominatim)
- Success rate: ~79%
- Quality: Variable (many centroid/locality matches)
- Time: Hours (sequential processing)
- Service: Self-hosted Nominatim

### This Batch (Mapbox)
- Success rate: 70.1%
- Quality: Higher (59.4% rooftop accuracy)
- Time: 3 minutes (batch processing)
- Service: Mapbox cloud API

**Key difference:** Mapbox rejects low-quality results (street-level, interpolated) that Nominatim accepts, resulting in lower success rate but higher quality coordinates.

---

## Recommendations

### Short-term (This Week)
1. ✅ Export 886 failed properties for manual review
2. ✅ Manually geocode high-value properties (>€500k)
3. ✅ Update documentation with lessons learned

### Medium-term (This Month)
1. 🔄 Set up automated biweekly geocoding after each PPR sync
2. 🔄 Implement address normalization pipeline
3. 🔄 Create monitoring dashboard for geocoding queue

### Long-term (Next Quarter)
1. 📋 Evaluate paid geocoding services for remaining difficult addresses
2. 📋 Implement routing key validation for all geocoded properties
3. 📋 Build quality scoring system into search ranking

---

## Conclusion

**Successful batch geocoding of 70.1% of properties** from recent PPR sync using Mapbox API with comprehensive validation.

**Key achievements:**
- ✅ 2,077 properties geocoded with high-quality coordinates
- ✅ Average quality score: 88.8/100
- ✅ 59.4% rooftop-level precision
- ✅ 100% within Ireland bounds
- ✅ Zero cost (within free tier)
- ✅ Completed in 3 minutes

**Remaining work:**
- 886 properties need manual review or alternative geocoding
- Focus on high-value properties first
- Consider address normalization for retry

**Overall impact:** Recent property data now 70% geocoded and fully searchable on homeiq.ie with validated, high-quality coordinates.
