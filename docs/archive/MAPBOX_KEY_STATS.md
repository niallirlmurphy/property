# Mapbox API Incident - Key Statistics

**Quick reference for discussions with Mapbox support**

---

## Top-Line Numbers

| Metric | Value |
|--------|-------|
| **Total API calls (June 2)** | 488,917 |
| **Expected usage** | 150,000 |
| **Excess usage** | 338,917 |
| **Waste percentage** | 69% |
| **Cost impact (if charged)** | ~€255 @ $0.75/1k |

---

## The Infinite Loop

| Properties | Times Processed | API Calls | Status |
|-----------|-----------------|-----------|---------|
| 4,448 | 41× (Run 2) | 182,368 | ❌ Wasted |
| 4,448 | 35× (Run 3) | 155,680 | ❌ Wasted |
| **Total** | **76 retries** | **338,048** | **69% waste** |

---

## Run-by-Run Breakdown

### Run 1 (15:46 IST) ✅
- Properties: 50,000
- API calls: 50,000  
- Status: Completed successfully
- Duration: ~30 minutes

### Run 2 (16:00 IST) ❌
- Properties: 42,736 initially
- API calls: 248,277
- Breakdown:
  - 42,736 first attempt: 42,736 calls ✓
  - 23,173 second attempt: 23,173 calls ✓
  - 4,448 × 41 retries: 182,368 calls ✗
- Duration: ~1.5 hours until manual stop

### Run 3 (16:40 IST) ❌  
- Properties: 34,960 initially
- API calls: 190,640
- Breakdown:
  - 34,960 first attempt: 34,960 calls ✓
  - 4,448 × 35 retries: 155,680 calls ✗
- Duration: ~1 hour until manual stop

---

## Legitimate vs Wasted Usage

```
Legitimate (unique first attempts):
  Run 1:  50,000 properties = 50,000 calls
  Run 2:  65,909 properties = 65,909 calls  
  Run 3:  34,960 properties = 34,960 calls
  ─────────────────────────────────────────
  Total:  150,869 calls (31%)

Wasted (duplicate retries):
  Run 2:  4,448 × 41 = 182,368 calls
  Run 3:  4,448 × 35 = 155,680 calls
  ─────────────────────────────────────────
  Total:  338,048 calls (69%)

GRAND TOTAL: 488,917 calls
```

---

## Historical Comparison

| Period | API Calls | Purpose | Notes |
|--------|-----------|---------|-------|
| **March 2026** | ~12,000 | New imports | Normal |
| **April 2026** | ~8,000 | Biweekly sync | Normal |
| **May 2026** | ~18,000 | Centroid cleanup | Normal |
| **June 1, 2026** | ~2,000 | Routine operations | Normal |
| **June 2, 2026** | **488,917** | **Bulk run (BUG)** | **24× spike** |
| **June 3-9, 2026** | ~1,500 | Regular operations | Normal |

**Average monthly usage (pre-bug):** 10,000-20,000 requests  
**June 2 spike:** 24× normal monthly usage in one day

---

## Timeline (June 2, 2026)

```
15:46:00  ─ Run 1 starts (50k properties)
16:15:30  ─ Run 1 completes ✓ (50k API calls)

16:00:37  ─ Run 2 starts (42k properties)  
16:00:43  ─ Batch 1 begins
16:08:47  ─ Batch 3 starts infinite loop
17:24:11  ─ Batch 43 still looping
~17:30    ─ Run 2 stopped manually (248k API calls)

16:40:46  ─ Run 3 starts (35k properties)
16:45:33  ─ Immediately enters same loop
~17:45    ─ Run 3 stopped manually (191k API calls)

Total incident duration: ~2 hours
```

---

## The 4,448 Problem Properties

**Why they consistently fail:**
- Interpolated coordinates (Mapbox estimates, not actual location)
- Rural/townland addresses without street numbers
- Incomplete OpenStreetMap data  
- Ambiguous address formats

**Common rejection reasons:**
```
precision_interpolated ─────── 4,200 properties (94%)
feature_type_region ─────────── 180 properties (4%)
county_boundary_violation ────── 68 properties (2%)
```

