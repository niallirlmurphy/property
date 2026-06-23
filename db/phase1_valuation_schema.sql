-- Property Valuation Phase 1 Database Schema
-- Created: 2026-06-23
-- Purpose: Support comparable-sales valuation algorithm

-- ============================================================================
-- 1. County Monthly Price Indices (Materialized View)
-- ============================================================================
-- Used for temporal price adjustments
-- Tracks median price movement by county and month since 2020

CREATE MATERIALIZED VIEW IF NOT EXISTS county_monthly_price_indices AS
WITH monthly_sales AS (
    SELECT
        county,
        DATE_TRUNC('month', sale_date) AS month,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
        COUNT(*) AS sale_count
    FROM properties
    WHERE
        not_full_market_price = FALSE
        AND sale_date >= '2020-01-01'
        AND price BETWEEN 50000 AND 5000000
        AND county IS NOT NULL
    GROUP BY county, month
    HAVING COUNT(*) >= 10  -- Minimum 10 sales for reliable median
)
SELECT
    county,
    month,
    median_price,
    sale_count,
    -- Calculate price index (normalized to first month = 1.0)
    median_price / FIRST_VALUE(median_price) OVER (
        PARTITION BY county
        ORDER BY month
    ) AS price_index
FROM monthly_sales;

-- Index for fast lookup during valuation requests
CREATE INDEX IF NOT EXISTS idx_price_indices_lookup
ON county_monthly_price_indices (county, month);

-- ============================================================================
-- 2. Valuation Requests Table
-- ============================================================================
-- Tracks all valuation requests for analytics and quality monitoring

CREATE TABLE IF NOT EXISTS valuation_requests (
    id SERIAL PRIMARY KEY,
    request_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,

    -- Input parameters
    address TEXT NOT NULL,
    eircode VARCHAR(8),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    property_type VARCHAR(50),
    bedrooms INTEGER,

    -- Valuation timestamp
    valuation_date TIMESTAMP DEFAULT NOW(),

    -- Results
    estimate INTEGER,
    confidence_level VARCHAR(20),  -- 'high', 'medium', 'low'
    n_comparables INTEGER,
    quality_score NUMERIC(3, 2),  -- 0.0 to 1.0

    -- Confidence interval
    estimate_lower INTEGER,
    estimate_upper INTEGER,

    -- Metadata
    algorithm_version VARCHAR(20) DEFAULT '1.0.0-mvp',
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_valuation_requests_created
ON valuation_requests (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_valuation_requests_county
ON valuation_requests (address)
WHERE address IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_valuation_requests_confidence
ON valuation_requests (confidence_level, created_at DESC);

-- ============================================================================
-- 3. Valuation Comparables Junction Table
-- ============================================================================
-- Links valuation requests to the comparable properties used
-- Enables analysis and debugging of valuation quality

CREATE TABLE IF NOT EXISTS valuation_comparables (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES valuation_requests(request_id) ON DELETE CASCADE,
    property_id INTEGER NOT NULL REFERENCES properties(id),

    -- Spatial relationship
    distance_m NUMERIC(10, 2) NOT NULL,

    -- Weighting
    weight NUMERIC(4, 3) NOT NULL,  -- 0.000 to 1.000

    -- Price adjustments
    original_price INTEGER NOT NULL,
    adjusted_price INTEGER NOT NULL,
    adjustment_factor NUMERIC(4, 3) NOT NULL,  -- ratio of adjusted/original

    -- Temporal info
    sale_date DATE NOT NULL,
    days_since_sale INTEGER NOT NULL,
    recency_score NUMERIC(4, 3),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for queries
CREATE INDEX IF NOT EXISTS idx_valuation_comparables_request
ON valuation_comparables (request_id);

CREATE INDEX IF NOT EXISTS idx_valuation_comparables_property
ON valuation_comparables (property_id);

-- ============================================================================
-- 4. Helper Functions
-- ============================================================================

-- Function to refresh price indices (call monthly via cron)
CREATE OR REPLACE FUNCTION refresh_price_indices()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY county_monthly_price_indices;
    RAISE NOTICE 'County monthly price indices refreshed at %', NOW();
END;
$$;

-- Function to get latest price index for a county
CREATE OR REPLACE FUNCTION get_county_price_index(
    p_county VARCHAR(50),
    p_target_date DATE
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    v_index NUMERIC;
BEGIN
    SELECT price_index INTO v_index
    FROM county_monthly_price_indices
    WHERE county = p_county
      AND month = DATE_TRUNC('month', p_target_date)
    ORDER BY month DESC
    LIMIT 1;

    -- Fallback to latest available if exact month not found
    IF v_index IS NULL THEN
        SELECT price_index INTO v_index
        FROM county_monthly_price_indices
        WHERE county = p_county
        ORDER BY month DESC
        LIMIT 1;
    END IF;

    RETURN COALESCE(v_index, 1.0);
END;
$$;

-- ============================================================================
-- 5. Initial Data Load
-- ============================================================================

-- Populate price indices materialized view
REFRESH MATERIALIZED VIEW county_monthly_price_indices;

-- ============================================================================
-- 6. Grant Permissions (if using RLS)
-- ============================================================================

-- Allow public SELECT on price indices (read-only reference data)
GRANT SELECT ON county_monthly_price_indices TO PUBLIC;

-- Valuation requests: allow authenticated users to INSERT and SELECT their own
-- (Adjust based on your auth setup)
GRANT SELECT, INSERT ON valuation_requests TO anon, authenticated;
GRANT SELECT, INSERT ON valuation_comparables TO anon, authenticated;

-- Allow sequence usage
GRANT USAGE ON SEQUENCE valuation_requests_id_seq TO anon, authenticated;
GRANT USAGE ON SEQUENCE valuation_comparables_id_seq TO anon, authenticated;

-- ============================================================================
-- 7. Verification Queries
-- ============================================================================

-- Verify price indices populated
DO $$
DECLARE
    v_count INTEGER;
    v_counties INTEGER;
BEGIN
    SELECT COUNT(*), COUNT(DISTINCT county) INTO v_count, v_counties
    FROM county_monthly_price_indices;

    RAISE NOTICE 'Price indices: % rows across % counties', v_count, v_counties;

    IF v_count = 0 THEN
        RAISE WARNING 'No price indices generated - check data availability';
    END IF;
END;
$$;

-- Show sample of price indices
SELECT
    county,
    COUNT(*) as months,
    MIN(month) as earliest,
    MAX(month) as latest,
    ROUND(AVG(price_index)::numeric, 3) as avg_index
FROM county_monthly_price_indices
GROUP BY county
ORDER BY county
LIMIT 10;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Run this script on Supabase/PostgreSQL with PostGIS enabled
-- 2. Requires existing 'properties' table with geog column and GIST index
-- 3. Price indices refresh monthly via cron (see backend/cron_jobs.py)
-- 4. All queries use existing spatial indexes (no performance impact)
-- 5. Tables support Phase 1 MVP; Phase 2 will add hedonic_coefficients table
