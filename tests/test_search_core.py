"""
Core search functionality tests - MUST PASS before any search-related changes.

This test suite protects critical search behavior from regressions.
Run locally: pytest tests/test_search_core.py -v
Run in CI: Automatically runs on every PR that touches search code

PROTECTED BEHAVIORS:
1. County filter must be respected in exact search
2. County filter must be respected in radius search
3. Exact matches should not leak across county boundaries
4. Search results should only contain properties from filtered county
"""

import pytest
import httpx
import os
import asyncio

# Use production URL if DATABASE_URL is set, otherwise local
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")

# Critical search scenarios that must always work
# Format: (query, county_filter, expected_county_in_results, min_results, description)
SEARCH_TEST_CASES = [
    # County filter correctness - exact search
    ("36 fairfield road", "Dublin", "Dublin", 0, "No Dublin result when Cork property exists"),
    ("36 fairfield road", "Cork", "Cork", 1, "Cork result when filtering Cork"),
    ("19 fairfield road", "Dublin", "Dublin", 1, "Dublin result when filtering Dublin"),

    # County filter correctness - radius search
    ("Dublin 2", "Dublin", "Dublin", 50, "Area search stays in county"),
    ("Nobber", "Meath", "Meath", 100, "Town search respects county filter"),
    ("Glasnevin", "Dublin", "Dublin", 200, "Neighborhood search respects county"),

    # Eircode search
    ("D02", None, "Dublin", 20, "Eircode search without filter"),
    ("D02", "Dublin", "Dublin", 20, "Eircode search with matching county"),

    # Cross-county ambiguous addresses
    ("Main Street", "Cork", "Cork", 10, "Generic street name filtered to Cork"),
    ("Main Street", "Galway", "Galway", 10, "Generic street name filtered to Galway"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,county,expected_county,min_count,description", SEARCH_TEST_CASES)
async def test_search_respects_county_filter(query, county, expected_county, min_count, description):
    """Verify search results respect county filter and return expected data."""
    params = {"q": query, "radius_km": "5"}
    if county:
        params["county"] = county

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test radius search
        response = await client.get(f"{BASE_URL}/search", params=params)
        assert response.status_code == 200, f"Search failed for: {description}"
        data = response.json()

        # Verify result count
        assert data["count"] >= min_count, \
            f"Expected >= {min_count} results for '{description}', got {data['count']}"

        # Verify all results match expected county
        if expected_county and data["results"]:
            counties = {r["county"] for r in data["results"]}
            assert expected_county in counties, \
                f"Expected {expected_county} in results for '{description}', got {counties}"

            # CRITICAL: If county filter is set, NO results from other counties
            if county:
                wrong_counties = [r for r in data["results"] if r["county"] != expected_county]
                assert len(wrong_counties) == 0, \
                    f"County filter breach in '{description}': found {len(wrong_counties)} results from wrong county"


@pytest.mark.asyncio
@pytest.mark.parametrize("address,county,expected_county,exact_count", [
    ("36 fairfield road", "Dublin", "Dublin", 0),  # No match in Dublin
    ("36 fairfield road", "Cork", "Cork", 1),      # Exact match in Cork
    ("19 fairfield road", "Dublin", "Dublin", 2),  # Multiple sales at same address
    ("36 fairfield road", None, "Cork", 1),        # No filter returns all
])
async def test_exact_search_respects_county_filter(address, county, expected_county, exact_count):
    """Verify exact search endpoint respects county filter."""
    params = {"address": address}
    if county:
        params["county"] = county

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/search/exact", params=params)
        assert response.status_code == 200
        data = response.json()

        # Verify count
        assert data["count"] == exact_count, \
            f"Expected {exact_count} exact matches for '{address}' in {county}, got {data['count']}"

        # CRITICAL: Verify county filter is respected
        if county and data["results"]:
            wrong_county = [r for r in data["results"] if r["county"] != county]
            assert len(wrong_county) == 0, \
                f"COUNTY FILTER BREACH: Exact search for '{address}' with county={county} returned {len(wrong_county)} results from other counties"


@pytest.mark.asyncio
async def test_cache_respects_county_filter():
    """Verify cache isolation - different counties should not share cached results."""
    address = "36 fairfield road"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request: Dublin (should return 0)
        response1 = await client.get(f"{BASE_URL}/search/exact", params={"address": address, "county": "Dublin"})
        data1 = response1.json()

        # Second request: Cork (should return 1)
        response2 = await client.get(f"{BASE_URL}/search/exact", params={"address": address, "county": "Cork"})
        data2 = response2.json()

        # Third request: Dublin again (should still return 0, not Cork's cached result)
        response3 = await client.get(f"{BASE_URL}/search/exact", params={"address": address, "county": "Dublin"})
        data3 = response3.json()

        assert data1["count"] == 0, "Dublin should have 0 results"
        assert data2["count"] == 1, "Cork should have 1 result"
        assert data3["count"] == 0, "Dublin should still have 0 results (cache isolation)"

        if data2["results"]:
            assert data2["results"][0]["county"] == "Cork", "Cork result should be from Cork"


@pytest.mark.asyncio
async def test_performance_regression():
    """Verify search performance hasn't regressed."""
    import time

    queries = [
        ("Dublin 2", "Dublin"),
        ("Nobber", "Meath"),
        ("19 fairfield road", "Dublin"),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query, county in queries:
            start = time.time()
            response = await client.get(f"{BASE_URL}/search", params={"q": query, "county": county, "radius_km": "5"})
            elapsed = time.time() - start

            assert response.status_code == 200
            assert elapsed < 1.0, f"Search for '{query}' took {elapsed:.2f}s (expected < 1.0s)"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify API is reachable."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


if __name__ == "__main__":
    # Allow running directly: python tests/test_search_core.py
    pytest.main([__file__, "-v", "--tb=short"])
