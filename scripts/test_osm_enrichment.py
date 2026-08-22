#!/usr/bin/env python3
"""
Test OpenStreetMap enrichment for apartment complexes.

Tests OSM Overpass API to extract:
- Building name
- Number of floors/levels
- Apartment count (building:flats tag)
- Building type
- Address details
"""

import requests
import json
import time
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')


def query_osm_building(lat, lon, radius_m=50):
    """
    Query OSM for building data near coordinates.

    Args:
        lat, lon: Property coordinates
        radius_m: Search radius in meters

    Returns:
        dict with building data or None
    """
    overpass_url = 'https://overpass-api.de/api/interpreter'

    # Query for buildings with useful tags
    query = f'''
    [out:json][timeout:10];
    (
      way["building"](around:{radius_m},{lat},{lon});
      relation["building"](around:{radius_m},{lat},{lon});
    );
    out body;
    '''

    try:
        response = requests.post(
            overpass_url,
            data={'data': query},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])

            # Find closest building with most tags
            if elements:
                best_building = max(elements, key=lambda x: len(x.get('tags', {})))
                return best_building.get('tags', {})

        return None

    except Exception as e:
        print(f"OSM error: {e}")
        return None


def extract_enrichment_data(osm_tags):
    """Extract useful enrichment data from OSM tags."""
    if not osm_tags:
        return {}

    enrichment = {}

    # Building name (complex name for apartments)
    if 'name' in osm_tags:
        enrichment['complex_name'] = osm_tags['name']
    elif 'addr:housename' in osm_tags:
        enrichment['complex_name'] = osm_tags['addr:housename']

    # Number of floors
    if 'building:levels' in osm_tags:
        try:
            enrichment['floors'] = int(osm_tags['building:levels'])
        except:
            pass

    # Apartment count
    if 'building:flats' in osm_tags:
        try:
            enrichment['unit_count'] = int(osm_tags['building:flats'])
        except:
            pass

    # Building type
    if 'building' in osm_tags and osm_tags['building'] != 'yes':
        enrichment['building_type'] = osm_tags['building']

    # Year built
    if 'start_date' in osm_tags:
        enrichment['year_built'] = osm_tags['start_date']
    elif 'construction_date' in osm_tags:
        enrichment['year_built'] = osm_tags['construction_date']

    # All OSM tags for reference
    enrichment['osm_tags'] = osm_tags

    return enrichment


def test_sample_properties():
    """Test OSM enrichment on sample high-value properties."""

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get 10 high-value apartment sales with coordinates
    cur.execute("""
        SELECT
            id,
            address,
            county,
            price,
            latitude,
            longitude
        FROM properties
        WHERE latitude IS NOT NULL
        AND price > 10000000
        AND (
            address ILIKE '%apartment%' OR
            address ILIKE '%apt%' OR
            address ILIKE '%block%' OR
            address ILIKE '%complex%'
        )
        ORDER BY price DESC
        LIMIT 10
    """)

    properties = cur.fetchall()

    print("=" * 80)
    print("OSM ENRICHMENT TEST - High-Value Apartment Complexes")
    print("=" * 80)
    print()

    results = []

    for prop in properties:
        prop_id, address, county, price, lat, lon = prop

        print(f"Property {prop_id}: €{price:,.0f}")
        print(f"  Address: {address[:60]}")
        print(f"  Coords: ({lat:.4f}, {lon:.4f})")

        # Query OSM
        osm_tags = query_osm_building(lat, lon, radius_m=50)

        if osm_tags:
            enrichment = extract_enrichment_data(osm_tags)

            print(f"  ✓ OSM Data Found:")
            if 'complex_name' in enrichment:
                print(f"    - Complex: {enrichment['complex_name']}")
            if 'floors' in enrichment:
                print(f"    - Floors: {enrichment['floors']}")
            if 'unit_count' in enrichment:
                print(f"    - Units: {enrichment['unit_count']}")
            if 'building_type' in enrichment:
                print(f"    - Type: {enrichment['building_type']}")
            if 'year_built' in enrichment:
                print(f"    - Built: {enrichment['year_built']}")

            results.append({
                'property_id': prop_id,
                'price': price,
                'osm_found': True,
                'enrichment': enrichment
            })
        else:
            print(f"  ✗ No OSM data found")
            results.append({
                'property_id': prop_id,
                'price': price,
                'osm_found': False
            })

        print()
        time.sleep(1)  # Rate limiting

    conn.close()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    found = sum(1 for r in results if r['osm_found'])
    print(f"Properties tested: {len(results)}")
    print(f"OSM data found: {found} ({100*found/len(results):.0f}%)")
    print()

    # Data quality
    with_name = sum(1 for r in results if r.get('osm_found') and 'complex_name' in r.get('enrichment', {}))
    with_floors = sum(1 for r in results if r.get('osm_found') and 'floors' in r.get('enrichment', {}))
    with_units = sum(1 for r in results if r.get('osm_found') and 'unit_count' in r.get('enrichment', {}))

    if found > 0:
        print(f"Data completeness (of properties with OSM data):")
        print(f"  - Complex name: {with_name}/{found} ({100*with_name/found:.0f}%)")
        print(f"  - Floor count: {with_floors}/{found} ({100*with_floors/found:.0f}%)")
        print(f"  - Unit count: {with_units}/{found} ({100*with_units/found:.0f}%)")

    return results


if __name__ == '__main__':
    test_sample_properties()
