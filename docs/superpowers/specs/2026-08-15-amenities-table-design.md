# Amenities Table — Design

**Date:** 2026-08-15
**Scope:** Database table + import script only (no API/UI — those are follow-up specs).

## Purpose

Store non-property points of interest useful for valuing properties and
providing context. Initial data: Dublin key transport infrastructure (122 rows)
and key educational institutions/schools (45 rows). Designed to absorb future
POI categories without schema churn.

## Source data

Two Excel files (single sheet each), copied into `data/amenities/`:

| Field | Transport (122) | Schools (45) |
|-------|-----------------|--------------|
| Name | Infrastructure Name | School Name |
| Type | Category | Level + Category |
| Coords | Latitude / Longitude | Latitude / Longitude |
| Text | Description | Description |

- Transport categories: Luas Green (36) / Red (32), DART (25), Commuter train (21), plus Airport, Bus, Ferry, DART Interchange.
- School levels: Secondary (26), Primary (10), Tertiary (7), Secondary & Primary (2). Category encodes ethos+gender (e.g. "Catholic (Boys)", "Educate Together").
- Data quality: no duplicate names, all coords within Dublin, no nulls.
- One ingest artifact: transport row for **Luas Dawson** had a comma-containing
  description spilled across trailing `Unnamed` columns — reconciled on import
  by rejoining into a single string.

## Structure decision

**Unified table (`amenities`) with typed columns + JSONB `attributes`.** The two
datasets are nearly identical in shape, so one table with a shared spatial index
and a single proximity-query path fits best. `attributes JSONB` future-proofs
type-specific fields without migrations. Matches existing conventions
(`BIGSERIAL` PK, `GEOGRAPHY(Point,4326)` `geog` + GIST index, `DOUBLE PRECISION`
coords, `TIMESTAMPTZ`).

### Schema (`db/amenities_schema.sql`)

```sql
CREATE TABLE amenities (
    id            BIGSERIAL PRIMARY KEY,
    amenity_type  TEXT NOT NULL,        -- 'transport' | 'school'
    name          TEXT NOT NULL,
    category      TEXT,                 -- 'DART Station', 'Catholic (Boys)'
    level         TEXT,                 -- schools: 'Primary'|'Secondary'|'Tertiary'
    description   TEXT,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    geog          GEOGRAPHY(Point, 4326),
    attributes    JSONB NOT NULL DEFAULT '{}'::jsonb,
    source        TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (amenity_type, name)
);
-- GIST index on geog; btree index on amenity_type.
```

## Import (`scripts/import_amenities.py`)

- Reads both `.xlsx` (configurable paths, `data/amenities/` defaults).
- Maps each file to the shared shape; transport reconciles the row-98 spill.
- Validates coords against Ireland bounds (51.4–55.5°N, −10.7–−5.4°W); skips
  rows missing a name or with out-of-bounds coords.
- Sets `geog = SRID=4326;POINT(lon lat)`.
- **Idempotent upsert** on `(amenity_type, name)` — re-runnable, bumps `updated_at`.
- `--dry-run` (parse/validate only), `--skip-schema`, `--transport`, `--schools`.

## Security

`scripts/enable_rls_security.py` is table-agnostic and covers every public table.
Run after creating `amenities`: RLS enabled, `backend_full_access_amenities`
policy (FOR ALL TO authenticated), anon revoked.

## Verification (run 2026-08-15)

- Import: 167/167 valid (122 transport, 45 school), 0 skipped.
- 0 rows with NULL geog.
- Proximity query (within 1km of Trinity College) returns Trinity at 0m then
  nearby Luas/DART/rail stations in ascending distance order — correct.
- RLS enabled on `amenities`; anon SELECT → false; backend read intact.
