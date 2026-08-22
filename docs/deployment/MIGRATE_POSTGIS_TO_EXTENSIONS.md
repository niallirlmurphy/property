# Migrate PostGIS to Extensions Schema

**Supabase Recommended Solution** ✅  
**Date:** June 9, 2026  
**Issue:** PostGIS installed in `public` schema (exposed via API)  
**Solution:** Move PostGIS to `extensions` schema (not exposed via API)  

---

## What Supabase Recommends

From Supabase support:

> Extensions should not be enabled under the public schema, but instead the extensions schema or a custom schema that is not exposed through the data API. This adds a layer of security that doesn't require RLS since the extension and related tables are not exposed publicly.

**Why this is better than RLS:**
- ✅ PostGIS tables (spatial_ref_sys, etc.) not exposed via API at all
- ✅ No RLS needed on system tables
- ✅ Cleaner architecture (extensions separate from data)
- ✅ Follows Supabase best practices
- ✅ Reduces attack surface

---

## Understanding the Migration

### What Gets Moved

**PostGIS system tables** (currently in `public`):
- `spatial_ref_sys` - Coordinate system definitions
- `geometry_columns` - Geometry metadata
- `geography_columns` - Geography metadata
- `raster_columns` - Raster metadata (if using)
- `raster_overviews` - Raster overviews (if using)

**Your data tables** (stay in `public`):
- `properties` - Your application data
- `search_log` - Your logs
- All other application tables

### What This Means

**Before (current state):**
```
public schema (exposed via API)
├── properties (your data) ✅
├── search_log (your data) ✅
└── spatial_ref_sys (PostGIS) ⚠️  exposed via API
    └── geometry_columns (PostGIS) ⚠️  exposed via API
```

**After (recommended):**
```
public schema (exposed via API)
├── properties (your data) ✅
└── search_log (your data) ✅

extensions schema (NOT exposed via API)
└── spatial_ref_sys (PostGIS) ✅ secure
    └── geometry_columns (PostGIS) ✅ secure
```

---

## Pre-Migration Checklist

### 1. Check Your Current Setup

```sql
-- What PostGIS version?
SELECT PostGIS_Version();

-- What schema is PostGIS in?
SELECT n.nspname as schema_name
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname = 'postgis';

-- Expected result: public (that's why we're migrating)
```

### 2. Check Your Geometry Columns

```sql
-- What geometry columns exist in your tables?
SELECT
    f_table_schema,
    f_table_name,
    f_geometry_column,
    type,
    srid
FROM geometry_columns
WHERE f_table_schema = 'public';

-- Expected: properties table with geog column
```

### 3. Backup Your Data (Critical!)

**Option A: Supabase Dashboard Backup**
1. Go to: Database → Backups
2. Create manual backup: "Before PostGIS migration"
3. Wait for completion (~5-10 minutes)

**Option B: SQL Dump**
```bash
# Dump just the properties table structure
pg_dump "$DATABASE_URL" \
  --schema-only \
  --table=properties \
  > properties_schema_backup.sql

# Your actual data stays in place - we're not touching it
```

### 4. Verify You Have Data

```sql
-- How much data do you have?
SELECT 
    COUNT(*) as total_properties,
    COUNT(geog) as with_geometry,
    COUNT(latitude) as with_coordinates
FROM properties;

-- Expected: 784k+ properties with geometry
```

---

## Migration Steps

### Step 1: Create Extensions Schema

```sql
-- Create the extensions schema
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant usage to necessary roles
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;

-- Verify
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'extensions';
```

### Step 2: Drop PostGIS from Public Schema

**⚠️ WARNING:** This will temporarily break geometry functions. Have your backend in maintenance mode or scheduled downtime window.

```sql
-- Drop the extension (this removes spatial_ref_sys, geometry_columns, etc.)
DROP EXTENSION IF EXISTS postgis CASCADE;

-- Verify it's gone
SELECT extname FROM pg_extension WHERE extname = 'postgis';
-- Expected: 0 rows
```

**What this does:**
- ❌ Removes PostGIS functions (ST_Distance, ST_Transform, etc.)
- ❌ Removes system tables (spatial_ref_sys, geometry_columns, etc.)
- ✅ Your data stays intact (properties table still has geog column)
- ✅ Coordinate values are preserved
- ❌ Cannot use PostGIS functions until reinstalled

### Step 3: Recreate PostGIS in Extensions Schema

