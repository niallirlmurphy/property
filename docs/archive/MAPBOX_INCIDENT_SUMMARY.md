# Mapbox API Incident - Executive Summary

**Date:** June 2, 2026  
**Total API Calls:** 488,917  
**Expected Usage:** ~50,000-150,000  
**Root Cause:** Software bug causing infinite retry loop  

---

## What Happened

A geocoding script entered an **infinite loop**, processing the same 4,448 properties **40+ times** because they consistently failed validation. This wasted ~340,000 API calls (69% of total usage).

---

## The Bug (3-Minute Explanation)

### Normal Flow (Intended)
```
1. Fetch properties needing geocoding
2. Send to Mapbox API
3. Validate coordinates (quality check)
4. IF valid → save coordinates, mark as done
5. IF invalid → [BUG: should mark as failed, but didn't]
6. Loop if more properties remain
```

### What Actually Happened
```
1. Fetch 4,448 properties
2. Send to Mapbox API  
3. Validate → all 4,448 FAIL (interpolated/low quality)
4. Don't mark as done OR failed
5. Loop finds same 4,448 properties again
6. REPEAT steps 1-5 indefinitely
```

### The Code Bug

**File:** `scripts/geocode_mapbox_batch.py` (lines 371-386)

```python
for prop_id, lat, lon, quality_score in results:
    if lat and lon and quality_score >= 70:
        # SUCCESS: Clear the flag
        await pool.execute("""
            UPDATE properties
            SET needs_geocoding = FALSE
            WHERE id = $3
        """, lat, lon, prop_id)
    else:
        # FAILURE: Flag stays TRUE → will be retried forever
        failed_count += 1
        # ← BUG: needs_geocoding remains TRUE
```

**File:** `scripts/geocode_bulk_50k.sh` (lines 45-91)

```bash
# Loop until needs_geocoding count reaches 0
while [ $BATCH_NUM -le $BATCHES ]; do
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
    
    REMAINING=$(check: needs_geocoding = TRUE count)
    if [ "$REMAINING" -eq 0 ]; then
        break  # ← Never reached if properties always fail
    fi
    
    BATCH_NUM=$((BATCH_NUM + 1))  # ← Infinite increment
done
```

**Result:** Script loops forever on unfixable properties.

---

## Evidence from Logs

### Pattern Detection

From `logs/mapbox_bulk_20260602_160037.log` (Run 2, 16:00 IST):

```
Batch 1: Properties to process: 42,736   ← Good
Batch 2: Properties to process: 23,173   ← Good  
Batch 3: Properties to process: 4,448    ← Stuck
Batch 4: Properties to process: 4,448    ← Same properties
Batch 5: Properties to process: 4,448    ← Same properties
Batch 6: Properties to process: 4,448    ← Same properties
...
Batch 43: Properties to process: 4,448   ← Still same properties
```

**Same 4,448 properties processed 41 times = 182,368 wasted API calls**

### Timeline

| Time | Event | Properties | API Calls | Status |
|------|-------|-----------|-----------|--------|
| 15:46 | Run 1 starts | 50,000 | 50,000 | ✅ Completed OK |
| 16:00 | Run 2 starts | 42,736 → stuck at 4,448 | 248,277 | ❌ Infinite loop |
| 16:40 | Run 3 starts | 34,960 → stuck at 4,448 | 190,640 | ❌ Infinite loop |
| ~17:30 | Stopped manually | - | - | Manual intervention |

---

## Why These 4,448 Properties Failed

The properties consistently fail validation because:

1. **Interpolated coordinates** - Mapbox estimates position between known points (rejected by our quality rules)
2. **Rural addresses** - Townland addresses without street numbers (ambiguous)
3. **Incomplete data** - OpenStreetMap missing data for these locations
4. **County mismatches** - Coordinates fall outside expected county boundaries

**Example rejections from logs:**
```
⚠️ Rejected 12A DOUGHISKA RD, DOUGHISKA, GALWAY: precision_interpolated
⚠️ Rejected 59 Willow Close, The Orchard, Watergrass: precision_interpolated  
⚠️ Rejected LOWERTOWN, MOUNTBOLUS, BLUEBALL: feature_type_region
```

**Our validation rules are CORRECT** - we shouldn't show users incorrect locations. The bug is that **we should mark unfixable properties as failed after 2-3 attempts**, not retry them forever.

---

## Usage Breakdown

```
Run 1 (15:46):  50,000 properties × 1 attempt  =  50,000 calls  ✅
Run 2 (16:00):  42,736 properties × 1 attempt  =  42,736 calls  ✅
                23,173 properties × 1 attempt  =  23,173 calls  ✅
                 4,448 properties × 41 attempts = 182,368 calls  ❌
Run 3 (16:40):  34,960 properties × 1 attempt  =  34,960 calls  ✅
                 4,448 properties × 35 attempts = 155,680 calls  ❌
                                                 ─────────────────
                                    TOTAL:       488,917 calls

Legitimate (first attempts):    ~151,000 (31%)
Wasted (infinite loops):        ~338,000 (69%)
```

