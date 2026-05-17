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


def _autoaddress_lookup(address: str, county: str) -> "str | None":
    """
    Two-step Autoaddress lookup:
      1. autocomplete — get candidate addresses + lookup token
      2. lookup       — resolve token to full address including postcode (eircode)

    Returns the eircode string (e.g. "D14 XT52") or None if not found.
    """
    headers = {"Authorization": f"Bearer {AUTOADDRESS_KEY}", "User-Agent": "HomeIQ-eircode-enricher/1.0"}

    query = f"{address}, {county}" if county else address

    # Step 1: autocomplete
    try:
        r = requests.get(AA_AUTOCOMPLETE, params={"key": AUTOADDRESS_KEY, "address": query},
                         headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Autocomplete request failed for {query!r}: {e}")
        return None

    options = r.json().get("options", [])
    if not options:
        log.debug(f"No autocomplete options for {query!r}")
        return None

    # Step 2: lookup using the href from the best match
    lookup_href = options[0]["link"]["href"]
    try:
        r2 = requests.get(lookup_href, headers=headers, timeout=10)
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

    # Fetch rows with no eircode, prioritising recently sold (most likely to be searched)
    cur.execute("""
        SELECT id, address, county
        FROM properties
        WHERE eircode IS NULL
          AND latitude IS NOT NULL
        ORDER BY sale_date DESC
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
