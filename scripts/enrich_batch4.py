#!/usr/bin/env python3
"""
Batch 4 enrichment - 5,000 properties targeting May/June 2026 first.

Priorities:
1. May/June 2026 properties (newest imports)
2. 2025 properties (high-value backfill)
3. Jan-Apr 2026 (fill early 2026 gap)

Target: >75% success rate
"""

import os
import psycopg2
import psycopg2.extras
import requests
import time
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Statistics tracking
stats = {
    'processed': 0,
    'success': 0,
    'failed': 0,
    'bedrooms_found': 0,
    'property_type_found': 0,
    'both_found': 0,
    'start_time': datetime.now()
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

    # Priority order
    type_keywords = [
        ('semi-detached', ['semi-detached', 'semi detached', 'semidetached']),
        ('detached', ['detached']),
        ('terraced', ['terraced', 'terrace']),
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

def search_duckduckgo(address, county):
    """Search DuckDuckGo for property details."""
    try:
        search_query = f"{address} {county} Ireland property"
        encoded_query = quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__snippet')
            combined_text = ' '.join([r.get_text() for r in results[:3]])

            if combined_text:
                bedrooms = extract_bedrooms(combined_text)
                property_type = extract_property_type(combined_text)

                return bedrooms, property_type

        return None, None

    except Exception as e:
        print(f"  Search error: {e}")
        return None, None

def enrich_property(prop_id, address, county):
    """Enrich a single property."""
    # Search for property details
    bedrooms, property_type = search_duckduckgo(address, county)

    # Track statistics
    stats['processed'] += 1

    if bedrooms:
        stats['bedrooms_found'] += 1
    if property_type:
        stats['property_type_found'] += 1
    if bedrooms and property_type:
        stats['both_found'] += 1

    if bedrooms or property_type:
        stats['success'] += 1
        return {
            'id': prop_id,
            'bedrooms': bedrooms,
            'property_type': property_type,
            'success': True
        }
    else:
        stats['failed'] += 1
        return {
            'id': prop_id,
            'bedrooms': None,
            'property_type': None,
            'success': False
        }

def print_stats():
    """Print current statistics."""
    if stats['processed'] == 0:
        return

    success_rate = stats['success'] / stats['processed'] * 100
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    rate = stats['processed'] / elapsed if elapsed > 0 else 0

    print(f"\n=== BATCH 4 STATISTICS ===")
    print(f"Processed: {stats['processed']:,}")
    print(f"Success: {stats['success']:,} ({success_rate:.1f}%)")
    print(f"Failed: {stats['failed']:,}")
    print(f"With bedrooms: {stats['bedrooms_found']:,}")
    print(f"With property_type: {stats['property_type_found']:,}")
    print(f"With both: {stats['both_found']:,}")
    print(f"Rate: {rate:.1f} properties/sec")
    print(f"Elapsed: {elapsed:.0f}s")

def main():
    print("=== BATCH 4 ENRICHMENT ===")
    print(f"Target: 5,000 properties")
    print(f"Goal: >75% success rate")
    print()

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get properties to enrich (prioritized)
    print("Fetching properties to enrich...")
    cur.execute("""
        -- Priority 1: May/June 2026 (newest imports)
        (
            SELECT id, address, county, sale_date, price
            FROM properties
            WHERE sale_date >= '2026-05-01'
              AND sale_date < '2026-07-01'
              AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY price DESC
            LIMIT 1500
        )
        UNION ALL
        -- Priority 2: 2025 high-value (>300k)
        (
            SELECT id, address, county, sale_date, price
            FROM properties
            WHERE EXTRACT(YEAR FROM sale_date) = 2025
              AND price >= 300000
              AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY price DESC, sale_date DESC
            LIMIT 2000
        )
        UNION ALL
        -- Priority 3: Jan-Apr 2026
        (
            SELECT id, address, county, sale_date, price
            FROM properties
            WHERE sale_date >= '2026-01-01'
              AND sale_date < '2026-05-01'
              AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY price DESC
            LIMIT 1500
        )
        LIMIT 5000
    """)

    properties = cur.fetchall()
    print(f"Loaded {len(properties):,} properties")
    print()

    # Result/input files live under logs/enrichment_results/ (resolved relative
    # to the project root so it works from any working directory)
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'logs', 'enrichment_results'
    )
    os.makedirs(results_dir, exist_ok=True)

    # Save to input file for resumability
    input_file = os.path.join(results_dir, f"enrichment_batch4_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(input_file, 'w') as f:
        json.dump([dict(p) for p in properties], f, indent=2, default=str)
    print(f"Saved input to: {input_file}")
    print()

    # Enrich properties
    results = []
    output_file = os.path.join(results_dir, f"enrichment_batch4_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    print("Starting enrichment...")
    print("(Progress updates every 100 properties)")
    print()

    for i, prop in enumerate(properties, 1):
        # Rate limiting: 10 seconds between requests
        if i > 1:
            time.sleep(10)

        result = enrich_property(prop['id'], prop['address'], prop['county'])
        results.append(result)

        # Progress updates
        if i % 100 == 0:
            print(f"Processed {i:,} / {len(properties):,}")
            print_stats()

            # Save intermediate results
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            # Check success rate
            current_success_rate = stats['success'] / stats['processed'] * 100
            if i >= 500 and current_success_rate < 75:
                print(f"\n⚠️  WARNING: Success rate ({current_success_rate:.1f}%) below 75% target!")
                print("Continuing...")
            print()

    # Final save
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Final statistics
    print()
    print("="*60)
    print_stats()
    print()
    print(f"✓ Results saved to: {output_file}")
    print()

    # Success rate check
    final_success_rate = stats['success'] / stats['processed'] * 100
    if final_success_rate >= 75:
        print(f"✓ SUCCESS: {final_success_rate:.1f}% success rate (target: >75%)")
    else:
        print(f"⚠️  WARNING: {final_success_rate:.1f}% success rate (target: >75%)")

    print()
    print("Next step: Import results to database")
    print(f"  python3 scripts/import_enrichment_results.py {output_file}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
