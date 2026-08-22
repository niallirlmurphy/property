# Offline Batch Enrichment Guide

Run batch enrichment **without database connectivity**. Results are saved to a local JSON file that you can upload manually later.

## Quick Start (Test Run)

Test with 10 sample properties immediately:

```bash
cd /Users/nmurphy/claude/property\ price\ project

# Run enrichment on sample data (10 properties, should take ~5 minutes)
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input_sample.json \
  --batch-size 10 \
  --batch-delay 60
```

**What happens:**
- Searches Google → Daft.ie → MyHome.ie for each property
- Rate limited: 4-5 seconds between requests
- Saves results to `enrichment_results_TIMESTAMP.json`
- No database required!

## Full Production Run

### Step 1: Create Input File (when you have database access)

```bash
# Export 500 recent high-value properties
python3 scripts/create_enrichment_input.py --months 3 --limit 500

# Or customize:
python3 scripts/create_enrichment_input.py \
  --months 6 \
  --limit 1000 \
  --min-price 300000 \
  --output my_properties.json
```

This creates `enrichment_input.json` with properties needing enrichment.

### Step 2: Run Offline Enrichment (no database needed)

```bash
# Standard batch: 50 properties per batch, 3-minute pauses
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input.json \
  --batch-size 50 \
  --batch-delay 180

# Conservative (safer, slower): 25 per batch, 5-minute pauses
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input.json \
  --batch-size 25 \
  --batch-delay 300

# Aggressive (faster, higher risk of blocking): 100 per batch, 2-minute pauses
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input.json \
  --batch-size 100 \
  --batch-delay 120
```

**Time estimates (for 500 properties):**
- **Standard (50/180s):** ~3 hours
- **Conservative (25/300s):** ~5 hours
- **Aggressive (100/120s):** ~2 hours

### Step 3: Upload Results to Database (when connectivity restored)

The script provides upload code in its final output. Example:

```bash
python3 -c "
import psycopg2, json, os
from dotenv import load_dotenv

load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

with open('enrichment_results_20260606_105230.json', 'r') as f:
    results = json.load(f)

updated = 0
for r in results:
    if r['bedrooms'] or r['property_type']:
        cur.execute('''
            UPDATE properties
            SET bedrooms = %s, property_type = %s
            WHERE id = %s
        ''', (r['bedrooms'], r['property_type'], r['id']))
        updated += 1

conn.commit()
print(f'✅ Updated {updated} properties in database')
conn.close()
"
```

## Output File Format

Results are saved as JSON:

```json
[
  {
    "id": 123,
    "address": "12 Fitzwilliam Square",
    "county": "Dublin",
    "price": 850000,
    "bedrooms": 4,
    "property_type": "terraced",
    "source": "google",
    "enriched_at": "2026-06-06T10:52:30.123456"
  },
  {
    "id": 124,
    "address": "45 Merrion Road",
    "county": "Dublin",
    "price": 725000,
    "bedrooms": null,
    "property_type": "semi-detached",
    "source": "daft",
    "enriched_at": "2026-06-06T10:52:45.789012"
  }
]
```

## Monitoring Progress

The script prints real-time progress:

```
================================================================================
BATCH 1: Processing properties 1-50
================================================================================

[1/500] 12 Fitzwilliam Square, Dublin (€850,000)
  ✅ Found: 4 bed, terraced (via google)

[2/500] 45 Merrion Road, Dublin (€725,000)
  ✅ Found: semi-detached (via daft)

[3/500] 8 Monastery Walk, Dublin (€425,000)
  ❌ No data found

...

================================================================================
Batch 1 complete: 37/50 enriched
================================================================================

💾 Saved 50 results to enrichment_results_20260606_105230.json

⏸️  Waiting 180s before next batch...
```

## Success Rate Expectations

**Expected success rate: 30-60%**

- **Google:** ~20-30% (best for addresses with unique keywords)
- **Daft.ie:** ~15-25% (good for recent listings)
- **MyHome.ie:** ~10-20% (backup source)

**Factors affecting success:**
- ✅ Recent sales (last 1-2 years)
- ✅ High-value properties (>€300k)
- ✅ Urban areas (Dublin, Cork, Galway)
- ✅ Unique/distinctive addresses
- ❌ Old sales (pre-2020)
- ❌ Rural/generic addresses
- ❌ Low-value properties

## Strategy & Best Practices

### Batch Sizing
- **Small batches (25-50):** Lower detection risk, spreads load
- **Large batches (100+):** Faster but higher blocking risk
- **Recommendation:** Start with 50, adjust based on success rate

