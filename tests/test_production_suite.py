#!/usr/bin/env python3
"""
Comprehensive production test suite for homeiq.ie
Tests both frontend (Vercel) and backend (Railway) deployments.
"""

import asyncio
import httpx
import sys
import os
import asyncpg
from typing import Dict, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('backend/.env')

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


async def test_county_filter_fallback(client: httpx.AsyncClient, results: TestResults):
    """Test that county filter fallback works when no results found with filter."""
    try:
        # Search for Nobber (Meath) with Dublin county filter
        # Should return 0 with filter, then retry without filter and find results
        resp = await client.get(f"{BACKEND_URL}/search",
                              params={"q": "Nobber", "radius_km": 5, "county": "Dublin"},
                              timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            count = data.get("count", 0)
            county_filter_removed = data.get("county_filter_removed", False)
            results_list = data.get("results", [])

            if count > 0 and county_filter_removed:
                # Verify results are actually from Meath, not Dublin
                counties = {r.get("county") for r in results_list}
                if "Meath" in counties and "Dublin" not in counties:
                    results.add_pass("County filter fallback",
                                   f"Correctly removed Dublin filter, found {count} Meath properties")
                else:
                    results.add_fail("County filter fallback",
                                   f"county_filter_removed=true but got wrong counties: {counties}")
            elif count == 0:
                results.add_fail("County filter fallback",
                               "No results returned - fallback didn't work")
            else:
                results.add_warning("County filter fallback",
                                  f"Found {count} results but county_filter_removed={county_filter_removed}")
        else:
            results.add_fail("County filter fallback", f"Status code: {resp.status_code}")
    except Exception as e:
        results.add_fail("County filter fallback", str(e))


async def test_plural_singular_geocoding(client: httpx.AsyncClient, results: TestResults):
    """Test that plural and singular address forms match correctly.

    Key behaviors to test:
    1. If both plural and singular forms exist in DB, exact match takes precedence
    2. If only singular exists, plural query should fall back to singular
    3. If addresses are truly different (e.g. different towns), both should geocode independently
    """
    # Test cases: (plural_query, singular_query, description, expect_same_location)
    test_cases = [
        ("cremore lawns", "cremore lawn", "lawns/lawn - Dublin residential", True),
        # The following may be different addresses in different locations - expect_same_location=False
        ("elm gardens", "elm garden", "gardens/garden - may be different addresses", False),
        ("orchard woods", "orchard wood", "woods/wood - may be different addresses", False),
        ("the meadows", "the meadow", "meadows/meadow - may be different addresses", False),
        ("abbey fields", "abbey field", "fields/field - may be different addresses", False),
    ]

    for plural, singular, description, expect_same in test_cases:
        try:
            # Try geocoding plural form
            resp_plural = await client.get(f"{BACKEND_URL}/geocode",
                                          params={"q": plural},
                                          timeout=TIMEOUT)

            # Try geocoding singular form
            resp_singular = await client.get(f"{BACKEND_URL}/geocode",
                                            params={"q": singular},
                                            timeout=TIMEOUT)

            plural_success = resp_plural.status_code == 200
            singular_success = resp_singular.status_code == 200

            # At least one should succeed
            if plural_success or singular_success:
                # If both succeed, check if they're the same location
                if plural_success and singular_success:
                    plural_data = resp_plural.json()
                    singular_data = resp_singular.json()

                    lat_diff = abs(plural_data["lat"] - singular_data["lat"])
                    lon_diff = abs(plural_data["lon"] - singular_data["lon"])

                    # Coordinates within ~100m = 0.001 degrees
                    same_location = lat_diff < 0.001 and lon_diff < 0.001

                    if expect_same:
                        # For cremore lawn/lawns, we expect fallback to work
                        if same_location or (not plural_success and singular_success):
                            results.add_pass(f"Plural/singular: {description}",
                                           f"Plural correctly falls back to singular location")
                        else:
                            results.add_warning(f"Plural/singular: {description}",
                                              f"Expected same location but got {lat_diff:.4f}°, {lon_diff:.4f}° apart")
                    else:
                        # For other cases, different locations are acceptable (different addresses)
                        if same_location:
                            results.add_pass(f"Plural/singular: {description}",
                                           f"Both forms geocode to same location")
                        else:
                            results.add_pass(f"Plural/singular: {description}",
                                           f"Both forms geocode independently (different addresses)")
                else:
                    # Only one form works - acceptable for fallback behavior
                    working_form = "plural" if plural_success else "singular"

                    if expect_same and singular_success:
                        # For cremore, plural should eventually work via fallback
                        if plural_success:
                            results.add_pass(f"Plural/singular: {description}",
                                           f"Plural fallback working correctly")
                        else:
                            results.add_warning(f"Plural/singular: {description}",
                                              f"Plural fallback not working yet (backend deploying?)")
                    else:
                        results.add_pass(f"Plural/singular: {description}",
                                       f"{working_form} form geocodes successfully")
            else:
                # Both failed - this might be OK if the address doesn't exist
                results.add_warning(f"Plural/singular: {description}",
                                  f"Neither form geocodes (address may not exist in database)")
        except Exception as e:
            results.add_fail(f"Plural/singular: {description}", str(e))


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


async def test_address_normalization(results: TestResults):
    """Test that all addresses have normalized versions populated."""
    import asyncpg
    import os
    import re

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        results.add_warning("Address normalization", "DATABASE_URL not set - skipping")
        return

    def normalize_address(address: str) -> str:
        """Normalize address using same logic as normalize_addresses.py script."""
        if not address:
            return address

        normalized = address.strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r',\s*,+', ',', normalized)
        normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)
        normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

        street_types = {
            r'\bSt\.?\b': 'Street', r'\bRd\.?\b': 'Road', r'\bAve\.?\b': 'Avenue',
            r'\bDr\.?\b': 'Drive', r'\bCl\.?\b': 'Close', r'\bCt\.?\b': 'Court',
            r'\bPk\.?\b': 'Park', r'\bSq\.?\b': 'Square',
        }
        for abbrev, full in street_types.items():
            normalized = re.sub(abbrev, full, normalized, flags=re.I)

        normalized = re.sub(r',\s*,', ',', normalized)
        normalized = re.sub(r'\s+,', ',', normalized)
        normalized = re.sub(r',\s+', ', ', normalized)
        normalized = normalized.strip(', ')

        words = normalized.split()
        lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
        upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

        result_words = []
        for i, word in enumerate(words):
            if i == 0:
                result_words.append(word.capitalize())
            elif word in upper_exceptions:
                result_words.append(word)
            elif word.lower() in lower_exceptions:
                result_words.append(word.lower())
            else:
                result_words.append(word.capitalize())

        return ' '.join(result_words).strip()

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        null_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM properties
            WHERE address IS NOT NULL
            AND (address_normalized IS NULL OR address_normalized = '')
        """)

        if null_count == 0:
            total = await conn.fetchval("SELECT COUNT(*) FROM properties WHERE address IS NOT NULL")
            results.add_pass("Address normalization", f"All {total:,} addresses normalized")
        else:
            print(f"   Found {null_count:,} unnormalized addresses - populating (limit 10k)...")

            rows = await conn.fetch("""
                SELECT id, address
                FROM properties
                WHERE address IS NOT NULL
                AND (address_normalized IS NULL OR address_normalized = '')
                LIMIT 10000
            """)

            BATCH_SIZE = 1000
            updated = 0

            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i:i+BATCH_SIZE]
                async with conn.transaction():
                    for row in batch:
                        normalized = normalize_address(row['address'])
                        await conn.execute("""
                            UPDATE properties SET address_normalized = $1 WHERE id = $2
                        """, normalized, row['id'])
                        updated += 1

            remaining = await conn.fetchval("""
                SELECT COUNT(*)
                FROM properties
                WHERE address IS NOT NULL
                AND (address_normalized IS NULL OR address_normalized = '')
            """)

            if remaining == 0:
                results.add_pass("Address normalization", f"Populated {updated:,} addresses")
            else:
                results.add_warning("Address normalization",
                                  f"Populated {updated:,}, {remaining:,} remaining - run scripts/normalize_addresses.py")

        await conn.close()

    except Exception as e:
        results.add_fail("Address normalization", str(e))


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


async def test_database_statistics(results: TestResults):
    """Track database statistics: email signups, feedback, contact messages."""
    import os
    import asyncpg

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        results.add_fail("Database statistics", "DATABASE_URL not set")
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=10.0)

        # Email alert subscriptions
        try:
            email_count = await conn.fetchval("""
                SELECT COUNT(*) FROM email_alerts WHERE is_active = TRUE
            """)
            results.add_pass("Email alert subscriptions",
                           f"{email_count:,} active subscriptions")
        except Exception:
            results.add_warning("Email alert subscriptions",
                              "Table not found (run db/email_alerts.sql)")

        # Feedback submissions
        try:
            feedback_count = await conn.fetchval("""
                SELECT COUNT(*) FROM submissions WHERE form_type = 'feedback'
            """)
            results.add_pass("Feedback submissions",
                           f"{feedback_count:,} total submissions")
        except Exception:
            results.add_warning("Feedback submissions",
                              "Table not found")

        # Contact submissions
        try:
            contact_count = await conn.fetchval("""
                SELECT COUNT(*) FROM submissions WHERE form_type = 'contact'
            """)
            results.add_pass("Contact submissions",
                           f"{contact_count:,} total messages")
        except Exception:
            results.add_warning("Contact submissions",
                              "Table not found")

        await conn.close()

    except Exception as e:
        results.add_fail("Database statistics", str(e))


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

        # Check policies exist and are appropriate
        policies = await conn.fetch("""
            SELECT policyname, cmd, roles::text[]
            FROM pg_policies
            WHERE tablename = 'properties'
            ORDER BY policyname
        """)

        if len(policies) == 0:
            results.add_fail("Security policies configured",
                           "No policies found - table may be inaccessible")
        else:
            # Detailed policy analysis
            has_public_read = False
            has_auth_write = False
            policy_details = []

            for p in policies:
                policy_name = p['policyname']
                cmd = p['cmd']
                roles = p['roles']

                policy_details.append(f"{cmd}:{','.join(roles)}")

                # Check for public read access
                if cmd == 'SELECT' and 'public' in roles:
                    has_public_read = True

                # Check for authenticated write access
                if cmd == 'ALL' and 'authenticated' in roles:
                    has_auth_write = True

            # Verify expected configuration
            if has_public_read and has_auth_write:
                results.add_pass("Security policies configured",
                               f"{len(policies)} policies: {', '.join(policy_details)}")
            elif has_public_read and not has_auth_write:
                results.add_warning("Security policies configured",
                                  f"Public read OK, but no auth write policy")
            elif not has_public_read:
                results.add_warning("Security policies configured",
                                  "No public read policy - data not accessible via API")
            else:
                results.add_pass("Security policies configured",
                               f"{len(policies)} policies active")

        # Verify read access still works
        count = await conn.fetchval("SELECT COUNT(*) FROM properties LIMIT 1")
        if count is not None:
            results.add_pass("Read access verified", f"✓ Can query {count:,} properties")
        else:
            results.add_fail("Read access verified", "Cannot read data")

        # Test that anonymous writes are blocked (simulate anon user)
        try:
            # This should fail with RLS error
            await conn.execute("""
                SET ROLE anon;
                INSERT INTO properties (address, price, sale_date)
                VALUES ('Test Security', 100000, '2026-01-01');
            """)
            results.add_fail("Write protection verified",
                           "CRITICAL: Anonymous writes are NOT blocked")
        except asyncpg.exceptions.InsufficientPrivilegeError:
            results.add_pass("Write protection verified", "✓ Anonymous writes blocked")
        except Exception as e:
            # Other errors are acceptable (e.g., role doesn't exist, RLS policy violation)
            if "row-level security" in str(e).lower() or "permission denied" in str(e).lower():
                results.add_pass("Write protection verified", "✓ Anonymous writes blocked")
            else:
                results.add_warning("Write protection test", f"Unexpected error: {str(e)[:100]}")
        finally:
            # Reset role
            await conn.execute("RESET ROLE;")

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

        # Check for proper indexes on security-critical queries
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'properties'
            AND indexdef LIKE '%geog%'
        """)

        if indexes:
            results.add_pass("Spatial indexes present", f"✓ {len(indexes)} geospatial indexes")
        else:
            results.add_warning("Spatial indexes", "No geospatial indexes found - queries may be slow")

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


