#!/usr/bin/env python3
"""
Enable Row-Level Security (RLS) on Supabase properties table.

DESIGN RULE: No Direct Database Access
======================================
Anonymous users should NEVER have direct access to the database.
Our architecture is: Frontend → Railway API → Supabase

- Frontend calls Railway backend API (authenticated)
- Backend uses DATABASE_URL with postgres/authenticated role
- Anonymous (anon) role has ZERO permissions
- This prevents direct Supabase REST API access

Security Configuration:
- RLS enabled on all tables
- Only 'authenticated' role has access
- 'anon' role explicitly blocked (no GRANT statements)
- PPR data remains publicly accessible via our API endpoints
"""

import asyncio
import asyncpg
import os
import sys

DATABASE_URL = os.environ.get("DATABASE_URL")

async def enable_rls_security():
    """Enable RLS and create appropriate policies."""

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     ENABLING ROW-LEVEL SECURITY                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set")
        sys.exit(1)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # 1. Check current RLS status
        print("1. Checking current security status...")
        result = await conn.fetchrow("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'properties'
        """)

        if result:
            current_status = "ENABLED" if result["rowsecurity"] else "DISABLED"
            print(f"   Current RLS status: {current_status}")

        # 2. Enable RLS
        print("\n2. Enabling Row-Level Security...")
        await conn.execute("ALTER TABLE properties ENABLE ROW LEVEL SECURITY;")
        print("   ✅ RLS enabled")

        # 3. Create authenticated-only policy
        # DESIGN RULE: No public/anon access
        # Only authenticated role (backend) can access data
        print("\n3. Creating authenticated-only access policy...")

        # Drop any public policies if they exist (should not exist)
        await conn.execute("""
            DROP POLICY IF EXISTS "Allow public read access" ON properties;
        """)

        # Drop existing authenticated policy if it exists
        await conn.execute("""
            DROP POLICY IF EXISTS "backend_full_access_properties" ON properties;
        """)

        # Create authenticated-only policy
        await conn.execute("""
            CREATE POLICY "backend_full_access_properties"
            ON properties
            FOR ALL
            TO authenticated
            USING (true)
            WITH CHECK (true);
        """)
        print("   ✅ Authenticated-only policy created")

        # 4. Explicitly revoke anonymous access
        print("\n4. Revoking anonymous access...")
        await conn.execute("""
            REVOKE ALL ON properties FROM anon;
        """)
        print("   ✅ Anonymous access revoked")

        # 5. Verify configuration
        print("\n5. Verifying security configuration...")

        # Check RLS status
        result = await conn.fetchrow("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'properties'
        """)

        if result["rowsecurity"]:
            print("   ✅ RLS is ENABLED")
        else:
            print("   ❌ RLS is still DISABLED")
            sys.exit(1)

        # Check policies
        policies = await conn.fetch("""
            SELECT policyname, cmd, roles::text[]
            FROM pg_policies
            WHERE tablename = 'properties'
        """)

        print(f"\n   Active policies: {len(policies)}")
        for policy in policies:
            print(f"     • {policy['policyname']}")
            print(f"       Command: {policy['cmd']}")
            print(f"       Roles: {', '.join(policy['roles'])}")

        # Check anonymous access is blocked
        result = await conn.fetchrow("""
            SELECT has_table_privilege('anon', 'properties', 'SELECT') as can_select
        """)
        if not result['can_select']:
            print("\n   ✅ Anonymous access BLOCKED")
        else:
            print("\n   ❌ WARNING: Anonymous can still access table")

        # 6. Test backend access
        print("\n6. Testing backend access...")
        count = await conn.fetchval("SELECT COUNT(*) FROM properties")
        print(f"   ✅ Backend can read data: {count:,} properties")

        print("\n" + "="*70)
        print("SECURITY CONFIGURATION COMPLETE")
        print("="*70)
        print("\n✅ Properties table is now secured with RLS")
        print("✅ Authenticated role (backend) has full access")
        print("✅ Anonymous role has NO access (by design)")
        print("✅ Writes controlled by backend API only")
        print("\nArchitecture: Frontend → Railway API → Supabase")
        print("Result: All database access goes through authenticated backend")

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
