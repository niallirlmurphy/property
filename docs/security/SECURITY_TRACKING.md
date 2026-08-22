# Security Issue Tracking

**Project:** homeiq.ie  
**Last Updated:** June 9, 2026  

---

## Active Issues

### None - All Issues Resolved ✅

---

## Recently Resolved

### spatial_ref_sys RLS Alert ✅

**Status:** ✅ RESOLVED  
**Submitted:** June 9, 2026  
**Resolved:** June 9, 2026 (same day!)  
**Resolution Time:** < 8 hours  
**Resolution Method:** Supabase migrated PostGIS to extensions schema  

**Timeline:**
- ✅ June 9 morning: Issue investigated and documented
- ✅ June 9 morning: Support ticket submitted to Supabase
- ✅ June 9 afternoon: Supabase replied with migration offer
- ✅ June 9 afternoon: Migration approved
- ✅ June 9 afternoon: Supabase completed migration
- ✅ June 9 evening: Verified everything working

**Solution:**
Supabase migrated PostGIS from `public` schema to `extensions` schema using:
```sql
ALTER EXTENSION postgis SET SCHEMA extensions;
```

**Result:**
- ✅ PostGIS in extensions schema (not exposed via API)
- ✅ No RLS needed on system tables (not in public schema)
- ✅ All PostGIS functions working
- ✅ Zero downtime during migration
- ✅ 784,854 properties verified working
- ✅ Production backend fully functional
- ✅ Alert will clear from dashboard (24-48h)

**What to expect:**

**Next 24-48 hours:**
- Supabase support will acknowledge your ticket
- They may ask clarifying questions (rare)
- Auto-reply confirming ticket received

**Within 1-3 business days:**
- Support team reviews the issue
- They'll either:
  1. Enable RLS at platform level (most likely)
  2. Suppress the alert for PostGIS tables
  3. Provide official guidance on handling this

**Within 3-5 business days:**
- Issue resolved
- Alert clears from dashboard
- You'll receive confirmation email

**What you'll see:**
1. Email from Supabase: "Issue resolved"
2. Dashboard alert disappears (check: Settings → Security)
3. No impact on your application (backend keeps working)

**If they ask questions:**
- Refer them to the ticket details
- Key point: "Table is owned by supabase_admin, I cannot modify it"
- Attach: `FIX_SPATIAL_REF_SYS.md` if needed

**If no response in 5 business days:**
- Reply to ticket: "Following up on spatial_ref_sys RLS request"
- Tag as urgent if needed
- Reference project ID: jyezhkgevzejhundypxn

---

## Resolved Issues

### properties Table RLS ✅

**Status:** ✅ RESOLVED  
**Reported:** June 8, 2026  
**Resolved:** June 9, 2026  
**Resolution Time:** < 24 hours  

**What was wrong:**
- Properties table exposed without RLS
- Anonymous users could potentially write to table
- Supabase security alert triggered

**How we fixed it:**
- Ran `python3 scripts/enable_rls_security.py`
- Enabled RLS on properties table
- Created 2 security policies:
  1. Public read access (PPR data is public)
  2. Authenticated write access (backend operations)
- Verified with automated tests

**Prevention:**
- Pre-commit hook now blocks RLS being disabled
- Test suite verifies RLS on every run
- Weekly audit monitors RLS status

**Current status:**
- ✅ RLS enabled
- ✅ 2 policies active
- ✅ 8/8 security tests passing
- ✅ Alert cleared from dashboard

---

## No Action Needed

### search_log Table

**Status:** ⚠️ LOW PRIORITY ENHANCEMENT  
**Issue:** RLS not enabled  
**Risk:** 🟢 Very Low (search query logs only)  
**Decision:** Optional - enable RLS or drop table  

**Options:**

**Option 1: Enable RLS (if using table)**
```sql
ALTER TABLE search_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_only" ON search_log
    FOR ALL TO service_role USING (true);
```

**Option 2: Drop table (if not using)**
```sql
DROP TABLE IF EXISTS search_log;
```

**Recommendation:** Check if table is actually being used by searching codebase:
```bash
grep -r "search_log" backend/ scripts/
```

If no results: drop the table  
If used: enable RLS with service_role-only policy

**Not urgent** - can be addressed anytime or ignored if table is unused.

---

## Security Posture Summary

### ✅ Protected
- properties table: RLS + policies
- API endpoints: CORS + headers
- Secrets: No leaks, proper env vars
- Code: Pre-commit hook active
- Tests: 8/8 passing

### ⏳ Pending
- spatial_ref_sys: Awaiting Supabase support

### ⚠️ Optional
- search_log: Low priority enhancement

**Overall Status:** ✅ SECURE

---

## What to Do While Waiting

### Nothing Required

Your application is secure. The outstanding alert is for a PostGIS system table that:
- Contains only public reference data (EPSG codes)
- Is not your application data
- Poses no security risk
- Can only be fixed by Supabase

### Optional: Run Weekly Audit

Get in the habit of weekly security checks:

```bash
# Every Monday morning:
python3 scripts/security_audit.py
```

Expected output while waiting:
```
✅ RLS enabled on properties table
✅ Security policies configured  
✅ Write protection verified
⚠️  Other tables without RLS: spatial_ref_sys, search_log
```

The warning about spatial_ref_sys will disappear once Supabase resolves the ticket.

---

## When Issue Is Resolved

### Verification Steps

Once you get confirmation from Supabase:

**1. Check Supabase Dashboard**
```
https://supabase.com/dashboard/project/jyezhkgevzejhundypxn/settings/security

Expected: No alerts for spatial_ref_sys
```

**2. Run Security Audit**
```bash
python3 scripts/security_audit.py

Expected: All checks passing, no warnings about spatial_ref_sys
```

**3. Test Backend Still Works**
```bash
curl "https://eloquent-optimism-production-350a.up.railway.app/search?q=Dublin"

Expected: Returns results (proves PostGIS still functioning)
```

**4. Update This Document**

Mark issue as resolved:
```markdown
### spatial_ref_sys RLS ✅

**Status:** ✅ RESOLVED
**Resolved:** [Date]
**Resolution:** Supabase enabled RLS at platform level
```

---

## Contact Information

**Supabase Support:**
- Dashboard: https://supabase.com/dashboard
- Support: https://supabase.com/support
- Project ID: jyezhkgevzejhundypxn

**Your Ticket:**
- Check: Support inbox / Supabase dashboard → Support
- Subject: "Request: Enable RLS on spatial_ref_sys"
- Status: You can check ticket status in dashboard

**If You Need Help:**
- Full documentation: `SECURITY.md`
- spatial_ref_sys guide: `FIX_SPATIAL_REF_SYS.md`
- Security status: `SECURITY_STATUS.md`

---

## Next Review Date

**Security Audit:** June 16, 2026 (1 week)  
**Supabase Follow-up:** June 14, 2026 (if no response by then)  
**Document Update:** When Supabase resolves ticket

---

**Current Status:** ✅ All action items completed, awaiting external response  
**Application Status:** ✅ Secure and operational  
**Risk Level:** 🟢 Low (no blocking issues)
