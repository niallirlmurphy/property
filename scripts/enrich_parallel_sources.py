#!/usr/bin/env python3
"""
Parallel multi-source property enrichment.

Assigns properties to sources in parallel:
- 5 sources = take 5 properties, assign 1 to each source
- Process all 5 simultaneously
- Long delay between batches lets all sources forget IP

Usage:
    python3 scripts/enrich_parallel_sources.py --input enrichment_batch4_input.csv --output enrichment_batch4.json --batch-delay 120
"""

import csv
import json
import requests
import time
import re
import argparse
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import concurrent.futures
from threading import Lock

# Source configuration and statistics
sources_config = {
    'duckduckgo': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
    },
    'google': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
    },
    'myhome': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
    },
    'daft': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
    },
    'propertyprice': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
    }
}

stats = {
    'total': {'processed': 0, 'enriched': 0, 'skipped': 0}
}

stats_lock = Lock()
MIN_SUCCESS_RATE = 75.0
MIN_ATTEMPTS_BEFORE_DISABLE = 20  # More attempts before disabling with parallel approach

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

def search_duckduckgo(address, county):
    """Search DuckDuckGo for property details."""
    query = f"{address} {county} property sale Ireland"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        return bedrooms, property_type

    except Exception as e:
        return None, None

def search_google(address, county):
    """Search Google for property details."""
    query = f"{address} {county} property Ireland"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        return bedrooms, property_type

    except Exception as e:
        return None, None

def search_myhome(address, county):
    """Search MyHome.ie for property details."""
    query = f"site:myhome.ie {address} {county}"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        return bedrooms, property_type

    except Exception as e:
        return None, None

def search_daft(address, county):
    """Search Daft.ie for property details."""
    query = f"site:daft.ie {address} {county}"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        return bedrooms, property_type

    except Exception as e:
        return None, None

def search_propertyprice(address, county):
    """Search PropertyPrice.ie for property details."""
    query = f"site:propertyprice.ie {address} {county}"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        return bedrooms, property_type

    except Exception as e:
        return None, None

# Map source names to functions
source_functions = {
    'duckduckgo': search_duckduckgo,
    'google': search_google,
    'myhome': search_myhome,
    'daft': search_daft,
    'propertyprice': search_propertyprice
}

def update_source_stats(source_name, found_data):
    """Update statistics for a source and check if it should be disabled."""
    with stats_lock:
        config = sources_config[source_name]
        config['attempts'] += 1

        if found_data:
            config['success'] += 1

        # Calculate success rate
        if config['attempts'] > 0:
            config['success_rate'] = (config['success'] / config['attempts']) * 100

        # Disable if below threshold (but only after minimum attempts)
        if config['attempts'] >= MIN_ATTEMPTS_BEFORE_DISABLE:
            if config['success_rate'] < MIN_SUCCESS_RATE:
                if config['enabled']:
                    config['enabled'] = False
                    print(f"\n⚠️  WARNING: Disabling {source_name} (success rate: {config['success_rate']:.1f}% < {MIN_SUCCESS_RATE}%)\n")

def enrich_with_source(prop, source_name):
    """Enrich a single property using a specific source."""
    address = prop.get('address') or prop.get('address_normalized', '')
    county = prop.get('county', '')
    prop_id = prop['id']

    # Check if already enriched
    if prop.get('bedrooms') or prop.get('property_type'):
        with stats_lock:
            stats['total']['skipped'] += 1
        return prop, source_name, True, True  # Already had data

    # Get the search function for this source
    search_func = source_functions[source_name]

    try:
        bedrooms, property_type = search_func(address, county)

        found_anything = bedrooms or property_type

        # Update property if found data
        if found_anything:
            prop['bedrooms'] = bedrooms
            prop['property_type'] = property_type
            prop['enrichment_source'] = source_name
            prop['enriched_at'] = datetime.now().isoformat()

        # Update stats
        update_source_stats(source_name, found_anything)

        with stats_lock:
            stats['total']['processed'] += 1
            if found_anything:
                stats['total']['enriched'] += 1

        return prop, source_name, found_anything, False

    except Exception as e:
        update_source_stats(source_name, False)
        with stats_lock:
            stats['total']['processed'] += 1
        return prop, source_name, False, False

def get_enabled_sources():
    """Get list of currently enabled source names."""
    return [name for name, cfg in sources_config.items() if cfg['enabled']]

