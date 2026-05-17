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

