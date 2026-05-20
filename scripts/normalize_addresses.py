#!/usr/bin/env python3
"""
Normalize all addresses in the properties table for better geocoding and enrichment.

Creates a new 'address_normalized' column with cleaned addresses that:
- Are more likely to match in geocoding APIs (Nominatim, Mapbox, Autoaddress)
- Follow consistent formatting rules
- Preserve the original address for display/legal purposes

Usage:
    python3 scripts/normalize_addresses.py [--limit N] [--dry-run]
"""

import asyncio
import asyncpg
import os
import sys
import re
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")


def normalize_address(address: str) -> str:
    """
    Normalize Irish property address for better API matching.

    Rules:
    1. Title case (except common words)
    2. Remove excessive punctuation
    3. Standardize common patterns
    4. Remove noise words that prevent matching
    5. Fix common OCR/data entry errors
    """
    if not address:
        return address

    normalized = address

    # 1. Basic cleanup
    normalized = normalized.strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
    normalized = re.sub(r',\s*,+', ',', normalized)  # Remove multiple commas

    # 2. Remove "No." / "No " prefix from house numbers
    # "No. 11 Main Street" → "11 Main Street"
    normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)

    # 3. Standardize apartment/unit formatting
    # "Apartment 5" → "Apt 5"
    # "Unit 12" → "Unit 12" (keep as is)
    normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

    # 4. Remove redundant location qualifiers that hurt matching
    # These often differ between PPR and geocoding databases
    noise_patterns = [
        r'\bMinisters?\s+Road\b',  # "Ministers Road" (specific to some estates)
        r'\bChurch\s+Fields\s+(East|West)\b',  # Directional qualifiers
        r'\bMiller\s*[\'S]*\s+Glen\b',  # Possessive variations
        r'\bStrawhall\b',  # Sub-locality that may not be in geocoder
    ]

    for pattern in noise_patterns:
        # Replace with space to avoid joining words
        normalized = re.sub(pattern, ' ', normalized, flags=re.I)

    # 5. Fix common OCR/data entry errors
    normalized = re.sub(r'\bCo\.?\s+', 'Co. ', normalized, flags=re.I)  # "Co Cork" → "Co. Cork"
    normalized = re.sub(r'\bCo\s+Dublin\b', 'Dublin', normalized, flags=re.I)  # "Co Dublin" → "Dublin"

    # 6. Standardize street types
    street_types = {
        r'\bSt\.?\b': 'Street',
        r'\bRd\.?\b': 'Road',
        r'\bAve\.?\b': 'Avenue',
        r'\bDr\.?\b': 'Drive',
        r'\bCl\.?\b': 'Close',
        r'\bCt\.?\b': 'Court',
        r'\bPk\.?\b': 'Park',
        r'\bSq\.?\b': 'Square',
    }

    for abbrev, full in street_types.items():
        normalized = re.sub(abbrev, full, normalized, flags=re.I)

    # 7. Clean up punctuation
    normalized = re.sub(r',\s*,', ',', normalized)  # Double commas
    normalized = re.sub(r'\s+,', ',', normalized)  # Space before comma
    normalized = re.sub(r',\s+', ', ', normalized)  # Standardize comma spacing
    normalized = normalized.strip(', ')  # Trim leading/trailing commas

    # 8. Title case with exceptions for common Irish words
    # Keep all-caps county names, fix mixed case
    words = normalized.split()
    lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
    upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

    result_words = []
    for i, word in enumerate(words):
        # First word always capitalized
        if i == 0:
            result_words.append(word.capitalize())
        # Keep known upper case
        elif word in upper_exceptions:
            result_words.append(word)
        # Lower case exceptions
        elif word.lower() in lower_exceptions:
            result_words.append(word.lower())
        # Title case for everything else
        else:
            result_words.append(word.capitalize())

    normalized = ' '.join(result_words)

    # 9. Final cleanup
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


async def add_normalized_column(pool):
    """Add address_normalized column if it doesn't exist."""
    print("Checking for address_normalized column...")

    async with pool.acquire() as conn:
        # Check if column exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'properties'
                AND column_name = 'address_normalized'
            )
        """)

        if not exists:
            print("  Creating address_normalized column...")
            await conn.execute("""
                ALTER TABLE properties
                ADD COLUMN address_normalized TEXT
            """)
            print("  ✅ Column created")

            # Add index for faster lookups
            print("  Creating index on address_normalized...")
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_normalized
                ON properties (address_normalized)
            """)
            print("  ✅ Index created")
        else:
            print("  ✅ Column already exists")