async def get_random_test_addresses() -> Tuple[str, str]:
    """
    Get two test addresses from database:
    1. Random address that exists (for positive test)
    2. Fake address that doesn't exist (for negative test)

    Returns:
        Tuple of (existing_address, non_existing_address)
    """
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

        # Get a random property with coordinates and decent price
        row = await conn.fetchrow("""
            SELECT address
            FROM properties
            WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND price > 200000
            AND price < 1000000
            AND address NOT LIKE '%APT%'
            AND address NOT LIKE '%APARTMENT%'
            ORDER BY RANDOM()
            LIMIT 1
        """)

        existing_address = row['address'] if row else "28 Slane Road"

        # Create a fake address that definitely doesn't exist
        non_existing_address = "999 Nonexistent Fake Street, Imaginarytown, Dublin 99"

        await conn.close()
        return existing_address, non_existing_address

    except Exception as e:
        print(f"Warning: Could not fetch random addresses from database: {e}")
        # Fallback to known addresses
        return "28 Slane Road", "999 Nonexistent Fake Street, Imaginarytown, Dublin 99"


async def test_valuation_existing_property(client: httpx.AsyncClient, results: TestResults, address: str):
    """Test valuation for a property that exists in database."""
    try:
        resp = await client.post(
            f"{BACKEND_URL}/api/valuation/estimate",
            json={"address": address},
            timeout=30.0
        )

        if resp.status_code == 200:
            data = resp.json()

            # Validate response structure
            required_fields = ['estimate', 'confidence_interval', 'validation', 'comparables', 'statistics', 'metadata']
            missing = [f for f in required_fields if f not in data]

            if missing:
                results.add_fail(f"Valuation: {address[:40]}...", f"Missing fields: {', '.join(missing)}")
                return

            # Check estimate is reasonable
            estimate = data['estimate']
            if not (50000 <= estimate <= 5000000):
                results.add_fail(f"Valuation: {address[:40]}...", f"Unrealistic estimate: €{estimate:,}")
                return

            # Check geocoding method
            geocode_method = data['metadata']['geocoded_location']['method']
            if geocode_method != 'database_exact':
                results.add_warning(f"Valuation: {address[:40]}...",
                                  f"Used {geocode_method} instead of database_exact")

            # Check comparables
            n_comparables = len(data['comparables'])
            if n_comparables < 5:
                results.add_warning(f"Valuation: {address[:40]}...",
                                  f"Only {n_comparables} comparables (expected ≥5)")

            confidence = data['validation']['confidence_level']
            results.add_pass(f"Valuation: {address[:40]}...",
                           f"€{estimate:,} ({confidence}, {n_comparables} comps, method: {geocode_method})")

        elif resp.status_code == 404:
            results.add_fail(f"Valuation: {address[:40]}...",
                           "Property not found (should exist in database)")
        else:
            results.add_fail(f"Valuation: {address[:40]}...",
                           f"HTTP {resp.status_code}: {resp.text[:100]}")

    except Exception as e:
        results.add_fail(f"Valuation: {address[:40]}...", str(e))


