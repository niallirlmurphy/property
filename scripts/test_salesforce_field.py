#!/usr/bin/env python3
"""
Test if PPR_Import__c field exists on Account object.
"""

import subprocess
import json
import sys

def run_sf_command(command):
    """Run Salesforce CLI command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def main():
    print("Checking for PPR_Import__c field on Account...")
    print()

    # Get org info
    stdout, stderr, code = run_sf_command("sf org display --json")
    if code != 0:
        print("✗ Not connected to Salesforce")
        print("Run: sf org login web --alias property-geocoding --set-default")
        sys.exit(1)

    org_data = json.loads(stdout)
    print(f"✓ Connected to: {org_data['result']['username']}")
    print()

    # Try to query the field
    query = "SELECT Id, PPR_Import__c FROM Account LIMIT 1"
    stdout, stderr, code = run_sf_command(f'sf data query --query "{query}" --json')

    if code == 0:
        print("✓ PPR_Import__c field exists!")
        print()

        # Check if any records have it set
        count_query = "SELECT COUNT() FROM Account WHERE PPR_Import__c = true"
        stdout2, stderr2, code2 = run_sf_command(f'sf data query --query "{count_query}" --json')

        if code2 == 0:
            data = json.loads(stdout2)
            count = data.get("result", {}).get("totalSize", 0)
            print(f"Records with PPR_Import__c = true: {count}")
            print()

        print("✅ Ready to import PPR data!")
        print()
        print("Next steps:")
        print("  python3 scripts/import_to_salesforce.py --limit 10  # Test run")
        print("  python3 scripts/import_to_salesforce.py --limit 100 # Production")

    else:
        error_text = stderr.lower()
        if "no such column" in error_text or "ppr_import__c" in error_text:
            print("✗ PPR_Import__c field NOT found")
            print()
            print("Please create the field:")
            print("  See: scripts/SALESFORCE_FIELD_SETUP.md")
            print()
            print("Quick steps:")
            print("  1. Login to Salesforce")
            print("  2. Setup → Object Manager → Account")
            print("  3. Fields & Relationships → New")
            print("  4. Type: Checkbox")
            print("  5. Label: PPR Import")
            print("  6. API Name: PPR_Import")
            sys.exit(1)
        else:
            print(f"✗ Unexpected error: {stderr}")
            sys.exit(1)


if __name__ == "__main__":
    main()
