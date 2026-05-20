#!/usr/bin/env python3
"""
Compare different geocoding services for Irish addresses.

Tests a sample of addresses with multiple geocoders and reports:
- Success rates
- Accuracy (distance from known-good coordinates)
- Speed
- Cost projection

Usage:
    python3 scripts/compare_geocoders.py [--samples N]
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import time
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")
SF_CONFIGURED = all([
    os.environ.get("SALESFORCE_INSTANCE_URL"),
    os.environ.get("SALESFORCE_CLIENT_ID"),
    os.environ.get("SALESFORCE_CLIENT_SECRET"),
    os.environ.get("SALESFORCE_USERNAME"),
    os.environ.get("SALESFORCE_PASSWORD"),
])

USER_AGENT = "PPR-geocode-comparison/1.0"


async def geocode_nominatim(address: str, county: str, eircode: str) -> Optional[Tuple[float, float]]:
    """Geocode with Nominatim."""
    query = f"{eircode} Ireland" if eircode else f"{address}, {county}, Ireland"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "ie",
                    "bounded": 1
                },
                headers={"User-Agent": USER_AGENT},
                timeout=10.0
            )
            await asyncio.sleep(1.0)  # Rate limit
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
                    if 51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4:
                        return (lat, lon)
    except:
        pass
    return None


async def geocode_mapbox(address: str, county: str) -> Optional[Tuple[float, float]]:
    """Geocode with Mapbox."""
    if not MAPBOX_TOKEN:
        return None
    query = f"{address}, {county}, Ireland"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json",
                params={
                    "access_token": MAPBOX_TOKEN,
                    "country": "ie",
                    "limit": 1
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("features"):
                    lon, lat = data["features"][0]["center"]
                    if 51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4:
                        return (lat, lon)
    except:
        pass
    return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two coordinates."""
    import math
    R = 6371000  # Earth radius in meters
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


