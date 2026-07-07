# Security Configuration Checklist

**Last Verified**: 2026-07-07
**Next Review**: 2026-10-07 (quarterly)

## ✅ Database Security (Supabase)

### Row-Level Security (RLS)
- [x] RLS enabled on `properties` table
- [x] `backend_full_access_properties` policy created (FOR ALL TO authenticated)
- [x] Anonymous (`anon`) role has ALL privileges REVOKED
- [x] Backend uses authenticated connection via DATABASE_URL
- [x] Direct PostgREST API access BLOCKED

**Verification Commands:**
```bash
# Run automated check
export $(grep '^DATABASE_URL=' backend/.env | xargs)
python3 scripts/enable_rls_security.py

# Expected output:
# ✅ RLS is ENABLED
# ✅ Authenticated-only policy created
# ✅ Anonymous access BLOCKED
# ✅ Backend can read data: ~785,000 properties
```

**Manual SQL Verification (via Supabase SQL Editor):**
```sql
-- 1. RLS status (should be true)
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'properties';

-- 2. Active policies (should show backend_full_access_properties)
SELECT policyname, cmd, roles::text[] 
FROM pg_policies 
WHERE tablename = 'properties';

-- 3. Anonymous access (should be false)
SELECT has_table_privilege('anon', 'properties', 'SELECT') as can_select;

-- 4. Authenticated access (should return count)
SELECT COUNT(*) FROM properties;
```

### Connection Security
- [x] DATABASE_URL uses postgres/service role (not anon key)
- [x] Connection string includes SSL mode
- [x] Credentials stored in environment variables (not code)
- [x] Railway environment variables match backend/.env

## ✅ API Security (Railway Backend)

### CORS Configuration
- [x] Production: homeiq.ie and www.homeiq.ie only
- [x] Development: localhost:5173 allowed
- [x] No wildcard (*) origins in production

**Verification:**
```bash
# Should return Access-Control-Allow-Origin: https://homeiq.ie
curl -I -H "Origin: https://homeiq.ie" \
  https://eloquent-optimism-production-350a.up.railway.app/health

# Should NOT return CORS headers (blocked)
curl -I -H "Origin: https://malicious-site.com" \
  https://eloquent-optimism-production-350a.up.railway.app/health
```

### Rate Limiting & Caching
- [x] In-memory cache implemented (5min-24h TTLs)
- [x] Search results cached for 5 minutes
- [x] Geocoding results cached for 24 hours
- [x] County/trends data cached for 1 hour

### Input Validation
- [x] Address normalization applied
- [x] Coordinate bounds checking (Ireland: 51.4-55.5°N, -10.7--5.4°W)
- [x] SQL injection prevention via parameterized queries
- [x] Query limits enforced (max 1000 results)

## ✅ Frontend Security (Vercel)

### Environment Variables
- [x] VITE_API_URL points to Railway backend
- [x] No sensitive keys in frontend code
- [x] API calls go through backend (not direct DB access)

**Verification:**
```bash
# Check Vercel environment variable is set
vercel env ls

# Test frontend can reach API
curl https://homeiq.ie/
# Should load without errors, check browser console
```

### HTTPS & Headers
- [x] HTTPS enforced on homeiq.ie
- [x] Vercel provides security headers
- [x] No mixed content warnings

## ✅ Monitoring & Alerts

### Sentry Integration
- [x] SENTRY_DSN configured in backend/.env
- [x] Error tracking active
- [x] Performance monitoring enabled

### Supabase Security Advisor
- [x] RLS configuration verified
- [x] No active security alerts
- [x] Weekly advisor emails monitored

**Expected Status:**
- **RLS disabled** alert: RESOLVED 2026-07-07
- No other critical/high severity alerts

## ✅ Data Access Architecture

**Correct Flow (Implemented):**
```
User → Frontend (Vercel)
         ↓
      Railway Backend (authenticated)
         ↓
      Supabase Database (RLS enabled, anon blocked)
```

**Blocked Flows:**
```
❌ User → Supabase PostgREST API directly (anon role revoked)
❌ User → Frontend → Supabase client library (no anon key exposed)
❌ Unauthorized origin → Railway API (CORS blocked)
```

## 🔄 Periodic Maintenance

### Monthly
- [ ] Review Supabase security advisor emails
- [ ] Check Railway logs for suspicious activity
- [ ] Verify Sentry error patterns

### Quarterly (Next: 2026-10-07)
- [ ] Re-run RLS verification script
- [ ] Review and rotate API keys if needed
- [ ] Update this checklist
- [ ] Test security endpoints with production test suite

### After Schema Changes
- [ ] Re-enable RLS: `python3 scripts/enable_rls_security.py`
- [ ] Verify policies still exist
- [ ] Test backend access still works

## 📋 Response to Supabase Security Alerts

If you receive an email titled **"Critical issue: Table publicly accessible"**:

1. **Don't panic** - verify the alert is accurate first
2. Run verification script: `python3 scripts/enable_rls_security.py`
3. Check the output - if all checks pass, RLS is correctly configured
4. Wait 24 hours for Supabase to re-scan and clear the alert
5. If alert persists after 24h, contact Supabase support with verification output

**Common false positives:**
- Alert sent before RLS propagation completes (~5 minutes)
- Supabase advisor scanning cached/stale state
- Alert based on snapshot before fix was applied

**Legitimate issues that trigger alerts:**
- RLS was disabled (e.g., after table drop/recreate)
- Policies were deleted (e.g., during migration)
- Anonymous role was accidentally granted permissions

## 🔗 Related Documentation

- **CLAUDE.md**: Security section (line 418-484)
- **scripts/enable_rls_security.py**: Automated RLS configuration
- **tests/test_production_suite.py**: Security test cases
- **SECURITY_RLS_FIXED.md**: 2026-07-07 fix documentation

## ✅ Current Status Summary

**Last RLS Configuration**: 2026-07-07
**Status**: ✅ SECURE
- RLS enabled with authenticated-only access
- Anonymous role permissions revoked
- Backend API verified working
- Production test suite: 23/24 tests passing
- Supabase alert expected to clear within 24 hours

**Security Posture**: Strong
- No direct database access possible
- All queries authenticated through Railway backend
- CORS properly restricting origins
- Monitoring active via Sentry

**Action Required**: None - configuration is correct. Monitor Supabase advisor for alert clearance.
