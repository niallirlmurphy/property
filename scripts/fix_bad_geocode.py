#!/usr/bin/env python3
"""
Remove incorrect coordinates for a specific property.

Usage:
    python3 scripts/fix_bad_geocode.py "MOUNT CARMEL, CROOKSHANE, RATHCOOLE"
    python3 scripts/fix_bad_geocode.py --id 123456
"""

import psycopg2
import argparse
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')


def find_property(address_pattern: str = None, property_id: int = None):
    """Find properties matching the pattern."""
    DATABASE_URL = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        if property_id:
            cur.execute('''
                SELECT id, address, county, latitude, longitude, eircode, sale_date, price
                FROM properties
                WHERE id = %s
            ''', (property_id,))
        else:
            cur.execute('''
                SELECT id, address, county, latitude, longitude, eircode, sale_date, price
                FROM properties
                WHERE address ILIKE %s
            ''', (f'%{address_pattern}%',))

        results = cur.fetchall()

        if not results:
            print(f"✗ No properties found matching: {address_pattern or property_id}")
            return []

        print(f"Found {len(results)} properties:")
        print()

        for row in results:
            print(f"ID: {row[0]}")
            print(f"Address: {row[1]}")
            print(f"County: {row[2]}")
            print(f"Coordinates: ({row[3]}, {row[4]})")
            print(f"Eircode: {row[5]}")
            print(f"Sale Date: {row[6]}")
            print(f"Price: €{row[7]:,.2f}")
            print("-" * 60)

        return results

    finally:
        cur.close()
        conn.close()


def remove_coordinates(property_id: int, dry_run: bool = False):
    """Remove coordinates for a specific property."""
    DATABASE_URL = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Get current data
        cur.execute('''
            SELECT id, address, latitude, longitude
            FROM properties
            WHERE id = %s
        ''', (property_id,))

        result = cur.fetchone()
        if not result:
            print(f"✗ Property ID {property_id} not found")
            return

        print(f"Property: {result[1]}")
        print(f"Current coordinates: ({result[2]}, {result[3]})")
        print()

        if dry_run:
            print("DRY RUN - Would execute:")
            print(f"UPDATE properties SET latitude = NULL, longitude = NULL, geog = NULL, needs_geocoding = TRUE WHERE id = {property_id};")
            print()
            print("Run without --dry-run to apply changes")
            return

        # Remove coordinates
        cur.execute('''
            UPDATE properties
            SET latitude = NULL,
                longitude = NULL,
                geog = NULL,
                needs_geocoding = TRUE
            WHERE id = %s
        ''', (property_id,))

        conn.commit()

        print(f"✓ Removed coordinates for property ID {property_id}")
        print(f"✓ Set needs_geocoding = TRUE")
        print()
        print("This property will be re-geocoded in the next batch geocoding run.")

    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Fix incorrectly geocoded property")
    parser.add_argument("address", nargs="?", help="Address pattern to search for")
    parser.add_argument("--id", type=int, help="Property ID to update directly")
    parser.add_argument("--remove", action="store_true", help="Remove coordinates (requires --id)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    if not args.address and not args.id:
        parser.error("Must provide either address pattern or --id")

    # Search for properties
    if args.address or (args.id and not args.remove):
        results = find_property(args.address, args.id)

        if not results:
            return

        if len(results) == 1 and not args.remove:
            print()
            print("To remove coordinates for this property, run:")
            print(f"python3 scripts/fix_bad_geocode.py --id {results[0][0]} --remove")
        elif len(results) > 1 and not args.remove:
            print()
            print("Multiple properties found. To remove coordinates, run:")
            print("python3 scripts/fix_bad_geocode.py --id <ID> --remove")

    # Remove coordinates
    if args.remove:
        if not args.id:
            parser.error("--remove requires --id")

        remove_coordinates(args.id, args.dry_run)


if __name__ == "__main__":
    main()
