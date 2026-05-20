#!/usr/bin/env python3
"""
Fast county validation using approximate bounding boxes.

Uses conservative bounding boxes for each Irish county to quickly validate
that geocoded coordinates are approximately in the right area.

This won't catch all errors (counties have irregular shapes) but will catch
obvious mistakes like a Meath address geocoded to Cork.
"""

from typing import Tuple, Optional


# Approximate bounding boxes for Irish counties: (min_lat, max_lat, min_lon, max_lon)
# Generated from OSM data, with slight padding for border areas
COUNTY_BOUNDS = {
    "Carlow": (52.58, 52.90, -6.99, -6.66),
    "Cavan": (53.75, 54.15, -7.66, -6.85),
    "Clare": (52.58, 53.20, -9.80, -8.38),
    "Cork": (51.42, 52.30, -9.90, -7.65),
    "Donegal": (54.45, 55.44, -8.55, -7.40),
    "Dublin": (53.20, 53.50, -6.50, -6.00),
    "Galway": (52.98, 53.70, -10.30, -8.15),
    "Kerry": (51.70, 52.50, -10.50, -9.20),
    "Kildare": (52.99, 53.42, -7.22, -6.50),
    "Kilkenny": (52.48, 52.82, -7.54, -7.00),
    "Laois": (52.75, 53.20, -7.80, -7.15),
    "Leitrim": (54.02, 54.47, -8.35, -7.65),
    "Limerick": (52.40, 52.75, -9.20, -8.30),
    "Longford": (53.58, 53.87, -8.00, -7.50),
    "Louth": (53.75, 54.16, -6.70, -6.17),
    "Mayo": (53.50, 54.30, -10.15, -8.60),
    "Meath": (53.50, 53.95, -7.30, -6.35),
    "Monaghan": (54.00, 54.35, -7.30, -6.60),
    "Offaly": (53.05, 53.43, -8.10, -7.18),
    "Roscommon": (53.53, 54.15, -8.65, -7.85),
    "Sligo": (54.05, 54.50, -8.95, -8.20),
    "Tipperary": (52.35, 52.95, -8.40, -7.40),
    "Waterford": (51.95, 52.40, -8.10, -6.95),
    "Westmeath": (53.38, 53.73, -7.90, -7.18),
    "Wexford": (52.20, 52.73, -6.95, -6.28),
    "Wicklow": (52.78, 53.28, -6.75, -5.99),
}

# Alternative spellings and common variations
COUNTY_ALIASES = {
    "Co. Carlow": "Carlow",
    "Co Carlow": "Carlow",
    "Co. Cavan": "Cavan",
    "Co Cavan": "Cavan",
    "Co. Clare": "Clare",
    "Co Clare": "Clare",
    "Co. Cork": "Cork",
    "Co Cork": "Cork",
    "Co. Donegal": "Donegal",
    "Co Donegal": "Donegal",
    "Co. Dublin": "Dublin",
    "Co Dublin": "Dublin",
    "Co. Galway": "Galway",
    "Co Galway": "Galway",
    "Co. Kerry": "Kerry",
    "Co Kerry": "Kerry",
    "Co. Kildare": "Kildare",
    "Co Kildare": "Kildare",
    "Co. Kilkenny": "Kilkenny",
    "Co Kilkenny": "Kilkenny",
    "Co. Laois": "Laois",
    "Co Laois": "Laois",
    "Laoighis": "Laois",
    "Co. Leitrim": "Leitrim",
    "Co Leitrim": "Leitrim",
    "Co. Limerick": "Limerick",
    "Co Limerick": "Limerick",
    "Co. Longford": "Longford",
    "Co Longford": "Longford",
    "Co. Louth": "Louth",
    "Co Louth": "Louth",
    "Co. Mayo": "Mayo",
    "Co Mayo": "Mayo",
    "Co. Meath": "Meath",
    "Co Meath": "Meath",
    "Co. Monaghan": "Monaghan",
    "Co Monaghan": "Monaghan",
    "Co. Offaly": "Offaly",
    "Co Offaly": "Offaly",
    "Co. Roscommon": "Roscommon",
    "Co Roscommon": "Roscommon",
    "Co. Sligo": "Sligo",
    "Co Sligo": "Sligo",
    "Co. Tipperary": "Tipperary",
    "Co Tipperary": "Tipperary",
    "North Tipperary": "Tipperary",
    "South Tipperary": "Tipperary",
    "Co. Waterford": "Waterford",
    "Co Waterford": "Waterford",
    "Co. Westmeath": "Westmeath",
    "Co Westmeath": "Westmeath",
    "Co. Wexford": "Wexford",
    "Co Wexford": "Wexford",
    "Co. Wicklow": "Wicklow",
    "Co Wicklow": "Wicklow",
}


