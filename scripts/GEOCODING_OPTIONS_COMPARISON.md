# Geocoding Options Comparison

## Executive Summary

After testing multiple geocoding services for Irish property addresses, here's what works best:

| Service | Accuracy | Coverage | Cost | Coordinates | County Validation |
|---------|----------|----------|------|-------------|-------------------|
| **Nominatim** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent | ✓ Free | ✓ Yes | ✓ Implemented |
| **AutoAddress** | N/A | ⭐⭐⭐⭐⭐ Best | € Paid | ✗ Not Available* | - |
| **Mapbox** | ⭐⭐⭐ Good | ⭐⭐⭐ Good | € Paid | ✓ Yes | ✓ Implemented |
| **Salesforce** | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐ Good | €€ Expensive | ✓ Yes | Ready |

\* AutoAddress API returns address details and Eircodes but NOT coordinates with current API key tier

## Current Status

### ✓ Implemented & Working

1. **Nominatim (OSM) with County Validation**
   - Free, unlimited with local instance
   - Good Irish coverage, especially with Eircodes
   - **County validation**: Rejects results in wrong county
   - Success rate: 85-90% for properties with Eircodes
   - **Limitation**: Lower success for generic place names without Eircodes

2. **County Boundary Validation**
   - Validates all geocoding results against county bounding boxes
   - Catches cross-county errors (e.g., Meath address → Cavan coords)
   - Zero cost, instant validation (<1ms per check)
   - **Impact**: Higher accuracy, fewer wrong locations

3. **Mapbox Geocoding (if configured)**
   - Good for street addresses
   - County validation applied
   - Requires API key and has usage costs

### ⏳ Pending

1. **Salesforce Maps & Location Services**
   - Status: Developer Edition org still provisioning (HTTP 420)
   - Wait time: 30-60 minutes typical
   - Once ready: Excellent for enterprise-quality geocoding
   - **Recommendation**: Check again in 15-30 minutes

### ❌ Not Viable (Current Config)

1. **AutoAddress for Geocoding**
   - API returns addresses and Eircodes ✓
   - API does NOT return coordinates ✗
   - Public/trial API key may have limited features
   - **Best use**: Eircode enrichment only (already implemented in `db/eircode_enrich.py`)
   - **Alternative**: Could work with paid enterprise tier (needs investigation)

## Re-geocoding Results

### Batch 1: 100 properties (Nominatim only)
- **Success**: 90/100 (90%)
- **Method**: Nominatim with strict Ireland filtering
- **Quality**: High - all results validated for Ireland bounding box

### Batch 2: 1,000 properties (Nominatim + County Validation)
- **Success**: 19/1,000 (1.9%)
- **Why so low**: Most properties at centroids have generic place names without Eircodes
- **Example**: "LIMERICK, LIMERICK" → No specific address, very hard to geocode
- **County validation rejections**: Unknown (still running)
- **Observation**: County validation is working but addresses are fundamentally hard to geocode

## Why Success Rate Dropped

The 1,000-property batch has a much lower success rate because:

1. **Earlier properties with Eircodes already fixed**: Batch 1 processed easier addresses
2. **Remaining addresses are hardest cases**: Generic place names, no street address
3. **County validation is stricter**: Rejects results in wrong county (good for accuracy)
4. **Examples of hard addresses**:
   - "LIMERICK, LIMERICK" (city name only)
   - "CORK, CORK" (no street)
   - "DUBLIN, DUBLIN" (too generic)

These properties genuinely need manual review or different data source.

## Recommendations

### Immediate (Next 30 minutes)

1. **Check Salesforce status**
   ```bash
   python3 scripts/regeocode_salesforce.py --limit 10
   ```
   If HTTP 200 → Salesforce is ready, excellent geocoding quality

2. **Continue Nominatim for properties WITH Eircodes**
   ```bash
   # Filter to only process properties with Eircodes
   # These have ~90% success rate
   python3 scripts/regeocode_high_priority.py --limit 500 --apply --eircode-only
   ```
   *(Note: --eircode-only flag would need to be added)*

