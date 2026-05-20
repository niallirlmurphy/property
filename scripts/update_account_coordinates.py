#!/usr/bin/env python3
"""
Update Salesforce Account records with geocoded coordinates.

Reads PPR-ALL-geocoded.csv and updates the corresponding Account records
with BillingLatitude and BillingLongitude values.

This populates the standard Salesforce geocoding fields so that:
- Records show on Salesforce Maps
- Can use geo-queries in reports
- Enables location-based features

Usage:
    python3 scripts/update_account_coordinates.py [--limit N] [--batch-size N]
"""

import subprocess
import json
import csv
import sys
import os
from datetime import datetime

PPR_GEOCODED_CSV = "PPR-ALL-geocoded.csv"
IMPORT_DATE = datetime.now().strftime("%Y-%m-%d")
BATCH_SIZE = 200


def run_sf_command(command):
    """Run Salesforce CLI command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def check_connection():
    """Verify Salesforce connection."""
    print("Checking Salesforce connection...")
    stdout, stderr, code = run_sf_command("sf org display --json")

    if code != 0:
        print("✗ Not connected. Run: sf org login web")
        return None

    org_data = json.loads(stdout)
    print(f"✓ Connected to: {org_data['result']['username']}")
    return org_data["result"]


def get_account_name_to_id_mapping(import_date):
    """Get mapping of Account Name → Id for imported records."""
    print(f"\nFetching Account IDs for records with PPR_Import__c = '{import_date}'...")

    query = f"SELECT Id, Name FROM Account WHERE PPR_Import__c = '{import_date}'"
    stdout, stderr, code = run_sf_command(f'sf data query --query "{query}" --json')

    if code != 0:
        print(f"✗ Query failed: {stderr}")
        return {}

    result = json.loads(stdout)
    records = result.get("result", {}).get("records", [])

    name_to_id = {}
    for record in records:
        # Use Name as key (should match Address from CSV)
        name_to_id[record["Name"]] = record["Id"]

    print(f"✓ Found {len(name_to_id):,} Account records")
    return name_to_id


def read_coordinates_from_csv(name_to_id, limit=None):
    """Read coordinates from geocoded CSV for accounts we have."""
    print(f"\nReading coordinates from {PPR_GEOCODED_CSV}...")

    updates = []

    with open(PPR_GEOCODED_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if limit and len(updates) >= limit:
                break

            address = row.get('Address', '').strip()[:80]  # Match Name field truncation
            latitude = row.get('Latitude', '').strip()
            longitude = row.get('Longitude', '').strip()

            # Skip if no coordinates
            if not latitude or not longitude:
                continue

            # Check if we have this account
            account_id = name_to_id.get(address)
            if not account_id:
                continue

            try:
                lat = float(latitude)
                lon = float(longitude)

                # Validate Ireland bounds
                if not (51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4):
                    continue

                updates.append({
                    'Id': account_id,
                    'BillingLatitude': lat,
                    'BillingLongitude': lon
                })

            except ValueError:
                continue

    print(f"✓ Found coordinates for {len(updates):,} accounts")
    return updates


def create_update_csv(updates, output_file="/tmp/account_coords_update.csv"):
    """Create CSV for bulk update."""
    if not updates:
        return None

    with open(output_file, 'wb') as f:
        # Write header
        header = "Id,BillingLatitude,BillingLongitude\n"
        f.write(header.encode('utf-8'))

        # Write rows
        for record in updates:
            row = f"{record['Id']},{record['BillingLatitude']},{record['BillingLongitude']}\n"
            f.write(row.encode('utf-8'))

    return output_file


def update_salesforce(csv_file):
    """Update Salesforce via bulk API."""
    print(f"\nUpdating Account coordinates in Salesforce...")

    cmd = f'sf data update bulk --sobject Account --file {csv_file} --wait 10'

    stdout, stderr, code = run_sf_command(cmd)
    print(stdout)

    if "Successful records:" in stdout:
        for line in stdout.split('\n'):
            if "Successful records:" in line:
                print(f"\n✓ Successfully updated coordinates!")
                return True

    return False


def verify_updates(import_date):
    """Verify coordinates were updated."""
    print(f"\nVerifying coordinate updates...")

    query = f"""SELECT COUNT()
                FROM Account
                WHERE PPR_Import__c = '{import_date}'
                AND BillingLatitude != null
                AND BillingLongitude != null"""

    stdout, stderr, code = run_sf_command(f'sf data query --query "{query}" 2>&1')

    if "Total number of records retrieved:" in stdout:
        for line in stdout.split('\n'):
            if "Total number of records retrieved:" in line:
                import re
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                count_str = clean_line.split(':')[1].strip().replace('.', '').replace(',', '')
                try:
                    count = int(count_str)
                    print(f"✓ {count:,} accounts now have coordinates")
                    return count
                except:
                    pass

    return 0


def main():
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     UPDATE ACCOUNT COORDINATES                               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if limit:
        print(f"Mode: LIMITED ({limit:,} records)")
    else:
        print("Mode: ALL imported records")

    print()

    # Check connection
    org_info = check_connection()
    if not org_info:
        sys.exit(1)

    # Get Account IDs
    name_to_id = get_account_name_to_id_mapping(IMPORT_DATE)
    if not name_to_id:
        print("\n✗ No imported accounts found")
        print(f"   Check that records exist with PPR_Import__c = '{IMPORT_DATE}'")
        sys.exit(1)

    # Read coordinates from CSV
    updates = read_coordinates_from_csv(name_to_id, limit=limit)
    if not updates:
        print("\n✗ No coordinates to update")
        sys.exit(1)

    # Process in batches
    total_updated = 0
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(updates) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n{'='*70}")
        print(f"Batch {batch_num}/{total_batches}: {len(batch)} records")
        print(f"{'='*70}")

        # Create CSV
        csv_file = f"/tmp/account_coords_batch_{batch_num}.csv"
        create_update_csv(batch, csv_file)

        # Update
        if update_salesforce(csv_file):
            total_updated += len(batch)

        # Cleanup
        os.remove(csv_file)

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     UPDATE COMPLETE                                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"Total records updated: {total_updated:,}")
    print()

    # Verify
    verify_updates(IMPORT_DATE)

    print()
    print("Next steps:")
    print("  1. View accounts on Salesforce Maps")
    print("  2. Run reports with location filters")
    print("  3. Use geo-queries in SOQL")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
