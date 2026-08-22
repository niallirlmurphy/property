#!/usr/bin/env python3
"""
Multi-source enrichment with low-volume batching and pauses.
Uses Google → Daft.ie → MyHome.ie cascade with batch delays to avoid blocking.

Strategy:
- Process in small batches (50-100 properties)
- 3-5 minute pause between batches
- Spreads load across all three sources
- Avoids triggering rate limits

Usage:
    python3 scripts/enrich_multi_batch.py --months 3 --batch-size 50 --batch-delay 180
"""

import os
import sys
import psycopg2
import requests
import time
import re
from dotenv import load_dotenv
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from datetime import datetime

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from canonical_geocoding import (
    initialize_cache,
    should_enrich,
    cache_enrichment_data
)

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Source statistics tracking
stats = {
    'google': {'attempts': 0, 'success': 0},
    'daft': {'attempts': 0, 'success': 0},
    'myhome': {'attempts': 0, 'success': 0},
    'total': {'attempts': 0, 'success': 0}
}

def extract_bedrooms(text):
    """Extract bedroom count from text."""
    if not text:
        return None

    text = text.lower()

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
    if bedrooms and not (1 <= bedrooms <= 10):
        bedrooms = None

    valid_types = ['house', 'apartment', 'terraced', 'detached',
                   'semi-detached', 'duplex', 'bungalow', 'cottage']
    if property_type and property_type not in valid_types:
        property_type = None

    return bedrooms, property_type

def search_google(address, county):
    """Search Google for property details."""
    try:
        # Simplified query for better success with low volume
        search_query = f'"{address}" {county} Ireland property bedrooms'
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

def search_daft(address, county):
    """Search Daft.ie directly."""
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
    """Search MyHome.ie directly."""
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

def cascade_search(address, county):
    """
    Try all three sources with delays.
    Low volume per batch avoids triggering blocks.
    """
    sources = [
        ('google', search_google, 4),    # 4s delay
        ('daft', search_daft, 5),        # 5s delay
        ('myhome', search_myhome, 5),    # 5s delay
    ]

    for i, (source_name, search_func, delay) in enumerate(sources):
        stats[source_name]['attempts'] += 1
        result = search_func(address, county)

        if result.get('success'):
            result['source'] = source_name
            stats[source_name]['success'] += 1
            return result

        if result.get('skip_source'):
            print(f"   ⚠️  {source_name} blocked/rate-limited", flush=True)
            # Don't break - try other sources

        # Rate limiting between sources
        if i < len(sources) - 1:
            time.sleep(delay)

    return {'success': False, 'reason': 'all_sources_failed'}

def enrich_batch(properties, batch_num, total_batches, dry_run=False):
    """Enrich a single batch of properties."""
    print(f"\n{'='*80}", flush=True)
    print(f"BATCH {batch_num}/{total_batches} - {len(properties)} properties | {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print(f"{'='*80}", flush=True)

    successful = 0
    updates = []
    start_time = time.time()

    for i, (prop_id, address, county, price, sale_date) in enumerate(properties, 1):
        stats['total']['attempts'] += 1
        result = cascade_search(address, county)

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

            if i <= 3:  # Show first 3 of each batch
                beds_str = f"{result['bedrooms']} bed" if result['bedrooms'] else "N/A"
                type_str = result['property_type'] or "N/A"
                source = result.get('source', 'unknown')
                print(f"   ✅ [{source}] {address[:45]:<45} → {beds_str}, {type_str}", flush=True)

        # Progress every 10 properties
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(properties)} ({100*i/len(properties):.0f}%) | Success: {successful} ({100*successful/i:.0f}%)", flush=True)

    elapsed = time.time() - start_time

    print(f"\n   Batch complete in {elapsed/60:.1f} minutes", flush=True)
    print(f"   Success: {successful}/{len(properties)} ({100*successful/len(properties):.1f}%)", flush=True)

    # Update database
    if not dry_run and updates:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        try:
            for prop_id, bedrooms, property_type, source, address in updates:
                cur.execute("""
                    UPDATE properties
                    SET bedrooms = %s, property_type = %s
                    WHERE id = %s
                """, (bedrooms, property_type, prop_id))
            conn.commit()
            print(f"   ✅ Database updated with {len(updates)} properties", flush=True)
        finally:
            conn.close()

    return successful, len(properties) - successful

