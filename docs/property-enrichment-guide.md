# Property Enrichment Guide

## Overview

Property enrichment adds bedroom counts and property types to recent sales by searching the web for property listings.

## Database Schema

**New columns added:**
- `bedrooms` (INTEGER) - Number of bedrooms
- `property_type` (TEXT) - Type: house, apartment, terraced, detached, semi-detached, etc.

Both columns are indexed for fast filtering.

## How It Works

1. **Finds recent properties** (last 3 months by default) without enrichment data
2. **Searches DuckDuckGo** for "{address} {county} Ireland property"
3. **Extracts data** from search result snippets:
   - Bedroom count: patterns like "3 bed", "2 bedroom", "4-bed"
   - Property type: keywords like "house", "apartment", "detached", etc.
4. **Updates database** with found information

## Usage

### Test First (Dry Run)
```bash
# Test with 20 properties, no database updates
python3 scripts/enrich_recent_properties.py --limit 20 --dry-run
```

### Enrich Recent Properties
```bash
# Last 3 months (default)
python3 scripts/enrich_recent_properties.py

# Last 6 months
python3 scripts/enrich_recent_properties.py --months 6

# Limit to 100 properties
python3 scripts/enrich_recent_properties.py --limit 100
```

### Options
- `--months N` - How many months back to search (default: 3)
- `--limit N` - Max properties to process (default: all)
- `--dry-run` - Preview without updating database

## Success Rates

**Expected results:**
- **60-90% success rate** for recent high-value properties
- **Higher success** for Dublin and major cities (more listings online)
- **Lower success** for rural properties (fewer online listings)
- **Bedroom data:** ~60-70% of successful searches
- **Property type:** ~90-100% of successful searches

## Rate Limiting

- **10 seconds between requests** to avoid being blocked
- Processing 100 properties takes ~17 minutes
- Processing 1,000 properties takes ~3 hours

**Recommendation:** Run in batches of 100-200 properties to avoid timeouts

## Example Results

```
55 ROCHESTOWN PARK, DUN LAOGHAIRE → 3 bed, semi-detached
77 DONNYBROOK CASTLE, DONNYBROOK → 2 bed, terraced
111 CASTLETOWN, LEIXLIP → 4 bed, house
19 THE AVENUE, KILL → 3 bed, terraced
```

## Scheduling

### Manual Schedule
Run monthly for new sales:
```bash
# First week of each month
python3 scripts/enrich_recent_properties.py --months 1
```

### Automated Schedule (Optional)
Add to cron (first of month at 3am):
```cron
0 3 1 * * cd /path/to/project && python3 scripts/enrich_recent_properties.py --months 1
```

## Monitoring

### Check Enrichment Coverage
```bash
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Recent properties (last 3 months)
cur.execute('''
    SELECT
        COUNT(*) as total,
        COUNT(bedrooms) as with_beds,
        COUNT(property_type) as with_type,
        ROUND(100.0 * COUNT(bedrooms) / COUNT(*), 1) as pct_beds,
        ROUND(100.0 * COUNT(property_type) / COUNT(*), 1) as pct_type
    FROM properties
    WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
''')

total, with_beds, with_type, pct_beds, pct_type = cur.fetchone()
print(f'Recent properties (last 3 months):')
print(f'  Total: {total:,}')
print(f'  With bedrooms: {with_beds:,} ({pct_beds}%)')
print(f'  With property type: {with_type:,} ({pct_type}%)')
conn.close()
"
```

### Check by County
```sql
SELECT
    county,
    COUNT(*) as total,
    COUNT(bedrooms) as with_beds,
    COUNT(property_type) as with_type,
    ROUND(100.0 * COUNT(bedrooms) / COUNT(*), 1) as pct_beds
FROM properties
WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY county
ORDER BY total DESC
LIMIT 10;
```

## Limitations

### What Works Well
- ✅ Recent sales (last 3-6 months)
- ✅ High-value properties (more likely to be listed)
- ✅ Urban areas (Dublin, Cork, Galway)
- ✅ Properties currently for sale or recently sold
- ✅ Unique addresses (easier to match)

### What Doesn't Work
- ❌ Old sales (no longer listed online)
- ❌ Rural properties (fewer listings)
- ❌ Very low-value properties (under €200k)
- ❌ Properties never listed publicly (family transfers)
- ❌ Generic addresses (hard to match)

## Data Quality

### Property Types Found
- house
- apartment
- terraced
- detached
- semi-detached
- duplex
- bungalow
- cottage

### Bedroom Range
- Validated: 1-10 bedrooms
- Most common: 2-4 bedrooms
- Invalid values are rejected

## Future Enhancements

**Potential improvements:**
1. **Official APIs** - Use Daft.ie or MyHome.ie APIs if available
2. **Historical enrichment** - Backfill older properties with archived listings
3. **More fields** - Add bathrooms, square footage, BER rating
4. **Machine learning** - Predict property type from address patterns
5. **Manual curation** - Flag uncertain values for review

## Costs

**Current approach:**
- ✅ **FREE** - Uses public web search
- ✅ No API costs
- ✅ No rate limiting fees

**Alternative approaches:**
- Property APIs: €0.01-0.10 per lookup
- Google Geocoding API: Already using for coordinates

## Support

**If enrichment fails:**
1. Check internet connection
2. Verify DATABASE_URL is set
3. Try with `--limit 10 --dry-run` to test
4. Check if being rate-limited (wait 10 minutes, try again)
5. Run in smaller batches (--limit 50)

**Files:**
- Script: `scripts/enrich_recent_properties.py`
- Schema: `db/add_property_details_columns.sql`
- This guide: `docs/property-enrichment-guide.md`

---

**Last updated:** June 4, 2026  
**Database coverage:** 0% enriched (newly added feature)  
**Target coverage:** 60-80% for recent properties
