# Email Alerts Setup Checklist

Quick reference for setting up the email alert system. See [EMAIL_ALERTS_SETUP.md](./EMAIL_ALERTS_SETUP.md) for detailed instructions.

## ✅ Setup Steps

### 1. Resend Setup (15 minutes)
- [ ] Create Resend account: https://resend.com
- [ ] Add domain: `homeiq.ie`
- [ ] Get DNS records from Resend dashboard
- [ ] Add DNS records to Letshost.ie:
  - [ ] SPF record (TXT)
  - [ ] 3 DKIM records (CNAME)
  - [ ] DMARC record (TXT)
- [ ] Wait for DNS propagation (5-60 mins)
- [ ] Verify domain in Resend dashboard
- [ ] Generate API key (starts with `re_...`)

### 2. Railway Environment Variables (2 minutes)
- [ ] Go to Railway dashboard → Backend service → Variables
- [ ] Add `RESEND_API_KEY=re_xxxxxxxxxxxx`
- [ ] Generate CRON_SECRET: `openssl rand -base64 32`
- [ ] Add `CRON_SECRET=[your-secret]`
- [ ] Save and redeploy

### 3. GitHub Secrets (1 minute)
- [ ] Go to: https://github.com/niallirlmurphy/property/settings/secrets/actions
- [ ] Add secret: `CRON_SECRET` (same value as Railway)

### 4. Deploy Code (5 minutes)
- [ ] Code already pushed to main branch
- [ ] Wait for Railway to deploy backend (~2 mins)
- [ ] Wait for Vercel to deploy frontend (~2 mins)
- [ ] Check deployments are successful

### 5. Test Confirmation Email (2 minutes)
- [ ] Go to https://homeiq.ie
- [ ] Search for "Dublin 2"
- [ ] Click "Property Email Alert" button
- [ ] Fill in form with your email
- [ ] Click "Confirm Signup"
- [ ] Check inbox for confirmation email
- [ ] Verify unsubscribe link works

### 6. Test Cron Endpoint (2 minutes)
```bash
curl -X POST https://eloquent-optimism-production-350a.up.railway.app/cron/send-monthly-alerts \
  -H "Authorization: Bearer YOUR_CRON_SECRET" \
  -H "Content-Type: application/json"
```
- [ ] Returns `{"ok": true, ...}`
- [ ] No errors in Railway logs

### 7. Test GitHub Actions Workflow (2 minutes)
- [ ] Go to: https://github.com/niallirlmurphy/property/actions
- [ ] Click "Monthly Property Alerts"
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Wait ~30 seconds
- [ ] Verify green checkmark and success logs

### 8. Monitor Setup (5 minutes)
- [ ] Add domain to Google Postmaster Tools
- [ ] Bookmark Resend dashboard: https://resend.com/emails
- [ ] Set up Railway notifications for errors
- [ ] Test unsubscribe flow

---

## 📋 Quick Reference

### Environment Variables Needed

**Railway Backend:**
```
RESEND_API_KEY=re_...
CRON_SECRET=[random-32-char-string]
```

**GitHub Secrets:**
```
CRON_SECRET=[same-as-railway]
```

### DNS Records (Letshost.ie)

```
TXT   @               v=spf1 include:resend.com ~all
CNAME resend._domainkey   [from Resend]
CNAME resend2._domainkey  [from Resend]
CNAME resend3._domainkey  [from Resend]
TXT   _dmarc          v=DMARC1; p=none; rua=mailto:dmarc@homeiq.ie
```

### Key Endpoints

- Subscribe: `POST /email-alerts/subscribe`
- Unsubscribe: `POST /email-alerts/unsubscribe/{token}`
- Cron: `POST /cron/send-monthly-alerts` (protected)
- Active: `GET /email-alerts/active`

### Cron Schedule

- **Runs:** 1st of each month at 2:00 AM UTC
- **Trigger:** GitHub Actions workflow
- **Workflow:** `.github/workflows/monthly-property-alerts.yml`
- **Manual:** GitHub Actions → Monthly Property Alerts → Run workflow

---

## 🚨 Troubleshooting

**Emails not sending?**
```bash
# Check Railway logs
railway logs --service backend

# Test Resend API
curl https://api.resend.com/emails \
  -H "Authorization: Bearer re_..." \
  -H "Content-Type: application/json" \
  -d '{"from":"onboarding@resend.dev","to":"your@email.com","subject":"Test","html":"<p>Test</p>"}'
```

**Cron job failing?**
1. Check GitHub Actions logs
2. Verify CRON_SECRET matches
3. Test endpoint with curl
4. Check Railway backend is running

**Emails going to spam?**
1. Check DNS records: `dig homeiq.ie TXT`
2. Check domain verified in Resend
3. Monitor Google Postmaster Tools
4. Check Resend deliverability metrics

---

## 📊 Success Criteria

- ✅ Confirmation emails arrive within 1 minute
- ✅ Emails from: `HomeIQ Property Alerts <alerts@homeiq.ie>`
- ✅ Unsubscribe link works
- ✅ Cron endpoint returns 200 OK
- ✅ GitHub Actions workflow succeeds
- ✅ Delivery rate > 98%
- ✅ Spam complaint rate < 0.10%

---

## 🎯 Next Actions After Setup

1. **Subscribe yourself** - Test the full flow
2. **Monitor for 7 days** - Check Resend dashboard daily
3. **Run manual cron** - Test monthly digest before 1st of month
4. **Set up monitoring** - Google Postmaster Tools + Railway alerts
5. **Document issues** - Note any problems for troubleshooting

---

**Estimated Total Setup Time:** ~30-40 minutes (mostly waiting for DNS propagation)
