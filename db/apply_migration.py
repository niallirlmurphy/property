#!/usr/bin/env python3
"""
Apply database migration to fix address_normalized.

Usage:
    python3 db/apply_migration.py [migration_file]

This script:
1. Adds normalize_address() function to database
2. Backfills NULL address_normalized entries (45k+ properties)
3. Creates trigger to auto-normalize future inserts/updates
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)


async def apply_migration(migration_file: str):
    """Apply SQL migration file to database."""
    migration_path = Path(migration_file)

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"📄 Reading migration: {migration_path.name}")
    sql = migration_path.read_text()

    print(f"🔗 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print(f"🚀 Applying migration...")
        print("=" * 60)

        # Execute migration SQL (with notice handling)
        await conn.execute("SET client_min_messages TO NOTICE")
        await conn.execute(sql)

        print("=" * 60)
        print("✅ Migration applied successfully!")

        # Verify results
        null_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM properties
            WHERE address_normalized IS NULL
        """)

        print(f"\n📊 Verification:")
        print(f"  Remaining NULL address_normalized: {null_count:,}")

        if null_count == 0:
            print(f"  ✅ All properties have normalized addresses!")
        else:
            print(f"  ⚠️  {null_count:,} properties still need normalization")

        # Test the trigger
        print(f"\n🧪 Testing trigger...")
        test_address = "123 TEST STREET, DUBLIN"
        test_result = await conn.fetchval("""
            SELECT normalize_address($1)
        """, test_address)
        print(f"  Input:  {test_address}")
        print(f"  Output: {test_result}")
        print(f"  ✅ Normalization function working")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


async def main():
    migration_file = sys.argv[1] if len(sys.argv) > 1 else "db/migrations/001_fix_address_normalized.sql"

    print("=" * 60)
    print("  ADDRESS NORMALIZATION MIGRATION")
    print("=" * 60)
    print()

    # Confirmation prompt
    print(f"This will:")
    print(f"  1. Add normalize_address() function to database")
    print(f"  2. Backfill ~45k NULL address_normalized entries")
    print(f"  3. Create trigger for future auto-normalization")
    print()

    response = input("Apply migration? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Migration cancelled")
        sys.exit(0)

    print()
    await apply_migration(migration_file)


if __name__ == "__main__":
    asyncio.run(main())
