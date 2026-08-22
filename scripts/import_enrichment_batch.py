#!/usr/bin/env python3
"""
Import enrichment batch results with canonical cache validation.

Tests cache functionality by:
1. Loading existing enrichment data into cache
2. Comparing batch results against cached canonical values
3. Showing conflicts where batch differs from cache
4. Updating database with cache-aware logic

Usage:
    python3 scripts/import_enrichment_batch.py enrichment_batch4_results_*.json [--dry-run]
"""

import json
import sys
import os
import psycopg2
from dotenv import load_dotenv
from collections import defaultdict

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))
from canonical_geocoding import (
    initialize_cache,
    get_canonical_property_data,
    cache_enrichment_data
)

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')


def load_batch_results(filepaths):
    """Load all batch result files."""
    all_results = []
    for filepath in filepaths:
        print(f"Loading {filepath}...")
        with open(filepath) as f:
            results = json.load(f)
            all_results.extend(results)
    return all_results


def fetch_addresses_from_db(property_ids):
    """Fetch address_normalized for property IDs."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT id, address_normalized
            FROM properties
            WHERE id = ANY(%s)
        """, (property_ids,))

        return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def analyze_cache_conflicts(batch_results, address_map):
    """
    Compare batch results against cached canonical values.

    Returns:
        dict with 'matches', 'conflicts', 'new_addresses' counts
    """
    stats = {
        'total': len(batch_results),
        'with_data': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'matches': 0,
        'conflicts': 0,
        'new_addresses': 0
    }

    conflicts = []

    for prop in batch_results:
        prop_id = prop.get('id')
        address_norm = address_map.get(prop_id)
        batch_bedrooms = prop.get('bedrooms')
        batch_type = prop.get('property_type')

        # Skip if no enrichment data
        if not batch_bedrooms and not batch_type:
            continue

        stats['with_data'] += 1

        if not address_norm:
            continue

        # Check cache
        cached = get_canonical_property_data(address_norm)

        if cached:
            stats['cache_hits'] += 1

            # Compare values
            if batch_bedrooms or batch_type:
                # Check for conflicts
                bedroom_conflict = (batch_bedrooms and cached.bedrooms and
                                  batch_bedrooms != cached.bedrooms)
                type_conflict = (batch_type and cached.property_type and
                               batch_type != cached.property_type)

                if bedroom_conflict or type_conflict:
                    stats['conflicts'] += 1
                    conflicts.append({
                        'id': prop_id,
                        'address': address_norm[:50],
                        'batch_bedrooms': batch_bedrooms,
                        'cached_bedrooms': cached.bedrooms,
                        'batch_type': batch_type,
                        'cached_type': cached.property_type
                    })
                else:
                    stats['matches'] += 1
        else:
            stats['cache_misses'] += 1
            if batch_bedrooms or batch_type:
                stats['new_addresses'] += 1

    return stats, conflicts


