# Supabase Alert: spatial_ref_sys RLS

**Alert Received:** June 9, 2026  
**Entity:** `public.spatial_ref_sys`  
**Issue:** "Table public.spatial_ref_sys is public, but RLS has not been enabled"  
**Status:** ✅ FALSE POSITIVE - Safe to ignore or suppress  

---

## What is spatial_ref_sys?

`spatial_ref_sys` is a **PostGIS system table**, not user data. It contains reference coordinate system definitions used by PostGIS for spatial calculations.

**Table Info:**
- **Owner:** `supabase_admin` (not your user)
- **Purpose:** Reference data for 8,500+ coordinate systems (EPSG codes)
- **Data Type:** Read-only lookups (SRID definitions)
- **Extension:** Part of PostGIS extension
- **Managed By:** Supabase/PostGIS, not your application

**Sample Data:**
```
SRID 4326: WGS 84 (GPS coordinates)
SRID 2157: Irish Transverse Mercator  
SRID 3857: Web Mercator (used by Google Maps)
... (8,497 more)
```

This is reference data similar to timezone definitions or currency codes - it's not your application data and doesn't contain any sensitive information.

---

## Why Can't We Enable RLS?

**Permission Error:**
```
asyncpg.exceptions.InsufficientPrivilegeError: must be owner of table spatial_ref_sys
```

You don't own this table - it's owned by `supabase_admin` and managed by Supabase. This is **correct behavior** - system tables should be managed by the platform, not individual projects.

---

## Is This a Security Risk?

**NO.** This is not a security vulnerability because:

1. **No sensitive data:** Contains only public EPSG coordinate system definitions
2. **Read-only data:** Reference data that never changes per project
3. **System table:** Managed by Supabase, not your application
4. **No write access:** Your application only reads from this table (for ST_Transform operations)
5. **Standard PostGIS:** Every PostGIS database has this table in the same state

**Comparison:**
- `properties` table: YOUR data, needs RLS ✅ (enabled)
- `spatial_ref_sys` table: POSTGIS data, managed by system ✅ (safe as-is)

---

## What Does This Table Do in Your App?

When you use PostGIS functions like `ST_Transform` to convert coordinates:

```sql
-- Convert from WGS84 (GPS) to Irish Grid
SELECT ST_Transform(
    ST_SetSRID(ST_MakePoint(lon, lat), 4326),  -- 4326 = WGS84
    2157                                         -- 2157 = Irish Transverse Mercator
)
```

PostGIS looks up SRID definitions in `spatial_ref_sys`:
- SRID 4326 → WGS 84 coordinate system definition
- SRID 2157 → Irish Transverse Mercator definition

It's a **lookup table**, not data storage.

---

## Response Options

### Option 1: Suppress the Alert (Recommended)

Contact Supabase support to suppress this specific alert:

```
Subject: False Positive: spatial_ref_sys RLS Alert

Hello Supabase Support,

I'm receiving a security alert for table `spatial_ref_sys` not having RLS enabled.

This is a PostGIS system table owned by `supabase_admin`, not user data. 
The table contains only EPSG coordinate system reference data (8,500+ rows 
of public coordinate definitions).

Request:
1. Suppress this alert for `spatial_ref_sys` on project [jyezhkgevzejhundypxn]
2. Or: Provide documentation on proper handling of PostGIS system tables

The table is safe as-is - it contains no sensitive data and is managed by 
the platform, not my application.

Thank you.
```

### Option 2: Exclude from Security Scans

Ask Supabase if they have an `.supabase/config.yml` or similar to exclude system tables:

```yaml
security:
  rls_check:
    exclude_tables:
      - spatial_ref_sys
      - geography_columns
      - geometry_columns
      - raster_columns
      - raster_overviews
```

### Option 3: Request Supabase Enable RLS

If Supabase policy requires RLS on all public schema tables, ask them to enable it:

