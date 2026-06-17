# Canonical Coordinates and Enrichment System

**Date:** 2026-06-17  
**Status:** Approved  
**Author:** Claude Code

## Problem Statement

Database analysis revealed 51,669 addresses (69.2% of repeat sales) have inconsistent geocoding coordinates across multiple sales. The same physical property should always have identical latitude/longitude values, but geocoding has run multiple times with different results.

Additionally, 11 addresses have inconsistent bedroom counts and 31 have inconsistent property types, indicating enrichment data quality issues.

**Impact:**
- Search results show duplicate properties at different map locations
- Distance calculations are incorrect for the same address
- User confusion when viewing multiple sales of same property
- Wasted API calls re-geocoding and re-enriching known addresses

## Goals

1. **Fix existing inconsistencies:** Standardize coordinates and enrichment data for all 51,669 affected addresses
2. **Prevent future inconsistencies:** Ensure all geocoding and enrichment scripts check cache before external API calls
3. **Improve performance:** Reduce redundant geocoding/enrichment by reusing known data
4. **Maintain data quality:** Use intelligent selection strategy to choose best coordinates and enrichment values

## Non-Goals

- Creating a persistent database table for canonical data (using in-memory cache per script run)
- Real-time cache synchronization across concurrent scripts
- Modifying the database schema (no new columns or tables)
- Handling address changes over time (e.g., property subdivisions, renumbering)

## Architecture Overview

### Components

**1. Canonical Geocoding Module** (`scripts/canonical_geocoding.py`)

Core Python module providing coordinate and enrichment data lookup, caching, and consistency enforcement.

**Key Functions:**
```python
def initialize_cache(database_url: str) -> None:
    """Load all property coordinates and enrichment into memory cache."""

def get_canonical_coordinates(address_normalized: str) -> Optional[Tuple[float, float]]:
    """Return cached coordinates or None if not found."""

def get_canonical_property_data(address_normalized: str) -> Optional[PropertyData]:
    """Return cached coordinates + enrichment data or None."""

def cache_coordinates(address_normalized: str, lat: float, lon: float) -> None:
    """Add coordinates to cache."""

def cache_enrichment_data(address_normalized: str, bedrooms: Optional[int], 
                         property_type: Optional[str]) -> None:
    """Add enrichment data to cache."""

def should_geocode(address_normalized: str) -> bool:
    """Return True only if no canonical coordinate exists in cache."""

def should_enrich(address_normalized: str) -> bool:
    """Return True only if no enrichment data exists in cache."""
```

**Cache Structure:**
```python
@dataclass
class PropertyData:
    latitude: float
    longitude: float
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    last_geocoded: Optional[datetime] = None
    last_enriched: Optional[datetime] = None

_canonical_cache: Dict[str, PropertyData] = {}
# Key: address_normalized
# Value: PropertyData with coordinates and optional enrichment
```

**2. Fix Script** (`scripts/fix_geocoding_inconsistencies.py`)

One-time remediation script to standardize all existing inconsistent data.

**Workflow:**
1. Query database for addresses with multiple distinct coordinates (51,669 addresses)
2. Query database for addresses with multiple distinct enrichment values (42 addresses total)
3. For each inconsistent address:
   - Apply hybrid selection strategy
   - Update all sales of that address to use canonical values
   - Log decision to audit file
4. Commit in batches of 5,000 addresses for resumability
5. Write complete audit log to `fix_geocoding_audit_YYYYMMDD_HHMMSS.json`

**3. Integration Layer**

Modifications to existing geocoding and enrichment scripts:

**Geocoding Scripts:**
- `scripts/geocode_mapbox_batch.py`
- `scripts/sync_ppr_updates.py`
- `scripts/geocode_from_existing_fast.py`
- Any other scripts that geocode properties

**Enrichment Scripts:**
- `scripts/enrich_recent_properties.py`
- `scripts/enrich_multi_batch.py`
- `scripts/enrich_from_csv.py`
- Any other scripts that scrape property details