def import_with_cache(batch_results, address_map, dry_run=False):
    """
    Import batch results using cache-aware logic.

    Strategy:
    - For addresses in cache: Use cached canonical values (ignore batch)
    - For new addresses: Use batch values and add to cache
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        updates = []
        cache_updates = []
        skipped_conflicts = []

        for prop in batch_results:
            prop_id = prop.get('id')
            address_norm = address_map.get(prop_id)
            batch_bedrooms = prop.get('bedrooms')
            batch_type = prop.get('property_type')

            if not address_norm or not prop_id:
                continue

            # Skip if no enrichment data
            if not batch_bedrooms and not batch_type:
                continue

            # Check cache
            cached = get_canonical_property_data(address_norm)

            if cached:
                # Use cached canonical values
                final_bedrooms = cached.bedrooms
                final_type = cached.property_type

                # Track if batch differs from cache
                if ((batch_bedrooms and batch_bedrooms != final_bedrooms) or
                    (batch_type and batch_type != final_type)):
                    skipped_conflicts.append({
                        'id': prop_id,
                        'address': address_norm[:50],
                        'batch': (batch_bedrooms, batch_type),
                        'used_cached': (final_bedrooms, final_type)
                    })
            else:
                # New address - use batch values
                final_bedrooms = batch_bedrooms
                final_type = batch_type

                # Add to cache
                if final_bedrooms or final_type:
                    cache_updates.append((address_norm, final_bedrooms, final_type))

            # Queue database update
            if final_bedrooms or final_type:
                updates.append((prop_id, final_bedrooms, final_type))

        # Update database
        if not dry_run and updates:
            print(f"\nUpdating database with {len(updates)} properties...")
            for prop_id, bedrooms, prop_type in updates:
                cur.execute("""
                    UPDATE properties
                    SET bedrooms = %s, property_type = %s
                    WHERE id = %s
                """, (bedrooms, prop_type, prop_id))
            conn.commit()
            print(f"✓ Database updated")

            # Update cache
            for address_norm, bedrooms, prop_type in cache_updates:
                cache_enrichment_data(address_norm, bedrooms, prop_type)
            print(f"✓ Cache updated with {len(cache_updates)} new addresses")

        return {
            'total_updates': len(updates),
            'new_addresses': len(cache_updates),
            'conflicts_resolved': len(skipped_conflicts),
            'conflicts': skipped_conflicts[:10]  # First 10 examples
        }

    finally:
        conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import enrichment batch with cache validation')
    parser.add_argument('files', nargs='+', help='Batch result JSON files')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating database')

    args = parser.parse_args()

    print("=" * 70)
    print("ENRICHMENT BATCH IMPORT (with canonical cache)")
    print("=" * 70)
    print()

    # 1. Initialize cache
    print("1. Initializing canonical cache...")
    initialize_cache(DATABASE_URL)
    print("   ✓ Cache loaded\n")

    # 2. Load batch results
    print("2. Loading batch results...")
    batch_results = load_batch_results(args.files)
    print(f"   ✓ Loaded {len(batch_results):,} properties\n")

    # 3. Fetch addresses from database
    print("3. Fetching addresses from database...")
    property_ids = [p['id'] for p in batch_results if 'id' in p]
    address_map = fetch_addresses_from_db(property_ids)
    print(f"   ✓ Fetched {len(address_map):,} addresses\n")

    # 4. Analyze cache conflicts
    print("4. Analyzing cache conflicts...")
    stats, conflicts = analyze_cache_conflicts(batch_results, address_map)

    print(f"   Cache Analysis:")
    print(f"   - Properties with enrichment data: {stats['with_data']:,}")
    print(f"   - Cache hits: {stats['cache_hits']:,}")
    print(f"   - Cache misses: {stats['cache_misses']:,}")
    print(f"   - Matches (batch = cache): {stats['matches']:,}")
    print(f"   - Conflicts (batch ≠ cache): {stats['conflicts']:,}")
    print(f"   - New addresses: {stats['new_addresses']:,}")
    print()

    if conflicts:
        print(f"   Example conflicts (showing first 5):")
        for c in conflicts[:5]:
            print(f"   - {c['address']}")
            print(f"     Batch: {c['batch_bedrooms']} bed, {c['batch_type']}")
            print(f"     Cache: {c['cached_bedrooms']} bed, {c['cached_type']}")
        print()

    # 5. Import with cache-aware logic
    print("5. Importing with cache-aware logic...")
    if args.dry_run:
        print("   DRY RUN - no database changes")

    results = import_with_cache(batch_results, address_map, dry_run=args.dry_run)

    print()
    print("=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Total updates: {results['total_updates']:,}")
    print(f"New addresses added to cache: {results['new_addresses']:,}")
    print(f"Conflicts resolved (used cache): {results['conflicts_resolved']:,}")

    if results['conflicts']:
        print()
        print("Example conflicts resolved (showing first 5):")
        for c in results['conflicts'][:5]:
            print(f"  Property {c['id']}: {c['address']}")
            print(f"    Batch had: {c['batch']}")
            print(f"    Used cache: {c['used_cached']}")

    if args.dry_run:
        print()
        print("⚠️  DRY RUN - No changes were made")
        print("    Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
