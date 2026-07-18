# Database Schema Documentation

Complete schema for the Property Price Register (PPR) database.

## Tables

### `properties`
Main table containing all property sales from Ireland's Property Price Register.

**Base columns** (from `schema.sql`):
```sql
id                    BIGSERIAL PRIMARY KEY
sale_date             DATE NOT NULL
address               TEXT NOT NULL
county                TEXT
eircode               TEXT
price                 NUMERIC(12, 2) NOT NULL
not_full_market_price BOOLEAN NOT NULL DEFAULT FALSE
vat_exclusive         BOOLEAN NOT NULL DEFAULT FALSE
description           TEXT
size_description      TEXT
latitude              DOUBLE PRECISION
longitude             DOUBLE PRECISION
geog                  GEOGRAPHY(Point, 4326)  -- PostGIS geography for fast spatial queries
```

**Additional columns** (from migrations):
```sql
-- Address normalization
address_normalized    TEXT  -- Normalized address for better geocoding matching

-- Eircode routing (from add_routing_key.sql)
routing_key           VARCHAR(3) GENERATED ALWAYS AS (
                        CASE WHEN eircode IS NOT NULL AND eircode != ''
                        THEN SUBSTRING(REPLACE(UPPER(eircode), ' ', ''), 1, 3)
                        ELSE NULL END
                      ) STORED  -- First 3 chars of Eircode (e.g., D02, H91)

-- Geocoding flags (from add_needs_geocoding_flag.sql and add_geocode_quality_flag.sql)
needs_geocoding       BOOLEAN DEFAULT FALSE  -- TRUE when imported without coordinates
geocode_quality_issue BOOLEAN DEFAULT FALSE  -- TRUE when validation detects quality issues

-- Property enrichment (from add_property_details_columns.sql)
bedrooms              INTEGER  -- Number of bedrooms (enriched from web search)
property_type         TEXT     -- house, apartment, terraced, detached, etc.

-- Property type provenance (from add_property_type_source.sql)
property_type_source  TEXT     -- how property_type was set, by confidence:
                                --   'web_enrichment'      scraped from listings (~90%, authoritative).
                                --                         NOTE: when property_type is ALSO NULL this means
                                --                         "scraped but found nothing" - a recorded attempt,
                                --                         deprioritised behind never-scraped rows.
                                --   'address_apartment'   APT/APARTMENT/FLAT token in address (~99%, protected)
                                --   'address_house_guess' bare place-name heuristic, 2010-2020 (~81%, overwritable)
                                --   NULL                  never attempted / legacy (highest scrape priority)
```

**Enrichment scrape priority** (`scripts/enrich_batch6_2026.py`): untyped rows
with `source IS NULL` (never attempted) are scraped first, then
`address_house_guess`, then untyped rows already stamped `web_enrichment`
(attempted, found empty) last.

**property_type precedence:** web enrichment overwrites `address_house_guess`,
legacy (NULL), and re-scraped rows on an address match, but never overwrites
`address_apartment`. The enrichment scraper (`scripts/enrich_batch6_2026.py`)
re-visits `address_house_guess` rows so real listing data replaces the guess.
Mark scripts: `scripts/mark_apartments_from_address.py`,
`scripts/mark_house_guess_from_address.py`.

**Indexes:**
```sql
-- Spatial indexes
CREATE INDEX properties_geog_idx ON properties USING GIST (geog);

-- Basic indexes
CREATE INDEX properties_county_idx ON properties (county);
CREATE INDEX properties_sale_date_idx ON properties (sale_date);
CREATE INDEX properties_price_idx ON properties (price);
CREATE INDEX properties_eircode_idx ON properties (eircode);

-- Functional index for eircode prefix matching
CREATE INDEX properties_eircode_norm_idx 
  ON properties (REPLACE(UPPER(eircode), ' ', ''))
  WHERE eircode IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX properties_county_date_idx 
  ON properties (LOWER(county), sale_date)
  WHERE not_full_market_price = FALSE;

-- Routing key indexes
CREATE INDEX idx_properties_routing_key 
  ON properties(routing_key)
  WHERE routing_key IS NOT NULL;

CREATE INDEX idx_properties_routing_key_date 
  ON properties(routing_key, sale_date DESC)
  WHERE routing_key IS NOT NULL;

-- Flag indexes (partial indexes for TRUE values only)
CREATE INDEX idx_properties_needs_geocoding 
  ON properties(needs_geocoding)
  WHERE needs_geocoding = TRUE;

CREATE INDEX idx_properties_geocode_quality_issue 
  ON properties(geocode_quality_issue)
  WHERE geocode_quality_issue = TRUE;

-- Enrichment indexes
CREATE INDEX properties_bedrooms_idx ON properties (bedrooms);
CREATE INDEX properties_property_type_idx ON properties (property_type);
```

