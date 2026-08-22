# Mapbox API Usage Tracking

## Overview

Centralized tracking system for all Mapbox API requests with **strict 50,000 requests/month limit** enforcement.

**Why 50k instead of 100k free tier?**
- Safety margin for unexpected usage spikes
- Reserve capacity for urgent geocoding needs
- Prevent overage charges ($0.75 per 1,000 after free tier)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    All Mapbox API Calls                     │
│                                                              │
│  geocode_mapbox_batch.py  │  backend/main.py  │  other     │
│         scripts...                  /geocode        scripts  │
└────────────────┬────────────────────┬────────────────┬───────┘
                 │                    │                │
                 └────────────────────┼────────────────┘
                                      ▼
                          ┌───────────────────────┐
                          │   MapboxClient        │
                          │   (scripts/mapbox_    │
                          │    client.py)         │
                          └───────────┬───────────┘
                                      │
                          ┌───────────▼───────────┐
                          │  MapboxUsageTracker   │
                          │  (scripts/mapbox_     │
                          │   usage_tracker.py)   │
                          └───────────┬───────────┘
                                      │
                          ┌───────────▼───────────┐
                          │  PostgreSQL Database  │
                          │  mapbox_usage table   │
                          └───────────────────────┘
```

## Database Schema

```sql
CREATE TABLE mapbox_usage (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(100) NOT NULL,       -- Script name: 'geocode_mapbox_batch', 'api', etc.
    request_count INTEGER NOT NULL,     -- Total requests made
    success_count INTEGER NOT NULL,     -- Successful geocodes
    error_count INTEGER NOT NULL,       -- Failed requests
    operation VARCHAR(50),              -- 'geocode', 'batch_geocode', 'search'
    notes TEXT                          -- Optional context
);

CREATE INDEX idx_mapbox_usage_timestamp ON mapbox_usage(timestamp DESC);
CREATE INDEX idx_mapbox_usage_source ON mapbox_usage(source, timestamp DESC);
```

## Usage in Scripts

### Standard Pattern (Recommended)

```python
from scripts.mapbox_client import MapboxClient, MapboxLimitExceeded

async def main():
    # Always use context manager for automatic tracking
    async with MapboxClient(source='my_script', operation='geocode') as client:
        # Single geocode
        result = await client.geocode('Dublin, Ireland')
        
        # Batch geocode (automatically enforces limits)
        addresses = ['Cork', 'Galway', 'Limerick']
        results = await client.batch_geocode(addresses)
        
        # Check remaining quota
        remaining = await client.get_remaining_quota()
        print(f"Remaining: {remaining:,} requests")
```

### Pre-flight Limit Check

```python
from scripts.mapbox_client import check_quota_before_run, MapboxClient

async def process_large_batch():
    # Check quota BEFORE expensive operations
    properties_count = 10_000
    
    if not await check_quota_before_run(properties_count, 'geocode_batch'):
        print("Insufficient quota, aborting")
        return
    
    # Proceed with processing
    async with MapboxClient(source='geocode_batch') as client:
        # ... process properties
        pass
```

### Error Handling

```python
from scripts.mapbox_client import MapboxClient, MapboxLimitExceeded

try:
    async with MapboxClient(source='my_script') as client:
        results = await client.batch_geocode(addresses)
except MapboxLimitExceeded as e:
    print(f"Cannot proceed: {e}")
    # Send alert, log error, schedule for next month, etc.
```

## Monitoring Usage

### Current Month Summary

```bash
python3 scripts/mapbox_usage_tracker.py --current-month
```

Output:
```
============================================================
Mapbox API Usage - July 2026
============================================================

Total Requests:     12,450
  ✓ Successful:     11,203
  ✗ Errors:          1,247

Monthly Limit:      50,000
Remaining:          37,550
Usage:               24.9%
Daily Average:       1,783

------------------------------------------------------------
Usage by Source:
------------------------------------------------------------
geocode_mapbox_batch           8,450 ( 67.9%)
api                            3,200 ( 25.7%)
regeocode_high_priority          800 (  6.4%)
============================================================
```

### Last N Days

```bash
python3 scripts/mapbox_usage_tracker.py 7  # Last 7 days
python3 scripts/mapbox_usage_tracker.py 30 # Last 30 days
```

### Programmatic Check

```python
from scripts.mapbox_usage_tracker import MapboxUsageTracker

# Get current month usage
usage = await MapboxUsageTracker.get_current_month_usage()
print(f"Used: {usage['total']['total_requests']:,}")
print(f"Remaining: {usage['remaining']:,}")

# Check if safe to proceed
safe = await MapboxUsageTracker.check_limit(warn_threshold=0.8)
```

## Initial Setup

```bash
# 1. Create tracking table
python3 scripts/setup_mapbox_tracking.py

# 2. Optionally backfill historical usage (estimates from recent geocoding)
python3 scripts/setup_mapbox_tracking.py --backfill

