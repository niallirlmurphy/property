#!/usr/bin/env python3
"""
Alternative enrichment using PropertyPal.com (covers all of Ireland now) and improved search.
"""

import os
import psycopg2
import requests
import time
import re
from dotenv import load_dotenv
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def extract_bedrooms(text):
    """Extract bedroom count from text."""
    if not text:
        return None

    text = text.lower()

    # Look for patterns
    patterns = [
        r'(\d+)\s*bed',
        r'(\d+)\s*-\s*bed',
        r'(\d+)\s*br\b',
        r'(\d+)\s*bedroom'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            count = int(match.group(1))
            if 1 <= count <= 10:
                return count

    return None

def extract_property_type(text):
    """Extract property type from text."""
    if not text:
        return None

    text = text.lower()

    # Priority order (more specific first)
    type_keywords = [
        ('semi-detached', ['semi-detached', 'semi detached', 'semidetached']),
        ('detached', ['detached']),
        ('terraced', ['terraced', 'terrace', 'townhouse']),
        ('apartment', ['apartment', 'apt', 'flat']),
        ('duplex', ['duplex']),
        ('bungalow', ['bungalow']),
        ('cottage', ['cottage']),
        ('house', ['house'])
    ]

    for prop_type, keywords in type_keywords:
        if any(keyword in text for keyword in keywords):
            return prop_type

    return None

def search_google(address, county):
    """Search Google for property details."""
    try:
        # Build search query for sold property
        search_query = f'"{address}" {county} Ireland bedrooms property sold'
        encoded_query = quote_plus(search_query)
        url = f"https://www.google.com/search?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Extract text content
            text = response.text

            bedrooms = extract_bedrooms(text)
            property_type = extract_property_type(text)

            if bedrooms or property_type:
                return {
                    'success': True,
                    'bedrooms': bedrooms,
                    'property_type': property_type,
                    'source': 'google'
                }

        return {'success': False, 'reason': 'No data found'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def search_bing(address, county):
    """Search Bing for property details."""
    try:
        search_query = f'"{address}" {county} Ireland property bedrooms'
        encoded_query = quote_plus(search_query)
        url = f"https://www.bing.com/search?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            bedrooms = extract_bedrooms(response.text)
            property_type = extract_property_type(response.text)

            if bedrooms or property_type:
                return {
                    'success': True,
                    'bedrooms': bedrooms,
                    'property_type': property_type,
                    'source': 'bing'
                }

        return {'success': False, 'reason': 'No data found'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def enrich_properties(months=3, limit=None, dry_run=False):
    """Enrich recent properties with bedroom and type data."""
    print("="*80, flush=True)
    print("IMPROVED PROPERTY ENRICHMENT (Google + Bing)", flush=True)
    print("="*80, flush=True)
    print(flush=True)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        print(f"1. Finding recent properties (last {months} months)...", flush=True)

        query = f"""
            SELECT id, address, county, price, sale_date
            FROM properties
            WHERE sale_date >= CURRENT_DATE - INTERVAL '{months} months'
            AND address IS NOT NULL
            AND county IS NOT NULL
            AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY sale_date DESC, price DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        properties = cur.fetchall()

        print(f"   Found {len(properties):,} properties to enrich", flush=True)
        print(flush=True)

        if len(properties) == 0:
            print("No properties need enrichment.", flush=True)
            return

        if dry_run:
            print("DRY RUN MODE - No database updates will be made", flush=True)
            print(flush=True)

        print(f"2. Searching for property details...", flush=True)
        print(flush=True)

        successful = 0
        failed = 0
        updates = []

        for i, (prop_id, address, county, price, sale_date) in enumerate(properties, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(properties)} ({100*i/len(properties):.1f}%) | Success: {successful}", flush=True)

            # Try Google first
            result = search_google(address, county)

            # If Google fails, try Bing
            if not result['success']:
                time.sleep(2)  # Small delay between search engines
                result = search_bing(address, county)

            if result['success']:
                successful += 1
                updates.append((
                    prop_id,
                    result['bedrooms'],
                    result['property_type'],
                    address[:50]
                ))

                if i <= 5:
                    beds_str = f"{result['bedrooms']} bed" if result['bedrooms'] else "N/A"
                    type_str = result['property_type'] or "N/A"
                    source = result.get('source', 'unknown')
                    print(f"   ✅ [{source}] {address[:45]:<45} → {beds_str}, {type_str}", flush=True)
            else:
                failed += 1

            # Rate limiting - 3 seconds between properties
            time.sleep(3)

        print(f"   Progress: {len(properties)}/{len(properties)} (100.0%)", flush=True)
        print(flush=True)

        # Summary
        print("3. Summary:", flush=True)
        print(f"   Successful: {successful}/{len(properties)} ({100*successful/len(properties):.1f}%)", flush=True)
        print(f"   Failed: {failed}/{len(properties)} ({100*failed/len(properties):.1f}%)", flush=True)
        print(flush=True)

        if not dry_run and updates:
            print(f"4. Updating database with {len(updates):,} enriched properties...", flush=True)

            for prop_id, bedrooms, property_type, address in updates:
                cur.execute("""
                    UPDATE properties
                    SET
                        bedrooms = %s,
                        property_type = %s
                    WHERE id = %s
                """, (bedrooms, property_type, prop_id))

            conn.commit()
            print(f"   ✅ Updated {len(updates):,} properties", flush=True)

    finally:
        conn.close()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--months', type=int, default=3)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()
    enrich_properties(months=args.months, limit=args.limit, dry_run=args.dry_run)
