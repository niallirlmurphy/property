#!/usr/bin/env python3
"""
Adaptive multi-source property enrichment.

Tries multiple sources in parallel with long delays between each.
Monitors success rate per source and automatically disables sources below 75%.

Usage:
    python3 scripts/enrich_adaptive_multisource.py --input enrichment_batch3_input.csv --output test_multisource.json --limit 50
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

# Source configuration and statistics
sources_config = {
    'duckduckgo': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
        'function': None  # Set below
    },
    'google': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
        'function': None
    },
    'myhome': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
        'function': None
    },
    'daft': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
        'function': None
    },
    'propertyprice': {
        'enabled': True,
        'attempts': 0,
        'success': 0,
        'success_rate': 0.0,
        'function': None
    }
}

stats = {
    'total': {'processed': 0, 'enriched': 0, 'skipped': 0}
}

MIN_SUCCESS_RATE = 75.0
MIN_ATTEMPTS_BEFORE_DISABLE = 10  # Need at least 10 attempts before disabling

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
        print(f"    ✗ DuckDuckGo error: {str(e)[:60]}")
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
        print(f"    ✗ Google error: {str(e)[:60]}")
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
        print(f"    ✗ MyHome error: {str(e)[:60]}")
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
        print(f"    ✗ Daft error: {str(e)[:60]}")
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
        print(f"    ✗ PropertyPrice error: {str(e)[:60]}")
        return None, None

# Register search functions
sources_config['duckduckgo']['function'] = search_duckduckgo
sources_config['google']['function'] = search_google
sources_config['myhome']['function'] = search_myhome
sources_config['daft']['function'] = search_daft
sources_config['propertyprice']['function'] = search_propertyprice

def update_source_stats(source_name, found_data):
    """Update statistics for a source and check if it should be disabled."""
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

def get_enabled_sources():
    """Get list of currently enabled sources."""
    return [(name, cfg) for name, cfg in sources_config.items() if cfg['enabled']]

def enrich_property(prop, source_delay=30):
    """Enrich a single property trying all enabled sources in parallel."""
    address = prop.get('address') or prop.get('address_normalized', '')
    county = prop.get('county', '')
    prop_id = prop['id']

    print(f"Enriching #{prop_id}: {address[:50]}...")

    # Check if already enriched
    if prop.get('bedrooms') or prop.get('property_type'):
        print(f"  ↷ Already has data: {prop.get('bedrooms', '?')} bed, {prop.get('property_type', '?')}")
        stats['total']['skipped'] += 1
        return prop

    bedrooms = None
    property_type = None
    sources_used = []

    # Try all enabled sources
    enabled_sources = get_enabled_sources()

    for i, (source_name, source_cfg) in enumerate(enabled_sources):
        search_func = source_cfg['function']

        try:
            b, pt = search_func(address, county)

            # Update if we got new info
            found_anything = False
            if b and not bedrooms:
                bedrooms = b
                found_anything = True
            if pt and not property_type:
                property_type = pt
                found_anything = True

            if found_anything:
                sources_used.append(source_name)
                print(f"    ✓ {source_name}: {b or '?'} bed, {pt or '?'}")

            # Update source stats
            update_source_stats(source_name, found_anything)

            # Long delay between sources to let services forget IP
            if i < len(enabled_sources) - 1:  # Don't delay after last source
                print(f"    ⏱  Waiting {source_delay}s before next source...")
                time.sleep(source_delay)

        except Exception as e:
            print(f"    ✗ {source_name} error: {str(e)[:60]}")
            update_source_stats(source_name, False)
            # Still wait to avoid rapid-fire requests
            if i < len(enabled_sources) - 1:
                time.sleep(source_delay)

    # Update property
    if bedrooms or property_type:
        prop['bedrooms'] = bedrooms
        prop['property_type'] = property_type
        prop['enrichment_sources'] = ','.join(sources_used)
        prop['enriched_at'] = datetime.now().isoformat()
        print(f"  ✅ Result: {bedrooms or '?'} bed, {property_type or '?'} (from {', '.join(sources_used)})")
        stats['total']['enriched'] += 1
    else:
        print(f"  ❌ No data found from any source")

    stats['total']['processed'] += 1

    return prop

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
    parser = argparse.ArgumentParser(description="Adaptive multi-source property enrichment")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", help="Output JSON file (default: enrichment_adaptive_TIMESTAMP.json)")
    parser.add_argument("--limit", type=int, help="Limit number of properties to process")
    parser.add_argument("--batch-size", type=int, default=10, help="Properties per batch (default: 10)")
    parser.add_argument("--batch-delay", type=int, default=120, help="Seconds to wait between batches (default: 120)")
    parser.add_argument("--source-delay", type=int, default=30, help="Seconds between sources (default: 30)")
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
        args.output = f"enrichment_adaptive_{timestamp}.json"

    print(f"\nAdaptive Multi-Source Enrichment:")
    print(f"  Sources: {', '.join(sources_config.keys())}")
    print(f"  Min success rate: {MIN_SUCCESS_RATE}%")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Batch delay: {args.batch_delay}s")
    print(f"  Source delay: {args.source_delay}s (between sources per property)")
    print(f"  Output: {args.output}")
    print()

    results = []
    batch_num = 0

    for i, prop in enumerate(properties, 1):
        # Check if we need a batch break
        if i > 1 and (i - 1) % args.batch_size == 0:
            batch_num += 1
            print_source_stats()
            print(f"Batch {batch_num} complete. Waiting {args.batch_delay}s before next batch...")
            print("="*70 + "\n")
            time.sleep(args.batch_delay)

        enriched = enrich_property(prop, source_delay=args.source_delay)
        results.append(enriched)

        # Save progress periodically
        if i % 5 == 0:
            save_results(args.output, results)
            print(f"\n  💾 Progress saved: {i}/{len(properties)} properties\n")

    # Final save
    save_results(args.output, results)

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
