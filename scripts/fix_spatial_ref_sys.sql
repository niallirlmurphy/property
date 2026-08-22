-- Fix for spatial_ref_sys RLS warning from Supabase
-- Based on Supabase latest RLS guidance (June 2026)
--
-- spatial_ref_sys is a PostGIS system table containing SRID metadata
-- (coordinate system definitions). It's reference data, not user data.
--
-- Two options:
-- 1. Enable RLS with read-only public access (if frontend needs it)
-- 2. Revoke public access (if only backend needs it)
--
-- For homeiq.ie: We use ST_Transform and similar functions which need
-- spatial_ref_sys access. However, PostGIS handles this internally, so
-- API clients don't need direct access.
--
-- RECOMMENDED: Revoke public access (backend can still use it)

-- Check current status
SELECT
    tablename,
    tableowner,
    rowsecurity,
    (SELECT count(*) FROM pg_policies WHERE tablename = 'spatial_ref_sys') as policy_count
FROM pg_tables
WHERE tablename = 'spatial_ref_sys';

-- Option 1: Enable RLS with read-only access
-- Use this if your frontend makes direct PostGIS queries
-- (Uncomment to use)

-- ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY "Allow public read access to coordinate systems"
-- ON spatial_ref_sys
-- FOR SELECT
-- TO anon, authenticated
-- USING (true);

-- Option 2: Revoke public API access (RECOMMENDED)
-- Backend/service role can still access it
-- API clients (anon/authenticated) cannot

-- Note: This requires admin/owner privileges
-- Run via Supabase SQL Editor or as postgres role

REVOKE ALL ON spatial_ref_sys FROM anon;
REVOKE ALL ON spatial_ref_sys FROM authenticated;

-- Verify service_role can still access (backend needs this)
GRANT SELECT ON spatial_ref_sys TO service_role;

-- Enable RLS anyway for hardening
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- No policies needed - only service_role has access
-- This follows least-privilege: API clients don't need SRID metadata

-- Verification queries:
-- Check RLS is enabled
SELECT
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'spatial_ref_sys';

-- Check privileges
SELECT
    grantee,
    privilege_type
FROM information_schema.table_privileges
WHERE table_name = 'spatial_ref_sys'
AND grantee IN ('anon', 'authenticated', 'service_role')
ORDER BY grantee, privilege_type;

-- Test that backend can still use PostGIS functions
-- (This should work even with RLS enabled and no public access)
SELECT ST_Transform(
    ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326),
    2157
) as irish_grid_coords;

-- Expected result: Backend queries work, API access blocked
