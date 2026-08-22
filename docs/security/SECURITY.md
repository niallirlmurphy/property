# Security Implementation Guide

**Status:** ✅ Security-first development enabled  
**Last Updated:** June 9, 2026  
**Goal:** ZERO security vulnerabilities, ZERO security alerts from external services  

---

## Philosophy: Security Woven Into Everything

We don't disable security alerts - we prevent them by making security checks mandatory at every step. Security is not an afterthought; it's part of the definition of "done."

**Core Principle:** Every change must maintain or improve security posture. No exceptions.

---

## Automated Security Layers

### Layer 1: Pre-Commit Checks (Immediate)

**Git hook:** `.git/hooks/pre-commit`  
**Runs:** Before every `git commit`  
**Blocks commits that:**
- Include .env files
- Contain hardcoded secrets (API keys, passwords)
- Disable Row-Level Security
- Set CORS to wildcard (`*`)
- Drop security policies without replacement

**Example:**
```bash
git add .
git commit -m "Add feature"

# Output:
🔒 Running security checks...
❌ BLOCKED: .env file in commit
   Files with secrets should never be committed
   Run: git reset HEAD .env
```

**Bypass:** Never bypass. If hook prevents commit, fix the issue.

### Layer 2: Test Suite (Before Push)

**Script:** `tests/test_production_suite.py`  
**Runs:** Manually before push, automatically in CI/CD  
**Tests:**
- ✅ RLS enabled on all tables
- ✅ Security policies configured correctly  
- ✅ Public read access works
- ✅ Anonymous write access blocked
- ✅ Security headers present
- ✅ CORS properly configured
- ✅ No sensitive endpoints exposed

**Run before every push:**
```bash
python3 tests/test_production_suite.py

# Must see:
✅ RLS enabled on properties table
✅ Security policies configured
✅ Write protection verified
✅ Security headers present
```

### Layer 3: Weekly Audit (Continuous)

**Script:** `scripts/security_audit.py`  
**Schedule:** Weekly (manual or cron)  
**Checks:**
- Database RLS status on all tables
- Security policies still active
- No secrets in recent commits
- API security configuration
- File permissions on .env files

**Run weekly:**
```bash
python3 scripts/security_audit.py

# Goal: 0 issues, minimal warnings
```

### Layer 4: External Monitoring (Passive)

**Services:**
- Supabase security alerts (enabled, not silenced)
- Sentry error tracking
- Railway/Vercel deploy logs

**Response:** If any alert arrives, treat as P0 incident.

---

## Security Checklist by Task Type

### Adding New Database Table

```bash
# 1. Create table with RLS in same migration
CREATE TABLE new_table (
    id SERIAL PRIMARY KEY,
    data TEXT
);

# 2. IMMEDIATELY enable RLS (same migration)
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

# 3. Create appropriate policies
CREATE POLICY "public_read" ON new_table
    FOR SELECT TO public USING (true);

CREATE POLICY "auth_write" ON new_table  
    FOR ALL TO authenticated USING (true);

# 4. Test
python3 -c "
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchrow('''
        SELECT rowsecurity FROM pg_tables 
        WHERE tablename = '\''new_table'\''
    ''')
    print(f'RLS: {\"ENABLED\" if result[\"rowsecurity\"] else \"DISABLED\"}')
    await conn.close()

asyncio.run(test())
"

# 5. Add to test suite
# Edit tests/test_production_suite.py to include new table
```

**✅ Done when:**
- [ ] RLS enabled
- [ ] Policies created
- [ ] Test added
- [ ] Security audit passes

### Adding New API Endpoint

```python
# backend/main.py

# 1. Input validation with Pydantic
from pydantic import BaseModel, validator

class NewEndpointRequest(BaseModel):
    user_input: str
    
    @validator('user_input')
    def validate_input(cls, v):
        # Sanitize, validate, reject malicious input
        if len(v) > 1000:
            raise ValueError('Input too long')
        return v.strip()

# 2. Use parameterized queries (NEVER string interpolation)
@app.post("/new-endpoint")
async def new_endpoint(request: NewEndpointRequest):
    # ✅ GOOD: Parameterized
    result = await conn.fetch(
        "SELECT * FROM table WHERE field = $1",
        request.user_input
    )
    
    # ❌ BAD: SQL injection risk
    # result = await conn.fetch(
    #     f"SELECT * FROM table WHERE field = '{request.user_input}'"
    # )
    
    return result

# 3. Add rate limiting (if write endpoint)
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/write-endpoint")
@limiter.limit("10/minute")
async def write_endpoint(request: Request):
    # ... implementation
    pass
```

**✅ Done when:**
- [ ] Input validated with Pydantic
- [ ] Parameterized queries only
- [ ] Rate limiting on writes
- [ ] CORS tested
- [ ] Added to test suite

### Deploying Changes

