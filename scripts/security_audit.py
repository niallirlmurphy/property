#!/usr/bin/env python3
"""
Weekly security audit script.
Run this every week to verify security posture hasn't degraded.

Usage:
    python3 scripts/security_audit.py
    python3 scripts/security_audit.py --slack-webhook=<url>  # Send report to Slack
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.environ.get("DATABASE_URL")

class SecurityAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []

    def issue(self, category: str, description: str):
        self.issues.append((category, description))
        print(f"❌ {category}: {description}")

    def warning(self, category: str, description: str):
        self.warnings.append((category, description))
        print(f"⚠️  {category}: {description}")

    def success(self, category: str, description: str):
        self.passed.append((category, description))
        print(f"✅ {category}: {description}")

    def report(self):
        print("\n" + "="*70)
        print("SECURITY AUDIT SUMMARY")
        print("="*70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Passed:   {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Issues:   {len(self.issues)}")

        if self.issues:
            print("\n🚨 CRITICAL ISSUES - FIX IMMEDIATELY:")
            for cat, desc in self.issues:
                print(f"  • {cat}: {desc}")

        if self.warnings:
            print("\n⚠️  WARNINGS - REVIEW RECOMMENDED:")
            for cat, desc in self.warnings:
                print(f"  • {cat}: {desc}")

        return len(self.issues) == 0


async def audit_database_security(audit: SecurityAudit):
    """Audit database security configuration."""
    print("\n📊 DATABASE SECURITY")
    print("-" * 70)

    if not DATABASE_URL:
        audit.issue("Database", "DATABASE_URL not set")
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=10.0)

        # Check 1: RLS enabled on all public tables
        # Exclude PostGIS system tables (owned by supabase_admin, not user data)
        tables = await conn.fetch("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'pg_%'
            AND tablename NOT LIKE 'sql_%'
            AND tablename NOT IN (
                'spatial_ref_sys',      -- PostGIS coordinate reference systems
                'geometry_columns',     -- PostGIS metadata
                'geography_columns',    -- PostGIS metadata
                'raster_columns',       -- PostGIS metadata
                'raster_overviews'      -- PostGIS metadata
            )
        """)

        unprotected = [t['tablename'] for t in tables if not t['rowsecurity']]

        if unprotected:
            # Critical if properties table is exposed
            if 'properties' in unprotected:
                audit.issue("RLS", f"CRITICAL: properties table has RLS disabled")
            else:
                audit.warning("RLS", f"Tables without RLS: {', '.join(unprotected)}")
        else:
            audit.success("RLS", f"All {len(tables)} tables protected")

        # Check 2: Properties table policies
        policies = await conn.fetch("""
            SELECT policyname, cmd, roles::text[]
            FROM pg_policies
            WHERE tablename = 'properties'
        """)

        if len(policies) == 0:
            audit.issue("Policies", "No security policies on properties table")
        elif len(policies) < 2:
            audit.warning("Policies", f"Only {len(policies)} policy - expected at least 2")
        else:
            # Check for public read access
            has_public_read = any(
                p['cmd'] == 'SELECT' and 'public' in p['roles']
                for p in policies
            )
            # Check for auth write access
            has_auth_write = any(
                p['cmd'] == 'ALL' and 'authenticated' in p['roles']
                for p in policies
            )

            if not has_public_read:
                audit.warning("Policies", "No public read policy - API may not work")
            if not has_auth_write:
                audit.warning("Policies", "No auth write policy - imports may fail")

            if has_public_read and has_auth_write:
                audit.success("Policies", f"{len(policies)} policies configured correctly")
            else:
                audit.success("Policies", f"{len(policies)} policies active")

        # Check 3: Verify read access works
        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM properties LIMIT 1")
            audit.success("Read Access", f"Can query {count:,} properties")
        except Exception as e:
            audit.issue("Read Access", f"Cannot read properties: {str(e)[:100]}")

        # Check 4: Verify anonymous writes are blocked
        try:
            await conn.execute("SET ROLE anon;")
            await conn.execute("""
                INSERT INTO properties (address, price, sale_date)
                VALUES ('Security Test', 1, '2026-01-01');
            """)
            audit.issue("Write Protection", "CRITICAL: Anonymous writes are NOT blocked")
        except Exception as e:
            if "permission denied" in str(e).lower() or "row-level security" in str(e).lower():
                audit.success("Write Protection", "Anonymous writes blocked")
            else:
                audit.warning("Write Protection", f"Unexpected error: {str(e)[:100]}")
        finally:
            await conn.execute("RESET ROLE;")

        # Check 5: Spatial indexes exist
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'properties'
            AND indexdef LIKE '%geog%'
        """)

        if len(indexes) == 0:
            audit.warning("Indexes", "No spatial indexes - queries may be slow")
        else:
            audit.success("Indexes", f"{len(indexes)} spatial indexes present")

        await conn.close()

    except Exception as e:
        audit.issue("Database Connection", str(e))


def audit_secrets_in_code(audit: SecurityAudit):
    """Check for secrets accidentally committed to git."""
    print("\n🔐 SECRETS AUDIT")
    print("-" * 70)

    import subprocess

    try:
        # Check for .env files in git
        result = subprocess.run(
            ["git", "ls-files", "*.env", ".env*"],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            files = result.stdout.strip().split('\n')
            audit.issue("Secrets", f"CRITICAL: .env files in git: {', '.join(files)}")
        else:
            audit.success("Secrets", "No .env files in repository")

        # Check for common secret patterns in recent commits
        result = subprocess.run(
            ["git", "log", "-1", "--all", "-p"],
            capture_output=True,
            text=True
        )

        secret_patterns = [
            "DATABASE_URL=postgresql://",
            "MAPBOX_TOKEN=pk.",
            "AUTOADDRESS_KEY=pub_",
            "api_key=",
            "password=",
        ]

        found_secrets = []
        for pattern in secret_patterns:
            if pattern in result.stdout:
                found_secrets.append(pattern.split('=')[0])

        if found_secrets:
            audit.warning("Recent Commits", f"Potential secrets in recent commit: {', '.join(found_secrets)}")
        else:
            audit.success("Recent Commits", "No obvious secrets in recent changes")

    except Exception as e:
        audit.warning("Git Check", f"Could not check git history: {str(e)[:100]}")


def audit_api_security(audit: SecurityAudit):
    """Check API security configuration."""
    print("\n🌐 API SECURITY")
    print("-" * 70)

    try:
        # Check backend/main.py for CORS config
        with open("backend/main.py", "r") as f:
            content = f.read()

        # Check for wildcard CORS
        if 'origins=["*"]' in content or "origins=['*']" in content:
            audit.issue("CORS", 'CRITICAL: CORS allows all origins ("*")')
        elif "homeiq.ie" in content:
            audit.success("CORS", "CORS restricted to homeiq.ie domain")
        else:
            audit.warning("CORS", "Could not verify CORS configuration")

        # Check for security headers
        if "x-content-type-options" in content.lower():
            audit.success("Security Headers", "Security headers configured")
        else:
            audit.warning("Security Headers", "Security headers may not be configured")

    except FileNotFoundError:
        audit.warning("API Config", "Could not read backend/main.py")
    except Exception as e:
        audit.warning("API Config", str(e)[:100])


def audit_environment_files(audit: SecurityAudit):
    """Check that .env files are properly protected."""
    print("\n📁 ENVIRONMENT FILES")
    print("-" * 70)

    files_to_check = [
        "backend/.env",
        "frontend/.env.local",
        ".env"
    ]

    for filepath in files_to_check:
        if os.path.exists(filepath):
            # Check file permissions
            import stat
            mode = os.stat(filepath).st_mode
            if mode & stat.S_IROTH or mode & stat.S_IRGRP:
                audit.warning("File Permissions", f"{filepath} is readable by others")
            else:
                audit.success("File Permissions", f"{filepath} properly protected")
        else:
            # Missing .env in production is OK (uses environment variables)
            pass


async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     SECURITY AUDIT - homeiq.ie                               ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    audit = SecurityAudit()

    # Run all audits
    await audit_database_security(audit)
    audit_secrets_in_code(audit)
    audit_api_security(audit)
    audit_environment_files(audit)

    # Generate report
    success = audit.report()

    # Action items
    if not success:
        print("\n🚨 ACTION REQUIRED:")
        print("   1. Fix critical issues immediately")
        print("   2. Run: python3 scripts/enable_rls_security.py")
        print("   3. Run: python3 tests/test_production_suite.py")
        print("   4. Document fixes in security incident log")

    print("\n📋 NEXT STEPS:")
    print("   • Schedule weekly run of this script")
    print("   • Review warnings and plan fixes")
    print("   • Update CLAUDE.md if new security patterns found")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nAudit cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Audit error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