**Current data stats** (as of 2026-06):
- Total properties: ~784,464
- Geocoded: ~614,200 (78.3%)
- With Eircode: ~233,000 (29.7%)
- Date range: 2010-01-01 to 2026-06-06
- Best geocoding coverage: 2022-2024 (89-91%)

---

### `routing_key_stats`
Materialized view with statistics and centroids for each Eircode routing key area.

```sql
CREATE MATERIALIZED VIEW routing_key_stats AS
SELECT
  routing_key           VARCHAR(3),
  primary_county        TEXT,              -- Most common county for this routing key
  property_count        BIGINT,            -- Total properties with this routing key
  counties              TEXT[],            -- All counties this routing key appears in
  earliest_sale         DATE,
  latest_sale           DATE,
  median_price          NUMERIC,           -- Median price (excluding not_full_market_price)
  centroid_lat          DOUBLE PRECISION,  -- Median latitude (geographic centroid)
  centroid_lon          DOUBLE PRECISION,  -- Median longitude
  geocoded_count        BIGINT,
  geocoded_pct          DOUBLE PRECISION   -- Percentage geocoded
FROM properties
WHERE routing_key IS NOT NULL
  AND routing_key ~ '^[A-Z][0-9][0-9W]$'
GROUP BY routing_key;
```

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_routing_key_stats_pk ON routing_key_stats(routing_key);
CREATE INDEX idx_routing_key_stats_count ON routing_key_stats(property_count DESC);
```

**Refresh:** Run `REFRESH MATERIALIZED VIEW routing_key_stats;` after bulk imports or periodically.

**Current stats:** 301 routing keys

---

### `submissions`
User feedback and contact form submissions.

```sql
id            BIGSERIAL PRIMARY KEY
kind          TEXT NOT NULL              -- 'feedback' | 'contact'
ts            TIMESTAMPTZ NOT NULL DEFAULT NOW()
name          TEXT
email         TEXT
datasets      TEXT
comments      TEXT
message       TEXT
price_updates BOOLEAN
```

**Indexes:**
```sql
-- None defined in base schema
```

---

### `search_log`
Analytics logging for all search queries.

```sql
id               BIGSERIAL PRIMARY KEY
ts               TIMESTAMPTZ NOT NULL DEFAULT NOW()
query            TEXT NOT NULL
resolved_lat     DOUBLE PRECISION
resolved_lon     DOUBLE PRECISION
radius_km        DOUBLE PRECISION NOT NULL
result_count     INTEGER NOT NULL
elapsed_ms       INTEGER NOT NULL
county_filter    TEXT
min_price        INTEGER
max_price        INTEGER
min_year         INTEGER
max_year         INTEGER
geocode_source   TEXT  -- 'db_exact' | 'nominatim' | 'db_tokens' | 'mapbox' | 'db_fuzzy' | 'cache'
user_agent       TEXT
ip_address       INET
```

**Indexes:**
```sql
CREATE INDEX search_log_ts_idx ON search_log (ts DESC);
CREATE INDEX search_log_query_idx ON search_log (query);
CREATE INDEX search_log_result_count_idx ON search_log (result_count) WHERE result_count = 0;
```

---

### `email_alerts`
User subscriptions for property price notifications.

```sql
id                BIGSERIAL PRIMARY KEY
email             TEXT NOT NULL
address           TEXT NOT NULL
radius_km         DOUBLE PRECISION NOT NULL DEFAULT 2.0
county            TEXT
is_active         BOOLEAN NOT NULL DEFAULT TRUE
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
last_sent_at      TIMESTAMPTZ
unsubscribe_token TEXT UNIQUE DEFAULT gen_random_uuid()::TEXT
```

**Indexes:**
```sql
CREATE INDEX email_alerts_active_idx ON email_alerts (is_active, email);
CREATE INDEX email_alerts_email_idx ON email_alerts (email);
CREATE INDEX email_alerts_token_idx ON email_alerts (unsubscribe_token);
```

---

## Views

### `properties_needing_geocoding`
Properties imported without coordinates, prioritized for geocoding.

```sql
CREATE OR REPLACE VIEW properties_needing_geocoding AS
SELECT
    id, sale_date, address, county, eircode, routing_key, price, description,
    CASE
        WHEN price > 500000 THEN 1
        WHEN price > 300000 THEN 2
        ELSE 3
    END as priority_tier
FROM properties
WHERE needs_geocoding = TRUE
ORDER BY priority_tier, sale_date DESC, price DESC;
```

**Purpose:** Used by biweekly PPR sync and geocoding scripts to queue properties for geocoding.

---

### `properties_needing_regeocode`
Properties with geocoding quality issues, prioritized for re-geocoding.

```sql
CREATE OR REPLACE VIEW properties_needing_regeocode AS
SELECT
    id, address, county, eircode, routing_key,
    latitude, longitude, sale_date, price,
    -- Calculate distance from routing key centroid
    CASE WHEN routing_key IS NOT NULL THEN (
        SELECT ST_Distance(
            ST_MakePoint(longitude, latitude)::geography,
            ST_MakePoint(AVG(p2.longitude), AVG(p2.latitude))::geography
        ) / 1000.0
        FROM properties p2
        WHERE p2.routing_key = properties.routing_key
          AND p2.latitude IS NOT NULL
    ) ELSE NULL END as distance_from_centroid_km
