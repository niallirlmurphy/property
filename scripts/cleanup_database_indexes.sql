-- Database Index Cleanup Script
-- Purpose: Free up disk space by removing unused/redundant indexes
-- Expected savings: 115-123 MB
-- Safe to run: YES (these indexes are not being used by queries)
--
-- IMPORTANT: Create a backup before running if not already covered by automatic backups
--
-- Run with: psql $DATABASE_URL -f scripts/cleanup_database_indexes.sql

\timing on

-- Show current database size
SELECT
    'Before cleanup' as status,
    pg_size_pretty(pg_database_size(current_database())) as database_size,
    pg_size_pretty(pg_total_relation_size('properties')) as properties_total,
    pg_size_pretty(pg_relation_size('properties')) as properties_table,
    pg_size_pretty(pg_total_relation_size('properties') - pg_relation_size('properties')) as properties_indexes;

\echo ''
\echo '=== DROPPING UNUSED TRIGRAM INDEX (saves 107 MB) ==='
\echo 'This index is not being used by ILIKE queries (does sequential scan instead)'

DROP INDEX IF EXISTS properties_address_trgm_idx;

\echo ''
\echo '=== DROPPING REDUNDANT SINGLE-COLUMN COUNTY INDEX (saves 8 MB) ==='
\echo 'The composite index properties_county_date_idx covers county-only queries'

DROP INDEX IF EXISTS properties_county_idx;

\echo ''
\echo '=== OPTIONAL: Uncomment to drop eircode normalization index (saves 8 MB) ==='
\echo '-- DROP INDEX IF EXISTS properties_eircode_norm_idx;'
\echo ''

-- Vacuum to reclaim disk space
\echo '=== VACUUMING TO RECLAIM DISK SPACE ==='
\echo 'This may take several minutes...'

VACUUM FULL properties;

-- Show final database size
\echo ''
\echo '=== CLEANUP COMPLETE ==='

SELECT
    'After cleanup' as status,
    pg_size_pretty(pg_database_size(current_database())) as database_size,
    pg_size_pretty(pg_total_relation_size('properties')) as properties_total,
    pg_size_pretty(pg_relation_size('properties')) as properties_table,
    pg_size_pretty(pg_total_relation_size('properties') - pg_relation_size('properties')) as properties_indexes;

\echo ''
\echo 'Remaining indexes on properties table:'

SELECT
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
FROM pg_indexes
WHERE tablename = 'properties'
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;

\echo ''
\echo 'Next step: Run address normalization to populate remaining 483k addresses'
\echo '  python3 scripts/normalize_addresses.py'
