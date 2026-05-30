# Email Alerts Setup Guide

This guide covers the complete setup for HomeIQ's email alert system with Resend + GitHub Actions cron.

## Architecture Overview

- **Email Provider:** Resend (3k emails/month free tier)
- **Cron Job:** GitHub Actions (runs 1st of each month at 2 AM UTC)
- **Templates:** HTML emails with plain text fallback (Mustache templating)
- **Features:** Double opt-in confirmation, one-click unsubscribe, monthly digests

## Prerequisites

1. **Resend Account** - Sign up at https://resend.com
2. **Domain Verification** - Verify homeiq.ie in Resend
3. **API Key** - Generate API key from Resend dashboard
4. **GitHub Secrets** - Access to repository settings

---

## Step 1: Resend Setup

### 1.1 Create Resend Account
1. Go to https://resend.com
2. Sign up with your email
3. Verify your email address

### 1.2 Add and Verify Domain
1. In Resend dashboard, go to **Domains**
2. Click **Add Domain**
3. Enter: `homeiq.ie`
4. Copy the DNS records provided by Resend

### 1.3 Configure DNS Records (via Letshost.ie)
Log in to https://www.letshost.ie and add these DNS records:

**SPF Record:**
```
Type: TXT
Name: @ (or homeiq.ie)
Value: v=spf1 include:resend.com ~all
TTL: 3600
```

**DKIM Records:** (Resend provides 3 records)
```
Type: CNAME
Name: resend._domainkey
Value: [value from Resend dashboard]
TTL: 3600

Type: CNAME
Name: resend2._domainkey
Value: [value from Resend dashboard]
TTL: 3600

Type: CNAME
Name: resend3._domainkey
Value: [value from Resend dashboard]
TTL: 3600
```

**DMARC Record:**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@homeiq.ie
TTL: 3600
```

**Note:** DNS propagation takes 5-60 minutes. Check status in Resend dashboard.

### 1.4 Generate API Key
1. In Resend dashboard, go to **API Keys**
2. Click **Create API Key**
3. Name: `HomeIQ Production`
4. Permission: **Sending access**
5. Copy the API key (starts with `re_...`)

---

## Step 2: Railway Environment Variables

Add these environment variables in Railway dashboard:

1. Go to https://railway.app/project/[your-project-id]
2. Select your backend service
3. Go to **Variables** tab
4. Add:

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
CRON_SECRET=[generate a random 32-character string]
```

**Generate CRON_SECRET:**
```bash
openssl rand -base64 32
# or
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Note:** Keep CRON_SECRET secure - it protects the cron endpoint from unauthorized access.

---

## Step 3: GitHub Secrets

Add these secrets in GitHub repository:

1. Go to: https://github.com/niallirlmurphy/property/settings/secrets/actions
2. Click **New repository secret**
3. Add:

```
Name: CRON_SECRET
Value: [same value as Railway CRON_SECRET]
```

---

## Step 4: Deploy Backend Changes

The following files have been created/modified:

**New Files:**
- `backend/email_service.py` - Email sending logic
- `backend/email_templates/confirmation.html` - Confirmation email template
- `backend/email_templates/monthly_digest.html` - Monthly digest template
- `backend/cron_monthly_alerts.py` - Standalone cron script (optional)
- `.github/workflows/monthly-property-alerts.yml` - GitHub Actions cron

**Modified Files:**
- `backend/requirements.txt` - Added `resend` and `pystache`
- `backend/main.py` - Updated subscribe endpoint, added cron endpoint
- `frontend/src/components/EmailAlertModal.tsx` - Updated success message

**Deployment Steps:**
```bash
# Commit changes
git add .
git commit -m "Add email alerts with Resend + GitHub Actions cron"
git push origin main

# Railway will auto-deploy backend
# Vercel will auto-deploy frontend
```

Wait 2-3 minutes for deployments to complete.

---

## Step 5: Verify Setup

### 5.1 Test Confirmation Email
1. Go to https://homeiq.ie
2. Search for any location (e.g., "Dublin 2")
3. Click **Property Email Alert** button
4. Fill in the form with your email
5. Click **Confirm Signup**
6. Check your inbox for confirmation email

**Expected:** 
- Success message in modal
- Confirmation email within 1 minute
- Email from: `HomeIQ Property Alerts <alerts@homeiq.ie>`
- Unsubscribe link works

### 5.2 Test Cron Endpoint (Manual Trigger)
```bash
# Test locally (requires CRON_SECRET from Railway)
curl -X POST https://eloquent-optimism-production-350a.up.railway.app/cron/send-monthly-alerts \
  -H "Authorization: Bearer YOUR_CRON_SECRET" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "ok": true,
