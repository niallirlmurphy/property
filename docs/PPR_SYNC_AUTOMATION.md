# PPR Sync Automation

**Automatic biweekly import of new property sales from the Property Price Register**

---

## Overview

The system automatically checks for and imports new property sales from the PPR every 2 weeks (1st and 15th of each month at 2:47 AM).

**Schedule:** Biweekly (1st and 15th at 2:47 AM)  
**Script:** `scripts/sync_ppr_updates.py`  
**Logs:** `logs/ppr_sync.log`

---

## How It Works

### Process Flow

```
1. Query database for most recent sale_date
   ↓
2. Download latest PPR-ALL.csv from propertypriceregister.ie
   ↓
3. Filter CSV to sales after most recent sale_date (delta only)
   ↓
4. Normalize format (DD/MM/YYYY → YYYY-MM-DD, €XXX → float, etc.)
   ↓
5. Geocode new properties (using existing geocode.py infrastructure)
   ↓
6. Import to database (batch insert, ON CONFLICT DO NOTHING)
   ↓
7. Refresh routing_key_stats materialized view
   ↓
8. Log results to logs/ppr_sync.log
```

### Automated Features

**1. Delta Detection**
- Queries DB for `MAX(sale_date)` to find cutoff
- Only processes sales after this date
- Prevents duplicate imports (ON CONFLICT DO NOTHING)

**2. Format Normalization**
- **Dates:** `DD/MM/YYYY` → `YYYY-MM-DD`
- **Prices:** `€256,000.00` → `256000.00`
- **Booleans:** `Yes`/`No` → `TRUE`/`FALSE`
- **Eircodes:** Stripped whitespace, uppercase
- **Addresses:** Trimmed, preserved as-is

**3. Geocoding**
- New properties geocoded using existing `geocode.py`
- Same logic: Nominatim → Photon fallback → cache
- Coordinates validated against Ireland bounds
- Routing keys auto-generated for Eircodes

**4. Quality Validation**
- Bad geocodes automatically flagged (see GEOCODING_QUALITY_MONITORING.md)
- Routing key distance validation applied
- Out-of-bounds coordinates rejected

---

## Cron Schedule

**Expression:** `47 2 1,15 * *`  
**Runs:** 1st and 15th of every month at 2:47 AM  
**Timezone:** Local (Ireland time)

### Why 2:47 AM?

- Off-peak hours (minimal user impact)
- After PPR typically updates (they update business hours, data available by midnight)
- Avoids :00 and :30 minute marks (load distribution)
- 1st and 15th captures biweekly PPR update cycle

### Cron Job Details

**Command:**
```bash
cd /Users/nmurphy/claude/property\ price\ project && \
DATABASE_URL="postgresql://..." \
python3 scripts/sync_ppr_updates.py >> logs/ppr_sync.log 2>&1
```

**Managed by:** Claude Code scheduled tasks (durable)  
**Auto-expires:** After 7 days (requires renewal)  
**Job ID:** Check `.claude/scheduled_tasks.json`

---

## Manual Usage

### Run Sync Manually

```bash
cd /Users/nmurphy/claude/property\ price\ project

# Dry run (see what would be imported)
DATABASE_URL="postgresql://..." python3 scripts/sync_ppr_updates.py --dry-run

# Real import
DATABASE_URL="postgresql://..." python3 scripts/sync_ppr_updates.py

# Import from specific date
DATABASE_URL="postgresql://..." python3 scripts/sync_ppr_updates.py --since 2025-01-01

# Use manually downloaded CSV
DATABASE_URL="postgresql://..." python3 scripts/sync_ppr_updates.py --manual-csv ~/Downloads/PPR-ALL.csv
```

### Force Re-Download

If automatic download fails:

```bash
# 1. Visit PPR website
open https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPRDownloads?OpenForm

# 2. Download PPR-ALL.csv manually

# 3. Run sync with manual CSV
DATABASE_URL="..." python3 scripts/sync_ppr_updates.py --manual-csv ~/Downloads/PPR-ALL.csv
```

---

## Monitoring

### Check Logs

```bash
# View recent sync
tail -100 logs/ppr_sync.log

# Watch live sync
tail -f logs/ppr_sync.log

# Count successful syncs
grep "✓ SYNC COMPLETE" logs/ppr_sync.log | wc -l

# Find errors
grep -i "error\|fail\|⚠" logs/ppr_sync.log
```

### Check Database Status

```sql
-- Most recent sale in database
SELECT MAX(sale_date) as most_recent, COUNT(*) as total_properties
FROM properties;

-- Sales added in last sync
SELECT COUNT(*) as new_sales
FROM properties
WHERE sale_date > (
    SELECT MAX(sale_date) - INTERVAL '14 days'
    FROM properties
);

-- Properties added today
SELECT COUNT(*) as added_today
FROM properties
WHERE id > (
    SELECT MAX(id) - 100 FROM properties
);
```

### Sync Statistics

**Expected behavior:**
- **Empty DB:** ~781,501 properties imported (initial load)
- **Biweekly update:** ~2,000-5,000 new sales (varies by season)
- **Duration:** 5-30 minutes depending on new property count
- **Geocoding rate:** ~80% success (matches existing coverage)

---

## Troubleshooting

### Sync Failed: Download Error

**Symptom:** Log shows "Failed to download PPR CSV"

**Cause:** PPR website blocking automated downloads or changed URL

**Solution:**
1. Manual download: Visit https://www.propertypriceregister.ie
2. Download PPR-ALL.csv
3. Run: `python3 scripts/sync_ppr_updates.py --manual-csv PPR-ALL.csv`