```
Subject: Request: Enable RLS on spatial_ref_sys

Hello Supabase Support,

To comply with your security requirements, could you enable RLS on the 
PostGIS system table `spatial_ref_sys` in project [jyezhkgevzejhundypxn]?

Since this is owned by `supabase_admin`, I cannot modify it myself.

Suggested policy:
CREATE POLICY "Allow public read" ON spatial_ref_sys 
FOR SELECT TO public USING (true);

This would silence the alert while maintaining the table's intended 
read-only behavior.

Thank you.
```

---

## How to Verify It's Safe

**Check ownership:**
```sql
SELECT tableowner FROM pg_tables WHERE tablename = 'spatial_ref_sys';
-- Result: supabase_admin (not your user)
```

**Check data type:**
```sql
SELECT srid, auth_name, srtext FROM spatial_ref_sys LIMIT 3;
-- Result: EPSG coordinate definitions (public reference data)
```

**Check your application usage:**
```bash
# Search your codebase for spatial_ref_sys
grep -r "spatial_ref_sys" backend/ frontend/ scripts/
# Result: No direct references (PostGIS uses it internally)
```

**Verify no writes:**
```sql
-- Try to insert (should fail)
INSERT INTO spatial_ref_sys (srid, auth_name) VALUES (99999, 'TEST');
-- Error: permission denied (as expected)
```

---

## Similar PostGIS System Tables

If you get alerts for these, they're also system tables (safe):

- `geometry_columns` - Metadata about geometry columns
- `geography_columns` - Metadata about geography columns
- `spatial_ref_sys` - Coordinate system definitions (this one)
- `raster_columns` - Metadata about raster columns (if using raster)
- `raster_overviews` - Raster overview metadata

**All of these are:**
- Owned by `supabase_admin`
- Managed by PostGIS extension
- Read-only reference/metadata
- Not your application data
- Safe without RLS

---

## Update Your Security Tests

Update `scripts/security_audit.py` to exclude PostGIS system tables:

```python
# In audit_database_security function
unprotected = await conn.fetch("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
    AND rowsecurity = false
    AND tablename NOT LIKE 'pg_%'
    AND tablename NOT LIKE 'sql_%'
    AND tablename NOT IN (
        'spatial_ref_sys',           -- PostGIS reference data
        'geometry_columns',           -- PostGIS metadata
        'geography_columns',          -- PostGIS metadata
        'raster_columns',            -- PostGIS metadata
        'raster_overviews'           -- PostGIS metadata
    )
""")
```

This prevents false warnings in your weekly security audits.

---

## Documentation for Supabase Support

If Supabase support asks for justification:

**Talking Points:**
1. `spatial_ref_sys` is a PostGIS extension system table, not application data
2. Contains only public EPSG coordinate system definitions (no PII, no sensitive data)
3. Table is owned by `supabase_admin` - projects cannot modify it
4. Read-only reference data used internally by PostGIS functions
5. Present in all PostGIS databases worldwide in the same state
6. No security risk - equivalent to system tables like `pg_catalog`

**Industry Standard:**
- PostGIS documentation: https://postgis.net/docs/using_postgis_dbmanagement.html#spatial_ref_sys
- Every PostGIS installation has this table in public schema
- Standard practice is to leave it unprotected (it's reference data)

**Security Posture:**
- Application data tables (`properties`): ✅ RLS enabled
- User-facing endpoints: ✅ CORS restricted, headers configured
- Secrets management: ✅ Environment variables only
- System tables: ✅ Managed by platform (spatial_ref_sys)

---

## Summary

**What:** Supabase alert about `spatial_ref_sys` missing RLS  
**Why:** PostGIS system table in public schema  
**Risk:** None - it's public reference data  
**Action:** Request alert suppression or platform-level RLS enable  
**Your Tables:** All protected ✅ (properties has RLS enabled)  

**Bottom Line:** This is a false positive. Your actual data (`properties` table) is properly secured with RLS. The alert is about a PostGIS system table containing public coordinate definitions.

---

**Recommended Action:** Reply to Supabase support with Option 1 (suppress alert) or Option 3 (request they enable RLS).

**Documentation:** Keep this file as evidence that you investigated and determined it's safe.

**Next Alert:** If you get similar alerts for other PostGIS tables (geometry_columns, etc.), same logic applies.
