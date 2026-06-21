#!/usr/bin/env python3
"""
Standardize coordinates for properties at the same address.
Uses the most recent sale's coordinates as the canonical version.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Find addresses with multiple coordinate values
cur.execute("""
    WITH address_coords AS (
        SELECT
            address_normalized,
            latitude,
            longitude,
            COUNT(*) as property_count,
            MAX(sale_date) as most_recent_sale
        FROM properties
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        GROUP BY address_normalized, latitude, longitude
    ),
    addresses_with_multiple_coords AS (
        SELECT
            address_normalized,
            COUNT(DISTINCT (latitude, longitude)) as coord_variations
        FROM address_coords
        GROUP BY address_normalized
        HAVING COUNT(DISTINCT (latitude, longitude)) > 1
    )
    SELECT
        ac.address_normalized,
        ac.latitude,
        ac.longitude,
        ac.property_count,
        ac.most_recent_sale,
        CASE WHEN ac.most_recent_sale = (
            SELECT MAX(most_recent_sale)
            FROM address_coords ac2
            WHERE ac2.address_normalized = ac.address_normalized
        ) THEN true ELSE false END as is_most_recent
    FROM address_coords ac
    WHERE ac.address_normalized IN (
        SELECT address_normalized FROM addresses_with_multiple_coords
    )
    ORDER BY ac.address_normalized, ac.most_recent_sale DESC
""")

address_map = {}
for row in cur.fetchall():
    addr, lat, lon, count, date, is_most_recent = row
    if addr not in address_map:
        address_map[addr] = []
    address_map[addr].append({
        'lat': lat,
        'lon': lon,
        'count': count,
        'date': date,
        'is_most_recent': is_most_recent
    })

print(f"Found {len(address_map)} addresses with coordinate variations")

# For each address, update all properties to use the most recent coordinates
updated_count = 0
for addr, coords in address_map.items():
    # Get the most recent coordinates
    canonical = [c for c in coords if c['is_most_recent']][0]
    canonical_lat = canonical['lat']
    canonical_lon = canonical['lon']

    # Update all properties at this address to use canonical coordinates
    cur.execute("""
        UPDATE properties
        SET
            latitude = %s,
            longitude = %s,
            geog = ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
        WHERE address_normalized = %s
          AND (latitude != %s OR longitude != %s)
    """, (canonical_lat, canonical_lon, canonical_lon, canonical_lat, addr, canonical_lat, canonical_lon))

    rows_updated = cur.rowcount
    if rows_updated > 0:
        updated_count += rows_updated
        print(f"  {addr[:60]}: updated {rows_updated} properties to ({canonical_lat:.6f}, {canonical_lon:.6f})")

conn.commit()
print(f"\nTotal properties updated: {updated_count}")
conn.close()
