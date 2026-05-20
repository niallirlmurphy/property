#!/usr/bin/env python3
"""
Geocoding Quality Dashboard

Real-time monitoring dashboard for geocoding quality metrics.
Shows current state and trends over time.

Usage:
    python3 scripts/geocoding_dashboard.py
    python3 scripts/geocoding_dashboard.py --watch  # Auto-refresh every 60s
"""

import asyncio
import asyncpg
import os
import sys
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
PROGRESS_DB = "regeocode_progress.db"


async def get_overall_stats(pool: asyncpg.Pool):
    """Get overall geocoding statistics."""
    row = await pool.fetchrow("""
        SELECT
            COUNT(*) as total,
            COUNT(latitude) as geocoded,
            COUNT(*) - COUNT(latitude) as missing,
            ROUND(100.0 * COUNT(latitude) / COUNT(*), 1) as pct
        FROM properties
    """)
    return dict(row)


async def get_centroid_stats(pool: asyncpg.Pool):
    """Get centroid coordinate statistics."""
    # High priority (100+ addresses)
    high_count = await pool.fetchval("""
        SELECT COUNT(*)
        FROM (
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= 100
        ) sub
    """)

    # Medium priority (10-99 addresses)
    medium_count = await pool.fetchval("""
        SELECT COUNT(*)
        FROM (
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) BETWEEN 10 AND 99
        ) sub
    """)

    # Affected properties
    affected = await pool.fetchval("""
        WITH centroid_coords AS (
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= 100
        )
        SELECT COUNT(DISTINCT p.id)
        FROM properties p
        INNER JOIN centroid_coords c
            ON ABS(p.latitude - c.latitude) < 0.000001
            AND ABS(p.longitude - c.longitude) < 0.000001
        WHERE p.latitude IS NOT NULL
    """)

    return {
        'high_priority': high_count,
        'medium_priority': medium_count,
        'affected_properties': affected
    }


