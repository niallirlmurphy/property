# Mapbox Scripts - Usage Tracking Required

## ⚠️ IMPORTANT: All Mapbox API calls must go through MapboxClient

To prevent exceeding the **50,000 requests/month limit**, all scripts using Mapbox MUST use the centralized tracking system.

## Quick Start

### 1. Set Up Tracking (One-time)

```bash
python3 scripts/setup_mapbox_tracking.py
```

### 2. Check Current Quota

```bash
./scripts/check_mapbox_quota.sh
# or
python3 scripts/mapbox_usage_tracker.py --current-month
```

### 3. Use MapboxClient in Your Script

```python
from scripts.mapbox_client import MapboxClient, MapboxLimitExceeded

async def my_geocoding_script():
    async with MapboxClient(source='my_script') as client:
        # Check quota first for large operations
        remaining = await client.get_remaining_quota()
        print(f"Remaining: {remaining:,} requests")
        
        # Single geocode
        result = await client.geocode('Dublin, Ireland')
        
        # Batch geocode (automatically tracked)
        results = await client.batch_geocode(['Cork', 'Galway'])
```

## Scripts Using Mapbox

| Script | Purpose | Typical Usage |
|--------|---------|---------------|
| `geocode_mapbox_batch.py` | Batch geocoding | 1k-10k requests |
| `regeocode_high_priority.py` | Re-geocode high-value properties | 100-1k requests |
| `compare_geocoders.py` | Test geocoding quality | 10-100 requests |
| `../backend/main.py` | API `/geocode` endpoint | Variable (user-driven) |

## Monthly Budget (50k total)

- **2k/month**: Biweekly PPR sync (automated, critical)
- **5k/month**: API geocoding endpoint (user searches)
- **43k/month**: Batch operations (centroid cleanup, re-geocoding)

## Before Running Large Operations

```bash
# Check quota before processing 10k properties
python3 -c "
import asyncio
from scripts.mapbox_client import check_quota_before_run

async def main():
    can_proceed = await check_quota_before_run(10000, 'my_operation')
    if not can_proceed:
        exit(1)

asyncio.run(main())
"
```

## Monitoring

### Daily Check (Automated)

GitHub Action runs daily at 9 AM UTC:
- Checks quota usage
- Creates GitHub issue if >90% used
- See: `.github/workflows/mapbox_quota_check.yml`

### Manual Check

```bash
./scripts/check_mapbox_quota.sh
```

## Troubleshooting

### "MapboxLimitExceeded" Error

Monthly quota exhausted. Options:
1. Wait until next calendar month (quota resets)
2. Review usage: `python3 scripts/mapbox_usage_tracker.py --current-month`
3. Defer non-critical operations

### Usage Not Tracking

1. Verify table exists: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM mapbox_usage;"`
2. Ensure script uses `MapboxClient` wrapper (not direct API calls)
3. Check database connection in script

## See Also

- [Complete Documentation](../docs/MAPBOX_USAGE_TRACKING.md)
- [CLAUDE.md Infrastructure Section](../CLAUDE.md#infrastructure)
