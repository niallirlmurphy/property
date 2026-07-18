-- Add provenance/confidence tracking for property_type.
-- Run with: psql $DATABASE_URL -f db/add_property_type_source.sql
--
-- Rationale: property_type is populated from several sources of differing
-- reliability. Web enrichment (reads actual listings) is ~90% accurate;
-- the apartment address rule (APT/APARTMENT/FLAT in the address) is ~99%;
-- a house guess from a bare place-name address is only ~81%. Tracking the
-- source lets low-confidence guesses be overwritten by better data later
-- while high-confidence values are protected.

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS property_type_source TEXT;

COMMENT ON COLUMN properties.property_type_source IS
  'Provenance of property_type: '
  '''web_enrichment'' (scraped from listings, high confidence) | '
  '''address_apartment'' (APT/APARTMENT/FLAT token in address, high confidence) | '
  '''address_house_guess'' (bare place-name heuristic, ~81% confidence, overwritable) | '
  'NULL (legacy/unknown, treated as established)';

-- Partial index: the enrichment scraper re-queries low-confidence guesses,
-- so make that lookup cheap without bloating the index for every row.
CREATE INDEX IF NOT EXISTS properties_property_type_source_guess_idx
  ON properties (property_type_source)
  WHERE property_type_source = 'address_house_guess';

-- One-time backfill: tag existing apartment rows that were derived from the
-- address rule so their provenance is explicit (high confidence, not re-scraped).
UPDATE properties
SET property_type_source = 'address_apartment'
WHERE property_type = 'apartment'
  AND property_type_source IS NULL
  AND address ~* '\m(APT|APTS|APARTMENT|APARTMENTS|FLAT)\M';

-- Report
SELECT property_type_source, COUNT(*)
FROM properties
WHERE property_type IS NOT NULL
GROUP BY property_type_source
ORDER BY COUNT(*) DESC;
