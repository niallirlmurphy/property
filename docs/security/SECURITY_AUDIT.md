# Security Audit Report - HomeIQ.ie
**Date:** 2026-06-07  
**Audited By:** Claude Code  
**Site:** https://homeiq.ie

## Executive Summary

Overall security posture: **GOOD** with some recommendations for improvement.

The site implements most security best practices including:
- ✅ RLS-protected database
- ✅ Parameterized SQL queries
- ✅ Rate limiting
- ✅ Input validation via Pydantic
- ✅ Security headers
- ✅ CORS restrictions
- ✅ HTTPS only (Vercel/Railway)

**Critical Issues:** 0  
**High Priority:** 1  
**Medium Priority:** 2  
**Low Priority:** 2

---

## 1. SQL Injection Protection ✅

**Status:** SECURE

**Analysis:**
- All database queries use parameterized queries (`$1, $2, ...`)
- No f-string interpolation in SQL queries
- Pydantic models validate all input types and ranges
- PostgreSQL parameter binding prevents SQL injection

**Evidence:**
```python
# Good: Parameterized queries
await db_pool.execute("""
    UPDATE properties SET latitude = $1, longitude = $2
    WHERE id = $3
""", payload.latitude, payload.longitude, payload.property_id)
```

**One Exception - Polygon Search (Line 933):**
```python
polygon_wkt = f"POLYGON(({points_str}))"
filters = [f"ST_Within(geog::geometry, ST_GeomFromText('{polygon_wkt}', 4326))"]
```

**Risk Assessment:** LOW
- Input is validated by Pydantic as `list[list[float]]` - only floats allowed
- String interpolation uses validated floats, not user strings
- No way to inject SQL through float values

**Recommendation:** Consider using `ST_MakePolygon` with array parameters instead of WKT strings for defense-in-depth.

---

## 2. Cross-Site Scripting (XSS) ✅

**Status:** SECURE

**Analysis:**
- React automatically escapes all rendered content
- No `dangerouslySetInnerHTML` usage found
- No `eval()`, `innerHTML`, or `document.write` found
- User input is only displayed through React components

**Verification:**
```bash
grep -r "dangerouslySetInnerHTML\|eval(\|innerHTML" frontend/src
# No results
```

---

## 3. Database Access Control ✅

**Status:** SECURE

**RLS Configuration:**
- Row-Level Security enabled on properties table
- Public has SELECT-only access (PPR data is public)
- INSERT/UPDATE/DELETE blocked by default (no policies)

**Script:** `scripts/enable_rls_security.py`

**Policy:**
```sql
CREATE POLICY "Allow public read access"
ON properties FOR SELECT TO public
USING (true);
```

**Recommendation:** Verify RLS is actually enabled in production:
```bash
DATABASE_URL=<prod-url> python3 scripts/enable_rls_security.py
```

---

## 4. Rate Limiting ✅

**Status:** IMPLEMENTED

**Current Limits:**
- Search endpoints: 60 requests/minute
- Polygon search: 30 requests/minute
- Geocoding updates: 10 requests/minute
- Feedback/Contact: 5 requests/minute
- Email alerts: 10 requests/minute

**Implementation:** `backend/main.py:153-162`
- Per-IP rate limiting using sliding window
- Respects `X-Forwarded-For` header (Railway proxy)

**Potential Issue:** ⚠️ **HIGH PRIORITY**
- Rate limiter uses in-memory storage - resets on app restart
- Doesn't persist across multiple Railway instances
- Can be bypassed by rotating IPs

**Recommendation:**
- Implement Redis-backed rate limiting for production
- Add distributed rate limiting across Railway replicas
- Consider adding exponential backoff for repeated violations

---

## 5. CORS Configuration ✅

**Status:** SECURE

**Current Configuration:**
```python
ALLOWED_ORIGINS = [
    "https://homeiq.ie",
    "https://www.homeiq.ie",
]
if os.environ.get("ENVIRONMENT") != "production":
    ALLOWED_ORIGINS.append("http://localhost:5173")
```

**Good:**
- Production only allows homeiq.ie domains
- Localhost only allowed in development
- Methods restricted to GET and POST

---

## 6. Security Headers ✅

**Status:** IMPLEMENTED

**Headers Applied (Line 196-213):**
```python
X-Content-Type-Options: nosniff        # Prevents MIME sniffing
X-Frame-Options: DENY                   # Prevents clickjacking
X-XSS-Protection: 1; mode=block        # Legacy XSS protection
Referrer-Policy: strict-origin-when-cross-origin
```

**Missing Headers:** ⚠️ **MEDIUM PRIORITY**
- `Content-Security-Policy` (CSP) - Not implemented
- `Strict-Transport-Security` (HSTS) - Not explicitly set
- `Permissions-Policy` - Not implemented

**Recommendation:**
Add CSP header:
```python
# Restrictive CSP
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://vercel.live; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https://eloquent-optimism-production-350a.up.railway.app; "
    "frame-ancestors 'none';"
)
```

**HSTS:** Vercel adds this automatically, but backend should add:
```python
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

---

## 7. Input Validation ✅

**Status:** SECURE

**Pydantic Models:**
- All API inputs validated via Pydantic BaseModel
- Type checking, range validation, regex patterns
- Email validation with regex
- String length limits enforced

**Examples:**
```python
class GeocodeUpdatePayload(BaseModel):
    property_id: int
    latitude: float = Field(..., ge=51.4, le=55.5)  # Ireland bounds
    longitude: float = Field(..., ge=-10.7, le=-5.4)
    address: Optional[str] = Field(None, max_length=500)
    eircode: Optional[str] = Field(None, max_length=10)

class EmailAlertSubscription(BaseModel):
    email: str = Field(..., max_length=255)
    radius_km: float = Field(2.0, ge=0.5, le=20.0)
