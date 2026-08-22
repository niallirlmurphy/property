#!/usr/bin/env python3
"""
Central duplicate handling module for applying data updates to all sales of the same property.

When we update one sale (geocoding, enrichment, etc.), this module automatically
finds and updates all other sales of the same address.
"""

import psycopg2
from typing import Optional, Tuple, List

def find_duplicate_sales(conn, address: str, exclude_id: Optional[int] = None) -> List[dict]:
    """
    Find all sales of the same property address.

    Args:
        conn: Database connection
        address: Property address to match
        exclude_id: Optional property ID to exclude from results

    Returns:
        List of dicts with id, address, sale_date for each duplicate
    """
    cur = conn.cursor()

    if exclude_id:
        cur.execute("""
            SELECT id, address, sale_date, price
            FROM properties
            WHERE address = %s AND id != %s
            ORDER BY sale_date DESC
        """, (address, exclude_id))
    else:
        cur.execute("""
            SELECT id, address, sale_date, price
            FROM properties
            WHERE address = %s
            ORDER BY sale_date DESC
        """, (address,))

    duplicates = []
    for row in cur.fetchall():
        duplicates.append({
            'id': row[0],
            'address': row[1],
            'sale_date': row[2],
            'price': row[3]
        })

    return duplicates


def update_geocoding_for_duplicates(
    conn,
    address: str,
    latitude: float,
    longitude: float,
    eircode: Optional[str] = None
) -> int:
    """
    Update geocoding data (coordinates and optional Eircode) for all sales of an address.

    Args:
        conn: Database connection
        address: Property address
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        eircode: Optional Eircode to set

    Returns:
        Number of properties updated
    """
    cur = conn.cursor()

    # Find all sales needing this geocoding
    cur.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE address = %s
          AND (latitude IS NULL OR longitude IS NULL OR eircode IS NULL)
    """, (address,))

    count_before = cur.fetchone()[0]

    if count_before == 0:
        return 0

    # Update coordinates for all matching addresses
    if eircode:
        cur.execute("""
            UPDATE properties
            SET latitude = %s,
                longitude = %s,
                eircode = COALESCE(eircode, %s)
            WHERE address = %s
              AND (latitude IS NULL OR longitude IS NULL OR eircode IS NULL)
        """, (latitude, longitude, eircode, address))
    else:
        cur.execute("""
            UPDATE properties
            SET latitude = %s,
                longitude = %s
            WHERE address = %s
              AND (latitude IS NULL OR longitude IS NULL)
        """, (latitude, longitude, address))

    conn.commit()

    # Return count of updated properties
    return cur.rowcount


def update_enrichment_for_duplicates(
    conn,
    address: str,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None
) -> int:
    """
    Update enrichment data (bedrooms, property_type) for all sales of an address.

    Args:
        conn: Database connection
        address: Property address
        bedrooms: Number of bedrooms
        property_type: Property type (e.g., 'terraced', 'apartment')

    Returns:
        Number of properties updated
    """
    cur = conn.cursor()

    if not bedrooms and not property_type:
        return 0

    # Build dynamic update query
    updates = []
    params = []

    if bedrooms is not None:
        updates.append("bedrooms = %s")
        params.append(bedrooms)

    if property_type is not None:
        updates.append("property_type = %s")
        params.append(property_type)

    params.append(address)

    # Update all matching addresses that are missing the data
    query = f"""
        UPDATE properties
        SET {', '.join(updates)}
        WHERE address = %s
          AND (bedrooms IS NULL OR property_type IS NULL)
    """

    cur.execute(query, params)
    conn.commit()

    return cur.rowcount


def update_all_fields_for_duplicates(
    conn,
    address: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    eircode: Optional[str] = None,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None
) -> Tuple[int, int]:
    """
    Update all available data for all sales of an address.

    Args:
        conn: Database connection
        address: Property address
        latitude: Optional latitude coordinate
        longitude: Optional longitude coordinate
        eircode: Optional Eircode
        bedrooms: Optional number of bedrooms
        property_type: Optional property type

    Returns:
        Tuple of (geocoding_updates, enrichment_updates)
    """
    geo_count = 0
    enrich_count = 0

    # Update geocoding if provided
    if latitude is not None and longitude is not None:
        geo_count = update_geocoding_for_duplicates(
            conn, address, latitude, longitude, eircode
        )

    # Update enrichment if provided
    if bedrooms is not None or property_type is not None:
        enrich_count = update_enrichment_for_duplicates(
            conn, address, bedrooms, property_type
        )

    return geo_count, enrich_count


def get_duplicate_statistics(conn, address: str) -> dict:
    """
    Get statistics about sales for a given address.

    Args:
        conn: Database connection
        address: Property address

    Returns:
        Dict with statistics (total_sales, with_coords, with_enrichment, etc.)
    """
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) as with_coords,
            COUNT(*) FILTER (WHERE bedrooms IS NOT NULL AND property_type IS NOT NULL) as with_enrichment,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL) as with_eircode,
            MIN(sale_date) as first_sale,
            MAX(sale_date) as latest_sale,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM properties
        WHERE address = %s
    """, (address,))

    row = cur.fetchone()

    return {
        'total_sales': row[0],
        'with_coords': row[1],
        'with_enrichment': row[2],
        'with_eircode': row[3],
        'first_sale': row[4],
        'latest_sale': row[5],
        'min_price': row[6],
        'max_price': row[7],
        'coord_coverage': (row[1] / row[0] * 100) if row[0] > 0 else 0,
        'enrichment_coverage': (row[2] / row[0] * 100) if row[0] > 0 else 0
    }


# Example usage
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv('backend/.env')
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Test with a known address
    test_address = "28 SLANE RD, CRUMLIN, DUBLIN 12"

    conn = psycopg2.connect(DATABASE_URL)

    print(f"Testing duplicate handler with: {test_address}")
    print()

    # Get statistics
    stats = get_duplicate_statistics(conn, test_address)
    print(f"Total sales: {stats['total_sales']}")
    print(f"With coordinates: {stats['with_coords']} ({stats['coord_coverage']:.1f}%)")
    print(f"With enrichment: {stats['with_enrichment']} ({stats['enrichment_coverage']:.1f}%)")
    print(f"First sale: {stats['first_sale']}")
    print(f"Latest sale: {stats['latest_sale']}")
    print(f"Price range: €{stats['min_price']:,} - €{stats['max_price']:,}")

    # Find duplicates
    duplicates = find_duplicate_sales(conn, test_address)
    print(f"\nFound {len(duplicates)} sales:")
    for dup in duplicates:
        print(f"  {dup['sale_date'].strftime('%Y-%m-%d')}: €{dup['price']:,}")

    conn.close()
