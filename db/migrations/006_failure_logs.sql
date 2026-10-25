-- Failed searches and valuations, so we can see what users ask for and don't get.
-- Successes are already logged (search_log, valuation_requests).
-- Check with: python3 scripts/failures_report.py [--days 7]

-- reason: no_location (resolve_location couldn't place the query; was geocode_misses),
--         no_results  (placed/normalized, but no sales matched),
--         error       (5xx)
CREATE TABLE IF NOT EXISTS search_failures (
    id        BIGSERIAL PRIMARY KEY,
    ts        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    endpoint  TEXT NOT NULL,
    query     TEXT,
    county    TEXT,
    reason    TEXT NOT NULL CHECK (reason IN ('no_location', 'no_results', 'error')),
    detail    TEXT
);
CREATE INDEX IF NOT EXISTS search_failures_ts_idx ON search_failures (ts DESC);

-- status_code: 400 can't geocode, 404 no comparables, 500 internal error
CREATE TABLE IF NOT EXISTS valuation_failures (
    id             BIGSERIAL PRIMARY KEY,
    ts             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    address        TEXT,
    eircode        TEXT,
    county         TEXT,
    property_type  TEXT,
    bedrooms       INT,
    status_code    INT NOT NULL,
    detail         TEXT
);
CREATE INDEX IF NOT EXISTS valuation_failures_ts_idx ON valuation_failures (ts DESC);

-- Carry over the old misses; geocode_misses is no longer written to.
INSERT INTO search_failures (ts, endpoint, query, county, reason)
SELECT ts, '/search', query, county, 'no_location' FROM geocode_misses
WHERE NOT EXISTS (SELECT 1 FROM search_failures WHERE reason = 'no_location');

-- Same lockdown as every other table (see scripts/enable_rls_security.py).
ALTER TABLE search_failures ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "backend_full_access_search_failures" ON search_failures;
CREATE POLICY "backend_full_access_search_failures" ON search_failures
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
REVOKE ALL ON search_failures FROM anon;
REVOKE ALL ON SEQUENCE search_failures_id_seq FROM anon;

ALTER TABLE valuation_failures ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "backend_full_access_valuation_failures" ON valuation_failures;
CREATE POLICY "backend_full_access_valuation_failures" ON valuation_failures
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
REVOKE ALL ON valuation_failures FROM anon;
REVOKE ALL ON SEQUENCE valuation_failures_id_seq FROM anon;

-- Keep 12 months of query logs (search_log holds IP addresses and user agents).
-- Sundays 04:00 UTC.
CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA pg_catalog;
SELECT cron.schedule('query-log-retention', '0 4 * * 0', $$
    DELETE FROM search_log         WHERE ts < NOW() - INTERVAL '12 months';
    DELETE FROM search_failures    WHERE ts < NOW() - INTERVAL '12 months';
    DELETE FROM valuation_failures WHERE ts < NOW() - INTERVAL '12 months';
    DELETE FROM geocode_misses     WHERE ts < NOW() - INTERVAL '12 months';
$$);
