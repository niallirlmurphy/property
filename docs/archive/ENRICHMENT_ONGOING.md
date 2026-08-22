# Property Enrichment - Ongoing Backward Process

**Strategy:** Enrich properties backward in time, 3 months at a time, while success rate remains high  
**Started:** June 10, 2026  
**Status:** ✅ Batch 1 complete, ⏳ Batch 2 running  

---

## Enrichment Strategy

**Goal:** Add bedroom count and property type to as many properties as possible

**Method:**
- Start with most recent properties (higher chance of online listings)
- Work backward in 3-month batches
- Continue as long as success rate stays above 90%
- Stop when success rate drops significantly (older properties have fewer online listings)

**Source:** DuckDuckGo search for property listings (with Google fallback)

---

## Batch 1: Complete ✅

**Date Range:** March 8 - May 22, 2026 (2.5 months)  
**Status:** ✅ COMPLETE

**Results:**
- Properties processed: 7,882
- Successfully enriched: 7,784 (98.8% success rate)
- Imported to database: ✅ June 10, 2026
- Time taken: ~25 hours

**Database Impact:**
- Bedrooms added: 6,663 properties (0.8% of database)
- Property types added: 7,923 properties (1.0% of database)

**Files:**
- Input: `enrichment_input_sample.json`
- Results: `enrichment_full_results.json` (5.3 MB)
- Log: `enrichment_progress.log` (939 KB)

---

## Batch 2: Running ⏳

**Date Range:** December 7, 2025 - March 7, 2026 (3 months)  
**Status:** ⏳ RUNNING  
**Started:** June 10, 2026 13:34

**Target:**
- Properties to process: 14,450
- Expected success rate: 95-98% (similar period to batch 1)
- Estimated time: ~40 hours (1.7 days)
- Expected completion: June 12, 2026

**Progress Tracking:**
```bash
# Check progress
python3 -c "
import json
try:
    with open('enrichment_batch2_results.json') as f:
        results = json.load(f)
    print(f'Processed: {len(results):,} / 14,450')
    enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
    print(f'Success rate: {len(enriched)/len(results)*100:.1f}%')
except FileNotFoundError:
    print('Not started yet')
"

# View live progress
tail -f enrichment_batch2_progress.log
```

**Files:**
- Input: `enrichment_batch2_input.csv` (14,450 properties)
- Results: `enrichment_batch2_results.json` (writing in progress)
- Log: `enrichment_batch2_progress.log`
- PID: 85521

**Settings:**
- Batch size: 50 properties
- Batch delay: 120 seconds (2 minutes between batches)
- Request delay: 10 seconds (between properties)
- Search provider: DuckDuckGo (Google fallback)

---

## Planned Batches

### Batch 3: September 7 - December 6, 2025

**To run after Batch 2 completes:**
- Date range: 3 months before batch 2
- Expected properties: ~13,000-15,000
- Expected time: ~35-40 hours

**Command to prepare:**
```bash
# Find oldest enriched date and create next batch
python3 << 'EOF'
import asyncio, asyncpg, os
from datetime import timedelta
async def next_batch():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    oldest = await conn.fetchval("SELECT MIN(sale_date) FROM properties WHERE bedrooms IS NOT NULL OR property_type IS NOT NULL")
    end_date = oldest - timedelta(days=1)
    start_date = end_date - timedelta(days=90)
    print(f"Next batch: {start_date} to {end_date}")
    await conn.close()
asyncio.run(next_batch())
EOF
```

### Batch 4: June 8 - September 6, 2025

**Projected:**
- Date range: 3 months before batch 3
- Expected properties: ~14,000
- Expected time: ~40 hours

### Continue until...

**Stop criteria:**
- Success rate drops below 90%
- Processing time becomes inefficient
- Very old properties (2010-2015) unlikely to have online listings

**Expected final coverage:**
- Best coverage: 2022-2026 (90-95% enriched)
- Good coverage: 2020-2021 (70-80% enriched)
- Moderate: 2018-2019 (50-70% enriched)
- Limited: Pre-2018 (20-50% enriched)

---

## Process Details

### How Enrichment Works

1. **Export from database:** Properties in date range without bedroom/type data
2. **Web search:** DuckDuckGo search for property address + "for sale" or "sold"
3. **Extract data:** Parse bedroom count and property type from listings
4. **Retry logic:** Try Google if DuckDuckGo fails
5. **Rate limiting:** 10 seconds between requests to avoid blocks
6. **Batch delays:** 2 minutes between 50-property batches
7. **Save progress:** Results saved every 10 properties
8. **Import to DB:** When batch completes, import all results

### What Gets Enriched

**Bedroom Count:**
- 1, 2, 3, 4, 5+ bedrooms
- Extracted from listing text: "3 bed", "3 bedroom", "3BR"

**Property Type:**
- Detached
- Semi-detached
- Terraced
- Apartment
- Bungalow
- Duplex

### Success Factors

**Higher success (95%+):**
- Recent properties (2024-2026)
- Urban areas (Dublin, Cork, Galway)
- Higher value properties (€300k+)
- Properties with Eircode (74%+ of recent)

**Lower success (60-80%):**
- Older properties (pre-2020)
- Rural areas
- Lower value properties
- No Eircode

---

## Monitoring & Management

### Check Progress

```bash
# Quick status
bash scripts/check_enrichment_progress.sh

# Detailed check
python3 << 'EOF'
import json
batches = ['enrichment_full_results.json', 'enrichment_batch2_results.json']
for batch in batches:
    try:
        with open(batch) as f:
            results = json.load(f)
        enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
        print(f'{batch}: {len(enriched)}/{len(results)} ({len(enriched)/len(results)*100:.1f}%)')
    except:
        print(f'{batch}: Not found')
EOF
```

