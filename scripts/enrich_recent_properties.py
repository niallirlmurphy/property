#!/usr/bin/env python3
"""
Production enrichment pipeline for recent property sales with canonical cache.
Searches web for property details (bedrooms, type) and updates database.
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

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))
from canonical_geocoding import (
    initialize_cache,
    get_canonical_property_data,
    cache_enrichment_data
)

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def extract_bedrooms(text):
    """Extract bedroom count from text."""
    if not text:
        return None

    text = text.lower()

    # Look for patterns like "3 bed", "2 bedroom", "4-bed"
    patterns = [
        r'(\d+)\s*bed',
        r'(\d+)\s*-\s*bed',
        r'(\d+)\s*br\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            count = int(match.group(1))
            if 1 <= count <= 10:  # Sanity check
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

def search_web_for_property(address, county):
    """Search web for property details using DuckDuckGo."""
    try:
        # Build search query
        search_query = f"{address} {county} Ireland property"
        encoded_query = quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get result snippets
            results = soup.find_all('a', class_='result__snippet')

            # Combine text from first 3 results
            combined_text = ' '.join([r.get_text() for r in results[:3]])

            if combined_text:
                bedrooms = extract_bedrooms(combined_text)
                property_type = extract_property_type(combined_text)

                if bedrooms or property_type:
                    return {
                        'success': True,
                        'bedrooms': bedrooms,
                        'property_type': property_type
                    }

        return {'success': False, 'reason': 'No data found'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def enrich_properties(months=3, limit=None, dry_run=False):
    """
    Enrich recent properties with bedroom and type data.

    Args:
        months: How many months back to search (default: 3)
        limit: Max properties to process (default: None = all)
        dry_run: If True, don't update database (default: False)
    """
    print("="*80, flush=True)
    print("PROPERTY ENRICHMENT PIPELINE", flush=True)
    print("="*80, flush=True)
    print(flush=True)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Find recent properties without enrichment data
        print(f"1. Finding recent properties (last {months} months)...", flush=True)

        query = f"""
            SELECT id, address, address_normalized, county, price, sale_date
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

        # Process each property
        print(f"2. Searching for property details (checking cache first)...", flush=True)
        print(flush=True)

        successful = 0
        failed = 0
        cached = 0
        updates = []

        for i, (prop_id, address, address_normalized, county, price, sale_date) in enumerate(properties, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(properties)} ({100*i/len(properties):.1f}%)", flush=True)

            # Check cache first
            bedrooms = None
            property_type = None

            if address_normalized:
                cached_data = get_canonical_property_data(address_normalized)
                if cached_data and cached_data.bedrooms is not None:
                    # Use cached enrichment
                    bedrooms = cached_data.bedrooms
                    property_type = cached_data.property_type
                    cached += 1
                    successful += 1
                    updates.append((prop_id, bedrooms, property_type, address[:50]))

                    if i <= 5:  # Show first 5
                        beds_str = f"{bedrooms} bed" if bedrooms else "N/A"
                        type_str = property_type or "N/A"
                        print(f"   ✅ [CACHE] {address[:50]:<50} → {beds_str}, {type_str}", flush=True)
                    continue  # Skip web scraping

            # Cache miss - web scrape
            result = search_web_for_property(address, county)

            if result['success']:
                successful += 1
                updates.append((
                    prop_id,
                    result['bedrooms'],
                    result['property_type'],
                    address[:50]
                ))

                # Update cache with new enrichment
                if address_normalized:
                    cache_enrichment_data(address_normalized, result['bedrooms'], result['property_type'])

                if i <= 5:  # Show first 5
                    beds_str = f"{result['bedrooms']} bed" if result['bedrooms'] else "N/A"
                    type_str = result['property_type'] or "N/A"
                    print(f"   ✅ {address[:50]:<50} → {beds_str}, {type_str}", flush=True)
            else:
                failed += 1

            # Rate limiting - only for actual web scraping (cache hits skip this)
            time.sleep(3)  # 3 seconds between requests

        print(f"   Progress: {len(properties)}/{len(properties)} (100.0%)", flush=True)
        print(flush=True)

        # Summary
        print("3. Summary:", flush=True)
        print(f"   Successful: {successful}/{len(properties)} ({100*successful/len(properties):.1f}%)", flush=True)
        print(f"   - From cache: {cached}", flush=True)
        print(f"   - Web scraped: {successful - cached}", flush=True)
        print(f"   Failed: {failed}/{len(properties)} ({100*failed/len(properties):.1f}%)", flush=True)
        print(flush=True)

        if not dry_run and updates:
            print(f"4. Updating database with {len(updates):,} enriched properties...", flush=True)

            # Batch update
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
            print(flush=True)

            # Final stats
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(bedrooms) as with_beds,
                    COUNT(property_type) as with_type,
                    ROUND(100.0 * COUNT(bedrooms) / COUNT(*), 1) as pct_beds,
                    ROUND(100.0 * COUNT(property_type) / COUNT(*), 1) as pct_type
                FROM properties
                WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
            """)

            total, with_beds, with_type, pct_beds, pct_type = cur.fetchone()

            print("Recent properties (last 3 months):", flush=True)
            print(f"   Total: {total:,}", flush=True)
            print(f"   With bedrooms: {with_beds:,} ({pct_beds}%)", flush=True)
            print(f"   With property type: {with_type:,} ({pct_type}%)", flush=True)

        elif dry_run:
            print("DRY RUN - No database updates performed", flush=True)
            print(f"Would have updated {len(updates):,} properties", flush=True)

        print(flush=True)
        print("="*80, flush=True)
        print("ENRICHMENT COMPLETE", flush=True)
        print("="*80, flush=True)

    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cur.close()
        conn.close()

    return 0

def main():
    import argparse

    # Initialize canonical cache
    print("Initializing canonical coordinate cache...")
    initialize_cache(DATABASE_URL)
    print("Cache initialized\n")

    parser = argparse.ArgumentParser(description='Enrich properties with bedroom and type data')
    parser.add_argument('--months', type=int, default=3, help='How many months back to search (default: 3)')
    parser.add_argument('--limit', type=int, help='Max properties to process (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating database')

    args = parser.parse_args()

    return enrich_properties(
        months=args.months,
        limit=args.limit,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    import sys
    sys.exit(main())
