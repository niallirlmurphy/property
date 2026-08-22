# Enrichment Run Status

## Current Run

**Started:** 2026-06-08
**Target:** 8,030 properties from last 3 months
**Output:** `enrichment_full_results.json`

### Settings
- Batch size: 50 properties
- Batch delay: 120 seconds (2 minutes between batches)
- Request delay: 10 seconds (between individual properties)
- Skip already enriched: Yes

### Time Estimate
- **Per property:** ~10 seconds
- **Per batch (50):** ~8-10 minutes
- **Total batches:** ~161 batches
- **Total time:** ~25-35 hours

The script will run continuously and save progress every 10 properties to `enrichment_full_results.json`.

---

## Monitoring Progress

### Check current progress:
```bash
bash scripts/check_enrichment_progress.sh
```

### View live output:
```bash
tail -f enrichment_progress.log
```

### Check results file:
```bash
# Count properties processed
python3 -c "
import json
try:
    with open('enrichment_full_results.json') as f:
        results = json.load(f)
    print(f'Processed: {len(results):,} / 8,030')
    enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
    print(f'Enriched: {len(enriched):,} ({len(enriched)/len(results)*100:.1f}%)')
except FileNotFoundError:
    print('Results file not created yet')
"
```

---

## If Interrupted

The enrichment saves progress every 10 properties. If it stops/crashes, resume with:

```bash
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --output enrichment_full_results.json \
  --batch-size 50 \
  --batch-delay 120 \
  --delay 10 \
  --skip-enriched
```

The `--skip-enriched` flag will skip properties already in the results file.

---

## When Complete

### 1. Review results:
```bash
python3 -c "
import json
with open('enrichment_full_results.json') as f:
    results = json.load(f)
    
total = len(results)
enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
with_bedrooms = sum(1 for r in results if r.get('bedrooms'))
with_type = sum(1 for r in results if r.get('property_type'))

print(f'Total: {total:,}')
print(f'Enriched: {len(enriched):,} ({len(enriched)/total*100:.1f}%)')
print(f'With bedrooms: {with_bedrooms:,}')
print(f'With property type: {with_type:,}')

# Show sample
print('\nSample enriched properties:')
for r in enriched[:5]:
    print(f\"  {r['id']}: {r.get('bedrooms', '?')} bed, {r.get('property_type', '?')}\")
"
```

### 2. Import to database (when online):
```bash
# Dry run first
python3 scripts/import_enrichment_results.py enrichment_full_results.json --dry-run

# Apply updates
python3 scripts/import_enrichment_results.py enrichment_full_results.json
```

---

## Files Generated

- `enrichment_full_results.json` - Main results file (saved every 10 properties)
- `enrichment_progress.log` - Live progress log (use tail -f to watch)
- `recent_3months.csv` - Input file (8,030 properties)

---

## Expected Results

Based on the property mix in your export:

### By Price
- **High-value (>€500k):** 60-90% success
- **Mid-range (€300k-500k):** 50-70% success
- **Lower (<€300k):** 30-50% success

### Overall
- **Target success rate:** 50-70%
- **Expected enriched:** 4,000-5,600 properties
- **With bedrooms:** 3,500-5,000
- **With property type:** 3,500-5,000

---

## Troubleshooting

### Process seems stuck
Check if it's in a batch delay (2 minutes):
```bash
tail -20 enrichment_progress.log
```
Look for "Batch X complete. Waiting 120s..."

### Low success rate (<30%)
- Normal for older/cheaper properties
- Consider focusing on high-value recent sales only

### Getting blocked (HTTP 429 errors)
Stop and increase delays:
```bash
# Kill current run (Ctrl-C or pkill -f enrich_from_csv)
# Resume with longer delays:
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --output enrichment_full_results.json \
  --delay 15 \
  --batch-delay 300 \
  --skip-enriched
```

---

## Progress Milestones

- ✅ **10 properties:** Script working correctly
- ✅ **100 properties:** ~20 minutes, sample results available
- ⏳ **1,000 properties:** ~3 hours
- ⏳ **4,000 properties:** ~12 hours (halfway)
- ⏳ **8,030 properties:** ~30 hours (complete)

Check progress regularly with: `bash scripts/check_enrichment_progress.sh`
