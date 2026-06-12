#!/usr/bin/env python3
"""
Setup Eircode Reference Database

Creates a reference table mapping Eircodes to coordinates from existing PPR data.
This provides fast geocoding for all Eircodes in the database without external API calls.

Usage:
    python3 scripts/setup_eircode_reference.py
    python3 scripts/setup_eircode_reference.py --rebuild  # Drop and recreate
"""

import os
import sys
import psycopg2
import argparse
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    parser = argparse.ArgumentParser(description='Setup Eircode reference database')
    parser.add_argument('--rebuild', action='store_true', help='Drop existing table and rebuild')
    args = parser.parse_args()

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        sys.exit(1)

    print("🔗 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Drop existing table if rebuild requested
        if args.rebuild:
            print("🗑️  Dropping existing eircode_reference table...")
            cur.execute("DROP TABLE IF EXISTS eircode_reference CASCADE")
            conn.commit()

        # Check if table already exists
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'eircode_reference'
        """)
        table_exists = cur.fetchone()[0] > 0

        if table_exists and not args.rebuild:
            print("ℹ️  eircode_reference table already exists")
            print("   Use --rebuild to drop and recreate")

            # Show current stats
            cur.execute("SELECT COUNT(*) FROM eircode_reference")
            count = cur.fetchone()[0]
            print(f"\n📊 Current data: {count:,} Eircodes")

        else:
            print("📄 Reading SQL script...")
            with open('db/create_eircode_reference.sql', 'r') as f:
                sql = f.read()

            print("🔧 Creating eircode_reference table...")
            cur.execute(sql)
            conn.commit()

            # Get statistics
            cur.execute("SELECT COUNT(*) FROM eircode_reference")
            total_eircodes = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(DISTINCT routing_key)
                FROM eircode_reference
            """)
            routing_keys = cur.fetchone()[0]

            cur.execute("""
                SELECT SUM(property_count)
                FROM eircode_reference
            """)
            total_properties = cur.fetchone()[0]

            cur.execute("""
                SELECT
                    routing_key,
                    COUNT(*) as eircode_count,
                    SUM(property_count) as props
                FROM eircode_reference
                GROUP BY routing_key
                ORDER BY props DESC
                LIMIT 10
            """)
            top_routing_keys = cur.fetchall()

            print("\n✅ Eircode reference database created successfully!")
            print(f"\n📊 Statistics:")
            print(f"   Total unique Eircodes: {total_eircodes:,}")
            print(f"   Total routing keys: {routing_keys}")
            print(f"   Properties with Eircodes: {total_properties:,}")
            print(f"   Coverage: {total_properties/784854*100:.1f}% of PPR database")

            print(f"\n🔝 Top 10 routing keys by property count:")
            for rk, count, props in top_routing_keys:
                print(f"   {rk}: {count:>4} Eircodes, {props:>6,} properties")

            # Test the function
            print(f"\n🧪 Testing geocoding function...")
            test_cases = ['D02 XY45', 'D02', 'H91 XY12']
            for test in test_cases:
                cur.execute("SELECT * FROM get_eircode_coordinates(%s)", (test,))
                result = cur.fetchone()
                if result:
                    lat, lon, source, confidence = result
                    print(f"   {test:12} → ({lat:.5f}, {lon:.5f}) [{source}, {confidence} confidence]")
                else:
                    print(f"   {test:12} → Not found")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

    print("\n✨ Setup complete!")

if __name__ == "__main__":
    main()
