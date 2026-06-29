# Search Logic - Critical Business Rules

**PROTECTED**: Changes to search logic require automated tests to pass + manual verification

## Overview

Search is the core feature of HomeIQ. This document defines expected behavior for county filtering, exact matching, and radius search. Any changes MUST maintain these guarantees.

## County Filter Behavior

### 1. Exact Search (`/search/exact`)

**Purpose**: Find ALL sales for a specific address (sales history for property pages)

**Rules**:
- MUST respect county parameter in both prefix and full-text search queries
- Cache key MUST include county for proper isolation
- Returns empty list if no matches in filtered county (correct behavior - don't show wrong county)
- Normalizes address input same as database (abbreviations, punctuation, title case)

**SQL Pattern**:
```sql
-- With county filter
WHERE starts_with(COALESCE(address_normalized, address), $1)
  AND county = $2

-- Without county filter  
WHERE starts_with(COALESCE(address_normalized, address), $1)
```

**Example**:
- Query: "36 fairfield road", County: "Dublin" → 0 results ✅ (correct - property is in Cork)
- Query: "36 fairfield road", County: "Cork" → 1 result ✅ (exact match in Cork)
- Query: "36 fairfield road", County: None → 1 result ✅ (returns all counties)

### 2. Radius Search (`/search`)

**Purpose**: Find properties near a geocoded location (map search, comparable properties)

**Rules**:
- MUST respect county parameter in ST_DWithin spatial query
- Auto-expansion (2x, 3x, 5x, 10x up to 20km) MUST stay within county bounds
- Geocoding MUST pass county hint to Nominatim for disambiguation
- Results ordered by distance (ST_Distance) ascending

**SQL Pattern**:
```sql
-- With county filter
WHERE ST_DWithin(geom::geography, ST_MakePoint($lon, $lat)::geography, $radius_m)
  AND county = $county

-- Without county filter
WHERE ST_DWithin(geom::geography, ST_MakePoint($lon, $lat)::geography, $radius_m)
```

**Example**:
- Query: "Glasnevin", County: "Dublin", Radius: 0.5km → Only Dublin results within 500m
- Query: "Main Street", County: "Cork" → Geocodes to Cork's Main Street, not Dublin's

### 3. Polygon Search (`/search/polygon`)

**Purpose**: Find properties within user-drawn map area

**Rules**:
- Uses ST_Within for polygon containment
- No county filter (polygon implicitly defines boundaries)
- Up to 1,000 results per query
- Supports price/year filters

## Cache Isolation

**CRITICAL**: Cache keys MUST include county parameter to prevent leakage.

```python
# ✅ CORRECT
cache_key = {"address": normalized, "county": county}

# ❌ WRONG - different counties would share cached results
cache_key = {"address": normalized}
```

**Cache TTLs**:
- Exact search: 24 hours (address sales history changes rarely)
- Radius search: 5 minutes (more dynamic, user expects fresh data)
- Trends: 1 hour (aggregated data, expensive to compute)

## Address Normalization

All addresses stored in `address_normalized` column with consistent formatting:
- Remove "No." prefix from house numbers
- Expand abbreviations: Rd→Road, St→Street, Ave→Avenue, Dr→Drive
- Title case with exceptions (Dublin, Cork, Co., etc.)
- Clean punctuation and whitespace

**User input normalization** (in API):
Search queries MUST be normalized with same logic before querying to ensure matches.

## Test Coverage

All search behavior protected by `tests/test_search_core.py`:

1. **County filter correctness** - exact and radius search
2. **Cross-county ambiguous addresses** - "Main Street" in Cork vs Galway  
3. **Cache isolation** - Dublin/Cork requests don't share cache
4. **Performance** - queries complete in < 1 second
5. **Eircode search** - routing key lookup and validation

## Pre-Merge Checklist

Before merging ANY search-related changes:

- [ ] All tests in `tests/test_search_core.py` pass locally
- [ ] GitHub Actions workflow passes (auto-runs on PR)
- [ ] Manual browser test: "36 fairfield road" + Dublin filter = 0 results
- [ ] Manual browser test: "36 fairfield road" + Cork filter = 1 result  
- [ ] Manual browser test: "19 fairfield road" + Dublin filter = 2 results
- [ ] No performance regression: check response times in logs
- [ ] Cache behavior verified if cache logic changed
- [ ] Database query uses indexes (run EXPLAIN ANALYZE)

## Common Pitfalls

### ❌ DON'T: Forget county filter in fallback queries

```python
# WRONG - full-text search doesn't respect county
rows = await db_pool.fetch("""
    SELECT * FROM properties
    WHERE to_tsvector('english', address) @@ to_tsquery('english', $1)
""", search_terms)
```

```python
# CORRECT - apply county filter consistently
if county:
    rows = await db_pool.fetch("""
        SELECT * FROM properties
        WHERE to_tsvector('english', address) @@ to_tsquery('english', $1)
          AND county = $2
    """, search_terms, county)
```

### ❌ DON'T: Use LIKE queries

LIKE queries don't use indexes efficiently and create maintenance issues:

```python
# WRONG
WHERE UPPER(address) LIKE UPPER($1) || '%'

# CORRECT - use normalized column with prefix search
WHERE starts_with(address_normalized, $1)
```

### ❌ DON'T: Merge results client-side by county

Let the database filter. Don't fetch all results and filter in Python/TypeScript.

```python
# WRONG - wastes bandwidth and CPU
all_results = await search_all_counties(query)
filtered = [r for r in all_results if r.county == county]

# CORRECT - filter in SQL
results = await search_with_county_filter(query, county)
```

## Monitoring

If using Sentry, track county filter breaches:

```python
# Alert if results contain wrong county
if county and result["count"] > 0:
    result_counties = {r["county"] for r in result["results"]}
    if county not in result_counties:
        sentry_sdk.capture_message(
            f"County filter breach: requested {county}, got {result_counties}",
            level="error",
            extras={"query": q, "county": county}
        )
```

## Related Documentation

- [Address Normalization](../scripts/normalize_addresses.py) - normalization logic
- [CLAUDE.md](../CLAUDE.md) - full project context
- [Schema](../db/schema.sql) - database structure and indexes
- [Test Suite](../tests/test_search_core.py) - automated test cases

## Questions?

Contact: @niallirlmurphy
Last updated: 2026-06-29
