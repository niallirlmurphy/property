-- No public access to the database, ever. Only the backend (postgres role, via
-- DATABASE_URL) reads or writes; PUBLIC, anon and authenticated (anyone with the
-- anon key, or anyone who signs up through Supabase Auth) get nothing.
--
-- Found 2026-10-27: county_monthly_price_indices readable by PUBLIC, and the
-- valuation tables granted to anon/authenticated, both from
-- db/phase1_valuation_schema.sql; our functions executable by PUBLIC (the default).
-- scripts/security_monitor.py checks for any of these grants coming back.

-- Everything in public: tables, views, materialized views, sequences, functions.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_eircode_coordinates, refresh_price_indices, get_county_price_index
    FROM PUBLIC, anon, authenticated;

-- Objects postgres creates later start with no public grants.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE ALL ON FUNCTIONS FROM PUBLIC, anon, authenticated;

-- The API roles can't see into public or extensions at all.
REVOKE ALL ON SCHEMA public FROM PUBLIC, anon, authenticated;
REVOKE ALL ON SCHEMA extensions FROM anon, authenticated;

-- pg_stat_statements holds every query's text.
REVOKE ALL ON extensions.pg_stat_statements, extensions.pg_stat_statements_info
    FROM PUBLIC, anon, authenticated;
