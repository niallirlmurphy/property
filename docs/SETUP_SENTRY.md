# Setting up Sentry

Quick guide to enable Sentry error tracking for the backend.

## 1. Create Sentry Account
1. Go to https://sentry.io/signup/
2. Sign up for free (5K errors/month included)
3. Select "Python" as the platform

## 2. Create Project
1. Create a new project
2. Choose "FastAPI" as the framework
3. Name it "ppr-backend" or similar

## 3. Get DSN
1. Go to Settings → Projects → [Your Project]
2. Click "Client Keys (DSN)"
3. Copy the DSN — it looks like:
   ```
   https://examplePublicKey@o000000.ingest.sentry.io/0000000
   ```

## 4. Configure Railway
1. Go to your Railway project
2. Open the backend service
3. Go to Variables tab
4. Add new variable:
   - Name: `SENTRY_DSN`
   - Value: (paste the DSN from step 3)
5. Save and redeploy

## 5. Verify It Works

Sentry is now capturing:
- Unhandled exceptions with full stack traces
- Performance data (10% sample of requests)
- Release tracking (links errors to git commits)

To test it's working, trigger a test error:
```bash
curl https://your-api.railway.app/nonexistent-endpoint
```

Check Sentry dashboard — you should see a 404 error appear within ~30 seconds.

## 6. Configure Alerts

Go to Alerts → Create Alert Rule:

**High Error Rate**
- Condition: Error count > 10 in 1 hour
- Action: Email notification

**New Issue**
- Condition: New issue appears
- Action: Email notification (for first occurrence only)

**Performance Regression**
- Condition: P95 response time > 2000ms
- Action: Slack/Email notification

## What to Monitor

Key metrics in Sentry:
- **Issues** — unique error fingerprints
- **Releases** — errors grouped by deploy (git commit)
- **Performance** — p50/p75/p95 latencies by endpoint
- **User feedback** — attach user context to errors

Filter by:
- `environment:production` — only show prod errors
- `release:latest` — errors in current deploy
- `endpoint:/search` — errors on specific route
