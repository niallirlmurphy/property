#!/usr/bin/env python3
"""
Centralized Mapbox API usage tracker.

Tracks all Mapbox API requests across all scripts and services to prevent
exceeding the 100k/month free tier limit.

Database schema:
    CREATE TABLE IF NOT EXISTS mapbox_usage (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        source VARCHAR(100) NOT NULL,  -- script name or 'api'
        request_count INTEGER NOT NULL,
        success_count INTEGER NOT NULL,
        error_count INTEGER NOT NULL,
        operation VARCHAR(50),  -- 'geocode', 'batch_geocode', etc.
        notes TEXT
    );

Usage:
    from scripts.mapbox_usage_tracker import MapboxUsageTracker

    tracker = MapboxUsageTracker(source='geocode_mapbox_batch')
    async with tracker.session():
        # Make Mapbox API calls
        tracker.record_request(success=True)
        tracker.record_request(success=False)
    # Automatically saves to database on exit

    # Or manual control:
    await tracker.start()
    tracker.record_request(success=True)
    await tracker.save()
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()


class MapboxUsageTracker:
    """Thread-safe Mapbox API usage tracker with database persistence."""

    def __init__(self, source: str, operation: str = 'geocode', notes: Optional[str] = None):
        """
        Initialize tracker.

        Args:
            source: Script name (e.g., 'geocode_mapbox_batch', 'api', 'regeocode_high_priority')
            operation: Type of operation ('geocode', 'batch_geocode', 'search')
            notes: Optional notes about this tracking session
        """
        self.source = source
        self.operation = operation
        self.notes = notes
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        self._lock = asyncio.Lock()
        self._conn = None

    async def start(self):
        """Initialize database connection and ensure schema exists."""
        self._conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await self._ensure_schema()
        self.start_time = datetime.utcnow()

    async def _ensure_schema(self):
        """Create mapbox_usage table if it doesn't exist."""
        await self._conn.execute("""
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
        """)

    def record_request(self, success: bool = True, count: int = 1):
        """
        Record Mapbox API request(s).

        Args:
            success: Whether request succeeded
            count: Number of requests (for batch operations)
        """
        self.request_count += count
        if success:
            self.success_count += count
        else:
            self.error_count += count

    def record_batch(self, total: int, succeeded: int):
        """
        Record batch geocoding results.

        Args:
            total: Total properties in batch
            succeeded: Number that successfully geocoded
        """
        self.request_count += total
        self.success_count += succeeded
        self.error_count += (total - succeeded)

    async def save(self):
        """Save current usage to database."""
        if not self._conn:
            raise RuntimeError("Tracker not started. Call await tracker.start() first.")

        if self.request_count == 0:
            return  # Nothing to save

        async with self._lock:
            await self._conn.execute("""
                INSERT INTO mapbox_usage
                (source, request_count, success_count, error_count, operation, notes)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, self.source, self.request_count, self.success_count,
                 self.error_count, self.operation, self.notes)

    async def close(self):
        """Save and close database connection."""
        if self._conn:
            await self.save()
            await self._conn.close()
            self._conn = None

    @asynccontextmanager
    async def session(self):
        """Context manager for automatic start/save/close."""
        await self.start()
        try:
            yield self
        finally:
            await self.close()

    @staticmethod
    async def get_usage_summary(days: int = 30) -> Dict:
        """
        Get usage summary for the last N days.

        Args:
            days: Number of days to look back (default: 30 for current month)

        Returns:
            Dict with total requests, by source, and daily breakdown
        """
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Total usage
            total = await conn.fetchrow("""
                SELECT
                    COALESCE(SUM(request_count), 0) as total_requests,
                    COALESCE(SUM(success_count), 0) as total_success,
                    COALESCE(SUM(error_count), 0) as total_errors
                FROM mapbox_usage
                WHERE timestamp >= $1
            """, cutoff)

            # Usage by source
            by_source = await conn.fetch("""
                SELECT
                    source,
                    SUM(request_count) as requests,
                    SUM(success_count) as success,
                    SUM(error_count) as errors
                FROM mapbox_usage
                WHERE timestamp >= $1
                GROUP BY source
                ORDER BY requests DESC
            """, cutoff)

            # Daily breakdown
            daily = await conn.fetch("""
                SELECT
                    DATE(timestamp) as date,
                    SUM(request_count) as requests,
                    SUM(success_count) as success,
                    SUM(error_count) as errors
                FROM mapbox_usage
                WHERE timestamp >= $1
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, cutoff)

            return {
                'period_days': days,
                'total': dict(total),
                'by_source': [dict(row) for row in by_source],
                'daily': [dict(row) for row in daily],
                'remaining': 100_000 - total['total_requests'],
                'percentage_used': (total['total_requests'] / 100_000) * 100
            }
        finally:
            await conn.close()

    @staticmethod
    async def get_current_month_usage() -> Dict:
        """Get usage for current calendar month."""
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        try:
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)

            total = await conn.fetchrow("""
                SELECT
                    COALESCE(SUM(request_count), 0) as total_requests,
                    COALESCE(SUM(success_count), 0) as total_success,
                    COALESCE(SUM(error_count), 0) as total_errors
                FROM mapbox_usage
                WHERE timestamp >= $1
            """, month_start)

            by_source = await conn.fetch("""
                SELECT
                    source,
                    SUM(request_count) as requests,
                    SUM(success_count) as success,
                    SUM(error_count) as errors
                FROM mapbox_usage
                WHERE timestamp >= $1
                GROUP BY source
                ORDER BY requests DESC
            """, month_start)

            return {
                'month': now.strftime('%B %Y'),
                'total': dict(total),
                'by_source': [dict(row) for row in by_source],
                'remaining': 100_000 - total['total_requests'],
                'percentage_used': (total['total_requests'] / 100_000) * 100,
                'daily_average': total['total_requests'] / now.day
            }
        finally:
            await conn.close()

    @staticmethod
    async def check_limit(warn_threshold: float = 0.8) -> bool:
        """
        Check if approaching monthly limit.

        Args:
            warn_threshold: Warn when usage exceeds this fraction (0.8 = 80%)

        Returns:
            True if safe to proceed, False if should stop
        """
        usage = await MapboxUsageTracker.get_current_month_usage()
        total = usage['total']['total_requests']

        if total >= 100_000:
            print(f"❌ MAPBOX LIMIT REACHED: {total:,} / 100,000 requests used")
            return False

        percentage = usage['percentage_used']
        if percentage >= warn_threshold * 100:
            print(f"⚠️  WARNING: {percentage:.1f}% of monthly Mapbox limit used ({total:,} / 100,000)")
            print(f"   Remaining: {usage['remaining']:,} requests")
            return True

        print(f"✓ Mapbox usage OK: {percentage:.1f}% used ({total:,} / 100,000)")
        return True