async def get_top_problem_coords(pool: asyncpg.Pool, limit: int = 5):
    """Get worst centroid coordinates."""
    rows = await pool.fetch("""
        SELECT
            latitude, longitude,
            COUNT(DISTINCT address) as addresses,
            COUNT(*) as sales,
            COUNT(DISTINCT county) as counties,
            STRING_AGG(DISTINCT county, ', ' ORDER BY county) as county_list
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


def get_regeocode_stats():
    """Get re-geocoding progress statistics."""
    if not os.path.exists(PROGRESS_DB):
        return None

    conn = sqlite3.connect(PROGRESS_DB)
    result = conn.execute("""
        SELECT processed, succeeded, failed, skipped, started_at, last_update
        FROM session_stats WHERE id = 1
    """).fetchone()
    conn.close()

    if not result or result[0] == 0:
        return None

    return {
        'processed': result[0],
        'succeeded': result[1],
        'failed': result[2],
        'skipped': result[3],
        'started_at': result[4],
        'last_update': result[5],
        'success_rate': 100.0 * result[1] / result[0] if result[0] > 0 else 0
    }


async def get_problem_locations(pool: asyncpg.Pool):
    """Check known problem locations."""
    # Nobber check
    nobber_wrong = await pool.fetchval("""
        SELECT COUNT(*)
        FROM properties
        WHERE address ILIKE '%nobber%'
          AND latitude IS NOT NULL
          AND ABS(latitude - 53.717143) < 0.001
          AND ABS(longitude - (-7.062706)) < 0.001
    """)

    nobber_total = await pool.fetchval("""
        SELECT COUNT(*)
        FROM properties
        WHERE address ILIKE '%nobber%'
          AND latitude IS NOT NULL
    """)

    return {
        'nobber': {
            'total': nobber_total,
            'wrong_coords': nobber_wrong,
            'fixed': nobber_wrong == 0
        }
    }


def print_dashboard(data):
    """Print formatted dashboard."""
    clear_screen = "\033[2J\033[H" if "--watch" in sys.argv else ""
    print(clear_screen)

    print("╔" + "═" * 78 + "╗")
    print("║" + " GEOCODING QUALITY DASHBOARD".center(78) + "║")
    print("║" + f" Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    # Overall Stats
    stats = data['overall']
    print("\n┌─ OVERALL STATISTICS " + "─" * 57 + "┐")
    print(f"│ Total Properties:        {stats['total']:>10,}                                  │")
    print(f"│ Geocoded:                {stats['geocoded']:>10,}  ({stats['pct']:>5}%)                      │")
    print(f"│ Missing Coordinates:     {stats['missing']:>10,}  ({100-stats['pct']:>5.1f}%)                      │")
    print("└" + "─" * 78 + "┘")

    # Centroid Issues
    centroid = data['centroid']
    print("\n┌─ CENTROID ISSUES (Addresses at Generic Locations) " + "─" * 25 + "┐")
    print(f"│ HIGH Priority (100+ addresses/coord):   {centroid['high_priority']:>5}                         │")
    print(f"│ MEDIUM Priority (10-99 addresses/coord): {centroid['medium_priority']:>5}                         │")
    print(f"│ Total Affected Properties:              {centroid['affected_properties']:>10,}                   │")
    print("└" + "─" * 78 + "┘")

    # Top Problem Coordinates
    print("\n┌─ TOP 5 PROBLEM COORDINATES " + "─" * 49 + "┐")
    print("│ Coordinate                     Addresses    Sales      Counties         │")
    print("│" + "─" * 76 + "│")
    for coord in data['top_problems']:
        lat, lon = coord['latitude'], coord['longitude']
        coord_str = f"({lat:.4f}, {lon:.4f})"
        counties = coord['county_list'][:30] if coord['county_list'] else "Unknown"
        print(f"│ {coord_str:<30} {coord['addresses']:>6,}    {coord['sales']:>8,}   {counties:<10} │")
    print("└" + "─" * 78 + "┘")

    # Re-geocoding Progress
    regeocode = data.get('regeocode')
    if regeocode:
        print("\n┌─ RE-GEOCODING PROGRESS " + "─" * 53 + "┐")
        print(f"│ Started:           {regeocode['started_at']:<30}                     │")
        print(f"│ Last Update:       {regeocode['last_update']:<30}                     │")
        print(f"│ Total Processed:   {regeocode['processed']:>10,}                                     │")
        print(f"│ ✓ Succeeded:       {regeocode['succeeded']:>10,}  ({regeocode['success_rate']:>5.1f}%)                        │")
        print(f"│ ✗ Failed:          {regeocode['failed']:>10,}                                     │")
        print(f"│ ⊘ Skipped:         {regeocode['skipped']:>10,}                                     │")
        print("└" + "─" * 78 + "┘")
    else:
        print("\n┌─ RE-GEOCODING PROGRESS " + "─" * 53 + "┐")
        print("│ No re-geocoding runs yet                                                  │")
        print("│ Run: python3 scripts/regeocode_high_priority.py --apply                   │")
        print("└" + "─" * 78 + "┘")

    # Known Problem Locations
    problems = data['problems']
    print("\n┌─ KNOWN PROBLEM LOCATIONS " + "─" * 51 + "┐")
    nobber = problems['nobber']
    status = "✓ FIXED" if nobber['fixed'] else "✗ NEEDS FIX"
    print(f"│ Nobber, Meath:     {nobber['total']:>3} properties   {nobber['wrong_coords']:>3} at wrong coords  {status:<12} │")
    print("└" + "─" * 78 + "┘")

    # Status Summary
    print("\n┌─ STATUS SUMMARY " + "─" * 60 + "┐")

    # Calculate overall health score
    issues = 0
    if centroid['high_priority'] > 50:
        issues += 1
    if centroid['medium_priority'] > 200:
        issues += 1
    if not nobber['fixed']:
        issues += 1
    if stats['pct'] < 75.0:
        issues += 1

    if issues == 0:
        status = "🟢 EXCELLENT"
        message = "No major issues detected"
    elif issues == 1:
        status = "🟡 GOOD"
        message = "Minor issues present, monitoring recommended"
    elif issues == 2:
        status = "🟠 FAIR"
        message = "Some issues need attention"
    else:
        status = "🔴 NEEDS ATTENTION"
        message = "Multiple issues require action"

    print(f"│ Health: {status:<20} {message:<44} │")

    if centroid['high_priority'] > 50:
        print("│   ⚠ High priority centroids exceed threshold (>50)                        │")
    if centroid['medium_priority'] > 200:
        print("│   ⚠ Medium priority clusters exceed threshold (>200)                      │")
    if not nobber['fixed']:
        print("│   ⚠ Nobber coordinates need fixing                                        │")
    if stats['pct'] < 75.0:
        print("│   ⚠ Geocoding coverage below 75%                                          │")

    print("└" + "─" * 78 + "┘")

    if "--watch" in sys.argv:
        print("\n[Watching... Press Ctrl+C to exit]")


async def main():
    watch = "--watch" in sys.argv

    while True:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)

        try:
            data = {
                'overall': await get_overall_stats(pool),
                'centroid': await get_centroid_stats(pool),
                'top_problems': await get_top_problem_coords(pool),
                'regeocode': get_regeocode_stats(),
                'problems': await get_problem_locations(pool)
            }

            print_dashboard(data)

            if not watch:
                break

            await asyncio.sleep(60)  # Refresh every 60 seconds

        finally:
            await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDashboard closed.")
