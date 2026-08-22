# URGENT: Admin Endpoints Exposed

**Status:** CRITICAL - Authentication not enforced  
**Discovered:** 2026-07-02 00:02  
**Impact:** HIGH - PII exposed, unauthorized admin access

## Issue

Admin endpoints are accessible without authentication despite code fixes:
- `/geocoding-queue/next` - ❌ Returns data (should be 401)
- `/email-alerts/active` - ❌ **Returns ALL email addresses** (should be 401)
- `/cron/send-monthly-alerts` - ❌ **Actually executes** (should be 401)

## Root Cause

Either:
1. Railway hasn't deployed the latest code (commit 8efe071)
2. Environment variables aren't configured correctly
3. Railway deployment failed silently

## Immediate Actions Required

### 1. Verify Railway Deployment
Go to Railway dashboard and check:
- Is the deployment running commit `8efe071`?
- Did the latest deployment succeed?
- Are there any build/deploy errors?

### 2. Verify Environment Variables
In Railway → Variables, confirm these exist:
- `ADMIN_API_TOKEN` (should be 32+ characters)
- `CRON_SECRET` (should be 32+ characters)
- Both should be random tokens, not placeholders

### 3. Force Redeploy if Needed
If variables are set but deployment is old:
1. Go to Railway dashboard
2. Click "Redeploy" on the latest build
3. Wait for deployment to complete (~2-3 minutes)

### 4. Test After Deployment

```bash
# Should return 401 Unauthorized
curl https://eloquent-optimism-production-350a.up.railway.app/geocoding-queue/next

# Should return 401 Unauthorized  
curl https://eloquent-optimism-production-350a.up.railway.app/email-alerts/active

# Should return 401 Unauthorized
curl -X POST https://eloquent-optimism-production-350a.up.railway.app/cron/send-monthly-alerts
```

All three should return:
```json
{"detail":"Missing authentication token"}
```
or
```json
{"detail":"Missing cron secret"}
```

### 5. If Still Not Working

Check Railway logs:
```
railway logs
```

Look for:
- `ADMIN_API_TOKEN not configured in environment` 
- `CRON_SECRET not configured in environment`
- Any startup errors

## GitHub Secret (Secondary Priority)

Once Railway is secured, add to GitHub:

1. Go to https://github.com/niallirlmurphy/property/settings/secrets/actions
2. Click "New repository secret"
3. Name: `CRON_SECRET`
4. Value: (same value as Railway's CRON_SECRET)
5. Click "Add secret"

Then update `.github/workflows/*.yml` to use:
```yaml
- name: Send monthly alerts
  run: |
    curl -X POST \
      -H "X-Cron-Secret: ${{ secrets.CRON_SECRET }}" \
      https://eloquent-optimism-production-350a.up.railway.app/cron/send-monthly-alerts
```

## Current Exposure

**Data exposed:**
- 5 email addresses (niall.murphy@gmail.com, test@example.com, etc.)
- Unsubscribe tokens for all subscriptions
- Property geocoding queue
- Ability to trigger cron jobs

**Mitigation:**
- Tokens are still valid (can be rotated if concerned)
- No passwords or payment info exposed
- Main impact: privacy breach + unauthorized admin actions

## Timeline

- 2026-07-01 23:39 - Security fixes committed (790fa8e)
- 2026-07-01 23:40 - Critical vuln fixes committed (8efe071)  
- 2026-07-01 23:41 - Pushed to GitHub
- 2026-07-02 00:02 - **Discovered endpoints still exposed**

## Status

🔴 **CRITICAL - Take action now**

Once Railway is verified and redeployed, update this status.
