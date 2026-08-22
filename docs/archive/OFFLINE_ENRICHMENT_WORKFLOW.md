# Offline Property Enrichment Workflow

Complete workflow for enriching properties when offline or without direct database access.

## Overview

This workflow allows you to:
1. Export properties from Supabase (via browser UI or script)
2. Enrich them offline by scraping property listing sites
3. Store results in a local JSON file
4. Import results back to database when online

## Step 1: Export Properties

### Option A: Using the export script (when online)
```bash
# Export last 3 months
python3 scripts/export_recent_properties_final.py --months 3 --output recent_3months.csv

# Export last 6 months
python3 scripts/export_recent_properties_final.py --months 6 --output recent_6months.csv

# Export specific date range
python3 scripts/export_recent_properties_final.py --since 2026-01-01 --output 2026_properties.csv

# Export with limit (for testing)
python3 scripts/export_recent_properties_final.py --months 3 --limit 100 --output test_export.csv
```

### Option B: Via Supabase SQL Editor
```sql
-- Export as CSV using the download button
SELECT
    id, sale_date, address, address_normalized, county,
    eircode, routing_key, price, not_full_market_price,
    vat_exclusive, description, size_description,
    latitude, longitude, needs_geocoding, geocode_quality_issue,
    bedrooms, property_type
FROM properties
WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
ORDER BY sale_date DESC;
```

**Note:** Supabase UI limits to ~1000 rows. For larger exports, use the script or psql.

---

## Step 2: Enrich Properties

Run the enrichment script on your exported CSV:

```bash
# Test run (first 20 properties)
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --output enrichment_test.json \
  --limit 20 \
  --delay 10

# Full run (recommended settings)
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --output enrichment_results.json \
  --batch-size 50 \
  --batch-delay 120 \
  --delay 10 \
  --skip-enriched

# Fast run (higher rate, risk of blocking)
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --delay 5 \
  --batch-size 100
```

### Parameters:
- `--input`: CSV file to enrich
- `--output`: JSON file to save results (default: `enrichment_results_TIMESTAMP.json`)
- `--limit`: Process only first N properties (for testing)
- `--batch-size`: Properties per batch before long break (default: 50)
- `--batch-delay`: Seconds to wait between batches (default: 120)
- `--delay`: Seconds between individual requests (default: 10)
- `--skip-enriched`: Skip properties that already have bedroom/type data

### What it does:
1. Loads properties from CSV
2. For each property without bedroom/type data:
   - Searches DuckDuckGo for property listings
   - Falls back to Google if needed
   - Extracts bedroom count and property type
   - Adds 10-second delay between requests (to avoid blocking)
3. Saves results to JSON after every 10 properties
4. Shows progress and statistics

### Expected success rate:
- High-value properties (>€500k): 60-90%
- Recent sales (2024+): 50-80%
- Older sales: 20-50%

### Time estimates:
- 100 properties: ~20 minutes
- 500 properties: ~2 hours
- 1,000 properties: ~4 hours
- 8,000 properties: ~32 hours (run overnight/weekend)

---

## Step 3: Review Results

Check the JSON output:

```bash
# View summary
python3 -c "
import json
with open('enrichment_results.json') as f:
    results = json.load(f)
    enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
    print(f'Total: {len(results)}')
    print(f'Enriched: {len(enriched)} ({len(enriched)/len(results)*100:.1f}%)')
    print(f'With bedrooms: {sum(1 for r in results if r.get('bedrooms'))}')
    print(f'With type: {sum(1 for r in results if r.get('property_type'))}')
"

# View first 10 enriched properties
python3 -c "
import json
with open('enrichment_results.json') as f:
    results = json.load(f)
    enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
    for r in enriched[:10]:
        print(f\"{r['id']}: {r.get('bedrooms', '?')} bed, {r.get('property_type', '?')} - {r.get('address', '')[:50]}\")
"
```

---

## Step 4: Import Results to Database

When you're back online:

```bash
# Dry run (show what would be updated)
python3 scripts/import_enrichment_results.py enrichment_results.json --dry-run

# Apply updates
python3 scripts/import_enrichment_results.py enrichment_results.json
```

The import script:
- Only updates properties that don't already have data
- Shows progress every 100 properties
- Commits all changes at once (atomic)
- Shows final database statistics

---

## Resuming Interrupted Enrichment

If enrichment is interrupted (network issues, ctrl-C, etc.):

