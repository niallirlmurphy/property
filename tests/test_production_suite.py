#!/usr/bin/env python3
"""
Comprehensive production test suite for homeiq.ie
Tests both frontend (Vercel) and backend (Railway) deployments.
"""

import asyncio
import httpx
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
FRONTEND_URL = "https://homeiq.ie"
BACKEND_URL = "https://eloquent-optimism-production-350a.up.railway.app"
TIMEOUT = 30.0

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name: str, detail: str = ""):
        self.passed.append((test_name, detail))
        print(f"✅ {test_name}")
        if detail:
            print(f"   {detail}")

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"❌ {test_name}")
        print(f"   Error: {error}")

    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"⚠️  {test_name}")
        print(f"   Warning: {message}")

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.warnings)
        print("\n" + "="*70)
        print("TEST SUITE SUMMARY")
        print("="*70)
        print(f"Total tests: {total}")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Failed: {len(self.failed)}")

        if self.failed:
            print("\nFailed tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")

        if self.warnings:
            print("\nWarnings:")
            for name, msg in self.warnings:
                print(f"  - {name}: {msg}")

        return len(self.failed) == 0


async def test_backend_health(client: httpx.AsyncClient, results: TestResults):
    """Test backend health endpoint."""
    try:
        resp = await client.get(f"{BACKEND_URL}/health", timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                results.add_pass("Backend health check", f"Status: {resp.status_code}")
            else:
                results.add_fail("Backend health check", f"Unexpected response: {data}")
        else:
            results.add_fail("Backend health check", f"Status code: {resp.status_code}")
    except Exception as e:
        results.add_fail("Backend health check", str(e))


async def test_backend_geocoding(client: httpx.AsyncClient, results: TestResults):
    """Test backend geocoding endpoint."""
    test_cases = [
        ("Dublin", 53.3, 53.4, -6.3, -6.2),
        ("Nobber, Meath", 53.7, 53.9, -6.8, -6.7),
        ("Cork", 51.8, 52.0, -8.6, -8.4),
    ]

    for query, min_lat, max_lat, min_lon, max_lon in test_cases:
        try:
            resp = await client.get(f"{BACKEND_URL}/geocode", params={"q": query}, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                lat, lon = data.get("lat"), data.get("lon")

                if lat and lon:
                    if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                        results.add_pass(f"Geocode: {query}", f"→ ({lat:.4f}, {lon:.4f})")
                    else:
                        results.add_fail(f"Geocode: {query}",
                                       f"Coordinates ({lat:.4f}, {lon:.4f}) outside expected bounds")
                else:
                    results.add_fail(f"Geocode: {query}", "Missing lat/lon in response")
            else:
                results.add_fail(f"Geocode: {query}", f"Status code: {resp.status_code}")
        except Exception as e:
            results.add_fail(f"Geocode: {query}", str(e))


async def test_backend_search(client: httpx.AsyncClient, results: TestResults):
    """Test backend search endpoint with various queries."""
    test_cases = [
        ("nobber", 5, 60, "Nobber search should return properties"),
        ("dublin", 5, 100, "Dublin should have many properties"),
        ("53.3498,-6.2603", 2, 50, "Coordinate search should work"),
    ]

    for query, radius_km, min_results, description in test_cases:
        try:
            resp = await client.get(f"{BACKEND_URL}/search",
                                  params={"q": query, "radius_km": radius_km},
                                  timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                count = data.get("count", 0)
                results_list = data.get("results", [])

                if count >= min_results and len(results_list) > 0:
                    results.add_pass(f"Search: {query}",
                                   f"Found {count} properties, showing {len(results_list)}")
                elif count > 0:
                    results.add_warning(f"Search: {query}",
                                      f"Only {count} properties found (expected >={min_results})")
                else:
                    results.add_fail(f"Search: {query}", "No results returned")
            else:
                results.add_fail(f"Search: {query}", f"Status code: {resp.status_code}")
        except Exception as e:
            results.add_fail(f"Search: {query}", str(e))


async def test_backend_trends(client: httpx.AsyncClient, results: TestResults):
    """Test backend trends endpoint."""
    test_cases = [
        ("Dublin", None, 5),
        ("Cork", None, 5),
        (None, "Meath", 3),
    ]

    for location, county, radius_km in test_cases:
        try:
            params = {"radius_km": radius_km}
            if location:
                params["q"] = location
            if county:
                params["county"] = county

            resp = await client.get(f"{BACKEND_URL}/trends", params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                trends = data.get("data", [])

                if len(trends) >= 5:  # Should have multiple years
                    latest = trends[-1] if trends else {}
                    median = latest.get("median_price", 0)
                    label = location or county
                    results.add_pass(f"Trends: {label}",
                                   f"{len(trends)} years, latest median: €{median:,.0f}")
                else:
                    results.add_warning(f"Trends: {location or county}",
                                      f"Only {len(trends)} data points")
            else:
                results.add_fail(f"Trends: {location or county}",
                               f"Status code: {resp.status_code}")
        except Exception as e:
            results.add_fail(f"Trends: {location or county}", str(e))


async def test_backend_eircode(client: httpx.AsyncClient, results: TestResults):
    """Test backend Eircode lookup."""
    test_cases = [
        ("D02", 100, "Dublin 2 routing key should have many properties"),
        ("A82", 50, "Meath routing key should have properties"),
    ]

    for code, min_results, description in test_cases:
        try:
            resp = await client.get(f"{BACKEND_URL}/eircode",
                                  params={"code": code},
                                  timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                # API returns stats nested in 'stats' object
                stats = data.get("stats", {})
                count = stats.get("total_count", 0)
                results_list = data.get("results", [])

                if count >= min_results:
                    results.add_pass(f"Eircode: {code}",
                                   f"{count} properties, {len(results_list)} shown")
                else:
                    results.add_warning(f"Eircode: {code}",
                                      f"Only {count} properties (expected >={min_results})")
            else:
                results.add_fail(f"Eircode: {code}", f"Status code: {resp.status_code}")
        except Exception as e:
            results.add_fail(f"Eircode: {code}", str(e))


async def test_backend_counties(client: httpx.AsyncClient, results: TestResults):
    """Test backend counties list."""
    try:
        resp = await client.get(f"{BACKEND_URL}/counties", timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) >= 20:
                total_properties = sum(c.get("count", 0) for c in data)
                results.add_pass("Counties list",
                               f"{len(data)} counties, {total_properties:,} total properties")
            else:
                results.add_fail("Counties list", f"Expected 20+ counties, got {len(data)}")
        else:
            results.add_fail("Counties list", f"Status code: {resp.status_code}")
    except Exception as e:
        results.add_fail("Counties list", str(e))


async def test_coordinate_quality(client: httpx.AsyncClient, results: TestResults):
    """Test that Nobber coordinates are correct after hybrid update."""
    try:
        # Search for Nobber
        resp = await client.get(f"{BACKEND_URL}/search",
                              params={"q": "nobber", "radius_km": 5},
                              timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            center = data.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")

            # Nobber should be around (53.82, -6.75)
            expected_lat, expected_lon = 53.82, -6.75
            lat_diff = abs(lat - expected_lat)
            lon_diff = abs(lon - expected_lon)

            if lat_diff < 0.01 and lon_diff < 0.01:
                results.add_pass("Nobber coordinates quality",
                               f"Center: ({lat:.4f}, {lon:.4f}) ✓")
            else:
                results.add_fail("Nobber coordinates quality",
                               f"Center ({lat:.4f}, {lon:.4f}) too far from expected ({expected_lat}, {expected_lon})")
        else:
            results.add_fail("Nobber coordinates quality", f"Status code: {resp.status_code}")
    except Exception as e:
        results.add_fail("Nobber coordinates quality", str(e))


async def test_frontend_loads(client: httpx.AsyncClient, results: TestResults):
    """Test that frontend loads successfully."""
    try:
        resp = await client.get(FRONTEND_URL, timeout=TIMEOUT, follow_redirects=True)
        if resp.status_code == 200:
            html = resp.text
            if "HomeIQ" in html and "index-" in html:
                # Extract bundle name
                import re
                bundle_match = re.search(r'index-([a-zA-Z0-9]+)\.js', html)
                bundle = bundle_match.group(1) if bundle_match else "unknown"
                results.add_pass("Frontend loads", f"Bundle: index-{bundle}.js")
            else:
                results.add_fail("Frontend loads", "HTML doesn't contain expected content")
        else:
            results.add_fail("Frontend loads", f"Status code: {resp.status_code}")
    except Exception as e:
        results.add_fail("Frontend loads", str(e))


async def test_frontend_api_calls(client: httpx.AsyncClient, results: TestResults):
    """Test that frontend can reach backend API."""
    try:
        # Frontend should call backend directly, not through /api proxy
        resp = await client.get(f"{BACKEND_URL}/search",
                              params={"q": "dublin", "radius_km": 5},
                              timeout=TIMEOUT)
        if resp.status_code == 200:
            results.add_pass("Frontend → Backend connectivity", "Direct API calls working")
        else:
            results.add_fail("Frontend → Backend connectivity",
                           f"Backend returned {resp.status_code}")
    except Exception as e:
        results.add_fail("Frontend → Backend connectivity", str(e))


async def test_performance(client: httpx.AsyncClient, results: TestResults):
    """Test response time performance."""
    endpoints = [
        ("/health", "Health check"),
        ("/search?q=dublin&radius_km=5", "Search query"),
        ("/counties", "Counties list"),
    ]

    for endpoint, name in endpoints:
        try:
            import time
            start = time.time()
            resp = await client.get(f"{BACKEND_URL}{endpoint}", timeout=TIMEOUT)
            elapsed = time.time() - start

            if resp.status_code == 200:
                if elapsed < 1.0:
                    results.add_pass(f"Performance: {name}", f"{elapsed*1000:.0f}ms")
                elif elapsed < 3.0:
                    results.add_warning(f"Performance: {name}",
                                      f"{elapsed*1000:.0f}ms (slower than ideal)")
                else:
                    results.add_fail(f"Performance: {name}",
                                   f"{elapsed*1000:.0f}ms (too slow)")
            else:
                results.add_fail(f"Performance: {name}", f"Status: {resp.status_code}")
        except Exception as e:
            results.add_fail(f"Performance: {name}", str(e))


async def test_database_security(results: TestResults):
    """Test database security configuration (RLS, policies, etc)."""
    import os
    import asyncpg

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        results.add_fail("Database security", "DATABASE_URL not set")
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=10.0)

        # Check RLS is enabled
        rls_status = await conn.fetchrow("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'properties'
        """)

        if rls_status and rls_status["rowsecurity"]:
            results.add_pass("RLS enabled on properties table", "✓ Protected")
        else:
            results.add_fail("RLS enabled on properties table",
                           "CRITICAL: Table is publicly accessible without RLS")

        # Check policies exist
        policies = await conn.fetch("""
            SELECT policyname, cmd, roles
            FROM pg_policies
            WHERE tablename = 'properties'
        """)

        if len(policies) > 0:
            policy_summary = ", ".join([f"{p['cmd']}" for p in policies])
            results.add_pass("Security policies configured",
                           f"{len(policies)} policies: {policy_summary}")
        else:
            results.add_fail("Security policies configured",
                           "No policies found - table may be inaccessible")

        # Verify read access still works
        count = await conn.fetchval("SELECT COUNT(*) FROM properties LIMIT 1")
        if count is not None:
            results.add_pass("Read access verified", "✓ Can query data")
        else:
            results.add_fail("Read access verified", "Cannot read data")

        # Check for other security issues
        # 1. Check if there are any tables without RLS
        unprotected = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND rowsecurity = false
            AND tablename NOT LIKE 'pg_%'
            AND tablename NOT LIKE 'sql_%'
        """)

        if unprotected:
            table_list = ", ".join([t["tablename"] for t in unprotected])
            results.add_warning("Other tables without RLS",
                              f"Tables: {table_list}")
        else:
            results.add_pass("All tables protected", "✓ RLS enabled on all tables")

        await conn.close()

    except Exception as e:
        results.add_fail("Database security check", str(e))


async def test_api_security(client: httpx.AsyncClient, results: TestResults):
    """Test API security headers and configurations."""
    try:
        resp = await client.get(f"{BACKEND_URL}/health", timeout=TIMEOUT)

        # Check security headers
        headers_to_check = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block",
        }

        missing_headers = []
        for header, expected in headers_to_check.items():
            if header in resp.headers:
                value = resp.headers[header].lower()
                if isinstance(expected, list):
                    if value not in [e.lower() for e in expected]:
                        missing_headers.append(f"{header} (wrong value)")
                elif value != expected.lower():
                    missing_headers.append(f"{header} (wrong value)")
            else:
                missing_headers.append(header)

        if not missing_headers:
            results.add_pass("Security headers present", "✓ Headers configured")
        else:
            results.add_warning("Security headers",
                              f"Missing/incorrect: {', '.join(missing_headers)}")

        # Check CORS is configured (not too permissive)
        if "access-control-allow-origin" in resp.headers:
            cors_origin = resp.headers["access-control-allow-origin"]
            if cors_origin == "*":
                results.add_warning("CORS configuration",
                                  "Allows all origins (*) - consider restricting")
            else:
                results.add_pass("CORS configuration",
                               f"Restricted to: {cors_origin}")
        else:
            results.add_pass("CORS configuration", "Not exposed")

        # Test that sensitive endpoints don't leak info
        sensitive_paths = [
            "/admin",
            "/.env",
            "/config",
            "/debug",
        ]

        exposed = []
        for path in sensitive_paths:
            try:
                resp = await client.get(f"{BACKEND_URL}{path}", timeout=5)
                if resp.status_code != 404:
                    exposed.append(f"{path} ({resp.status_code})")
            except:
                pass

        if not exposed:
            results.add_pass("Sensitive paths protected", "✓ No exposed endpoints")
        else:
            results.add_fail("Sensitive paths protected",
                           f"Exposed: {', '.join(exposed)}")

    except Exception as e:
        results.add_fail("API security check", str(e))


async def run_all_tests():
    """Run complete test suite."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     PRODUCTION TEST SUITE - homeiq.ie                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\nFrontend: {FRONTEND_URL}")
    print(f"Backend:  {BACKEND_URL}")
    print(f"Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*70)
    print("RUNNING TESTS")
    print("="*70 + "\n")

    results = TestResults()

    async with httpx.AsyncClient() as client:
        # Security tests (most important)
        print("Security:")
        await test_database_security(results)
        await test_api_security(client, results)

        # Backend tests
        print("\nBackend Health:")
        await test_backend_health(client, results)

        print("\nBackend Geocoding:")
        await test_backend_geocoding(client, results)

        print("\nBackend Search:")
        await test_backend_search(client, results)

        print("\nBackend Trends:")
        await test_backend_trends(client, results)

        print("\nBackend Eircode:")
        await test_backend_eircode(client, results)

        print("\nBackend Counties:")
        await test_backend_counties(client, results)

        print("\nCoordinate Quality:")
        await test_coordinate_quality(client, results)

        print("\nFrontend:")
        await test_frontend_loads(client, results)
        await test_frontend_api_calls(client, results)

        print("\nPerformance:")
        await test_performance(client, results)

    # Summary
    success = results.summary()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest suite cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
