# Reply to Supabase Support - Approve PostGIS Migration

**Copy-paste this reply to your support ticket:**

---

Hello Supabase Support,

Thank you for the detailed explanation and the offer to relocate PostGIS to the extensions schema.

**I authorize Supabase to run the migration SQL** to move PostGIS from `public` schema to `extensions` schema for project **jyezhkgevzejhundypxn**.

Please proceed with:
```sql
BEGIN;
UPDATE pg_extension
  SET extrelocatable = true
WHERE extname = 'postgis';

ALTER EXTENSION postgis
  SET SCHEMA extensions;

ALTER EXTENSION postgis
  UPDATE TO "3.3.7next";

ALTER EXTENSION postgis UPDATE;

UPDATE pg_extension
  SET extrelocatable = false
WHERE extname = 'postgis';
COMMIT;
```

**Confirmation:**
- Project ID: jyezhkgevzejhundypxn
- Current PostGIS location: public schema
- Target location: extensions schema
- Authorization: Approved

**My setup:**
- Main data table: `properties` (~784k rows with geography column)
- Backend: FastAPI on Railway (uses ST_Distance, ST_Transform, ST_DWithin)
- Frontend: React on Vercel (calls backend API, no direct PostGIS queries)

**After migration, please confirm:**
1. PostGIS is now in extensions schema
2. My properties.geog column still works
3. The spatial_ref_sys security alert is resolved

Thank you for handling this migration!

Best regards,
[Your name]

---

## What Happens Next

**Supabase will:**
1. Schedule the migration (usually within 24 hours)
2. Run the SQL during low-traffic period
3. Verify migration succeeded
4. Reply to confirm completion

**You should:**
1. Check your application after they confirm (~24-48 hours)
2. Run test suite to verify everything works
3. Check that security alert is cleared
4. Update your documentation

**Expected:** Zero downtime, everything keeps working, alert disappears.

---

**Status:** ✅ Ready to send  
**Action:** Reply to your Supabase support ticket with the approval above
