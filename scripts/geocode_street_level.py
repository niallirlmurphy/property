#!/usr/bin/env python3
"""
Geocode properties by finding street/development name patterns.
Matches properties on same street even if house numbers differ.
"""

import os
import re
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def extract_street_pattern(address):
    """
    Extract street/development name pattern from address.
    Examples:
      "No. 58, Balnagowan, Palmerstown Park" → "Balnagowan, Palmerstown Park"
      "43 Balnagowan, Palmerstown Park" → "Balnagowan, Palmerstown Park"
      "10 Main Street, Dublin" → "Main Street, Dublin"
    """
    # Remove leading house numbers and "No."
    pattern = re.sub(r'^(no\.?\s*)?(\d+[a-z]?\s*,?\s*)', '', address, flags=re.IGNORECASE)
    pattern = pattern.strip()

    # Must have at least 15 characters to be a meaningful pattern
    if len(pattern) < 15:
        return None

    return pattern

def main():
    print("╔══════════════════════════════════════════════════════════════╗", flush=True)
    print("║     STREET-LEVEL PATTERN MATCHING                            ║", flush=True)
    print("╚══════════════════════════════════════════════════════════════╝", flush=True)
    print(flush=True)

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set", flush=True)
        return 1

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        print("1. Finding street/development patterns from geocoded properties...", flush=True)
        print("   (This will take 2-3 minutes)", flush=True)
        print(flush=True)

        # Strategy: For each missing property, extract street pattern,
        # then find geocoded properties with the same pattern in same county

        cur.execute("""
            WITH missing_patterns AS (
                SELECT
                    id,
                    address,
                    county,
                    -- Remove house number prefix to get street pattern
                    TRIM(REGEXP_REPLACE(
                        REGEXP_REPLACE(address, '^no\\.?\\s*', '', 'i'),
                        '^\\d+[a-z]?\\s*,?\\s*',
                        '',
                        'i'
                    )) as street_pattern
                FROM properties
                WHERE latitude IS NULL
                AND address IS NOT NULL
                AND county IS NOT NULL
                AND LENGTH(address) > 20  -- Must have meaningful address
            ),
            geocoded_patterns AS (
                SELECT
                    county,
                    TRIM(REGEXP_REPLACE(
                        REGEXP_REPLACE(address, '^no\\.?\\s*', '', 'i'),
                        '^\\d+[a-z]?\\s*,?\\s*',
                        '',
                        'i'
                    )) as street_pattern,
                    AVG(latitude) as avg_lat,
                    AVG(longitude) as avg_lon,
                    COUNT(*) as geocoded_count
                FROM properties
                WHERE latitude IS NOT NULL
                AND county IS NOT NULL
                GROUP BY county, street_pattern
                HAVING COUNT(*) >= 2  -- Need at least 2 properties for confidence
            )
            SELECT
                mp.id,
                mp.address,
                mp.county,
                gp.avg_lat,
                gp.avg_lon,
                gp.geocoded_count,
                mp.street_pattern
            FROM missing_patterns mp
            JOIN geocoded_patterns gp
                ON mp.county = gp.county
                AND LOWER(mp.street_pattern) = LOWER(gp.street_pattern)
            WHERE LENGTH(mp.street_pattern) >= 15  -- Meaningful street name
            LIMIT 50000
        """)

        matches = cur.fetchall()

        print(f"✅ Found {len(matches):,} properties with matching street patterns!", flush=True)
        print(flush=True)

        if len(matches) == 0:
            print("No street-level matches found.", flush=True)
            return 0

        # Show samples
        print("Sample matches:", flush=True)
        for i, (prop_id, addr, county, lat, lon, count, pattern) in enumerate(matches[:10]):
            print(f"  {i+1}. {addr[:50]:<50}", flush=True)
            print(f"     Pattern: '{pattern[:45]}' ({count} geocoded props)", flush=True)
            print(f"     → ({lat:.6f}, {lon:.6f})", flush=True)

        if len(matches) > 10:
            print(f"  ... and {len(matches)-10:,} more", flush=True)
        print(flush=True)

        # Group by pattern confidence
        high_conf = [m for m in matches if m[5] >= 5]  # 5+ geocoded properties
        med_conf = [m for m in matches if 2 <= m[5] < 5]

        print(f"Match confidence:", flush=True)
        print(f"  High (5+ existing properties): {len(high_conf):,}", flush=True)
        print(f"  Medium (2-4 existing properties): {len(med_conf):,}", flush=True)
        print(flush=True)

        # Auto-apply
        print(f"Applying coordinates to {len(matches):,} properties...", flush=True)
        print(flush=True)

        print("2. Applying street-level coordinates...", flush=True)

        batch_size = 1000
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i+batch_size]

            # Batch update
            values = ','.join(
                f"({prop_id},{lat},{lon})"
                for prop_id, _, _, lat, lon, _, _ in batch
            )

            cur.execute(f"""
                UPDATE properties p
                SET
                    latitude = m.lat,
                    longitude = m.lon,
                    geog = ST_SetSRID(ST_MakePoint(m.lon, m.lat), 4326)::geography,
                    needs_geocoding = FALSE
                FROM (VALUES {values}) AS m(id, lat, lon)
                WHERE p.id = m.id::bigint
            """)

            conn.commit()
            print(f"   Updated {min(i+batch_size, len(matches)):,}/{len(matches):,}", flush=True)

        print(flush=True)
        print("="*70, flush=True)
        print("STREET-LEVEL GEOCODING COMPLETE", flush=True)
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
