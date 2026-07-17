#!/usr/bin/env python3
"""
Offline batch enrichment - no database required.
Reads property list from CSV/JSON, enriches via Google/Daft/MyHome, saves to local file.

This version works without database connectivity:
- Input: CSV file with properties to enrich
- Output: JSON file with enrichment results
- You can manually upload results to database later

Usage:
    # Create input file from database (when you have connectivity):
    python3 -c "
    import psycopg2, json, os
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute('''
        SELECT id, address, county, price
        FROM properties
        WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
          AND (bedrooms IS NULL OR property_type IS NULL)
          AND price > 200000
        ORDER BY price DESC, sale_date DESC
        LIMIT 500
    ''')
    props = [{'id': r[0], 'address': r[1], 'county': r[2], 'price': r[3]} for r in cur.fetchall()]
    with open('enrichment_input.json', 'w') as f:
        json.dump(props, f, indent=2)
    print(f'Exported {len(props)} properties to enrichment_input.json')
    conn.close()
    "

    # Then run offline enrichment:
    python3 scripts/enrich_offline_batch.py --input enrichment_input.json --batch-size 50 --batch-delay 180

    # Results saved to: enrichment_results_TIMESTAMP.json
"""

import os
import json
import requests
import time
import re
import argparse
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

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
        url = f'https://www.google.com/search?q={quote_plus(search_query)}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        stats['google']['attempts'] += 1
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text().lower()

            bedrooms = extract_bedrooms(text)
            property_type = extract_property_type(text)

            if bedrooms or property_type:
                stats['google']['success'] += 1
                return bedrooms, property_type, 'google'

        return None, None, None

    except Exception as e:
        print(f"  ⚠️  Google error: {e}")
        return None, None, None

def search_daft(address, county):
    """Search Daft.ie for property details."""
    try:
        search_query = f'{address} {county}'
        url = f'https://www.daft.ie/property-for-sale/ireland?searchSource=sale&query={quote_plus(search_query)}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        stats['daft']['attempts'] += 1
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text().lower()

            bedrooms = extract_bedrooms(text)
            property_type = extract_property_type(text)

            if bedrooms or property_type:
                stats['daft']['success'] += 1
                return bedrooms, property_type, 'daft'

        return None, None, None

    except Exception as e:
        print(f"  ⚠️  Daft error: {e}")
        return None, None, None

def search_myhome(address, county):
    """Search MyHome.ie for property details."""
    try:
        search_query = f'{address} {county}'
        url = f'https://www.myhome.ie/residential/ireland/property-for-sale?search={quote_plus(search_query)}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        stats['myhome']['attempts'] += 1
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text().lower()

            bedrooms = extract_bedrooms(text)
            property_type = extract_property_type(text)

            if bedrooms or property_type:
                stats['myhome']['success'] += 1
                return bedrooms, property_type, 'myhome'

        return None, None, None

    except Exception as e:
        print(f"  ⚠️  MyHome error: {e}")
        return None, None, None

def enrich_property(prop):
    """
    Try to enrich property from multiple sources in cascade.
    Returns dict with enrichment results.
    """
    address = prop['address']
    county = prop['county']
    prop_id = prop['id']

    bedrooms = None
    property_type = None
    source = None

    # Try Google first
    bedrooms, property_type, source = search_google(address, county)
    time.sleep(4)  # Rate limit

    # If unsuccessful, try Daft
    if not (bedrooms or property_type):
        bedrooms, property_type, source = search_daft(address, county)
        time.sleep(4)

    # If still unsuccessful, try MyHome
    if not (bedrooms or property_type):
        bedrooms, property_type, source = search_myhome(address, county)
        time.sleep(4)

    # Validate data
    bedrooms, property_type = validate_enrichment_data(bedrooms, property_type)

    result = {
        'id': prop_id,
        'address': address,
        'county': county,
        'price': prop['price'],
        'bedrooms': bedrooms,
        'property_type': property_type,
        'source': source,
        'enriched_at': datetime.now().isoformat()
    }

    if bedrooms or property_type:
        stats['total']['success'] += 1
        stats['total']['attempts'] += 1
        return result, True
    else:
        stats['total']['attempts'] += 1
        return result, False

def process_batch(properties, batch_num, batch_size):
    """Process one batch of properties."""
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, len(properties))
    batch = properties[start_idx:end_idx]

    print(f"\n{'='*80}")
    print(f"BATCH {batch_num + 1}: Processing properties {start_idx + 1}-{end_idx}")
    print(f"{'='*80}")

    results = []
    success_count = 0

    for i, prop in enumerate(batch, 1):
        print(f"\n[{start_idx + i}/{len(properties)}] {prop['address']}, {prop['county']} (€{prop['price']:,})")

        result, success = enrich_property(prop)
        results.append(result)

        if success:
            success_count += 1
            parts = []
            if result['bedrooms']:
                parts.append(f"{result['bedrooms']} bed")
            if result['property_type']:
                parts.append(result['property_type'])
            print(f"  ✅ Found: {', '.join(parts)} (via {result['source']})")
        else:
            print(f"  ❌ No data found")

    print(f"\n{'='*80}")
    print(f"Batch {batch_num + 1} complete: {success_count}/{len(batch)} enriched")
    print(f"{'='*80}")

    return results

