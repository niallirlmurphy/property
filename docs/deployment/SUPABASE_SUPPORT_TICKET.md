# Supabase Support Ticket - spatial_ref_sys RLS

**Copy-paste this into Supabase support**

---

## Subject
Request: Enable RLS on spatial_ref_sys (PostGIS System Table)

---

## Message

Hello Supabase Support,

I'm receiving a security alert for `spatial_ref_sys` not having RLS enabled:

```
Entity: public.spatial_ref_sys
Issue: Table public.spatial_ref_sys is public, but RLS has not been enabled.
Project ID: jyezhkgevzejhundypxn
```

I attempted to enable RLS via SQL Editor but received:
```
ERROR: 42501: must be owner of table spatial_ref_sys
```

**Request:** Could you please enable RLS on this table at the platform level?

**Recommended SQL:**
```sql
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;

-- Option A: If clients need read access
CREATE POLICY "Allow public read" ON spatial_ref_sys
    FOR SELECT TO anon, authenticated USING (true);

-- OR Option B: Restrict to backend only (preferred)
REVOKE ALL ON spatial_ref_sys FROM anon, authenticated;
GRANT SELECT ON spatial_ref_sys TO service_role;
```

**Context:**
- `spatial_ref_sys` is a PostGIS system table (EPSG coordinate definitions)
- Owned by `supabase_admin`, not my user
- Contains only public reference data (8,500 coordinate systems)
- My application data tables already have RLS enabled

**Preference:** Option B (restrict to backend) - my frontend doesn't query this table directly.

Thank you for your assistance.

---

**Project ID:** jyezhkgevzejhundypxn  
**Table:** public.spatial_ref_sys  
**Owner:** supabase_admin

---

## Alternative: Request Alert Suppression

If enabling RLS is not standard practice for PostGIS system tables, could you suppress this alert? The table contains only public EPSG reference data and poses no security risk.

---

## What to Expect

**Response time:** 1-3 business days  
**Likely outcome:** Supabase will either:
1. Enable RLS with Option B (recommended) - alert clears
2. Suppress the alert for PostGIS system tables
3. Provide guidance on handling extension-managed tables

**After resolution:**
- Alert disappears from dashboard
- Your application continues working unchanged
- No further action needed
