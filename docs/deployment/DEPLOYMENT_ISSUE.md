# Deployment Issue - Valuation Endpoint 404

**Issue:** Valuation endpoint returning 404 Not Found  
**URL:** https://eloquent-optimism-production-350a.up.railway.app/api/valuation/estimate  
**Status:** Under investigation

---

## What's Working ✅
- Backend health check: `/health` returns 200 OK
- Frontend deployed successfully to Vercel
- Frontend can load: https://homeiq.ie/valuation
- Code is committed and pushed to GitHub

## What's Not Working ❌
- POST `/api/valuation/estimate` returns 404
- Endpoint not appearing in `/docs` (OpenAPI)
- Suggests import error or router not registered

---

## Investigation Steps

### 1. Verified Code is Committed
```bash
git show 75e60da:backend/main.py | grep valuation
# Result: ✅ Router import and include_router present
```

### 2. Verified Files in Git
```bash
git ls-tree -r 75e60da --name-only | grep backend/valuation
# Result: ✅ All 9 valuation module files present
```

### 3. Tested Backend Health
```bash
curl https://eloquent-optimism-production-350a.up.railway.app/health
# Result: ✅ {"status":"ok"}
```

### 4. Tested Valuation Endpoint
```bash
curl -X POST .../api/valuation/estimate -d '{"address":"..."}' 
# Result: ❌ {"detail":"Not Found"}
```

---

## Possible Causes

### 1. Import Error on Startup
Railway may have a Python import error that's preventing the router from loading.

**Check:**
- Railway logs for ImportError or ModuleNotFoundError
- Missing dependencies in requirements.txt

### 2. Working Directory Issue
The import `from valuation.api import router` assumes backend/ is the working directory.

**Railway config:**
```toml
startCommand = "/opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT"
```

If Railway runs from repo root instead of backend/, imports will fail.

### 3. Stale Build Cache
Railway may be serving a cached build without the new code.

**Solution:** Triggered redeploy with empty commit

### 4. Missing __pycache__ Initialization
Python module not initialized properly.

**Check:** All `__init__.py` files present

---

## Next Steps

1. **Wait for Railway redeploy** (~2 min)
   - Triggered at: 2026-06-23 10:30
   - Check: https://railway.app/project/[project-id]

2. **Check Railway logs** for import errors:
   ```
   Railway Dashboard → Deployments → Latest → View Logs
   ```

3. **If still failing**, check if Railway needs explicit working directory:
   ```toml
   [deploy]
   workingDirectory = "backend"
   ```

4. **Test locally** to verify imports work:
   ```bash
   cd backend
   python -c "from valuation.api import router; print(router.routes)"
   ```

---

## Workaround (if needed)

If Railway working directory is the issue, update railway.toml:

```toml
[build]
builder = "nixpacks"
buildCommand = "cd backend && pip install -r requirements.txt"

[deploy]
startCommand = "cd backend && /opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT"
workingDirectory = "backend"
```

---

**Status:** Waiting for redeploy (fd5c383)  
**ETA:** 2-3 minutes
