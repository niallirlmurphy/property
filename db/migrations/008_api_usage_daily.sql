-- Requests per feature per day, flushed from memory every 10 minutes by
-- backend/usage.py. Aggregates only (no queries, IPs or user agents), so no
-- retention limit. endpoint is "METHOD /route/{template}".
CREATE TABLE IF NOT EXISTS api_usage_daily (
    day       DATE NOT NULL,
    endpoint  TEXT NOT NULL,
    status    INT  NOT NULL,
    requests  INT  NOT NULL,
    total_ms  BIGINT NOT NULL,
    PRIMARY KEY (day, endpoint, status)
);

-- Same lockdown as every other table (see scripts/enable_rls_security.py).
ALTER TABLE api_usage_daily ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "backend_full_access_api_usage_daily" ON api_usage_daily;
CREATE POLICY "backend_full_access_api_usage_daily" ON api_usage_daily
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
REVOKE ALL ON api_usage_daily FROM anon;
