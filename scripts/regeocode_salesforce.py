#!/usr/bin/env python3
"""
Re-geocode properties using Salesforce Maps & Location Services API.

Salesforce provides high-quality geocoding with good international coverage.

Requirements:
- Salesforce account with Maps & Location Services enabled
- API credentials (instance URL, client ID, client secret, username, password)

Setup:
1. Enable Maps & Location Services in your Salesforce org
2. Create a Connected App with OAuth2 credentials
3. Add credentials to backend/.env:
   SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
   SALESFORCE_CLIENT_ID=your_client_id
   SALESFORCE_CLIENT_SECRET=your_client_secret
   SALESFORCE_USERNAME=your_username
   SALESFORCE_PASSWORD=your_password
   SALESFORCE_SECURITY_TOKEN=your_security_token

API Limits:
- Standard: 5,000 geocoding requests per day
- Higher tiers available with additional licenses

Usage:
    python3 scripts/regeocode_salesforce.py [--apply] [--limit N] [--county COUNTY]
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import time
import sqlite3
from datetime import datetime
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
SF_INSTANCE_URL = os.environ.get("SALESFORCE_INSTANCE_URL", "")
SF_CLIENT_ID = os.environ.get("SALESFORCE_CLIENT_ID", "")
SF_CLIENT_SECRET = os.environ.get("SALESFORCE_CLIENT_SECRET", "")
SF_USERNAME = os.environ.get("SALESFORCE_USERNAME", "")
SF_PASSWORD = os.environ.get("SALESFORCE_PASSWORD", "")
SF_SECURITY_TOKEN = os.environ.get("SALESFORCE_SECURITY_TOKEN", "")

PROGRESS_DB = "regeocode_salesforce_progress.db"

# Rate limits
SF_RATE_LIMIT = 5.0  # 5 requests per second (conservative)
SF_DAILY_LIMIT = 5000  # Standard tier


class SalesforceGeocoder:
    """Salesforce Maps & Location Services geocoding client."""

    def __init__(self):
        self.access_token = None
        self.token_expires = 0
        self.requests_today = 0
        self.last_request_date = None

    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Authenticate with Salesforce OAuth2."""
        if not all([SF_INSTANCE_URL, SF_CLIENT_ID, SF_CLIENT_SECRET, SF_USERNAME, SF_PASSWORD]):
            print("❌ Salesforce credentials not configured")
            print("\nRequired environment variables:")
            print("  SALESFORCE_INSTANCE_URL")
            print("  SALESFORCE_CLIENT_ID")
            print("  SALESFORCE_CLIENT_SECRET")
            print("  SALESFORCE_USERNAME")
            print("  SALESFORCE_PASSWORD")
            print("  SALESFORCE_SECURITY_TOKEN")
            return False

        try:
            # OAuth2 password flow
            auth_url = f"{SF_INSTANCE_URL}/services/oauth2/token"
            password_with_token = SF_PASSWORD + (SF_SECURITY_TOKEN or "")

            resp = await client.post(auth_url, data={
                "grant_type": "password",
                "client_id": SF_CLIENT_ID,
                "client_secret": SF_CLIENT_SECRET,
                "username": SF_USERNAME,
                "password": password_with_token
            }, timeout=10.0)

            if resp.status_code != 200:
                print(f"❌ Salesforce authentication failed: {resp.status_code}")
                print(f"Response: {resp.text}")
                return False

            data = resp.json()
            self.access_token = data["access_token"]
            self.token_expires = time.time() + 7200  # 2 hours
            print("✓ Salesforce authentication successful")
            return True

        except Exception as e:
            print(f"❌ Salesforce authentication error: {e}")
            return False

    async def ensure_authenticated(self, client: httpx.AsyncClient) -> bool:
        """Ensure we have a valid access token."""
        if not self.access_token or time.time() >= self.token_expires:
            return await self.authenticate(client)
        return True

    def check_daily_limit(self) -> bool:
        """Check if we've hit the daily API limit."""
        today = datetime.now().date()
        if self.last_request_date != today:
            self.requests_today = 0
            self.last_request_date = today

        if self.requests_today >= SF_DAILY_LIMIT:
            print(f"⚠️  Daily API limit reached ({SF_DAILY_LIMIT} requests)")
            return False
        return True

    async def geocode(self, address: str, county: str, client: httpx.AsyncClient,
                     country: str = "Ireland") -> Optional[Tuple[float, float, float]]:
        """
        Geocode an address using Salesforce Maps API.
        Returns (lat, lon, accuracy_score) or None.
        """
        if not await self.ensure_authenticated(client):
            return None

        if not self.check_daily_limit():
            return None

        # Format address for Salesforce
        full_address = f"{address}, {county}, {country}"

        try:
            # Salesforce Geocoding API endpoint
            geocode_url = f"{SF_INSTANCE_URL}/services/data/v58.0/sobjects/Address/actions/geocode"

            resp = await client.post(
                geocode_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "addresses": [{
                        "street": address,
                        "city": county,
                        "country": country
                    }]
                },
                timeout=10.0
            )

            self.requests_today += 1
            await asyncio.sleep(1.0 / SF_RATE_LIMIT)  # Rate limit

            if resp.status_code != 200:
                print(f"  Salesforce API error: {resp.status_code} - {resp.text[:100]}")
                return None

            data = resp.json()

            # Parse response
            if data and len(data) > 0 and data[0].get("location"):
                location = data[0]["location"]
                lat = location.get("latitude")
                lon = location.get("longitude")
                accuracy = data[0].get("accuracy", 0.0)

                # Validate coordinates are in Ireland
                if lat and lon and 51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4:
                    return (float(lat), float(lon), float(accuracy))

        except Exception as e:
            print(f"  Salesforce geocoding error for {address}: {e}")

        return None


