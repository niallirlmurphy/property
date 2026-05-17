"""
Security tests for the HomeIQ API and infrastructure.

Covers:
  - API schema / docs not exposed in production
  - CORS origin lockdown
  - Input validation and parameter bounds
  - SQL injection resistance
  - POST form payload size limits
  - Supabase REST API not directly accessible without a key
  - Secrets not exposed in API responses
  - Rate-limit headroom (no single query can exhaust the DB)
"""

import pytest
import requests as req

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(api_url, path, **params):
    return req.get(f"{api_url}{path}", params=params, timeout=15)

def post(api_url, path, payload):
    return req.post(f"{api_url}{path}", json=payload, timeout=15)


# ---------------------------------------------------------------------------
# API schema exposure
# ---------------------------------------------------------------------------

def test_openapi_docs_not_exposed(api):
    """/docs, /redoc, /openapi.json should not be publicly accessible in production."""
    for path in ["/docs", "/redoc", "/openapi.json"]:
        r = req.get(f"{api}{path}", timeout=10)
        assert r.status_code in (401, 403, 404), (
            f"{path} returned {r.status_code} — API schema is publicly accessible. "
            "Set app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None) in main.py "
            "or restrict via middleware."
        )


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def test_cors_rejects_arbitrary_origin(api):
    """Requests from arbitrary origins must not receive CORS approval."""
    r = req.get(f"{api}/health", headers={"Origin": "https://evil.com"}, timeout=10)
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    assert acao not in ("*", "https://evil.com"), (
        f"CORS allows arbitrary origin: Access-Control-Allow-Origin: {acao}"
    )


def test_cors_allows_homeiq(api):
    """Legitimate homeiq.ie origin receives CORS approval."""
    r = req.get(f"{api}/health", headers={"Origin": "https://homeiq.ie"}, timeout=10)
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    assert acao == "https://homeiq.ie", (
        f"CORS not set for homeiq.ie — got: {acao!r}"
    )


# ---------------------------------------------------------------------------
# Input validation — parameter bounds
# ---------------------------------------------------------------------------

def test_search_radius_too_large_rejected(api):
    """radius_km above maximum is rejected with 422."""
    r = get(api, "/search", q="Rathmines", radius_km=9999)
    assert r.status_code == 422, f"Expected 422 for radius_km=9999, got {r.status_code}"


def test_search_limit_too_large_rejected(api):
    """limit above maximum is rejected with 422."""
    r = get(api, "/search", q="Rathmines", limit=9999)
    assert r.status_code == 422, f"Expected 422 for limit=9999, got {r.status_code}"


def test_search_sort_invalid_rejected(api):
    """Invalid sort value is rejected with 422."""
    r = get(api, "/search", q="Rathmines", sort="evil")
    assert r.status_code == 422, f"Expected 422 for sort=evil, got {r.status_code}"


def test_search_radius_zero_rejected(api):
    """radius_km=0 is rejected with 422."""
    r = get(api, "/search", q="Rathmines", radius_km=0)
    assert r.status_code == 422, f"Expected 422 for radius_km=0, got {r.status_code}"


# ---------------------------------------------------------------------------
# SQL injection resistance
# ---------------------------------------------------------------------------

SQL_INJECTIONS = [
    "'; DROP TABLE properties; --",
    "' OR '1'='1",
    "1; SELECT * FROM submissions; --",
    "' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13 --",
]

@pytest.mark.parametrize("payload", SQL_INJECTIONS)
def test_search_sql_injection_safe(api, payload):
    """SQL injection in q param does not cause a 500 or leak data."""
    r = get(api, "/search", q=payload, radius_km=1)
    assert r.status_code in (200, 404), (
        f"SQL injection payload caused unexpected {r.status_code}: {r.text[:200]}"
    )
    if r.status_code == 200:
        data = r.json()
        # Should geocode to some location but return 0 results or normal results
        assert "results" in data


@pytest.mark.parametrize("payload", SQL_INJECTIONS)
def test_geocode_sql_injection_safe(api, payload):
    """SQL injection in geocode q param does not cause a 500."""
    r = get(api, "/geocode", q=payload)
    assert r.status_code in (200, 404), (
        f"SQL injection payload caused {r.status_code}: {r.text[:200]}"
    )


@pytest.mark.parametrize("payload", SQL_INJECTIONS)
def test_trends_county_sql_injection_safe(api, payload):
    """SQL injection in trends county param does not cause a 500."""
    r = get(api, "/trends", county=payload)
    assert r.status_code in (200, 404), (
        f"SQL injection in county caused {r.status_code}: {r.text[:200]}"
    )


# ---------------------------------------------------------------------------
# POST form payload limits
# ---------------------------------------------------------------------------

