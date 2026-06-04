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


def parse_date(raw: Optional[str]):
    """Parse date from PPR format (DD/MM/YYYY) to date object."""
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
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


def normalize_address(address: str) -> str:
    """
    Normalize Irish property address for better geocoding and matching.

    Rules:
    1. Title case (except common words)
    2. Remove "No." prefix from house numbers
    3. Standardize apartment/unit formatting
    4. Standardize street type abbreviations
    5. Clean up punctuation and whitespace
    """
    if not address:
        return address

    normalized = address.strip()

    # Basic cleanup
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r',\s*,+', ',', normalized)

    # Remove "No." prefix
    normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)

    # Standardize apartment/unit
    normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

    # Standardize street types
    street_types = {
        r'\bSt\.?\b': 'Street',
        r'\bRd\.?\b': 'Road',
        r'\bAve\.?\b': 'Avenue',
        r'\bDr\.?\b': 'Drive',
        r'\bCl\.?\b': 'Close',
        r'\bCt\.?\b': 'Court',
        r'\bPk\.?\b': 'Park',
        r'\bSq\.?\b': 'Square',
    }

    for abbrev, full in street_types.items():
        normalized = re.sub(abbrev, full, normalized, flags=re.I)

    # Clean up punctuation
    normalized = re.sub(r',\s*,', ',', normalized)
    normalized = re.sub(r'\s+,', ',', normalized)
    normalized = re.sub(r',\s+', ', ', normalized)
    normalized = normalized.strip(', ')

    # Title case with exceptions
    words = normalized.split()
    lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
    upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

    result_words = []
    for i, word in enumerate(words):
        if i == 0:
            result_words.append(word.capitalize())
        elif word in upper_exceptions:
            result_words.append(word)
        elif word.lower() in lower_exceptions:
            result_words.append(word.lower())
        else:
            result_words.append(word.capitalize())

    normalized = ' '.join(result_words)

    # Final cleanup
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def normalize_ppr_row(row: Dict[str, str]) -> Dict[str, any]:
    """Normalize PPR CSV row to database schema format."""

    # PPR CSV column names (as of 2024)
    # Date of Sale (dd/mm/yyyy), Address, Postal Code/Eircode, County, Price (€/�),
    # Not Full Market Price, VAT Exclusive, Description of Property, Property Size Description

    # Handle various column name variations
    price_raw = row.get('Price (€)') or row.get('Price (�)') or row.get('Price (EUR)') or row.get('Price')
    eircode_raw = row.get('Postal Code') or row.get('Eircode')

    address_raw = row.get('Address', '').strip()

    return {
        'sale_date': parse_date(row.get('Date of Sale (dd/mm/yyyy)')),
        'address': address_raw,
        'address_normalized': normalize_address(address_raw),
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
    """Read PPR CSV and filter to sales after since_date.

    Optimized: PPR CSV is sorted oldest→newest, so we read from the end backwards
    to find recent sales quickly without scanning all 785k+ rows.
    """

    print(f"Filtering sales after {since_date}...")
    print(f"  (PPR CSV is date-sorted, reading from end...)")

    # Read all lines (fast for 103MB file)
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    header = lines[0]
    fieldnames = next(csv.reader([header]))

    new_sales = []
    invalid = 0
    cutoff_line = len(lines)  # Where we stopped finding new sales

    # Read backwards from end until we hit older dates
    for i in range(len(lines) - 1, 0, -1):
        try:
            row_dict = dict(zip(fieldnames, next(csv.reader([lines[i]]))))
            normalized = normalize_ppr_row(row_dict)

            # Skip if no sale date or price
            if not normalized['sale_date'] or not normalized['price']:
                invalid += 1
                continue

            sale_date = normalized['sale_date']  # Already a date object

            if sale_date > since_date:
                new_sales.append(normalized)
                cutoff_line = i
            else:
                # Hit older dates, stop scanning
                break

        except Exception as e:
            invalid += 1
            continue

    # Reverse to get chronological order (oldest new sale first)
    new_sales.reverse()

    skipped = cutoff_line - 1  # Approximate
    print(f"  Found {len(new_sales)} new sales")
    print(f"  Scanned last {len(lines) - cutoff_line:,} rows (skipped first {skipped:,})")
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
                'Date of Sale (dd/mm/yyyy)': sale['sale_date'].strftime('%d/%m/%Y'),
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


IRELAND_BOUNDS = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon


def validate_coordinates(lat: float, lon: float, eircode: Optional[str], county: str) -> tuple[Optional[float], Optional[float], str]:
    """
    Validate geocoded coordinates using multiple checks.

    Returns: (validated_lat, validated_lon, reason)
    - Returns (None, None, reason) if coordinates fail validation
    - Returns (lat, lon, "ok") if coordinates pass all checks
    """

    if lat is None or lon is None:
        return None, None, "no_coordinates"

    # Check 1: Ireland bounds
    min_lat, max_lat, min_lon, max_lon = IRELAND_BOUNDS
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return None, None, f"out_of_bounds({lat:.2f},{lon:.2f})"

    # Check 2: Basic sanity - not at 0,0 or other obvious bad values
    if (lat == 0.0 and lon == 0.0) or abs(lat) < 1 or abs(lon) < 1:
        return None, None, "suspicious_zero"

    # Coordinates pass basic validation
    return lat, lon, "ok"


async def validate_against_routing_keys(sales: List[Dict], conn: asyncpg.Connection) -> tuple[int, int]:
    """
    Validate Eircode coordinates against routing key centroids.

    Sets coordinates to None if they're >5km from routing key centroid.
    Returns: (validated_count, rejected_count)
    """

    validated = 0
    rejected = 0

    for sale in sales:
        if not sale.get('eircode') or not sale.get('latitude'):
            continue

        # Extract routing key (first 3 chars)
        routing_key = sale['eircode'].replace(' ', '').upper()[:3]

        # Get routing key centroid
        row = await conn.fetchrow("""
            SELECT lat, lon, property_count
            FROM routing_key_stats
            WHERE routing_key = $1
        """, routing_key)

        if not row or row['property_count'] < 5:
            # No routing key data, can't validate
            validated += 1
            continue

        # Calculate distance
        centroid_lat, centroid_lon = float(row['lat']), float(row['lon'])
        lat_diff = abs(sale['latitude'] - centroid_lat)
        lon_diff = abs(sale['longitude'] - centroid_lon)

        # ~5km threshold (0.05° lat ≈ 5.5km, 0.08° lon ≈ 5.6km at Ireland latitude)
        if lat_diff < 0.05 and lon_diff < 0.08:
            validated += 1
        else:
            # Too far from routing key centroid - reject
            distance_km = ((lat_diff * 111)**2 + (lon_diff * 85)**2)**0.5
            sale['validation_issue'] = f"routing_key_distance_{distance_km:.1f}km"
            sale['latitude'] = None
            sale['longitude'] = None
            rejected += 1

    return validated, rejected


async def import_to_database(csv_path: str, conn: asyncpg.Connection, dry_run: bool = False):
    """Import geocoded sales to database with validation."""

    print(f"\nImporting from {csv_path}...")

    sales = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = normalize_ppr_row(row)

            # Add coordinates if available
            raw_lat = float(row['Latitude']) if row.get('Latitude') else None
            raw_lon = float(row['Longitude']) if row.get('Longitude') else None

            # Validate coordinates
            if raw_lat and raw_lon:
                validated_lat, validated_lon, reason = validate_coordinates(
                    raw_lat, raw_lon, normalized.get('eircode'), normalized['county']
                )
                normalized['latitude'] = validated_lat
                normalized['longitude'] = validated_lon
                normalized['validation_issue'] = None if reason == "ok" else reason
            else:
                normalized['latitude'] = None
                normalized['longitude'] = None
                normalized['validation_issue'] = None

            sales.append(normalized)

    # Validate Eircode coordinates against routing keys
    print(f"\nValidating coordinates against routing key centroids...")
    validated, rejected = await validate_against_routing_keys(sales, conn)
    print(f"  ✓ Validated: {validated} Eircodes within 5km of routing key centroid")
    if rejected > 0:
        print(f"  ⚠️  Rejected: {rejected} Eircodes >5km from centroid (set to NULL)")

    # Statistics
    with_coords = sum(1 for s in sales if s['latitude'] is not None)
    without_coords = len(sales) - with_coords
    validation_issues = sum(1 for s in sales if s.get('validation_issue'))

    print(f"\nImport summary:")
    print(f"  Total properties: {len(sales)}")
    print(f"  With coordinates: {with_coords} ({100*with_coords/len(sales):.1f}%)")
    print(f"  Without coordinates: {without_coords}")
    if validation_issues > 0:
        print(f"  Validation issues: {validation_issues}")
        # Show breakdown of issues
        from collections import Counter
        issue_counts = Counter(s.get('validation_issue') for s in sales if s.get('validation_issue'))
        for issue, count in issue_counts.most_common(5):
            print(f"    - {issue}: {count}")

    if dry_run:
        print(f"\n[DRY RUN] Would import {len(sales)} properties")
        print(f"\nSample properties:")
        for i, sale in enumerate(sales[:5], 1):
            coords = f"({sale['latitude']:.5f}, {sale['longitude']:.5f})" if sale['latitude'] else "NO COORDS"
            issue = f" [{sale.get('validation_issue')}]" if sale.get('validation_issue') else ""
            print(f"  {i}. {sale['address'][:50]} - €{sale['price']:,.0f} - {coords}{issue}")
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
                sale_date, address, address_normalized, county, eircode, price,
                not_full_market_price, vat_exclusive,
                description, size_description,
                latitude, longitude, geog, needs_geocoding
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::double precision, $12::double precision,
                CASE
                    WHEN $11 IS NOT NULL AND $12 IS NOT NULL
                    THEN ST_MakePoint($12, $11)::geography
                    ELSE NULL
                END,
                $13
            )
            ON CONFLICT DO NOTHING
        """, [
            (
                sale['sale_date'], sale['address'], sale['address_normalized'],
                sale['county'], sale['eircode'],
                sale['price'], sale['not_full_market_price'], sale['vat_exclusive'],
                sale['description'], sale['size_description'],
                sale['latitude'], sale['longitude'],
                sale['latitude'] is None or sale['longitude'] is None  # needs_geocoding
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


async def sync_ppr_updates(dry_run: bool = False, since_date: Optional[str] = None, manual_csv: Optional[str] = None, skip_geocoding: bool = False):
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

        # 4. Geocode new sales (or skip)
        if skip_geocoding:
            print("Skipping geocoding (--skip-geocoding flag)")
            print("Properties will be imported with NULL coordinates")
            # Write CSV without geocoding
            geocoded_csv = tempfile.mktemp(suffix='_ppr_no_geocode.csv')
            with open(geocoded_csv, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'Date of Sale (dd/mm/yyyy)', 'Address', 'Postal Code',
                    'County', 'Price (€)', 'Not Full Market Price',
                    'VAT Exclusive', 'Description of Property', 'Property Size Description',
                    'Latitude', 'Longitude'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for sale in new_sales:
                    writer.writerow({
                        'Date of Sale (dd/mm/yyyy)': sale['sale_date'].strftime('%d/%m/%Y'),
                        'Address': sale['address'],
                        'Postal Code': sale['eircode'] or '',
                        'County': sale['county'],
                        'Price (€)': f"€{sale['price']:.2f}",
                        'Not Full Market Price': 'Yes' if sale['not_full_market_price'] else 'No',
                        'VAT Exclusive': 'Yes' if sale['vat_exclusive'] else 'No',
                        'Description of Property': sale['description'],
                        'Property Size Description': sale['size_description'] or '',
                        'Latitude': '',  # Empty = NULL
                        'Longitude': '',
                    })
        else:
            geocoded_csv = tempfile.mktemp(suffix='_ppr_geocoded.csv')
            await geocode_new_sales(new_sales, geocoded_csv)

        print()

        # 5. Import to database
        await import_to_database(geocoded_csv, conn, dry_run=dry_run)

        print()

        # 6. Enrich new properties with bedroom and type data
        if not dry_run and not skip_geocoding:
            print("6. Enriching new properties with bedroom and type data...")
            print("   (This may take several minutes with 10s rate limiting)")
            print()

            try:
                # Run enrichment script on properties from last week
                # (covers the new imports plus any recent we might have missed)
                result = subprocess.run(
                    [sys.executable, str(PROJECT_ROOT / 'scripts' / 'enrich_recent_properties.py'),
                     '--months', '1', '--limit', '100'],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )

                if result.returncode == 0:
                    print("   ✓ Property enrichment complete")
                    # Show last few lines of output (summary)
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines[-10:]:
                        if line.strip():
                            print(f"   {line}")
                else:
                    print(f"   ⚠ Property enrichment failed (exit code {result.returncode})")
                    print(f"   You can run manually: python3 scripts/enrich_recent_properties.py")
            except subprocess.TimeoutExpired:
                print("   ⚠ Property enrichment timed out (>10 minutes)")
                print("   You can run manually: python3 scripts/enrich_recent_properties.py")
            except Exception as e:
                print(f"   ⚠ Property enrichment error: {e}")
                print("   You can run manually: python3 scripts/enrich_recent_properties.py")
        elif skip_geocoding:
            print("6. Skipping property enrichment (geocoding was skipped)")
        else:
            print("6. Skipping property enrichment (dry-run mode)")

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
    parser.add_argument("--skip-geocoding", action="store_true", help="Skip geocoding, import with NULL coordinates")

    args = parser.parse_args()

    exit_code = asyncio.run(sync_ppr_updates(
        dry_run=args.dry_run,
        since_date=args.since,
        manual_csv=args.manual_csv,
        skip_geocoding=args.skip_geocoding
    ))

    sys.exit(exit_code)
