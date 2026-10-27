#!/usr/bin/env python3
"""
Automated security monitoring script.
Runs proactive checks and alerts if security configuration drifts.

Usage:
  python3 scripts/security_monitor.py              # Run checks and report
  python3 scripts/security_monitor.py --fix        # Auto-fix issues found
  python3 scripts/security_monitor.py --notify     # Send notification on issues

Set up as a daily cron job or Railway scheduled task to catch security drift.
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple

DATABASE_URL = os.environ.get("DATABASE_URL")
NO_PUBLIC_ACCESS_SQL = os.path.join(os.path.dirname(__file__), "..", "db", "migrations",
                                    "009_no_public_access.sql")

_PUBLIC_ROLES = "(0, 'anon'::regrole::oid, 'authenticated'::regrole::oid)"
# Every grant to PUBLIC (grantee 0), anon or authenticated in schema public: tables,
# views, materialized views, sequences, functions, and the schema itself.
PUBLIC_GRANTS_SQL = f"""
    SELECT obj AS object,
           CASE a.grantee WHEN 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END AS grantee,
           string_agg(a.privilege_type, ', ' ORDER BY a.privilege_type) AS privs
    FROM (
        SELECT c.relname::text AS obj, c.relacl AS acl
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        UNION ALL
        SELECT p.oid::regprocedure::text,
               COALESCE(p.proacl, acldefault('f', p.proowner))
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND pg_get_userbyid(p.proowner) = 'postgres'
        UNION ALL
        SELECT 'schema public', nspacl FROM pg_namespace WHERE nspname = 'public'
    ) o
    CROSS JOIN LATERAL aclexplode(o.acl) a
    WHERE a.grantee IN {_PUBLIC_ROLES}
    GROUP BY 1, 2
    ORDER BY 1, 2
