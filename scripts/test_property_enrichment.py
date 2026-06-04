#!/usr/bin/env python3
"""
Test property data enrichment by searching recent sales on property websites.
Checks Daft.ie and MyHome.ie for property details like bedrooms, type, etc.
"""

import os
import psycopg2
import requests
import time
from dotenv import load_dotenv
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def search_daft(address, county):
    """Search Daft.ie for property details."""
    try:
        # Daft search URL
        search_query = f"{address}, {county}"
        encoded_query = quote_plus(search_query)
        url = f"https://www.daft.ie/property-for-sale/ireland?searchSource=sale&query={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for property listings
            # Daft typically shows results with class names like 'SearchPage__Result'
            listings = soup.find_all('div', {'data-testid': 'result'})

            if listings:
                # Try to extract info from first result
                first = listings[0]

                # Look for bedroom count
                beds_text = first.find(text=lambda t: t and 'bed' in t.lower())

                # Look for property type
                type_text = first.find(text=lambda t: t and any(w in t.lower() for w in ['house', 'apartment', 'flat', 'terraced', 'detached', 'semi-detached']))

                return {
                    'found': True,
                    'source': 'daft',
                    'beds': beds_text if beds_text else None,
                    'property_type': type_text if type_text else None,
                    'url': url
                }

            return {'found': False, 'source': 'daft', 'reason': 'No listings found'}

    except Exception as e:
        return {'found': False, 'source': 'daft', 'error': str(e)}

    return None

def search_myhome(address, county):
    """Search MyHome.ie for property details."""
    try:
        # MyHome search URL
        search_query = f"{address}, {county}"
        encoded_query = quote_plus(search_query)
        url = f"https://www.myhome.ie/residential/ireland/property-for-sale?searchTerm={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for property cards
            cards = soup.find_all('div', class_=lambda c: c and 'PropertyCard' in c)

            if cards:
                first = cards[0]

                # Look for bedroom count
                beds = first.find(text=lambda t: t and 'bed' in t.lower())

                # Look for property type
                prop_type = first.find(text=lambda t: t and any(w in t.lower() for w in ['house', 'apartment', 'flat', 'terraced', 'detached']))

                return {
                    'found': True,
                    'source': 'myhome',
                    'beds': beds if beds else None,
                    'property_type': prop_type if prop_type else None,
                    'url': url
                }

            return {'found': False, 'source': 'myhome', 'reason': 'No listings found'}

    except Exception as e:
        return {'found': False, 'source': 'myhome', 'error': str(e)}

    return None

def google_search_property(address, county):
    """Try Google search to find property info."""
    try:
        # Use DuckDuckGo instead (no API key needed)
        search_query = f"{address} {county} Ireland bedrooms"
        encoded_query = quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for property-related snippets
            snippets = soup.find_all('a', class_='result__snippet')

            found_beds = None
            found_type = None

            for snippet in snippets[:3]:
                text = snippet.get_text().lower()

                # Look for bedroom mentions
                if 'bed' in text and not found_beds:
                    # Extract bedroom count (e.g., "3 bed", "2 bedroom")
                    import re
                    match = re.search(r'(\d+)\s*bed', text)
                    if match:
                        found_beds = f"{match.group(1)} bed"

                # Look for property type
                if not found_type:
                    for ptype in ['house', 'apartment', 'flat', 'terrace', 'detached', 'semi-detached']:
                        if ptype in text:
                            found_type = ptype
                            break

            if found_beds or found_type:
                return {
                    'found': True,
                    'source': 'google',
                    'beds': found_beds,
                    'property_type': found_type
                }

            return {'found': False, 'source': 'google', 'reason': 'No property info in search results'}

    except Exception as e:
        return {'found': False, 'source': 'google', 'error': str(e)}

    return None

def main():
    print("="*80)
    print("TESTING PROPERTY DATA ENRICHMENT")
    print("="*80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get 20 recent properties from last 3 months
    print("Fetching 20 recent properties (last 3 months)...")
    cur.execute("""
        SELECT id, address, county, price, sale_date
        FROM properties
        WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
        AND address IS NOT NULL
        AND county IS NOT NULL
        ORDER BY sale_date DESC, price DESC
        LIMIT 20
    """)

    recent = cur.fetchall()
    print(f"Found {len(recent)} recent properties")
    print()

    results = []

    for i, (prop_id, address, county, price, sale_date) in enumerate(recent, 1):
        print(f"{i}. {address[:60]}")
        print(f"   County: {county}, Price: €{price:,.0f}, Sold: {sale_date}")

        property_result = {
            'id': prop_id,
            'address': address,
            'county': county,
            'price': price,
            'sale_date': str(sale_date),
            'searches': []
        }

        # Try Daft
        print(f"   Searching Daft.ie...", end=' ')
        daft_result = search_daft(address, county)
        if daft_result:
            property_result['searches'].append(daft_result)
            if daft_result.get('found'):
                print(f"✅ FOUND - Beds: {daft_result.get('beds')}, Type: {daft_result.get('property_type')}")
            else:
                print(f"❌ Not found - {daft_result.get('reason', daft_result.get('error', 'Unknown'))}")
        else:
            print("❌ Failed")

        time.sleep(2)  # Rate limiting

        # Try MyHome
        print(f"   Searching MyHome.ie...", end=' ')
        myhome_result = search_myhome(address, county)
        if myhome_result:
            property_result['searches'].append(myhome_result)
            if myhome_result.get('found'):
                print(f"✅ FOUND - Beds: {myhome_result.get('beds')}, Type: {myhome_result.get('property_type')}")
            else:
                print(f"❌ Not found - {myhome_result.get('reason', myhome_result.get('error', 'Unknown'))}")
        else:
            print("❌ Failed")

        time.sleep(2)  # Rate limiting

        # Try Google/DuckDuckGo
        print(f"   Searching web...", end=' ')
        google_result = google_search_property(address, county)
        if google_result:
            property_result['searches'].append(google_result)
            if google_result.get('found'):
                print(f"✅ FOUND - Beds: {google_result.get('beds')}, Type: {google_result.get('property_type')}")
            else:
                print(f"❌ Not found - {google_result.get('reason', google_result.get('error', 'Unknown'))}")
        else:
            print("❌ Failed")

        results.append(property_result)
        print()

        time.sleep(2)  # Rate limiting between properties

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    found_any = [r for r in results if any(s.get('found') for s in r['searches'])]
    found_daft = [r for r in results if any(s.get('found') and s['source']=='daft' for s in r['searches'])]
    found_myhome = [r for r in results if any(s.get('found') and s['source']=='myhome' for s in r['searches'])]
    found_google = [r for r in results if any(s.get('found') and s['source']=='google' for s in r['searches'])]

    print(f"Properties with data found: {len(found_any)}/{len(results)} ({100*len(found_any)/len(results):.1f}%)")
    print()
    print(f"Success by source:")
    print(f"  Daft.ie: {len(found_daft)}/{len(results)} ({100*len(found_daft)/len(results):.1f}%)")
    print(f"  MyHome.ie: {len(found_myhome)}/{len(results)} ({100*len(found_myhome)/len(results):.1f}%)")
    print(f"  Web search: {len(found_google)}/{len(results)} ({100*len(found_google)/len(results):.1f}%)")
    print()

    # Show what data we found
    if found_any:
        print("Sample enriched data:")
        for r in found_any[:5]:
            print(f"  {r['address'][:50]}")
            for search in r['searches']:
                if search.get('found'):
                    print(f"    {search['source']}: {search.get('beds', 'N/A')} | {search.get('property_type', 'N/A')}")

    conn.close()

if __name__ == "__main__":
    main()