class ProgressTracker:
    """Track Salesforce re-geocoding progress."""

    def __init__(self, db_path: str = PROGRESS_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS salesforce_log (
                property_id INTEGER PRIMARY KEY,
                old_lat REAL,
                old_lon REAL,
                new_lat REAL,
                new_lon REAL,
                accuracy REAL,
                status TEXT,
                error TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS salesforce_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                started_at TEXT,
                last_update TEXT,
                processed INTEGER DEFAULT 0,
                succeeded INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                api_requests_today INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            INSERT INTO salesforce_stats (id, started_at, last_update)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_update = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def is_processed(self, property_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "SELECT 1 FROM salesforce_log WHERE property_id = ?",
            (property_id,)
        ).fetchone()
        conn.close()
        return result is not None

    def log_result(self, property_id: int, old_coords: Tuple[float, float],
                   new_coords: Optional[Tuple[float, float, float]],
                   status: str, error: str = None):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO salesforce_log
            (property_id, old_lat, old_lon, new_lat, new_lon, accuracy, status, error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            property_id,
            old_coords[0], old_coords[1],
            new_coords[0] if new_coords else None,
            new_coords[1] if new_coords else None,
            new_coords[2] if new_coords and len(new_coords) > 2 else None,
            status, error,
            datetime.now().isoformat()
        ))

        if status == 'success':
            conn.execute("UPDATE salesforce_stats SET succeeded = succeeded + 1, processed = processed + 1")
        elif status == 'failed':
            conn.execute("UPDATE salesforce_stats SET failed = failed + 1, processed = processed + 1")

        conn.execute("UPDATE salesforce_stats SET last_update = ?", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()


async def fetch_centroid_properties(pool: asyncpg.Pool, limit: int = None,
                                   county: str = None) -> list[dict]:
    """Fetch properties at centroid coordinates."""
    print("Fetching properties at centroid coordinates...")

    centroid_coords = await pool.fetch("""
        SELECT latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
    """)

    print(f"Found {len(centroid_coords)} centroid coordinates")

    properties = []
    for coord in centroid_coords:
        where_clauses = [
            "ABS(latitude - $1) < 0.000001",
            "ABS(longitude - $2) < 0.000001"
        ]
        params = [coord["latitude"], coord["longitude"]]
        idx = 3

        if county:
            where_clauses.append(f"LOWER(county) = LOWER(${idx})")
            params.append(county)

        where = " AND ".join(where_clauses)

        rows = await pool.fetch(f"""
            SELECT id, address, county, eircode, latitude, longitude
            FROM properties
            WHERE {where}
            ORDER BY
                CASE WHEN eircode IS NOT NULL THEN 0 ELSE 1 END,
                sale_date DESC
            LIMIT 500
        """, *params)

        for row in rows:
            properties.append(dict(row))
            if limit and len(properties) >= limit:
                return properties

    return properties


async def regeocode_with_salesforce(limit: int = None, dry_run: bool = True,
                                    county: str = None):
    """Re-geocode properties using Salesforce."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    tracker = ProgressTracker()
    geocoder = SalesforceGeocoder()

    try:
        properties = await fetch_centroid_properties(pool, limit=limit, county=county)

        print(f"\n{'='*70}")
        print(f"SALESFORCE RE-GEOCODING")
        print(f"{'='*70}")
        print(f"Properties to process: {len(properties):,}")
        print(f"Mode: {'DRY RUN' if dry_run else 'APPLY'}")
        print(f"Daily API limit: {SF_DAILY_LIMIT:,} requests")
        print()

        if dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made\n")

        async with httpx.AsyncClient() as client:
            # Authenticate
            if not await geocoder.authenticate(client):
                return

            success_count = 0
            failed_count = 0

            for i, prop in enumerate(properties, 1):
                if tracker.is_processed(prop["id"]):
                    continue

                if not geocoder.check_daily_limit():
                    print(f"\n⚠️  Stopping: Daily API limit reached")
                    break

                old_coords = (prop["latitude"], prop["longitude"])

                result = await geocoder.geocode(
                    prop["address"],
                    prop["county"] or "",
                    client=client
                )

                if result:
                    lat, lon, accuracy = result
                    success_count += 1
                    tracker.log_result(prop["id"], old_coords, result, 'success')

                    if not dry_run:
                        await pool.execute("""
                            UPDATE properties
                            SET latitude = $1, longitude = $2,
                                geog = ST_MakePoint($2, $1)::geography
                            WHERE id = $3
                        """, lat, lon, prop["id"])

                    if i <= 5 or i % 20 == 0:
                        print(f"  ✓ [{i}/{len(properties)}] {prop['address'][:50]}")
                        print(f"    Accuracy: {accuracy:.2f} | {old_coords[0]:.6f},{old_coords[1]:.6f} → {lat:.6f},{lon:.6f}")
                else:
                    failed_count += 1
                    tracker.log_result(prop["id"], old_coords, None, 'failed', 'No result from Salesforce')

                if i % 50 == 0:
                    print(f"\nProgress: {i}/{len(properties)} | Success: {success_count} | Failed: {failed_count}")
                    print(f"API requests today: {geocoder.requests_today}/{SF_DAILY_LIMIT}\n")

        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Processed: {i:,}")
        print(f"✓ Success: {success_count:,} ({100*success_count/i:.1f}%)")
        print(f"✗ Failed: {failed_count:,}")
        print(f"API requests used: {geocoder.requests_today:,}/{SF_DAILY_LIMIT:,}")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to commit.")

    finally:
        await pool.close()


async def main():
    dry_run = "--apply" not in sys.argv
    limit = None
    county = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]

    await regeocode_with_salesforce(limit=limit, dry_run=dry_run, county=county)


if __name__ == "__main__":
    asyncio.run(main())