# 3. Verify setup
python3 scripts/mapbox_usage_tracker.py --current-month
```

## Integration Checklist

**All scripts using Mapbox MUST:**
- [ ] Import `MapboxClient` instead of calling Mapbox API directly
- [ ] Use `async with MapboxClient(...)` context manager
- [ ] Check quota with `check_quota_before_run()` before large operations
- [ ] Handle `MapboxLimitExceeded` exceptions gracefully
- [ ] Set meaningful `source` name for tracking (script filename)

**Scripts to update:**
- [ ] `scripts/geocode_mapbox_batch.py` - Batch geocoding (primary consumer)
- [ ] `scripts/regeocode_high_priority.py` - Priority re-geocoding
- [ ] `scripts/compare_geocoders.py` - Geocoder comparison tests
- [ ] `backend/main.py` - `/geocode` API endpoint
- [ ] `scripts/sync_ppr_updates.py` - Biweekly PPR sync (if calls Mapbox)

## Monitoring & Alerts

### Daily Checks (Automated)

Add to `.github/workflows/daily_checks.yml`:

```yaml
- name: Check Mapbox Usage
  run: |
    python3 scripts/mapbox_usage_tracker.py --current-month
    # Fail if usage > 90%
    python3 -c "
    import asyncio
    from scripts.mapbox_usage_tracker import MapboxUsageTracker
    async def check():
        usage = await MapboxUsageTracker.get_current_month_usage()
        if usage['percentage_used'] > 90:
            raise Exception(f\"Mapbox usage critical: {usage['percentage_used']:.1f}%\")
    asyncio.run(check())
    "
```

### Manual Checks Before Large Operations

```bash
# Before running centroid cleanup (10k+ requests)
python3 -c "
import asyncio
from scripts.mapbox_client import check_quota_before_run

async def main():
    can_proceed = await check_quota_before_run(10000, 'centroid_cleanup')
    if not can_proceed:
        print('Abort operation')
        exit(1)

asyncio.run(main())
"

# Then run if quota OK
python3 scripts/geocode_mapbox_batch.py --centroid --limit 10000 --apply
```

## Usage Patterns & Best Practices

### Monthly Budget Allocation

With 50k/month limit:
- **Reserve 2k/month** for biweekly PPR sync (1k × 2 runs)
- **Reserve 5k/month** for API `/geocode` endpoint (user searches)
- **Remaining 43k/month** for batch operations (centroid cleanup, re-geocoding)

### Prioritization Strategy

1. **Critical (Always run):** PPR sync - new property imports
2. **High Priority:** User-facing API geocoding
3. **Medium Priority:** High-value property re-geocoding (>€500k)
4. **Low Priority:** Centroid cleanup (can defer to next month)

### Rate Limiting

```python
# Process in batches with monthly budget awareness
async with MapboxClient(source='batch_job') as client:
    remaining = await client.get_remaining_quota()
    
    # Process only what we can afford
    batch_size = min(remaining - 5000, 10000)  # Leave 5k buffer
    properties = properties[:batch_size]
    
    for batch in chunks(properties, 1000):
        results = await client.batch_geocode(batch)
        await asyncio.sleep(1)  # Rate limiting
```

## Troubleshooting

### "MapboxLimitExceeded" Error

**Cause:** Monthly quota exhausted (50k requests used)

**Solutions:**
1. Wait until next calendar month (quota resets)
2. Review usage by source: `python3 scripts/mapbox_usage_tracker.py --current-month`
3. Identify and stop non-critical scripts
4. Consider upgrading Mapbox plan if consistently hitting limit

### Usage Not Tracking

**Check:**
1. Table exists: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM mapbox_usage;"`
2. Scripts updated to use `MapboxClient` wrapper
3. Database connection working in scripts

### Historical Usage Unknown

**Solution:**
```bash
python3 scripts/setup_mapbox_tracking.py --backfill
```

Estimates usage from `geocoding_quality` column in properties table.

## API Reference

### MapboxClient

```python
class MapboxClient:
    def __init__(source: str, operation: str = 'geocode', notes: str = None)
    
    async def geocode(address: str, country: str = 'ie') -> Optional[Dict]
    async def batch_geocode(addresses: List[str]) -> List[Optional[Dict]]
    async def get_remaining_quota() -> int
    async def can_process(count: int) -> Tuple[bool, str]
```

### MapboxUsageTracker

```python
class MapboxUsageTracker:
    @staticmethod
    async def get_current_month_usage() -> Dict
    
    @staticmethod
    async def get_usage_summary(days: int = 30) -> Dict
    
    @staticmethod
    async def check_limit(warn_threshold: float = 0.8) -> bool
```

## See Also

- [Mapbox Geocoding API Docs](https://docs.mapbox.com/api/search/geocoding/)
- [CLAUDE.md](../CLAUDE.md) - Project documentation
- [Geocoding Quality Monitoring](./GEOCODING_QUALITY_MONITORING.md)
