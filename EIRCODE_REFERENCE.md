# Eircode Reference Database

## Overview

The `eircode_reference` table provides fast, local geocoding for Irish Eircodes without external API calls. It contains pre-computed centroid coordinates for **222,539 unique Eircodes** covering **29.8% of the PPR database** (233,545 properties).

## Data Source

**Built from Property Price Register (PPR) data:**
- Source: Existing PPR properties with validated coordinates
- Coverage: All Eircodes present in residential sales 2010-2026
- Quality: Validated coordinates within Ireland bounds (51.4-55.5°N, -10.7--5.4°W)
- Routing Keys: 302 unique 3-character prefixes (D01-D24, H91, V94, etc.)

**Future Enhancement:**
- Potential integration with GeoHive/OSI open geospatial datasets
- Autoaddress API enrichment for missing Eircodes
- Quarterly updates from new PPR sales

## Database Schema

```sql
CREATE TABLE eircode_reference (
    eircode TEXT PRIMARY KEY,              -- Full 7-char Eircode (D02XY45)
    latitude NUMERIC NOT NULL,             -- Centroid latitude
    longitude NUMERIC NOT NULL,            -- Centroid longitude
    property_count INTEGER NOT NULL,       -- Properties used for centroid
    county TEXT,                           -- Primary county
    routing_key TEXT,                      -- 3-char prefix (D02)
    std_lat NUMERIC,                       -- Cluster tightness (latitude)
    std_lon NUMERIC,                       -- Cluster tightness (longitude)
    source TEXT DEFAULT 'ppr',             -- Data source
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Geocoding Integration

The Eircode reference table is integrated into the geocoding waterfall at **Stage 5**:

```
1. Raw coordinates      (instant passthrough)
2. Cache hit           (24h TTL)
3. Routing key → DB    (D02 → centroid of all D02 properties)
4. Full Eircode → PPR  (exact match from properties table)
5. ✨ Full Eircode → Reference table ✨  [NEW]
6. Token-based → DB    (address matching)
7. Nominatim          (OSM geocoder)
8. Mapbox             (commercial fallback)
9. Fuzzy DB ILIKE     (last resort)
```

### Why This Order?

- **Stage 4** checks properties table first (real-time, most accurate)
- **Stage 5** provides fallback for Eircodes not in recent sales
- Reference table is **pre-computed and indexed** (sub-millisecond lookup)
- Avoids external API calls for 222k+ Eircodes

## Usage

### Setup

```bash
# Create the reference table and populate from PPR data
python3 scripts/setup_eircode_reference.py

# Rebuild (drop and recreate)
python3 scripts/setup_eircode_reference.py --rebuild
```

### Query Examples

**Direct table query:**
```sql
-- Get coordinates for specific Eircode
SELECT latitude, longitude, property_count
FROM eircode_reference
WHERE eircode = 'D02XY45';

-- Get all Eircodes in routing key
SELECT eircode, latitude, longitude
FROM eircode_reference
WHERE routing_key = 'D02'
ORDER BY property_count DESC
LIMIT 10;
```

**Using the helper function:**
```sql
-- Geocode with automatic fallback to routing key
SELECT * FROM get_eircode_coordinates('D02 XY45');
-- Returns: (lat, lon, source, confidence)

