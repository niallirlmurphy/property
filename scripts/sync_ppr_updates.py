#!/usr/bin/env python3
"""
Sync new property sales from Property Price Register (PPR).

Fetches latest sales data from PPR, compares with database, and imports delta.

Process:
1. Query database for most recent sale date
2. Download PPR CSV data (full dataset or recent subset)
3. Filter to sales newer than most recent in DB
4. Normalize format to match existing schema
5. Geocode new properties (using existing geocode.py logic)
6. Import to database

Schedule: Biweekly cron (every 2 weeks)

Usage:
    python3 scripts/sync_ppr_updates.py [--dry-run] [--since YYYY-MM-DD]
"""

import asyncpg
import asyncio
import csv
import os
import sys
import re
import requests
import tempfile
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
PPR_DOWNLOAD_PAGE = "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPRDownloads?OpenForm"

# Note: PPR website requires manual download through their form.
# Direct CSV URL changes frequently and may not work reliably.
# Users should download manually from the website.

PROJECT_ROOT = Path(__file__).parent.parent


def parse_date(raw: Optional[str]) -> Optional[str]:
    """Parse date from PPR format (DD/MM/YYYY) to ISO format (YYYY-MM-DD)."""
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_price(raw: Optional[str]) -> Optional[float]:
    """Parse price, removing currency symbols and formatting."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_bool(raw: str) -> bool:
    """Parse Yes/No to boolean."""
    return raw.strip().lower() in ("yes", "true", "1")


def normalize_ppr_row(row: Dict[str, str]) -> Dict[str, any]:
    """Normalize PPR CSV row to database schema format."""

    # PPR CSV column names (as of 2024)
    # Date of Sale (dd/mm/yyyy), Address, Postal Code/Eircode, County, Price (€/�),
    # Not Full Market Price, VAT Exclusive, Description of Property, Property Size Description

    # Handle various column name variations
    price_raw = row.get('Price (€)') or row.get('Price (�)') or row.get('Price (EUR)') or row.get('Price')
    eircode_raw = row.get('Postal Code') or row.get('Eircode')

    return {
        'sale_date': parse_date(row.get('Date of Sale (dd/mm/yyyy)')),
        'address': row.get('Address', '').strip(),
        'eircode': (eircode_raw or '').strip() or None,
        'county': row.get('County', '').strip(),
        'price': parse_price(price_raw),
        'not_full_market_price': parse_bool(row.get('Not Full Market Price', 'No')),
        'vat_exclusive': parse_bool(row.get('VAT Exclusive', 'No')),
        'description': row.get('Description of Property', '').strip(),
        'size_description': row.get('Property Size Description', '').strip() or None,
    }


async def get_most_recent_sale_date(conn: asyncpg.Connection) -> Optional[datetime.date]:
    """Get the most recent sale date in the database."""
    row = await conn.fetchrow("""
        SELECT MAX(sale_date) as max_date
        FROM properties
    """)
    return row['max_date'] if row else None


async def download_ppr_csv(output_path: str) -> bool:
    """
    Download PPR CSV file by submitting form to PPR website.

    The PPR website requires form submission rather than direct download.
    This function automates the form submission process.
    """
    print(f"Downloading PPR data via form submission...")

    try:
        import warnings
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')

        # Step 1: Submit form to request "ALL" data
        session = requests.Session()
        session.verify = False  # PPR has SSL cert issues

        form_url = "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPRDownloads?OpenForm&Seq=1"

        # Form data requesting ALL periods
        form_data = {
            '%%Surrogate_dsPeriod': '1',
            'dsPeriod': 'ALL',
        }

        print(f"  Submitting download request...")
        response = session.post(form_url, data=form_data, timeout=60)

        if response.status_code != 200:
            raise Exception(f"Form submission failed: HTTP {response.status_code}")

        # Step 2: Parse response to find download link
        # The response should contain a link to the generated CSV
        content = response.text

        # Look for CSV download link in response
        import re
        csv_link_match = re.search(r'href="([^"]*PPR[^"]*\.csv[^"]*)"', content, re.IGNORECASE)

        if not csv_link_match:
            # Fallback: try to find any .csv link
            csv_link_match = re.search(r'href="([^"]*\.csv[^"]*)"', content, re.IGNORECASE)

        if not csv_link_match:
            print(f"  ⚠️  Could not find CSV download link in form response")
            print(f"  Response preview: {content[:500]}")
            raise Exception("No CSV download link found")

        csv_path = csv_link_match.group(1)

        # Build full URL (may be relative)
        if csv_path.startswith('http'):
            csv_url = csv_path
        elif csv_path.startswith('/'):
            csv_url = f"https://www.propertypriceregister.ie{csv_path}"
        else:
            csv_url = f"https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/{csv_path}"

        print(f"  Found CSV URL: {csv_url}")
        print(f"  Downloading...")

        # Step 3: Download the CSV file
        csv_response = session.get(csv_url, timeout=300, stream=True)
        csv_response.raise_for_status()

        # Save to file
        with open(output_path, 'wb') as f:
            for chunk in csv_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Verify it's a CSV
        with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
            first_line = f.readline()
            if 'Date of Sale' not in first_line and 'Address' not in first_line:
                raise Exception(f"Downloaded file doesn't look like PPR CSV. First line: {first_line[:100]}")

        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"  ✓ Downloaded {file_size:.1f} MB to {output_path}")
        return True

    except Exception as e:
        print(f"  ✗ Automatic download failed: {e}")
        print(f"\n  Manual download fallback:")
        print(f"    1. Visit: {PPR_DOWNLOAD_PAGE}")
        print(f"    2. Select 'ALL' and click 'Perform Download'")
        print(f"    3. Save PPR-ALL.csv")
        print(f"    4. Re-run: python3 scripts/sync_ppr_updates.py --manual-csv ~/Downloads/PPR-ALL.csv")
        return False


async def filter_new_sales(csv_path: str, since_date: datetime.date) -> List[Dict]:
    """Read PPR CSV and filter to sales after since_date."""

    new_sales = []
    skipped = 0
    invalid = 0

    print(f"Filtering sales after {since_date}...")

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)

        # PPR uses comma delimiter
        reader = csv.DictReader(f)

        for row in reader:
            try:
                normalized = normalize_ppr_row(row)

                # Skip if no sale date or price
                if not normalized['sale_date'] or not normalized['price']:
                    invalid += 1
                    continue

                sale_date = datetime.fromisoformat(normalized['sale_date']).date()

                # Filter to new sales only
                if sale_date > since_date:
                    new_sales.append(normalized)
                else:
                    skipped += 1

            except Exception as e:
                invalid += 1
                continue

    print(f"  Found {len(new_sales)} new sales")
    print(f"  Skipped {skipped} existing sales")
    print(f"  Invalid {invalid} rows")

    return new_sales


async def geocode_new_sales(sales: List[Dict], output_csv: str):
    """
    Geocode new sales using existing geocode.py infrastructure.

    Writes sales to temp CSV, runs geocode.py, reads geocoded CSV.
    """

    if not sales:
        print("No sales to geocode")
        return []

    print(f"\nGeocoding {len(sales)} new properties...")

    # Write to temp CSV in PPR format for geocode.py
    temp_input = output_csv.replace('.csv', '_input.csv')

    with open(temp_input, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Date of Sale (dd/mm/yyyy)', 'Address', 'Postal Code',
            'County', 'Price (€)', 'Not Full Market Price',
            'VAT Exclusive', 'Description of Property', 'Property Size Description'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for sale in sales:
            writer.writerow({
                'Date of Sale (dd/mm/yyyy)': datetime.fromisoformat(sale['sale_date']).strftime('%d/%m/%Y'),
                'Address': sale['address'],
                'Postal Code': sale['eircode'] or '',
                'County': sale['county'],
                'Price (€)': f"€{sale['price']:.2f}",
                'Not Full Market Price': 'Yes' if sale['not_full_market_price'] else 'No',
                'VAT Exclusive': 'Yes' if sale['vat_exclusive'] else 'No',
                'Description of Property': sale['description'],
                'Property Size Description': sale['size_description'] or '',
            })

    print(f"  Wrote {len(sales)} sales to {temp_input}")
    print(f"  Running geocoder (this may take a while)...")

    # Run geocode.py on temp file
    # Note: This requires geocode.py to accept custom input/output paths
    # May need to adapt geocode.py or implement geocoding directly here

    geocode_script = PROJECT_ROOT / "geocode.py"

    if geocode_script.exists():
        try:
            # Run geocode.py with temp file
            # TODO: Adapt geocode.py to accept --input and --output flags
            result = subprocess.run([
                sys.executable,
                str(geocode_script),
                "--input", temp_input,
                "--output", output_csv,
            ], capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                print(f"  ✓ Geocoding complete")
            else:
                print(f"  ⚠️  Geocoding had errors: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Geocoding timed out (>1 hour)")
        except Exception as e:
            print(f"  ⚠️  Geocoding failed: {e}")
    else:
        print(f"  ⚠️  geocode.py not found, skipping geocoding")
        print(f"     Sales will be imported without coordinates")
        # Just copy input to output for now
        import shutil
        shutil.copy(temp_input, output_csv)

    return output_csv


async def import_to_database(csv_path: str, conn: asyncpg.Connection, dry_run: bool = False):
    """Import geocoded sales to database."""

    print(f"\nImporting from {csv_path}...")

    sales = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = normalize_ppr_row(row)

            # Add coordinates if available
            normalized['latitude'] = float(row['Latitude']) if row.get('Latitude') else None
            normalized['longitude'] = float(row['Longitude']) if row.get('Longitude') else None

            sales.append(normalized)

    if dry_run:
        print(f"[DRY RUN] Would import {len(sales)} properties")
        for i, sale in enumerate(sales[:5], 1):
            print(f"  {i}. {sale['address']} - €{sale['price']:,.0f} on {sale['sale_date']}")
        if len(sales) > 5:
            print(f"  ... and {len(sales) - 5} more")
        return

    # Batch insert
    BATCH_SIZE = 1000
    imported = 0

    for i in range(0, len(sales), BATCH_SIZE):
        batch = sales[i:i+BATCH_SIZE]

        await conn.executemany("""
            INSERT INTO properties (
                sale_date, address, county, eircode, price,
                not_full_market_price, vat_exclusive,
                description, size_description,
                latitude, longitude, geog
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                CASE
                    WHEN $10 IS NOT NULL AND $11 IS NOT NULL
                    THEN ST_MakePoint($11, $10)::geography
                    ELSE NULL
                END
            )
            ON CONFLICT DO NOTHING
        """, [
            (
                sale['sale_date'], sale['address'], sale['county'], sale['eircode'],
                sale['price'], sale['not_full_market_price'], sale['vat_exclusive'],
                sale['description'], sale['size_description'],
                sale['latitude'], sale['longitude']
            )
            for sale in batch
        ])

        imported += len(batch)
        print(f"  Imported {imported}/{len(sales)} properties...")

    print(f"✓ Imported {imported} new properties")

    # Refresh routing key stats if any new properties have Eircodes
    with_eircodes = sum(1 for s in sales if s['eircode'])
    if with_eircodes > 0:
        print(f"\nRefreshing routing_key_stats materialized view...")
        await conn.execute("REFRESH MATERIALIZED VIEW routing_key_stats")
        print(f"✓ Routing key stats updated")


async def sync_ppr_updates(dry_run: bool = False, since_date: Optional[str] = None, manual_csv: Optional[str] = None):
    """Main sync process."""

    print("=" * 70)
    print("PPR UPDATE SYNC")
    print("=" * 70)
    print()

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # 1. Determine cutoff date
        if since_date:
            cutoff = datetime.fromisoformat(since_date).date()
            print(f"Using specified cutoff date: {cutoff}")
        else:
            cutoff = await get_most_recent_sale_date(conn)
            if cutoff:
                print(f"Most recent sale in database: {cutoff}")
            else:
                print("No sales in database, importing all")
                cutoff = datetime(2010, 1, 1).date()  # PPR starts from 2010

        print()

        # 2. Download or use manual CSV
        if manual_csv:
            csv_path = manual_csv
            print(f"Using manually provided CSV: {csv_path}")
        else:
            # Try to use existing source data file
            source_csv = PROJECT_ROOT / "source data" / "PPR-ALL.csv"
            if source_csv.exists():
                csv_path = str(source_csv)
                print(f"Using existing source file: {csv_path}")
                file_age_days = (datetime.now() - datetime.fromtimestamp(source_csv.stat().st_mtime)).days
                print(f"File age: {file_age_days} days old")
                if file_age_days > 14:
                    print(f"⚠️  Source file is >{file_age_days} days old, consider updating")
                    print(f"   Download latest from: {PPR_DOWNLOAD_PAGE}")
            else:
                print(f"\n⚠️  No source CSV found at: {source_csv}")
                print(f"   Download PPR-ALL.csv from: {PPR_DOWNLOAD_PAGE}")
                print(f"   Save to: {source_csv}")
                print(f"   Or use: --manual-csv /path/to/PPR-ALL.csv")
                return 1

        print()

        # 3. Filter to new sales
        new_sales = await filter_new_sales(csv_path, cutoff)

        if not new_sales:
            print("\n✓ Database is up to date, no new sales to import")
            return 0

        print()

        # 4. Geocode new sales
        geocoded_csv = tempfile.mktemp(suffix='_ppr_geocoded.csv')
        await geocode_new_sales(new_sales, geocoded_csv)

        print()

        # 5. Import to database
        await import_to_database(geocoded_csv, conn, dry_run=dry_run)

        print()
        print("=" * 70)
        print("✓ SYNC COMPLETE")
        print("=" * 70)

        return 0

    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync new property sales from PPR")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without importing")
    parser.add_argument("--since", help="Override cutoff date (YYYY-MM-DD)")
    parser.add_argument("--manual-csv", help="Path to manually downloaded PPR-ALL.csv")

    args = parser.parse_args()

    exit_code = asyncio.run(sync_ppr_updates(
        dry_run=args.dry_run,
        since_date=args.since,
        manual_csv=args.manual_csv
    ))

    sys.exit(exit_code)
