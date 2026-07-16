#!/usr/bin/env python3
"""
Batch 6 enrichment: Target all 2026 properties missing enrichment data.
Prioritizes June 2026 properties first, then works backwards through the year.
"""

import os
import sys
import psycopg2
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

def extract_bedrooms(text):
    """Extract bedroom count from text."""
    if not text:
        return None

    text = text.lower()
    patterns = [
        r'(\d+)\s*bed',
        r'(\d+)\s*-\s*bed',
        r'(\d+)\s*br\b'
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
        ('terraced', ['terraced', 'terrace']),
        ('apartment', ['apartment', 'apt']),
        ('duplex', ['duplex']),
        ('bungalow', ['bungalow']),
        ('cottage', ['cottage']),
        ('house', ['house'])
    ]

    for prop_type, keywords in type_keywords:
        if any(keyword in text for keyword in keywords):
            return prop_type

    return None

def search_web_for_property(address, county, max_retries=2):
    """Search web for property details using DuckDuckGo with retries."""
    for attempt in range(max_retries):
        try:
            search_query = f"{address} {county} Ireland property"
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return None, None

            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text().lower()

            bedrooms = extract_bedrooms(text_content)
            property_type = extract_property_type(text_content)

            return bedrooms, property_type

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Search failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(5)
            else:
                print(f"  ⚠️  Search failed after {max_retries} attempts: {e}")
                return None, None

    return None, None

def fetch_properties_to_enrich(conn, limit=100):
    """Fetch 2026 properties missing enrichment data, prioritizing June first."""
    cur = conn.cursor()

    # Prioritize: June 2026, then May, April, etc. (most recent first)
    # Only fetch properties missing BOTH fields to maximize impact.
    # Use a sargable date RANGE (not EXTRACT(YEAR ...)) so the planner can use
    # properties_sale_date_idx as an Index Cond instead of a full index filter.
    cur.execute("""
        SELECT id, address, county, sale_date, price
        FROM properties
        WHERE sale_date >= '2026-01-01'
          AND sale_date < '2027-01-01'
          AND bedrooms IS NULL
          AND property_type IS NULL
        ORDER BY sale_date DESC
        LIMIT %s
    """, (limit,))

    properties = []
    for row in cur.fetchall():
        properties.append({
            'id': row[0],
            'address': row[1],
            'county': row[2],
            'sale_date': row[3],
            'price': row[4]
        })

    return properties

def update_property_enrichment(property_id, address, bedrooms, property_type):
    """Update property with enrichment data, applying to all sales of the same address.
    Uses a fresh connection for each update to avoid pooling issues."""

    updates = []
    params = []

    if bedrooms is not None:
        updates.append("bedrooms = %s")
        params.append(bedrooms)

    if property_type is not None:
        updates.append("property_type = %s")
        params.append(property_type)

    if not updates:
        return False, 0

    # Create fresh connection for this update
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()

        # Check if there are multiple sales of the same property
        cur.execute("""
            SELECT id, sale_date
            FROM properties
            WHERE address = %s
              AND (bedrooms IS NULL OR property_type IS NULL)
            ORDER BY sale_date DESC
        """, (address,))

        duplicate_sales = cur.fetchall()

        if len(duplicate_sales) > 1:
            # Update all sales of this property
            params_copy = params.copy()
            params_copy.append(address)
            query = f"UPDATE properties SET {', '.join(updates)} WHERE address = %s"
            cur.execute(query, params_copy)
            conn.commit()
            return True, len(duplicate_sales)
        else:
            # Update just this property
            params.append(property_id)
            query = f"UPDATE properties SET {', '.join(updates)} WHERE id = %s"
            cur.execute(query, params)
            conn.commit()
            return True, 1
    finally:
        conn.close()

