#!/usr/bin/env python3
"""
Complete PPR import pipeline with all enhancements from 2026-07-09.

This script runs the full pipeline:
1. Import new sales from CSV (with address normalization)
2. Geocode addresses (with HTML cleaning, Eircode-first, bulk extraction)
3. Enrich properties (bedrooms, property types via DuckDuckGo)
4. Regenerate static area/eircode/county page data (backend API required)

Enhancements included:
- HTML entity cleaning (Tandy&#039;s → Tandy's)
- Eircode-first geocoding strategy
- Bulk sale address extraction (Units 1-76 → base address)
- Address normalization for reliable searches
- Improved DuckDuckGo scraping (full page text, not just snippets)
- MapboxClient wrapper with usage tracking

Usage:
    # Full pipeline (import + geocode + enrich)
    python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"

    # Just geocode + enrich recent imports
    python3 scripts/ppr_full_pipeline.py --skip-import

    # Dry run (preview without database changes)
    python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv" --dry-run

Options:
    --csv PATH              Path to PPR CSV file (required unless --skip-import)
    --skip-import           Skip import step (just geocode + enrich)
    --skip-geocoding        Skip geocoding step
    --skip-enrichment       Skip enrichment step
    --skip-page-data        Skip static page-data generation step
    --geocode-limit N       Limit geocoding to N properties (default: all)
    --enrich-limit N        Limit enrichment to N properties (default: 100)
    --enrich-rate-limit N   Seconds between enrichment requests (default: 5)
    --dry-run               Preview mode - no database changes
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

def run_command(cmd, description, dry_run=False):
    """Run shell command and handle errors."""
    if dry_run:
        print(f"\n[DRY RUN] Would run: {description}")
        print(f"  Command: {' '.join(cmd)}")
        return True

    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error in {description}")
        print(f"Exit code: {e.returncode}")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Complete PPR pipeline: import → geocode → enrich',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--csv', type=str, help='Path to PPR CSV file')
    parser.add_argument('--skip-import', action='store_true', help='Skip import step')
    parser.add_argument('--skip-geocoding', action='store_true', help='Skip geocoding step')
    parser.add_argument('--skip-enrichment', action='store_true', help='Skip enrichment step')
    parser.add_argument('--skip-page-data', action='store_true', help='Skip static page-data generation step')
    parser.add_argument('--geocode-limit', type=int, help='Limit geocoding to N properties')
    parser.add_argument('--enrich-limit', type=int, default=100, help='Limit enrichment (default: 100)')
    parser.add_argument('--enrich-rate-limit', type=int, default=5, help='Seconds between enrichment (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Preview mode - no changes')

    args = parser.parse_args()

    # Validation
    if not args.skip_import and not args.csv:
        parser.error("--csv required unless using --skip-import")

    if args.csv and not Path(args.csv).exists():
        print(f"❌ Error: CSV file not found: {args.csv}")
        return 1

    print("="*80)
    print("PPR FULL PIPELINE - Enhanced with 2026-07-09 improvements")
    print("="*80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No database changes will be made")

    print("\nPipeline steps:")
    print(f"  1. Import:     {'SKIP' if args.skip_import else 'YES'}")
    print(f"  2. Geocode:    {'SKIP' if args.skip_geocoding else 'YES'}")
    print(f"  3. Enrich:     {'SKIP' if args.skip_enrichment else 'YES'}")
    print(f"  4. Page data:  {'SKIP' if args.skip_page_data else 'YES'}")
    print()

    # Step 1: Import new sales from CSV
    if not args.skip_import:
        cmd = ['python3', 'scripts/sync_ppr_updates.py']
        if args.skip_geocoding:
            cmd.append('--skip-geocoding')

        success = run_command(
            cmd,
            "STEP 1: Import new sales from CSV",
            dry_run=args.dry_run
        )

        if not success:
            print("\n❌ Pipeline failed at import step")
            return 1

    # Step 2: Geocode addresses with MapboxClient (HTML cleaning, Eircode-first, bulk extraction)
    if not args.skip_geocoding:
        cmd = ['python3', 'scripts/geocode_mapbox_batch.py', '--needs-geocoding']

        if not args.dry_run:
            cmd.append('--apply')

        if args.geocode_limit:
            cmd.extend(['--limit', str(args.geocode_limit)])

        success = run_command(
            cmd,
            "STEP 2: Geocode addresses (MapboxClient with enhancements)",
            dry_run=args.dry_run
        )

        if not success:
            print("\n⚠️  Warning: Geocoding had errors, continuing to enrichment...")

    # Step 3: Enrich properties (bedrooms, types via DuckDuckGo full-page scraping)
    if not args.skip_enrichment:
        cmd = [
            'python3', 'scripts/enrich_batch6_2026.py',
            '--batch-size', str(args.enrich_limit),
            '--rate-limit', str(args.enrich_rate_limit)
        ]

        success = run_command(
            cmd,
            "STEP 3: Enrich properties (DuckDuckGo full-page scraping)",
            dry_run=args.dry_run
        )

        if not success:
            print("\n⚠️  Warning: Enrichment had errors")

    # Step 4: Regenerate static area/eircode/county page data (calls the backend API)
    if not args.skip_page_data:
        success = run_command(
            ['python3', 'scripts/generate_page_data.py'],
            "STEP 4: Generate static page data (area / eircode / county)",
            dry_run=args.dry_run
        )

        if not success:
            print("\n⚠️  Warning: Page-data generation had errors")

    # Summary
    print("\n" + "="*80)
    print("PIPELINE COMPLETE")
    print("="*80)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes were made")
        print("Run without --dry-run to apply changes")

    print("\nNext steps:")
    print("  - Check logs in logs/ directory")
    print("  - Monitor Mapbox usage: python3 scripts/mapbox_usage_tracker.py --current-month")
    print("  - Verify data quality in database")

    return 0

if __name__ == "__main__":
    sys.exit(main())