async def print_usage_report(days: int = 30):
    """Print formatted usage report."""
    summary = await MapboxUsageTracker.get_usage_summary(days)

    print(f"\n{'='*60}")
    print(f"Mapbox API Usage Report - Last {days} Days")
    print(f"{'='*60}\n")

    total = summary['total']
    print(f"Total Requests:  {total['total_requests']:>8,}")
    print(f"  ✓ Successful:  {total['total_success']:>8,}")
    print(f"  ✗ Errors:      {total['total_errors']:>8,}")
    print(f"\nMonthly Limit:   {100_000:>8,}")
    print(f"Remaining:       {summary['remaining']:>8,}")
    print(f"Usage:           {summary['percentage_used']:>7.1f}%")

    if summary['by_source']:
        print(f"\n{'-'*60}")
        print("Usage by Source:")
        print(f"{'-'*60}")
        for row in summary['by_source']:
            print(f"{row['source']:30s} {row['requests']:>8,} requests")

    if summary['daily']:
        print(f"\n{'-'*60}")
        print("Recent Daily Usage:")
        print(f"{'-'*60}")
        for row in summary['daily'][:7]:  # Show last 7 days
            print(f"{row['date']} {row['requests']:>8,} requests")

    print(f"{'='*60}\n")


async def print_current_month_report():
    """Print formatted report for current calendar month."""
    usage = await MapboxUsageTracker.get_current_month_usage()

    print(f"\n{'='*60}")
    print(f"Mapbox API Usage - {usage['month']}")
    print(f"{'='*60}\n")

    total = usage['total']
    print(f"Total Requests:  {total['total_requests']:>8,}")
    print(f"  ✓ Successful:  {total['total_success']:>8,}")
    print(f"  ✗ Errors:      {total['total_errors']:>8,}")
    print(f"\nMonthly Limit:   {100_000:>8,}")
    print(f"Remaining:       {usage['remaining']:>8,}")
    print(f"Usage:           {usage['percentage_used']:>7.1f}%")
    print(f"Daily Average:   {usage['daily_average']:>8,.0f}")

    if usage['by_source']:
        print(f"\n{'-'*60}")
        print("Usage by Source:")
        print(f"{'-'*60}")
        for row in usage['by_source']:
            pct = (row['requests'] / total['total_requests']) * 100
            print(f"{row['source']:30s} {row['requests']:>8,} ({pct:>5.1f}%)")

    print(f"{'='*60}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--current-month':
        asyncio.run(print_current_month_report())
    else:
        days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
        asyncio.run(print_usage_report(days))