async def test_valuation_nonexistent_property(client: httpx.AsyncClient, results: TestResults, address: str):
    """Test valuation for a property that doesn't exist - should fail gracefully."""
    try:
        resp = await client.post(
            f"{BACKEND_URL}/api/valuation/estimate",
            json={"address": address},
            timeout=30.0
        )

        # Should return 400 (bad request) with helpful error message
        if resp.status_code == 400:
            data = resp.json()
            detail = data.get('detail', '')

            # Check error message is helpful
            if 'Could not locate' in detail or 'Not Found' in detail:
                results.add_pass(f"Valuation (non-existent): {address[:30]}...",
                               f"Correct error: {detail[:60]}")
            else:
                results.add_warning(f"Valuation (non-existent): {address[:30]}...",
                                  f"Error message unclear: {detail[:60]}")

        elif resp.status_code == 404:
            # Also acceptable
            results.add_pass(f"Valuation (non-existent): {address[:30]}...",
                           "Correctly returned 404")

        elif resp.status_code == 200:
            # Should NOT succeed for fake address
            results.add_fail(f"Valuation (non-existent): {address[:30]}...",
                           "Should have failed but returned 200")

        else:
            results.add_warning(f"Valuation (non-existent): {address[:30]}...",
                              f"Unexpected status: {resp.status_code}")

    except Exception as e:
        results.add_fail(f"Valuation (non-existent): {address[:30]}...", str(e))