"""

class SecurityIssue:
    def __init__(self, severity: str, title: str, description: str, fix_available: bool = False):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.title = title
        self.description = description
        self.fix_available = fix_available

class SecurityMonitor:
    def __init__(self, conn):
        self.conn = conn
        self.issues: List[SecurityIssue] = []

    async def check_rls_enabled(self) -> bool:
        """Check that RLS is enabled on EVERY public table, not just properties.

        Supabase's rls_disabled_in_public scanner fires on ANY unprotected
        public table, so checking only `properties` misses the tables that
        actually trigger the recurring security-alert emails.
        """
        unprotected = await self.conn.fetch("""
            SELECT c.relname AS name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind IN ('r', 'p')
              AND c.relrowsecurity = false
              AND c.relname NOT LIKE 'pg_%'
              AND c.relname NOT LIKE 'sql_%'
            ORDER BY c.relname
        """)

        if unprotected:
            names = ", ".join(r["name"] for r in unprotected)
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="RLS not enabled on public tables",
                description=f"Row-Level Security is disabled on: {names}",
                fix_available=True
            ))
            return False
        return True

    async def check_authenticated_policy(self) -> bool:
        """Check if authenticated-only policy exists."""
        policies = await self.conn.fetch("""
            SELECT policyname, cmd, roles::text[]
            FROM pg_policies
            WHERE tablename = 'properties'
            AND 'authenticated' = ANY(roles)
        """)

        if not policies:
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="No authenticated policy found",
                description="Backend API may not be able to access database",
                fix_available=True
            ))
            return False
        return True

    async def check_anon_access_revoked(self) -> bool:
        """Check that PUBLIC, anon and authenticated have ZERO access to public.

        Reads the catalog ACLs, not information_schema, which leaves out
        materialized views (county_monthly_price_indices was PUBLIC-readable
        until 2026-10-27) and functions. authenticated counts as public: anyone
        can sign up through Supabase Auth.
        """
        grants = await self.conn.fetch(PUBLIC_GRANTS_SQL)
        if grants:
            detail = "; ".join(f"{g['object']} -> {g['grantee']}: {g['privs']}" for g in grants)
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="Public roles have database access",
                description=f"PUBLIC/anon/authenticated grants: {detail}",
                fix_available=True
            ))
            return False
        return True

    async def check_public_policies(self) -> bool:
        """Check for unintended public/anon access policies on ANY public table."""
        public_policies = await self.conn.fetch("""
            SELECT tablename, policyname
            FROM pg_policies
            WHERE schemaname = 'public'
            AND ('public' = ANY(roles) OR 'anon' = ANY(roles))
            ORDER BY tablename, policyname
        """)

        if public_policies:
            detail = ", ".join(f"{p['tablename']}.{p['policyname']}" for p in public_policies)
            self.issues.append(SecurityIssue(
                severity="HIGH",
                title="Public/anon policies detected",
                description=f"Found policies granting public access: {detail}",
                fix_available=True
            ))
            return False
        return True

    async def check_backend_access(self) -> bool:
        """Verify backend can still access the database."""
        try:
            count = await self.conn.fetchval("SELECT COUNT(*) FROM properties LIMIT 1")
            if count is None:
                self.issues.append(SecurityIssue(
                    severity="CRITICAL",
                    title="Backend cannot access database",
                    description="SELECT queries are failing - backend API will be broken",
                    fix_available=False
                ))
                return False
            return True
        except Exception as e:
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="Backend database access error",
                description=f"Query failed: {str(e)}",
                fix_available=False
            ))
            return False

    async def check_postgis_extension(self) -> bool:
        """Verify PostGIS extension is still enabled."""
        result = await self.conn.fetchrow("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'postgis'
        """)

        if not result:
            self.issues.append(SecurityIssue(
                severity="HIGH",
                title="PostGIS extension not found",
                description="Spatial queries will fail - critical for search functionality",
                fix_available=False
            ))
            return False
        return True

    async def run_all_checks(self) -> Tuple[bool, List[SecurityIssue]]:
        """Run all security checks and return status."""
        checks = [
            ("RLS Enabled", self.check_rls_enabled()),
            ("Authenticated Policy", self.check_authenticated_policy()),
            ("Anonymous Access Blocked", self.check_anon_access_revoked()),
            ("No Public Policies", self.check_public_policies()),
            ("Backend Access", self.check_backend_access()),
            ("PostGIS Extension", self.check_postgis_extension()),
        ]

        results = {}
        for name, check in checks:
            results[name] = await check

        all_passed = all(results.values())
        return all_passed, self.issues

async def auto_fix_issues(conn, issues: List[SecurityIssue]) -> int:
    """Attempt to automatically fix security issues across ALL public tables.

    Rather than patching individual tables (which is what allowed new tables to
    slip through and re-trigger alerts), we re-apply the canonical, table-agnostic
    RLS hardening: enable RLS + authenticated-only policy on every public table,
    and revoke every anon grant. This is idempotent and safe to run repeatedly.
    """
    fixable = [i for i in issues if i.fix_available]
    if not fixable:
        return 0

    try:
        # Enable RLS + authenticated-only policy on every public table.
        tables = await conn.fetch("""
            SELECT c.relname AS name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind IN ('r', 'p')
              AND c.relname NOT LIKE 'pg_%'
              AND c.relname NOT LIKE 'sql_%'
        """)
        for t in tables:
            qname = f'"{t["name"]}"'
            policy = f'backend_full_access_{t["name"]}'
            await conn.execute(f"ALTER TABLE {qname} ENABLE ROW LEVEL SECURITY;")
            await conn.execute(f'DROP POLICY IF EXISTS "{policy}" ON {qname};')
            await conn.execute('DROP POLICY IF EXISTS "Allow public read access" ON ' + qname + ';')
            await conn.execute('DROP POLICY IF EXISTS "Enable read access for all users" ON ' + qname + ';')
            await conn.execute(f"""
                CREATE POLICY "{policy}" ON {qname}
                FOR ALL TO authenticated USING (true) WITH CHECK (true);
            """)

        # Revoke every public grant (db/migrations/009_no_public_access.sql).
        with open(NO_PUBLIC_ACCESS_SQL) as fh:
            await conn.execute(fh.read())

        print(f"  ✅ Re-applied RLS hardening across {len(tables)} table(s)")
        return len(fixable)

    except Exception as e:
        print(f"  ❌ Failed to auto-fix: {e}")
        return 0