#   "subscriptions_processed": 1,
#   "emails_sent": 0,
#   "skipped": 1,
#   "errors": 0
# }
```

**Note:** `emails_sent: 0` is normal if no new properties since subscription.

### 5.3 Test GitHub Actions Cron
1. Go to: https://github.com/niallirlmurphy/property/actions
2. Click **Monthly Property Alerts** workflow
3. Click **Run workflow** → **Run workflow** (manual trigger)
4. Wait ~30 seconds
5. Check logs for success message

**Expected:**
- ✅ Green checkmark
- Logs show: "Monthly alerts job completed successfully"
- JSON response with `ok: true`

---

## Step 6: Monitor Deliverability

### 6.1 Google Postmaster Tools
1. Go to https://postmaster.google.com
2. Add domain: `homeiq.ie`
3. Verify ownership (add TXT record to DNS)
4. Monitor:
   - Spam rate (keep < 0.10%)
   - IP reputation
   - Domain reputation

### 6.2 Resend Dashboard
Monitor in https://resend.com/emails:
- Delivery rate (target: 98%+)
- Bounce rate (keep < 2%)
- Spam complaints (keep < 0.10%)

### 6.3 Set Up Alerts
In Railway, enable notifications for:
- Backend deployment failures
- High error rates
- Slow response times

---

## How It Works

### User Subscribes
1. User fills out form on homeiq.ie
2. Frontend sends POST to `/email-alerts/subscribe`
3. Backend:
   - Saves subscription to `email_alerts` table
   - Generates unsubscribe token
   - Sends confirmation email via Resend
4. User receives confirmation email

### Monthly Cron Job
1. GitHub Actions triggers on 1st of month at 2 AM UTC
2. Calls Railway endpoint: `POST /cron/send-monthly-alerts`
3. Backend:
   - Fetches all active subscriptions
   - For each subscription:
     - Geocodes address to get lat/lon
     - Queries properties added since `last_sent_at`
     - If new properties found → send digest email
     - Update `last_sent_at` timestamp
   - Returns summary: emails sent, skipped, errors
4. If job fails → GitHub creates issue automatically

### User Unsubscribes
1. User clicks unsubscribe link in email
2. Frontend route: `/email-alerts/unsubscribe/{token}`
3. Backend marks subscription as `is_active = FALSE`
4. No more emails sent

---

## Cost Estimate

**Free Tier (0-3,000 emails/month):**
- ✅ Confirmation emails: ~100/month
- ✅ Monthly digests: ~100/month
- ✅ Total: ~200/month
- **Cost: $0/month**

**Paid Tier (3,000-50,000 emails/month):**
- 500 subscribers × 2 emails = 1,000/month
- **Cost: $0/month** (within free tier)

**At Scale (50,000+ emails/month):**
- 10,000 subscribers × 2 emails = 20,000/month
- **Cost: $20/month** (Resend Pro plan)

**Note:** GitHub Actions is free for this usage (< 5 minutes/month).

---

## Troubleshooting

### Confirmation emails not sending
1. Check Railway logs: `railway logs --service backend`
2. Verify `RESEND_API_KEY` is set in Railway
3. Check Resend dashboard → Emails → look for errors
4. Verify DNS records are propagated: `dig homeiq.ie TXT`

### Cron job failing
1. Check GitHub Actions logs
2. Verify `CRON_SECRET` matches in Railway and GitHub
3. Test endpoint manually with curl
4. Check Railway backend is running: `curl https://eloquent-optimism-production-350a.up.railway.app/health`

### Emails going to spam
1. Check SPF/DKIM/DMARC records are correct
2. Monitor Google Postmaster Tools
3. Check Resend deliverability metrics
4. Ensure unsubscribe link is prominent
5. Reduce email frequency if complaint rate > 0.10%

### High bounce rate
1. Validate email addresses on signup (already implemented)
2. Remove hard bounces immediately
3. Re-engagement campaign for inactive users
4. Check Resend bounce logs for patterns

---

## Next Steps

1. **Monitor for 30 days** - Let the system run and watch deliverability
2. **Adjust frequency** - If complaint rate high, reduce to quarterly
3. **Add features** - Property images, price trends, area statistics
4. **Scale** - If > 3k emails/month, upgrade to Resend Pro ($20/month)

---

## Support

- **Resend Docs:** https://resend.com/docs
- **GitHub Actions Cron:** https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule
- **Email Deliverability:** https://www.mail-tester.com

For issues, check Railway logs first, then Resend dashboard, then GitHub Actions logs.
