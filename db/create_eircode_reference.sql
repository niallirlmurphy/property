-- Create Eircode Reference Table
-- Built from PPR properties with validated coordinates
-- Provides centroid coordinates for all Eircodes and routing keys

CREATE TABLE IF NOT EXISTS eircode_reference (
    eircode TEXT PRIMARY KEY,
    latitude NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,
    property_count INTEGER NOT NULL,
    county TEXT,
    routing_key TEXT,
    std_lat NUMERIC,
    std_lon NUMERIC,
    source TEXT DEFAULT 'ppr',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eircode_ref_routing ON eircode_reference(routing_key);
CREATE INDEX IF NOT EXISTS idx_eircode_ref_county ON eircode_reference(county);
CREATE INDEX IF NOT EXISTS idx_eircode_ref_coords ON eircode_reference(latitude, longitude);

COMMENT ON TABLE eircode_reference IS 'Reference table mapping Eircodes to coordinates, built from PPR properties';
COMMENT ON COLUMN eircode_reference.eircode IS 'Full 7-character Eircode (e.g., D02XY45)';
COMMENT ON COLUMN eircode_reference.latitude IS 'Centroid latitude of all properties with this Eircode';
COMMENT ON COLUMN eircode_reference.longitude IS 'Centroid longitude of all properties with this Eircode';
COMMENT ON COLUMN eircode_reference.property_count IS 'Number of properties used to calculate centroid';
COMMENT ON COLUMN eircode_reference.std_lat IS 'Standard deviation of latitude (cluster tightness)';
COMMENT ON COLUMN eircode_reference.std_lon IS 'Standard deviation of longitude (cluster tightness)';
COMMENT ON COLUMN eircode_reference.source IS 'Data source: ppr (Property Price Register), geohive, autoaddress';

-- Populate from PPR properties with validated coordinates
INSERT INTO eircode_reference (
    eircode,
    latitude,
    longitude,
    property_count,
    county,
    routing_key,
    std_lat,
    std_lon,
    source
)
SELECT
    REPLACE(UPPER(eircode), ' ', '') as eircode,
    AVG(latitude) as latitude,
    AVG(longitude) as longitude,
    COUNT(*) as property_count,
    MODE() WITHIN GROUP (ORDER BY county) as county,  -- most common county
    LEFT(REPLACE(UPPER(eircode), ' ', ''), 3) as routing_key,
    STDDEV(latitude) as std_lat,
    STDDEV(longitude) as std_lon,
    'ppr' as source
FROM properties
WHERE eircode IS NOT NULL
  AND eircode != ''
  AND latitude IS NOT NULL
  AND longitude IS NOT NULL
  -- Only include properties with valid coordinates (within Ireland bounds)
  AND latitude BETWEEN 51.4 AND 55.5
  AND longitude BETWEEN -10.7 AND -5.4
GROUP BY REPLACE(UPPER(eircode), ' ', '')
HAVING COUNT(*) >= 1;  -- At least 1 property with this Eircode

-- Create summary view for routing keys
CREATE OR REPLACE VIEW eircode_routing_key_summary AS
SELECT
    routing_key,
    COUNT(*) as eircode_count,
    SUM(property_count) as total_properties,
    AVG(latitude) as centroid_lat,
    AVG(longitude) as centroid_lon,
    MODE() WITHIN GROUP (ORDER BY county) as primary_county
FROM eircode_reference
GROUP BY routing_key
ORDER BY routing_key;

COMMENT ON VIEW eircode_routing_key_summary IS 'Summary statistics for Eircode routing keys (3-char prefixes)';

-- Create function to get coordinates for any Eircode
CREATE OR REPLACE FUNCTION get_eircode_coordinates(input_eircode TEXT)
RETURNS TABLE(lat NUMERIC, lon NUMERIC, source TEXT, confidence TEXT) AS $$
DECLARE
    norm_eircode TEXT;
    routing_prefix TEXT;
BEGIN
    -- Normalize input
    norm_eircode := REPLACE(UPPER(input_eircode), ' ', '');
    routing_prefix := LEFT(norm_eircode, 3);

    -- Try exact match first
    RETURN QUERY
    SELECT
        latitude as lat,
        longitude as lon,
        eircode_reference.source,
        CASE
            WHEN std_lat < 0.001 AND std_lon < 0.001 THEN 'high'
            WHEN std_lat < 0.01 AND std_lon < 0.01 THEN 'medium'
            ELSE 'low'
        END as confidence
    FROM eircode_reference
    WHERE eircode = norm_eircode
    LIMIT 1;

    -- If no exact match and input looks like routing key, return routing key centroid
    IF NOT FOUND AND LENGTH(norm_eircode) <= 4 THEN
        RETURN QUERY
        SELECT
            centroid_lat as lat,
            centroid_lon as lon,
            'routing_key' as source,
            'medium' as confidence
        FROM eircode_routing_key_summary
        WHERE routing_key = routing_prefix
        LIMIT 1;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_eircode_coordinates IS 'Get coordinates for an Eircode with confidence level. Falls back to routing key if exact match not found.';