```sql
-- Reinstall PostGIS in the extensions schema
CREATE EXTENSION postgis SCHEMA extensions;

-- Verify location
SELECT n.nspname as schema_name
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname = 'postgis';

-- Expected result: extensions
```

### Step 4: Update search_path

```sql
-- Add extensions schema to search path so PostGIS functions are found
ALTER DATABASE postgres SET search_path TO public, extensions;

-- Also set for current session
SET search_path TO public, extensions;

-- Verify
SHOW search_path;
-- Expected: public, extensions
```

### Step 5: Verify Geometry Columns Still Work

```sql
-- Check that your geometry column is recognized
SELECT
    f_table_schema,
    f_table_name,
    f_geometry_column,
    type,
    srid
FROM extensions.geometry_columns
WHERE f_table_schema = 'public' AND f_table_name = 'properties';

-- Expected: properties table with geog column, SRID 4326
```

### Step 6: Test PostGIS Functions

```sql
-- Test coordinate transformation (uses spatial_ref_sys)
SELECT ST_Transform(
    ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326),
    2157
) as irish_grid_coords;

-- Test distance calculation
SELECT ST_Distance(
    ST_MakePoint(-6.2603, 53.3498)::geography,
    ST_MakePoint(-6.2700, 53.3400)::geography
) as distance_meters;

-- Test your actual data
SELECT 
    COUNT(*),
    ST_X(ST_Centroid(geog::geometry)) as avg_lon,
    ST_Y(ST_Centroid(geog::geometry)) as avg_lat
FROM properties
WHERE geog IS NOT NULL
LIMIT 1;

-- All should work
```

### Step 7: Test Backend API

```bash
# Test geocoding (uses ST_Transform internally)
curl "https://eloquent-optimism-production-350a.up.railway.app/geocode?q=Dublin"

# Test search (uses ST_DWithin)
curl "https://eloquent-optimism-production-350a.up.railway.app/search?q=Dublin"

# Test trends
curl "https://eloquent-optimism-production-350a.up.railway.app/trends?county=Dublin"

# All should return results
```

---

## Troubleshooting

### If Geometry Column Not Found

**Symptom:** `geometry_columns` view doesn't show your table

**Fix:**
```sql
-- Manually register the geometry column
SELECT Populate_Geometry_Columns('public.properties'::regclass);

-- Or recreate the geography column constraint
ALTER TABLE properties 
  DROP CONSTRAINT IF EXISTS enforce_srid_geog;

ALTER TABLE properties
  ADD CONSTRAINT enforce_srid_geog 
  CHECK (ST_SRID(geog::geometry) = 4326);
```

### If Backend Gets "Function Not Found" Errors

**Symptom:** `function st_distance(geography, geography) does not exist`

**Fix:**
```sql
-- Check search_path for your connection role
SELECT rolname, rolconfig 
FROM pg_roles 
WHERE rolname = 'authenticator';

-- Set search_path for authenticator role (Supabase uses this)
ALTER ROLE authenticator SET search_path TO public, extensions;

-- Reconnect backend to pick up new search_path
# Restart Railway service
```

### If Migration Fails Midway

**Symptom:** PostGIS dropped but reinstall fails

**Recovery:**
```sql
-- Reinstall in public schema (temporary)
CREATE EXTENSION postgis SCHEMA public;

-- Your data is safe, just fix the migration later
```

Then retry migration with more careful execution.

---

## Post-Migration Verification

### 1. Check Extension Location

```sql
SELECT 
    e.extname,
    n.nspname as schema
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname = 'postgis';

-- Expected: postgis | extensions
```

### 2. Check System Tables

```sql
-- spatial_ref_sys should be in extensions schema
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename = 'spatial_ref_sys';

-- Expected: extensions | spatial_ref_sys
```

### 3. Check Public Schema

```sql
-- Public schema should only have your data
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Expected: properties, search_log (no PostGIS tables)
```

### 4. Check API Exposure

```bash
# Try to access spatial_ref_sys via Supabase API (should fail)
curl "https://jyezhkgevzejhundypxn.supabase.co/rest/v1/spatial_ref_sys" \
  -H "apikey: YOUR_ANON_KEY"

# Expected: 404 or "relation not found" (not exposed)
```

### 5. Run Full Test Suite

```bash
python3 tests/test_production_suite.py

# All tests should pass
```

### 6. Check Supabase Dashboard