### If Process Stops

**Check if running:**
```bash
ps aux | grep enrich_from_csv
```

**Restart from where it left off:**
```bash
# Results file has progress saved every 10 properties
# Script automatically skips already-processed IDs
nohup python3 scripts/enrich_from_csv.py \
  --input enrichment_batch2_input.csv \
  --output enrichment_batch2_results.json \
  --batch-size 50 \
  --batch-delay 120 \
  --delay 10 \
  > enrichment_batch2_progress.log 2>&1 &
```

### When Batch Completes

1. **Verify results:**
   ```bash
   python3 -c "
   import json
   with open('enrichment_batch2_results.json') as f:
       results = json.load(f)
   enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
   print(f'Success rate: {len(enriched)/len(results)*100:.1f}%')
   "
   ```

2. **Import to database:**
   ```bash
   python3 scripts/import_enrichment_results.py enrichment_batch2_results.json
   ```

3. **Prepare next batch:**
   - Find oldest enriched date
   - Go back 3 months
   - Create new input CSV
   - Start enrichment

4. **Update this document:**
   - Mark batch as complete
   - Add statistics
   - Plan next batch

---

## Database Impact

### Current Coverage

**After Batch 1 (as of June 10, 2026):**
```
Total properties: 784,854
With bedrooms: 6,663 (0.8%)
With property type: 7,923 (1.0%)
Enriched (either/both): ~7,900 (1.0%)
```

**Projected After All Batches (optimistic):**
```
2024-2026: ~30,000 properties (~95% enriched)
2022-2023: ~40,000 properties (~85% enriched)
2020-2021: ~35,000 properties (~70% enriched)
2018-2019: ~30,000 properties (~60% enriched)
Total enriched: ~135,000 properties (~17% of database)
```

### Benefits

**Search Enhancement:**
- Filter by bedrooms: "Show me 3-bed properties in Dublin"
- Filter by type: "Show me detached houses in Cork"
- Better user experience: More relevant results

**Analytics:**
- Price per bedroom trends
- Property type distribution by area
- Market insights (apartments vs houses, etc.)

**SEO:**
- Richer content for property pages
- Better search engine results
- More specific landing pages

---

## Cost Analysis

### Time Investment

**Per batch:**
- Setup: 5 minutes
- Processing: 25-40 hours (automated)
- Import: 5-10 minutes
- Total: ~40 hours automated + 15 minutes manual

**Total project (12 batches):**
- Processing: ~480 hours (20 days automated)
- Manual: ~3 hours
- Calendar time: ~6-8 weeks (running continuously)

### API/Rate Limits

**DuckDuckGo:**
- Free search API (via web scraping)
- Rate limit: 10 seconds between requests (safe)
- No API key needed
- Risk: IP blocking (mitigated by delays)

**Google (fallback):**
- Used rarely (<5% of requests)
- Custom search rate limits apply
- Fallback for DuckDuckGo failures

### Server Resources

**CPU:** Low (mostly waiting on network)
**Memory:** ~50 MB per process
**Disk:** ~5 MB per 10k properties (JSON results)
**Network:** Minimal bandwidth

---

## Success Metrics

### Batch 1 Results ✅

- **Success rate:** 98.8% (excellent)
- **Processing time:** 25 hours (as expected)
- **Data quality:** Good (bedroom counts match PPR property descriptions)
- **Verdict:** Continue with more batches

### Target Metrics

**Good batch (continue):**
- Success rate: ≥90%
- Processing time: ≤48 hours
- Data quality: Matches property descriptions

**Poor batch (stop or adjust):**
- Success rate: <80%
- Many properties without online listings
- Low data quality

**Stopping point:**
- Success rate drops below 70%
- Properties too old (no online listings)
- Time investment not worth the coverage

---

## Files & Logs

### Active Files

**Batch 1:**
- ✅ `enrichment_full_results.json` (5.3 MB, 7,884 properties)
- ✅ `enrichment_progress.log` (939 KB)

**Batch 2:**
- ⏳ `enrichment_batch2_input.csv` (14,450 properties)
- ⏳ `enrichment_batch2_results.json` (writing...)
- ⏳ `enrichment_batch2_progress.log` (writing...)

**Scripts:**
- `scripts/enrich_from_csv.py` - Main enrichment script
- `scripts/import_enrichment_results.py` - Import to database
- `scripts/check_enrichment_progress.sh` - Progress checker

**Documentation:**
- `ENRICHMENT_STATUS.md` - Original batch 1 documentation
- `ENRICHMENT_ONGOING.md` - This file (ongoing process)
- `OFFLINE_ENRICHMENT.md` - Technical details

---

## Next Actions

### Immediate (Automated)

- ⏳ Batch 2 running (14,450 properties)
- ⏳ Expected completion: June 12, 2026
- ⏳ Auto-saving progress every 10 properties

### When Batch 2 Completes

1. **Import results:**
   ```bash
   python3 scripts/import_enrichment_results.py enrichment_batch2_results.json
   ```

2. **Check success rate:**
   - If ≥90%: Continue with batch 3
   - If <90%: Evaluate whether to continue

3. **Prepare batch 3:**
   - Date range: Sep 7 - Dec 6, 2025
   - Create input CSV
   - Start enrichment

4. **Update documentation:**
   - Mark batch 2 complete
   - Add statistics
   - Update projections

---

**Last Updated:** June 10, 2026 13:40  
**Status:** Batch 1 ✅ complete (7,784 enriched), Batch 2 ⏳ running (14,450 target)  
**Next Review:** June 12, 2026 (when batch 2 completes)
