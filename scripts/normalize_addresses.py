#!/usr/bin/env python3
"""
Normalize all addresses in the properties table for better geocoding and enrichment.

Creates a new 'address_normalized' column with cleaned addresses that:
- Are more likely to match in geocoding APIs (Nominatim, Mapbox, Autoaddress)
- Follow consistent formatting rules
- Preserve the original address for display/legal purposes

Usage:
    python3 scripts/normalize_addresses.py [--limit N] [--dry-run]
    python3 scripts/normalize_addresses.py --recheck [--apply]

--recheck re-runs the normalizer over every row and rewrites the ones whose stored
value no longer matches (after a rule change). Dry run unless --apply.
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from address_normalize import normalize_address  # noqa: E402

DATABASE_URL = os.environ.get("DATABASE_URL")


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


async def recheck_all_addresses(pool, apply=False):
    """Rewrite address_normalized wherever the current rules give a different value."""
    CHUNK = 5000
    last_id, scanned, changes = 0, 0, []
    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '30s'")
        while True:
            rows = await conn.fetch("""
                SELECT id, address, address_normalized FROM properties
                WHERE id > $1 AND address IS NOT NULL
                ORDER BY id LIMIT $2
            """, last_id, CHUNK)
            if not rows:
                break
            last_id = rows[-1]['id']
            scanned += len(rows)
            for r in rows:
                new = normalize_address(r['address'])
                if new != r['address_normalized']:
                    changes.append((r['id'], r['address_normalized'], new))
            if scanned % 100000 < CHUNK:
                print(f"  scanned {scanned:,}, {len(changes):,} to change")

        print(f"\nScanned {scanned:,} rows; {len(changes):,} would change")
        for _, old, new in changes[:25]:
            print(f"  {old}  →  {new}")
        if not apply:
            print("\nDry run. Re-run with --apply to write.")
            return

        for i in range(0, len(changes), 1000):
            batch = changes[i:i + 1000]
            await conn.execute("""
                UPDATE properties p SET address_normalized = v.new
                FROM unnest($1::bigint[], $2::text[]) AS v(id, new)
                WHERE p.id = v.id
            """, [c[0] for c in batch], [c[2] for c in batch])
            print(f"  updated {min(i + 1000, len(changes)):,} / {len(changes):,}")
            await asyncio.sleep(0.5)  # spread the writes out for the Disk IO budget
        print(f"\n✅ Rewrote {len(changes):,} addresses")


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

    if "--recheck" in sys.argv:
        try:
            await recheck_all_addresses(pool, apply="--apply" in sys.argv)
        finally:
            await pool.close()
        return

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
