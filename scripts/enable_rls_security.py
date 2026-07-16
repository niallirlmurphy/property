#!/usr/bin/env python3
"""
Enable Row-Level Security (RLS) on ALL public Supabase tables.

DESIGN RULE: No Direct Database Access
======================================
Anonymous users should NEVER have direct access to the database.
Our architecture is: Frontend → Railway API → Supabase

- Frontend calls Railway backend API (authenticated)
- Backend uses DATABASE_URL with postgres/authenticated role
- Anonymous (anon) role has ZERO permissions
- This prevents direct Supabase REST API access
- PPR data remains publicly accessible via our API endpoints

Security Configuration:
- RLS enabled on EVERY public table (not just `properties`)
- Only 'authenticated' role has access, via a per-table FOR ALL policy
- 'anon' role has ALL privileges revoked on every table AND view

WHY THIS IS TABLE-AGNOSTIC
==========================
Supabase's rls_disabled_in_public scanner fires on ANY public table without
RLS. Previously this script only touched `properties`, so every new feature
table (valuation_*, search_log, mapbox_usage, ...) re-triggered the alert.
This version iterates over all base tables so new tables are covered too.
"""

import asyncio
import asyncpg
import os
import sys

DATABASE_URL = os.environ.get("DATABASE_URL")


async def get_public_tables(conn):
    """Return all base/partitioned tables in the public schema."""
    rows = await conn.fetch("""
        SELECT c.relname AS name
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p')          -- ordinary + partitioned tables
          AND c.relname NOT LIKE 'pg_%'
          AND c.relname NOT LIKE 'sql_%'
        ORDER BY c.relname
    """)
    return [r["name"] for r in rows]


async def get_anon_granted_relations(conn):
    """Return all public relations (tables AND views) where anon has any grant."""
    rows = await conn.fetch("""
        SELECT DISTINCT table_name
        FROM information_schema.role_table_grants
        WHERE grantee = 'anon' AND table_schema = 'public'
        ORDER BY table_name
    """)
    return [r["table_name"] for r in rows]


async def enable_rls_security():
    """Enable RLS and create authenticated-only policies on all public tables."""

    print("=" * 66)
    print("  ENABLING ROW-LEVEL SECURITY ON ALL PUBLIC TABLES")
    print("=" * 66)
    print()

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set")
        sys.exit(1)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        tables = await get_public_tables(conn)
        print(f"Found {len(tables)} public table(s): {', '.join(tables)}\n")

        # 1. Enable RLS + authenticated-only policy on every table.
        for table in tables:
            qname = f'"{table}"'

            await conn.execute(f"ALTER TABLE {qname} ENABLE ROW LEVEL SECURITY;")

            policy = f"backend_full_access_{table}"
            await conn.execute(f'DROP POLICY IF EXISTS "{policy}" ON {qname};')
            # Also drop any legacy public/anon read policies.
            await conn.execute(
                f'DROP POLICY IF EXISTS "Allow public read access" ON {qname};'
            )
            await conn.execute(
                f'DROP POLICY IF EXISTS "Enable read access for all users" ON {qname};'
            )
            await conn.execute(f"""
                CREATE POLICY "{policy}"
                ON {qname}
                FOR ALL
                TO authenticated
                USING (true)
                WITH CHECK (true);
            """)
            print(f"  ✅ RLS + authenticated policy: {table}")

        # 2. Revoke ALL anon privileges on every relation anon can touch
        #    (covers tables AND views - Supabase flags anon-accessible views too).
        print("\nRevoking anonymous access...")
        anon_relations = await get_anon_granted_relations(conn)
        for rel in anon_relations:
            await conn.execute(f'REVOKE ALL ON "{rel}" FROM anon;')
            print(f"  ✅ Revoked anon access: {rel}")
        # Belt-and-braces: revoke default schema-wide too.
        await conn.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;")
        await conn.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;")

        # 3. Verify
        print("\nVerifying configuration...")
        still_off = await conn.fetch("""
            SELECT c.relname AS name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind IN ('r', 'p')
              AND c.relrowsecurity = false
              AND c.relname NOT LIKE 'pg_%'
              AND c.relname NOT LIKE 'sql_%'
        """)
        remaining_anon = await get_anon_granted_relations(conn)

        if still_off:
            print(f"  ❌ RLS still disabled on: {', '.join(r['name'] for r in still_off)}")
            sys.exit(1)
        print("  ✅ RLS enabled on all public tables")

        if remaining_anon:
            print(f"  ❌ anon still has grants on: {', '.join(remaining_anon)}")
            sys.exit(1)
        print("  ✅ anon role has zero table privileges")

        # Backend still works?
        count = await conn.fetchval("SELECT COUNT(*) FROM properties")
        print(f"  ✅ Backend can read data: {count:,} properties")

        print("\n" + "=" * 66)
        print("SECURITY CONFIGURATION COMPLETE")
        print("=" * 66)
        print("Architecture: Frontend → Railway API → Supabase")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(enable_rls_security())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
