"""Tiny in-memory TTL cache for the valuation pipeline.

The valuation helpers (ValuationGeocoder, MVPAdjuster) are instantiated *per
request* in api.py, so a per-instance cache would only help within a single
valuation. These caches are therefore module-level singletons that persist for
the life of the worker process, so repeated valuations of the same address /
county-month / locality reuse earlier database work.

Concurrency: the backend runs a single asyncio event loop per worker, and get/
set here contain no ``await``, so they are never interleaved mid-operation and
need no locking. Two requests can both miss and both fetch the same key — a
benign double-fetch, never a correctness problem.
"""

import time
from typing import Any, Tuple


class TTLCache:
    """Dict-backed cache with a fixed TTL and a soft size bound.

    ``get`` returns ``(hit, value)`` rather than a sentinel so a legitimately
    cached ``None`` (e.g. "this county/month has no price index") still counts
    as a hit and short-circuits the query.
    """

    def __init__(self, ttl_seconds: float, max_size: int = 8192):
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._store: dict = {}

    def get(self, key) -> Tuple[bool, Any]:
        entry = self._store.get(key)
        if entry is not None:
            value, expires = entry
            if expires > time.monotonic():
                return True, value
            del self._store[key]  # expired
        return False, None

    def set(self, key, value) -> None:
        if len(self._store) >= self._max_size and key not in self._store:
            # Cheap bound: drop the oldest-inserted entry (dicts preserve
            # insertion order). Good enough — these key spaces are small.
            self._store.pop(next(iter(self._store)), None)
        self._store[key] = (value, time.monotonic() + self._ttl)

    def clear(self) -> None:
        self._store.clear()
