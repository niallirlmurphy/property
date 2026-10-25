"""Per-feature request counts (table api_usage_daily) and the switch that keeps
test traffic out of every query log (search_log, search_failures,
valuation_requests, valuation_failures, api_usage_daily).

Counts are kept in memory and flushed every 10 minutes as one upsert per
(day, endpoint, status), so logging costs a few writes an hour, not one per request.
"""
import asyncio
import contextvars
import logging
import os
from collections import defaultdict
from datetime import date

logger = logging.getLogger(__name__)

# Only the Railway deployment logs: the pre-commit regression tests run a local
# backend against the production database. The production test suite marks its
# requests with TEST_HEADER.
LOGGING_ENABLED = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
TEST_HEADER = "x-homeiq-test"
FLUSH_INTERVAL_S = 600

_log_request = contextvars.ContextVar("log_request", default=LOGGING_ENABLED)
_counts: "defaultdict[tuple, list]" = defaultdict(lambda: [0, 0])  # -> [requests, total_ms]


def start_request(headers) -> None:
    """Call at the start of each request; tasks it spawns inherit the setting."""
    _log_request.set(LOGGING_ENABLED and TEST_HEADER not in headers)


def query_logging_enabled() -> bool:
    return _log_request.get()


def record(endpoint: str, status: int, elapsed_ms: int) -> None:
    if not _log_request.get():
        return
    c = _counts[(date.today(), endpoint, status)]
    c[0] += 1
    c[1] += elapsed_ms


async def flush(pool) -> None:
    if not _counts or pool is None:
        return
    items = list(_counts.items())
    _counts.clear()
    try:
        await pool.executemany("""
            INSERT INTO api_usage_daily (day, endpoint, status, requests, total_ms)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (day, endpoint, status) DO UPDATE
            SET requests = api_usage_daily.requests + EXCLUDED.requests,
                total_ms = api_usage_daily.total_ms + EXCLUDED.total_ms
        """, [(d, e, s, n, ms) for (d, e, s), (n, ms) in items])
    except Exception as e:
        logger.warning(f"API usage flush failed ({len(items)} rows dropped): {e}")


async def flush_loop(get_pool) -> None:
    while True:
        await asyncio.sleep(FLUSH_INTERVAL_S)
        await flush(get_pool())
