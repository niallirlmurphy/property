#!/usr/bin/env python3
"""
Multi-source property enrichment pipeline with cascade fallback.
Tries Google → Bing → Daft.ie → MyHome.ie until success.

Usage:
    python3 scripts/enrich_recent_properties_v2.py --months 3 --limit 100
    python3 scripts/enrich_recent_properties_v2.py --months 3 --limit 50 --dry-run
    python3 scripts/enrich_recent_properties_v2.py --test-source google --limit 5
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

# Source statistics tracking
stats = {
    'google': {'attempts': 0, 'success': 0},
    'bing': {'attempts': 0, 'success': 0},
    'daft': {'attempts': 0, 'success': 0},
    'myhome': {'attempts': 0, 'success': 0},
    'total': {'attempts': 0, 'success': 0}
}

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

def validate_enrichment_data(bedrooms, property_type):
    """Validate extracted data quality."""
    # Bedroom range check
    if bedrooms and not (1 <= bedrooms <= 10):
        bedrooms = None

    # Property type whitelist
    valid_types = ['house', 'apartment', 'terraced', 'detached',
                   'semi-detached', 'duplex', 'bungalow', 'cottage']
    if property_type and property_type not in valid_types:
        property_type = None

    return bedrooms, property_type

def search_google(address, county):
    """Search Google for property details with rich snippets."""
    try:
        # Build search query targeting Irish property sites
        search_query = f'"{address}" {county} Ireland bedrooms property site:(daft.ie OR myhome.ie OR sherryfitz.ie)'
        encoded_query = quote_plus(search_query)
        url = f"https://www.google.com/search?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            return {'success': False, 'skip_source': True, 'reason': 'rate_limited'}
        elif response.status_code in [403, 503]:
            return {'success': False, 'skip_source': True, 'reason': 'blocked'}
        elif response.status_code == 200:
            bedrooms = extract_bedrooms(response.text)
            property_type = extract_property_type(response.text)

            if bedrooms or property_type:
                bedrooms, property_type = validate_enrichment_data(bedrooms, property_type)
                if bedrooms or property_type:
                    return {
                        'success': True,
                        'bedrooms': bedrooms,
                        'property_type': property_type
                    }

        return {'success': False, 'reason': 'no_data_found'}

    except requests.Timeout:
        return {'success': False, 'reason': 'timeout'}
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

        if response.status_code == 429:
            return {'success': False, 'skip_source': True, 'reason': 'rate_limited'}
        elif response.status_code in [403, 503]:
            return {'success': False, 'skip_source': True, 'reason': 'blocked'}
        elif response.status_code == 200:
            bedrooms = extract_bedrooms(response.text)
            property_type = extract_property_type(response.text)

            if bedrooms or property_type:
                bedrooms, property_type = validate_enrichment_data(bedrooms, property_type)
                if bedrooms or property_type:
                    return {
                        'success': True,
                        'bedrooms': bedrooms,
                        'property_type': property_type
                    }

        return {'success': False, 'reason': 'no_data_found'}

    except requests.Timeout:
        return {'success': False, 'reason': 'timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def search_daft(address, county):
    """Search Daft.ie directly for property details."""
    try:
        search_query = f"{address}, {county}"
        encoded_query = quote_plus(search_query)
        url = f"https://www.daft.ie/property-for-sale/ireland?searchSource=sale&query={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            return {'success': False, 'skip_source': True, 'reason': 'rate_limited'}
        elif response.status_code in [403, 503]:
            return {'success': False, 'skip_source': True, 'reason': 'blocked'}
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('div', {'data-testid': 'result'})

            if listings:
                first = listings[0]
                full_text = first.get_text()

                bedrooms = extract_bedrooms(full_text)
                property_type = extract_property_type(full_text)

                if bedrooms or property_type:
                    bedrooms, property_type = validate_enrichment_data(bedrooms, property_type)
                    if bedrooms or property_type:
                        return {
                            'success': True,
                            'bedrooms': bedrooms,
                            'property_type': property_type
                        }

        return {'success': False, 'reason': 'no_listings_found'}

    except requests.Timeout:
        return {'success': False, 'reason': 'timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def search_myhome(address, county):
    """Search MyHome.ie directly for property details."""
    try:
        search_query = f"{address}, {county}"
        encoded_query = quote_plus(search_query)
        url = f"https://www.myhome.ie/residential/ireland/property-for-sale?searchTerm={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            return {'success': False, 'skip_source': True, 'reason': 'rate_limited'}
        elif response.status_code in [403, 503]:
            return {'success': False, 'skip_source': True, 'reason': 'blocked'}
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('div', class_=lambda c: c and 'PropertyCard' in c)

            if cards:
                first = cards[0]
                full_text = first.get_text()

                bedrooms = extract_bedrooms(full_text)
                property_type = extract_property_type(full_text)

                if bedrooms or property_type:
                    bedrooms, property_type = validate_enrichment_data(bedrooms, property_type)
                    if bedrooms or property_type:
                        return {
                            'success': True,
                            'bedrooms': bedrooms,
                            'property_type': property_type
                        }

        return {'success': False, 'reason': 'no_listings_found'}

    except requests.Timeout:
        return {'success': False, 'reason': 'timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def cascade_search(address, county, test_source=None):
    """
    Try multiple sources in priority order until success.
    Returns: {'success': bool, 'bedrooms': int, 'property_type': str, 'source': str}
    """
    sources = [
        ('google', search_google, 3),      # 3s delay
        ('bing', search_bing, 3),          # 3s delay
        ('daft', search_daft, 5),          # 5s delay (respectful)
        ('myhome', search_myhome, 5),      # 5s delay
    ]

    # If testing specific source
    if test_source:
        sources = [(name, func, delay) for name, func, delay in sources if name == test_source]

    for i, (source_name, search_func, delay) in enumerate(sources):
        stats[source_name]['attempts'] += 1
        result = search_func(address, county)

        if result.get('success'):
            result['source'] = source_name
            stats[source_name]['success'] += 1
            return result

        # Skip remaining sources if this one is blocked
        if result.get('skip_source'):
            break

        # Rate limiting between sources (except after last source)
        if i < len(sources) - 1:
            time.sleep(delay)

    return {'success': False, 'reason': 'all_sources_failed'}

def enrich_properties(months=3, limit=None, dry_run=False, test_source=None):
    """
    Enrich recent properties with bedroom and type data using multi-source cascade.

    Args:
        months: How many months back to search (default: 3)
        limit: Max properties to process (default: None = all)
        dry_run: If True, don't update database (default: False)
        test_source: Test specific source only (google, bing, daft, myhome)
    """
    print("="*80, flush=True)
    print("MULTI-SOURCE PROPERTY ENRICHMENT PIPELINE", flush=True)
    if test_source:
        print(f"TEST MODE: {test_source.upper()} only", flush=True)
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

        print(f"2. Enriching via cascade (Google → Bing → Daft → MyHome)...", flush=True)
        print(flush=True)

        successful = 0
        failed = 0
        updates = []

        start_time = time.time()

        for i, (prop_id, address, county, price, sale_date) in enumerate(properties, 1):
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(properties) - i) * avg_time
                print(f"   Progress: {i}/{len(properties)} ({100*i/len(properties):.1f}%) | Success: {successful} ({100*successful/i:.1f}%) | ETA: {remaining/60:.1f}min", flush=True)

            stats['total']['attempts'] += 1
            result = cascade_search(address, county, test_source=test_source)

            if result['success']:
                successful += 1
                stats['total']['success'] += 1
                updates.append((
                    prop_id,
                    result['bedrooms'],
                    result['property_type'],
                    result.get('source', 'unknown'),
                    address[:50]
                ))

                if i <= 5:
                    beds_str = f"{result['bedrooms']} bed" if result['bedrooms'] else "N/A"
                    type_str = result['property_type'] or "N/A"
                    source = result.get('source', 'unknown')
                    print(f"   ✅ [{source}] {address[:45]:<45} → {beds_str}, {type_str}", flush=True)
            else:
                failed += 1

        print(f"   Progress: {len(properties)}/{len(properties)} (100.0%)", flush=True)
        print(flush=True)

        # Summary
        print("3. Summary:", flush=True)
        print(f"   Total processed: {len(properties):,}", flush=True)
        print(f"   Successful: {successful}/{len(properties)} ({100*successful/len(properties):.1f}%)", flush=True)
        print(f"   Failed: {failed}/{len(properties)} ({100*failed/len(properties):.1f}%)", flush=True)
        print(flush=True)

        # Per-source statistics
        print("4. Success by source:", flush=True)
        for source in ['google', 'bing', 'daft', 'myhome']:
            attempts = stats[source]['attempts']
            success = stats[source]['success']
            if attempts > 0:
                print(f"   {source.capitalize():10} {success:3}/{attempts:3} ({100*success/attempts:.1f}%)", flush=True)
        print(flush=True)

        if not dry_run and updates:
            print(f"5. Updating database with {len(updates):,} enriched properties...", flush=True)

            for prop_id, bedrooms, property_type, source, address in updates:
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
    parser.add_argument('--months', type=float, default=3)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--test-source', choices=['google', 'bing', 'daft', 'myhome'], default=None,
                        help='Test specific source only')

    args = parser.parse_args()
    enrich_properties(months=args.months, limit=args.limit, dry_run=args.dry_run, test_source=args.test_source)
