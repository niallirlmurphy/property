# Duplicate Handling Strategy

## Overview

Many properties in the PPR database have multiple sales over time (2010-2026). When we gather new data for one sale (geocoding, enrichment, etc.), we should **automatically apply it to ALL sales of that property** to maximize data quality and minimize API costs.

## Rationale

**Example:** "28 Slane Road, Crumlin, Dublin 12" has 3 sales:
- 2023: €285,500
- 2024: €530,000
- 2025: €465,000

If we find that it's a "5 bed terraced house" when enriching the 2025 sale, we should apply this to ALL 3 sales since the property characteristics don't change between sales.

Similarly, if we geocode one sale to coordinates (53.32645, -6.29807), all 3 sales should get the same coordinates.

## Benefits

### 1. **Data Quality**
- Ensures consistency across all sales of the same property
- Reduces missing data percentage
- Improves database completeness

### 2. **Cost Efficiency**
- One web search enriches multiple sales
- One geocoding call provides coordinates for multiple records
- Reduces API usage and costs

### 3. **Impact Multiplier**
- **Batch 6 Example:** Target was 702 properties, but enriched 509 additional due to duplicates
- Each successful operation has 2-5x the impact when properties have multiple sales

## Implementation

### Central Module: `duplicate_handler.py`

Provides reusable functions for all data workflows:

```python
from duplicate_handler import (
    find_duplicate_sales,
    update_geocoding_for_duplicates,
    update_enrichment_for_duplicates,
    update_all_fields_for_duplicates,
    get_duplicate_statistics
)
```

### Key Functions

#### 1. **find_duplicate_sales(conn, address)**
Find all sales of the same property.

```python
duplicates = find_duplicate_sales(conn, "28 SLANE RD, CRUMLIN, DUBLIN 12")
# Returns list of all sales with id, address, sale_date, price
```

#### 2. **update_geocoding_for_duplicates(conn, address, lat, lon, eircode)**
Apply geocoding to all sales of an address.

```python
count = update_geocoding_for_duplicates(
    conn,
    address="28 SLANE RD, CRUMLIN, DUBLIN 12",
    latitude=53.32645,
    longitude=-6.29807,
    eircode="D12W227"
)
# Returns: 3 (all 3 sales updated)
```

#### 3. **update_enrichment_for_duplicates(conn, address, bedrooms, property_type)**
Apply enrichment to all sales of an address.

```python
count = update_enrichment_for_duplicates(
    conn,
    address="28 SLANE RD, CRUMLIN, DUBLIN 12",
    bedrooms=5,
    property_type="terraced"
)
# Returns: 3 (all 3 sales updated)
```

#### 4. **update_all_fields_for_duplicates(conn, address, ...)**
Apply all available data in one call.

```python
geo_count, enrich_count = update_all_fields_for_duplicates(
    conn,
    address="28 SLANE RD, CRUMLIN, DUBLIN 12",
    latitude=53.32645,
    longitude=-6.29807,
    bedrooms=5,
    property_type="terraced"
)
```

## Integrated Workflows

### 1. **Enrichment** (`enrich_recent_properties.py`, `enrich_batch6_2026.py`)

**Before:**
```python
# Update only the property we're processing
UPDATE properties SET bedrooms = 5, property_type = 'terraced'
WHERE id = 12345
```

**After:**
```python
# Update ALL sales of this address
from duplicate_handler import update_enrichment_for_duplicates

count = update_enrichment_for_duplicates(conn, address, bedrooms, property_type)
print(f"Updated {count} sales")  # Might be 1, 3, 5, etc.
```

### 2. **Geocoding** (`geocode_mapbox_batch.py`, PPR sync)

**Before:**
```python
# Geocode only one sale
UPDATE properties SET latitude = X, longitude = Y
WHERE id = 12345
```

**After:**
```python
# Geocode ALL sales of this address
from duplicate_handler import update_geocoding_for_duplicates

count = update_geocoding_for_duplicates(conn, address, lat, lon, eircode)
```

### 3. **PPR Import** (`sync_ppr_updates.py`)

When importing new sales, check if the property already exists and copy known data:

