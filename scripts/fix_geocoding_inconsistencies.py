#!/usr/bin/env python3
"""
One-time fix script to standardize geocoding and enrichment inconsistencies.

Fixes 51,669 addresses with multiple distinct coordinates and 42 addresses
with inconsistent enrichment data.

Usage:
    python3 scripts/fix_geocoding_inconsistencies.py [--dry-run]
"""

import asyncio
import asyncpg
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))
from canonical_geocoding import (
    _select_canonical_coordinates,
    _select_canonical_enrichment
)

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

BATCH_SIZE = 5000


async def query_inconsistent_coordinates(conn: asyncpg.Connection) -> List[str]:
    """
    Query addresses with multiple distinct coordinates.

    Returns:
        List of address_normalized strings with inconsistent coordinates
    """
    rows = await conn.fetch("""
        SELECT address_normalized
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND latitude IS NOT NULL
        GROUP BY address_normalized
        HAVING COUNT(DISTINCT latitude) > 1 OR COUNT(DISTINCT longitude) > 1
    """)

    return [row['address_normalized'] for row in rows]


async def query_inconsistent_enrichment(conn: asyncpg.Connection) -> List[str]:
    """
    Query addresses with multiple distinct enrichment values.

    Returns:
        List of address_normalized strings with inconsistent enrichment
    """
    # Bedrooms
    bedroom_rows = await conn.fetch("""
        SELECT address_normalized
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND bedrooms IS NOT NULL
        GROUP BY address_normalized
        HAVING COUNT(DISTINCT bedrooms) > 1
    """)

    # Property types
    type_rows = await conn.fetch("""
        SELECT address_normalized
        FROM properties
        WHERE address_normalized IS NOT NULL
          AND property_type IS NOT NULL
        GROUP BY address_normalized
        HAVING COUNT(DISTINCT property_type) > 1
    """)

    # Combine and dedupe
    addresses = set()
    addresses.update(row['address_normalized'] for row in bedroom_rows)
    addresses.update(row['address_normalized'] for row in type_rows)

    return list(addresses)


async def fetch_sales_for_address(
    conn: asyncpg.Connection,
    address_normalized: str
) -> List[Dict]:
    """Fetch all sales for an address."""
    rows = await conn.fetch("""
        SELECT
            id,
            latitude,
            longitude,
            bedrooms,
            property_type,
            sale_date,
            price,
            geocode_quality_issue
        FROM properties
        WHERE address_normalized = $1
        ORDER BY sale_date DESC
    """, address_normalized)

    return [dict(row) for row in rows]


async def fix_address_coordinates(
    conn: asyncpg.Connection,
    address_normalized: str,
    dry_run: bool = False
) -> Dict:
    """
    Fix coordinates for all sales of an address.

    Returns:
        Audit log entry with decision details
    """
    sales = await fetch_sales_for_address(conn, address_normalized)

    if not sales:
        return None

    # Apply selection strategy
    canonical_lat, canonical_lon = _select_canonical_coordinates(sales)

    # Count how many will be updated
    property_ids = [s['id'] for s in sales]
    updated_count = len(property_ids)

    # Update database
    if not dry_run:
        await conn.execute("""
            UPDATE properties
            SET latitude = $1, longitude = $2
            WHERE id = ANY($3::bigint[])
        """, canonical_lat, canonical_lon, property_ids)

    # Return audit log entry
    return {
        'address_normalized': address_normalized,
        'chosen_coordinates': [canonical_lat, canonical_lon],
        'updated_count': updated_count,
        'reason': 'hybrid_selection',
        'timestamp': datetime.now().isoformat()
    }


