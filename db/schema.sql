-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Main properties table
CREATE TABLE IF NOT EXISTS properties (
    id                    BIGSERIAL PRIMARY KEY,
    sale_date             DATE NOT NULL,
    address               TEXT NOT NULL,
    county                TEXT,
    eircode               TEXT,
    price                 NUMERIC(12, 2) NOT NULL,
    not_full_market_price BOOLEAN NOT NULL DEFAULT FALSE,
    vat_exclusive         BOOLEAN NOT NULL DEFAULT FALSE,
    description           TEXT,
    size_description      TEXT,
    latitude              DOUBLE PRECISION,
    longitude             DOUBLE PRECISION,
    geog                  GEOGRAPHY(Point, 4326)
);

-- Spatial index for radius queries
CREATE INDEX IF NOT EXISTS properties_geog_idx
    ON properties USING GIST (geog);

-- Form submissions (feedback + contact)
CREATE TABLE IF NOT EXISTS submissions (
    id            BIGSERIAL PRIMARY KEY,
    kind          TEXT NOT NULL,
    ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name          TEXT,
    email         TEXT,
    datasets      TEXT,
    comments      TEXT,
    message       TEXT,
    price_updates BOOLEAN
);

-- Supporting indexes for filtering
CREATE INDEX IF NOT EXISTS properties_county_idx  ON properties (county);
CREATE INDEX IF NOT EXISTS properties_sale_date_idx ON properties (sale_date);
CREATE INDEX IF NOT EXISTS properties_price_idx   ON properties (price);
CREATE INDEX IF NOT EXISTS properties_eircode_idx ON properties (eircode);

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

-- Email alerts for property notifications
CREATE TABLE IF NOT EXISTS email_alerts (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT NOT NULL,
    address       TEXT NOT NULL,
    radius_km     DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    county        TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_sent_at  TIMESTAMPTZ,
    unsubscribe_token TEXT UNIQUE DEFAULT gen_random_uuid()::TEXT
);

-- Index for active subscriptions
CREATE INDEX IF NOT EXISTS email_alerts_active_idx ON email_alerts (is_active, email);
CREATE INDEX IF NOT EXISTS email_alerts_email_idx ON email_alerts (email);
CREATE INDEX IF NOT EXISTS email_alerts_token_idx ON email_alerts (unsubscribe_token);