```

**Verified:** Pydantic correctly rejects out-of-range and wrong-type inputs.

---

## 8. API Documentation ⚠️ **MEDIUM PRIORITY**

**Status:** DISABLED

```python
app = FastAPI(
    docs_url=None,      # Swagger UI disabled
    redoc_url=None,     # ReDoc disabled
    openapi_url=None,   # OpenAPI schema disabled
)
```

**Good:** Reduces attack surface by not exposing API schema publicly

**Trade-off:** Makes it harder to audit endpoints without reading code

**Recommendation:** Keep disabled in production, but consider enabling in staging/dev environments with authentication.

---

## 9. Sensitive Data Exposure ✅

**Status:** SECURE

**API Keys Protected:**
- `MAPBOX_TOKEN` - Server-side only
- `AUTOADDRESS_KEY` - Server-side only
- `DATABASE_URL` - Server-side only
- `SENTRY_DSN` - Public exposure is safe (write-only)

**Frontend Environment:**
- `VITE_API_URL` - Public (intentional, points to backend)

**No Secrets in Git:**
```bash
# .env files properly gitignored
.env
.env.local
backend/.env
```

---

## 10. Authentication & Authorization ⚠️ **LOW PRIORITY**

**Status:** NO AUTHENTICATION REQUIRED

**Current Design:**
- All PPR data is public (correct - government data)
- No user accounts or login system
- Admin endpoints require manual database access

**Manual Geocoding Tool Risk:**
- `/geocoding-queue/update` endpoint allows updating property coordinates
- Protected only by rate limiting (10 req/min)
- No authentication required

**Recommendation:**
Add basic auth or API key for admin endpoints:
```python
from fastapi import Header, HTTPException

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")

async def verify_admin_key(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key

@app.post("/geocoding-queue/update", dependencies=[Depends(verify_admin_key)])
async def update_property_geocode(...):
    ...
```

---

## 11. Logging & Monitoring ✅

**Status:** IMPLEMENTED

**Sentry Integration:**
- Error tracking enabled
- Performance monitoring (10% sample rate)
- Environment and release tracking

**Search Analytics:**
- All searches logged to `search_log` table
- Includes query, results, timing, IP address
- Used for debugging and improving search quality

**Privacy Consideration:** ⚠️ **LOW PRIORITY**
- IP addresses stored in `search_log` table
- May require GDPR compliance review if EU users
- Consider hashing IPs or shorter retention period

**Recommendation:**
Add IP anonymization:
```python
def _anonymize_ip(ip: str) -> str:
    """Hash IP for privacy-preserving analytics."""
    return hashlib.sha256(f"{ip}:daily_salt".encode()).hexdigest()[:16]
```

---

## 12. Dependency Security

**Status:** NOT AUDITED IN THIS REVIEW

**Recommendation:**
Run security audits regularly:
```bash
# Python
pip install safety
safety check -r backend/requirements.txt

# Node.js
npm audit
npm audit fix
```

---

## 13. HTTPS & Transport Security ✅

**Status:** SECURE

**Configuration:**
- Frontend: Vercel (automatic HTTPS)
- Backend: Railway (automatic HTTPS)
- No HTTP fallback
- Modern TLS versions only

---

## Priority Recommendations

### High Priority
1. **Implement distributed rate limiting** - Current in-memory rate limiter doesn't scale across Railway instances. Use Redis or similar.

### Medium Priority
2. **Add Content-Security-Policy header** - Prevents XSS, clickjacking, and other injection attacks
3. **Add HSTS header to backend** - Force HTTPS for all connections

### Low Priority
4. **Add authentication to admin endpoints** - `/geocoding-queue/update` should require API key
5. **Anonymize IP addresses in logs** - GDPR compliance consideration

---

## Security Checklist

- [x] SQL injection protection (parameterized queries)
- [x] XSS prevention (React auto-escaping)
- [x] CSRF protection (not needed - no sessions/cookies)
- [x] RLS enabled on database
- [x] Rate limiting implemented
- [x] CORS properly configured
- [x] Security headers present
- [x] Input validation via Pydantic
- [x] HTTPS enforced
- [x] Secrets not in git
- [x] Error tracking (Sentry)
- [ ] CSP header (recommended)
- [ ] Distributed rate limiting (recommended)
- [ ] Admin endpoint auth (recommended)
- [ ] IP anonymization (optional)
- [ ] Regular dependency audits (ongoing)

---

## Testing Commands

```bash
# Test RLS is enabled
DATABASE_URL=<url> python3 scripts/enable_rls_security.py

# Run production test suite (includes security checks)
python3 tests/test_production_suite.py

# Check for vulnerable dependencies
pip install safety && safety check -r backend/requirements.txt
npm audit

# Test rate limiting
for i in {1..70}; do curl https://homeiq.ie/api/search?q=Dublin; done
# Should return 429 after 60 requests

# Check security headers
curl -I https://eloquent-optimism-production-350a.up.railway.app/health
```

---

## Compliance Notes

**GDPR Considerations:**
- No personal data collected except email alerts (opt-in)
- Email alert unsubscribe mechanism implemented
- IP addresses logged (consider anonymization)
- PPR data is public government data (no PII concerns)

**Data Retention:**
- Search logs retained indefinitely (consider 90-day retention)
- Email alerts: user controls via unsubscribe
- No cookies or tracking beyond Vercel Analytics

---

## Conclusion

HomeIQ.ie has a **solid security foundation** with no critical vulnerabilities identified. The main improvements needed are:

1. Distributed rate limiting for scalability
2. CSP headers for defense-in-depth
3. Admin endpoint authentication

The site follows security best practices and is suitable for production use with the recommended enhancements.