### Sync Failed: No New Sales

**Symptom:** "Database is up to date, no new sales to import"

**Expected:** If PPR hasn't released new data yet

**Check:**
```bash
# When was last sync?
ls -lh logs/ppr_sync.log

# What's the most recent sale in DB?
psql $DATABASE_URL -c "SELECT MAX(sale_date) FROM properties;"

# Is there really new data? Check PPR website
```

### Sync Failed: Geocoding Timeout

**Symptom:** "Geocoding timed out (>1 hour)"

**Cause:** Too many properties to geocode (>5000), geocoding is slow

**Solution:**
1. Import without geocoding first (coordinates NULL)
2. Geocode separately later in smaller batches
3. Or increase timeout in script

### Sync Failed: Database Connection

**Symptom:** "connection refused" or "authentication failed"

**Cause:** DATABASE_URL incorrect or database down

**Solution:**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check .env file
cat backend/.env | grep DATABASE_URL

# Verify Supabase is accessible
curl -I https://jyezhkgevzejhundypxn.supabase.co
```

### Cron Job Not Running

**Check scheduled tasks:**
```bash
cat ~/.claude/scheduled_tasks.json | grep ppr_sync

# Or use Claude Code:
# "Show me scheduled cron jobs"
```

**Renew if expired:**
- Cron jobs auto-expire after 7 days
- Re-run setup to create new job
- Or manually edit scheduled_tasks.json

---

## Maintenance

### Renew Cron Job (Weekly)

Since cron jobs expire after 7 days:

```bash
# In Claude Code:
"Renew the PPR sync cron job"

# Or manually add to crontab:
47 2 1,15 * * cd /path && DATABASE_URL="..." python3 scripts/sync_ppr_updates.py >> logs/ppr_sync.log 2>&1
```

### Clean Old Logs

```bash
# Archive logs older than 90 days
find logs/ -name "ppr_sync.log" -mtime +90 -exec gzip {} \;

# Or rotate logs (keep last 10 syncs)
tail -10000 logs/ppr_sync.log > logs/ppr_sync.log.tmp
mv logs/ppr_sync.log.tmp logs/ppr_sync.log
```

### Verify Data Quality

After each sync, spot-check:

```sql
-- Recent imports (should be today)
SELECT COUNT(*), MIN(sale_date), MAX(sale_date)
FROM properties
WHERE id > (SELECT MAX(id) - 1000 FROM properties);

-- Geocoding coverage (should stay ~79%)
SELECT 
    COUNT(*) FILTER (WHERE latitude IS NOT NULL) * 100.0 / COUNT(*) as geocoded_pct
FROM properties;

-- Flagged for quality issues
SELECT COUNT(*) FROM properties WHERE geocode_quality_issue = TRUE;
```

---

## Future Enhancements

### 1. Email Notifications

Send email after each sync with summary:
- Properties added
- Geocoding success rate
- Errors encountered

### 2. Incremental API

If PPR releases an incremental API (sales since date):
- Replace full CSV download with API call
- Faster, more efficient
- Reduce bandwidth/processing

### 3. Real-time Updates

If PPR provides webhook or RSS:
- Trigger sync on new data availability
- Reduce lag between PPR update and DB update
- More responsive to market changes

### 4. Address Normalization

Run `scripts/normalize_addresses.py` on new imports:
- Improve geocoding hit rate
- Better Eircode enrichment success
- Consistent formatting

### 5. Automatic Re-Geocoding

For properties that failed geocoding:
- Retry after 30 days with updated geocoders
- Use Mapbox for high-value properties
- Flag persistent failures for manual review

---

## PPR Data Format Reference

### CSV Columns (as of 2024)

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| Date of Sale (dd/mm/yyyy) | Date | 15/01/2024 | Sale completion date |
| Address | Text | 10 Main Street, Dublin 1 | Full address as registered |
| Postal Code | Text | D01 X2Y3 | Eircode (may be blank) |
| County | Text | Dublin | Irish county name |
| Price (€) | Currency | €256,000.00 | Sale price in euros |
| Not Full Market Price | Yes/No | No | Discounted/non-market sale flag |
| VAT Exclusive | Yes/No | No | VAT not included in price |
| Description of Property | Text | Second-Hand Dwelling house /Apartment | Property type |
| Property Size Description | Text | greater than or equal to 38 sq metres and less than 125 sq metres | Size band (optional) |

### Data Quirks

**Addresses:**
- Inconsistent formatting (some all caps, some title case)
- Missing street numbers common in rural areas
- Townland names may or may not be included
- County name sometimes repeated in address field

**Eircodes:**
- ~29% have Eircode (lower for older sales)
- Format: XXX XXXX (3 chars + space + 4 chars)
- May be blank or "Not available"

**Prices:**
- Currency symbol and commas included
- Some sales marked "Not Full Market Price" (family transfers, etc.)
- VAT exclusive flag for commercial properties

**Dates:**
- Always DD/MM/YYYY format
- Registration date, not transaction date (may lag)
- Sales from ~2010 onwards (PPR started Jan 2010)

---

## Summary

**Automatic biweekly sync** ensures the database stays current with minimal manual intervention.

**Key Points:**
- ✅ Runs automatically 1st and 15th of each month
- ✅ Only imports new sales (delta detection)
- ✅ Geocodes and validates new properties
- ✅ Logs everything to logs/ppr_sync.log
- ✅ Handles errors gracefully (manual fallback available)

**Result:** Up-to-date property data with ~2-week lag maximum, automated quality validation, and full audit trail.
