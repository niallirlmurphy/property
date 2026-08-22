#!/usr/bin/env python3
"""
Apply Phase 1 valuation database schema to Supabase.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in backend/.env")
    sys.exit(1)

# Read schema SQL
schema_path = 'db/phase1_valuation_schema.sql'
try:
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
except FileNotFoundError:
    print(f"ERROR: Schema file not found: {schema_path}")
    sys.exit(1)

print(f"Connecting to database...")
print(f"URL: {DATABASE_URL[:50]}...")

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    print("\n" + "="*70)
    print("APPLYING PHASE 1 VALUATION SCHEMA")
    print("="*70)

    # Execute schema SQL
    cur.execute(schema_sql)

    print("\n✅ Schema applied successfully!")

    # Verify tables created
    print("\n" + "-"*70)
    print("VERIFYING TABLES...")
    print("-"*70)

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('valuation_requests', 'valuation_comparables')
        ORDER BY table_name;
    """)

    tables = cur.fetchall()
    for table in tables:
        print(f"✅ Table created: {table[0]}")

    # Verify materialized view
    cur.execute("""
        SELECT matviewname
        FROM pg_matviews
        WHERE schemaname = 'public'
        AND matviewname = 'county_monthly_price_indices';
    """)

    if cur.fetchone():
        print(f"✅ Materialized view created: county_monthly_price_indices")

    # Check price indices data
    print("\n" + "-"*70)
    print("PRICE INDICES STATISTICS")
    print("-"*70)

    cur.execute("""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT county) as counties,
            MIN(month) as earliest_month,
            MAX(month) as latest_month
        FROM county_monthly_price_indices;
    """)

    stats = cur.fetchone()
    print(f"Total rows: {stats[0]:,}")
    print(f"Counties: {stats[1]}")
    print(f"Earliest month: {stats[2]}")
    print(f"Latest month: {stats[3]}")

    # Show sample data
    print("\n" + "-"*70)
    print("SAMPLE PRICE INDICES (Top 5 Counties)")
    print("-"*70)

    cur.execute("""
        SELECT
            county,
            COUNT(*) as months,
            MIN(month) as from_month,
            MAX(month) as to_month,
            ROUND(AVG(price_index::numeric), 3) as avg_index
        FROM county_monthly_price_indices
        GROUP BY county
        ORDER BY months DESC
        LIMIT 5;
    """)

    print(f"{'County':<15} {'Months':<8} {'From':<12} {'To':<12} {'Avg Index'}")
    print("-"*70)
    for row in cur.fetchall():
        print(f"{row[0]:<15} {row[1]:<8} {str(row[2]):<12} {str(row[3]):<12} {row[4]}")

    # Verify functions created
    print("\n" + "-"*70)
    print("VERIFYING FUNCTIONS...")
    print("-"*70)

    cur.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name IN ('refresh_price_indices', 'get_county_price_index')
        ORDER BY routine_name;
    """)

    functions = cur.fetchall()
    for func in functions:
        print(f"✅ Function created: {func[0]}()")

    # Test get_county_price_index function
    print("\n" + "-"*70)
    print("TESTING FUNCTIONS...")
    print("-"*70)

    cur.execute("""
        SELECT get_county_price_index('Dublin', '2026-06-01'::DATE);
    """)

    result = cur.fetchone()
    if result:
        print(f"✅ get_county_price_index('Dublin', '2026-06-01') = {result[0]}")

    print("\n" + "="*70)
    print("✅ PHASE 1 SCHEMA APPLIED SUCCESSFULLY!")
    print("="*70)
    print("\nNext steps:")
    print("1. Create backend/valuation/ module structure")
    print("2. Implement geocoder, comparable search, adjustments")
    print("3. Build FastAPI endpoint")
    print("4. Create frontend ValuationPage")
    print("\nSee VALUATION_QUICK_START.md for detailed implementation guide.")

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"\n❌ DATABASE ERROR:")
    print(f"   {e}")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR:")
    print(f"   {e}")
    sys.exit(1)
