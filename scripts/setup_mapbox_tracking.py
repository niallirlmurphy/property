#!/usr/bin/env python3
"""
Set up Mapbox usage tracking database table and backfill historical data.

This script:
1. Creates mapbox_usage table with indexes
2. Optionally backfills approximate usage from recent database changes
3. Displays current usage summary

Usage:
    python3 scripts/setup_mapbox_tracking.py
    python3 scripts/setup_mapbox_tracking.py --backfill  # Estimate historical usage
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


async def create_tracking_table():
    """Create mapbox_usage table and indexes."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    try:
        print("Creating mapbox_usage tracking table...")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mapbox_usage (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                source VARCHAR(100) NOT NULL,
                request_count INTEGER NOT NULL,
                success_count INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                operation VARCHAR(50),
                notes TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_mapbox_usage_timestamp
            ON mapbox_usage(timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_mapbox_usage_source
            ON mapbox_usage(source, timestamp DESC);

            COMMENT ON TABLE mapbox_usage IS
            'Tracks Mapbox API usage across all scripts and services to enforce 50k/month limit';
        """)

        print("✓ Table and indexes created successfully")

    finally:
        await conn.close()


async def backfill_historical_usage():
    """
    Estimate historical Mapbox usage based on recent geocoding_quality updates.

    This provides approximate historical data by counting properties geocoded
    in the last 30 days with geocoding_quality scores.
    """
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    try:
        print("\nEstimating historical usage from recent geocoding activity...")

        # Count properties geocoded in last 30 days with good quality scores
        # (Indicates Mapbox geocoding, which adds quality scores)
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as geocoded_count,
                MIN(created_at) as earliest_geocode
            FROM properties
            WHERE geocoding_quality >= 70
            AND created_at >= NOW() - INTERVAL '30 days'
        """)

        if result['geocoded_count'] > 0:
            print(f"Found {result['geocoded_count']:,} properties geocoded in last 30 days")
            print(f"Earliest: {result['earliest_geocode']}")

            # Create approximate backfill entry
            await conn.execute("""
                INSERT INTO mapbox_usage
                (timestamp, source, request_count, success_count, error_count, operation, notes)
                VALUES ($1, 'historical_backfill', $2, $3, 0, 'geocode',
                        'Estimated from properties table geocoding_quality column')
            """, result['earliest_geocode'], result['geocoded_count'], result['geocoded_count'])

            print(f"✓ Backfilled ~{result['geocoded_count']:,} requests from historical data")
        else:
            print("No recent geocoding activity found to backfill")

    finally:
        await conn.close()


async def display_current_usage():
    """Display current usage summary."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.mapbox_usage_tracker import MapboxUsageTracker

    print("\n" + "="*60)
    print("Current Mapbox Usage Summary")
    print("="*60)

    usage = await MapboxUsageTracker.get_current_month_usage()

    total = usage['total']
    print(f"\nMonth:           {usage['month']}")
    print(f"Total Requests:  {total['total_requests']:>8,}")
    print(f"  ✓ Successful:  {total['total_success']:>8,}")
    print(f"  ✗ Errors:      {total['total_errors']:>8,}")
    print(f"\nMonthly Limit:   {50_000:>8,}  (strict limit)")
    print(f"Remaining:       {usage['remaining']:>8,}")
    print(f"Usage:           {usage['percentage_used']:>7.1f}%")

    if total['total_requests'] > 0:
        print(f"Daily Average:   {usage['daily_average']:>8,.0f}")

    if usage['by_source']:
        print(f"\n{'-'*60}")
        print("Usage by Source:")
        print(f"{'-'*60}")
        for row in usage['by_source']:
            pct = (row['requests'] / total['total_requests']) * 100 if total['total_requests'] > 0 else 0
            print(f"{row['source']:30s} {row['requests']:>8,} ({pct:>5.1f}%)")

    print("="*60 + "\n")


async def main():
    import sys

    print("Mapbox Usage Tracking Setup")
    print("="*60 + "\n")

    # Create table
    await create_tracking_table()

    # Backfill if requested
    if '--backfill' in sys.argv:
        await backfill_historical_usage()

    # Show current usage
    await display_current_usage()

    print("\n✓ Setup complete!")
    print("\nNext steps:")
    print("1. Update scripts to use MapboxClient wrapper")
    print("2. Monitor usage with: python3 scripts/mapbox_usage_tracker.py")
    print("3. Check quota before large operations with MapboxClient.can_process()")


if __name__ == '__main__':
    asyncio.run(main())
