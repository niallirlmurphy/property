# Security Checklist - HomeIQ Database

## DESIGN RULE: No Direct Database Access

**Critical Principle:** Anonymous users MUST NEVER have direct access to the Supabase database.

### Architecture
```
Internet
   ↓
Frontend (Vercel) - JavaScript/React
   ↓
Backend API (Railway) - FastAPI with DATABASE_URL credentials
   ↓
Supabase Database - PostgreSQL with RLS
```

### Security Requirements

#### ✅ Database Access Control
- [ ] RLS enabled on all data tables
- [ ] `anon` role has ZERO permissions (no GRANT statements)
- [ ] `authenticated` role has appropriate access for backend
- [ ] Backend connects via `DATABASE_URL` with postgres/authenticated credentials
- [ ] Direct Supabase REST API returns 401/403 for unauthenticated requests

#### ✅ Verification Commands
```bash
# Check RLS status
psql $DATABASE_URL -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';"

# Check anon permissions (should return all FALSE)
psql $DATABASE_URL -c "SELECT 
    has_table_privilege('anon', 'properties', 'SELECT') as can_select,
    has_table_privilege('anon', 'properties', 'INSERT') as can_insert,
    has_table_privilege('anon', 'properties', 'UPDATE') as can_update,
    has_table_privilege('anon', 'properties', 'DELETE') as can_delete;"

# Check policies
psql $DATABASE_URL -c "SELECT tablename, policyname, cmd, roles FROM pg_policies WHERE tablename = 'properties';"

# Test direct API access (should return 401)
curl https://jyezhkgevzejhundypxn.supabase.co/rest/v1/properties?limit=1
```

#### ✅ Test Suite Validation
```bash
# Run security tests
python3 tests/test_production_suite.py

# Expected results:
# ✅ RLS enabled on properties table
# ✅ Security policies configured (authenticated only)
# ✅ Read access verified
# ✅ Write protection verified
# ✅ Anonymous writes blocked
```

### Common Security Anti-Patterns

#### ❌ NEVER DO THIS
```sql
-- WRONG: Grants public read access
GRANT SELECT ON properties TO anon;

-- WRONG: Public read policy
CREATE POLICY "Allow public read access"
ON properties FOR SELECT TO public USING (true);
```

#### ✅ CORRECT APPROACH
```sql
-- Revoke all anonymous access
REVOKE ALL ON properties FROM anon;

-- Only authenticated backend can access
CREATE POLICY "backend_full_access_properties"
ON properties FOR ALL TO authenticated
USING (true) WITH CHECK (true);
```

### Why This Matters

**Without this design rule:**
- ❌ Anyone can query Supabase directly via PostgREST API
- ❌ No rate limiting on direct database queries
- ❌ No logging/monitoring of database access
- ❌ No input validation or sanitization
- ❌ Potential for data scraping or abuse
- ❌ Cannot implement API-level features (caching, analytics, etc.)

**With authenticated-only access:**
- ✅ All queries go through controlled FastAPI backend
- ✅ Backend enforces rate limits, validation, caching
- ✅ Search analytics tracked in application code
- ✅ API-level monitoring with Sentry
- ✅ Can implement query optimization and caching strategies
- ✅ Single point of control for all data access

### Supabase Advisor Compliance

This configuration satisfies Supabase's security requirements:
- ✅ RLS enabled (no "Table publicly accessible" warnings)
- ✅ Appropriate policies in place
- ✅ Anonymous access blocked by design
- ✅ Backend uses authenticated connection

**Expected Supabase Advisor Status:**
- No critical security warnings
- RLS confirmed enabled
- Policies validated

### New Table Checklist

When creating new tables, always:
1. Enable RLS: `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;`
2. Create authenticated policy: `CREATE POLICY ... TO authenticated`
3. Revoke anon access: `REVOKE ALL ON <table> FROM anon;`
4. Test: Verify anon cannot access table
5. Verify: Backend can access via DATABASE_URL

### Maintenance

**Monthly checks:**
- [ ] Review Supabase Advisor for security warnings
- [ ] Run test suite security tests
- [ ] Verify no new public policies added
- [ ] Check anon role still has zero permissions

**After any schema changes:**
- [ ] Re-run `python3 scripts/enable_rls_security.py`
- [ ] Run test suite
- [ ] Verify production API still works

### Emergency Response

If Supabase reports "Table publicly accessible":
1. Immediately revoke anon access: `REVOKE ALL ON <table> FROM anon;`
2. Drop any public policies: `DROP POLICY IF EXISTS "<public_policy>" ON <table>;`
3. Verify: `SELECT has_table_privilege('anon', '<table>', 'SELECT');` returns FALSE
4. Test: Production API should still work
5. Run test suite to confirm

### References
- CLAUDE.md: Security section
- SECURITY_FIX_2026-07-01.md: Historical fix documentation
- scripts/enable_rls_security.py: Automated security setup
- tests/test_production_suite.py: Security test validation
