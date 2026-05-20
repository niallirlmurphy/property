#!/usr/bin/env python3
"""
County boundary validation for geocoding.

Uses Overpass API to fetch Ireland county boundaries from OSM and validates
that geocoded coordinates fall within the expected county.

Uses Overpass Turbo API for boundary data and shapely for point-in-polygon checks.
"""

import asyncio
import httpx
import json
from typing import Optional, Tuple, Dict
from pathlib import Path
from shapely.geometry import shape, Point, MultiPolygon, Polygon
from shapely.prepared import prep

CACHE_FILE = Path("data/county_boundaries.json")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class CountyBoundaryValidator:
    """Validates that coordinates fall within expected county boundaries."""

    def __init__(self):
        self.boundaries: Dict[str, any] = {}
        self.prepared_boundaries: Dict[str, any] = {}
        self._load_cache()

    def _load_cache(self):
        """Load cached county boundaries."""
        if CACHE_FILE.exists():
            with open(CACHE_FILE) as f:
                data = json.load(f)
                for county, geojson in data.items():
                    self.boundaries[county] = geojson
                    geom = shape(geojson)
                    self.prepared_boundaries[county] = prep(geom)
            print(f"✓ Loaded {len(self.boundaries)} county boundaries from cache")

    def _save_cache(self):
        """Save county boundaries to cache."""
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.boundaries, f, indent=2)
        print(f"✓ Saved {len(self.boundaries)} county boundaries to cache")

    async def fetch_county_boundary(self, county: str, client: httpx.AsyncClient) -> Optional[dict]:
        """
        Fetch county boundary polygon from Overpass API.
        Returns GeoJSON geometry or None.
        """
        # Normalize county name
        county_normalized = county.strip().title()

        if county_normalized in self.boundaries:
            return self.boundaries[county_normalized]

        try:
            # Overpass query for Irish county administrative boundaries
            # admin_level=6 in Ireland corresponds to counties
            query = f"""
            [out:json][timeout:25];
            area["ISO3166-1"="IE"]->.ireland;
            (
              relation["admin_level"="6"]["name"="{county_normalized}"](area.ireland);
            );
            out geom;
            """

            resp = await client.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=30.0
            )
            await asyncio.sleep(2.0)  # Overpass rate limit

            if resp.status_code != 200:
                print(f"  Warning: Could not fetch boundary for {county_normalized}: {resp.status_code}")
                return None

            data = resp.json()
            if not data.get("elements"):
                print(f"  Warning: No boundary found for {county_normalized}")
                return None

            # Convert OSM relation to GeoJSON polygon
            element = data["elements"][0]

            # Extract outer way coordinates
            outer_coords = []
            for member in element.get("members", []):
                if member.get("role") == "outer" and member.get("geometry"):
                    coords = [(point["lon"], point["lat"]) for point in member["geometry"]]
                    outer_coords.append(coords)

            if not outer_coords:
                print(f"  Warning: No valid geometry for {county_normalized}")
                return None

            # Create GeoJSON polygon
            if len(outer_coords) == 1:
                geojson = {
                    "type": "Polygon",
                    "coordinates": outer_coords
                }
            else:
                # Multiple outer rings = MultiPolygon
                geojson = {
                    "type": "MultiPolygon",
                    "coordinates": [[ring] for ring in outer_coords]
                }

            self.boundaries[county_normalized] = geojson

            # Prepare geometry for fast point-in-polygon checks
            geom = shape(geojson)
            self.prepared_boundaries[county_normalized] = prep(geom)

            self._save_cache()
            print(f"  ✓ Loaded boundary for {county_normalized}")
            return geojson

        except Exception as e:
            print(f"  Error fetching boundary for {county_normalized}: {e}")
            return None

    def validate_coordinate(self, lat: float, lon: float, expected_county: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a coordinate falls within the expected county.
        Returns (is_valid, reason).

        - is_valid: True if coordinate is in expected county
        - reason: Explanation if invalid (None if valid)
        """
        county_normalized = expected_county.strip().title()

        if county_normalized not in self.prepared_boundaries:
            # Can't validate without boundary data
            return (True, None)

        point = Point(lon, lat)  # Shapely uses (x, y) = (lon, lat)
        prepared_geom = self.prepared_boundaries[county_normalized]

        if prepared_geom.contains(point):
            return (True, None)
        else:
            return (False, f"Coordinate ({lat:.6f}, {lon:.6f}) falls outside {expected_county} boundary")

    async def preload_counties(self, counties: list[str], client: httpx.AsyncClient):
        """Preload boundary data for a list of counties."""
        print(f"Preloading boundaries for {len(counties)} counties...")
        for county in counties:
            if county.strip().title() not in self.boundaries:
                await self.fetch_county_boundary(county, client)


async def main():
    """Test county boundary validation."""
    validator = CountyBoundaryValidator()

    async with httpx.AsyncClient() as client:
        # Preload common counties
        await validator.preload_counties([
            "Dublin", "Cork", "Galway", "Limerick", "Meath",
            "Kildare", "Wicklow", "Clare", "Kerry", "Tipperary"
        ], client)

    print("\n" + "="*70)
    print("Testing county boundary validation:")
    print("="*70)

    # Test cases: (lat, lon, expected_county, should_pass)
    test_cases = [
        (53.3498, -6.2603, "Dublin", True),       # Dublin city center
        (51.8969, -8.4863, "Cork", True),          # Cork city center
        (53.2707, -9.0568, "Galway", True),        # Galway city center
        (53.8217, -6.7479, "Meath", True),         # Nobber, Meath
        (53.3498, -6.2603, "Cork", False),         # Dublin coords, wrong county
    ]

    for lat, lon, county, should_pass in test_cases:
        is_valid, reason = validator.validate_coordinate(lat, lon, county)

        status = "✓" if is_valid == should_pass else "✗"
        result = "VALID" if is_valid else f"INVALID - {reason}"

        print(f"\n{status} ({lat:.4f}, {lon:.4f}) in {county}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
