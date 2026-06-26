#!/usr/bin/env python3
"""
Apply BER rating migration to database.

Adds ber_rating column to properties table.
"""

import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv('backend/.env')


async def main():
    """Apply BER rating migration."""

    print("🔧 Applying BER rating migration...")

    # Connect to database
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    try:
        # Read migration file
        with open('db/migrations/002_add_ber_rating.sql', 'r') as f:
            migration_sql = f.read()

        # Execute migration
        print("📝 Executing migration SQL...")
        await conn.execute(migration_sql.split('-- Check results')[0])

        # Check results
        print("\n✅ Migration complete! Checking results...")
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_properties,
                COUNT(ber_rating) as with_ber,
                ROUND(100.0 * COUNT(ber_rating) / COUNT(*), 2) as ber_coverage_pct
            FROM properties;
        """)

        print(f"   Total properties: {result['total_properties']:,}")
        print(f"   With BER rating: {result['with_ber']:,} ({result['ber_coverage_pct']}%)")

        # Verify column exists
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'properties'
            AND column_name IN ('ber_rating', 'bedrooms', 'eircode');
        """)

        print("\n📊 Property enrichment columns:")
        for col in columns:
            print(f"   {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

        print("\n✨ Ready to receive crowdsourced data from valuation requests!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