**Integration Pattern:**
```python
# Import at top of script
from canonical_geocoding import (
    initialize_cache, 
    get_canonical_coordinates,
    get_canonical_property_data,
    cache_coordinates,
    cache_enrichment_data
)

# Initialize cache at script startup
async def main():
    initialize_cache(DATABASE_URL)
    
    # Before geocoding
    coords = get_canonical_coordinates(address_normalized)
    if coords is None:
        coords = await geocode_with_mapbox(address)
        cache_coordinates(address_normalized, coords[0], coords[1])
    
    # Before enrichment
    data = get_canonical_property_data(address_normalized)
    if data and data.bedrooms is not None:
        # Reuse cached enrichment
        bedrooms, property_type = data.bedrooms, data.property_type
    else:
        # Web scrape only if not cached
        bedrooms, property_type = await scrape_property_details(address)
        cache_enrichment_data(address_normalized, bedrooms, property_type)
```

## Data Flow

### Initial Cache Population

```
Script Startup
    ↓
initialize_cache(DATABASE_URL)
    ↓
Query: SELECT address_normalized, latitude, longitude, 
              bedrooms, property_type, sale_date, price,
              geocode_quality_issue
       FROM properties
       WHERE address_normalized IS NOT NULL
         AND (latitude IS NOT NULL 
              OR bedrooms IS NOT NULL 
              OR property_type IS NOT NULL)
    ↓
For each address_normalized with multiple coordinate pairs:
    Apply hybrid selection strategy → Choose canonical coordinates
    ↓
For each address_normalized with multiple enrichment values:
    Apply enrichment selection strategy → Choose canonical values
    ↓
Populate _canonical_cache with PropertyData objects
```

### Geocoding Flow (with cache)

```
New property needs geocoding
    ↓
get_canonical_coordinates(address_normalized)
    ↓
Cache Hit? → YES → Use cached coordinates
    |              ↓
    |          Skip external API call
    |              ↓
    |          Return coordinates
    |
    NO
    ↓
Call Mapbox/Nominatim API
    ↓
Validate coordinates
    ↓
cache_coordinates(address_normalized, lat, lon)
    ↓
Return coordinates
```

### Enrichment Flow (with cache)

```
Property needs enrichment
    ↓
get_canonical_property_data(address_normalized)
    ↓
Cache Hit with enrichment? → YES → Use cached bedrooms/type
    |                                ↓
    |                            Skip web scraping
    |                                ↓
    |                            Return enrichment data
    |
    NO
    ↓
Web scrape property details (DuckDuckGo search)
    ↓
Wait 10 seconds (rate limiting)
    ↓
cache_enrichment_data(address_normalized, bedrooms, property_type)
    ↓
Return enrichment data
```

## Selection Strategies

### Hybrid Coordinate Selection

**Goal:** Choose the most accurate coordinate pair for each address.

**Algorithm:**
```
For address with multiple coordinate pairs:

1. Fetch all sales with coordinates:
   SELECT latitude, longitude, sale_date, geocode_quality_issue
   FROM properties
   WHERE address_normalized = $1
     AND latitude IS NOT NULL
   ORDER BY sale_date DESC

2. Filter to coordinates WITHOUT geocode_quality_issue=TRUE:
   candidates = [c for c in coords if not c.geocode_quality_issue]

3. If candidates is non-empty:
     a. Group by (lat, lon) and count occurrences
     b. Pick most common coordinate pair
     c. If tie in count:
        - Pick pair with most recent sale_date
     d. If still tied:
        - Use lexicographic sort on (latitude, longitude)
   Else (all have quality issues):
     a. Use all coordinates (including quality issues)
     b. Group by (lat, lon) and count occurrences
     c. Pick most common coordinate pair
     d. If tie: most recent sale_date
     e. If still tied: lexicographic sort

4. Return chosen (latitude, longitude)
```

**Rationale:**
- Prioritize coordinates without known quality issues
- Democratic approach: most common coordinate likely correct
- Recency as tiebreaker: newer geocoding may use better data
- Deterministic tiebreaker: lexicographic sort ensures consistency

### Enrichment Value Selection

**Goal:** Choose the most reliable enrichment data for each address.

