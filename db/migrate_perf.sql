-- Performance migration
-- Run once against the Supabase/Postgres DB.
--
-- 1. Add a stored geography column so ST_DWithin/ST_Distance
--    avoid a per-row ::geography cast (the most expensive part of radius search).
-- 2. Add a functional index on normalised eircode for fast LIKE prefix matching.
-- 3. Add a composite index for county + sale_date (trends queries).

-- Step 1: geography column (geom column removed; geog is populated directly at import)
ALTER TABLE properties
    ADD COLUMN IF NOT EXISTS geog GEOGRAPHY(Point, 4326);

UPDATE properties
    SET geog = ST_MakePoint(longitude, latitude)::geography
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND geog IS NULL;

CREATE INDEX IF NOT EXISTS properties_geog_idx
    ON properties USING GIST (geog);

-- Step 2: functional eircode index (supports LIKE 'D04%' prefix scans)
CREATE INDEX IF NOT EXISTS properties_eircode_norm_idx
    ON properties (REPLACE(UPPER(eircode), ' ', ''))
    WHERE eircode IS NOT NULL;

-- Step 3: composite index for county trends
CREATE INDEX IF NOT EXISTS properties_county_date_idx
    ON properties (LOWER(county), sale_date)
    WHERE not_full_market_price = FALSE;
