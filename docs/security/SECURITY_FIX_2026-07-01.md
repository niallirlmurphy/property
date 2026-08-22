# Database Security Fix - July 1, 2026

## Issue
Supabase security alert: "Table publicly accessible - Row-Level Security is not enabled"

## Root Cause
RLS was enabled BUT the `anon` (anonymous) role had SELECT permission on the table. This created a security vulnerability where anyone with the Supabase project URL could read data directly via the PostgREST API.

**Important:** The actual application architecture doesn't need anonymous database access because:
- Frontend → Railway Backend (FastAPI) → Supabase Database
- Frontend never connects directly to Supabase
- Backend uses authenticated `postgres` role with full credentials

## Fix Applied

### 1. Revoked Anonymous Access
```sql
REVOKE ALL ON properties FROM anon;
```

### 2. Removed Unnecessary Policy
```sql
DROP POLICY IF EXISTS "Allow public read access" ON properties;
```

## Final Security Configuration

### Database Security
- ✅ **RLS Enabled**: Row-Level Security active on properties table
- ✅ **Anonymous Access**: BLOCKED (anon role has no permissions)
- ✅ **Backend Access**: Full access via postgres role (DATABASE_URL)
- ✅ **Active Policies**: 1 policy for authenticated users

### Policy Details
```
• backend_full_access_properties
  Command: ALL
  Roles: authenticated
```

### Access Test Results
```bash
Anonymous (anon) role:
  SELECT: ❌ BLOCKED
  INSERT: ❌ BLOCKED
  UPDATE: ❌ BLOCKED
  DELETE: ❌ BLOCKED

Backend (postgres) role:
  ✅ Full access to 785,975 properties

Direct Supabase API access:
  ✅ Returns 401 Unauthorized (correctly blocked)
```

## Production Verification

### API Endpoints (all working)
```bash
✅ /health: 200 (307ms)
✅ /search: 200 (291ms)
✅ /counties: 200 (318ms)
```

### Frontend
✅ Application fully functional at https://homeiq.ie

### Architecture Security
```
Internet
   ↓
Frontend (Vercel)
   ↓
Backend API (Railway) ← Authenticated with DATABASE_URL
   ↓
Supabase Database ← Anonymous access BLOCKED
```

## Why This is Correct

The initial fix (granting SELECT to anon) was **incorrect** because:
1. Frontend doesn't need direct database access
2. All data flows through the authenticated Railway backend
3. Granting public read access unnecessarily exposed the database

The current configuration is **secure** because:
1. Only the backend can access the database (via authenticated connection)
2. Anonymous users cannot query Supabase directly
3. All data access is controlled through the FastAPI backend
4. PPR data remains publicly accessible via the API (appropriate for public records)

## Timeline
- **Issue Reported**: June 28, 2026 (Supabase weekly security scan)
- **Initial (Incorrect) Fix**: July 1, 2026 - Granted anon SELECT permission
- **Corrected Fix**: July 1, 2026 - Revoked anon access entirely
- **Verification**: All production tests passing

## Expected Outcome
- Supabase security alert should clear within 24-48 hours (next scan cycle)
- If alert persists, contact Supabase support with this documentation

## References
- CLAUDE.md: "Security: Only authenticated backend can access database"
- Backend: backend/main.py uses DATABASE_URL with postgres role
- Frontend: frontend/src/api.ts calls Railway API, never Supabase directly
