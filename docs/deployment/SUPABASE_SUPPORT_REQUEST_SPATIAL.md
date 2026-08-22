# Email to Supabase Support - spatial_ref_sys Alert

**Copy-paste this into Supabase support ticket**

---

**Subject:** Security Alert False Positive: spatial_ref_sys (PostGIS System Table)

**To:** Supabase Support

**Project ID:** jyezhkgevzejhundypxn

---

Hello Supabase Support Team,

I'm receiving a security alert for the table `spatial_ref_sys` not having Row-Level Security (RLS) enabled:

```
Entity: public.spatial_ref_sys
Issue: Table public.spatial_ref_sys is public, but RLS has not been enabled.
```

## Issue Summary

This is a **false positive** - `spatial_ref_sys` is a PostGIS system table, not application data.

**Table Details:**
- **Owner:** `supabase_admin` (not my user account)
- **Purpose:** PostGIS coordinate system reference data (EPSG definitions)
- **Content:** 8,500+ public coordinate system definitions
- **Data Type:** Read-only reference data
- **Extension:** Part of PostGIS extension
- **Managed By:** Supabase platform

**Verification:**
```sql
SELECT tableowner, rowsecurity 
FROM pg_tables 
WHERE tablename = 'spatial_ref_sys';

Result:
tableowner: supabase_admin
rowsecurity: false
```

## Why This Is Not a Security Risk

1. **No sensitive data** - Contains only public EPSG coordinate definitions (e.g., "SRID 4326 = WGS 84")
2. **Reference data** - Industry-standard coordinate systems, not user data
3. **Read-only** - Application only reads for coordinate transformations
4. **System table** - Managed by PostGIS/Supabase, not the application
5. **Cannot modify** - Owned by `supabase_admin`, user lacks permissions

**My Application Data:**
- `properties` table: ✅ RLS enabled, policies configured
- All user data tables: ✅ Properly secured

**PostGIS System Tables:**
- `spatial_ref_sys`: ⚠️ Alert triggered (but safe)

## Request

Could you please take one of the following actions:

### Option A: Suppress This Alert (Preferred)

Exclude `spatial_ref_sys` and other PostGIS system tables from security scans for this project:
- `spatial_ref_sys`
- `geometry_columns`
- `geography_columns`
- `raster_columns`
- `raster_overviews`

These are all PostGIS-managed system tables containing reference/metadata, not user data.

### Option B: Platform-Level RLS

If Supabase policy requires RLS on all public schema tables, could you enable it at the platform level?

```sql
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON spatial_ref_sys
    FOR SELECT TO public USING (true);
```

Since the table is owned by `supabase_admin`, users cannot make this change themselves.

## Supporting Documentation

**PostGIS Documentation:**
- https://postgis.net/docs/using_postgis_dbmanagement.html#spatial_ref_sys
- Standard PostGIS system table present in all installations
- Contains EPSG coordinate system definitions (public data)

**Industry Practice:**
- Every PostGIS database has this table in public schema
- Standard practice is to leave unprotected (it's reference data)
- Similar to system tables in `pg_catalog` or `information_schema`

**My Security Posture:**
- Application data: ✅ All tables have RLS enabled
- API security: ✅ CORS restricted, security headers configured
- Secrets: ✅ Environment variables only, none in codebase
- Monitoring: ✅ Weekly security audits automated

## Context

I take security seriously and have implemented:
- Row-Level Security on all application tables
- Automated security testing in CI/CD
- Pre-commit hooks to prevent security regressions
- Weekly security audits

This alert is for a PostGIS system table, not my application data. My actual data tables are properly secured.

## Conclusion

**Request:** Please suppress security alerts for PostGIS system tables, or enable RLS on them at the platform level.

**Reason:** These are reference data tables managed by Supabase/PostGIS, not application data requiring RLS.

**Evidence:** Table is owned by `supabase_admin`, contains only public EPSG definitions, application data is properly secured.

Thank you for your assistance with this false positive.

Best regards,
[Your Name]
[Your Email]

---

## Alternative: Shorter Version

If you prefer a more concise message:

---

**Subject:** Request: Suppress RLS Alert for PostGIS System Table

Hello Supabase Support,

I'm receiving a security alert for `spatial_ref_sys`, which is a PostGIS system table owned by `supabase_admin`, not application data.

**Table:** spatial_ref_sys  
**Owner:** supabase_admin  
**Content:** Public EPSG coordinate definitions (reference data)  
**Risk:** None - no sensitive data, read-only, managed by platform  

**Request:** Please suppress this alert or enable RLS at the platform level.

My application tables (`properties`, etc.) are properly secured with RLS enabled.

Thank you.

---

## What to Expect

**Best Case:**
- Supabase acknowledges this is a known false positive
- They suppress the alert for your project
- Alert removed within 1-2 business days

**Likely Case:**
- Supabase enables RLS on the table at platform level
- Adds public read policy
- Alert cleared within 3-5 business days

**If They Ask for More Info:**
- Provide `SUPABASE_SPATIAL_REF_SYS.md` (full documentation)
- Show query results proving it's a system table
- Reference PostGIS documentation

---

**Status:** Ready to send  
**Priority:** Low (false positive, no actual security risk)  
**Urgency:** Not urgent (can wait for support response)
