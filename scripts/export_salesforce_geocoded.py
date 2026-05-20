#!/usr/bin/env python3
"""
Export geocoded Account records from Salesforce to CSV.

Uses Salesforce Bulk API to efficiently extract large datasets.
"""

import subprocess
import json
import csv
import sys
from simple_salesforce import Salesforce, SFType

OUTPUT_FILE = "Salesforce-geocoded-irish-properties.csv"

def get_salesforce_connection():
    """Get Salesforce connection from CLI session."""
    print("Connecting to Salesforce...")

    result = subprocess.run(
        ["sf", "org", "display", "--json"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("✗ Not connected to Salesforce")
        print("Run: sf org login web")
        return None

    org_data = json.loads(result.stdout)
    access_token = org_data["result"]["accessToken"]
    instance_url = org_data["result"]["instanceUrl"]

    print(f"✓ Connected to: {org_data['result']['username']}")

    sf = Salesforce(
        instance_url=instance_url,
        session_id=access_token
    )

    return sf


def export_geocoded_accounts(sf):
    """Export geocoded accounts using pagination."""
    print("\nExporting geocoded Account records...")
    print()

    query = """
        SELECT Name, BillingStreet, BillingCity, BillingPostalCode, BillingCountry,
               BillingLatitude, BillingLongitude, Description, PPR_Import__c
        FROM Account
        WHERE PPR_Import__c IN ('2026-05-18', '2026-05-19')
        AND BillingLatitude != null
        AND BillingLongitude != null
        ORDER BY Id
    """

    # Execute query
    print("Executing query...")
    result = sf.query_all(query)

    total_records = result['totalSize']
    print(f"✓ Found {total_records:,} geocoded records")
    print()

    # Write to CSV
    print(f"Writing to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            'Name', 'BillingStreet', 'BillingCity', 'BillingPostalCode',
            'BillingCountry', 'BillingLatitude', 'BillingLongitude',
            'Description', 'PPR_Import__c'
        ])

        # Write records
        count = 0
        for record in result['records']:
            writer.writerow([
                record.get('Name', ''),
                record.get('BillingStreet', ''),
                record.get('BillingCity', ''),
                record.get('BillingPostalCode', ''),
                record.get('BillingCountry', ''),
                record.get('BillingLatitude', ''),
                record.get('BillingLongitude', ''),
                record.get('Description', ''),
                record.get('PPR_Import__c', '')
            ])

            count += 1
            if count % 10000 == 0:
                print(f"  Exported {count:,} records...")

    print()
    print(f"✓ Export complete!")
    print(f"  Total records: {count:,}")

    return count


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     EXPORT SALESFORCE GEOCODED DATA                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Connect to Salesforce
    sf = get_salesforce_connection()
    if not sf:
        sys.exit(1)

    # Export data
    count = export_geocoded_accounts(sf)

    # Show file info
    print()
    print("="*70)
    print("OUTPUT FILE")
    print("="*70)
    print(f"File: {OUTPUT_FILE}")

    import os
    size = os.path.getsize(OUTPUT_FILE)
    print(f"Size: {size/1024/1024:.1f} MB")
    print(f"Records: {count:,}")
    print()

    # Show sample
    print("Sample records:")
    with open(OUTPUT_FILE, 'r') as f:
        for i, line in enumerate(f):
            if i < 3:
                print(f"  {line.strip()}")
            else:
                break

    print()
    print("✓ File ready: Salesforce-geocoded-irish-properties.csv")


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