async def compare_geocoders(num_samples: int = 50):
    """Compare geocoding services on a sample of properties."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)

    try:
        # Get sample of properties with known-good coordinates
        # Use properties that are NOT at centroid coordinates
        print(f"Selecting {num_samples} sample properties with good coordinates...\n")

        rows = await pool.fetch("""
            WITH centroid_coords AS (
                SELECT latitude, longitude
                FROM properties
                WHERE latitude IS NOT NULL
                GROUP BY latitude, longitude
                HAVING COUNT(DISTINCT address) >= 10
            )
            SELECT p.id, p.address, p.county, p.eircode, p.latitude, p.longitude
            FROM properties p
            LEFT JOIN centroid_coords c
                ON ABS(p.latitude - c.latitude) < 0.000001
                AND ABS(p.longitude - c.longitude) < 0.000001
            WHERE p.latitude IS NOT NULL
              AND c.latitude IS NULL  -- Exclude centroid coordinates
              AND p.eircode IS NOT NULL  -- Prefer properties with eircodes
            ORDER BY RANDOM()
            LIMIT $1
        """, num_samples)

        if len(rows) < num_samples:
            print(f"⚠️  Only found {len(rows)} suitable properties")

        samples = [dict(r) for r in rows]

        print(f"{'='*70}")
        print(f"GEOCODER COMPARISON")
        print(f"{'='*70}\n")

        # Test each geocoder
        results = {
            "nominatim": {"success": 0, "total_error_m": 0, "times": []},
            "mapbox": {"success": 0, "total_error_m": 0, "times": []},
        }

        for i, prop in enumerate(samples, 1):
            print(f"[{i}/{len(samples)}] Testing: {prop['address'][:50]}")
            print(f"  Known coords: ({prop['latitude']:.6f}, {prop['longitude']:.6f})")

            # Nominatim
            start = time.time()
            nom_result = await geocode_nominatim(prop["address"], prop["county"], prop["eircode"])
            nom_time = time.time() - start
            results["nominatim"]["times"].append(nom_time)

            if nom_result:
                error_m = haversine_distance(
                    prop["latitude"], prop["longitude"],
                    nom_result[0], nom_result[1]
                )
                results["nominatim"]["success"] += 1
                results["nominatim"]["total_error_m"] += error_m
                print(f"  ✓ Nominatim: ({nom_result[0]:.6f}, {nom_result[1]:.6f}) | Error: {error_m:.0f}m")
            else:
                print(f"  ✗ Nominatim: No result")

            # Mapbox
            if MAPBOX_TOKEN:
                start = time.time()
                mbx_result = await geocode_mapbox(prop["address"], prop["county"])
                mbx_time = time.time() - start
                results["mapbox"]["times"].append(mbx_time)

                if mbx_result:
                    error_m = haversine_distance(
                        prop["latitude"], prop["longitude"],
                        mbx_result[0], mbx_result[1]
                    )
                    results["mapbox"]["success"] += 1
                    results["mapbox"]["total_error_m"] += error_m
                    print(f"  ✓ Mapbox:    ({mbx_result[0]:.6f}, {mbx_result[1]:.6f}) | Error: {error_m:.0f}m")
                else:
                    print(f"  ✗ Mapbox: No result")
            else:
                print(f"  ⊘ Mapbox: Not configured")

            print()

        # Print summary
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}\n")

        print(f"{'Service':<15} {'Success Rate':<15} {'Avg Error (m)':<18} {'Avg Time (s)':<15} {'Cost'}")
        print(f"{'-'*70}")

        for service, data in results.items():
            if data["times"]:
                success_rate = 100.0 * data["success"] / len(samples)
                avg_error = data["total_error_m"] / max(data["success"], 1)
                avg_time = sum(data["times"]) / len(data["times"])

                # Cost projection for 235k properties
                if service == "nominatim":
                    cost = "Free"
                    time_est = f"{235000 * avg_time / 3600:.0f}h"
                elif service == "mapbox":
                    cost = "$0 (free tier)" if MAPBOX_TOKEN else "N/A"
                    time_est = f"{235000 * avg_time / 3600:.0f}h"
                elif service == "salesforce":
                    cost = "~$235-940"
                    time_est = "47 days (5k/day limit)"
                else:
                    cost = "N/A"
                    time_est = "N/A"

                print(f"{service.title():<15} {success_rate:>6.1f}%        {avg_error:>10.0f}        "
                      f"{avg_time:>6.2f}s         {cost}")
            else:
                print(f"{service.title():<15} Not tested")

        print(f"\n{'='*70}")
        print(f"RECOMMENDATIONS")
        print(f"{'='*70}\n")

        # Determine best geocoder
        best_accuracy = None
        best_speed = None

        for service, data in results.items():
            if data["success"] > 0:
                avg_error = data["total_error_m"] / data["success"]
                if best_accuracy is None or avg_error < best_accuracy[1]:
                    best_accuracy = (service, avg_error)

                avg_time = sum(data["times"]) / len(data["times"])
                if best_speed is None or avg_time < best_speed[1]:
                    best_speed = (service, avg_time)

        if best_accuracy:
            print(f"🎯 Best Accuracy: {best_accuracy[0].title()} ({best_accuracy[1]:.0f}m avg error)")
        if best_speed:
            print(f"⚡ Fastest: {best_speed[0].title()} ({best_speed[1]:.2f}s per request)")

        print(f"\n💡 Recommended Strategy:")
        print(f"   1. Nominatim for eircodes (free, good Irish coverage)")
        print(f"   2. Mapbox for street addresses (fast, accurate)")
        if SF_CONFIGURED:
            print(f"   3. Salesforce for remaining (enterprise quality)")
        else:
            print(f"   3. Salesforce available but not configured")

        print(f"\n📊 Projected Timeline for 235,405 properties:")
        if "nominatim" in results and results["nominatim"]["times"]:
            nom_time = 235405 / 3600  # 1 req/s rate limit
            print(f"   Nominatim only: ~{nom_time:.0f} hours")

        if "mapbox" in results and results["mapbox"]["times"] and MAPBOX_TOKEN:
            mbx_time = 235405 / 36000  # 10 req/s
            print(f"   Mapbox only: ~{mbx_time:.0f} hours")

        print(f"   Salesforce only: 47 days (5,000/day limit)")
        print(f"   Hybrid approach: ~1-2 weeks (best quality)")

    finally:
        await pool.close()


async def main():
    num_samples = 50

    for i, arg in enumerate(sys.argv):
        if arg == "--samples" and i + 1 < len(sys.argv):
            num_samples = int(sys.argv[i + 1])

    print("Geocoder Comparison Tool\n")
    print("Testing with sample Irish addresses...\n")

    if not MAPBOX_TOKEN:
        print("⚠️  MAPBOX_TOKEN not set - Mapbox comparison will be skipped")
        print("   Add MAPBOX_TOKEN to backend/.env to test Mapbox\n")

    if not SF_CONFIGURED:
        print("⚠️  Salesforce not configured - comparison will exclude Salesforce")
        print("   See scripts/SALESFORCE_GEOCODING.md for setup\n")

    await compare_geocoders(num_samples)


if __name__ == "__main__":
    asyncio.run(main())