def print_stats():
    """Print enrichment statistics."""
    print(f"\n{'='*80}")
    print("SOURCE STATISTICS")
    print(f"{'='*80}")

    for source in ['google', 'daft', 'myhome']:
        attempts = stats[source]['attempts']
        success = stats[source]['success']
        rate = (success / attempts * 100) if attempts > 0 else 0
        print(f"{source.upper():10} - Attempts: {attempts:4}, Success: {success:4} ({rate:.1f}%)")

    total_attempts = stats['total']['attempts']
    total_success = stats['total']['success']
    total_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0

    print(f"\n{'TOTAL':10} - Attempts: {total_attempts:4}, Success: {total_success:4} ({total_rate:.1f}%)")
    print(f"{'='*80}")

def main():
    parser = argparse.ArgumentParser(description='Offline batch enrichment')
    parser.add_argument('--input', default='enrichment_input.json',
                       help='Input JSON file with properties to enrich')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Properties per batch (default: 50)')
    parser.add_argument('--batch-delay', type=int, default=180,
                       help='Seconds to wait between batches (default: 180)')
    parser.add_argument('--limit', type=int, help='Limit total properties to process')

    args = parser.parse_args()

    # Load input properties
    try:
        with open(args.input, 'r') as f:
            properties = json.load(f)
        print(f"✅ Loaded {len(properties)} properties from {args.input}")
    except FileNotFoundError:
        print(f"❌ Input file not found: {args.input}")
        print("\nTo create input file (requires database access):")
        print("  1. Ensure DATABASE_URL is set in backend/.env")
        print("  2. Run the SQL export command from the script header")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {args.input}: {e}")
        return

    if args.limit:
        properties = properties[:args.limit]
        print(f"⚠️  Limited to first {len(properties)} properties")

    # Calculate batches
    num_batches = (len(properties) + args.batch_size - 1) // args.batch_size

    print(f"\n{'='*80}")
    print(f"OFFLINE BATCH ENRICHMENT")
    print(f"{'='*80}")
    print(f"Properties: {len(properties)}")
    print(f"Batch size: {args.batch_size}")
    print(f"Batches: {num_batches}")
    print(f"Delay between batches: {args.batch_delay}s ({args.batch_delay//60}m {args.batch_delay%60}s)")

    # Estimate time
    time_per_property = 15  # ~15 seconds per property (4s × 3 sources + overhead)
    time_per_batch = args.batch_size * time_per_property + args.batch_delay
    total_seconds = num_batches * time_per_batch
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    print(f"Estimated time: {hours}h {minutes}m")
    print(f"{'='*80}")

    # Process all batches
    all_results = []
    start_time = time.time()

    for batch_num in range(num_batches):
        batch_results = process_batch(properties, batch_num, args.batch_size)
        all_results.extend(batch_results)

        # Save intermediate results after each batch, under logs/enrichment_results/
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'logs', 'enrichment_results'
        )
        os.makedirs(results_dir, exist_ok=True)
        output_file = os.path.join(results_dir, f"enrichment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        print(f"\n💾 Saved {len(all_results)} results to {output_file}")

        # Wait before next batch (except after last batch)
        if batch_num < num_batches - 1:
            print(f"\n⏸️  Waiting {args.batch_delay}s before next batch...")
            time.sleep(args.batch_delay)

    # Final statistics
    elapsed = time.time() - start_time
    print_stats()

    print(f"\n{'='*80}")
    print("ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Total properties: {len(properties)}")
    print(f"Successfully enriched: {stats['total']['success']}")
    print(f"Success rate: {stats['total']['success']/len(properties)*100:.1f}%")
    print(f"Time elapsed: {int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"\n📁 Results saved to: {output_file}")
    print(f"\n{'='*80}")
    print("TO UPLOAD RESULTS TO DATABASE:")
    print(f"{'='*80}")
    print("""
python3 -c "
import psycopg2, json, os
from dotenv import load_dotenv

load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

with open('{output_file}', 'r') as f:
    results = json.load(f)

updated = 0
for r in results:
    if r['bedrooms'] or r['property_type']:
        cur.execute('''
            UPDATE properties
            SET bedrooms = %s, property_type = %s
            WHERE id = %s
        ''', (r['bedrooms'], r['property_type'], r['id']))
        updated += 1

conn.commit()
print(f'✅ Updated {{updated}} properties in database')
conn.close()
"
""".replace('{output_file}', output_file))

if __name__ == '__main__':
    main()