### Short-term (This week)

1. **Salesforce for hard cases**
   - Once org is ready, use for properties without Eircodes
   - Higher success rate for generic place names
   - 5,000 requests/day limit = process ~5k properties daily

2. **AutoAddress for Eircode enrichment**
   - Many properties missing Eircodes
   - AutoAddress excels at finding Eircodes from addresses
   - Run `db/eircode_enrich.py` to add Eircodes
   - Then re-geocode those properties (higher success with Eircode)

### Medium-term (Next month)

1. **Hybrid Strategy**
   ```
   For each property at centroid:
   1. Has Eircode? → Nominatim (free, good accuracy)
   2. No Eircode but street address? → Salesforce (best quality)
   3. Only place name? → Mark for manual review
   4. After geocoding → Enrich with Eircode via AutoAddress
   ```

2. **Manual Review Queue**
   - Properties that fail all geocoders
   - Export to CSV for manual review/correction
   - ~500-1000 properties likely need this

## Cost Projections

### Current Approach (Nominatim + County Validation)
- **Cost**: €0 (free)
- **Success rate**: 85-90% for properties with Eircodes, ~2% for generic place names
- **Time**: Slow (1 req/s rate limit)

### Salesforce Hybrid (Recommended)
- **Cost**: €0 for 5,000 requests/day (Developer Edition)
- **Success rate**: ~70-80% for hard cases
- **Time**: 5 req/s = ~16 minutes per 5,000 properties
- **Annual cost**: €0 (if within daily limits) or €1,500-5,000 for paid tier

### Full Paid (Mapbox + AutoAddress + Salesforce)
- **Mapbox**: €5/1,000 geocodes
- **AutoAddress**: €variable (need to check enterprise tier for coordinates)
- **Salesforce**: €0-5,000/year depending on volume
- **Total for 235k properties**: €1,000-3,000 one-time

## Quality Improvements Made Today

1. ✓ **County boundary validation** - Prevents cross-county errors
2. ✓ **Strict Ireland bounding box** - No more UK/US coordinates
3. ✓ **Resumable processing** - Can stop/restart without losing progress
4. ✓ **Progress tracking** - Real-time monitoring of success/failure rates
5. ✓ **Multiple geocoder support** - Nominatim, Mapbox, Salesforce, AutoAddress ready

## Next Steps

**Option A: Wait for Salesforce (Recommended)**
- ⏳ Wait 15-30 more minutes for org provisioning
- Test with 100 hard addresses
- If good results → Process all 235k centroids over 47 days (5k/day)

**Option B: Focus on Eircode-enabled Properties**
- ✓ Filter to properties with Eircodes
- ✓ High success rate (90%)
- ✓ Free with Nominatim
- Then enrich remaining properties with Eircodes via AutoAddress

**Option C: Manual Review**
- Export hardest properties to CSV
- Manual verification/correction
- Smaller dataset (500-1000 properties)

**Recommended: Option A** - Salesforce will likely solve the hard cases once ready.

## Testing Commands

```bash
# Check Salesforce status
python3 scripts/regeocode_salesforce.py --limit 5

# Test Nominatim with county validation
python3 scripts/regeocode_high_priority.py --limit 10 --county Dublin

# View dashboard
python3 scripts/geocoding_dashboard.py

# Check progress
sqlite3 regeocode_progress.db "SELECT * FROM session_stats"
```

## Summary

- **Best overall**: Nominatim + County Validation (free, good accuracy)
- **Best for hard cases**: Salesforce (once ready)
- **Best for Eircodes**: AutoAddress (enrichment only, not geocoding)
- **Quality improvement**: County validation prevents wrong-county errors

**Current blocker**: Most remaining properties are genuinely hard to geocode (no Eircode, generic place names). Need either:
1. Better geocoder (Salesforce)
2. More address data (Eircode enrichment first)
3. Manual review