- Wait 24-48 hours
- Check: Settings → Security
- Expected: No alert for spatial_ref_sys (it's no longer in public schema)

---

## Rollback Plan

If something goes wrong and you need to revert:

```sql
-- Drop PostGIS from extensions schema
DROP EXTENSION IF EXISTS postgis CASCADE;

-- Reinstall in public schema (original state)
CREATE EXTENSION postgis SCHEMA public;

-- Reset search_path
ALTER DATABASE postgres SET search_path TO public;

-- Test backend
-- (Should work - back to original state)
```

Your data is never at risk - the properties table and its geog column are never modified.

---

## Update Your Configuration

### After Migration Succeeds

**1. Update connection strings (if needed)**

Most clients don't need changes - search_path handles schema resolution.

**2. Update documentation**

```markdown
# Add to CLAUDE.md or db/SCHEMA.md

PostGIS Extension:
- Schema: extensions (not public)
- System tables: extensions.spatial_ref_sys, extensions.geometry_columns
- Not exposed via Supabase API
- Backend accesses via search_path: public, extensions
```

**3. Update security tests**

```python
# In tests/test_production_suite.py

# Remove exclusion for spatial_ref_sys in public schema
# It's no longer there!

# Add check that PostGIS is in extensions schema
postgis_schema = await conn.fetchval("""
    SELECT n.nspname 
    FROM pg_extension e
    JOIN pg_namespace n ON e.extnamespace = n.oid
    WHERE e.extname = 'postgis'
""")

if postgis_schema == 'extensions':
    results.add_pass("PostGIS Location", "In extensions schema (not exposed via API)")
else:
    results.add_warning("PostGIS Location", f"In {postgis_schema} schema (should be extensions)")
```

**4. Update security audit**

```python
# In scripts/security_audit.py

# Remove spatial_ref_sys from exclusion list
# It's no longer in public schema

# Add check that public schema only has your data
public_tables = await conn.fetch("""
    SELECT tablename FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename NOT LIKE 'pg_%'
""")

postgis_tables = [t for t in public_tables if t['tablename'] in 
    ['spatial_ref_sys', 'geometry_columns', 'geography_columns']]

if postgis_tables:
    audit.warning("Schema", f"PostGIS tables in public: {postgis_tables}")
else:
    audit.success("Schema", "PostGIS properly isolated in extensions schema")
```

---

## Timeline Estimate

**Preparation:** 15 minutes
- Review checklist
- Create backup
- Read through migration steps

**Execution:** 10 minutes
- Run SQL commands
- Test functions
- Verify backend

**Verification:** 15 minutes
- Run test suite
- Check all endpoints
- Monitor for errors

**Total:** ~40 minutes

**Recommended timing:**
- Low-traffic period (early morning)
- Or schedule maintenance window
- Have rollback ready if needed

---

## Benefits After Migration

### Security

✅ **PostGIS system tables not exposed via API**
- spatial_ref_sys not accessible via Supabase REST API
- No RLS needed (not in public schema)
- Reduced attack surface

✅ **Cleaner separation of concerns**
- Extensions in extensions schema
- Application data in public schema
- System tables separated from user data

### Compliance

✅ **Follows Supabase best practices**
- Extensions in dedicated schema
- Proper schema isolation
- Aligns with official documentation

✅ **No more false-positive alerts**
- spatial_ref_sys alert will never return
- Security dashboard stays clean
- Less noise, more signal

### Maintenance

✅ **Easier to manage**
- Clear separation of extension vs. data
- Future extensions follow same pattern
- Simpler RLS policies (only on data tables)

---

## Summary

**Current state:** PostGIS in `public` schema → triggers security alerts  
**Recommended state:** PostGIS in `extensions` schema → no API exposure  
**Migration:** Drop and recreate extension (your data stays safe)  
**Downtime:** ~10 minutes (or schedule maintenance window)  
**Risk:** Low (data preserved, straightforward rollback)  

**After migration:**
- ✅ No RLS needed on PostGIS tables (not exposed)
- ✅ Security alert resolves permanently
- ✅ Cleaner architecture
- ✅ Follows Supabase best practices

---

**Next Steps:**
1. Review this guide
2. Schedule migration window (or do during low traffic)
3. Create backup
4. Execute migration
5. Verify everything works
6. Update documentation
7. Reply to Supabase ticket: "Migrated PostGIS to extensions schema"

**Files to Update After Migration:**
- `scripts/security_audit.py` - Remove spatial_ref_sys exclusion
- `tests/test_production_suite.py` - Add PostGIS schema check
- `db/SCHEMA.md` - Document new structure
- `SECURITY_TRACKING.md` - Mark as resolved
