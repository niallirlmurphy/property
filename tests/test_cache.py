#!/usr/bin/env python3
"""
Cache implementation tests for LRUTTLCache.

Tests LRU eviction, TTL expiration, hit/miss tracking, and memory bounds.
"""

import pytest
import time
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import LRUTTLCache


class TestLRUTTLCache:
    """Test suite for LRU cache with TTL."""

    def test_basic_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = LRUTTLCache(max_size=10)

        # Set a value
        cache.set("test", {"key": "value1"}, {"data": "test_data"}, ttl_seconds=60)

        # Get it back
        result = cache.get("test", {"key": "value1"})

        assert result == {"data": "test_data"}
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """Test cache miss tracking."""
        cache = LRUTTLCache(max_size=10)

        # Get non-existent key
        result = cache.get("test", {"key": "nonexistent"})

        assert result is None
        assert cache._hits == 0
        assert cache._misses == 1

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = LRUTTLCache(max_size=10)

        # Set with 1 second TTL
        cache.set("test", {"key": "value1"}, {"data": "test_data"}, ttl_seconds=1)

        # Should be available immediately
        result = cache.get("test", {"key": "value1"})
        assert result == {"data": "test_data"}

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        result = cache.get("test", {"key": "value1"})
        assert result is None
        assert cache._misses == 1  # Expired counts as miss

    def test_lru_eviction(self):
        """Test that LRU eviction removes oldest entries when at capacity."""
        cache = LRUTTLCache(max_size=3)

        # Fill cache to capacity
        cache.set("ns", {"key": "1"}, "value1", ttl_seconds=60)
        cache.set("ns", {"key": "2"}, "value2", ttl_seconds=60)
        cache.set("ns", {"key": "3"}, "value3", ttl_seconds=60)

        assert len(cache._store) == 3

        # Access key 1 (moves to end)
        cache.get("ns", {"key": "1"})

        # Add new key (should evict key 2, the oldest unused)
        cache.set("ns", {"key": "4"}, "value4", ttl_seconds=60)

        assert len(cache._store) == 3
        assert cache.get("ns", {"key": "1"}) == "value1"  # Still there (recently used)
        assert cache.get("ns", {"key": "2"}) is None       # Evicted
        assert cache.get("ns", {"key": "3"}) == "value3"   # Still there
        assert cache.get("ns", {"key": "4"}) == "value4"   # Newly added

    def test_lru_update_existing_key(self):
        """Test that updating an existing key doesn't count against capacity."""
        cache = LRUTTLCache(max_size=3)

        # Fill cache
        cache.set("ns", {"key": "1"}, "value1", ttl_seconds=60)
        cache.set("ns", {"key": "2"}, "value2", ttl_seconds=60)
        cache.set("ns", {"key": "3"}, "value3", ttl_seconds=60)

        # Update existing key
        cache.set("ns", {"key": "2"}, "value2_updated", ttl_seconds=60)

        # Should still have 3 entries
        assert len(cache._store) == 3
        assert cache.get("ns", {"key": "2"}) == "value2_updated"

    def test_namespace_isolation(self):
        """Test that different namespaces don't interfere with each other."""
        cache = LRUTTLCache(max_size=10)

        # Set values in different namespaces
        cache.set("namespace1", {"key": "1"}, "value_ns1", ttl_seconds=60)
        cache.set("namespace2", {"key": "1"}, "value_ns2", ttl_seconds=60)

        # Both should be accessible
        assert cache.get("namespace1", {"key": "1"}) == "value_ns1"
        assert cache.get("namespace2", {"key": "1"}) == "value_ns2"

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        cache = LRUTTLCache(max_size=10)

        # Perform some operations
        cache.set("test", {"key": "1"}, "value1", ttl_seconds=60)
        cache.get("test", {"key": "1"})  # Hit
        cache.get("test", {"key": "2"})  # Miss
        cache.get("test", {"key": "1"})  # Hit
        cache.get("test", {"key": "3"})  # Miss

        stats = cache.stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5  # 2 hits out of 4 total

    def test_hit_rate_calculation(self):
        """Test hit rate calculation edge cases."""
        cache = LRUTTLCache(max_size=10)

        # No requests yet
        stats = cache.stats()
        assert stats["hit_rate"] == 0

        # Add some hits
        cache.set("test", {"key": "1"}, "value1", ttl_seconds=60)
        cache.get("test", {"key": "1"})  # Hit
        cache.get("test", {"key": "1"})  # Hit

        stats = cache.stats()
        assert stats["hit_rate"] == 1.0  # 100% hits

    def test_memory_bounds(self):
        """Test that cache respects max_size and doesn't grow unbounded."""
        cache = LRUTTLCache(max_size=100)

        # Add 200 entries (2x max_size)
        for i in range(200):
            cache.set("test", {"key": str(i)}, f"value{i}", ttl_seconds=60)

        # Should not exceed max_size
        assert len(cache._store) == 100

        # Oldest 100 should be evicted
        for i in range(100):
            assert cache.get("test", {"key": str(i)}) is None

        # Newest 100 should still be there
        for i in range(100, 200):
            assert cache.get("test", {"key": str(i)}) == f"value{i}"

    def test_complex_params_hashing(self):
        """Test that complex parameter objects are hashed correctly."""
        cache = LRUTTLCache(max_size=10)

        # Complex params (order should not matter)
        params1 = {"q": "dublin", "radius_km": 5, "min_price": 100000, "max_price": 500000}
        params2 = {"max_price": 500000, "q": "dublin", "min_price": 100000, "radius_km": 5}

        cache.set("search", params1, {"results": [1, 2, 3]}, ttl_seconds=60)

        # Should hit cache with params in different order (JSON sorts keys)
        result = cache.get("search", params2)
        assert result == {"results": [1, 2, 3]}

    def test_invalidate_namespace(self):
        """Test namespace invalidation."""
        cache = LRUTTLCache(max_size=10)

        # Add entries in multiple namespaces
        cache.set("search", {"key": "1"}, "value1", ttl_seconds=60)
        cache.set("search", {"key": "2"}, "value2", ttl_seconds=60)
        cache.set("trends", {"key": "1"}, "value3", ttl_seconds=60)

        # Invalidate search namespace
        cache.invalidate("search")

        # Search entries should be gone
        assert cache.get("search", {"key": "1"}) is None
        assert cache.get("search", {"key": "2"}) is None

        # Trends should still be there
        assert cache.get("trends", {"key": "1"}) == "value3"

    def test_concurrent_access_pattern(self):
        """Test realistic concurrent access pattern."""
        cache = LRUTTLCache(max_size=50)

        # Simulate hot keys (frequently accessed) and cold keys
        hot_keys = ["dublin", "cork", "galway", "limerick"]

        # Access pattern: 80% hot keys, 20% random
        for i in range(100):
            if i % 5 == 0:
                # Cold key (random)
                cache.set("search", {"q": f"random_{i}"}, f"result_{i}", ttl_seconds=60)
            else:
                # Hot key
                hot_key = hot_keys[i % len(hot_keys)]
                cache.set("search", {"q": hot_key}, f"result_{hot_key}", ttl_seconds=60)
                cache.get("search", {"q": hot_key})  # Immediate re-access

        # Hot keys should still be in cache
        for key in hot_keys:
            assert cache.get("search", {"q": key}) is not None

        # Cache should not exceed max_size
        assert len(cache._store) <= 50

    def test_zero_ttl(self):
        """Test that zero TTL expires immediately."""
        cache = LRUTTLCache(max_size=10)

        cache.set("test", {"key": "1"}, "value1", ttl_seconds=0)

        # Should be expired immediately (or very soon)
        time.sleep(0.01)
        result = cache.get("test", {"key": "1"})
        assert result is None


