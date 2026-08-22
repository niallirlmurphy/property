# Fix: spatial_ref_sys RLS Alert

**Alert:** Table `public.spatial_ref_sys` is public, but RLS has not been enabled  
**Status:** ⏳ Requires Supabase Support (owner-only operation)  
**Priority:** Low (security hardening, not a data breach)  
**Action:** Submit support ticket (template provided below)  

---

## What Supabase Recommends (Latest Guidance)

According to Supabase's latest RLS guidance:

> Tables in API-exposed schemas (public) should have RLS enabled to enforce least-privilege access. For extension-managed tables like `spatial_ref_sys`, either:
> 1. Enable RLS with read-only policies, or
> 2. Revoke public API access (preferred if clients don't need direct access)

---

## Understanding spatial_ref_sys

**What it is:**
- PostGIS system table containing SRID metadata
- 8,500+ coordinate system definitions (EPSG codes)
- Used by PostGIS functions like `ST_Transform`
- Owned by `supabase_admin`, not your application

**Example data:**
```
SRID 4326: WGS 84 (GPS coordinates)
SRID 2157: Irish Transverse Mercator (Irish Grid)
SRID 3857: Web Mercator (Google Maps)
```

**Does your frontend query it directly?**
- ❌ No - our frontend calls backend APIs
- ❌ No - backend uses PostGIS functions internally
- ✅ PostGIS accesses it automatically (no direct queries)

**Conclusion:** API clients (anon/authenticated) don't need access. Backend (service_role) does.

---

## Recommended Fix: Request Supabase Support

**Why this requires support:**
- Table is owned by `supabase_admin` (not your user)
- Even SQL Editor lacks permissions to modify it
- Error: `must be owner of table spatial_ref_sys`
- Only Supabase platform team can modify this table

**Why this option:**
- ✅ Follows least-privilege principle
- ✅ API clients don't need SRID metadata
- ✅ Backend can still use PostGIS functions
- ✅ Reduces attack surface
- ✅ Silences Supabase alert

**How to apply:**

### Step 1: Submit Support Ticket

Copy-paste from `SUPABASE_SUPPORT_TICKET.md` or use this template:

**Subject:** Request: Enable RLS on spatial_ref_sys (PostGIS System Table)

**Message:**
```
Hello Supabase Support,

I'm receiving a security alert for spatial_ref_sys not having RLS enabled 
(Project ID: jyezhkgevzejhundypxn).

I attempted to fix via SQL Editor but received:
ERROR: 42501: must be owner of table spatial_ref_sys

Could you please enable RLS on this table at the platform level?

Recommended SQL:
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON spatial_ref_sys FROM anon, authenticated;
GRANT SELECT ON spatial_ref_sys TO service_role;

Context: This is a PostGIS system table. My app doesn't query it directly.
My application data tables already have RLS enabled.

Thank you.
```

### Step 2: Wait for Supabase Response

**Expected timeline:** 1-3 business days

**Likely outcomes:**
1. ✅ **Best case:** They enable RLS and restrict access → alert clears
2. ✅ **Alternative:** They suppress the alert for PostGIS tables
3. ℹ️ **Guidance:** They provide official guidance on handling this

### Step 3: Verify After Fix (If Supabase Enables RLS)

```sql
-- Revoke API access (anon/authenticated cannot query)
REVOKE ALL ON spatial_ref_sys FROM anon;
REVOKE ALL ON spatial_ref_sys FROM authenticated;

-- Ensure backend can still access
GRANT SELECT ON spatial_ref_sys TO service_role;

-- Enable RLS for hardening
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- Verify
SELECT
    tablename,
    rowsecurity as rls_enabled,
    (SELECT count(*) FROM pg_policies WHERE tablename = 'spatial_ref_sys') as policies
FROM pg_tables
WHERE tablename = 'spatial_ref_sys';

-- Check privileges
SELECT grantee, privilege_type
FROM information_schema.table_privileges
WHERE table_name = 'spatial_ref_sys'
AND grantee IN ('anon', 'authenticated', 'service_role')
ORDER BY grantee;
```

### Step 3: Test Backend Still Works

```sql
-- This should succeed (backend using PostGIS internally)
SELECT ST_Transform(
    ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326),
    2157
) as irish_grid_coords;

-- Expected: Returns Irish Grid coordinates
-- (Proves backend can still use PostGIS/spatial_ref_sys)
```

### Step 4: Verify in Production

```bash
# Test backend API (should work)
curl https://eloquent-optimism-production-350a.up.railway.app/search?q=Dublin

# If this works, PostGIS is functioning correctly
# (backend accesses spatial_ref_sys via service_role)
```

**Expected Result:**
- ✅ RLS enabled on spatial_ref_sys
- ✅ API clients (anon/authenticated) have no access
- ✅ Backend (service_role) retains SELECT access
- ✅ PostGIS functions work normally
- ✅ Supabase alert clears within 24-48 hours

---

## Alternative: Enable RLS with Read-Only Access

**Use this if:** Your frontend makes direct PostGIS queries (we don't)

```sql
-- Enable RLS
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- Allow read-only access
CREATE POLICY "Allow public read access to coordinate systems"
ON spatial_ref_sys
FOR SELECT
TO anon, authenticated
USING (true);

-- Verify
SELECT policyname, cmd, roles
FROM pg_policies
WHERE tablename = 'spatial_ref_sys';
```

**When to use:**
- Frontend queries PostGIS directly via Supabase client
- You need to expose GIS functions via PostgREST API
- Frontend uses `ST_Distance`, `ST_Within`, etc. via SQL

**For homeiq.ie:** Not needed - we use backend APIs, not direct PostGIS queries.

---

## Why Can't We Do This via Python?

```python
# This fails:
await conn.execute("REVOKE ALL ON spatial_ref_sys FROM anon")

# Error:
# asyncpg.exceptions.InsufficientPrivilegeError:
# must be owner of table spatial_ref_sys
```

**Reason:** 
- Table is owned by `supabase_admin`
- Python script connects as your user role
- Only admin/owner can modify permissions

**Solution:** Use Supabase SQL Editor (runs as admin)

---

## Impact Assessment

**Before Fix:**
```
RLS: DISABLED
Access: anon ✅, authenticated ✅, service_role ✅
Alert: ⚠️ Table exposed without RLS
Risk: Low (reference data only)
```

**After Fix (Recommended):**
```
RLS: ENABLED
Access: anon ❌, authenticated ❌, service_role ✅
Alert: ✅ Clear
Risk: Minimal (least-privilege)
```

**Does this break anything?**
- ❌ No - frontend doesn't query this table
- ❌ No - backend uses service_role (still has access)
- ❌ No - PostGIS functions work internally
- ✅ Yes - API clients can't query it (intended)

---

## Post-Fix Verification Checklist

After applying the fix:

### 1. Check RLS Status
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'spatial_ref_sys';

-- Expected: rowsecurity = true
```

### 2. Check Privileges
```sql
SELECT grantee, privilege_type
FROM information_schema.table_privileges
WHERE table_name = 'spatial_ref_sys'
AND grantee IN ('anon', 'authenticated', 'service_role');

-- Expected:
-- anon: (no rows)
-- authenticated: (no rows)
-- service_role: SELECT
```

### 3. Test Backend API
```bash
# Should return results (proves backend works)
curl "https://eloquent-optimism-production-350a.up.railway.app/search?q=Dublin" | jq '.properties | length'

# Expected: 200 (or similar)
```

### 4. Test PostGIS Functions
```bash
# Via backend
curl "https://eloquent-optimism-production-350a.up.railway.app/geocode?q=Dublin"

# Expected: Returns lat/lon coordinates
```

### 5. Check Supabase Dashboard
- Wait 24-48 hours
- Check: https://supabase.com/dashboard/project/jyezhkgevzejhundypxn/settings/security
- Expected: spatial_ref_sys alert cleared

### 6. Run Local Security Tests
```bash
python3 tests/test_production_suite.py

# Expected: All security tests pass
```

---

## Troubleshooting

### If Backend API Breaks After Fix

**Symptom:** Backend returns errors about coordinate transformations

**Diagnosis:**
```sql
-- Check if service_role lost access
SELECT grantee, privilege_type
FROM information_schema.table_privileges
WHERE table_name = 'spatial_ref_sys'
AND grantee = 'service_role';

-- Should return: SELECT
```

**Fix:**
```sql
GRANT SELECT ON spatial_ref_sys TO service_role;
```

### If Alert Doesn't Clear

**Wait:** Supabase security scans run periodically (24-48 hours)

**Manual refresh:**
1. Go to Supabase Dashboard → Settings → Security
2. Click "Refresh" or "Re-scan"
3. Alert should disappear

**If still showing:**
Contact Supabase support:
```
Subject: RLS Alert Not Clearing - spatial_ref_sys

Hello,

I've enabled RLS on spatial_ref_sys and revoked public access per your guidance:
- RLS: ENABLED
- Privileges: anon/authenticated revoked, service_role granted
- Verified: All backend queries work

The security alert is still showing. Could you refresh the security scan?

Project ID: jyezhkgevzejhundypxn
Table: public.spatial_ref_sys

Thank you.
```

---

## Update Your Security Tests

After fixing, update the security audit to verify this table:

```python
# In scripts/security_audit.py

# Check that spatial_ref_sys has RLS enabled
spatial_rls = await conn.fetchrow("""
    SELECT rowsecurity
    FROM pg_tables
    WHERE tablename = 'spatial_ref_sys'
""")

if spatial_rls and spatial_rls['rowsecurity']:
    audit.success("PostGIS Tables", "spatial_ref_sys has RLS enabled")
else:
    audit.warning("PostGIS Tables", "spatial_ref_sys missing RLS")

# Check that anon/authenticated don't have access
spatial_privs = await conn.fetch("""
    SELECT grantee
    FROM information_schema.table_privileges
    WHERE table_name = 'spatial_ref_sys'
    AND grantee IN ('anon', 'authenticated')
""")

if len(spatial_privs) == 0:
    audit.success("PostGIS Privileges", "Public API access revoked (least-privilege)")
else:
    audit.warning("PostGIS Privileges", f"Public has access: {[p['grantee'] for p in spatial_privs]}")
```

---

## Summary

**Problem:** Supabase alert - spatial_ref_sys exposed without RLS  
**Root Cause:** PostGIS system table in API-exposed schema  
**Security Risk:** Low (reference data), but violates least-privilege  
**Recommended Fix:** Revoke public access, enable RLS  
**Why:** API clients don't need SRID metadata  
**Impact:** None (backend retains access via service_role)  

**Action Required:**
1. Open Supabase SQL Editor
2. Run the fix SQL (revoke + enable RLS)
3. Verify backend still works
4. Wait for alert to clear (24-48h)

**Status After Fix:**
- ✅ RLS enabled (hardening)
- ✅ Least-privilege enforced
- ✅ Backend unaffected
- ✅ Alert cleared

---

**Files:**
- SQL script: `scripts/fix_spatial_ref_sys.sql`
- Full guide: This document
- Support template: `SUPABASE_SUPPORT_REQUEST_SPATIAL.md` (if issues)

**Next Steps:**
1. Apply fix via Supabase SQL Editor
2. Run post-fix verification checklist
3. Update security tests to monitor this table
4. Document in security incident log
