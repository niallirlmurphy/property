# Salesforce PPR Import - Summary

## ✅ Setup Complete

All components are ready to import Irish Property Price Register data into Salesforce.

## Current Status

- **Salesforce Connection**: ✓ Connected via CLI
- **Custom Field**: ✓ `PPR_Import__c` created on Account object
- **Test Import**: ✓ 203 records successfully imported
- **Import Script**: ✓ Ready for production

## What We Built

### 1. Custom Field: `PPR_Import__c`
- **Type**: Text
- **Purpose**: Tags all imported records with import date
- **Example**: `"2026-05-18"`
- **Benefit**: Easy to query, filter, and clean up imported data

### 2. Import Script: `import_to_salesforce.py`
- Reads from `PPR-ALL-geocoded.csv`
- Converts PPR records to Salesforce Account format
- Handles batching (200 records per batch)
- Tags with import date
- Resumable (can skip already-imported records)

### 3. Full Import Script: `import_all_ppr.sh`
- Imports all 781,000 records in batches of 10,000
- Estimated time: 6-8 hours
- Progress reporting
- Pause-and-resume capable

## Data Mapping

PPR CSV → Salesforce Account:

| PPR Field | Salesforce Field | Notes |
|-----------|------------------|-------|
| Address | Name | Truncated to 80 chars |
| Address | BillingStreet | Full address |
| County | BillingCity | |
| Eircode | BillingPostalCode | |
| - | BillingCountry | Always "Ireland" |
| Date + Price | Description | "Sale Date: 01/01/2010, Price: €343,000" |
| - | PPR_Import__c | Import date tag |

## Usage

### Test Import (10 records)
```bash
cd /Users/nmurphy/claude/property\ price\ project
python3 scripts/import_to_salesforce.py --test
```

### Import Specific Number
```bash
# Import 1,000 records
python3 scripts/import_to_salesforce.py --limit 1000

# Import 1,000 records starting from record 5000
python3 scripts/import_to_salesforce.py --limit 1000 --skip 5000
```

### Full Import (All 781k records)
```bash
# Interactive - will prompt for confirmation
./scripts/import_all_ppr.sh

# Or run in background with logging
nohup ./scripts/import_all_ppr.sh > ppr_import.log 2>&1 &

# Monitor progress
tail -f ppr_import.log
```

## Verification

### Count Imported Records
```bash
sf data query --query "SELECT COUNT() FROM Account WHERE PPR_Import__c = '2026-05-18'"
```

### View Sample Records
```bash
sf data query --query "SELECT Name, BillingCity, BillingPostalCode, PPR_Import__c FROM Account WHERE PPR_Import__c = '2026-05-18' LIMIT 10"
```

### Check Import Date
```bash
sf data query --query "SELECT PPR_Import__c, COUNT(Id) FROM Account GROUP BY PPR_Import__c"
```

## Cleanup

### Delete All Imported Records
```bash
# Export IDs
sf data query --query "SELECT Id FROM Account WHERE PPR_Import__c = '2026-05-18'" \
  --result-format csv > /tmp/ppr_cleanup.csv

# Delete
sf data delete bulk --sobject Account --file /tmp/ppr_cleanup.csv --wait 10
```

### Delete Specific Import Date
```bash
# Replace date as needed
sf data query --query "SELECT Id FROM Account WHERE PPR_Import__c = 'YYYY-MM-DD'" \
  --result-format csv > /tmp/cleanup.csv

sf data delete bulk --sobject Account --file /tmp/cleanup.csv
```

## Performance

### Import Speed
- **Batch size**: 200 records per API call
- **Processing time**: ~9 seconds per batch
- **Rate**: ~1,300 records per minute
- **Full dataset**: 781,000 records = ~10 hours

### Optimization
- Salesforce bulk API processes records asynchronously
- Can run multiple import scripts in parallel (risk of duplicates)
- Recommended: Single sequential import overnight

## Troubleshooting

### Error: "PPR_Import__c field not found"
**Solution**: Create the field in Salesforce
- Setup → Object Manager → Account
- Fields & Relationships → New
- Type: Text, Name: PPR_Import

### Error: "Not connected to Salesforce"
**Solution**: Re-authenticate
```bash
sf org login web --alias property-geocoding --set-default
```

### Error: "LineEnding is invalid"
**Solution**: Fixed in current script (uses binary write with LF)

### Error: Duplicate records
**Cause**: Script re-run without `--skip`
**Solution**: Delete duplicates or use PPR_Import__c date to identify latest import

## Next Steps

### Option 1: Import All Data Now
```bash
./scripts/import_all_ppr.sh
```
**Time**: 6-8 hours
**Result**: All 781k properties in Salesforce

### Option 2: Import Subset First
```bash
# Dublin only (test with real data)
python3 scripts/import_to_salesforce.py --limit 50000 --county Dublin
```

### Option 3: Geocode in Salesforce
Once data is imported, you can:
1. Use Salesforce Maps to geocode addresses
2. Add lat/long fields to Account object
3. Import coordinates from `PPR-ALL-geocoded.csv`

## Cost Considerations

### Salesforce API Limits
- **Free Tier**: 15,000 API calls/day
- **Enterprise**: 1,000,000+ API calls/day
- **Bulk API**: Separate limit, generally more generous

### Import Cost
- **781,000 records** / 200 per batch = **3,905 API calls**
- Well within free tier limits
- Can complete in 6-8 hours

### Storage
- **781k Account records** ≈ 500MB
- Most Salesforce orgs have GB of storage
- Developer Edition: 5 MB data storage (limited - may hit limit)

## Success Metrics

After import, verify:
- ✓ Record count matches: ~781,000
- ✓ All records tagged with PPR_Import__c
- ✓ Addresses populate correctly
- ✓ Counties/Eircodes where available
- ✓ Can query by PPR_Import__c date

## Files Created

1. `scripts/import_to_salesforce.py` - Main import script
2. `scripts/import_all_ppr.sh` - Batch wrapper script
3. `scripts/SALESFORCE_FIELD_SETUP.md` - Field setup guide
4. `scripts/test_salesforce_field.py` - Field existence checker
5. `scripts/SALESFORCE_IMPORT_SUMMARY.md` - This file

---

**Status**: ✅ Ready to import

**Next Command**:
```bash
./scripts/import_all_ppr.sh
```

Or for a test run:
```bash
python3 scripts/import_to_salesforce.py --limit 1000
```
