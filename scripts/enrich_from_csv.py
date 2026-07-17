#!/usr/bin/env python3
"""
Enrich properties from CSV export file.

Takes the exported CSV, enriches properties via Google/DuckDuckGo,
and saves results to a local JSON file for later import.

Usage:
    python3 scripts/enrich_from_csv.py --input recent_3months.csv --output enrichment_results.json --limit 100
    python3 scripts/enrich_from_csv.py --input recent_3months.csv --batch-size 20 --batch-delay 120
"""

import os
import csv
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
    'duckduckgo': {'attempts': 0, 'success': 0},
    'total': {'processed': 0, 'enriched': 0, 'skipped': 0}
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

def search_duckduckgo(address, county):
    """Search DuckDuckGo for property details."""
    query = f"{address} {county} property sale Ireland"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        stats['duckduckgo']['attempts'] += 1
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text from results
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        if bedrooms or property_type:
            stats['duckduckgo']['success'] += 1
            return bedrooms, property_type

        return None, None

    except Exception as e:
        print(f"  ✗ DuckDuckGo error: {e}")
        return None, None

def search_google(address, county):
    """Search Google for property details."""
    query = f"{address} {county} property Ireland"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        stats['google']['attempts'] += 1
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()

        bedrooms = extract_bedrooms(text_content)
        property_type = extract_property_type(text_content)

        if bedrooms or property_type:
            stats['google']['success'] += 1
            return bedrooms, property_type

        return None, None

    except Exception as e:
        print(f"  ✗ Google error: {e}")
        return None, None

def enrich_property(prop, delay=10):
    """Enrich a single property."""
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
    source = None

    # Try DuckDuckGo first (less likely to block)
    bedrooms, property_type = search_duckduckgo(address, county)
    if bedrooms or property_type:
        source = 'duckduckgo'

    # If no results, try Google
    if not bedrooms and not property_type:
        time.sleep(delay)  # Rate limit
        bedrooms, property_type = search_google(address, county)
        if bedrooms or property_type:
            source = 'google'

    # Update property
    if bedrooms or property_type:
        prop['bedrooms'] = bedrooms
        prop['property_type'] = property_type
        prop['enrichment_source'] = source
        prop['enriched_at'] = datetime.now().isoformat()
        print(f"  ✓ Found: {bedrooms} bed, {property_type} (via {source})")
        stats['total']['enriched'] += 1
    else:
        print(f"  ✗ No data found")

    stats['total']['processed'] += 1
    time.sleep(delay)  # Rate limit between properties

    return prop

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
    parser = argparse.ArgumentParser(description="Enrich properties from CSV export")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", help="Output JSON file (default: enrichment_results_TIMESTAMP.json)")
    parser.add_argument("--limit", type=int, help="Limit number of properties to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Properties per batch (default: 50)")
    parser.add_argument("--batch-delay", type=int, default=120, help="Seconds to wait between batches (default: 120)")
    parser.add_argument("--delay", type=int, default=10, help="Seconds between requests (default: 10)")
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

    # Default output filename with timestamp, under logs/enrichment_results/
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'logs', 'enrichment_results'
        )
        os.makedirs(results_dir, exist_ok=True)
        args.output = os.path.join(results_dir, f"enrichment_results_{timestamp}.json")

    print(f"\nStarting enrichment:")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Batch delay: {args.batch_delay}s")
    print(f"  Request delay: {args.delay}s")
    print(f"  Output: {args.output}")
    print()

    results = []
    batch_num = 0

    for i, prop in enumerate(properties, 1):
        # Check if we need a batch break
        if i > 1 and (i - 1) % args.batch_size == 0:
            batch_num += 1
            print(f"\n{'='*70}")
            print(f"Batch {batch_num} complete. Waiting {args.batch_delay}s before next batch...")
            print(f"{'='*70}\n")
            time.sleep(args.batch_delay)

        enriched = enrich_property(prop, delay=args.delay)
        results.append(enriched)

        # Save progress periodically
        if i % 10 == 0:
            save_results(args.output, results)
            print(f"\n  Progress saved: {i}/{len(properties)} properties\n")

    # Final save
    save_results(args.output, results)

    print(f"\n{'='*70}")
    print("Enrichment complete!")
    print(f"{'='*70}")
    print(f"\nResults saved to: {args.output}")
    print(f"\nStatistics:")
    print(f"  Total processed: {stats['total']['processed']:,}")
    print(f"  Successfully enriched: {stats['total']['enriched']:,} ({stats['total']['enriched']/len(properties)*100:.1f}%)")
    print(f"  Skipped (already had data): {stats['total']['skipped']:,}")
    print()
    print(f"  DuckDuckGo: {stats['duckduckgo']['success']}/{stats['duckduckgo']['attempts']} success")
    print(f"  Google: {stats['google']['success']}/{stats['google']['attempts']} success")
    print()
    print("Next step: Import results back to database when online")

if __name__ == "__main__":
    main()
