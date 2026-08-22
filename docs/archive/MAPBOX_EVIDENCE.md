# Mapbox API Incident - Visual Evidence

**Quick proof that 500k API calls were caused by a bug, not intentional use.**

---

## The Smoking Gun: Same Properties, 41 Times

From `logs/mapbox_bulk_20260602_160037.log`:

```
16:00:43 - BATCH 1 of 43
           Properties to process: 42,736

16:05:12 - BATCH 2 of 43  
           Properties to process: 23,173
           
16:08:47 - BATCH 3 of 43
           Properties to process: 4,448  ← Stuck here
           
16:11:23 - BATCH 4 of 43
           Properties to process: 4,448  ← Same 4,448
           
16:13:58 - BATCH 5 of 43
           Properties to process: 4,448  ← Same 4,448
           
16:16:34 - BATCH 6 of 43
           Properties to process: 4,448  ← Same 4,448

... [batches 7-42: all processing same 4,448 properties] ...

17:24:11 - BATCH 43 of 43
           Properties to process: 4,448  ← Still same 4,448
```

**4,448 properties × 41 batches = 182,368 API calls on the SAME addresses**

---

## The Numbers Don't Lie

### Expected Behavior
```
50,000 properties × 1 geocoding attempt each = 50,000 API calls
Duration: 30-60 minutes
Result: Some succeed, some fail, all marked as processed
```

### What Actually Happened (June 2)
```
~150,000 unique properties processed
~340,000 duplicate attempts on failed properties  
Duration: 2+ hours
Result: Infinite loop until manual stop
```

### Visual Breakdown

```
Run 1 (15:46)
════════════════════════════════════════════════════
50,000 NEW      [████████████████████████████████████] 50k calls ✓

Run 2 (16:00)  
════════════════════════════════════════════════════
42,736 NEW      [██████████████████████████████] 43k calls ✓
23,173 NEW      [████████████████████] 23k calls ✓
 4,448 RETRY #1 [████] 4k calls
 4,448 RETRY #2 [████] 4k calls
 4,448 RETRY #3 [████] 4k calls
    ... (38 more retries)
 4,448 RETRY #41 [████] 4k calls
                      └─ 182k WASTED calls ✗

Run 3 (16:40)
════════════════════════════════════════════════════
34,960 NEW      [████████████████████████] 35k calls ✓
 4,448 RETRY #1 [████] 4k calls
 4,448 RETRY #2 [████] 4k calls  
    ... (33 more retries)
 4,448 RETRY #35 [████] 4k calls
                      └─ 156k WASTED calls ✗

TOTAL LEGITIMATE:  ████████████████ 151k
TOTAL WASTED:      ████████████████████████████████ 338k
```

---

## Proof It's the Same Properties

### Log Analysis

**Command:**
```bash
grep "Properties to process:" logs/mapbox_bulk_20260602_160037.log
```

**Output (excerpt):**
```
Properties to process: 42,736
Properties to process: 23,173
Properties to process: 4,448
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
Properties to process: 4,448  ← REPEAT
... (continues for 41 total occurrences)
```

**Count verification:**
```bash
$ grep "Properties to process: 4,448" logs/mapbox_bulk_20260602_160037.log | wc -l
41
```

---

## The Properties That Failed

These addresses **consistently fail** Mapbox's geocoding:

```
⚠️ Rejected 12A DOUGHISKA RD, DOUGHISKA, GALWAY: precision_interpolated
   Reason: Only interpolated coordinates available (low quality)
   
⚠️ Rejected 59 Willow Close, The Orchard, Watergrass: precision_interpolated
   Reason: Only interpolated coordinates available (low quality)
   
⚠️ Rejected 4 LOSSET HALL, BELGARD SQ WEST, TALLAGHT: precision_interpolated
   Reason: Only interpolated coordinates available (low quality)

⚠️ Rejected LOWERTOWN, MOUNTBOLUS, BLUEBALL: feature_type_region
   Reason: Only region-level location available (not specific address)
```

**Why they fail:**
- Rural addresses without street numbers
- Townland addressing (Irish system Mapbox struggles with)
- Incomplete OpenStreetMap data
- Ambiguous/outdated address formats

**Why we reject them:**
- Our quality rules require "rooftop", "parcel", or "point" precision
- We don't want to show users wrong property locations
- This validation is CORRECT behavior

**The bug:**
- We should mark unfixable properties as failed after 2-3 attempts
- Instead, we retried them forever

---

## Comparison to Normal Operations

### May 29, 2026 (Working Correctly)

**Command:** 
```bash
python3 scripts/geocode_mapbox_batch.py --centroid --limit 10000 --apply
```

**Result:**
- Properties processed: 10,000
- API calls: 10,000 (1:1 ratio)
- Success rate: 92-97%
- Failed properties: Logged for review, NOT retried
- Duration: ~20 minutes
- Log size: 500 lines