SELECT * FROM get_eircode_coordinates('D02');
-- Falls back to routing key centroid
```

### API Integration

The backend automatically uses this table:

```bash
# These requests now hit the reference table
curl "https://homeiq.ie/api/geocode?q=D02XY45"
curl "https://homeiq.ie/api/search?q=D02XY45&radius_km=1"
```

## Statistics

### Coverage by Routing Key (Top 10)

| Routing Key | Unique Eircodes | Properties | Area |
|-------------|----------------|------------|------|
| V94 | 8,006 | 8,434 | Limerick City |
| H91 | 6,996 | 7,300 | Galway City |
| T12 | 6,437 | 6,703 | Cork City |
| D15 | 6,308 | 6,579 | Dublin 15 |
| X91 | 5,099 | 5,474 | Waterford City |
| D24 | 4,464 | 4,662 | Dublin 24 |
| A92 | 4,436 | 4,660 | Dundalk/Drogheda |
| W91 | 4,168 | 4,375 | Sligo |
| D18 | 3,950 | 4,134 | Dublin 18 |
| R32 | 3,588 | 3,789 | Roscommon |

### Data Quality

**Confidence Levels:**
- **High:** Standard deviation < 0.001° (~100m radius) - properties in same building
- **Medium:** Standard deviation < 0.01° (~1km radius) - properties in same neighborhood  
- **Low:** Standard deviation > 0.01° - scattered properties

**Typical Accuracy:**
- Urban Eircodes (D01-D24, H91, V94): **High** (rooftop to street level)
- Suburban Eircodes: **Medium** (neighborhood level)
- Rural Eircodes: **Medium-Low** (townland level)

## Benefits

### Performance
- **Speed:** <1ms lookup (indexed table query)
- **Cost:** €0 (no external API calls)
- **Availability:** 100% uptime (local database)
- **Scalability:** Handles unlimited requests

### Coverage Improvement
- **Before:** 29.8% exact Eircode matches from PPR properties table
- **After:** Same 29.8% but with optimized, pre-computed lookups
- **Routing Keys:** 100% coverage for 302 prefixes (always have fallback)

### Future Enhancements
When official GeoHive data becomes available:
1. Download OSI Eircode point dataset (~700k Eircodes)
2. Import with `source='geohive'`
3. Automatic coverage increase to 90%+

## Maintenance

### Update Schedule

**Automatic:**
- New PPR properties with Eircodes are used in real-time (Stage 4)
- Reference table provides fallback for historical data

**Manual (recommended quarterly):**
```bash
# Rebuild reference table with latest PPR data
python3 scripts/setup_eircode_reference.py --rebuild
```

### Monitoring

```sql
-- Check table size and coverage
SELECT
    COUNT(*) as total_eircodes,
    COUNT(DISTINCT routing_key) as routing_keys,
    SUM(property_count) as total_properties,
    MAX(updated_at) as last_update
FROM eircode_reference;

-- Find gaps (routing keys with few Eircodes)
SELECT
    routing_key,
    COUNT(*) as eircode_count,
    SUM(property_count) as property_count
FROM eircode_reference
GROUP BY routing_key
HAVING COUNT(*) < 100
ORDER BY COUNT(*);
```

## Troubleshooting

### No results for known Eircode

**Check if Eircode exists in PPR:**
```sql
SELECT COUNT(*), AVG(latitude), AVG(longitude)
FROM properties
WHERE REPLACE(UPPER(eircode), ' ', '') = 'D02XY45'
  AND latitude IS NOT NULL;
```

**Check if in reference table:**
```sql
SELECT * FROM eircode_reference WHERE eircode = 'D02XY45';
```

**If missing:** Eircode not in PPR data (no sales with that Eircode yet)
- Fallback: Use routing key (D02)
- Future: Autoaddress API enrichment

### Poor coordinate quality

**Check cluster tightness:**
```sql
SELECT eircode, std_lat, std_lon, property_count
FROM eircode_reference
WHERE eircode = 'D02XY45';
```

**High standard deviation (>0.01):** Properties are scattered
- Possible causes: Large Eircode coverage area, data quality issues
- Solution: Use with appropriate search radius

## Related Documentation

- **Geocoding Flow:** See `backend/main.py` `resolve_location()` function
- **PPR Database:** See `db/schema.sql`
- **Routing Keys:** See `routing_key_stats` materialized view
- **About Page:** Frontend displays GeoHive/OSI attribution

## License & Attribution

**Data Source:**
- Property Price Register (Irish Government Open Data)
- Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)
- https://www.propertypriceregister.ie

**Attribution:**
When using this data, credit should be given to:
- Property Services Regulatory Authority (PSRA)
- Ordnance Survey Ireland (OSI) - for geospatial framework
- HomeIQ.ie - for data processing and geocoding

## Future Enhancements

### Phase 1: GeoHive Integration (€0, 90% coverage)
- Download OSI Eircode boundary dataset
- Import ~700k Eircode centroids
- Update script: `scripts/import_geohive_eircodes.py`

### Phase 2: Autoaddress Enrichment (€2,800, 70% coverage)
- Enrich 280k missing Eircodes via Autoaddress API
- Focus on recent sales (2020+) and high-value properties
- Update reference table with rooftop-level coordinates

### Phase 3: Continuous Updates
- Automatic rebuild on PPR data refresh (biweekly)
- Real-time enrichment for new Eircodes
- Quality monitoring dashboard
