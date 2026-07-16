-- Disk I/O remediation migration (2026-07-17)
--
-- Root cause: `properties` was accumulating full sequential scans (6.3B rows
-- read across ~15k seq scans) driven by pipeline/enrichment queries that
-- filter on UNINDEXED columns. This burns the Supabase Disk IO budget.
--
-- Findings from pg_stat_statements + pg_stat_user_tables:
--   1. Enrichment (scripts/enrich_batch6_2026.py) and the valuation crowdsource
--      updater (backend/valuation/api.py) filter on the RAW `address` column,
--      which had ZERO indexes -> full 204 MB seq scan per lookup.
--   2. Geocoding scripts COUNT(*) WHERE needs_geocoding repeatedly -> seq scan.
--   3. A historical COUNT(*) ... geom IS NULL query was the biggest single I/O
--      consumer, but the `geom` column has since been DROPPED; those stats are
--      leftover history and the query no longer runs. No index needed.
--
-- All indexes use CREATE INDEX CONCURRENTLY so they do NOT lock the table.
-- NOTE: CONCURRENTLY cannot run inside a transaction block. Run this file
-- statement-by-statement (psql runs each separately by default; do NOT wrap
-- in BEGIN/COMMIT).

-- 1. Index the raw `address` column used by enrichment + valuation updates.
--    Partial: enrichment only touches rows missing bedrooms/property_type,
--    but a plain btree on address serves all raw-address equality lookups.
CREATE INDEX CONCURRENTLY IF NOT EXISTS properties_address_idx
    ON properties (address);

-- 2. Partial index for the geocoding backlog counts/scans.
--    Only ~unfilled rows are indexed, so the index stays tiny and the
--    "how many still need geocoding" checks become an index-only count.
CREATE INDEX CONCURRENTLY IF NOT EXISTS properties_needs_geocoding_idx
    ON properties (needs_geocoding)
    WHERE needs_geocoding = TRUE;

-- 3. After indexes exist, refresh planner stats (last_analyze was NULL).
--    Run separately (ANALYZE is safe, brief, non-locking for reads).
ANALYZE properties;
