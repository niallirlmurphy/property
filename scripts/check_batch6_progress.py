#!/usr/bin/env python3
"""Check Batch 6 enrichment progress by querying the database."""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def check_progress():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Check current status
    cur.execute("""
        SELECT
            COUNT(*) as total_2026,
            COUNT(*) FILTER (WHERE bedrooms IS NULL AND property_type IS NULL) as no_enrichment,
            COUNT(*) FILTER (WHERE bedrooms IS NOT NULL AND property_type IS NOT NULL) as fully_enriched,
            COUNT(*) FILTER (
                WHERE (bedrooms IS NOT NULL AND property_type IS NULL)
                   OR (bedrooms IS NULL AND property_type IS NOT NULL)
            ) as partially_enriched
        FROM properties
        WHERE EXTRACT(YEAR FROM sale_date) = 2026
    """)

    total, missing, fully, partial = cur.fetchone()

    print("=" * 60)
    print(f"BATCH 6 PROGRESS CHECK - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print(f"Total 2026 sales: {total:,}")
    print(f"Fully enriched: {fully:,} ({fully/total*100:.1f}%)")
    print(f"Partially enriched: {partial:,} ({partial/total*100:.1f}%)")
    print(f"Not enriched: {missing:,} ({missing/total*100:.1f}%)")
    print()

    # Progress vs target
    target = 702
    enriched_since_start = target - missing
    print(f"Target: {target} properties")
    print(f"Enriched so far: {enriched_since_start}")
    print(f"Remaining: {missing}")

    if enriched_since_start > 0:
        print(f"Progress: {enriched_since_start/target*100:.1f}%")

    # Breakdown by month
    print()
    print("By month:")
    cur.execute("""
        SELECT
            TO_CHAR(sale_date, 'YYYY-MM') as month,
            COUNT(*) FILTER (WHERE bedrooms IS NULL AND property_type IS NULL) as missing
        FROM properties
        WHERE EXTRACT(YEAR FROM sale_date) = 2026
        GROUP BY TO_CHAR(sale_date, 'YYYY-MM')
        ORDER BY month DESC
    """)

    for month, missing_count in cur.fetchall():
        print(f"  {month}: {missing_count} properties still need enrichment")

    conn.close()

if __name__ == '__main__':
    check_progress()
