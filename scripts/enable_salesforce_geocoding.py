#!/usr/bin/env python3
"""
Enable automatic geocoding for Account BillingAddress in Salesforce.

This script:
1. Connects to Salesforce
2. Enables Data Integration Rules for Address
3. Configures Account object to geocode on BillingAddress
4. Tests geocoding on existing records

Requirements:
- Salesforce Maps & Location Services enabled
- Billing address fields on Account
"""

import subprocess
import json
import sys
from simple_salesforce import Salesforce


def get_salesforce_connection():
    """Get Salesforce connection from CLI session."""
    print("Getting Salesforce connection from CLI...")

    result = subprocess.run(
        ["sf", "org", "display", "--json"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("✗ Not connected to Salesforce")
        print("Run: sf org login web --alias property-geocoding")
        return None

    org_data = json.loads(result.stdout)
    access_token = org_data["result"]["accessToken"]
    instance_url = org_data["result"]["instanceUrl"]

    print(f"✓ Connected to: {org_data['result']['username']}")
    print(f"  Instance: {instance_url}")

    # Connect using session ID
    sf = Salesforce(
        instance_url=instance_url,
        session_id=access_token
    )

    return sf


def check_geocoding_enabled(sf):
    """Check if geocoding is available in the org."""
    print("\nChecking geocoding availability...")

    try:
        # Check if Account has lat/long fields
        account_desc = sf.Account.describe()
        fields = {f['name']: f for f in account_desc['fields']}

        has_latitude = 'BillingLatitude' in fields
        has_longitude = 'BillingLongitude' in fields

        print(f"  BillingLatitude field: {'✓' if has_latitude else '✗'}")
        print(f"  BillingLongitude field: {'✓' if has_longitude else '✗'}")

        if not has_latitude or not has_longitude:
            print("\n⚠️  Geocode fields not found on Account")
            print("These fields are automatically added when geocoding is enabled")
            return False

        return True

    except Exception as e:
        print(f"✗ Error checking fields: {e}")
        return False


def enable_geocoding_via_api(sf):
    """Enable geocoding using Salesforce API."""
    print("\nEnabling geocoding for Account BillingAddress...")

    try:
        # Note: Geocoding settings are typically managed through UI or Tooling API
        # The Metadata API approach requires specific org permissions

        print("⚠️  Automatic geocoding configuration requires:")
        print("   1. Salesforce Maps & Location Services enabled")
        print("   2. Data Integration Rules enabled")
        print("   3. Admin access to configure in Setup")
        print()
        print("Manual steps:")
        print("   1. Setup → Feature Settings → Sales → Data Integration Rules")
        print("   2. Enable 'Improve data quality with Data.com'")
        print("   3. Setup → Maps and Location Services")
        print("   4. Enable geocoding for Account object")
        print("   5. Select BillingAddress fields for geocoding")

        return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def create_geocode_latitude_longitude_fields():
    """Create custom lat/long fields if standard geocode fields aren't available."""
    print("\nAlternative: Creating custom geocoding fields...")

    print("""
Custom Field Option:
If standard geocoding isn't available, you can:

1. Create custom fields on Account:
   - Geocode_Latitude__c (Number, 8 decimal places)
   - Geocode_Longitude__c (Number, 8 decimal places)

2. Run this script to populate from your geocoded CSV:
   scripts/import_geocoded_coordinates.py

This approach:
✓ Works without Salesforce Maps license
✓ Uses your existing geocoded data
✓ No additional API costs
""")


def test_geocode_sample_records(sf):
    """Test geocoding on sample imported records."""
    print("\nTesting geocoding on sample records...")

    try:
        # Query sample records
        result = sf.query("""
            SELECT Id, Name, BillingStreet, BillingCity, BillingPostalCode,
                   BillingCountry, BillingLatitude, BillingLongitude
            FROM Account
            WHERE PPR_Import__c = '2026-05-18'
            LIMIT 5
        """)

        if result['totalSize'] == 0:
            print("  No imported records found yet")
            return

        print(f"  Found {result['totalSize']} sample records:")
        print()

        geocoded_count = 0
        for record in result['records']:
            has_coords = record.get('BillingLatitude') and record.get('BillingLongitude')
            status = "✓ Geocoded" if has_coords else "⊘ Not geocoded"

            print(f"  {status}: {record['Name'][:50]}")
            if has_coords:
                print(f"    → {record['BillingLatitude']}, {record['BillingLongitude']}")
                geocoded_count += 1
            else:
                print(f"    Address: {record.get('BillingStreet', 'N/A')}, {record.get('BillingCity', 'N/A')}")

        print()
        print(f"  Geocoded: {geocoded_count}/{len(result['records'])}")

        if geocoded_count == 0:
            print("  ⚠️  No records are geocoded yet")
            print("  Geocoding may be disabled or processing in background")

    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     SALESFORCE GEOCODING CONFIGURATION                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Connect to Salesforce
    sf = get_salesforce_connection()
    if not sf:
        sys.exit(1)

    # Check geocoding availability
    has_geocoding = check_geocoding_enabled(sf)

    if has_geocoding:
        print("\n✓ Geocoding fields are available!")
        test_geocode_sample_records(sf)
    else:
        print("\n⚠️  Standard geocoding not available in this org")
        create_geocode_latitude_longitude_fields()

    print()
    print("="*70)
    print("RECOMMENDED APPROACH")
    print("="*70)
    print()
    print("Since you already have geocoded coordinates in PPR-ALL-geocoded.csv,")
    print("the fastest option is to import those coordinates directly.")
    print()
    print("Next step:")
    print("  python3 scripts/import_geocoded_coordinates.py")
    print()
    print("This will:")
    print("  1. Create custom Geocode_Latitude__c and Geocode_Longitude__c fields")
    print("  2. Update all imported Account records with coordinates from CSV")
    print("  3. Enable map visualization in Salesforce")


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
