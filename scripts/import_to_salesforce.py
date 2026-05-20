#!/usr/bin/env python3
"""
Import PPR (Property Price Register) data into Salesforce as Account records.

Each property becomes an Account with:
- Name: Address
- BillingStreet: Address
- BillingCity: County
- BillingPostalCode: Eircode
- BillingCountry: Ireland
- PPR_Import__c: Import date (YYYY-MM-DD)
- Custom fields for sale data

Usage:
    python3 scripts/import_to_salesforce.py [--limit N] [--skip N] [--test]
"""

import subprocess
import json
import csv
import sys
import os
from datetime import datetime
from pathlib import Path

# File paths
PPR_GEOCODED_CSV = "PPR-ALL-geocoded.csv"
IMPORT_DATE = datetime.now().strftime("%Y-%m-%d")

# Batch size for Salesforce bulk API
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


def check_salesforce_connection():
    """Verify Salesforce CLI connection."""
    print("Checking Salesforce connection...")
    stdout, stderr, code = run_sf_command("sf org display --json")

    if code != 0:
        print("✗ Not connected to Salesforce")
        print("Run: sf org login web --alias property-geocoding")
        return None

    org_data = json.loads(stdout)
    username = org_data["result"]["username"]
    instance = org_data["result"]["instanceUrl"]

    print(f"✓ Connected to: {username}")
    print(f"  Instance: {instance}")
    return org_data["result"]


def check_ppr_import_field():
    """Check if PPR_Import__c field exists."""
    print("\nChecking PPR_Import__c field...")
    stdout, stderr, code = run_sf_command(
        'sf data query --query "SELECT Id, PPR_Import__c FROM Account LIMIT 1" 2>&1'
    )

    if "No such column" in stderr or "No such column" in stdout:
        print("✗ PPR_Import__c field not found on Account object")
        print("Please create it first: scripts/SALESFORCE_FIELD_SETUP.md")
        return False

    print("✓ PPR_Import__c field exists")
    return True


def count_existing_ppr_records():
    """Count existing PPR import records."""
    print("\nChecking existing PPR records...")
    query = f"SELECT COUNT() FROM Account WHERE PPR_Import__c != null"
    stdout, stderr, code = run_sf_command(f'sf data query --query "{query}" 2>&1')

    if "Total number of records retrieved:" in stdout:
        # Parse count from output
        for line in stdout.split('\n'):
            if "Total number of records retrieved:" in line:
                # Remove ANSI escape codes
                import re
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                count_str = clean_line.split(':')[1].strip().replace('.', '').replace(',', '')
                try:
                    count = int(count_str)
                    print(f"  Existing PPR records: {count:,}")
                    return count
                except:
                    pass

    return 0


