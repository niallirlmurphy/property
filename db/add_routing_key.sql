-- Add routing key column and indexes for Eircode-based search optimization
-- Routing keys are the first 3 characters of Irish Eircodes (e.g., D02, H91, V94)
-- Each routing key represents a geographic area containing ~15,000 addresses

-- Step 1: Add generated column for routing key (extracted from eircode)
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS routing_key VARCHAR(3) GENERATED ALWAYS AS (
  CASE
    WHEN eircode IS NOT NULL AND eircode != ''
    THEN SUBSTRING(REPLACE(UPPER(eircode), ' ', ''), 1, 3)
    ELSE NULL
  END
) STORED;

-- Step 2: Create index for fast routing key lookups
CREATE INDEX IF NOT EXISTS idx_properties_routing_key
ON properties(routing_key)
WHERE routing_key IS NOT NULL;

-- Step 3: Create composite index for routing key + sale date (common query pattern)
CREATE INDEX IF NOT EXISTS idx_properties_routing_key_date
ON properties(routing_key, sale_date DESC)
WHERE routing_key IS NOT NULL;

-- Step 4: Create materialized view for routing key statistics and centroids
CREATE MATERIALIZED VIEW IF NOT EXISTS routing_key_stats AS
SELECT
  routing_key,
  MODE() WITHIN GROUP (ORDER BY county) as primary_county,
  COUNT(*) as property_count,
  ARRAY_AGG(DISTINCT county ORDER BY county) as counties,
  MIN(sale_date) as earliest_sale,
  MAX(sale_date) as latest_sale,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) FILTER (WHERE NOT not_full_market_price) as median_price,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latitude) as centroid_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY longitude) as centroid_lon,
  COUNT(*) FILTER (WHERE latitude IS NOT NULL) as geocoded_count,
  COUNT(*) FILTER (WHERE latitude IS NOT NULL)::FLOAT / COUNT(*)::FLOAT as geocoded_pct
FROM properties
WHERE routing_key IS NOT NULL
  AND routing_key ~ '^[A-Z][0-9][0-9W]$'  -- Valid Irish Eircode routing key format
GROUP BY routing_key;

-- Step 5: Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_routing_key_stats_pk
ON routing_key_stats(routing_key);

-- Step 6: Create index for sorting by property count
CREATE INDEX IF NOT EXISTS idx_routing_key_stats_count
ON routing_key_stats(property_count DESC);

-- Step 7: Refresh the materialized view to populate it
REFRESH MATERIALIZED VIEW routing_key_stats;

-- Step 8: Add comment explaining the routing key system
COMMENT ON COLUMN properties.routing_key IS
  'First 3 characters of Eircode representing geographic routing area. ' ||
  'Format: [Letter][Digit][Digit or W]. ' ||
  'Each routing key covers ~15,000 addresses in a contiguous geographic area. ' ||
  'Automatically extracted from eircode column.';

COMMENT ON MATERIALIZED VIEW routing_key_stats IS
  'Summary statistics and geographic centroids for each Eircode routing key area. ' ||
  'Refresh after bulk imports or periodically (weekly/monthly). ' ||
  'Used for routing key autocomplete, area search, and analytics.';
