-- Add flag for properties with geocoding quality issues
-- These properties should be prioritized for re-geocoding from trusted sources

-- Add column to track geocoding quality issues
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS geocode_quality_issue BOOLEAN DEFAULT FALSE;

-- Add index for efficient querying of flagged properties
CREATE INDEX IF NOT EXISTS idx_properties_geocode_quality_issue
ON properties(geocode_quality_issue)
WHERE geocode_quality_issue = TRUE;

-- Create view for properties needing re-geocoding priority
CREATE OR REPLACE VIEW properties_needing_regeocode AS
SELECT
    id,
    address,
    county,
    eircode,
    routing_key,
    latitude,
    longitude,
    sale_date,
    price,
    -- Calculate distance from routing key centroid for debugging
    CASE
        WHEN routing_key IS NOT NULL THEN (
            SELECT ST_Distance(
                ST_MakePoint(longitude, latitude)::geography,
                ST_MakePoint(AVG(p2.longitude), AVG(p2.latitude))::geography
            ) / 1000.0  -- Convert to km
            FROM properties p2
            WHERE p2.routing_key = properties.routing_key
              AND p2.latitude IS NOT NULL
        )
        ELSE NULL
    END as distance_from_centroid_km
FROM properties
WHERE geocode_quality_issue = TRUE
ORDER BY
    CASE WHEN price > 500000 THEN 1 ELSE 2 END,  -- High value first
    sale_date DESC,  -- Recent sales first
    CASE WHEN routing_key IS NOT NULL THEN 1 ELSE 2 END;  -- With routing key first

COMMENT ON COLUMN properties.geocode_quality_issue IS
    'TRUE if geocoding validation detected quality issues. ' ||
    'Flagged properties should be prioritized for re-geocoding from trusted sources ' ||
    '(Mapbox, Autoaddress reverse, Salesforce Maps, etc.)';

COMMENT ON VIEW properties_needing_regeocode IS
    'Properties with geocoding quality issues, prioritized for re-geocoding. ' ||
    'Order: high-value properties, recent sales, properties with routing keys.';
