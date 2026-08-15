-- Amenities: non-property points of interest useful for valuing properties
-- and providing context (transport infrastructure, schools, and future
-- categories). Unified table keyed by amenity_type, with a JSONB attributes
-- column to absorb type-specific fields without future migrations.
--
-- RLS: not configured here. scripts/enable_rls_security.py is table-agnostic
-- and covers every public table (anon revoked, authenticated full access).
-- Run it after creating this table (see CLAUDE.md Security section).

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS amenities (
    id            BIGSERIAL PRIMARY KEY,
    amenity_type  TEXT NOT NULL,               -- 'transport' | 'school'
    name          TEXT NOT NULL,
    category      TEXT,                         -- e.g. 'DART Station', 'Catholic (Boys)'
    level         TEXT,                         -- schools only: 'Primary' | 'Secondary' | 'Tertiary'
    description   TEXT,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    geog          GEOGRAPHY(Point, 4326),
    attributes    JSONB NOT NULL DEFAULT '{}'::jsonb,
    source        TEXT,                         -- provenance (source filename)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (amenity_type, name)
);

-- Spatial index for radius/proximity queries (ST_DWithin on geog)
CREATE INDEX IF NOT EXISTS amenities_geog_idx ON amenities USING GIST (geog);

-- Filter by type (transport vs school)
CREATE INDEX IF NOT EXISTS amenities_type_idx ON amenities (amenity_type);
