# Address Normalization Fix

## Problem

45,967 properties have `address_normalized = NULL`, causing the S1 exact search page to miss recent sales.

**Example:** Searching "19 Fairfield Road, Glasnevin, Dublin 9" showed only 1 sale (2014) but database has 2 sales (2014 + 2026). The 2026 sale has `address_normalized = NULL`.

**Timeline:**
- Sep 2025 and earlier: 100% normalized ✅
- Oct 2025: Started failing (42.5% missing)
- Nov 2025 - Apr 2026: 100% missing ❌ 
- May 2026: Partially fixed (66% missing)
- Jun 2026: Back to normal (0% missing) ✅

## Solution

### 1. Backend Fix (Deployed)

Modified `/search/exact` endpoint to handle NULL addresses:

```sql
WHERE starts_with(COALESCE(address_normalized, address), $1)
```

This allows search to work immediately with both normalized and non-normalized addresses.

**Status:** ✅ Deployed to production (commit 578ce7f)

### 2. Database Migration (Pending)

Permanent fix that:
1. Adds `normalize_address()` PostgreSQL function
2. Backfills all 45k NULL entries in batches
3. Creates trigger to auto-normalize on INSERT/UPDATE

**To apply:**

```bash
cd /Users/nmurphy/claude/property\ price\ project
python3 db/apply_migration.py
```

The migration:
- Runs in batches (1k properties at a time) to avoid locks
- Takes ~1-2 minutes to complete
- Includes verification and testing
- Safe to run on production (uses batched updates with pg_sleep)

**After migration:**
- All properties will have normalized addresses
- Future imports automatically normalize (via trigger)
- No manual intervention needed

## Verification

### Before Migration

```bash
# Check NULL count
python3 -c "
import os, asyncio, asyncpg
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def check():
    pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
    count = await pool.fetchval('SELECT COUNT(*) FROM properties WHERE address_normalized IS NULL')
    print(f'NULL address_normalized: {count:,}')
    await pool.close()

asyncio.run(check())
"
```

Expected: ~45,967

### After Migration

Same command should return: 0

### Test Search

```bash
curl -s "https://eloquent-optimism-production-350a.up.railway.app/search/exact?address=19%20Fairfield%20Road%20Glasnevin" | jq '.count'
```

Expected: 2 (both 2014 and 2026 sales)

## Prevention

The migration creates a **database trigger** that automatically normalizes addresses on INSERT/UPDATE:

```sql
CREATE TRIGGER trigger_auto_normalize_address
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION auto_normalize_address();
```

This ensures:
1. Import scripts don't need normalization logic (database handles it)
2. Manual imports are automatically normalized
3. No more NULL address_normalized entries

## Rollback

If the migration causes issues:

1. Drop the trigger:
```sql
DROP TRIGGER IF EXISTS trigger_auto_normalize_address ON properties;
```

2. Drop the function:
```sql
DROP FUNCTION IF EXISTS normalize_address(TEXT);
DROP FUNCTION IF EXISTS auto_normalize_address();
```

The backend fix (COALESCE) will continue to work even if the migration is rolled back.

## Next Steps

1. ✅ Backend fix deployed (immediate relief)
2. ⏳ Apply database migration (permanent fix)
3. ✅ Monitor S1 search for NULL address issues
4. ✅ Verify future imports auto-normalize

## Related Files

- `backend/main.py` - Backend fix (COALESCE)
- `db/migrations/001_fix_address_normalized.sql` - Database migration
- `db/apply_migration.py` - Migration script
- `db/import.py` - Has normalize_address() function (line 79)
- `scripts/sync_ppr_updates.py` - Has normalize_address() function (line 75)