```bash
# Results are saved every 10 properties, so you can resume:
python3 scripts/enrich_from_csv.py \
  --input recent_3months.csv \
  --output enrichment_results.json \
  --skip-enriched  # This skips already enriched properties
```

The `--skip-enriched` flag will skip any properties that already have bedroom or property_type data in the CSV.

---

## Output Format

### Enrichment Results JSON
```json
[
  {
    "id": "123456",
    "address": "1 Main Street",
    "county": "Dublin",
    "price": "450000",
    "bedrooms": 3,
    "property_type": "terraced",
    "enrichment_source": "duckduckgo",
    "enriched_at": "2026-06-08T14:30:00"
  },
  {
    "id": "123457",
    "address": "2 Park Avenue",
    "county": "Cork",
    "price": "380000",
    "bedrooms": null,
    "property_type": "apartment",
    "enrichment_source": "google",
    "enriched_at": "2026-06-08T14:30:15"
  }
]
```

---

## Rate Limiting & Best Practices

### Recommended Settings
- **Small batch (test):** `--limit 20 --delay 10`
- **Medium batch:** `--batch-size 50 --batch-delay 120 --delay 10`
- **Large batch (overnight):** `--batch-size 100 --batch-delay 300 --delay 15`

### Why Rate Limiting Matters
- DuckDuckGo: Generally permissive, but may block on excessive requests
- Google: More aggressive blocking, hence the delay
- 10 seconds between requests = 360 requests/hour (safe)
- 5 seconds = 720/hour (riskier)

### If You Get Blocked
1. Stop the script (Ctrl-C)
2. Wait 1-2 hours
3. Resume with `--skip-enriched` flag
4. Increase delays: `--delay 15 --batch-delay 300`

---

## Troubleshooting

### "No data found" for most properties
- **Cause:** Old properties may not have active listings
- **Solution:** Focus on recent sales (last 6-12 months)

### Connection timeouts
- **Cause:** Network issues or blocking
- **Solution:** 
  - Increase `--delay` to 15-20 seconds
  - Use VPN if consistently blocked
  - Try different times of day

### Low success rate (<30%)
- **Cause:** Property addresses are hard to find
- **Solution:**
  - Filter by price (>€200k have better listing coverage)
  - Focus on Dublin/Cork/Galway (better online presence)
  - Check if addresses are normalized

### Script crashes
- **Cause:** Invalid CSV format or missing columns
- **Solution:** Re-export using `export_recent_properties_final.py`

---

## Alternative: Use Existing Offline Script

For properties already in JSON format:

```bash
python3 scripts/enrich_offline_batch.py \
  --input enrichment_input.json \
  --batch-size 50 \
  --batch-delay 180
```

This uses the same enrichment logic but expects JSON input:
```json
[
  {"id": 123, "address": "1 Main St", "county": "Dublin", "price": 450000},
  {"id": 124, "address": "2 Park Ave", "county": "Cork", "price": 380000}
]
```

---

## Integration with PPR Sync

The biweekly PPR sync (`scripts/sync_ppr_updates.py`) automatically enriches recent properties. To manually enrich after a sync:

```bash
# 1. Export recent unprocessed properties
python3 scripts/export_recent_properties_final.py --months 1 --output latest_month.csv

# 2. Enrich
python3 scripts/enrich_from_csv.py --input latest_month.csv --skip-enriched

# 3. Import results
python3 scripts/import_enrichment_results.py enrichment_results_*.json
```

---

## Expected Results

### By Price Range
| Price Range | Success Rate |
|-------------|--------------|
| €500k+      | 70-90%       |
| €300k-500k  | 50-70%       |
| €200k-300k  | 40-60%       |
| <€200k      | 20-40%       |

### By Location
| Area       | Success Rate |
|------------|--------------|
| Dublin     | 70-85%       |
| Cork       | 60-75%       |
| Galway     | 55-70%       |
| Other      | 40-60%       |

### By Age
| Sale Date  | Success Rate |
|------------|--------------|
| 2024+      | 70-85%       |
| 2022-2023  | 50-70%       |
| 2020-2021  | 30-50%       |
| <2020      | 20-40%       |

---

## Files Generated

- `recent_3months.csv` - Exported properties (input)
- `enrichment_results_TIMESTAMP.json` - Enriched data (output)
- `enrichment_test.json` - Test run results

Keep these files for:
- Debugging enrichment issues
- Re-running imports if needed
- Auditing what was enriched
