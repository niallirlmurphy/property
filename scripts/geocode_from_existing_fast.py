#!/usr/bin/env python3
"""
Fast geocoding by matching against existing addresses.
Uses efficient SQL with proper indexing and batching.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    print("╔══════════════════════════════════════════════════════════════╗", flush=True)
    print("║     FAST GEOCODING FROM EXISTING MATCHES                     ║", flush=True)
    print("╚══════════════════════════════════════════════════════════════╝", flush=True)
    print(flush=True)

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set", flush=True)
        return 1

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Strategy: Use a single efficient SQL query to find exact matches
        # by joining on normalized addresses within the same county

        print("1. Finding exact address matches (this may take 2-3 minutes)...", flush=True)
        print("   Using normalized address matching in same county", flush=True)
        print(flush=True)

        # Create a single query that does all the matching
        cur.execute("""
            WITH missing AS (
                SELECT id, address, county
                FROM properties
                WHERE latitude IS NULL
                AND address IS NOT NULL
                AND county IS NOT NULL
                LIMIT 10000
            ),
            normalized_missing AS (
                SELECT
                    id,
                    address,
                    county,
                    LOWER(REGEXP_REPLACE(REGEXP_REPLACE(address, '[.,\\-]', ' ', 'g'), '\\s+', ' ', 'g')) as norm_addr
                FROM missing
            ),
            geocoded_normalized AS (
                SELECT DISTINCT ON (county, norm_addr)
                    county,
                    LOWER(REGEXP_REPLACE(REGEXP_REPLACE(address, '[.,\\-]', ' ', 'g'), '\\s+', ' ', 'g')) as norm_addr,
                    latitude,
                    longitude
                FROM properties
                WHERE latitude IS NOT NULL
                AND county IS NOT NULL
            )
            SELECT
                nm.id,
                gn.latitude,
                gn.longitude,
                nm.address
            FROM normalized_missing nm
            JOIN geocoded_normalized gn
                ON nm.county = gn.county
                AND nm.norm_addr = gn.norm_addr
        """)

        matches = cur.fetchall()

        print(f"✅ Found {len(matches):,} exact matches!", flush=True)
        print(flush=True)

        if len(matches) == 0:
            print("No matches found. Properties may need external geocoding.", flush=True)
            return 0

        # Show sample matches
        print("Sample matches:", flush=True)
        for i, (prop_id, lat, lon, address) in enumerate(matches[:5]):
            print(f"  {i+1}. {address[:60]:<60} → ({lat:.6f}, {lon:.6f})", flush=True)
        if len(matches) > 5:
            print(f"  ... and {len(matches)-5:,} more", flush=True)
        print(flush=True)

        # Auto-apply (comment out to require confirmation)
        print(f"Applying coordinates to {len(matches):,} properties...", flush=True)

        # Apply updates in batches
        print(flush=True)
        print(f"2. Applying coordinates to {len(matches):,} properties...", flush=True)

        batch_size = 1000
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i+batch_size]

            # Use UPDATE ... FROM for efficient batch update
            cur.execute("""
                UPDATE properties p
                SET
                    latitude = m.lat,
                    longitude = m.lon,
                    geog = ST_SetSRID(ST_MakePoint(m.lon, m.lat), 4326)::geography,
                    needs_geocoding = FALSE
                FROM (VALUES %s) AS m(id, lat, lon)
                WHERE p.id = m.id::bigint
            """ % ','.join(f"({prop_id},{lat},{lon})" for prop_id, lat, lon, _ in batch))

            conn.commit()
            print(f"   Updated {min(i+batch_size, len(matches)):,}/{len(matches):,}", flush=True)

        print(flush=True)
        print("="*70, flush=True)
        print("GEOCODING COMPLETE", flush=True)
        print("="*70, flush=True)
        print(flush=True)

        # Show final stats
        cur.execute('SELECT COUNT(*), COUNT(latitude) FROM properties')
        total, geocoded = cur.fetchone()
        print(f"Final stats:", flush=True)
        print(f"  Total properties: {total:,}", flush=True)
        print(f"  Geocoded: {geocoded:,} ({100*geocoded/total:.1f}%)", flush=True)
        print(f"  Missing: {total-geocoded:,} ({100*(total-geocoded)/total:.1f}%)", flush=True)

    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
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
