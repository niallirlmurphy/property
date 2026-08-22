# Cache Optimization Recommendations

## Current Caching Implementation

### Existing Cache Setup
- **Type:** Simple in-memory TTL cache (Python dict)
- **Location:** Backend only (no CDN/Redis)
- **Cached endpoints:**
  - Search: 5 minutes (300s)
  - Geocode: 24 hours (86400s)
  - Trends: 1 hour (3600s)
  - Eircode: 1 hour (3600s)
  - Counties: 1 hour (3600s)

### Current Limitations
1. **No size limit** - cache can grow unbounded
2. **No LRU eviction** - old entries stay until TTL expires
3. **Single-instance** - each Railway instance has separate cache (no sharing)
4. **Lost on restart** - cache cleared when backend restarts
5. **No cache warming** - cold start after restart

---

## Recommended Approaches

### 1. **LRU Cache with Size Limit** (Quick Win - 1 hour implementation)

**Problem:** Current cache grows unbounded and may consume excessive memory.

**Solution:** Add LRU (Least Recently Used) eviction policy with configurable max size.

```python
from collections import OrderedDict
import time

class LRUTTLCache:
    def __init__(self, max_size: int = 1000):
        self._store: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def _key(self, namespace: str, params: dict) -> str:
        raw = namespace + json.dumps(params, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, namespace: str, params: dict):
        key = self._key(namespace, params)
        entry = self._store.get(key)
        
        if entry and time.time() < entry["expires"]:
            # Move to end (mark as recently used)
            self._store.move_to_end(key)
            self._hits += 1
            return entry["value"]
        
        # Expired or not found
        if entry:
            del self._store[key]
        self._misses += 1
        return None

    def set(self, namespace: str, params: dict, value, ttl_seconds: int):
        key = self._key(namespace, params)
        
        # Evict oldest if at capacity
        if len(self._store) >= self._max_size and key not in self._store:
            self._store.popitem(last=False)  # Remove oldest (FIFO)
        
        self._store[key] = {
            "value": value,
            "expires": time.time() + ttl_seconds
        }
        self._store.move_to_end(key)

    def stats(self) -> dict:
        """Return cache statistics for monitoring."""
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }
```

**Recommended max_size:**
- Search: 500 entries (most important for performance)
- Geocode: 1000 entries (addresses reused frequently)
- Trends: 200 entries (26 counties × a few time periods)
- Total memory: ~10-20MB

**Benefits:**
- ✅ Predictable memory usage
- ✅ No code changes to existing cache calls
- ✅ Can monitor hit rates
- ✅ Fast (in-memory)

---

### 2. **Redis for Shared Cache** (Medium effort - 1 day implementation)

**Problem:** Each Railway instance has its own cache, so load-balanced requests don't benefit from shared caching.

**Solution:** Use Redis (Railway add-on or external service) for shared cache across all instances.

```python
import redis.asyncio as redis
import json

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, namespace: str, params: dict):
        key = f"{namespace}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, namespace: str, params: dict, value, ttl_seconds: int):
        key = f"{namespace}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        await self.redis.setex(key, ttl_seconds, json.dumps(value))

    async def invalidate(self, namespace: str):
        # Use SCAN to find and delete keys with namespace prefix
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=f"{namespace}:*", count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

**Setup:**
```bash
# Railway
railway add redis

# Environment variable
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

**Benefits:**
- ✅ Shared across all instances
- ✅ Persists across restarts
- ✅ Built-in TTL support
- ✅ Can monitor with Redis CLI
- ❌ Adds network latency (~1-5ms)
- ❌ Additional cost ($5-10/month)

**When to use:**
- Multiple Railway instances (horizontal scaling)
- High traffic (>1000 req/min)
- Cache warming needed

---

### 3. **Frontend Browser Cache** (Quick win - 2 hours)

**Problem:** Users searching the same address multiple times make redundant API calls.

**Solution:** Cache search results in browser localStorage/sessionStorage.

