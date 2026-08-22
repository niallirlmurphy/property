# Fix Bad Geocode Guide

**Purpose:** Remove incorrect coordinates for properties that were geocoded to the wrong location.

---

## Quick Fix for "MOUNT CARMEL, CROOKSHANE, RATHCOOLE"

### Step 1: Find the property

```bash
cd ~/claude/property\ price\ project
python3 scripts/fix_bad_geocode.py "MOUNT CARMEL, CROOKSHANE, RATHCOOLE"
```

**Expected output:**
```
Found 1 properties:

ID: 123456
Address: MOUNT CARMEL, CROOKSHANE, RATHCOOLE
County: Dublin
Coordinates: (53.xxxx, -6.xxxx)
Eircode: ...
Sale Date: ...
Price: €...
------------------------------------------------------------

To remove coordinates for this property, run:
python3 scripts/fix_bad_geocode.py --id 123456 --remove
```

### Step 2: Remove the bad coordinates (dry run first)

```bash
python3 scripts/fix_bad_geocode.py --id 123456 --remove --dry-run
```

**Expected output:**
```
Property: MOUNT CARMEL, CROOKSHANE, RATHCOOLE
Current coordinates: (53.xxxx, -6.xxxx)

DRY RUN - Would execute:
UPDATE properties SET latitude = NULL, longitude = NULL, geog = NULL, needs_geocoding = TRUE WHERE id = 123456;

Run without --dry-run to apply changes
```

### Step 3: Apply the fix

```bash
python3 scripts/fix_bad_geocode.py --id 123456 --remove
```

**Expected output:**
```
Property: MOUNT CARMEL, CROOKSHANE, RATHCOOLE
Current coordinates: (53.xxxx, -6.xxxx)

✓ Removed coordinates for property ID 123456
✓ Set needs_geocoding = TRUE

This property will be re-geocoded in the next batch geocoding run.
```

---

## General Usage

### Find properties by address pattern

```bash
# Search for any property containing these keywords
python3 scripts/fix_bad_geocode.py "BALLSBRIDGE"

# Case-insensitive, finds all Ballsbridge properties
python3 scripts/fix_bad_geocode.py "ballsbridge"
```

### Find property by ID

```bash
python3 scripts/fix_bad_geocode.py --id 123456
```

### Remove coordinates

```bash
# Always dry run first!
python3 scripts/fix_bad_geocode.py --id 123456 --remove --dry-run

# If looks good, apply
python3 scripts/fix_bad_geocode.py --id 123456 --remove
```

---

## What the Script Does

### When searching:
- Finds properties matching your search pattern
- Shows full details (address, coordinates, eircode, etc.)
- Provides the command to fix if needed

### When removing coordinates (`--remove`):
1. **Sets `latitude = NULL`**
2. **Sets `longitude = NULL`**
3. **Sets `geog = NULL`** (PostGIS geography column)
4. **Sets `needs_geocoding = TRUE`** (flags for re-geocoding)

### After removal:
- Property disappears from map immediately (no coordinates)
- Property still shows in search results (with note: needs geocoding)
- Next geocoding run will attempt to geocode it correctly

---

## Re-geocoding After Removal

### Automatic (biweekly PPR sync):
The property will be automatically re-geocoded during the next biweekly sync:
```bash
python3 scripts/sync_ppr_updates.py
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
```

### Manual (immediate):
Re-geocode just this property (or a small batch):
```bash
# Re-geocode all properties flagged needs_geocoding
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 100 --apply
```

---

## Common Issues & Solutions

### Issue: "No properties found"
**Possible causes:**
- Typo in address
- Property doesn't exist in database
- Using exact match instead of pattern

**Solution:** Try broader search:
```bash
# Instead of exact address
python3 scripts/fix_bad_geocode.py "MOUNT CARMEL"

# Or search by part of address
python3 scripts/fix_bad_geocode.py "CROOKSHANE"
```

### Issue: "Multiple properties found"
**Expected:** Some addresses have multiple sales over time.

**Solution:** Check the list and choose the correct ID:
```bash
python3 scripts/fix_bad_geocode.py --id 123456 --remove
```

### Issue: "Property ID not found"
**Cause:** Typo in ID or property doesn't exist.

**Solution:** Re-search to get correct ID:
```bash
python3 scripts/fix_bad_geocode.py "ADDRESS PATTERN"
```

---

## Safety Features

### Dry Run Mode
- **Always use `--dry-run` first**
- Shows exactly what will happen
- No changes made to database
- Safe to test

### Single Property Updates
- Script only updates one property at a time
- Uses property ID (not pattern matching)
- Requires explicit `--remove` flag
- No accidental bulk updates

### Audit Trail
- Shows before/after coordinates
- Confirms what was changed
- Logs to terminal

---

## Examples

### Example 1: Fix known bad geocode
```bash
# 1. Find the property
python3 scripts/fix_bad_geocode.py "44 MOUNT CARMEL ROAD"

# Output shows ID: 789123

# 2. Dry run
python3 scripts/fix_bad_geocode.py --id 789123 --remove --dry-run

# 3. Apply fix
python3 scripts/fix_bad_geocode.py --id 789123 --remove
```

### Example 2: Check property before fixing
```bash
# Look up by ID to verify it's the right one
python3 scripts/fix_bad_geocode.py --id 789123

# If coordinates look wrong, remove them
python3 scripts/fix_bad_geocode.py --id 789123 --remove
```

### Example 3: Batch check multiple properties
```bash
# Search for all properties in an area
python3 scripts/fix_bad_geocode.py "RATHCOOLE"

# Check each one manually
# Fix individually if needed
```

---

## When to Use This Script

### Use when:
- ✅ Property is geocoded to completely wrong location
- ✅ Coordinates are in different county/country
- ✅ Property shows on map but address doesn't match
- ✅ Manual verification confirms wrong location

### Don't use when:
- ❌ Coordinates are "close but not exact" (within 100m)
- ❌ Building number is slightly off on same street
- ❌ Geocoding quality is just "okay" (>70 score)
- ❌ Unsure if it's actually wrong

**Rule:** Only remove coordinates when clearly, obviously wrong.

---

## Monitoring Bad Geocodes

### Check for properties flagged as needing re-geocoding:
```bash
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE')
print(f'Properties needing geocoding: {cur.fetchone()[0]:,}')
conn.close()
"
```

### Check geocoding quality issues:
```bash
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM properties WHERE geocode_quality_issue = TRUE')
print(f'Properties with quality issues: {cur.fetchone()[0]:,}')
conn.close()
"
```

---

## Next Steps After Fixing

1. **Immediate:** Property removed from map
2. **Within minutes:** Vercel revalidates, change visible on site
3. **Next geocoding run:** Property re-geocoded automatically
4. **Verify fix:** Check property appears correctly on map

---

## Related Scripts

- `scripts/geocode_mapbox_batch.py` - Batch geocoding (re-geocode after removal)
- `scripts/export_bad_geocodes.py` - Export properties with quality issues
- `scripts/validate_geocodes.py` - Validate all coordinates (if exists)

---

## Quick Reference

```bash
# Search
python3 scripts/fix_bad_geocode.py "ADDRESS"

# Check by ID
python3 scripts/fix_bad_geocode.py --id ID

# Fix (dry run)
python3 scripts/fix_bad_geocode.py --id ID --remove --dry-run

# Fix (apply)
python3 scripts/fix_bad_geocode.py --id ID --remove

# Re-geocode after
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 100 --apply
```

**Always dry run first! Never skip verification!**