class TestCacheIntegration:
    """Integration tests for cache usage in API endpoints."""

    def test_search_cache_key_uniqueness(self):
        """Test that different search parameters generate unique cache keys."""
        cache = LRUTTLCache(max_size=10)

        # Different queries should have different cache keys
        params1 = {"q": "dublin", "radius_km": 1.0}
        params2 = {"q": "dublin", "radius_km": 2.0}
        params3 = {"q": "cork", "radius_km": 1.0}

        cache.set("search", params1, {"results": ["a"]}, ttl_seconds=60)
        cache.set("search", params2, {"results": ["b"]}, ttl_seconds=60)
        cache.set("search", params3, {"results": ["c"]}, ttl_seconds=60)

        assert cache.get("search", params1) == {"results": ["a"]}
        assert cache.get("search", params2) == {"results": ["b"]}
        assert cache.get("search", params3) == {"results": ["c"]}

    def test_geocode_cache_longevity(self):
        """Test that geocode results are cached for 24 hours."""
        cache = LRUTTLCache(max_size=100)

        # Geocode should have long TTL (addresses don't move)
        cache.set("geocode_v3", {"q": "22 Cremore Lawn, Dublin"},
                  {"lat": 53.377159, "lon": -6.280229},
                  ttl_seconds=86400)  # 24 hours

        # Should be available after 1 hour
        time.sleep(0.1)  # Simulate time passing (can't actually wait 1 hour)
        result = cache.get("geocode_v3", {"q": "22 Cremore Lawn, Dublin"})
        assert result is not None


class TestCacheEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_value_cached(self):
        """Test that None values can be cached (cache negative results)."""
        cache = LRUTTLCache(max_size=10)

        # Cache a None result
        cache.set("search", {"q": "nonexistent"}, None, ttl_seconds=60)

        # Should hit cache (not miss)
        result = cache.get("search", {"q": "nonexistent"})
        assert result is None
        assert cache._hits == 1  # Should be a hit, not a miss

    def test_empty_params(self):
        """Test that empty params work correctly."""
        cache = LRUTTLCache(max_size=10)

        cache.set("test", {}, "empty_params_value", ttl_seconds=60)
        result = cache.get("test", {})
        assert result == "empty_params_value"

    def test_large_value_caching(self):
        """Test caching large values (typical search results with 200 properties)."""
        cache = LRUTTLCache(max_size=10)

        # Simulate large search result
        large_value = {
            "properties": [
                {
                    "id": i,
                    "address": f"Address {i}",
                    "price": 300000 + i * 1000,
                    "latitude": 53.3 + i * 0.001,
                    "longitude": -6.2 + i * 0.001
                }
                for i in range(200)
            ]
        }

        cache.set("search", {"q": "dublin"}, large_value, ttl_seconds=300)

        # Should retrieve entire large value
        result = cache.get("search", {"q": "dublin"})
        assert result is not None
        assert len(result["properties"]) == 200

    def test_unicode_in_params(self):
        """Test that unicode characters in params are handled correctly."""
        cache = LRUTTLCache(max_size=10)

        # Irish characters
        cache.set("search", {"q": "Dún Laoghaire"}, "result1", ttl_seconds=60)
        cache.set("search", {"q": "Áth Cliath"}, "result2", ttl_seconds=60)

        assert cache.get("search", {"q": "Dún Laoghaire"}) == "result1"
        assert cache.get("search", {"q": "Áth Cliath"}) == "result2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