def process_batch(properties_batch):
    """Process a batch of properties in parallel, one per source."""
    enabled_sources = get_enabled_sources()

    if not enabled_sources:
        print("⚠️  No enabled sources remaining!")
        return []

    # Take up to N properties where N = number of enabled sources
    batch_size = min(len(properties_batch), len(enabled_sources))
    props_to_process = properties_batch[:batch_size]

    # Assign each property to a different source
    assignments = list(zip(props_to_process, enabled_sources[:batch_size]))

    results = []

    # Process all assignments in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = [
            executor.submit(enrich_with_source, prop, source)
            for prop, source in assignments
        ]

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            prop, source, found, skipped = future.result()
            prop_id = prop['id']
            address = (prop.get('address') or prop.get('address_normalized', ''))[:40]

            if skipped:
                print(f"  [{i+1}/{batch_size}] #{prop_id} ({source:12}) ↷ Already enriched")
            elif found:
                bedrooms = prop.get('bedrooms', '?')
                prop_type = prop.get('property_type', '?')
                print(f"  [{i+1}/{batch_size}] #{prop_id} ({source:12}) ✓ {bedrooms} bed, {prop_type}")
            else:
                print(f"  [{i+1}/{batch_size}] #{prop_id} ({source:12}) ✗ No data")

            results.append(prop)

    return results

def print_source_stats():
    """Print current statistics for all sources."""
    print("\n" + "="*70)
    print("SOURCE PERFORMANCE:")
    print("="*70)

    for source_name, config in sources_config.items():
        status = "✅ ENABLED" if config['enabled'] else "❌ DISABLED"
        if config['attempts'] > 0:
            print(f"{source_name:15} {status:12} {config['success']:3}/{config['attempts']:3} ({config['success_rate']:5.1f}%)")
        else:
            print(f"{source_name:15} {status:12}   0/0   (  -.-%)")

    print("="*70 + "\n")

def load_csv(input_file):
    """Load properties from CSV."""
    properties = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

def save_results(output_file, results):
    """Save enrichment results to JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Parallel multi-source property enrichment")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", help="Output JSON file (default: enrichment_parallel_TIMESTAMP.json)")
    parser.add_argument("--limit", type=int, help="Limit number of properties to process")
    parser.add_argument("--batch-delay", type=int, default=120, help="Seconds between batches (default: 120)")
    parser.add_argument("--skip-enriched", action="store_true", help="Skip properties already enriched")

    args = parser.parse_args()

    # Load properties
    print(f"Loading properties from {args.input}...")
    properties = load_csv(args.input)
    print(f"Loaded {len(properties):,} properties")

    # Filter if needed
    if args.skip_enriched:
        to_enrich = [p for p in properties if not (p.get('bedrooms') or p.get('property_type'))]
        print(f"Skipping {len(properties) - len(to_enrich):,} already enriched")
        properties = to_enrich

    if args.limit:
        properties = properties[:args.limit]
        print(f"Limited to {len(properties):,} properties")

    # Default output filename with timestamp
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"enrichment_parallel_{timestamp}.json"

    enabled_sources = get_enabled_sources()
    batch_size = len(enabled_sources)

    print(f"\nParallel Multi-Source Enrichment:")
    print(f"  Sources: {', '.join(enabled_sources)}")
    print(f"  Parallel batch size: {batch_size} properties (1 per source)")
    print(f"  Min success rate: {MIN_SUCCESS_RATE}%")
    print(f"  Batch delay: {args.batch_delay}s")
    print(f"  Output: {args.output}")
    print()

    all_results = []
    batch_num = 0
    position = 0

    while position < len(properties):
        batch_num += 1
        enabled_sources = get_enabled_sources()

        if not enabled_sources:
            print("All sources disabled. Stopping.")
            break

        batch_size = len(enabled_sources)
        batch = properties[position:position + batch_size]

        print(f"Batch {batch_num}: Processing {len(batch)} properties in parallel ({position+1}-{position+len(batch)}/{len(properties)})")

        batch_results = process_batch(batch)
        all_results.extend(batch_results)
        position += len(batch)

        # Save progress
        save_results(args.output, all_results)
        print(f"  💾 Progress saved: {position}/{len(properties)} properties")

        # Show stats periodically
        if batch_num % 10 == 0:
            print_source_stats()

        # Delay between batches (let all sources forget IP)
        if position < len(properties):
            print(f"  ⏱  Waiting {args.batch_delay}s before next batch...\n")
            time.sleep(args.batch_delay)

    # Final save
    save_results(args.output, all_results)

    # Final statistics
    print("\n" + "="*70)
    print("ENRICHMENT COMPLETE!")
    print("="*70)
    print(f"\nResults saved to: {args.output}")
    print(f"\nOverall Statistics:")
    print(f"  Total processed: {stats['total']['processed']:,}")
    print(f"  Successfully enriched: {stats['total']['enriched']:,} ({stats['total']['enriched']/len(properties)*100:.1f}%)")
    print(f"  Skipped (already had data): {stats['total']['skipped']:,}")

    print_source_stats()

    enabled_count = sum(1 for cfg in sources_config.values() if cfg['enabled'])
    disabled_count = len(sources_config) - enabled_count

    if disabled_count > 0:
        print(f"⚠️  {disabled_count} source(s) were disabled due to low success rates")

    print("\nNext step: Import results back to database")

if __name__ == "__main__":
    main()
