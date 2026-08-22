#!/usr/bin/env python3
"""
Run address normalization and property enrichment in batches with progress reporting.

Usage:
    python3 scripts/batch_process_properties.py
    python3 scripts/batch_process_properties.py --resume  # Resume from saved state
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

BATCH_SIZE = 5000  # Normalize 5k addresses per batch
ENRICHMENT_BATCH_SIZE = 50  # Enrich 50 properties per batch (10s rate limit = ~8-10 min per batch)
PROGRESS_INTERVAL = 900  # 15 minutes in seconds
STATE_FILE = '/Users/nmurphy/claude/property price project/scripts/batch_process_state.json'

def load_state():
    """Load processing state from file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_state(state):
    """Save processing state to file."""
    state['last_updated'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

def get_normalization_progress():
    """Get count of properties with normalized addresses."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM properties WHERE address_normalized IS NOT NULL")
    normalized_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM properties")
    total_count = cur.fetchone()[0]

    conn.close()

    return normalized_count, total_count

def get_enrichment_progress():
    """Get count of recently enriched properties (last 3 months)."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Properties from last 3 months
    cur.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
    """)
    total_recent = cur.fetchone()[0]

    # Properties from last 3 months with enrichment data
    cur.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
        AND (bedrooms IS NOT NULL OR property_type IS NOT NULL)
    """)
    enriched_recent = cur.fetchone()[0]

    conn.close()

    return enriched_recent, total_recent

def run_normalization_batch(state):
    """Run one batch of address normalization."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running normalization batch ({BATCH_SIZE} properties)...")

    result = subprocess.run(
        ['python3', 'scripts/normalize_addresses.py', '--limit', str(BATCH_SIZE)],
        cwd='/Users/nmurphy/claude/property price project',
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✓ Normalization batch completed")
        state['normalization']['batches_run'] += 1
        state['normalization']['last_batch_time'] = datetime.now().isoformat()

        # Check if we're done
        normalized, total = get_normalization_progress()
        state['normalization']['completed'] = normalized
        state['normalization']['total'] = total
        state['normalization']['percent'] = round(normalized / total * 100, 1)
        save_state(state)

        if normalized >= total:
            print(f"✓ All addresses normalized ({normalized:,}/{total:,})")
            return True
    else:
        print(f"✗ Normalization batch failed: {result.stderr[:200]}")

    return False

def run_enrichment_batch(state):
    """Run one batch of property enrichment."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running enrichment batch ({ENRICHMENT_BATCH_SIZE} properties)...")

    result = subprocess.run(
        ['python3', 'scripts/enrich_recent_properties.py', '--months', '3', '--limit', str(ENRICHMENT_BATCH_SIZE)],
        cwd='/Users/nmurphy/claude/property price project',
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✓ Enrichment batch completed")
        state['enrichment']['batches_run'] += 1
        state['enrichment']['last_batch_time'] = datetime.now().isoformat()

        # Check progress
        enriched, total = get_enrichment_progress()
        state['enrichment']['completed'] = enriched
        state['enrichment']['total'] = total
        state['enrichment']['percent'] = round(enriched / total * 100, 1) if total > 0 else 0
        save_state(state)

        if enriched >= total:
            print(f"✓ All recent properties enriched ({enriched:,}/{total:,})")
            return True
    else:
        print(f"✗ Enrichment batch failed: {result.stderr[:200]}")

    return False

def main():
    """Main batch processing loop."""
    print("=" * 70)
    print("BATCH PROCESSING: Address Normalization + Property Enrichment")
    print("=" * 70)

    # Load or create state
    state = load_state()
    if state:
        print(f"\nResuming from saved state (last updated: {state.get('last_updated', 'unknown')})")
    else:
        print("\nStarting fresh...")
        state = {
            'started_at': datetime.now().isoformat(),
            'status': 'running',
            'normalization': {
                'completed': 0,
                'total': 0,
                'percent': 0.0,
                'batches_run': 0,
                'last_batch_time': None
            },
            'enrichment': {
                'completed': 0,
                'total': 0,
                'percent': 0.0,
                'batches_run': 0,
                'last_batch_time': None
            }
        }

    # Initial progress
    normalized, total = get_normalization_progress()
    enriched, total_recent = get_enrichment_progress()

    # Update state with current values
    state['normalization']['completed'] = normalized
    state['normalization']['total'] = total
    state['normalization']['percent'] = round(normalized / total * 100, 1)
    state['enrichment']['completed'] = enriched
    state['enrichment']['total'] = total_recent
    state['enrichment']['percent'] = round(enriched / total_recent * 100, 1) if total_recent > 0 else 0
    save_state(state)

    print(f"\nInitial status:")
    print(f"  Normalized addresses: {normalized:,}/{total:,} ({normalized/total*100:.1f}%)")
    print(f"  Enriched (last 3 months): {enriched:,}/{total_recent:,} ({enriched/total_recent*100 if total_recent > 0 else 0:.1f}%)")

    normalization_done = (normalized >= total)
    enrichment_done = (enriched >= total_recent)

    last_report_time = time.time()

    while not (normalization_done and enrichment_done):
        cycle_start = time.time()

        # Run normalization batch
        if not normalization_done:
            normalization_done = run_normalization_batch(state)

        # Run enrichment batch (with 10s rate limiting built-in)
        if not enrichment_done:
            enrichment_done = run_enrichment_batch(state)

        # Report progress every 15 minutes
        if time.time() - last_report_time >= PROGRESS_INTERVAL:
            normalized, total = get_normalization_progress()
            enriched, total_recent = get_enrichment_progress()

            print("\n" + "=" * 70)
            print(f"PROGRESS REPORT [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print("=" * 70)
            print(f"Normalized addresses: {normalized:,}/{total:,} ({normalized/total*100:.1f}%)")
            print(f"Enriched (last 3 months): {enriched:,}/{total_recent:,} ({enriched/total_recent*100 if total_recent > 0 else 0:.1f}%)")
            print(f"Batches: Normalization={state['normalization']['batches_run']}, Enrichment={state['enrichment']['batches_run']}")
            print("=" * 70)

            last_report_time = time.time()

        # Small delay between cycles if both still running
        if not (normalization_done and enrichment_done):
            time.sleep(5)

    # Final report
    state['status'] = 'completed'
    state['completed_at'] = datetime.now().isoformat()
    save_state(state)

    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE!")
    print("=" * 70)
    normalized, total = get_normalization_progress()
    enriched, total_recent = get_enrichment_progress()
    print(f"Final normalized addresses: {normalized:,}/{total:,} ({normalized/total*100:.1f}%)")
    print(f"Final enriched (last 3 months): {enriched:,}/{total_recent:,} ({enriched/total_recent*100 if total_recent > 0 else 0:.1f}%)")
    print(f"Total batches: Normalization={state['normalization']['batches_run']}, Enrichment={state['enrichment']['batches_run']}")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