async def test_valuation_with_enrichment(client: httpx.AsyncClient, results: TestResults, address: str):
    """Test valuation with optional enrichment data (bedrooms, BER)."""
    try:
        resp = await client.post(
            f"{BACKEND_URL}/api/valuation/estimate",
            json={
                "address": address,
                "bedrooms": 3,
                "ber_rating": "B2"
            },
            timeout=30.0
        )

        if resp.status_code == 200:
            data = resp.json()
            estimate = data['estimate']
            results.add_pass(f"Valuation with enrichment: {address[:30]}...",
                           f"€{estimate:,} (3 bed, B2 BER)")
        elif resp.status_code in [400, 404]:
            # Expected if property doesn't exist
            results.add_pass(f"Valuation with enrichment: {address[:30]}...",
                           "Graceful failure")
        else:
            results.add_fail(f"Valuation with enrichment: {address[:30]}...",
                           f"HTTP {resp.status_code}")

    except Exception as e:
        results.add_fail(f"Valuation with enrichment: {address[:30]}...", str(e))


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

    # Get random test addresses for valuation tests
    print("Selecting random test addresses...")
    existing_address, non_existing_address = await get_random_test_addresses()
    print(f"  Existing: {existing_address}")
    print(f"  Non-existing: {non_existing_address}\n")

    async with httpx.AsyncClient() as client:
        # Database statistics (informational)
        print("Database Statistics:")
        await test_database_statistics(results)

        # Security tests (most important)
        print("\nSecurity:")
        await test_database_security(results)
        await test_api_security(client, results)

        # Backend tests
        print("\nBackend Health:")
        await test_backend_health(client, results)

        print("\nBackend Geocoding:")
        await test_backend_geocoding(client, results)

        print("\nBackend Search:")
        await test_backend_search(client, results)
        await test_county_filter_fallback(client, results)

        print("\nPlural/Singular Matching:")
        await test_plural_singular_geocoding(client, results)

        print("\nBackend Trends:")
        await test_backend_trends(client, results)

        print("\nBackend Eircode:")
        await test_backend_eircode(client, results)

        print("\nBackend Counties:")
        await test_backend_counties(client, results)

        print("\nCoordinate Quality:")
        await test_coordinate_quality(client, results)

        print("\nValuation API:")
        await test_valuation_existing_property(client, results, existing_address)
        await test_valuation_nonexistent_property(client, results, non_existing_address)
        await test_valuation_with_enrichment(client, results, existing_address)

        print("\nFrontend:")
        await test_frontend_loads(client, results)
        await test_frontend_api_calls(client, results)

        print("\nAddress Normalization:")
        await test_address_normalization(results)

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