def enrich_properties(months=3, batch_size=50, batch_delay=180, dry_run=False):
    """
    Enrich properties in small batches with pauses.

    Default: 50 properties per batch, 3 minute pause between batches.
    This keeps volume low per source and avoids triggering blocks.
    """
    print("="*80, flush=True)
    print("LOW-VOLUME BATCHED ENRICHMENT (Google → Daft → MyHome)", flush=True)
    print("="*80, flush=True)
    print(f"Batch size: {batch_size} properties", flush=True)
    print(f"Batch delay: {batch_delay} seconds ({batch_delay/60:.1f} minutes)", flush=True)
    if dry_run:
        print("DRY RUN MODE - No database updates", flush=True)
    print(flush=True)

    # Initialize canonical cache
    print("Initializing canonical enrichment cache...", flush=True)
    initialize_cache(DATABASE_URL)
    print("Cache initialized\n", flush=True)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        print(f"Finding recent properties (last {months} months)...", flush=True)

        query = f"""
            SELECT id, address, county, price, sale_date
            FROM properties
            WHERE sale_date >= CURRENT_DATE - INTERVAL '{months} months'
            AND address IS NOT NULL
            AND county IS NOT NULL
            AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY sale_date DESC, price DESC
        """

        cur.execute(query)
        all_properties = cur.fetchall()

        print(f"Found {len(all_properties):,} properties to enrich", flush=True)
        print(flush=True)

        if len(all_properties) == 0:
            print("No properties need enrichment.", flush=True)
            return

        # Split into batches
        batches = [all_properties[i:i+batch_size] for i in range(0, len(all_properties), batch_size)]
        total_batches = len(batches)

        print(f"Processing in {total_batches} batches...", flush=True)
        est_time = (total_batches * batch_delay / 60) + (len(all_properties) * 14 / 60)  # 14s avg per property
        print(f"Estimated time: {est_time/60:.1f} hours", flush=True)
        print(flush=True)

        total_successful = 0
        total_failed = 0

        for batch_num, batch in enumerate(batches, 1):
            successful, failed = enrich_batch(batch, batch_num, total_batches, dry_run=dry_run)
            total_successful += successful
            total_failed += failed

            # Delay between batches (except after last batch)
            if batch_num < total_batches:
                next_batch_time = datetime.now()
                next_batch_time = next_batch_time.replace(second=0, microsecond=0)
                mins_to_add = batch_delay // 60
                print(f"\n   ⏸️  Pausing {batch_delay}s ({batch_delay/60:.0f} min) before batch {batch_num+1}...", flush=True)
                print(f"   Next batch at approximately {(datetime.now()).strftime('%H:%M')}", flush=True)
                time.sleep(batch_delay)

        # Final summary
        print(f"\n{'='*80}", flush=True)
        print("FINAL SUMMARY", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Total processed: {len(all_properties):,}", flush=True)
        print(f"Successful: {total_successful:,} ({100*total_successful/len(all_properties):.1f}%)", flush=True)
        print(f"Failed: {total_failed:,} ({100*total_failed/len(all_properties):.1f}%)", flush=True)
        print(flush=True)

        print("Success by source:", flush=True)
        for source in ['google', 'daft', 'myhome']:
            attempts = stats[source]['attempts']
            success = stats[source]['success']
            if attempts > 0:
                print(f"  {source.capitalize():10} {success:4}/{attempts:4} ({100*success/attempts:.1f}%)", flush=True)

    finally:
        conn.close()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--months', type=float, default=3)
    parser.add_argument('--batch-size', type=int, default=50, help='Properties per batch (default: 50)')
    parser.add_argument('--batch-delay', type=int, default=180, help='Seconds between batches (default: 180 = 3min)')
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()
    enrich_properties(
        months=args.months,
        batch_size=args.batch_size,
        batch_delay=args.batch_delay,
        dry_run=args.dry_run
    )
