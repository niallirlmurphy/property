#!/usr/bin/env python3
"""
Monitor Batch 4 enrichment progress.
Quick status check without interrupting the running process.
"""

import json
import os
from datetime import datetime

def monitor_batch4():
    results_file = 'enrichment_batch4_results_20260617_122837.json'
    input_file = 'enrichment_batch4_input_20260617_122837.json'

    if not os.path.exists(results_file):
        print("❌ Results file not found")
        return

    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)

    # Calculate stats
    total = len(results)
    success = sum(1 for r in results if r.get('success'))
    failed = total - success
    with_beds = sum(1 for r in results if r.get('bedrooms'))
    with_type = sum(1 for r in results if r.get('property_type'))
    both = sum(1 for r in results if r.get('bedrooms') and r.get('property_type'))

    # Calculate timing
    start_time = datetime.fromtimestamp(os.path.getmtime(input_file))
    current_time = datetime.now()
    elapsed_hours = (current_time - start_time).total_seconds() / 3600

    # Progress
    progress_pct = total / 5000 * 100
    success_rate = success / total * 100 if total > 0 else 0

    # ETA
    if total > 100:
        rate = total / (elapsed_hours * 60)  # per minute
        remaining = 5000 - total
        eta_minutes = remaining / rate if rate > 0 else 0
        eta_hours = eta_minutes / 60
    else:
        eta_hours = 0

    # Print status
    print("=" * 60)
    print(f"BATCH 4 ENRICHMENT MONITOR - {current_time.strftime('%H:%M:%S')}")
    print("=" * 60)
    print(f"\nProgress: {total:,} / 5,000 ({progress_pct:.1f}%)")
    print(f"Elapsed: {elapsed_hours:.1f} hours")
    print(f"Remaining: {5000-total:,} properties")

    if eta_hours > 0:
        completion = datetime.fromtimestamp(current_time.timestamp() + eta_hours * 3600)
        print(f"ETA: {eta_hours:.1f}h ({completion.strftime('%a %H:%M')})")

    print(f"\nSuccess Rate: {success_rate:.1f}%", end="")
    if success_rate >= 75:
        print(" ✅ (Target: >75%)")
    elif success_rate >= 70:
        print(" ⚠️  (Target: >75%)")
    else:
        print(" ❌ (Target: >75%)")

    print(f"  Success: {success:,}")
    print(f"  Failed:  {failed:,}")

    print(f"\nEnrichment:")
    print(f"  Bedrooms: {with_beds:,} ({with_beds/total*100:.1f}%)")
    print(f"  Type:     {with_type:,} ({with_type/total*100:.1f}%)")
    print(f"  Both:     {both:,} ({both/total*100:.1f}%)")

    # Expected final
    expected_success = int(5000 * (success/total)) if total > 0 else 0
    print(f"\nExpected Final: ~{expected_success:,} enriched properties")
    print("=" * 60)

if __name__ == "__main__":
    monitor_batch4()