**Algorithm:**
```
For each field (bedrooms, property_type):

1. Fetch all sales with enrichment:
   SELECT bedrooms, property_type, sale_date, price
   FROM properties
   WHERE address_normalized = $1
     AND (bedrooms IS NOT NULL OR property_type IS NOT NULL)
   ORDER BY sale_date DESC

2. For bedrooms:
   a. Group by bedroom count and count occurrences
   b. Pick most common value
   c. If tie: pick value from most recent sale_date
   d. If still tied: pick value from highest price (better listing data)

3. For property_type:
   a. Group by property_type and count occurrences
   b. Pick most common value
   c. If tie: pick value from most recent sale_date
   d. If still tied: pick value from highest price

4. Return chosen (bedrooms, property_type)
```

**Rationale:**
- Most common value likely correct (reduces impact of scraping errors)
- Recent sales have better listing data (more photos, detailed descriptions)
- High-value properties have more detailed listings (better for scraping)

## Error Handling

### Cache Initialization Failures

**Scenario:** Cannot connect to database during cache initialization.

**Handling:**
- Raise exception immediately with clear error message
- Do not run script with empty cache (defeats consistency purpose)
- User must fix database connection before proceeding

**Code:**
```python
def initialize_cache(database_url: str) -> None:
    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        raise RuntimeError(
            f"Cannot initialize canonical cache: database connection failed. "
            f"Refusing to run with empty cache. Error: {e}"
        )
```

### Cache Miss During Runtime

**Scenario:** Property not in cache, external API call fails.

**Handling:**
- Return None from geocoding/enrichment function
- Allow script to flag property with `needs_geocoding=TRUE` for retry
- Log warning with address details

**Code:**
```python
coords = get_canonical_coordinates(address_normalized)
if coords is None:
    try:
        coords = await geocode_with_mapbox(address)
        cache_coordinates(address_normalized, coords[0], coords[1])
    except Exception as e:
        logger.warning(f"Geocoding failed for {address}: {e}")
        return None  # Will retry later
```

### Conflicting Coordinates (Tiebreaker Edge Case)

**Scenario:** Address has 2 coordinate pairs with same frequency, same quality, same recency.

**Handling:**
- Use lexicographic sort on (latitude, longitude) as final tiebreaker
- Ensures deterministic, reproducible results
- Log as "tie_broken_arbitrarily" in audit trail

**Code:**
```python
if len(top_coords) > 1:
    # Deterministic tiebreaker: lexicographic sort
    chosen = sorted(top_coords, key=lambda c: (c[0], c[1]))[0]
    reason = "tie_broken_arbitrarily"
else:
    chosen = top_coords[0]
    reason = "most_common"
```

### Address Normalization Missing

**Scenario:** Some properties have `address_normalized = NULL`.

**Handling:**
- Fix script generates normalized address on-the-fly
- Uses same normalization logic as `sync_ppr_updates.py`
- Updates both `address_normalized` and coordinates in single transaction

**Code:**
```python
if address_normalized is None:
    from sync_ppr_updates import normalize_address
    address_normalized = normalize_address(address)
    # Update property record with normalized address
```

### Partial Batch Failure in Fix Script

**Scenario:** Database update fails mid-batch during fix script execution.

**Handling:**
- Transaction rollback for failed batch
- Log error with batch details
- Continue processing next batch
- Script is resumable: re-run skips already-fixed addresses

**Code:**
```python
for batch in batches:
    try:
        async with conn.transaction():
            # Update coordinates for batch
            await update_batch(conn, batch)
            logger.info(f"Fixed batch: {len(batch)} addresses")
    except Exception as e:
        logger.error(f"Batch failed: {e}. Rolling back and continuing.")
        continue  # Next batch
```

### Memory Constraints

**Scenario:** 694k addresses might use significant memory (~50-100MB for cache).

**Handling:**
- Acceptable for modern systems with 4GB+ RAM
- Add memory usage logging at cache initialization
- If issues arise, can implement LRU cache with size limit

**Monitoring:**
```python
import sys

def initialize_cache(database_url: str) -> None:
    # ... populate cache ...
    cache_size = sys.getsizeof(_canonical_cache)
    logger.info(f"Cache initialized: {len(_canonical_cache)} addresses, "
                f"{cache_size / 1024 / 1024:.1f} MB")
```