def read_ppr_csv(limit=None, skip=0):
    """Read PPR CSV and convert to Salesforce Account format."""
    print(f"\nReading PPR data from: {PPR_GEOCODED_CSV}")

    if not Path(PPR_GEOCODED_CSV).exists():
        print(f"✗ File not found: {PPR_GEOCODED_CSV}")
        return []

    records = []

    with open(PPR_GEOCODED_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            # Skip records if requested
            if i < skip:
                continue

            # Stop if limit reached
            if limit and len(records) >= limit:
                break

            # Convert to Salesforce Account format
            address = row.get('Address', '').strip()
            county = row.get('County', '').strip()
            eircode = row.get('Eircode', '').strip()
            # Try both column names (encoding issues)
            price = row.get('Price (€)', row.get('Price (�)', '')).replace('€', '').replace('�', '').replace(',', '').strip()
            sale_date = row.get('Date of Sale (dd/mm/yyyy)', '').strip()

            # Convert price to number
            try:
                price_num = float(price) if price else 0
            except:
                price_num = 0

            # Parse latitude/longitude if available
            latitude = row.get('Latitude', '').strip()
            longitude = row.get('Longitude', '').strip()

            # Skip records without address
            if not address:
                continue

            # Create Account record
            account = {
                'Name': address[:80],  # Salesforce Name field max 80 chars
                'BillingStreet': address[:255],
                'BillingCity': county[:40] if county else 'Unknown',
                'BillingPostalCode': eircode[:20] if eircode else '',
                'BillingCountry': 'Ireland',
                'PPR_Import__c': IMPORT_DATE,
                'Description': f"Sale Date: {sale_date}, Price: €{price_num:,.0f}"
            }

            records.append(account)

    print(f"✓ Loaded {len(records):,} records")
    if skip > 0:
        print(f"  (skipped first {skip:,} records)")

    return records


def create_import_csv(records, output_file="/tmp/ppr_import.csv"):
    """Create CSV file for Salesforce bulk import with Unix (LF) line endings."""
    if not records:
        return None

    # Get field names from first record
    fieldnames = list(records[0].keys())

    # Write in binary mode to ensure LF line endings (Salesforce requirement)
    with open(output_file, 'wb') as f:
        # Write header
        header = ','.join(fieldnames) + '\n'
        f.write(header.encode('utf-8'))

        # Write data rows
        for record in records:
            values = []
            for field in fieldnames:
                val = str(record.get(field, ''))
                # Quote values that contain commas or quotes
                if ',' in val or '"' in val or '\n' in val:
                    val = '"' + val.replace('"', '""') + '"'
                values.append(val)

            row = ','.join(values) + '\n'
            f.write(row.encode('utf-8'))

    return output_file


def import_to_salesforce(csv_file, batch_description=""):
    """Import CSV to Salesforce using bulk API."""
    print(f"\n{'='*70}")
    print(f"IMPORTING TO SALESFORCE {batch_description}")
    print(f"{'='*70}")

    cmd = f'sf data import bulk --sobject Account --file {csv_file} --wait 10'

    print("Running bulk import...")
    print(f"Command: {cmd}")
    print()

    stdout, stderr, code = run_sf_command(cmd)

    # Parse results
    print(stdout)

    # Extract success/failure counts (ignore spinner characters)
    import re
    success_count = 0
    failed_count = 0

    for line in stdout.split('\n'):
        if "Successful records:" in line:
            # Extract numbers only, ignore ANSI codes and spinner chars
            match = re.search(r'Successful records:\s*(\d+)', line)
            if match:
                success_count = int(match.group(1))
                print(f"\n✓ Successfully imported: {success_count} records")
        elif "Failed records:" in line:
            match = re.search(r'Failed records:\s*(\d+)', line)
            if match:
                failed_count = int(match.group(1))
                if failed_count > 0:
                    print(f"⚠ Failed records: {failed_count}")

    return code == 0


def main():
    # Parse arguments
    limit = None
    skip = 0
    test_mode = False

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--skip" and i + 1 < len(sys.argv):
            skip = int(sys.argv[i + 1])
        elif arg == "--test":
            test_mode = True
            limit = 10

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     PPR DATA → SALESFORCE IMPORT                             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"Import Date Tag: {IMPORT_DATE}")
    if test_mode:
        print("Mode: TEST (10 records)")
    elif limit:
        print(f"Mode: LIMITED ({limit:,} records)")
    else:
        print("Mode: FULL IMPORT (all records)")
    print()

    # Pre-flight checks
    org_info = check_salesforce_connection()
    if not org_info:
        sys.exit(1)

    if not check_ppr_import_field():
        sys.exit(1)

    existing_count = count_existing_ppr_records()

    # Confirm if not test mode
    if not test_mode and limit is None:
        print()
        print("⚠️  WARNING: This will import ALL 781,000+ PPR records!")
        print("This may take several hours and consume significant API limits.")
        print()
        print("Type 'IMPORT' to confirm: ", end="")
        confirmation = input().strip()
        if confirmation != "IMPORT":
            print("Cancelled.")
            sys.exit(0)

    # Read PPR data
    records = read_ppr_csv(limit=limit, skip=skip)

    if not records:
        print("✗ No records to import")
        sys.exit(1)

    # Process in batches
    total_records = len(records)
    batch_size = BATCH_SIZE
    success_total = 0

    for batch_start in range(0, total_records, batch_size):
        batch_end = min(batch_start + batch_size, total_records)
        batch_records = records[batch_start:batch_end]

        batch_num = (batch_start // batch_size) + 1
        total_batches = (total_records + batch_size - 1) // batch_size

        print(f"\n{'='*70}")
        print(f"Batch {batch_num}/{total_batches}: Records {batch_start+1}-{batch_end}")
        print(f"{'='*70}")

        # Create CSV for this batch
        csv_file = f"/tmp/ppr_import_batch_{batch_num}.csv"
        create_import_csv(batch_records, csv_file)

        # Import to Salesforce
        success = import_to_salesforce(
            csv_file,
            batch_description=f"(Batch {batch_num}/{total_batches})"
        )

        if success:
            success_total += len(batch_records)

        # Cleanup temp file
        os.remove(csv_file)

    # Final summary
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     IMPORT COMPLETE                                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"Total records processed: {total_records:,}")
    print(f"Successfully imported: {success_total:,}")
    print(f"Import date tag: {IMPORT_DATE}")
    print()
    print("Verify with:")
    print(f'  sf data query --query "SELECT COUNT() FROM Account WHERE PPR_Import__c = \'{IMPORT_DATE}\'"')
    print()
    print("To clean up imported records:")
    print(f'  sf data query --query "SELECT Id FROM Account WHERE PPR_Import__c = \'{IMPORT_DATE}\'" --result-format csv > /tmp/cleanup.csv')
    print('  sf data delete bulk --sobject Account --file /tmp/cleanup.csv')


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
