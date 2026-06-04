#!/usr/bin/env python3
"""
Geocode properties by matching against existing geocoded addresses in the database.

Strategy:
1. Find properties without coordinates
2. For each, search for similar geocoded addresses
3. Match at different levels: exact address, same street+area, same street+county
4. Copy coordinates from best match with quality score
"""

import os
import re
import psycopg2
from dotenv import load_dotenv
from typing import Optional, Tuple

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def normalize_address(address: str) -> str:
    """Normalize address for matching."""
    addr = address.lower()

    # Remove common prefixes
    addr = re.sub(r'^no\.?\s*\d+\s*', '', addr)

    # Standardize abbreviations
    replacements = {
        r'\brd\b': 'road',
        r'\bave?\b': 'avenue',
        r'\bdr\b': 'drive',
        r'\btce\b': 'terrace',
        r'\bterr\b': 'terrace',
        r'\bcres\b': 'crescent',
        r'\bgdns?\b': 'gardens',
        r'\bsq\b': 'square',
        r'\bpk\b': 'park',
        r'\bblvd\b': 'boulevard',
        r'\bmt\b': 'mount',
        r'\bnth\b': 'north',
        r'\bsth\b': 'south',
        r'\bst\b': 'street',
    }

    for pattern, replacement in replacements.items():
        addr = re.sub(pattern, replacement, addr)

    # Remove punctuation and extra spaces
    addr = re.sub(r'[.,\-]', ' ', addr)
    addr = re.sub(r'\s+', ' ', addr)

    return addr.strip()

def extract_street_and_area(address: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract street name and area from address."""
    normalized = normalize_address(address)
    parts = normalized.split(',')

    if len(parts) >= 2:
        # First part is usually street, last part is usually area/county
        street = parts[0].strip()
        area = parts[-1].strip() if len(parts) > 1 else None
        return street, area

    return None, None

def find_matching_coordinates(cur, address: str, county: str) -> Optional[Tuple[float, float, int, str]]:
    """
    Find coordinates from existing geocoded properties.
    Returns (latitude, longitude, quality_score, match_type) or None.

    Match levels:
    1. Exact address match (quality: 100)
    2. Same street + area (quality: 90)
    3. Same street + county (quality: 80)
    """

    normalized_addr = normalize_address(address)
    street, area = extract_street_and_area(address)

    # Level 1: Exact normalized address match in same county
    cur.execute("""
        SELECT latitude, longitude, COUNT(*) as cnt
        FROM properties
        WHERE latitude IS NOT NULL
        AND county = %s
        AND LOWER(REGEXP_REPLACE(REGEXP_REPLACE(address, '[.,\\-]', ' ', 'g'), '\\s+', ' ', 'g')) = %s
        GROUP BY latitude, longitude
        ORDER BY cnt DESC
        LIMIT 1
    """, (county, normalized_addr))

    result = cur.fetchone()
    if result and result[2] >= 1:  # At least 1 match
        return (result[0], result[1], 100, 'exact_address')

    # Level 2: Same street name in same county (if we can extract it)
    if street:
        # Look for properties with similar street in the same county
        cur.execute("""
            SELECT latitude, longitude, COUNT(*) as cnt
            FROM properties
            WHERE latitude IS NOT NULL
            AND county = %s
            AND LOWER(REGEXP_REPLACE(REGEXP_REPLACE(address, '[.,\\-]', ' ', 'g'), '\\s+', ' ', 'g')) LIKE %s
            GROUP BY latitude, longitude
            HAVING COUNT(*) >= 3  -- Must have at least 3 properties at this location
            ORDER BY cnt DESC
            LIMIT 1
        """, (county, f'%{street}%'))

        result = cur.fetchone()
        if result and result[2] >= 3:
            return (result[0], result[1], 80, 'same_street')

    return None

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     GEOCODE FROM EXISTING DATABASE MATCHES                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set")
        return 1

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Get properties without coordinates
        print("1. Finding properties without coordinates...")
        cur.execute("""
            SELECT id, address, county
            FROM properties
            WHERE latitude IS NULL
            AND address IS NOT NULL
            AND county IS NOT NULL
            ORDER BY sale_date DESC
            LIMIT 10000
        """)

        missing = cur.fetchall()
        print(f"   Found {len(missing):,} properties without coordinates")
        print()

        if not missing:
            print("✅ All properties already geocoded!")
            return 0

        # Try to match each one
        print("2. Searching for matching geocoded addresses...")
        print()

        matches = {
            'exact_address': 0,
            'same_street': 0,
            'no_match': 0
        }

        updates = []

        for i, (prop_id, address, county) in enumerate(missing):
            if i > 0 and i % 100 == 0:
                print(f"   Processed {i:,}/{len(missing):,} ({100*i/len(missing):.1f}%)")

            result = find_matching_coordinates(cur, address, county)

            if result:
                lat, lon, quality, match_type = result
                matches[match_type] += 1
                updates.append((lat, lon, quality, match_type, prop_id))
            else:
                matches['no_match'] += 1

        print(f"   Processed {len(missing):,}/{len(missing):,} (100.0%)")
        print()

        # Show results
        print("3. Match Results:")
        print(f"   ✅ Exact address matches: {matches['exact_address']:,}")
        print(f"   ✅ Same street matches: {matches['same_street']:,}")
        print(f"   ❌ No matches found: {matches['no_match']:,}")
        print()

        total_matches = matches['exact_address'] + matches['same_street']

        if total_matches == 0:
            print("No matches found. No updates to apply.")
            return 0

        print(f"4. Found {total_matches:,} properties that can be geocoded from existing data")
        print()

        # Ask for confirmation
        response = input("Apply these coordinates to the database? (yes/no): ")

        if response.lower() != 'yes':
            print("Cancelled. No changes made.")
            return 0

        # Apply updates
        print()
        print("5. Applying coordinates...")

        for lat, lon, quality, match_type, prop_id in updates:
            cur.execute("""
                UPDATE properties
                SET latitude = %s,
                    longitude = %s,
                    geog = ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    geocode_quality = %s,
                    needs_geocoding = FALSE
                WHERE id = %s
            """, (lat, lon, lon, lat, quality, prop_id))

        conn.commit()

        print(f"   ✅ Updated {total_matches:,} properties")
        print()

        # Show final stats
        print("6. Final Statistics:")
        cur.execute('SELECT COUNT(*), COUNT(latitude) FROM properties')
        total, geocoded = cur.fetchone()
        print(f"   Total properties: {total:,}")
        print(f"   Geocoded: {geocoded:,} ({100*geocoded/total:.1f}%)")
        print(f"   Missing: {total-geocoded:,} ({100*(total-geocoded)/total:.1f}%)")
        print()

        print("="*70)
        print("GEOCODING FROM EXISTING MATCHES COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cur.close()
        conn.close()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
