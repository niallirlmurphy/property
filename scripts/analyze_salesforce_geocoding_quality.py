#!/usr/bin/env python3
"""
Data quality analysis for Salesforce-geocoded Irish properties.

Compares against the quality issues we found with Nominatim/Mapbox geocoding:
- Centroid coordinates (100+ addresses at same point)
- Out of bounds coordinates
- Suspicious precision patterns
- Geographic distribution
- County validation
"""

import csv
import sys
from collections import defaultdict, Counter
from datetime import datetime

sys.path.insert(0, '/Users/nmurphy/claude/property price project/scripts')
from county_validator import validate_county

INPUT_FILE = "Salesforce-geocoded-irish-properties.csv"
IRELAND_BBOX = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon


def analyze_geocoding_quality():
    """Run comprehensive quality analysis."""

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     SALESFORCE GEOCODING QUALITY ANALYSIS                    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Data structures for analysis
    coord_to_addresses = defaultdict(list)
    county_stats = defaultdict(int)
    precision_patterns = Counter()
    out_of_bounds = []
    county_mismatches = []

    total_records = 0
    missing_coords = 0

    print(f"Reading {INPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_records += 1

            name = row.get('Name', '')
            city = row.get('BillingCity', '')
            lat_str = row.get('BillingLatitude', '')
            lon_str = row.get('BillingLongitude', '')

            # Check for missing coordinates
            if not lat_str or not lon_str:
                missing_coords += 1
                continue

            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                missing_coords += 1
                continue

            # County stats
            county_stats[city] += 1

            # Round to 6 decimals for centroid detection
            coord_key = (round(lat, 6), round(lon, 6))
            coord_to_addresses[coord_key].append({
                'name': name,
                'county': city,
                'lat': lat,
                'lon': lon
            })

            # Check bounds
            min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
            if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                out_of_bounds.append({
                    'name': name,
                    'county': city,
                    'lat': lat,
                    'lon': lon
                })

            # Check precision patterns
            lat_decimals = len(str(lat).split('.')[-1]) if '.' in str(lat) else 0
            lon_decimals = len(str(lon).split('.')[-1]) if '.' in str(lon) else 0
            precision_patterns[(lat_decimals, lon_decimals)] += 1

            # County validation
            if city:
                is_valid, reason = validate_county(lat, lon, city)
                if not is_valid:
                    county_mismatches.append({
                        'name': name,
                        'county': city,
                        'lat': lat,
                        'lon': lon,
                        'reason': reason
                    })

            if total_records % 50000 == 0:
                print(f"  Processed {total_records:,} records...")

    print(f"✓ Processed {total_records:,} records")
    print()

    # Analysis Results
    print("="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    print(f"Total records: {total_records:,}")
    print(f"Valid coordinates: {total_records - missing_coords:,} ({100*(total_records-missing_coords)/total_records:.1f}%)")
    print(f"Missing coordinates: {missing_coords:,}")
    print()

    # Centroid Detection
    print("="*70)
    print("CENTROID DETECTION")
    print("="*70)

    high_priority = {coord: addrs for coord, addrs in coord_to_addresses.items()
                     if len(addrs) >= 100}
    medium_priority = {coord: addrs for coord, addrs in coord_to_addresses.items()
                       if 10 <= len(addrs) < 100}

    print(f"HIGH Priority (100+ addresses at same point): {len(high_priority):,}")
    print(f"MEDIUM Priority (10-99 addresses): {len(medium_priority):,}")
    print(f"Total affected properties: {sum(len(addrs) for addrs in high_priority.values()):,}")
    print()

    if high_priority:
        print("Top 10 problem coordinates:")
        print(f"{'Coordinate':<30} {'Count':<10} {'Sample Counties'}")
        print("-" * 70)

        sorted_centroids = sorted(high_priority.items(),
                                 key=lambda x: len(x[1]),
                                 reverse=True)[:10]

        for coord, addresses in sorted_centroids:
            counties = list(set(a['county'] for a in addresses[:10]))
            county_str = ', '.join(counties[:3])
            if len(counties) > 3:
                county_str += f" +{len(counties)-3} more"

            print(f"{str(coord):<30} {len(addresses):<10} {county_str}")

    print()

    # Out of Bounds
    print("="*70)
    print("OUT OF BOUNDS COORDINATES")
    print("="*70)
    print(f"Properties outside Ireland: {len(out_of_bounds):,}")

    if out_of_bounds:
        print("\nSample out-of-bounds properties:")
        for prop in out_of_bounds[:5]:
            print(f"  {prop['name'][:50]}")
            print(f"    County: {prop['county']}, Coords: ({prop['lat']:.6f}, {prop['lon']:.6f})")

    print()

    # County Validation
    print("="*70)
    print("COUNTY BOUNDARY VALIDATION")
    print("="*70)
    print(f"Properties in wrong county: {len(county_mismatches):,}")

    if county_mismatches:
        print(f"  Percentage: {100*len(county_mismatches)/total_records:.2f}%")
        print("\nSample county mismatches:")
        for prop in county_mismatches[:10]:
            print(f"  {prop['name'][:50]}")
            print(f"    Expected: {prop['county']}")
            print(f"    {prop['reason']}")

    print()

    # Precision Patterns
    print("="*70)
    print("COORDINATE PRECISION")
    print("="*70)
    print("Top precision patterns (lat decimals, lon decimals):")
    for pattern, count in precision_patterns.most_common(10):
        pct = 100 * count / total_records
        print(f"  {pattern}: {count:,} records ({pct:.1f}%)")

    print()

    # Geographic Distribution
    print("="*70)
    print("GEOGRAPHIC DISTRIBUTION")
    print("="*70)
    print("Top 10 counties by record count:")
    for county, count in sorted(county_stats.items(),
                                key=lambda x: x[1],
                                reverse=True)[:10]:
        pct = 100 * count / total_records
        print(f"  {county:<20} {count:>8,} ({pct:>5.1f}%)")

    print()

    # Comparison with Previous Results
    print("="*70)
    print("COMPARISON WITH NOMINATIM/MAPBOX GEOCODING")
    print("="*70)
    print()
    print("Previous geocoding issues:")
    print("  ✗ 172 HIGH priority centroids (100+ addresses per point)")
    print("  ✗ 5,287 MEDIUM priority centroids (10-99 addresses)")
    print("  ✗ 235,405 properties at centroid coordinates")
    print()
    print("Salesforce geocoding results:")
    print(f"  {'✓' if len(high_priority) < 50 else '⚠'} {len(high_priority):,} HIGH priority centroids")
    print(f"  {'✓' if len(medium_priority) < 200 else '⚠'} {len(medium_priority):,} MEDIUM priority centroids")
    print(f"  {'✓' if len(out_of_bounds) == 0 else '✗'} {len(out_of_bounds):,} out-of-bounds coordinates")
    print(f"  {'✓' if len(county_mismatches) < 1000 else '⚠'} {len(county_mismatches):,} county boundary mismatches")
    print()

    # Quality Score
    issues = 0
    if len(high_priority) >= 50:
        issues += 1
    if len(medium_priority) >= 200:
        issues += 1
    if len(out_of_bounds) > 0:
        issues += 1
    if len(county_mismatches) > total_records * 0.01:  # >1% mismatch
        issues += 1

    if issues == 0:
        status = "🟢 EXCELLENT"
        message = "Very few issues detected"
    elif issues == 1:
        status = "🟡 GOOD"
        message = "Minor issues detected"
    elif issues == 2:
        status = "🟠 FAIR"
        message = "Some issues need attention"
    else:
        status = "🔴 NEEDS ATTENTION"
        message = "Multiple quality issues found"

    print("="*70)
    print("OVERALL QUALITY ASSESSMENT")
    print("="*70)
    print(f"Status: {status}")
    print(f"Assessment: {message}")
    print()

    if len(high_priority) > 0:
        print("⚠ Recommendation: Review high-priority centroid coordinates")
    if len(county_mismatches) > 0:
        print(f"⚠ Note: {len(county_mismatches):,} properties may have incorrect coordinates")

    print()
    print("="*70)
    print("DETAILED ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    try:
        analyze_geocoding_quality()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