```bash
# 1. Run full test suite
python3 tests/test_production_suite.py

# 2. Check for secrets
git diff main | grep -E "(DATABASE_URL|MAPBOX_TOKEN|password|secret)"

# 3. Review security checklist
# - No .env files staged
# - No hardcoded secrets
# - RLS still enabled
# - Tests passing

# 4. Commit (pre-commit hook runs automatically)
git add .
git commit -m "Add feature X"

# 5. Push (CI runs tests again)
git push origin main

# 6. Verify deploy
# - Check Railway/Vercel logs
# - Run smoke test on production
# - Monitor for errors in Sentry
```

**✅ Done when:**
- [ ] Tests pass locally
- [ ] Pre-commit checks pass
- [ ] CI/CD checks pass
- [ ] Production smoke test passes
- [ ] No new Sentry errors

---

## Security Configuration Details

### Database (Supabase/Postgres)

**Current Configuration:**
```sql
-- Properties table (main data)
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

-- Policy 1: Public can read (PPR data is public by law)
CREATE POLICY "Allow public read access" ON properties
    FOR SELECT TO public USING (true);

-- Policy 2: Authenticated users can write (backend operations)
CREATE POLICY "backend_full_access_properties" ON properties
    FOR ALL TO authenticated USING (true);
```

**Verification:**
```bash
# Check RLS status
psql $DATABASE_URL -c "
    SELECT tablename, rowsecurity 
    FROM pg_tables 
    WHERE tablename = 'properties';
"

# Check policies
psql $DATABASE_URL -c "
    SELECT policyname, cmd, roles 
    FROM pg_policies 
    WHERE tablename = 'properties';
"
```

**Expected Output:**
```
tablename   | rowsecurity
------------|------------
properties  | t           ✅

policyname                     | cmd    | roles
-------------------------------|--------|------------------
Allow public read access       | SELECT | {public}
backend_full_access_properties | ALL    | {authenticated}
```

### API (FastAPI/Railway)

**CORS Configuration:**
```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware

# ✅ PRODUCTION (restrictive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://homeiq.ie",
        "https://www.homeiq.ie",
        "http://localhost:5173"  # Development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ❌ NEVER DO THIS IN PRODUCTION
# allow_origins=["*"]  # Allows any website to call your API
```

**Security Headers:**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Frontend (React/Vercel)

**Environment Variables:**
```bash
# frontend/.env.local (NOT COMMITTED)
VITE_API_URL=https://eloquent-optimism-production-350a.up.railway.app

# ✅ Starts with VITE_ = safe to expose to client
# ❌ Never put secrets in VITE_ variables (visible in browser)
```

**API Key Safety:**
```typescript
// ✅ GOOD: No API keys in frontend
const response = await fetch(`${import.meta.env.VITE_API_URL}/search?q=${query}`);

// ❌ BAD: API key exposed in client code
// const response = await fetch(`https://api.mapbox.com/...?access_token=pk.xxx`);
// Anyone can view source and steal the key!
```

---

## Incident Response

### When Security Alert Arrives

**Priority:** P0 (Drop everything)

**Response Steps:**
1. **Acknowledge immediately** (< 15 minutes)
2. **Assess severity:**
   - Critical: RLS disabled, secrets exposed, data accessible
   - High: Policies missing, CORS misconfigured
   - Medium: Missing security headers, outdated dependencies
3. **Fix same day:**
   - Run `python3 scripts/enable_rls_security.py`
   - Run `python3 tests/test_production_suite.py`
   - Verify fix in production
4. **Document:**
   - Add to security incident log
   - Update tests to prevent regression
   - Review: How did this bypass our checks?
5. **Reply to alert service:**
   - Confirm issue resolved
   - Provide evidence (test results)
   - Request removal from alert list

**Example Response to Supabase:**
```
Subject: Security Issue Resolved - Project [ID]

Hello Supabase Security Team,

The reported RLS issue has been resolved:
✅ RLS enabled on affected table
✅ Security policies created
✅ Verified with automated tests
✅ Regression test added to test suite

Current status:
- RLS: ENABLED
- Policies: 2 active
- Tests: All passing

The table can be removed from the security alert list.

Regards,
[Your name]
```

---

## Security Testing

### Run Tests Locally

```bash
# Full test suite (recommended before every push)
python3 tests/test_production_suite.py

# Security-only tests (faster)
python3 -c "
import asyncio
from tests.test_production_suite import test_database_security, test_api_security, TestResults

async def quick_security_test():
    results = TestResults()
    await test_database_security(results)
    # Skip API test if not needed
    return results.summary()

success = asyncio.run(quick_security_test())
print('✅ Security checks passed' if success else '❌ Security issues found')
"

