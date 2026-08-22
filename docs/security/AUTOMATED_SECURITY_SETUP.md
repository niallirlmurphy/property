# Automated Security Monitoring Setup

**Goal**: Proactive daily checks to prevent Supabase security alert emails.

## What This Does

The automated security monitor runs daily and:
- ✅ Checks RLS is enabled on properties table
- ✅ Verifies authenticated-only policy exists
- ✅ Confirms anonymous role has no access
- ✅ Detects unintended public policies
- ✅ Tests backend database connectivity
- ✅ Validates PostGIS extension is enabled

If issues are detected, it **automatically fixes them** and notifies you only if auto-fix fails.

## Setup Options

Choose **ONE** of these options (GitHub Actions recommended for simplicity):

### Option 1: GitHub Actions (Recommended)

**Pros**: Free, no configuration needed, runs automatically
**Cons**: Requires GitHub repository

**Setup (5 minutes):**

1. **Add DATABASE_URL secret to GitHub:**
   - Go to your repository on GitHub
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DATABASE_URL`
   - Value: (copy from `backend/.env`)
   - Click "Add secret"

2. **Enable GitHub Actions:**
   - Push the `.github/workflows/security-monitor.yml` file (already committed)
   - GitHub will automatically start running the workflow

3. **Test it manually:**
   - Go to Actions tab in your GitHub repository
   - Click "Daily Security Monitoring" workflow
   - Click "Run workflow" button
   - Verify it passes with green checkmark

**Schedule**: Runs daily at 3:00 AM UTC (4:00 AM IST)

**Notifications**: 
- ✅ Success: Silent (no notification)
- ❌ Failure: Creates GitHub Issue automatically

### Option 2: Railway Cron Job

**Pros**: Runs in your production environment
**Cons**: Requires Railway Pro plan ($20/month) for cron jobs

**Setup:**

1. **In Railway dashboard:**
   - Go to your backend service
   - Click "Settings" tab
   - Scroll to "Cron Jobs"
   - Click "Add Cron Job"

2. **Configure cron job:**
   - Name: `Security Monitor`
   - Schedule: `0 3 * * *` (daily at 3 AM)
   - Command: `/app/scripts/railway_security_cron.sh`
   - Save

**Notifications**: Check Railway logs for results

### Option 3: Local Cron Job (Mac/Linux)

**Pros**: Free, simple
**Cons**: Only runs when your computer is on

**Setup:**

1. **Create wrapper script** (`~/security_check.sh`):
```bash
#!/bin/bash
cd /Users/nmurphy/claude/property\ price\ project
export $(grep '^DATABASE_URL=' backend/.env | xargs)
python3 scripts/security_monitor.py --fix
```

2. **Make it executable:**
```bash
chmod +x ~/security_check.sh
```

3. **Add to crontab:**
```bash
crontab -e
```

Add this line:
```
0 3 * * * /Users/nmurphy/security_check.sh >> /Users/nmurphy/security_monitor.log 2>&1
```

**Notifications**: Check `~/security_monitor.log`

## Manual Testing

Test the monitor anytime:

```bash
# Run checks only (report issues)
python3 scripts/security_monitor.py

# Run checks and auto-fix issues
python3 scripts/security_monitor.py --fix
```

**Expected output when everything is secure:**
```
✅ ALL SECURITY CHECKS PASSED

✅ RLS enabled on properties table
✅ Authenticated-only policy active
✅ Anonymous access blocked
✅ No public policies found
✅ Backend can access database
✅ PostGIS extension enabled

🔒 Security posture: STRONG
📧 No action needed - Supabase alerts should not trigger
```

## What Happens When Issues Are Detected

### Automated Flow:
1. **Daily check runs** (3 AM)
2. **Issue detected** (e.g., RLS disabled)
3. **Auto-fix attempts** (runs `enable_rls_security.py` logic)
4. **Verification** (re-runs checks)
5. **Success**: Silent (no notification)
6. **Failure**: Notification sent (GitHub Issue or log entry)

### Manual Intervention (Rare):
If auto-fix fails, you'll receive a notification with:
- Description of the issue
- Severity level (CRITICAL/HIGH/MEDIUM/LOW)
- Link to verification documentation

**Action**: Run `python3 scripts/enable_rls_security.py` manually

## Monitoring Schedule

**Daily**: Automated security checks (3:00 AM UTC)
**Weekly**: Review GitHub Actions history or Railway logs
**Quarterly**: Manual verification using SECURITY_CHECKLIST.md (calendar reminder)

## Integration with Supabase Alerts

**Before automated monitoring:**
- Supabase scans weekly → finds issue → sends email → manual fix required

**After automated monitoring:**
- Daily check → finds issue → auto-fixes immediately → Supabase scan sees correct config → no email

**Result**: You should stop receiving Supabase security alert emails.

## Troubleshooting

### GitHub Action fails with "DATABASE_URL not set"
- Verify secret is added in GitHub Settings → Secrets
- Re-run workflow

### "Permission denied" error
- Ensure scripts are executable: `chmod +x scripts/*.py scripts/*.sh`

### Auto-fix doesn't work
- Check DATABASE_URL has admin permissions (postgres role, not anon key)
- Run `scripts/enable_rls_security.py` manually for detailed output

### Still receiving Supabase emails after setup
- Wait 24-48 hours for Supabase to re-scan
- Check GitHub Actions ran successfully (green checkmark)
- Manually verify: `python3 scripts/security_monitor.py`

## Cost Analysis

| Option | Setup Time | Monthly Cost | Reliability |
|--------|------------|--------------|-------------|
| GitHub Actions | 5 min | Free | High |
| Railway Cron | 10 min | $20 | High |
| Local Cron | 10 min | Free | Medium (requires computer on) |

**Recommendation**: Start with GitHub Actions (free and reliable).

## Next Steps

1. ✅ Set up GitHub Actions (Option 1 above)
2. ✅ Test manually: `python3 scripts/security_monitor.py`
3. ⏳ Wait 24-48 hours for next Supabase scan
4. ✅ Confirm no alert emails received

## Related Files

- `scripts/security_monitor.py` - Main monitoring script
- `scripts/enable_rls_security.py` - Manual fix script
- `.github/workflows/security-monitor.yml` - GitHub Actions workflow
- `SECURITY_CHECKLIST.md` - Manual verification checklist
- `SUPABASE_SECURITY_ALERTS_RESPONSE.md` - Quick reference guide