### Delay Between Batches
- **3 minutes (180s):** Standard, balanced approach
- **5 minutes (300s):** Conservative, safer for long runs
- **2 minutes (120s):** Aggressive, use if success rate is high

### Multi-Session Strategy
For large datasets (1000+ properties):

1. **Session 1:** 500 properties over 3 hours
2. **Wait:** 6-12 hours (different time of day)
3. **Session 2:** Next 500 properties
4. **Repeat:** Until complete

This mimics human browsing patterns better than one long session.

### IP Rotation
If you have access to different networks:
- Run some batches on home WiFi
- Run some batches on mobile hotspot
- Reduces blocking risk

## Troubleshooting

### "No data found" for most properties
- Try smaller batches (25 instead of 50)
- Increase delay (300s instead of 180s)
- Wait 12-24 hours and try again
- Consider different time of day

### HTTP errors (429, 403)
- You've been rate limited or blocked
- **Stop immediately** (Ctrl+C)
- Wait 12-24 hours
- Resume with smaller batches and longer delays

### Script crashes
- Results are saved after each batch
- Find latest `enrichment_results_*.json`
- Remove already-processed properties from input file
- Resume with remaining properties

### Network timeout errors
- Normal for occasional failures
- Script handles timeouts gracefully
- Only concern if >50% of requests timeout

## Resuming Interrupted Runs

If script stops mid-run:

```bash
# 1. Find your latest results file
ls -lt enrichment_results_*.json | head -1

# 2. Check how many completed
python3 -c "
import json
with open('enrichment_results_20260606_105230.json') as f:
    results = json.load(f)
print(f'Completed: {len(results)} properties')
"

# 3. Create new input with remaining properties
python3 -c "
import json

# Load original input
with open('enrichment_input.json') as f:
    all_props = json.load(f)

# Load completed results
with open('enrichment_results_20260606_105230.json') as f:
    results = json.load(f)

completed_ids = {r['id'] for r in results}
remaining = [p for p in all_props if p['id'] not in completed_ids]

# Save remaining
with open('enrichment_input_remaining.json', 'w') as f:
    json.dump(remaining, f, indent=2)

print(f'Remaining: {len(remaining)} properties')
"

# 4. Resume with remaining properties
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input_remaining.json \
  --batch-size 50 \
  --batch-delay 180
```

## Expected Results (500 properties)

**Optimistic (50% success):**
- 250 properties enriched
- Mix of bedrooms + property type
- ~3 hours runtime

**Realistic (35% success):**
- 175 properties enriched
- Some with bedrooms only, some with type only
- ~3 hours runtime

**Conservative (20% success):**
- 100 properties enriched
- Mostly property type (easier to extract)
- ~3 hours runtime

## Advantages of Offline Mode

✅ **No database required** - run anywhere, anytime
✅ **Resumable** - results saved after each batch
✅ **Verifiable** - inspect results before uploading
✅ **Safe** - no risk of corrupting database
✅ **Flexible** - run on different machines/networks
✅ **Portable** - JSON files easy to transfer

## Files Created

- `enrichment_input.json` - Properties to enrich (input)
- `enrichment_results_TIMESTAMP.json` - Enrichment results (output)
- `enrichment_input_sample.json` - Test data (10 properties)

## Next Steps After Enrichment

1. **Review results:**
   ```bash
   python3 -c "
   import json
   with open('enrichment_results_*.json') as f:
       results = json.load(f)
   
   total = len(results)
   with_bedrooms = sum(1 for r in results if r['bedrooms'])
   with_type = sum(1 for r in results if r['property_type'])
   with_both = sum(1 for r in results if r['bedrooms'] and r['property_type'])
   
   print(f'Total: {total}')
   print(f'With bedrooms: {with_bedrooms} ({with_bedrooms/total*100:.1f}%)')
   print(f'With type: {with_type} ({with_type/total*100:.1f}%)')
   print(f'With both: {with_both} ({with_both/total*100:.1f}%)')
   "
   ```

2. **Upload to database** (when connectivity restored)
   - Use upload code from script output
   - Or use your own upload method

3. **Verify in production:**
   ```bash
   # Check search results show bedroom/type data
   curl "https://eloquent-optimism-production-350a.up.railway.app/search?q=Dublin&radius=5"
   ```

4. **Continue with next batch** (if needed)
   - Export next 500 properties
   - Wait 12-24 hours
   - Run enrichment again