## Edge Cases

### New Properties with Same Address as Inconsistent Address

**Scenario:** New sale imported for address that previously had inconsistent coordinates.

**Handling:** Use canonical coordinates from cache, don't re-geocode.

**Result:** New sale automatically gets consistent coordinates.

### Manual Coordinate Corrections

**Scenario:** Admin manually updates coordinates in database after fix script runs.

**Handling:** Cache is stale until next script run.

**Mitigation:** Acceptable - manual corrections are rare. If frequent corrections needed, document process to clear cache or restart scripts.

### Multiple Concurrent Geocoding Scripts

**Scenario:** Two geocoding scripts running simultaneously.

**Handling:** Each has own in-memory cache (isolated), no cache coherency issues.

**Why safe:** Database is source of truth. Worst case: both scripts geocode same new address (small waste, no data corruption).

### Property Address Changes Over Time

**Scenario:** Property is renumbered, street name changes, or property is subdivided.

**Handling:** Out of scope. Treat as different properties.

**Rationale:** PPR data doesn't track address changes. If address text differs, it's a different cache entry.

## Testing Strategy

### Unit Tests (`tests/test_canonical_geocoding.py`)

**Cache Operations:**
- Test cache initialization from mock database
- Test get/set operations for coordinates and enrichment
- Test cache hit/miss scenarios
- Test memory usage calculation

**Hybrid Selection Strategy:**
- Test selection with quality issues vs without quality issues
- Test most common coordinate selection
- Test tie-breaking by recency
- Test lexicographic tiebreaker for identical scenarios
- Test edge case: all coordinates have quality issues

**Enrichment Selection:**
- Test most common bedroom count selection
- Test most common property_type selection
- Test tie-breaking by recency
- Test tie-breaking by price
- Test partial enrichment (bedrooms but no property_type)

**Address Normalization:**
- Test handling of NULL address_normalized
- Test cache key consistency across different address formats

**Test Data Fixtures:**
```python
# Address with multiple coordinates (quality issue vs no quality issue)
test_data_quality_mix = [
    {"lat": 53.35, "lon": -6.26, "quality_issue": False, "sale_date": "2025-01-01"},
    {"lat": 53.36, "lon": -6.27, "quality_issue": True, "sale_date": "2024-01-01"},
]

# Address with multiple bedrooms (3 vs 4)
test_data_bedrooms = [
    {"bedrooms": 3, "sale_date": "2025-01-01", "price": 400000},
    {"bedrooms": 3, "sale_date": "2024-06-01", "price": 380000},
    {"bedrooms": 4, "sale_date": "2023-01-01", "price": 420000},
]
```

### Integration Tests

**Fix Script Validation:**
- Create test database with sample inconsistent addresses
- Run fix script on test data
- Verify all sales of same address get identical coordinates
- Verify audit log completeness and format
- Test batch commit and resumability (interrupt and restart)

**Geocoding Script Integration:**
- Test `geocode_mapbox_batch.py` with cache enabled
- Mock Mapbox API responses
- Verify API calls only happen for cache misses
- Verify cached coordinates are used correctly
- Verify cache is updated after successful geocoding

**Enrichment Script Integration:**
- Test enrichment scripts with pre-populated cache
- Mock web scraping responses
- Verify no web scraping happens for cached addresses
- Verify cache updates after new enrichment
- Verify 10-second rate limiting is skipped for cached addresses

### Production Validation

**After running fix script:**

1. **Zero inconsistencies check:**
```sql
-- Should return 0
SELECT COUNT(DISTINCT address_normalized) 
FROM (
    SELECT address_normalized
    FROM properties
    GROUP BY address_normalized
    HAVING COUNT(*) > 1 AND COUNT(DISTINCT latitude) > 1
) sub;
```

2. **Enrichment consistency check:**
```sql
-- Should return 0 for both
SELECT COUNT(DISTINCT address_normalized)
FROM (
    SELECT address_normalized
    FROM properties
    WHERE bedrooms IS NOT NULL
    GROUP BY address_normalized
    HAVING COUNT(DISTINCT bedrooms) > 1
) sub;

SELECT COUNT(DISTINCT address_normalized)
FROM (
    SELECT address_normalized
    FROM properties
    WHERE property_type IS NOT NULL
    GROUP BY address_normalized
    HAVING COUNT(DISTINCT property_type) > 1
) sub;
```

