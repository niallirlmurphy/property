#!/usr/bin/env python3
"""
Clean up Salesforce Account and Contact data.

This script will:
1. Authenticate to Salesforce using interactive web login
2. Delete all Accounts and Contacts
3. Report results

Usage:
    python3 scripts/salesforce_cleanup.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_sf_command(command):
    """Run Salesforce CLI command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def authenticate_salesforce():
    """Authenticate to Salesforce using CLI."""
    print("="*70)
    print("SALESFORCE AUTHENTICATION")
    print("="*70)
    print()
    print("This will open your browser to log into Salesforce.")
    print("Press Enter to continue...")
    input()

    # Try to authenticate
    cmd = "sf org login web --alias cleanup-temp --set-default"
    stdout, stderr, code = run_sf_command(cmd)

    if code == 0:
        print("✓ Successfully authenticated!")
        return True
    else:
        print(f"✗ Authentication failed: {stderr}")
        return False


def get_org_info():
    """Get current org information."""
    cmd = "sf org display --json"
    stdout, stderr, code = run_sf_command(cmd)

    if code == 0:
        data = json.loads(stdout)
        result = data.get("result", {})
        return {
            "username": result.get("username"),
            "instance_url": result.get("instanceUrl"),
            "org_id": result.get("id"),
            "alias": result.get("alias")
        }
    return None


def count_records(object_type):
    """Count records for an object type."""
    cmd = f"sf data query --query \"SELECT COUNT() FROM {object_type}\" --json"
    stdout, stderr, code = run_sf_command(cmd)

    if code == 0:
        data = json.loads(stdout)
        return data.get("result", {}).get("totalSize", 0)
    return 0


def delete_all_records(object_type):
    """Delete all records for an object type."""
    print(f"\nDeleting all {object_type} records...")

    # Query all record IDs
    cmd = f"sf data query --query \"SELECT Id FROM {object_type}\" --json"
    stdout, stderr, code = run_sf_command(cmd)

    if code != 0:
        print(f"  ✗ Failed to query {object_type}: {stderr}")
        return 0

    data = json.loads(stdout)
    records = data.get("result", {}).get("records", [])

    if not records:
        print(f"  No {object_type} records to delete")
        return 0

    print(f"  Found {len(records)} {object_type} records")

    # Delete in batches of 200 (Salesforce bulk API limit)
    deleted = 0
    batch_size = 200

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        ids = [r["Id"] for r in batch]

        # Create temp file with IDs
        temp_file = f"/tmp/sf_delete_{object_type}_{i}.csv"
        with open(temp_file, 'w') as f:
            f.write("Id\n")
            for record_id in ids:
                f.write(f"{record_id}\n")

        # Delete via bulk API
        cmd = f"sf data delete bulk --sobject {object_type} --file {temp_file} --wait 10"
        stdout, stderr, code = run_sf_command(cmd)

        if code == 0:
            deleted += len(batch)
            print(f"  ✓ Deleted batch {i//batch_size + 1}: {len(batch)} records (total: {deleted})")
        else:
            print(f"  ⚠ Batch {i//batch_size + 1} failed: {stderr}")

        # Cleanup temp file
        os.remove(temp_file)

    return deleted


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        SALESFORCE DATA CLEANUP UTILITY                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Check if Salesforce CLI is installed
    stdout, stderr, code = run_sf_command("sf --version")
    if code != 0:
        print("✗ Salesforce CLI not installed")
        print("  Install from: https://developer.salesforce.com/tools/salesforcecli")
        sys.exit(1)

    print(f"✓ Salesforce CLI version: {stdout.strip()}")
    print()

    # Check if already authenticated
    org_info = get_org_info()

    if org_info:
        print("✓ Already authenticated to Salesforce:")
        print(f"  Username: {org_info['username']}")
        print(f"  Instance: {org_info['instance_url']}")
        print()
        print("Use this org? (Y/n): ", end="")
        choice = input().strip().lower()
        if choice and choice != 'y':
            # Re-authenticate
            if not authenticate_salesforce():
                sys.exit(1)
            org_info = get_org_info()
    else:
        # Authenticate
        if not authenticate_salesforce():
            sys.exit(1)
        org_info = get_org_info()

    print()
    print("="*70)
    print("CURRENT DATA")
    print("="*70)

    # Count records
    account_count = count_records("Account")
    contact_count = count_records("Contact")

    print(f"Accounts: {account_count:,}")
    print(f"Contacts: {contact_count:,}")
    print()

    if account_count == 0 and contact_count == 0:
        print("✓ No data to clean up!")
        return

    # Confirm deletion
    print("⚠️  WARNING: This will DELETE ALL Accounts and Contacts!")
    print("Type 'DELETE' to confirm: ", end="")
    confirmation = input().strip()

    if confirmation != "DELETE":
        print("Cancelled.")
        return

    print()
    print("="*70)
    print("DELETING DATA")
    print("="*70)

    # Delete Contacts first (child objects)
    if contact_count > 0:
        deleted_contacts = delete_all_records("Contact")
        print(f"✓ Deleted {deleted_contacts} Contacts")

    # Delete Accounts
    if account_count > 0:
        deleted_accounts = delete_all_records("Account")
        print(f"✓ Deleted {deleted_accounts} Accounts")

    print()
    print("="*70)
    print("VERIFICATION")
    print("="*70)

    # Verify deletion
    remaining_accounts = count_records("Account")
    remaining_contacts = count_records("Contact")

    print(f"Remaining Accounts: {remaining_accounts:,}")
    print(f"Remaining Contacts: {remaining_contacts:,}")
    print()

    if remaining_accounts == 0 and remaining_contacts == 0:
        print("✓ All data successfully deleted!")
    else:
        print("⚠ Some records remain. They may be in the recycle bin.")
        print("  To permanently delete, empty the recycle bin in Salesforce UI.")


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