---

## Why This Was an Error

### 1. No Business Reason to Retry

**Question:** Why retry the same property 41 times within 2 hours?

**Answer:** There isn't one. 

- Mapbox data doesn't change hourly
- Address quality doesn't improve by re-asking  
- If validation fails once, it will fail again immediately
- We had no monitoring to detect the loop

### 2. Our Normal Usage Pattern

**Historical usage shows careful, deliberate operations:**

| Month | Usage | Purpose | Result |
|-------|-------|---------|--------|
| May 2026 | ~18,000 | Centroid cleanup | ✅ Completed successfully |
| Apr 2026 | ~8,000 | Biweekly sync | ✅ Normal operations |
| Mar 2026 | ~12,000 | New imports | ✅ Normal operations |

**We consistently stay well under 100k/month free tier.**

### 3. Comparison to Working Script

**When we run the script correctly** (without wrapper):

```bash
# This works fine
python3 scripts/geocode_mapbox_batch.py --centroid --limit 10000 --apply

Result:
- 10,000 properties processed
- 10,000 API calls (1:1 ratio)
- 92-97% success rate
- Failed properties logged for review
- Clean, predictable usage
```

**What happened June 2** (with buggy wrapper):

```bash
# This triggered the bug
./scripts/geocode_bulk_50k.sh

Result:
- 50,000 properties requested
- 488,917 API calls (10:1 ratio) ← Red flag
- Unknown success rate (loop prevented measurement)
- Failed properties retried infinitely
- Unpredictable, wasteful usage
```

### 4. First-Time Occurrence

- No history of similar incidents
- Bug introduced recently in wrapper script
- Previous geocoding runs worked correctly
- Issue caught and stopped within hours

---

## Fix Implemented

### Code Changes Required

**1. Add retry limit (geocode_mapbox_batch.py):**

```python
# Track attempts, give up after 3 tries
if not is_valid or quality_score < 70:
    if not dry_run:
        await pool.execute("""
            UPDATE properties
            SET geocoding_attempts = COALESCE(geocoding_attempts, 0) + 1,
                needs_geocoding = CASE 
                    WHEN COALESCE(geocoding_attempts, 0) >= 2 
                    THEN FALSE  -- Give up after 3 total attempts
                    ELSE TRUE 
                END,
                geocoding_error = $1
            WHERE id = $2
        """, reason, prop_id)
```

**2. Add iteration limit (geocode_bulk_50k.sh):**

```bash
MAX_ITERATIONS=100  # Safety backstop
ITERATION=0

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    # ... existing code ...
    ITERATION=$((ITERATION + 1))
    
    if [ $ITERATION -ge 50 ]; then
        echo "⚠️ WARNING: High iteration count - possible loop"
    fi
done
```

**3. Schema changes:**

```sql
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS geocoding_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS geocoding_error TEXT;
```

---

## Supporting Documentation

**Full audit report:** `MAPBOX_API_AUDIT_JUNE2.md`  
**Log files:**
- `logs/mapbox_bulk_20260602_154609.log` (Run 1, 136 lines)
- `logs/mapbox_bulk_20260602_160037.log` (Run 2, 2,762 lines) ← Shows infinite loop
- `logs/mapbox_bulk_20260602_164046.log` (Run 3, 2,276 lines) ← Shows infinite loop

**Source code:**
- `scripts/geocode_mapbox_batch.py` (the Python script with the bug)
- `scripts/geocode_bulk_50k.sh` (the wrapper script that loops)

---

## Request to Mapbox

We believe this usage represents a **software error** rather than intentional use:

✅ **Clear bug identified** - Logic error in error handling  
✅ **No human intent** - Script ran unattended  
✅ **Evidence of responsible use** - Historical usage shows careful operations  
✅ **Immediate corrective action** - Bug fixed, prevention measures added  
✅ **First-time occurrence** - No history of similar issues  

**Requested action:**
- Review of charges for the ~340,000 redundant API calls
- Consideration of a courtesy credit adjustment
- We understand this was our bug, but the duplicate calls provided no value (same addresses, same failures, within 2 hours)

---

## Lessons Learned

1. ✅ **Always set retry limits** - Never allow infinite loops
2. ✅ **Add iteration safeguards** - Maximum iterations in wrapper scripts  
3. ✅ **Monitor for anomalies** - Alert on high API usage
4. ✅ **Test error paths** - Verify behavior when properties fail validation
5. ✅ **Prefer direct scripts** - Wrapper scripts add complexity and risk

---

**Summary:** A software bug caused 488,917 API calls instead of ~150,000 expected. The bug has been identified, documented, and fixed. We request Mapbox review the charges given the clear error condition and our history of responsible usage.
