#!/usr/bin/env python3
"""Batch Eircode backfill for resale addresses"""

import os
import psycopg2
from dotenv import load_dotenv
import time

load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print('Batched Eircode Backfill - Resales Only')
print('=' * 70)
print()

# Get list of (address, eircode) pairs to backfill
print('Finding addresses to backfill...')
start = time.time()
cur.execute('''
    WITH resale_addresses AS (
        SELECT address_normalized
        FROM properties
        WHERE address_normalized IS NOT NULL
        GROUP BY address_normalized
        HAVING COUNT(*) > 1
    ),
    address_eircodes AS (
        SELECT
            p.address_normalized,
            p.eircode
        FROM properties p
        JOIN resale_addresses ra ON p.address_normalized = ra.address_normalized
        WHERE p.eircode IS NOT NULL
          AND p.sale_date >= '2022-01-01'
        GROUP BY p.address_normalized, p.eircode
    )
    SELECT address_normalized, eircode
    FROM address_eircodes
    WHERE address_normalized IN (
        SELECT address_normalized
        FROM address_eircodes
        GROUP BY address_normalized
        HAVING COUNT(*) = 1
    )
''')

backfill_pairs = cur.fetchall()
print(f'Found {len(backfill_pairs):,} addresses with unique Eircodes ({time.time()-start:.1f}s)')
print()

# Process in batches
BATCH_SIZE = 500
total_updated = 0

print(f'Processing in batches of {BATCH_SIZE}...')
start_time = time.time()

for i in range(0, len(backfill_pairs), BATCH_SIZE):
    batch = backfill_pairs[i:i+BATCH_SIZE]

    # Use parameterized query to avoid SQL injection
    for addr_norm, eircode in batch:
        cur.execute('''
            UPDATE properties
            SET eircode = %s
            WHERE address_normalized = %s
              AND eircode IS NULL
        ''', (eircode, addr_norm))
        total_updated += cur.rowcount

    conn.commit()

    if (i + BATCH_SIZE) % 1000 == 0:
        elapsed = time.time() - start_time
        rate = total_updated / elapsed
        remaining = len(backfill_pairs) - (i + BATCH_SIZE)
        eta = remaining / ((i + BATCH_SIZE) / elapsed)
        print(f'   {i + BATCH_SIZE:,} / {len(backfill_pairs):,} addresses | {total_updated:,} properties updated | ETA: {eta/60:.1f}min')

print()
print(f'✅ COMPLETE: Updated {total_updated:,} properties across {len(backfill_pairs):,} addresses')
print(f'   Total time: {(time.time()-start_time)/60:.1f} minutes')
print()

# Show new stats
cur.execute('''
    SELECT
        COUNT(*) as total,
        COUNT(eircode) as with_eircode,
        ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct
    FROM properties
''')
total, with_eircode, pct = cur.fetchone()
print(f'📊 New Eircode coverage: {with_eircode:,} / {total:,} ({pct}%)')

cur.execute('''
    SELECT
        EXTRACT(YEAR FROM sale_date) as year,
        COUNT(*) as total,
        COUNT(eircode) as with_eircode,
        ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct
    FROM properties
    WHERE sale_date >= '2010-01-01'
    GROUP BY year
    ORDER BY year DESC
''')
print(f'\nCoverage by year (2010+):')
for year, total, with_eircode, pct in cur.fetchall():
    print(f'  {int(year)}: {with_eircode:,} / {total:,} ({pct}%)')

conn.close()
print()
print('=' * 70)