FROM properties
WHERE geocode_quality_issue = TRUE
ORDER BY
    CASE WHEN price > 500000 THEN 1 ELSE 2 END,
    sale_date DESC,
    CASE WHEN routing_key IS NOT NULL THEN 1 ELSE 2 END;
```

**Purpose:** Used by `export_bad_geocodes.py` and re-geocoding workflows.

---

## Schema Evolution

### Initial schema
- `schema.sql` - Base table with address, price, coordinates

### Migrations (in order)
1. `migrate_perf.sql` - Add geography column, functional indexes, composite indexes
2. `add_routing_key.sql` - Generate routing keys from Eircodes, create stats view
3. `add_needs_geocoding_flag.sql` - Flag for properties needing initial geocoding
4. `add_geocode_quality_flag.sql` - Flag for properties needing re-geocoding
5. `add_property_details_columns.sql` - Add bedrooms and property_type for enrichment
6. `add_search_log.sql` - Analytics logging table
7. `email_alerts.sql` - User notification subscriptions

### Address normalization
Applied via `scripts/normalize_addresses.py` - adds `address_normalized` column with:
- Title case formatting
- Whitespace cleanup
- Standardized abbreviations
- Remove "No." prefix
- Standardize apartment/unit notation

---

## Column Usage Guide

### For exports/reports
**Always include:**
- `id`, `sale_date`, `address`, `county`, `eircode`, `price`
- `latitude`, `longitude` (for mapping)
- `not_full_market_price`, `vat_exclusive` (for price analysis)

**Optional enrichment:**
- `bedrooms`, `property_type` (when available)
- `routing_key` (for area-based grouping)
- `address_normalized` (for geocoding/matching)

**For debugging:**
- `needs_geocoding`, `geocode_quality_issue`
- `description`, `size_description`

### For geocoding scripts
**Query:** `id`, `address`, `address_normalized`, `county`, `eircode`, `latitude`, `longitude`

**Update:** `latitude`, `longitude`, `geog`, `needs_geocoding`

**Validation:** Check `geocode_quality_issue` after updates

---

## Common Queries

### Export recent properties (last 3 months)
```sql
SELECT
    id, sale_date, address, address_normalized, county,
    eircode, routing_key, price, not_full_market_price,
    vat_exclusive, description, size_description,
    latitude, longitude, needs_geocoding, geocode_quality_issue,
    bedrooms, property_type
FROM properties
WHERE sale_date >= CURRENT_DATE - INTERVAL '3 months'
ORDER BY sale_date DESC;
```

### Properties needing geocoding (high priority)
```sql
SELECT * FROM properties_needing_geocoding LIMIT 1000;
```

### Properties at centroid coordinates (for cleanup)
```sql
WITH centroids AS (
    SELECT latitude, longitude
    FROM properties
    WHERE latitude IS NOT NULL
    GROUP BY latitude, longitude
    HAVING COUNT(DISTINCT address) >= 100
)
SELECT p.*
FROM properties p
JOIN centroids c ON ABS(p.latitude - c.latitude) < 0.000001
                 AND ABS(p.longitude - c.longitude) < 0.000001
WHERE p.sale_date >= '2020-01-01'
ORDER BY p.price DESC;
```

### Geocoding coverage by year
```sql
SELECT
    EXTRACT(YEAR FROM sale_date) as year,
    COUNT(*) as total,
    COUNT(latitude) as geocoded,
    ROUND(100.0 * COUNT(latitude) / COUNT(*), 1) as pct_geocoded,
    COUNT(eircode) as with_eircode,
    ROUND(100.0 * COUNT(eircode) / COUNT(*), 1) as pct_eircode
FROM properties
GROUP BY year
ORDER BY year DESC;
```

### Routing key stats
```sql
SELECT * FROM routing_key_stats
ORDER BY property_count DESC
LIMIT 20;
```

---

## Notes

- **PostGIS required:** Database must have PostGIS extension enabled for geography/geometry operations
- **No geocode_quality or geocode_source columns:** These exist in `search_log` table but NOT in `properties` table
- **Routing keys:** Auto-generated from Eircode, no manual updates needed
- **Materialized views:** Refresh `routing_key_stats` after bulk imports
- **Performance:** Geography column `geog` enables fast radius queries via GIST index
- **Validation:** Properties >5km from routing key centroid flagged as `geocode_quality_issue = TRUE`