def test_feedback_large_payload_rejected(api):
    """Feedback endpoint rejects payloads with oversized fields."""
    r = post(api, "/feedback", {
        "datasets":  "x" * 100_000,
        "comments":  "y" * 100_000,
        "name":      "z" * 10_000,
        "email":     None,
    })
    assert r.status_code in (400, 413, 422), (
        f"Expected rejection of 200KB feedback payload, got {r.status_code}. "
        "Add field length validation to FeedbackPayload model."
    )


def test_contact_large_payload_rejected(api):
    """Contact endpoint rejects payloads with oversized fields."""
    r = post(api, "/contact", {
        "message":       "x" * 100_000,
        "price_updates": False,
        "name":          "y" * 10_000,
        "email":         None,
    })
    assert r.status_code in (400, 413, 422), (
        f"Expected rejection of 100KB contact payload, got {r.status_code}. "
        "Add field length validation to ContactPayload model."
    )


def test_feedback_invalid_email_rejected(api):
    """Feedback endpoint rejects invalid email addresses."""
    r = post(api, "/feedback", {
        "datasets": "test",
        "comments": "",
        "name":     "Test",
        "email":    "not-an-email",
    })
    assert r.status_code == 422, (
        f"Expected 422 for invalid email, got {r.status_code}"
    )


def test_contact_invalid_email_rejected(api):
    """Contact endpoint rejects invalid email addresses."""
    r = post(api, "/contact", {
        "message":       "test",
        "price_updates": False,
        "name":          "Test",
        "email":         "not-an-email",
    })
    assert r.status_code == 422, (
        f"Expected 422 for invalid email, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Secrets not leaked in responses
# ---------------------------------------------------------------------------

SECRET_PATTERNS = [
    "DATABASE_URL",
    "supabase.co",
    "postgresql://",
    "AUTOADDRESS_KEY",
    "pub_42b886b9",     # autoaddress key prefix
    "eboCukbtcBX0",     # DB password fragment
    "MAPBOX_TOKEN",
]

def test_health_does_not_leak_secrets(api):
    """Health endpoint response does not contain secret values."""
    r = req.get(f"{api}/health", timeout=10)
    body = r.text
    for pattern in SECRET_PATTERNS:
        assert pattern not in body, (
            f"Secret pattern {pattern!r} found in /health response"
        )


def test_error_response_does_not_leak_secrets(api):
    """Error responses (404 from bad geocode) do not leak connection strings."""
    r = req.get(f"{api}/search", params={"q": "xyzzy foobarbaz qux 99999"}, timeout=30)
    body = r.text
    for pattern in SECRET_PATTERNS:
        assert pattern not in body, (
            f"Secret pattern {pattern!r} found in error response: {body[:300]}"
        )


# ---------------------------------------------------------------------------
# Supabase direct access
# ---------------------------------------------------------------------------

def test_supabase_rest_api_requires_auth(api):
    """Supabase PostgREST API is not accessible without authentication."""
    # Extract project ref from the known API URL structure
    # We test that the REST endpoint rejects unauthenticated requests
    project_ref = "jyezhkgevzejhundypxn"
    r = req.get(
        f"https://{project_ref}.supabase.co/rest/v1/properties",
        params={"limit": "1"},
        timeout=10,
    )
    assert r.status_code in (401, 403), (
        f"Supabase REST API returned {r.status_code} without auth — "
        "table may be publicly readable. Enable RLS on the properties table."
    )


def test_supabase_rest_api_rejects_bad_key(api):
    """Supabase PostgREST API rejects invalid API keys."""
    project_ref = "jyezhkgevzejhundypxn"
    r = req.get(
        f"https://{project_ref}.supabase.co/rest/v1/properties",
        params={"limit": "1"},
        headers={"apikey": "invalid_key_xxxxx"},
        timeout=10,
    )
    assert r.status_code in (401, 403), (
        f"Supabase REST API returned {r.status_code} with an invalid key"
    )


# ---------------------------------------------------------------------------
# DDoS / abuse headroom
# ---------------------------------------------------------------------------

def test_single_search_response_time_reasonable(api):
    """A single search completes in under 10 seconds (DDoS baseline)."""
    import time
    start = time.time()
    r = get(api, "/search", q="Rathmines", radius_km=1, county="Dublin")
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 10.0, (
        f"Search took {elapsed:.1f}s — slow enough to amplify DDoS impact"
    )


def test_max_radius_search_completes(api):
    """Search at maximum radius (20km) still completes without timeout."""
    import time
    start = time.time()
    r = get(api, "/search", q="Dublin", radius_km=20, limit=500)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 15.0, (
        f"Max-radius search took {elapsed:.1f}s — may be exploitable for slow-query DDoS"
    )


def test_trends_without_filter_completes(api):
    """Trends query without geographic filter completes in reasonable time."""
    import time
    start = time.time()
    r = get(api, "/trends", county="Dublin")
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 10.0, (
        f"Trends query took {elapsed:.1f}s"
    )