async def normalize_all_addresses(pool, limit=None, dry_run=False):
    """Normalize all addresses in the database."""

    print("\n" + "="*70)
    print("NORMALIZING ADDRESSES")
    print("="*70)
    print()

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print()

    # Get addresses to normalize
    if dry_run:
        # In dry run, just get any addresses (column may not exist yet)
        query = """
            SELECT id, address
            FROM properties
            WHERE address IS NOT NULL
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
    else:
        # In live mode, only process un-normalized addresses
        query = """
            SELECT id, address
            FROM properties
            WHERE address IS NOT NULL
            AND (address_normalized IS NULL OR address_normalized = '')
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)

    total = len(rows)
    print(f"Found {total:,} addresses to normalize")
    print()

    if dry_run:
        print("Sample normalizations (first 20):")
        print("-" * 70)
        for row in rows[:20]:
            original = row['address']
            normalized = normalize_address(original)
            changed = "✓" if normalized != original else " "
            print(f"{changed} {original[:40]:<40} → {normalized[:40]}")
        print()
        return

    # Process in batches
    BATCH_SIZE = 1000
    updated = 0

    print("Processing batches...")

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]

        async with pool.acquire() as conn:
            async with conn.transaction():
                for row in batch:
                    normalized = normalize_address(row['address'])
                    await conn.execute("""
                        UPDATE properties
                        SET address_normalized = $1
                        WHERE id = $2
                    """, normalized, row['id'])
                    updated += 1

        if updated % 10000 == 0:
            print(f"  Updated {updated:,} / {total:,} addresses...")

    print(f"\n✅ Normalized {updated:,} addresses")


async def show_stats(pool):
    """Show statistics about address normalization."""

    print("\n" + "="*70)
    print("NORMALIZATION STATISTICS")
    print("="*70)
    print()

    async with pool.acquire() as conn:
        # Total addresses
        total = await conn.fetchval("SELECT COUNT(*) FROM properties WHERE address IS NOT NULL")

        # Normalized
        normalized = await conn.fetchval("""
            SELECT COUNT(*) FROM properties
            WHERE address_normalized IS NOT NULL AND address_normalized != ''
        """)

        # Changed vs unchanged
        changed = await conn.fetchval("""
            SELECT COUNT(*) FROM properties
            WHERE address_normalized IS NOT NULL
            AND address_normalized != address
        """)

        unchanged = normalized - changed

        print(f"Total addresses: {total:,}")
        print(f"Normalized: {normalized:,} ({100*normalized/total:.1f}%)")
        print(f"  Changed: {changed:,} ({100*changed/normalized:.1f}% of normalized)")
        print(f"  Unchanged: {unchanged:,} ({100*unchanged/normalized:.1f}% of normalized)")
        print()

        # Sample improvements
        print("Sample improvements (addresses that changed most):")
        print("-" * 70)

        samples = await conn.fetch("""
            SELECT address, address_normalized
            FROM properties
            WHERE address_normalized IS NOT NULL
            AND address != address_normalized
            AND length(address) - length(address_normalized) > 10
            LIMIT 10
        """)

        for row in samples:
            print(f"Original:    {row['address'][:60]}")
            print(f"Normalized:  {row['address_normalized'][:60]}")
            print()


async def main():
    limit = None
    dry_run = "--dry-run" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     ADDRESS NORMALIZATION                                    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    if limit:
        print(f"Limit: {limit:,} addresses")
    print()

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set")
        sys.exit(1)

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    try:
        # Add column if needed
        if not dry_run:
            await add_normalized_column(pool)

        # Normalize addresses
        await normalize_all_addresses(pool, limit=limit, dry_run=dry_run)

        # Show stats
        if not dry_run:
            await show_stats(pool)

        print()
        print("="*70)
        print("COMPLETE")
        print("="*70)

        if dry_run:
            print("\nTo apply changes, run without --dry-run flag:")
            print("  python3 scripts/normalize_addresses.py")

    finally:
        await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
