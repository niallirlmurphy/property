#!/usr/bin/env python3
"""
Monitor enrichment success rate and alert if it falls below threshold.
Usage: python3 scripts/monitor_enrichment_rate.py enrichment_batch3_results.json --threshold 75
"""

import json
import sys
import time
import argparse
from pathlib import Path

def check_success_rate(results_file, threshold=75):
    """Check enrichment success rate from results file."""
    if not Path(results_file).exists():
        return None, 0, "File not found"

    try:
        with open(results_file) as f:
            results = json.load(f)

        if len(results) == 0:
            return None, 0, "No results yet"

        total = len(results)
        enriched = sum(1 for r in results if r.get('bedrooms') or r.get('property_type'))
        success_rate = (enriched / total) * 100

        return success_rate, total, None
    except json.JSONDecodeError:
        return None, 0, "Invalid JSON"
    except Exception as e:
        return None, 0, str(e)

def main():
    parser = argparse.ArgumentParser(description='Monitor enrichment success rate')
    parser.add_argument('results_file', help='Path to enrichment results JSON file')
    parser.add_argument('--threshold', type=float, default=75.0,
                       help='Alert threshold percentage (default: 75)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300 = 5 min)')
    parser.add_argument('--once', action='store_true',
                       help='Check once and exit (no continuous monitoring)')

    args = parser.parse_args()

    print(f"Monitoring {args.results_file}")
    print(f"Alert threshold: {args.threshold}%")
    print(f"Check interval: {args.interval}s")
    print("-" * 60)

    last_count = 0
    alert_shown = False

    while True:
        rate, count, error = check_success_rate(args.results_file, args.threshold)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if error:
            print(f"[{timestamp}] {error}")
        elif rate is None:
            print(f"[{timestamp}] Waiting for results file...")
        else:
            # Show progress
            new_properties = count - last_count
            status = "✓" if rate >= args.threshold else "⚠"

            print(f"[{timestamp}] {status} {count:,} properties | "
                  f"Success: {rate:.1f}% | "
                  f"+{new_properties} since last check")

            # Alert if below threshold
            if rate < args.threshold and not alert_shown:
                print("\n" + "="*60)
                print(f"⚠️  ALERT: Success rate dropped below {args.threshold}%")
                print(f"   Current rate: {rate:.1f}%")
                print(f"   Properties processed: {count:,}")
                print("="*60 + "\n")
                alert_shown = True
            elif rate >= args.threshold and alert_shown:
                # Clear alert if rate improves
                alert_shown = False

            last_count = count

        if args.once:
            sys.exit(0 if rate and rate >= args.threshold else 1)

        time.sleep(args.interval)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        sys.exit(0)