```typescript
// frontend/src/utils/searchCache.ts
interface CachedSearch {
  params: SearchParams;
  results: SearchResponse;
  timestamp: number;
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
const MAX_CACHE_SIZE = 20;

export class SearchCache {
  private key = 'homeiq_search_cache';

  private getCache(): CachedSearch[] {
    try {
      const cached = sessionStorage.getItem(this.key);
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  }

  private saveCache(cache: CachedSearch[]) {
    try {
      sessionStorage.setItem(this.key, JSON.stringify(cache.slice(0, MAX_CACHE_SIZE)));
    } catch {
      // Storage full - clear and retry
      sessionStorage.removeItem(this.key);
    }
  }

  get(params: SearchParams): SearchResponse | null {
    const cache = this.getCache();
    const now = Date.now();

    const cached = cache.find(c => 
      c.params.q === params.q &&
      c.params.radius_km === params.radius_km &&
      c.params.county === params.county &&
      now - c.timestamp < CACHE_TTL_MS
    );

    return cached?.results || null;
  }

  set(params: SearchParams, results: SearchResponse) {
    const cache = this.getCache();
    const now = Date.now();

    // Remove expired entries
    const fresh = cache.filter(c => now - c.timestamp < CACHE_TTL_MS);

    // Add new entry at front
    fresh.unshift({ params, results, timestamp: now });

    this.saveCache(fresh);
  }

  clear() {
    sessionStorage.removeItem(this.key);
  }
}
```

**Usage in api.ts:**
```typescript
const searchCache = new SearchCache();

export async function searchProperties(params: SearchParams): Promise<SearchResponse> {
  // Check cache first
  const cached = searchCache.get(params);
  if (cached) {
    console.log('Cache hit:', params.q);
    return cached;
  }

  // Fetch from API
  const response = await fetch(`${API_URL}/search?${new URLSearchParams(params)}`);
  const data = await response.json();

  // Cache for next time
  searchCache.set(params, data);
  
  return data;
}
```

**Benefits:**
- ✅ Zero backend load for repeat searches
- ✅ Instant response (no network)
- ✅ Works offline
- ✅ No backend changes needed
- ✅ Per-user cache (privacy)

**Use sessionStorage (not localStorage):**
- Cleared when tab closes
- Separate per-tab (user can compare searches)
- Doesn't persist forever

---

### 4. **CDN Caching with Vercel** (Quick win - 30 minutes)

**Problem:** Popular searches hit the backend every time, even though results rarely change.

**Solution:** Add HTTP cache headers for Vercel Edge Network caching.

```python
# backend/main.py
from fastapi.responses import JSONResponse

@app.get("/search")
async def search(...):
    # ... existing code ...
    
    # Add cache headers
    headers = {
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",  # 5min cache, 10min stale OK
        "CDN-Cache-Control": "max-age=300",
        "Vary": "Accept-Encoding",
    }
    
    return JSONResponse(content=result, headers=headers)
```

**What this does:**
- `s-maxage=300`: CDN caches for 5 minutes
- `stale-while-revalidate=600`: Serve stale for 10min while revalidating
- Popular searches (Dublin, Cork) cached at edge
- 100+ edge locations worldwide

**Benefits:**
- ✅ Free (included with Vercel)
- ✅ Global distribution
- ✅ Minimal code changes
- ✅ Works immediately

**Endpoints to cache:**
- `/search` - 5 minutes
- `/trends` - 1 hour
- `/counties` - 1 day
- `/eircode/{code}` - 1 hour

---

### 5. **Query Normalization** (Medium effort - 3 hours)

**Problem:** "dublin", "Dublin", "DUBLIN" create separate cache entries.

**Solution:** Normalize queries before caching.

```python
def normalize_query(q: str) -> str:
    """Normalize search query for consistent caching."""
    q = q.strip().lower()
    
    # Remove extra spaces
    q = re.sub(r'\s+', ' ', q)
    
    # Normalize Irish abbreviations
    abbrevs = {
        'rd': 'road',
        'st': 'street',
        'ave': 'avenue',
        'dr': 'drive',
        'co': 'county',
    }
    for abbrev, full in abbrevs.items():
        q = re.sub(rf'\b{abbrev}\b', full, q)
    
    return q

# Use in search endpoint
@app.get("/search")
async def search(q: str, ...):
    normalized_q = normalize_query(q)
    cache_params = {"q": normalized_q, ...}  # Use normalized version for cache key
    
    # But still geocode with original query
    lat, lon, geocode_source = await resolve_location(q, county=county)
```

**Benefits:**
- ✅ Higher cache hit rate
- ✅ More consistent results
- ✅ Works with existing cache

---

### 6. **Cache Warming** (Advanced - 1 day)

**Problem:** Cold start after backend restart = slow first requests.

**Solution:** Pre-populate cache with popular searches on startup.

