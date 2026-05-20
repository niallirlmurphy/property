#!/usr/bin/env python3
"""
Demand-driven eircode enrichment worker.

Reads up to DAILY_LIMIT properties with eircode IS NULL from the DB,
looks up each address via the Autoaddress.com API, and writes the result back.

Usage:
    AUTOADDRESS_KEY=pub_xxx DATABASE_URL=xxx python3 db/eircode_enrich.py [--limit N] [--dry-run]

Run daily (e.g. via cron or a simple shell script).
Free trial: 150 total lookups. Paid tiers give higher allowances.
"""

import os
import sys
import time
import logging
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DATABASE_URL    = os.environ["DATABASE_URL"]
AUTOADDRESS_KEY = os.environ.get("AUTOADDRESS_KEY", "")
DAILY_LIMIT     = int(next((sys.argv[sys.argv.index("--limit") + 1]
                            for i, a in enumerate(sys.argv) if a == "--limit"), 100))
DRY_RUN         = "--dry-run" in sys.argv
DELAY_SECS      = 1.1  # stay well under any rate limit

AA_AUTOCOMPLETE = "https://api.autoaddress.com/3.0/autocomplete"
AA_LOOKUP       = "https://api.autoaddress.com/3.0/lookup"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _clean_address(address: str) -> str:
    """Clean PPR address for better Autoaddress matching."""
    import re

    # Remove common noise that prevents matches
    cleaned = address
    cleaned = re.sub(r'\bMinisters?\s+Road\b', '', cleaned, flags=re.I)  # "Ministers Road"
    cleaned = re.sub(r'\bChurch\s+Fields\s+(East|West|Park)\b', 'Church Fields', cleaned, flags=re.I)
    cleaned = re.sub(r'\bMiller\s*[\'S]*\s+Glen\b', 'Millers Glen', cleaned, flags=re.I)
    cleaned = re.sub(r',\s*,', ',', cleaned)  # Remove double commas
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
    cleaned = cleaned.strip(', ')

    return cleaned


def _autoaddress_lookup(address: str, county: str) -> "str | None":
    """
    Two-step Autoaddress lookup:
      1. autocomplete — get candidate addresses + lookup token
      2. lookup       — resolve token to full address including postcode (eircode)

    Returns the eircode string (e.g. "D14 XT52") or None if not found.
    """
    cleaned_address = _clean_address(address)
    query = f"{cleaned_address}, {county}" if county else cleaned_address

    # Step 1: autocomplete
    try:
        # Use 'key' parameter (not Authorization header) for Autoaddress API
        r = requests.get(AA_AUTOCOMPLETE, params={"key": AUTOADDRESS_KEY, "address": query},
                         headers={"User-Agent": "HomeIQ-eircode-enricher/1.0"}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Autocomplete request failed for {query!r}: {e}")
        return None

    options = r.json().get("options", [])
    if not options:
        log.debug(f"No autocomplete options for {query!r}")
        return None

    # Filter to only "lookup" rel links (not "drilldown" which need more steps)
    lookup_options = [opt for opt in options if opt.get("link", {}).get("rel") == "lookup"]
    if not lookup_options:
        log.debug(f"No direct lookup options for {query!r} (only drilldowns)")
        return None

    # Step 2: lookup using the href from the best match
    lookup_href = lookup_options[0]["link"]["href"]
    try:
        r2 = requests.get(lookup_href, headers={"User-Agent": "HomeIQ-eircode-enricher/1.0"}, timeout=10)
        r2.raise_for_status()
    except Exception as e:
        log.warning(f"Lookup request failed for {query!r}: {e}")
        return None

    data = r2.json()
    postcode = data.get("address", {}).get("postcode", {}).get("value", "").strip()
    return postcode or None


def run():
    if not AUTOADDRESS_KEY:
        print("ERROR: AUTOADDRESS_KEY not set. Export it or add to backend/.env")
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()

    # Fetch rows with no eircode, prioritizing addresses most likely to have Eircodes:
    # 1. Urban areas (Dublin, Cork, Galway, Limerick, Waterford)
    # 2. Addresses with house numbers (more structured)
    # 3. Recent sales (more likely to be searched)
    # 4. Has coordinates (already validated)
    cur.execute("""
        SELECT id, address, county
        FROM properties
        WHERE eircode IS NULL
          AND latitude IS NOT NULL
          AND (
            -- Urban counties (high priority)
            county IN ('Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford',
                      'Louth', 'Kildare', 'Meath', 'Wicklow')
            -- OR has a house number (indicates structured address)
            OR address ~ '^[0-9]+'
          )
        ORDER BY
          -- Prioritize urban addresses
          CASE
            WHEN county IN ('Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford') THEN 1
            WHEN county IN ('Louth', 'Kildare', 'Meath', 'Wicklow') THEN 2
            ELSE 3
          END,
          -- Then prioritize addresses with house numbers
          CASE WHEN address ~ '^[0-9]+' THEN 1 ELSE 2 END,
          -- Finally by recency
          sale_date DESC
        LIMIT %s
    """, (DAILY_LIMIT,))
    rows = cur.fetchall()
    log.info(f"Processing {len(rows)} properties (limit={DAILY_LIMIT}, dry_run={DRY_RUN})")

    found = 0
    not_found = 0

    for prop_id, address, county in rows:
        eircode = _autoaddress_lookup(address, county)

        if eircode:
            log.info(f"  ID {prop_id}: {address!r} → {eircode}")
            found += 1
            if not DRY_RUN:
                cur.execute("UPDATE properties SET eircode = %s WHERE id = %s", (eircode, prop_id))
                conn.commit()
        else:
            log.debug(f"  ID {prop_id}: {address!r} → not found")
            not_found += 1

        time.sleep(DELAY_SECS)

    log.info(f"Done. Found: {found}, Not found: {not_found}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    if DRY_RUN:
        log.info("--- DRY RUN --- no DB writes")
    run()
