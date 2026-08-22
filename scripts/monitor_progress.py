#!/usr/bin/env python3
"""
Monitor batch processing progress and report updates.
Reads from the state file updated by batch_process_properties.py
"""

import json
import time
import os
from datetime import datetime

STATE_FILE = '/Users/nmurphy/claude/property price project/scripts/batch_process_state.json'
CHECK_INTERVAL = 900  # 15 minutes

def format_time_delta(start_iso):
    """Format time elapsed since start."""
    start = datetime.fromisoformat(start_iso)
    elapsed = datetime.now() - start
    hours = int(elapsed.total_seconds() // 3600)
    minutes = int((elapsed.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"

def print_progress_report(state):
    """Print formatted progress report."""
    print("\n" + "=" * 80)
    print(f"BATCH PROCESSING PROGRESS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Time tracking
    elapsed = format_time_delta(state['started_at'])
    print(f"\nRunning since: {state['started_at']}")
    print(f"Elapsed time: {elapsed}")
    print(f"Status: {state['status']}")

    # Normalization progress
    norm = state['normalization']
    print(f"\n📝 ADDRESS NORMALIZATION:")
    print(f"   Progress: {norm['completed']:,} / {norm['total']:,} ({norm['percent']}%)")
    print(f"   Remaining: {norm['total'] - norm['completed']:,} properties")
    print(f"   Batches completed: {norm['batches_run']}")
    if norm['last_batch_time']:
        print(f"   Last batch: {norm['last_batch_time']}")

    # Enrichment progress
    enrich = state['enrichment']
    print(f"\n🏠 PROPERTY ENRICHMENT (Last 3 months):")
    print(f"   Progress: {enrich['completed']:,} / {enrich['total']:,} ({enrich['percent']}%)")
    print(f"   Remaining: {enrich['total'] - enrich['completed']:,} properties")
    print(f"   Batches completed: {enrich['batches_run']}")
    if enrich['last_batch_time']:
        print(f"   Last batch: {enrich['last_batch_time']}")

    # Estimates
    if norm['completed'] < norm['total']:
        remaining_norm = norm['total'] - norm['completed']
        print(f"\n⏱️  ESTIMATES:")
        print(f"   ~{remaining_norm // 5000} normalization batches remaining")

    if enrich['completed'] < enrich['total']:
        remaining_enrich = enrich['total'] - enrich['completed']
        batches_left = (remaining_enrich + 49) // 50  # Round up
        # Each batch takes ~8-10 minutes due to rate limiting
        est_minutes = batches_left * 9
        est_hours = est_minutes / 60
        print(f"   ~{batches_left} enrichment batches remaining (~{est_hours:.1f} hours)")

    print("=" * 80)

def monitor():
    """Continuously monitor and report progress."""
    print("Starting progress monitor...")
    print(f"Will report every {CHECK_INTERVAL // 60} minutes")
    print("Press Ctrl+C to stop monitoring\n")

    last_report = None

    while True:
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)

                # Print report if it's time or if this is the first run
                current_update = state.get('last_updated')
                if last_report != current_update:
                    print_progress_report(state)
                    last_report = current_update

                    # Check if complete
                    if state.get('status') == 'completed':
                        print("\n✅ Processing complete! Monitor exiting.")
                        break
            else:
                print(f"Waiting for state file to be created...")

            time.sleep(60)  # Check every minute, but only report based on state updates

        except KeyboardInterrupt:
            print("\n\nMonitor stopped by user.")
            break
        except Exception as e:
            print(f"Error reading state: {e}")
            time.sleep(60)

if __name__ == '__main__':
    monitor()