def run_enrichment_batch(batch_size=100, rate_limit_seconds=10, report_interval=5):
    """Run batch enrichment process."""
    print("=" * 70)
    print("BATCH 6 ENRICHMENT: 2026 Properties")
    print("=" * 70)
    print(f"Target: Properties missing both bedrooms AND property_type")
    print(f"Priority: June 2026 → January 2026 (most recent first)")
    print(f"Batch size: {batch_size}")
    print(f"Rate limit: {rate_limit_seconds}s between requests")
    print(f"Progress reports: Every {report_interval} properties")
    print()

    conn = psycopg2.connect(DATABASE_URL)

    # Fetch properties to enrich
    print("📊 Fetching properties to enrich...")
    properties = fetch_properties_to_enrich(conn, limit=batch_size)

    if not properties:
        print("✅ No properties to enrich!")
        conn.close()
        return

    print(f"Found {len(properties)} properties to enrich")
    print()

    # Track statistics
    stats = {
        'total': len(properties),
        'enriched': 0,
        'partial': 0,
        'failed': 0,
        'duplicate_updates': 0,  # Track how many duplicate sales we updated
        'by_month': {}
    }

    results = []

    for i, prop in enumerate(properties, 1):
        month = prop['sale_date'].strftime('%Y-%m')
        if month not in stats['by_month']:
            stats['by_month'][month] = {'total': 0, 'enriched': 0}
        stats['by_month'][month]['total'] += 1

        print(f"[{i}/{len(properties)}] {prop['address'][:50]}")
        print(f"  📅 {prop['sale_date'].strftime('%d %b %Y')} | €{prop['price']:,.0f}")

        # Search web for property details
        bedrooms, property_type = search_web_for_property(prop['address'], prop['county'])

        if bedrooms or property_type:
            success, count = update_property_enrichment(prop['id'], prop['address'], bedrooms, property_type)

            if success:
                if bedrooms and property_type:
                    if count > 1:
                        print(f"  ✅ Fully enriched: {bedrooms} bed, {property_type} (updated {count} sales)")
                        stats['duplicate_updates'] += (count - 1)
                    else:
                        print(f"  ✅ Fully enriched: {bedrooms} bed, {property_type}")
                    stats['enriched'] += 1
                    stats['by_month'][month]['enriched'] += 1
                else:
                    if count > 1:
                        print(f"  ⚠️  Partial: {bedrooms or '?'} bed, {property_type or '?'} (updated {count} sales)")
                    else:
                        print(f"  ⚠️  Partial: {bedrooms or '?'} bed, {property_type or '?'}")
                    stats['partial'] += 1
            else:
                print(f"  ❌ Update failed")
                stats['failed'] += 1
        else:
            print(f"  ❌ No data found")
            stats['failed'] += 1

        results.append({
            'id': prop['id'],
            'address': prop['address'],
            'sale_date': prop['sale_date'].isoformat(),
            'bedrooms': bedrooms,
            'property_type': property_type
        })

        # Progress report every N properties
        if i % report_interval == 0:
            print()
            print("─" * 70)
            print(f"📊 PROGRESS REPORT: {i}/{len(properties)} ({i/len(properties)*100:.1f}%)")
            print(f"   ✅ Fully enriched: {stats['enriched']} ({stats['enriched']/i*100:.1f}%)")
            print(f"   ⚠️  Partially enriched: {stats['partial']} ({stats['partial']/i*100:.1f}%)")
            print(f"   ❌ Failed: {stats['failed']} ({stats['failed']/i*100:.1f}%)")
            if stats['duplicate_updates'] > 0:
                print(f"   🎁 Bonus updates: {stats['duplicate_updates']} additional sales")
            print("─" * 70)
            print()

        # Rate limiting
        if i < len(properties):
            time.sleep(rate_limit_seconds)

    conn.close()

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'enrichment_batch6_results_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 70)
    print("BATCH 6 ENRICHMENT COMPLETE")
    print("=" * 70)
    print(f"Total processed: {stats['total']}")
    print(f"Fully enriched: {stats['enriched']} ({stats['enriched']/stats['total']*100:.1f}%)")
    print(f"Partially enriched: {stats['partial']} ({stats['partial']/stats['total']*100:.1f}%)")
    print(f"Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    if stats['duplicate_updates'] > 0:
        print(f"Bonus: {stats['duplicate_updates']} additional sales enriched via duplicate detection!")
    print()
    print("Breakdown by month:")
    for month in sorted(stats['by_month'].keys(), reverse=True):
        m_stats = stats['by_month'][month]
        print(f"  {month}: {m_stats['enriched']}/{m_stats['total']} enriched")
    print()
    print(f"Results saved to: {output_file}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Batch 6: Enrich 2026 properties')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of properties to process')
    parser.add_argument('--rate-limit', type=int, default=10, help='Seconds between requests')
    parser.add_argument('--report-interval', type=int, default=5, help='Progress report every N properties')

    args = parser.parse_args()

    run_enrichment_batch(
        batch_size=args.batch_size,
        rate_limit_seconds=args.rate_limit,
        report_interval=args.report_interval
    )
