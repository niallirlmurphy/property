-- Searches that resolve_location could not place (it no longer calls Mapbox).
-- Check periodically with: python3 scripts/geocode_misses_report.py
CREATE TABLE IF NOT EXISTS geocode_misses (
    id      BIGSERIAL PRIMARY KEY,
    ts      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    query   TEXT NOT NULL,
    county  TEXT
);

CREATE INDEX IF NOT EXISTS geocode_misses_ts_idx ON geocode_misses (ts DESC);

-- Same lockdown as every other table (see scripts/enable_rls_security.py).
ALTER TABLE geocode_misses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "backend_full_access_geocode_misses" ON geocode_misses;
CREATE POLICY "backend_full_access_geocode_misses" ON geocode_misses
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
REVOKE ALL ON geocode_misses FROM anon;
REVOKE ALL ON SEQUENCE geocode_misses_id_seq FROM anon;
