-- Migration: Add BER rating column to properties table
-- Date: 2026-06-26
-- Purpose: Store crowdsourced BER ratings from valuation requests

-- Add BER rating column
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS ber_rating VARCHAR(2);

-- Add comment explaining the column
COMMENT ON COLUMN properties.ber_rating IS 'BER energy rating (A1-G), crowdsourced from valuation requests';

-- Create index for filtering by BER rating
CREATE INDEX IF NOT EXISTS idx_properties_ber_rating ON properties(ber_rating) WHERE ber_rating IS NOT NULL;

-- Check results
SELECT
    COUNT(*) as total_properties,
    COUNT(ber_rating) as with_ber,
    ROUND(100.0 * COUNT(ber_rating) / COUNT(*), 2) as ber_coverage_pct
FROM properties;