async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          SECURITY MONITORING - PROACTIVE CHECKS             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    auto_fix = "--fix" in sys.argv
    notify = "--notify" in sys.argv

    # The Supabase pooler occasionally drops SSL mid-connect. Retry a few times
    # so a transient network blip is not reported as a security failure.
    conn = None
    last_err = None
    for attempt in range(4):
        try:
            conn = await asyncpg.connect(DATABASE_URL, timeout=15.0)
            break
        except Exception as e:
            last_err = e
            print(f"  ⚠️  Connection attempt {attempt + 1} failed: {str(e)[:80]}")
            await asyncio.sleep(2)
    if conn is None:
        print(f"\n❌ Could not connect to database after retries: {last_err}")
        print("   This is a connectivity issue, not a security failure.")
        sys.exit(2)

    try:
        monitor = SecurityMonitor(conn)

        print("Running security checks...\n")
        all_passed, issues = await monitor.run_all_checks()

        if all_passed:
            print("=" * 70)
            print("✅ ALL SECURITY CHECKS PASSED")
            print("=" * 70)
            print("\n✅ RLS enabled on properties table")
            print("✅ Authenticated-only policy active")
            print("✅ Anonymous access blocked")
            print("✅ No public policies found")
            print("✅ Backend can access database")
            print("✅ PostGIS extension enabled")
            print("\n🔒 Security posture: STRONG")
            print("📧 No action needed - Supabase alerts should not trigger")
            sys.exit(0)

        # Issues found
        print("=" * 70)
        print("⚠️  SECURITY ISSUES DETECTED")
        print("=" * 70)
        print()

        # Group by severity
        critical = [i for i in issues if i.severity == "CRITICAL"]
        high = [i for i in issues if i.severity == "HIGH"]
        medium = [i for i in issues if i.severity == "MEDIUM"]
        low = [i for i in issues if i.severity == "LOW"]

        for severity, severity_issues in [
            ("CRITICAL", critical),
            ("HIGH", high),
            ("MEDIUM", medium),
            ("LOW", low)
        ]:
            if not severity_issues:
                continue

            print(f"\n🚨 {severity} Issues ({len(severity_issues)}):")
            print("-" * 70)
            for issue in severity_issues:
                print(f"\n  • {issue.title}")
                print(f"    {issue.description}")
                if issue.fix_available:
                    print(f"    [Auto-fix available]")

        # Auto-fix if requested
        if auto_fix:
            print("\n" + "=" * 70)
            print("Attempting to auto-fix issues...")
            print("=" * 70)
            fixed = await auto_fix_issues(conn, issues)

            if fixed > 0:
                print(f"\n✅ Fixed {fixed} issue(s)")
                print("\nRe-running checks to verify...")

                # Re-run checks
                monitor2 = SecurityMonitor(conn)
                all_passed2, issues2 = await monitor2.run_all_checks()

                if all_passed2:
                    print("\n✅ All issues resolved!")
                    sys.exit(0)
                else:
                    print(f"\n⚠️  {len(issues2)} issue(s) still remain")
                    sys.exit(1)
            else:
                print("\n⚠️  No issues could be auto-fixed")
                sys.exit(1)

        else:
            print("\n" + "=" * 70)
            print("ACTION REQUIRED")
            print("=" * 70)
            print("\nRun with --fix to automatically resolve issues:")
            print("  python3 scripts/security_monitor.py --fix")
            print("\nOr manually run:")
            print("  python3 scripts/enable_rls_security.py")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