3. **Spot-check random addresses:**
```sql
-- Pick 10 previously-inconsistent addresses
-- Verify all sales have identical coordinates
SELECT address_normalized, 
       COUNT(DISTINCT latitude) as distinct_lats,
       COUNT(DISTINCT longitude) as distinct_lons,
       COUNT(*) as total_sales
FROM properties
WHERE address_normalized IN (
    -- Sample from audit log
    'meenmore, dungloe, donegal',
    '86 captains ave, crumlin, dublin 12',
    -- ... etc
)
GROUP BY address_normalized;
```

4. **Run existing production test suite:**
```bash
python3 tests/test_production_suite.py
```
Should pass all tests with no regressions.

## Implementation Checklist

**Phase 1: Core Module**
- [ ] Create `scripts/canonical_geocoding.py` with PropertyData class
- [ ] Implement cache initialization from database
- [ ] Implement hybrid coordinate selection strategy
- [ ] Implement enrichment selection strategy
- [ ] Implement get/set cache functions
- [ ] Add memory usage logging
- [ ] Write unit tests for canonical_geocoding module

**Phase 2: Fix Script**
- [ ] Create `scripts/fix_geocoding_inconsistencies.py`
- [ ] Query addresses with inconsistent coordinates
- [ ] Query addresses with inconsistent enrichment
- [ ] Apply selection strategies
- [ ] Implement batch updates with transaction handling
- [ ] Create audit log JSON output
- [ ] Add progress reporting
- [ ] Test on subset of data
- [ ] Write integration tests for fix script

**Phase 3: Geocoding Script Integration**
- [ ] Modify `scripts/geocode_mapbox_batch.py`
- [ ] Modify `scripts/sync_ppr_updates.py`
- [ ] Modify `scripts/geocode_from_existing_fast.py`
- [ ] Test each modified script with cache
- [ ] Verify API call reduction

**Phase 4: Enrichment Script Integration**
- [ ] Modify `scripts/enrich_recent_properties.py`
- [ ] Modify `scripts/enrich_multi_batch.py`
- [ ] Modify `scripts/enrich_from_csv.py`
- [ ] Test each modified script with cache
- [ ] Verify web scraping reduction

**Phase 5: Production Deployment**
- [ ] Run fix script on production database (backup first!)
- [ ] Run validation queries
- [ ] Spot-check results
- [ ] Run production test suite
- [ ] Monitor first biweekly PPR sync with new system
- [ ] Document cache usage in CLAUDE.md

## Success Metrics

**Data Quality:**
- Zero addresses with inconsistent coordinates (down from 51,669)
- Zero addresses with inconsistent bedroom counts (down from 11)
- Zero addresses with inconsistent property types (down from 31)

**Performance:**
- Geocoding: 70-80% cache hit rate for biweekly PPR sync (reusing coordinates from prior sales)
- Enrichment: 60-70% cache hit rate for new enrichment runs (skipping known addresses)
- API cost reduction: ~60% fewer Mapbox API calls, ~60% fewer web scrapes

**Maintainability:**
- All geocoding/enrichment scripts use canonical module
- Single source of truth for coordinate selection logic
- Comprehensive test coverage (>90% for canonical_geocoding module)

## Future Enhancements (Out of Scope)

- Persistent cache storage (Redis, database table, file-based cache)
- Cache TTL/expiration for stale data
- Admin UI for viewing/editing canonical coordinates
- API endpoint to query canonical coordinates
- Real-time cache synchronization across distributed scripts
- Machine learning model to predict best coordinate from multiple options
- Address change tracking (property renumbering, street name changes)

## References

- Analysis showing 51,669 addresses with inconsistent coordinates
- CLAUDE.md: Project architecture and geocoding pipeline
- `scripts/geocode_mapbox_batch.py`: Current geocoding implementation
- `scripts/sync_ppr_updates.py`: Biweekly PPR sync process
- `scripts/enrich_recent_properties.py`: Web scraping enrichment process
