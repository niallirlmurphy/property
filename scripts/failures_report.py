#!/usr/bin/env python3
"""
Report failed searches and valuations (tables search_failures, valuation_failures).

Search geocoding (backend/main.py::resolve_location) uses only our own data, no
Mapbox; no_location rows show whether misses are frequent enough to justify
bringing an external geocoder back. no_results rows are queries we placed but had
no sales for; error rows are 5xx responses.

Usage:
    python3 scripts/failures_report.py            # last 30 days
    python3 scripts/failures_report.py --days 7
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
        print(f"Failed searches, last {days} days")
        totals = await conn.fetch("""
            SELECT reason, COUNT(*) AS n FROM search_failures
            WHERE ts > NOW() - make_interval(days => $1)
            GROUP BY 1 ORDER BY 2 DESC
        """, days)
        print("  " + (", ".join(f"{r['reason']}: {r['n']}" for r in totals) or "none"))
        rows = await conn.fetch("""
            SELECT reason, endpoint, LOWER(TRIM(query)) AS q, county,
                   COUNT(*) AS n, MAX(ts) AS last_seen
            FROM search_failures
            WHERE ts > NOW() - make_interval(days => $1)
            GROUP BY 1, 2, 3, 4
            ORDER BY n DESC, last_seen DESC
            LIMIT 50
        """, days)
        for r in rows:
            county = f" [{r['county']}]" if r["county"] else ""
            print(f"{r['n']:5}  {r['last_seen']:%Y-%m-%d}  {r['reason']:<11} "
                  f"{r['endpoint']:<14} {r['q']}{county}")

        print(f"\nFailed valuations, last {days} days")
        rows = await conn.fetch("""
            SELECT status_code, LOWER(TRIM(address)) AS a, county, detail,
                   COUNT(*) AS n, MAX(ts) AS last_seen
            FROM valuation_failures
            WHERE ts > NOW() - make_interval(days => $1)
            GROUP BY 1, 2, 3, 4
            ORDER BY n DESC, last_seen DESC
            LIMIT 50
        """, days)
        if not rows:
            print("  none")
        for r in rows:
            county = f" [{r['county']}]" if r["county"] else ""
            print(f"{r['n']:5}  {r['last_seen']:%Y-%m-%d}  {r['status_code']}  "
                  f"{r['a']}{county}  ({(r['detail'] or '')[:60]})")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--days", type=int, default=30)
    asyncio.run(main(parser.parse_args().days))
