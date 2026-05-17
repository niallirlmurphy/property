-- Migration: Add search_log table for analytics
-- Run this against an existing database to add search query logging

-- Search query analytics log
CREATE TABLE IF NOT EXISTS search_log (
    id               BIGSERIAL PRIMARY KEY,
    ts               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    query            TEXT NOT NULL,
    resolved_lat     DOUBLE PRECISION,
    resolved_lon     DOUBLE PRECISION,
    radius_km        DOUBLE PRECISION NOT NULL,
    result_count     INTEGER NOT NULL,
    elapsed_ms       INTEGER NOT NULL,
    county_filter    TEXT,
    min_price        INTEGER,
    max_price        INTEGER,
    min_year         INTEGER,
    max_year         INTEGER,
    geocode_source   TEXT,  -- 'db_exact' | 'nominatim' | 'db_tokens' | 'mapbox' | 'db_fuzzy' | 'cache'
    user_agent       TEXT,
    ip_address       INET
);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS search_log_ts_idx ON search_log (ts DESC);
CREATE INDEX IF NOT EXISTS search_log_query_idx ON search_log (query);
CREATE INDEX IF NOT EXISTS search_log_result_count_idx ON search_log (result_count) WHERE result_count = 0;

-- Verify table was created
SELECT COUNT(*) as search_log_rows FROM search_log;
