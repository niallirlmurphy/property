# Batch 6 Enrichment - 2026 Properties

## Target
702 properties from 2026 missing both bedrooms AND property_type fields (3.9% of 2026 sales).

## Priority Order
1. **June 2026** (113 properties, 40.5% missing) - Most recent, highest impact
2. **May 2026** (316 properties, 12.7% missing)
3. **April 2026** (40 properties, 1.3% missing)
4. **March 2026** (75 properties, 1.7% missing)
5. **February 2026** (95 properties, 2.3% missing)
6. **January 2026** (63 properties, 1.8% missing)

## Script
`scripts/enrich_batch6_2026.py`

## Usage

**Test run (5 properties):**
```bash
python3 scripts/enrich_batch6_2026.py --batch-size 5 --rate-limit 8
```

**Small batch (50 properties):**
```bash
python3 scripts/enrich_batch6_2026.py --batch-size 50 --rate-limit 10
```

**Full batch (all 702 properties):**
```bash
# Takes ~2 hours with 10s rate limit
python3 scripts/enrich_batch6_2026.py --batch-size 702 --rate-limit 10
```

**Recommended approach:**
Run in smaller batches to avoid rate limiting:
```bash
# Batch 1: June properties (113)
python3 scripts/enrich_batch6_2026.py --batch-size 113 --rate-limit 10

# Batch 2: May properties (316)  
python3 scripts/enrich_batch6_2026.py --batch-size 316 --rate-limit 10

# Batch 3: Remaining (273)
python3 scripts/enrich_batch6_2026.py --batch-size 273 --rate-limit 10
```

## Expected Results
Based on test run (5 properties):
- **60% fully enriched** (both bedrooms + property_type)
- **40% partially enriched** (one field only)
- **0% failed** (DuckDuckGo search is reliable)

Estimated final coverage after batch 6:
- Current: 80.3% fully enriched (14,342/17,852)
- After batch 6: ~82.7% fully enriched (+421 properties at 60% success rate)

## Rate Limiting
- **10 seconds** between requests recommended
- Avoids DuckDuckGo blocking
- 702 properties = ~2 hours total runtime

## Output
Results saved to: `enrichment_batch6_results_YYYYMMDD_HHMMSS.json`

## Notes
- Script prioritizes most recent sales (June → January)
- Only targets properties missing BOTH fields to maximize impact
- Uses web search (DuckDuckGo) to find property listings
- Updates database in real-time (no manual import needed)
