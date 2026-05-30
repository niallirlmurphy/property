# County Filter Fallback Fix

**Date**: 2026-05-21  
**Issue**: Search returns 0 results when geocoding is correct but county filter doesn't match

## Problem

When a user searches for a location (e.g., "Nobber, Meath") with a default county filter set (e.g., "Dublin"), the backend would:
1. Successfully geocode "Nobber" to correct coordinates (53.82, -6.75 in Meath)
2. Run radius search with `county = 'Dublin'` filter
3. Return 0 results because Nobber is in Meath, not Dublin

This was confusing to users who expected results for valid locations.

## Solution

**Auto-retry without county filter if no results found**

The search endpoint now implements a two-stage fallback:

1. **First attempt**: Search with all filters including county (if provided)
   - Try radius expansion: 1km → 2km → 3km → 5km → 10km → 20km
   - If results found, return them
   
2. **Second attempt**: If still 0 results and county filter was applied, retry without it
   - Remove county filter only
   - Keep all other filters (price, year, etc.)
   - Reset radius and try expansion again: 1km → 2km → 3km → 5km → 10km → 20km
   - Return results from any county near the geocoded location

## Response Changes

The `/search` endpoint now includes a new field:

```json
{
  "center": {"lat": 53.82, "lon": -6.75},
  "radius_km": 5.0,
  "radius_expanded": false,
  "county_filter_removed": true,  // NEW: indicates county filter was dropped
  "requested_radius_km": 5.0,
  "count": 42,
  "results": [...]
}
```

## Logging

When the fallback occurs, the backend logs:

```
No results found with county filter 'Dublin' for query 'Nobber', retrying without county filter
```

This helps monitor how often the fallback is triggered and identify patterns.

## Frontend Integration

The frontend can use the `county_filter_removed` flag to:
- Show a message: "Showing results from Meath (no results found in Dublin)"
- Update the county filter UI to reflect actual results
- Provide clearer feedback about what was searched

## Example Scenarios

### Before Fix
- Search: "Nobber" with county=Dublin
- Result: 0 results (confusing - Nobber exists!)

### After Fix
- Search: "Nobber" with county=Dublin
- First attempt: 0 results with county=Dublin
- Second attempt: 42 results from Meath (county filter removed)
- Response includes `county_filter_removed: true`

### Still Works Normally
- Search: "Rathmines" with county=Dublin
- First attempt: Found results in Dublin
- No fallback needed
- Response includes `county_filter_removed: false`

## Edge Cases

1. **County filter intentional**: If user explicitly filters to Dublin only, the fallback still occurs. This is by design - a geocoded location should show results even if county doesn't match.

2. **Still no results**: If no properties exist near the geocoded location in any county, still returns 0 results (as expected).

3. **Other filters**: Price and year filters are preserved in the retry (only county is removed).

4. **Performance**: Minimal impact - fallback only runs when first attempt returns 0 results.

## Commit

```
41029f0 - Auto-retry search without county filter if no results found
```

## Related Issues

- Original issue: Nobber search returning 0 results with Dublin county filter
- Root cause: County filter mismatch when geocoding resolves to different county
- Similar issues likely for any cross-county search with default filters