# Weekly audit (comprehensive)
python3 scripts/security_audit.py
```

### What Tests Check

**Database Security:**
- ✅ RLS enabled on properties table
- ✅ Minimum 2 policies active
- ✅ Public read policy exists (SELECT for public role)
- ✅ Auth write policy exists (ALL for authenticated role)
- ✅ Read access works (can query data)
- ✅ Write access blocked for anonymous users
- ✅ Other tables checked for RLS
- ✅ Spatial indexes present

**API Security:**
- ✅ Security headers present (X-Content-Type-Options, X-Frame-Options, etc.)
- ✅ CORS not set to wildcard (`*`)
- ✅ Sensitive paths return 404 (/admin, /.env, /config, /debug)

**Code Security:**
- ✅ No .env files in git repository
- ✅ No secrets in recent commits
- ✅ CORS configuration restrictive
- ✅ File permissions on .env files

---

## Common Security Mistakes (And How We Prevent Them)

### Mistake 1: Forgetting to Enable RLS on New Table

**How we prevent:**
- ✅ Pre-commit hook checks for new tables without RLS
- ✅ Security audit scans all tables weekly
- ✅ Template in CLAUDE.md shows correct pattern

**Fix if it happens:**
```sql
ALTER TABLE forgotten_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON forgotten_table FOR SELECT TO public USING (true);
```

### Mistake 2: Committing .env File

**How we prevent:**
- ✅ .gitignore includes `.env`, `.env.local`, `.env.*`
- ✅ Pre-commit hook blocks .env files
- ✅ Security audit checks git history

**Fix if it happens:**
```bash
# Remove from git history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch backend/.env' \
  --prune-empty --tag-name-filter cat -- --all

# Rotate ALL secrets in that file
# - New DATABASE_URL from Supabase
# - New MAPBOX_TOKEN from Mapbox
# - New AUTOADDRESS_KEY from Autoaddress

# Push to force update remote
git push origin --force --all
```

### Mistake 3: SQL Injection via String Interpolation

**How we prevent:**
- ✅ Code reviews check for f-strings in SQL queries
- ✅ Pydantic models enforce input validation
- ✅ Test suite includes malicious input tests

**Bad:**
```python
# ❌ NEVER DO THIS
query = f"SELECT * FROM properties WHERE address = '{user_input}'"
result = await conn.fetch(query)
```

**Good:**
```python
# ✅ ALWAYS USE PARAMETERIZED QUERIES
result = await conn.fetch(
    "SELECT * FROM properties WHERE address = $1",
    user_input
)
```

### Mistake 4: Wildcard CORS in Production

**How we prevent:**
- ✅ Pre-commit hook blocks `origins=["*"]`
- ✅ Test suite verifies CORS configuration
- ✅ Security audit checks backend/main.py

**Fix:**
```python
# ❌ BAD
allow_origins=["*"]

# ✅ GOOD
allow_origins=[
    "https://homeiq.ie",
    "https://www.homeiq.ie"
]
```

---

## Security Monitoring & Maintenance

### Daily
- Check Sentry for security-related errors
- Monitor deploy logs for failures

### Weekly
```bash
# Run security audit
python3 scripts/security_audit.py

# Check for dependency vulnerabilities
cd backend && pip list --outdated
cd frontend && npm audit

# Review recent commits for security issues
git log --oneline -n 20 | grep -i "security\|fix\|urgent"
```

### Monthly
- Review and rotate API keys if needed
- Check for Supabase/Railway/Vercel security announcements
- Update dependencies with security patches
- Review access logs for unusual patterns

### Quarterly
- Full security review with external perspective
- Penetration testing (manual or automated)
- Review and update security documentation
- Audit user permissions and API keys

---

## Security Contacts & Resources

**Internal:**
- Security incidents: [Your email]
- Escalation: [Manager/CTO email]

**External:**
- Supabase Security: https://supabase.com/docs/guides/platform/going-into-prod#security
- Railway Security: https://docs.railway.app/reference/security
- Vercel Security: https://vercel.com/docs/security

**Tools:**
- RLS Documentation: https://supabase.com/docs/guides/auth/row-level-security
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- SQL Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

---

## Security Metrics (Current)

**Database:**
- ✅ RLS enabled: YES
- ✅ Security policies: 2 active
- ✅ Tables protected: 100% (properties table)
- ✅ Anonymous writes: BLOCKED

**API:**
- ✅ CORS restricted: homeiq.ie only
- ✅ Security headers: Configured
- ✅ Sensitive paths: Protected
- ✅ HTTPS enforced: YES

**Code:**
- ✅ Secrets in git: 0
- ✅ .env files committed: 0
- ✅ Security tests: 8 passing
- ✅ Pre-commit hook: Active

**Incidents:**
- Last alert: June 8, 2026 (RLS)
- Time to resolution: < 1 day
- Regression prevention: Test added

**Goal:** 
- Zero security alerts from external services
- Zero incidents in past 90 days
- 100% of commits pass security checks

---

## Summary: Security is Everyone's Job

Security is not a separate task - it's woven into every aspect of development:

✅ **Write code:** Input validation, parameterized queries, no hardcoded secrets  
✅ **Commit code:** Pre-commit hook blocks security issues  
✅ **Test code:** Security tests run with every test suite  
✅ **Deploy code:** CI/CD runs security checks automatically  
✅ **Monitor code:** Weekly audits + external alerts  

**Result:** Security vulnerabilities caught before they reach production. Zero security alerts from external services. Confidence that our data and users are protected.

---

**Last Security Audit:** June 9, 2026  
**Status:** ✅ All checks passing  
**Next Audit:** June 16, 2026
