#!/usr/bin/env python3
"""
Report searches the backend could not geocode (table geocode_misses).

Search geocoding (backend/main.py::resolve_location) uses only our own data, no
Mapbox. Every query it can't place is logged here; check this now and then to see
whether misses are frequent enough to justify bringing an external geocoder back.

Usage:
    python3 scripts/geocode_misses_report.py            # last 30 days
    python3 scripts/geocode_misses_report.py --days 7
"""

import argparse
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")


async def main(days: int) -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], statement_cache_size=0,
                                 server_settings={"statement_timeout": "20000"})
    try:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM geocode_misses WHERE ts > NOW() - make_interval(days => $1)", days)
        print(f"Geocode misses, last {days} days: {total}")
        rows = await conn.fetch("""
            SELECT LOWER(TRIM(query)) AS q, county, COUNT(*) AS n, MAX(ts) AS last_seen
            FROM geocode_misses
            WHERE ts > NOW() - make_interval(days => $1)
            GROUP BY 1, 2
            ORDER BY n DESC, last_seen DESC
            LIMIT 50
        """, days)
        for r in rows:
            county = f" [{r['county']}]" if r["county"] else ""
            print(f"{r['n']:5}  {r['last_seen']:%Y-%m-%d}  {r['q']}{county}")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--days", type=int, default=30)
    asyncio.run(main(parser.parse_args().days))
