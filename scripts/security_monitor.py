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
        """Check if RLS is enabled on properties table."""
        result = await self.conn.fetchrow("""
            SELECT rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename = 'properties'
        """)

        if not result or not result['rowsecurity']:
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="RLS not enabled on properties table",
                description="Row-Level Security is disabled, allowing direct database access",
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
        """Check if anonymous role has no access."""
        result = await self.conn.fetchrow("""
            SELECT has_table_privilege('anon', 'properties', 'SELECT') as can_select,
                   has_table_privilege('anon', 'properties', 'INSERT') as can_insert,
                   has_table_privilege('anon', 'properties', 'UPDATE') as can_update,
                   has_table_privilege('anon', 'properties', 'DELETE') as can_delete
        """)

        has_any_access = any([
            result['can_select'],
            result['can_insert'],
            result['can_update'],
            result['can_delete']
        ])

        if has_any_access:
            self.issues.append(SecurityIssue(
                severity="CRITICAL",
                title="Anonymous role has database access",
                description="Anonymous users can access the database directly via PostgREST API",
                fix_available=True
            ))
            return False
        return True

    async def check_public_policies(self) -> bool:
        """Check for unintended public access policies."""
        public_policies = await self.conn.fetch("""
            SELECT policyname
            FROM pg_policies
            WHERE tablename = 'properties'
            AND ('public' = ANY(roles) OR 'anon' = ANY(roles))
        """)

        if public_policies:
            policy_names = [p['policyname'] for p in public_policies]
            self.issues.append(SecurityIssue(
                severity="HIGH",
                title="Public/anon policies detected",
                description=f"Found policies granting public access: {', '.join(policy_names)}",
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
    """Attempt to automatically fix security issues."""
    fixed_count = 0

    for issue in issues:
        if not issue.fix_available:
            continue

        try:
            if "RLS not enabled" in issue.title:
                await conn.execute("ALTER TABLE properties ENABLE ROW LEVEL SECURITY;")
                print(f"  ✅ Fixed: {issue.title}")
                fixed_count += 1

            elif "No authenticated policy" in issue.title:
                await conn.execute("""
                    CREATE POLICY IF NOT EXISTS "backend_full_access_properties"
                    ON properties FOR ALL TO authenticated
                    USING (true) WITH CHECK (true);
                """)
                print(f"  ✅ Fixed: {issue.title}")
                fixed_count += 1

            elif "Anonymous role has database access" in issue.title:
                await conn.execute("REVOKE ALL ON properties FROM anon;")
                print(f"  ✅ Fixed: {issue.title}")
                fixed_count += 1

            elif "Public/anon policies" in issue.title:
                # Drop any public/anon policies
                await conn.execute('DROP POLICY IF EXISTS "Allow public read access" ON properties;')
                await conn.execute('DROP POLICY IF EXISTS "Enable read access for all users" ON properties;')
                print(f"  ✅ Fixed: {issue.title}")
                fixed_count += 1

        except Exception as e:
            print(f"  ❌ Failed to fix '{issue.title}': {e}")

    return fixed_count

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

    conn = await asyncpg.connect(DATABASE_URL)

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