def normalize_county(county: str) -> str:
    """Normalize county name."""
    if not county:
        return ""

    county = county.strip()

    # Check aliases first
    if county in COUNTY_ALIASES:
        return COUNTY_ALIASES[county]

    # Title case
    county_title = county.title()
    if county_title in COUNTY_BOUNDS:
        return county_title

    # Remove "Co." or "Co" prefix
    if county.lower().startswith("co."):
        county = county[3:].strip()
    elif county.lower().startswith("co "):
        county = county[3:].strip()

    county_title = county.title()
    if county_title in COUNTY_BOUNDS:
        return county_title

    return county_title


def validate_county(lat: float, lon: float, county: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that coordinates fall within expected county bounding box.

    Returns:
        (is_valid, reason)
        - is_valid: True if coordinates are approximately in the correct county
        - reason: Explanation if invalid (None if valid)
    """
    county_normalized = normalize_county(county)

    if not county_normalized:
        # No county specified, can't validate
        return (True, None)

    if county_normalized not in COUNTY_BOUNDS:
        # Unknown county, can't validate
        return (True, None)

    min_lat, max_lat, min_lon, max_lon = COUNTY_BOUNDS[county_normalized]

    # Check if coordinate is within bounding box
    if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
        return (True, None)

    # Find which county it might actually be in
    actual_counties = []
    for c, bounds in COUNTY_BOUNDS.items():
        min_lat_c, max_lat_c, min_lon_c, max_lon_c = bounds
        if min_lat_c <= lat <= max_lat_c and min_lon_c <= lon <= max_lon_c:
            actual_counties.append(c)

    if actual_counties:
        return (False, f"Coordinate ({lat:.6f}, {lon:.6f}) is outside {county_normalized} bounds. "
                      f"Appears to be in: {', '.join(actual_counties)}")
    else:
        return (False, f"Coordinate ({lat:.6f}, {lon:.6f}) is outside {county_normalized} bounds "
                      f"and doesn't match any other Irish county")


def main():
    """Test county validation."""
    print("="*70)
    print("County Boundary Validation Tests")
    print("="*70)
    print()

    # Test cases: (lat, lon, county, should_pass, description)
    test_cases = [
        (53.3498, -6.2603, "Dublin", True, "Dublin city center → Dublin county"),
        (51.8969, -8.4863, "Cork", True, "Cork city center → Cork county"),
        (53.2707, -9.0568, "Galway", True, "Galway city center → Galway county"),
        (53.8217, -6.7479, "Meath", True, "Nobber → Meath county"),
        (53.8217, -6.7479, "Co. Meath", True, "Nobber → 'Co. Meath' (alias test)"),
        (52.6600, -8.6300, "Limerick", True, "Limerick city → Limerick county"),
        (53.3498, -6.2603, "Cork", False, "Dublin coords → Cork (should fail)"),
        (51.8969, -8.4863, "Dublin", False, "Cork coords → Dublin (should fail)"),
        (53.717143, -7.062706, "Meath", True, "Wrong Nobber coords → Meath (still in bounds)"),
        (52.6843, -8.5774, "Limerick", True, "Limerick centroid → Limerick"),
    ]

    passed = 0
    failed = 0

    for lat, lon, county, should_pass, description in test_cases:
        is_valid, reason = validate_county(lat, lon, county)

        if is_valid == should_pass:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"{status}: {description}")
        print(f"  County: {county} | Coords: ({lat:.4f}, {lon:.4f})")
        if not is_valid:
            print(f"  Reason: {reason}")
        print()

    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)


if __name__ == "__main__":
    main()
