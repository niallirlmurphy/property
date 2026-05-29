-- Add flag for properties needing geocoding
-- Used by PPR sync when importing properties without coordinates

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS needs_geocoding BOOLEAN DEFAULT FALSE;

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_properties_needs_geocoding
ON properties(needs_geocoding)
WHERE needs_geocoding = TRUE;

-- Mark existing properties without coordinates as needing geocoding
-- (only recent sales from 2024+, prioritize newer data)
UPDATE properties
SET needs_geocoding = TRUE
WHERE latitude IS NULL
  AND longitude IS NULL
  AND sale_date >= '2024-01-01';

-- Create view for properties needing geocoding (prioritized)
CREATE OR REPLACE VIEW properties_needing_geocoding AS
SELECT
    id,
    sale_date,
    address,
    county,
    eircode,
    routing_key,
    price,
    description,
    -- Priority scoring
    CASE
        WHEN price > 500000 THEN 1
        WHEN price > 300000 THEN 2
        ELSE 3
    END as priority_tier
FROM properties
WHERE needs_geocoding = TRUE
ORDER BY
    priority_tier,
    sale_date DESC,
    price DESC;

-- Add comment
COMMENT ON COLUMN properties.needs_geocoding IS
'Flag indicating property needs geocoding. Set by PPR sync when importing without coordinates.';
