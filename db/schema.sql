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

-- Persistent price-outlier flag. TRUE for records outside the trend price band
-- (NULL, < €10k, or > €20M) — nominal transfers and multi-unit/portfolio sales
-- filed at a shared price. Kept in the DB (genuine PPR records) but excluded from
-- landing-page lists, aggregates, and valuations. STORED generated column so it
-- stays in sync automatically on insert/update. Idempotent for existing databases.
ALTER TABLE properties
    ADD COLUMN IF NOT EXISTS stats_excluded BOOLEAN
    GENERATED ALWAYS AS (price IS NULL OR price < 10000 OR price > 20000000) STORED;

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

-- Full-text index backing the valuation geocoder's fuzzy address match
-- (backend/valuation/geocoder.py uses plainto_tsquery, NOT LIKE/ILIKE, per the
-- project's query rules). Without this the tsvector match seq-scans ~784k rows.
CREATE INDEX IF NOT EXISTS idx_properties_address_fts
    ON properties
    USING gin (to_tsvector('simple', COALESCE(address_normalized, address)));

-- Prefix index for exact-address lookups (starts_with(address_normalized, $1)).
-- The plain btree uses the en_US collation, which can't serve a prefix match,
-- so without this each valuation miss seq-scanned the table (~10s).
CREATE INDEX IF NOT EXISTS idx_properties_address_normalized_prefix
    ON properties (address_normalized text_pattern_ops);

-- Hand-checked coordinates for named developments (scripts/development_pins.py).
-- Every sale whose address matches match_query (to_tsquery('simple', ...) over
-- address_normalized) is placed on the pin before any Mapbox call, and never flagged
-- by flag_bad_geocodes.py. RLS: run scripts/enable_rls_security.py after creating.
CREATE TABLE IF NOT EXISTS development_pins (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    county       TEXT NOT NULL,
    match_query  TEXT NOT NULL,
    latitude     DOUBLE PRECISION NOT NULL,
    longitude    DOUBLE PRECISION NOT NULL,
    source       TEXT NOT NULL DEFAULT 'manual',
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (county, match_query)
);
-- Optional: rows already visible within this many metres of the pin keep their own
-- geocode (spread-out estates); NULL puts every matching row on the pin.
ALTER TABLE development_pins ADD COLUMN IF NOT EXISTS keep_within_m DOUBLE PRECISION;

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