```python
# backend/main.py
POPULAR_SEARCHES = [
    ("dublin", 1.0),
    ("cork", 1.0),
    ("galway", 1.0),
    ("limerick", 1.0),
    # Top 20 most searched addresses/areas
]

async def warm_cache():
    """Pre-populate cache with popular searches on startup."""
    logger.info("Warming cache with popular searches...")
    
    async with httpx.AsyncClient() as client:
        for query, radius in POPULAR_SEARCHES:
            try:
                # Warm geocode cache
                await resolve_location(query)
                
                # Warm search cache (make internal request)
                params = {"q": query, "radius_km": radius, "limit": 200}
                # Call search function directly (not via HTTP)
                
                logger.info(f"Warmed cache: {query}")
            except Exception as e:
                logger.warning(f"Failed to warm cache for {query}: {e}")
    
    logger.info("Cache warming complete")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, _aa_semaphore
    db_pool = await asyncpg.create_pool(...)
    _aa_semaphore = asyncio.Semaphore(5)
    
    # Warm cache in background (don't block startup)
    asyncio.create_task(warm_cache())
    
    asyncio.create_task(_heartbeat_loop())
    yield
    # Shutdown
    await db_pool.close()
```

**Benefits:**
- ✅ Fast response for popular searches after restart
- ✅ Reduces database load spike
- ✅ Runs async (doesn't slow startup)

---

## Recommended Implementation Priority

### Phase 1: Quick Wins (Week 1)
1. **LRU cache with size limit** (1 hour) - prevents memory issues
2. **Frontend browser cache** (2 hours) - instant repeat searches
3. **CDN caching headers** (30 minutes) - edge caching for popular searches
4. **Query normalization** (3 hours) - higher cache hit rate

**Total effort:** ~1 day  
**Expected improvement:** 30-50% reduction in backend load

### Phase 2: Shared Cache (Week 2)
5. **Redis cache** (1 day) - only if scaling to multiple instances
6. **Cache warming** (1 day) - optimize cold starts

**Total effort:** 2 days  
**Expected improvement:** 50-70% reduction in database queries

---

## Monitoring Recommendations

Add cache statistics endpoint:

```python
@app.get("/admin/cache/stats")
async def cache_stats():
    """Return cache performance statistics."""
    stats = cache.stats()
    
    return {
        "cache": stats,
        "endpoints": {
            "search": {"ttl": TTL_SEARCH, "size": len([k for k in cache._store if k.startswith("search")])},
            "geocode": {"ttl": TTL_GEOCODE, "size": len([k for k in cache._store if k.startswith("geocode")])},
            "trends": {"ttl": TTL_TRENDS, "size": len([k for k in cache._store if k.startswith("trends")])},
        },
        "recommendations": {
            "hit_rate": "optimal" if stats["hit_rate"] > 0.7 else "low",
            "size_usage": f"{stats['size'] / stats['max_size'] * 100:.1f}%"
        }
    }
```

Monitor:
- Cache hit rate (target: >70%)
- Cache size (ensure not hitting limit)
- Popular queries (identify candidates for warming)

---

## Cost-Benefit Analysis

| Approach | Implementation Time | Monthly Cost | Performance Gain | Best For |
|----------|-------------------|--------------|------------------|----------|
| LRU Cache | 1 hour | $0 | +20% hit rate | All apps |
| Frontend Cache | 2 hours | $0 | Instant repeats | All apps |
| CDN Caching | 30 min | $0 (Vercel included) | +30% edge hits | Popular queries |
| Query Normalization | 3 hours | $0 | +15% hit rate | All apps |
| Redis Cache | 1 day | $5-10 | +50% shared cache | Multi-instance |
| Cache Warming | 1 day | $0 | Fast cold starts | High traffic |

**Recommended starting point:** Phase 1 (Quick Wins) - maximum impact with minimal effort and zero cost.

---

## Implementation Example: LRU Cache Drop-in Replacement

```python
# Replace current cache implementation in backend/main.py

# Old:
# cache = TTLCache()

# New:
cache = LRUTTLCache(max_size=2000)  # Increase from 1000 if memory allows

# Add stats endpoint
@app.get("/health")
async def health():
    stats = cache.stats()
    return {
        "status": "ok",
        "cache_hit_rate": f"{stats['hit_rate']:.2%}",
        "cache_size": f"{stats['size']}/{stats['max_size']}"
    }
```

**That's it!** All existing `cache.get()` and `cache.set()` calls work unchanged.

---

## Questions to Consider

1. **How many Railway instances are running?**
   - Single instance → LRU cache sufficient
   - Multiple instances → Redis recommended

2. **What's the request volume?**
   - <1000/day → Current cache fine
   - >10,000/day → Implement all Phase 1 optimizations
   - >100,000/day → Add Redis + CDN

3. **What's the most common search pattern?**
   - Browse by county → Warm top counties
   - Specific addresses → Frontend cache critical
   - Map exploration → CDN caching helps

4. **What's the budget?**
   - $0 → Phase 1 only
   - $10/month → Add Redis
   - $50+/month → Consider CloudFlare Workers cache

Let me know which approach you'd like to implement first!
