#!/usr/bin/env python3
"""
Test different geocoding methods on sample addresses.
Tries: Nominatim, web search hints, address enrichment.
"""

import os
import requests
import time
from dotenv import load_dotenv
import psycopg2

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def geocode_nominatim(address, county):
    """Try Nominatim geocoding."""
    try:
        # Add Ireland and county to improve results
        full_query = f"{address}, {county}, Ireland"

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': full_query,
            'format': 'json',
            'countrycodes': 'ie',
            'limit': 1
        }
        headers = {'User-Agent': 'HomeIQ.ie/1.0'}

        response = requests.get(url, params=params, headers=headers, timeout=5)
        time.sleep(1)  # Rate limit: 1 request per second

        if response.status_code == 200:
            results = response.json()
            if results:
                return {
                    'lat': float(results[0]['lat']),
                    'lon': float(results[0]['lon']),
                    'display_name': results[0].get('display_name', ''),
                    'method': 'nominatim'
                }
    except Exception as e:
        print(f"    Nominatim error: {e}")

    return None

def search_google_hint(address, county):
    """Search Google for address hints (returns search suggestions, not actual geocoding)."""
    try:
        # Use Google search to see if we can find a better address format
        query = f"{address}, {county}, Ireland"

        # Use DuckDuckGo instead (no API key needed, respects privacy)
        url = "https://duckduckgo.com/"
        params = {'q': query, 't': 'h_', 'ia': 'web'}
        headers = {'User-Agent': 'HomeIQ.ie/1.0'}

        response = requests.get(url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            # Look for common address patterns in results
            text = response.text.lower()

            # Check if we can find better address info
            if 'eircode' in text or 'google maps' in text:
                return {'hint': 'Found on web, may have more detail available', 'method': 'web_search'}

    except Exception as e:
        print(f"    Web search error: {e}")

    return None

def try_address_variations(address, county):
    """Try variations of the address that might geocode better."""
    variations = []

    # Remove common problematic prefixes
    if address.lower().startswith('no.') or address.lower().startswith('no '):
        cleaned = address[3:].strip() if address[2] == '.' else address[2:].strip()
        variations.append(cleaned)

    # Try with just the street/area name (remove unit numbers)
    if ',' in address:
        parts = [p.strip() for p in address.split(',')]
        if len(parts) > 1:
            # Try just the last part (often the area name)
            variations.append(f"{parts[-1]}, {county}, Ireland")
            # Try last two parts
            if len(parts) > 2:
                variations.append(f"{parts[-2]}, {parts[-1]}, {county}, Ireland")

    return variations

def main():
    print("="*80)
    print("TESTING GEOCODING METHODS ON SAMPLE ADDRESSES")
    print("="*80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get 20 diverse sample addresses
    print("Fetching 20 sample addresses from different counties...")
    cur.execute("""
        WITH ranked AS (
            SELECT
                id,
                address,
                county,
                ROW_NUMBER() OVER (PARTITION BY county ORDER BY RANDOM()) as rn
            FROM properties
            WHERE latitude IS NULL
            AND address IS NOT NULL
            AND county IS NOT NULL
        )
        SELECT id, address, county
        FROM ranked
        WHERE rn = 1
        LIMIT 20
    """)

    samples = cur.fetchall()
    print(f"Testing {len(samples)} addresses...")
    print()

    results = []

    for i, (prop_id, address, county) in enumerate(samples, 1):
        print(f"{i}. {address[:70]}")
        print(f"   County: {county}")

        # Try Nominatim first
        result = geocode_nominatim(address, county)

        if result:
            print(f"   ✅ FOUND via {result['method']}: ({result['lat']:.6f}, {result['lon']:.6f})")
            print(f"   Display: {result['display_name'][:70]}")
            results.append({
                'id': prop_id,
                'address': address,
                'county': county,
                'success': True,
                'method': result['method'],
                'lat': result['lat'],
                'lon': result['lon']
            })
        else:
            # Try address variations
            print(f"   ❌ Not found with full address, trying variations...")
            variations = try_address_variations(address, county)

            found = False
            for var in variations[:2]:  # Try max 2 variations to avoid rate limits
                print(f"      Trying: {var[:60]}")
                result = geocode_nominatim(var, county)
                if result:
                    print(f"      ✅ FOUND: ({result['lat']:.6f}, {result['lon']:.6f})")
                    results.append({
                        'id': prop_id,
                        'address': address,
                        'county': county,
                        'success': True,
                        'method': 'nominatim_variation',
                        'lat': result['lat'],
                        'lon': result['lon'],
                        'variation': var
                    })
                    found = True
                    break

            if not found:
                print(f"      ❌ No variations worked")
                results.append({
                    'id': prop_id,
                    'address': address,
                    'county': county,
                    'success': False,
                    'method': None
                })

        print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"✅ Successfully geocoded: {len(successful)}/{len(results)} ({100*len(successful)/len(results):.1f}%)")
    print(f"❌ Failed: {len(failed)}/{len(results)} ({100*len(failed)/len(results):.1f}%)")
    print()

    if successful:
        print("Methods that worked:")
        methods = {}
        for r in successful:
            method = r['method']
            methods[method] = methods.get(method, 0) + 1

        for method, count in methods.items():
            print(f"  - {method}: {count}")
        print()

    if failed:
        print("Failed addresses (sample):")
        for r in failed[:5]:
            print(f"  - {r['address'][:60]}, {r['county']}")

    conn.close()

if __name__ == "__main__":
    main()
