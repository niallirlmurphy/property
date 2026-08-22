#!/usr/bin/env python3
"""
Monitor database connectivity and auto-resume enrichment/normalization processes.

Usage:
    python3 scripts/monitor_and_resume.py           # Check once and resume if needed
    python3 scripts/monitor_and_resume.py --watch   # Continuous monitoring (check every 5 min)
    python3 scripts/monitor_and_resume.py --status  # Just show status, don't resume
"""

import os
import sys
import time
import subprocess
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')
PROJECT_DIR = '/Users/nmurphy/claude/property price project'

def test_database_connection():
    """Test if database is reachable."""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        conn.close()
        return True
    except Exception as e:
        return False

def get_database_stats():
    """Get current progress from database."""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        cur = conn.cursor()

        # Address normalization
        cur.execute('SELECT COUNT(*) FROM properties WHERE address_normalized IS NOT NULL')
        normalized = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM properties')
        total = cur.fetchone()[0]

        # Enrichment (last 3 months)
        cur.execute('''
            SELECT
                COUNT(*) as total,
                COUNT(bedrooms) as with_beds,
                COUNT(property_type) as with_type,
                COUNT(CASE WHEN bedrooms IS NOT NULL AND property_type IS NOT NULL THEN 1 END) as with_both
            FROM properties
            WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
        ''')
        total_3m, with_beds, with_type, with_both = cur.fetchone()

        conn.close()

        return {
            'normalization': {
                'completed': normalized,
                'total': total,
                'percent': round(normalized / total * 100, 1)
            },
            'enrichment': {
                'total': total_3m,
                'with_beds': with_beds,
                'with_type': with_type,
                'with_both': with_both,
                'percent': round(with_both / total_3m * 100, 1) if total_3m > 0 else 0
            }
        }
    except Exception as e:
        return None

def is_process_running(script_name):
    """Check if a process is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', f'python3.*{script_name}'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip()
    except:
        # If pgrep fails, check via ps
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            return script_name in result.stdout
        except:
            return False

def start_enrichment():
    """Start the batched enrichment process."""
    try:
        cmd = [
            'nohup',
            'python3',
            f'{PROJECT_DIR}/scripts/enrich_multi_batch.py',
            '--months', '3',
            '--batch-size', '50',
            '--batch-delay', '180'
        ]

        with open(f'{PROJECT_DIR}/logs/enrichment_batched.log', 'w') as log:
            subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_DIR,
                start_new_session=True
            )

        return True
    except Exception as e:
        print(f"Error starting enrichment: {e}")
        return False

def start_normalization():
    """Start the address normalization process."""
    try:
        cmd = [
            'nohup',
            'python3',
            f'{PROJECT_DIR}/scripts/normalize_addresses.py'
        ]

        with open(f'{PROJECT_DIR}/logs/normalize.log', 'w') as log:
            subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_DIR,
                start_new_session=True
            )

        return True
    except Exception as e:
        print(f"Error starting normalization: {e}")
        return False

def print_status(db_connected, stats, enrichment_running, normalization_running):
    """Print current status."""
    print("\n" + "="*80)
    print(f"STATUS CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Database connectivity
    if db_connected:
        print("✅ Database: CONNECTED")
    else:
        print("❌ Database: DISCONNECTED (network issue)")

    print()

    # Progress
    if stats:
        norm = stats['normalization']
        enrich = stats['enrichment']

        print("📝 ADDRESS NORMALIZATION:")
        print(f"   Progress: {norm['completed']:,} / {norm['total']:,} ({norm['percent']}%)")
        print(f"   Remaining: {norm['total'] - norm['completed']:,}")

        print("\n🏠 PROPERTY ENRICHMENT (Last 3 months):")
        print(f"   Total properties: {enrich['total']:,}")
        print(f"   With bedrooms: {enrich['with_beds']:,} ({enrich['with_beds']/enrich['total']*100:.1f}%)")
        print(f"   With type: {enrich['with_type']:,} ({enrich['with_type']/enrich['total']*100:.1f}%)")
        print(f"   With both: {enrich['with_both']:,} ({enrich['percent']}%)")
        print(f"   Still needed: {enrich['total'] - enrich['with_both']:,}")
    else:
        print("⚠️  Cannot retrieve progress (database unavailable)")

    print()

    # Process status
    print("🔄 RUNNING PROCESSES:")
    if enrichment_running:
        print("   ✅ Enrichment: RUNNING")
    else:
        print("   ❌ Enrichment: NOT RUNNING")

    if normalization_running:
        print("   ✅ Normalization: RUNNING")
    else:
        print("   ❌ Normalization: NOT RUNNING")

    print("="*80)

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring (check every 5 min)')
    parser.add_argument('--status', action='store_true', help='Show status only, do not resume')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300)')

    args = parser.parse_args()

    print("="*80)
    print("PROCESS MONITOR & AUTO-RESUME")
    print("="*80)

    if args.watch:
        print(f"Watching mode: checking every {args.interval} seconds")
        print("Press Ctrl+C to stop")
        print()

    iteration = 0

    while True:
        iteration += 1

        # Test database connection
        db_connected = test_database_connection()

        # Get current stats
        stats = get_database_stats() if db_connected else None

        # Check if processes are running
        enrichment_running = is_process_running('enrich_multi_batch.py')
        normalization_running = is_process_running('normalize_addresses.py')

        # Print status
        print_status(db_connected, stats, enrichment_running, normalization_running)

        # Auto-resume if needed (unless --status flag)
        if not args.status and db_connected:
            resumed = False

            if not enrichment_running and stats and stats['enrichment']['with_both'] < stats['enrichment']['total']:
                print("\n🚀 Resuming enrichment process...")
                if start_enrichment():
                    print("   ✅ Enrichment started")
                    enrichment_running = True
                    resumed = True
                else:
                    print("   ❌ Failed to start enrichment")

            if not normalization_running and stats and stats['normalization']['completed'] < stats['normalization']['total']:
                print("\n🚀 Resuming normalization process...")
                if start_normalization():
                    print("   ✅ Normalization started")
                    normalization_running = True
                    resumed = True
                else:
                    print("   ❌ Failed to start normalization")

            if resumed:
                print("\n✅ Processes resumed successfully")
            elif enrichment_running and normalization_running:
                print("\n✅ All processes already running")

        # Exit if not in watch mode
        if not args.watch:
            break

        # Wait for next check
        print(f"\n⏸️  Next check in {args.interval} seconds...")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            break

if __name__ == '__main__':
    main()
