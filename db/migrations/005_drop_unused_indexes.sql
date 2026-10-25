-- Indexes on properties with no scans since the 2026-10-18 restart and no query
-- that could use them (checked 2026-10-25). ~95 MB that every insert/update had
-- to maintain and that competed for the 224 MB of shared_buffers.
--   idx_properties_address_normalized: equality is served by
--     idx_properties_address_normalized_prefix (text_pattern_ops covers =)
--   properties_eircode_idx: lookups use properties_eircode_norm_idx
--   idx_properties_routing_key_date: lookups use idx_properties_routing_key
--   properties_bedrooms_idx, properties_property_type_idx: never filtered on
-- Kept: properties_address_idx (scripts/duplicate_handler.py: WHERE address = %s)
-- CONCURRENTLY can't run in a transaction: run each statement on its own.
SET lock_timeout = '5s';
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_address_normalized;
DROP INDEX CONCURRENTLY IF EXISTS properties_eircode_idx;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_routing_key_date;
DROP INDEX CONCURRENTLY IF EXISTS properties_bedrooms_idx;
DROP INDEX CONCURRENTLY IF EXISTS properties_property_type_idx;