**Example addresses that failed:**
```
"12A DOUGHISKA RD, DOUGHISKA, GALWAY"
"59 Willow Close, The Orchard, Watergrass"  
"LOWERTOWN, MOUNTBOLUS, BLUEBALL"
"4 LOSSET HALL, BELGARD SQ WEST, TALLAGHT"
```

---

## Evidence Strength

| Evidence Type | Quality | Notes |
|--------------|---------|-------|
| **Log files** | 🟢 Strong | 5,174 lines showing exact repetition |
| **Timestamp data** | 🟢 Strong | Precise timing of each batch |
| **Property counts** | 🟢 Strong | Same 4,448 count 76 times |
| **Source code** | 🟢 Strong | Bug clearly identified |
| **Historical usage** | 🟢 Strong | Proves anomaly |
| **First occurrence** | 🟢 Strong | No pattern of abuse |
| **Immediate action** | 🟢 Strong | Stopped + fixed within hours |

---

## Cost Impact

**If within free tier (100k/month):**
```
Free tier: 100,000 requests/month
June 2 usage: 488,917 requests
Overage: 388,917 requests
Cost: 388,917 / 1,000 × $0.75 = $291.69
```

**If you had existing usage:**
```
Existing usage: 0-10k (normal operations)
Free remaining: 90k-100k
June 2 usage: 488,917
Overage: 388k-398k
Cost: $291-299
```

**Cost of wasted calls specifically:**
```
Wasted calls: 338,048
Cost: 338,048 / 1,000 × $0.75 = $253.54
```

**In EUR (approximate):**
```
Total overage cost: €255-275
Wasted calls only: €230-240
```

---

## Bug Impact Summary

**What broke:**
- Error handling in `geocode_mapbox_batch.py`
- Missing iteration limit in `geocode_bulk_50k.sh`

**What caused the waste:**
- Properties failed validation → stayed flagged
- Wrapper looped until flagged count = 0
- 4,448 properties always failed
- Loop ran until manual stop

**What should have happened:**
- Properties fail validation → mark as unfixable after 3 attempts
- Move on to next properties
- Complete in 30-60 minutes
- Use ~150k API calls

**What actually happened:**
- Properties fail validation → stay flagged forever
- Retry same properties infinitely  
- Run until manual intervention
- Use ~489k API calls (3.3× expected)

---

## Fix Verification

**Changes made:**
1. ✅ Add `geocoding_attempts` counter
2. ✅ Clear flag after 3 failed attempts
3. ✅ Add max iteration limit (100)
4. ✅ Add warning at 50 iterations
5. ✅ Add monitoring for API usage spikes

**Test results:**
```sql
-- Before fix:
SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE;
-- Result: 4,448 (stuck forever)

-- After fix:
SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE;
-- Result: 0 (processed once, marked as unfixable)

SELECT COUNT(*) FROM properties WHERE geocoding_attempts >= 3;
-- Result: 4,448 (marked as exhausted retries)
```

---

## Support Request Summary

**Requesting:**
- Review of ~340k redundant API calls
- Consideration of courtesy credit
- We acknowledge our bug but duplicates provided no value

**Justification:**
1. Same addresses geocoded 40+ times
2. No business value from duplicates
3. Error detected and fixed same day
4. History shows responsible usage
5. First-time occurrence

**Outcome expectations:**
- Best case: 100% credit (~€255)
- Realistic: 50% credit (~€127)
- Worst case: No credit (policy decision)

---

## Quick Facts for Discussion

> "We processed the same 4,448 properties 76 times due to a bug in our 
> error handling logic. This represented 69% of our June 2 usage."

> "Our normal monthly usage is 10-20k requests. June 2 was a 24× spike 
> caused by an infinite loop we stopped within 2 hours."

> "The duplicate calls provided zero business value - Mapbox returned 
> the same failed validation results each time."

> "We've fixed the bug and implemented prevention measures. This was 
> a one-time software error, not a pattern of misuse."

---

**Last updated:** June 9, 2026  
**Files:** 
- Full audit: `MAPBOX_API_AUDIT_JUNE2.md`
- Summary: `MAPBOX_INCIDENT_SUMMARY.md`
- Evidence: `MAPBOX_EVIDENCE.md`  
- Support request: `MAPBOX_SUPPORT_REQUEST.md`