async def fix_address_enrichment(
    conn: asyncpg.Connection,
    address_normalized: str,
    dry_run: bool = False
) -> Dict:
    """
    Fix enrichment for all sales of an address.

    Returns:
        Audit log entry with decision details
    """
    sales = await fetch_sales_for_address(conn, address_normalized)

    if not sales:
        return None

    # Apply selection strategy
    canonical_enrichment = _select_canonical_enrichment(sales)

    # Update database
    property_ids = [s['id'] for s in sales]

    if not dry_run:
        await conn.execute("""
            UPDATE properties
            SET bedrooms = $1, property_type = $2
            WHERE id = ANY($3::bigint[])
        """, canonical_enrichment['bedrooms'], canonical_enrichment['property_type'], property_ids)

    return {
        'address_normalized': address_normalized,
        'chosen_enrichment': canonical_enrichment,
        'updated_count': len(property_ids),
        'timestamp': datetime.now().isoformat()
    }


def process_in_batches(items: List, batch_size: int):
    """Yield batches of items."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


async def process_batch(
    conn: asyncpg.Connection,
    addresses: List[str],
    fix_type: str,
    dry_run: bool
) -> List[Dict]:
    """
    Process a batch of addresses.

    Args:
        conn: Database connection
        addresses: List of address_normalized strings
        fix_type: 'coordinates' or 'enrichment'
        dry_run: If True, don't update database

    Returns:
        List of audit log entries
    """
    audit_entries = []

    for address in addresses:
        try:
            if fix_type == 'coordinates':
                entry = await fix_address_coordinates(conn, address, dry_run)
            elif fix_type == 'enrichment':
                entry = await fix_address_enrichment(conn, address, dry_run)
            else:
                raise ValueError(f"Unknown fix_type: {fix_type}")

            if entry:
                audit_entries.append(entry)

        except Exception as e:
            print(f"Error fixing {address}: {e}")
            audit_entries.append({
                'address_normalized': address,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    return audit_entries


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fix geocoding and enrichment inconsistencies'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating database'
    )
    args = parser.parse_args()

    audit_log = {
        'start_time': datetime.now().isoformat(),
        'dry_run': args.dry_run,
        'coordinates': [],
        'enrichment': []
    }

    print(f"Starting fix script (dry_run={args.dry_run})...")

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Fix coordinates
        print("\n1. Fixing coordinate inconsistencies...")
        coord_addresses = await query_inconsistent_coordinates(conn)
        print(f"Found {len(coord_addresses)} addresses with inconsistent coordinates")

        batch_num = 0
        for batch in process_in_batches(coord_addresses, BATCH_SIZE):
            batch_num += 1
            print(f"Processing coordinate batch {batch_num}/{(len(coord_addresses) + BATCH_SIZE - 1) // BATCH_SIZE}...")

            async with conn.transaction():
                entries = await process_batch(conn, batch, 'coordinates', args.dry_run)
                audit_log['coordinates'].extend(entries)

        # Fix enrichment
        print("\n2. Fixing enrichment inconsistencies...")
        enrichment_addresses = await query_inconsistent_enrichment(conn)
        print(f"Found {len(enrichment_addresses)} addresses with inconsistent enrichment")

        batch_num = 0
        for batch in process_in_batches(enrichment_addresses, BATCH_SIZE):
            batch_num += 1
            print(f"Processing enrichment batch {batch_num}...")

            async with conn.transaction():
                entries = await process_batch(conn, batch, 'enrichment', args.dry_run)
                audit_log['enrichment'].extend(entries)

        # Write audit log
        audit_log['end_time'] = datetime.now().isoformat()
        audit_log['summary'] = {
            'coordinates_fixed': len(audit_log['coordinates']),
            'enrichment_fixed': len(audit_log['enrichment'])
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audit_filename = f"fix_geocoding_audit_{timestamp}.json"

        with open(audit_filename, 'w') as f:
            json.dump(audit_log, f, indent=2)

        print(f"\n✓ Complete!")
        print(f"  Coordinates fixed: {len(audit_log['coordinates'])} addresses")
        print(f"  Enrichment fixed: {len(audit_log['enrichment'])} addresses")
        print(f"  Audit log: {audit_filename}")

        if args.dry_run:
            print("\n⚠️  DRY RUN - No changes were made to database")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