```python
from duplicate_handler import get_duplicate_statistics, find_duplicate_sales

# Check if we already have data for this address
stats = get_duplicate_statistics(conn, new_address)

if stats['total_sales'] > 0:
    # Property exists! Copy data from previous sales
    duplicates = find_duplicate_sales(conn, new_address)
    if duplicates:
        # Copy coords, bedrooms, property_type from most recent sale
        copy_data_from_duplicate(new_sale_id, duplicates[0])
```

## Statistics & Monitoring

### get_duplicate_statistics(conn, address)

Get comprehensive stats about a property:

```python
stats = get_duplicate_statistics(conn, "28 SLANE RD, CRUMLIN, DUBLIN 12")
print(f"Total sales: {stats['total_sales']}")
print(f"With coords: {stats['with_coords']} ({stats['coord_coverage']:.1f}%)")
print(f"With enrichment: {stats['with_enrichment']} ({stats['enrichment_coverage']:.1f}%)")
print(f"First sale: {stats['first_sale']}")
print(f"Latest sale: {stats['latest_sale']}")
print(f"Price range: €{stats['min_price']:,} - €{stats['max_price']:,}")
```

## Best Practices

### 1. **Always Use for New Data**
Whenever you update geocoding or enrichment data, use the duplicate handler to apply it to all sales.

### 2. **Report Impact**
Always report how many properties were updated:
```python
count = update_enrichment_for_duplicates(conn, address, bedrooms, property_type)
if count > 1:
    print(f"✅ Enriched {count} sales (duplicate detection)")
else:
    print(f"✅ Enriched 1 sale")
```

### 3. **Track Bonus Updates**
In batch scripts, track the duplicate multiplier:
```python
stats = {
    'processed': 100,
    'duplicate_bonus': 0  # Extra updates from duplicates
}

count = update_enrichment_for_duplicates(conn, address, bedrooms, property_type)
if count > 1:
    stats['duplicate_bonus'] += (count - 1)

# Report: "Processed 100 properties, bonus: 50 additional sales enriched"
```

### 4. **Don't Update Price**
The duplicate handler updates **property characteristics** (coords, bedrooms, type) but NOT **sale-specific data** (price, sale_date, not_full_market_price, etc.) which varies between sales.

## Performance Considerations

### Indexing
The duplicate queries use `WHERE address = $1` which should be indexed:

```sql
CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(address);
```

This index already exists in our schema.

### Batch Operations
For large batch jobs, duplicates are handled per-property, not in bulk. This is intentional to ensure accurate counting and logging.

## Testing

Test the module:
```bash
python3 scripts/duplicate_handler.py
```

This will test with "28 SLANE RD, CRUMLIN, DUBLIN 12" and show statistics.

## Migration Guide

### Updating Existing Scripts

1. **Import the module:**
```python
from duplicate_handler import update_enrichment_for_duplicates
```

2. **Replace single-row updates:**
```python
# Old
cur.execute("UPDATE properties SET bedrooms = %s WHERE id = %s", (beds, prop_id))

# New
count = update_enrichment_for_duplicates(conn, address, bedrooms=beds)
```

3. **Track and report duplicates:**
```python
if count > 1:
    stats['duplicate_updates'] += (count - 1)
```

## Results

### Batch 6 Enrichment (June 2026)
- **Target:** 702 properties
- **Enriched:** 632 properties (90%)
- **Bonus from duplicates:** 509 additional sales
- **Total impact:** 1,141 property records enriched
- **Multiplier:** 1.8x (each enrichment updated 1.8 properties on average)

### Coverage Improvement
- **Before Batch 6:** 80.3% of 2026 properties fully enriched
- **After Batch 6:** 83.2% of 2026 properties fully enriched
- **Net gain:** +2.9 percentage points (+509 properties)

## Future Enhancements

1. **Proactive Copying:** When importing new sales, automatically copy data from previous sales
2. **Validation:** Detect when different sales have conflicting data (e.g., different bedroom counts)
3. **Audit Trail:** Log when data is copied between sales for debugging
4. **Bulk API:** Create batch update functions for very large operations
