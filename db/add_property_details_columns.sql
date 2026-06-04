-- Add property details columns to properties table
-- Run with: psql $DATABASE_URL -f db/add_property_details_columns.sql

-- Add bedroom count column
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS bedrooms INTEGER;

-- Add property type column
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS property_type TEXT;

-- Add index for filtering by bedrooms
CREATE INDEX IF NOT EXISTS properties_bedrooms_idx ON properties (bedrooms);

-- Add index for filtering by property type
CREATE INDEX IF NOT EXISTS properties_property_type_idx ON properties (property_type);

-- Add comment documentation
COMMENT ON COLUMN properties.bedrooms IS 'Number of bedrooms (enriched from web search of property listings)';
COMMENT ON COLUMN properties.property_type IS 'Property type: house, apartment, terraced, detached, semi-detached, etc. (enriched from web search)';

-- Check current stats
SELECT
    COUNT(*) as total_properties,
    COUNT(bedrooms) as with_bedrooms,
    COUNT(property_type) as with_property_type,
    ROUND(100.0 * COUNT(bedrooms) / COUNT(*), 1) as pct_bedrooms,
    ROUND(100.0 * COUNT(property_type) / COUNT(*), 1) as pct_property_type
FROM properties;