### June 2, 2026 (Bug Triggered)

**Command:**
```bash
./scripts/geocode_bulk_50k.sh
```

**Result:**
- Properties requested: 50,000
- API calls: 488,917 (10:1 ratio) ← **RED FLAG**
- Success rate: Unknown (loop prevented measurement)
- Failed properties: Retried 40+ times
- Duration: 2+ hours until manual stop
- Log size: 5,174 lines (10× normal)

---

## Timeline with Timestamps

```
15:46:00  Run 1 starts
          └─ 50,000 properties queued
15:46:10  Batch processing begins
16:15:30  Run 1 completes ✓
          └─ 50,000 API calls (normal)

16:00:37  Run 2 starts  
          └─ 42,736 properties flagged
16:00:43  Batch 1 processing (42,736 → 23,173)
16:05:12  Batch 2 processing (23,173 → 4,448)
16:08:47  Batch 3 processing (4,448 remains)
16:11:23  Batch 4 processing (4,448 remains)  ← Loop detected
16:13:58  Batch 5 processing (4,448 remains)
          ... [36 more identical batches]
17:24:11  Batch 43 processing (4,448 remains)
~17:30    Run 2 stopped manually
          └─ 248,277 API calls (5× expected)

16:40:46  Run 3 starts
          └─ 34,960 properties flagged
16:40:52  Batch 1 processing (34,960 → 4,448)
16:45:33  Batch 2 processing (4,448 remains)  ← Immediately stuck
          ... [34 more identical batches]
~17:45    Run 3 stopped manually
          └─ 190,640 API calls (5× expected)

Total duration: ~2 hours
Total API calls: 488,917
Wasted: ~69%
```

---

## The Bug in Code

### geocode_mapbox_batch.py (lines 371-386)

```python
for prop_id, lat, lon, quality_score in results:
    if lat and lon and quality_score >= 70:
        success_count += 1
        quality_scores.append(quality_score)
        
        if not dry_run:
            await pool.execute("""
                UPDATE properties
                SET latitude = $1, longitude = $2,
                    geog = ST_MakePoint($2, $1)::geography,
                    needs_geocoding = FALSE    # ← Only cleared on success
                WHERE id = $3
            """, lat, lon, prop_id)
    else:
        failed_count += 1
        # ↑ BUG: Property remains flagged, will retry forever
```

### geocode_bulk_50k.sh (lines 67-82)

```bash
# Check if there are more properties to process
REMAINING=$(python3 << 'EOF'
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE")
print(cur.fetchone()[0])
conn.close()
EOF
)

if [ "$REMAINING" -eq 0 ]; then
    echo "No more properties to geocode. Done!"
    break   # ← Never reached if 4,448 properties always fail
fi

BATCH_NUM=$((BATCH_NUM + 1))  # ← Infinite increment
```

**Result:** Loop continues until manual intervention.

---

## Why This Proves It Was an Error

### ✅ 1. Same Properties, Many Times
- 4,448 properties processed **41 times** in Run 2
- 4,448 properties processed **35 times** in Run 3
- No business reason to retry same addresses hourly

### ✅ 2. Inconsistent with History
- Previous months: 10-20k API calls (careful usage)
- June 2: 488k API calls (10× spike)
- Pattern shows this was anomalous

### ✅ 3. No User Intent
- Scripts ran unattended  
- No monitoring to detect loop
- Stopped only when user checked logs

### ✅ 4. Properties Can't Be Fixed
- Addresses consistently fail validation
- Mapbox data doesn't change hourly
- Retrying provides no value

### ✅ 5. Bug Clearly Identified
- Missing `needs_geocoding = FALSE` for failures
- No iteration limit in wrapper
- Fix is straightforward

---

## What We're Asking

**Mapbox Support Review:**

Given:
- Clear software bug causing infinite loop
- ~340,000 duplicate calls on same addresses
- No business value from the duplicates  
- First-time occurrence
- History of responsible usage
- Immediate corrective action

**Request:**
- Review of charges for redundant API calls
- Consideration of courtesy credit adjustment
- We acknowledge our bug, but duplicate calls provided zero value

---

## Contact Information

**Project:** HomeIQ.ie (Irish Property Price Register)  
**Incident Date:** June 2, 2026  
**Detection:** Same day (within 2 hours)  
**Status:** Bug fixed, prevention measures implemented  

**Supporting Files:**
- `MAPBOX_API_AUDIT_JUNE2.md` - Full technical audit (23 pages)
- `MAPBOX_INCIDENT_SUMMARY.md` - Executive summary (8 pages)  
- `MAPBOX_EVIDENCE.md` - Visual proof (this document)
- Log files available upon request

---

**Bottom line:** 69% of June 2nd API usage was the same 4,448 addresses being geocoded repeatedly due to a software bug. This is clearly an error, not intentional use.
