# Salesforce Setup Checklist

Quick reference checklist for setting up Salesforce geocoding. Check off each step as you complete it.

---

## ✅ Pre-Setup Checklist

- [ ] I have a Salesforce account
- [ ] I have System Administrator access (or equivalent)
- [ ] I can access Setup (gear icon ⚙️)
- [ ] I have 15 minutes to complete setup

---

## ✅ Part 1: Enable Maps (5 min)

- [ ] **Step 1**: Logged into Salesforce
- [ ] **Step 2**: Opened Setup (gear icon ⚙️ → Setup)
- [ ] **Step 3**: Searched "Maps" in Quick Find
- [ ] **Step 4**: Verified Maps & Location Services is enabled
  - If not enabled: Enabled it via App Manager
  - If not available: Checked Salesforce edition/AppExchange

**Status**: Maps is ready ✓

---

## ✅ Part 2: Create Connected App (10 min)

### Basic Info
- [ ] **Step 1**: In Setup, searched "App Manager"
- [ ] **Step 2**: Clicked "New Connected App"
- [ ] **Step 3**: Filled in basic information:
  - [ ] Connected App Name: `Property Geocoding API`
  - [ ] API Name: `Property_Geocoding_API` (auto-filled)
  - [ ] Contact Email: _________________

### OAuth Settings
- [ ] **Step 4**: Checked "Enable OAuth Settings" ✓
- [ ] **Step 5**: Entered Callback URL: `http://localhost:8080/callback`
- [ ] **Step 6**: Added OAuth Scopes (moved from left to right):
  - [ ] ✓ Access and manage your data (api)
  - [ ] ✓ Perform requests on your behalf at any time (refresh_token)
  - [ ] ✓ Provide access to your data via the Web (web)
- [ ] **Step 7**: Checked "Require Secret for Web Server Flow" ✓
- [ ] **Step 8**: Set IP Relaxation to "Relax IP restrictions" (recommended)

### Save
- [ ] **Step 9**: Clicked "Save"
- [ ] **Step 10**: Clicked "Continue" on the 2-10 minute warning
- [ ] **Step 11**: Waited 2-10 minutes for changes to take effect

**Status**: Connected App created ✓

---

## ✅ Part 3: Collect Credentials (5 min)

### Consumer Key & Secret
- [ ] **Step 1**: On Connected App detail page, found "API (Enable OAuth Settings)"
- [ ] **Step 2**: Copied Consumer Key (Client ID):
  ```
  Saved: _________________________________________________
  ```
- [ ] **Step 3**: Clicked "Click to reveal" for Consumer Secret
- [ ] **Step 4**: Copied Consumer Secret:
  ```
  Saved: _________________________________________________
  ```

### Instance URL
- [ ] **Step 5**: Copied Salesforce URL from browser:
  ```
  Example: https://your-company.my.salesforce.com
  Yours: _________________________________________________
  ```

### Security Token
- [ ] **Step 6**: Clicked profile picture → Settings
- [ ] **Step 7**: Navigated to: My Personal Information → Reset My Security Token
- [ ] **Step 8**: Clicked "Reset Security Token"
- [ ] **Step 9**: Checked email for security token
- [ ] **Step 10**: Copied security token:
  ```
  Saved: _________________________________________________
  ```

**Status**: All credentials collected ✓

---

## ✅ Part 4: Configure .env File (2 min)

- [ ] **Step 1**: Opened `backend/.env` file
- [ ] **Step 2**: Added these lines (with your actual values):
  ```bash
  SALESFORCE_INSTANCE_URL=
  SALESFORCE_CLIENT_ID=
  SALESFORCE_CLIENT_SECRET=
  SALESFORCE_USERNAME=
  SALESFORCE_PASSWORD=
  SALESFORCE_SECURITY_TOKEN=
  ```
- [ ] **Step 3**: Verified no spaces around `=` signs
- [ ] **Step 4**: Saved the file
- [ ] **Step 5**: Checked `.gitignore` includes `.env`

**Status**: Environment configured ✓

---

## ✅ Part 5: Test Connection (3 min)

- [ ] **Step 1**: Ran test command:
  ```bash
  python3 scripts/regeocode_salesforce.py --limit 5
  ```

- [ ] **Step 2**: Verified success message:
  - [ ] Saw: `✓ Salesforce authentication successful`
  - [ ] Saw: Properties being geocoded with accuracy scores
  - [ ] No error messages

**If you saw errors:**
- [ ] 401 authentication failure → Check username/password/token
- [ ] 400 invalid_client → Check CLIENT_ID and CLIENT_SECRET
- [ ] 403 Maps not available → Verify Maps is enabled

**Status**: Connection tested successfully ✓

---

## 🎉 Setup Complete!

**Final Checklist:**
- [x] Maps & Location Services enabled
- [x] Connected App created
- [x] OAuth credentials collected
- [x] Environment variables configured
- [x] Connection tested successfully

---

## 📝 Quick Reference (Fill This In)

**Your Credentials** (for quick access - keep secure!):

```
Instance URL: _________________________________________
Client ID:    _________________________________________
Username:     _________________________________________
```

**Test Command:**
```bash
python3 scripts/regeocode_salesforce.py --limit 5
```

**Main Command:**
```bash
python3 scripts/regeocode_salesforce.py --limit 100 --apply
```

**Dashboard:**
```bash
python3 scripts/geocoding_dashboard.py --watch
```

---

## 🚀 Next Steps

Now that setup is complete, you can:

1. **Compare geocoders** (recommended first step):
   ```bash
   python3 scripts/compare_geocoders.py
   ```
   This will show you how Salesforce compares to Nominatim/Mapbox

2. **Test with real data**:
   ```bash
   python3 scripts/regeocode_salesforce.py --county Dublin --limit 50
   ```

3. **Start re-geocoding** (after comparing):
   ```bash
   # Daily run (5,000 limit)
   python3 scripts/regeocode_salesforce.py --limit 5000 --apply
   ```

4. **Monitor progress**:
   ```bash
   python3 scripts/geocoding_dashboard.py --watch
   ```

---

## 🔍 Troubleshooting Quick Guide

**Problem**: Authentication fails (401)
**Fix**: Reset security token → Update `.env`

**Problem**: Invalid client (400)
**Fix**: Re-copy Consumer Key & Secret → Update `.env`

**Problem**: Maps not available (403)
**Fix**: Enable Maps in Setup → App Manager

**Problem**: IP blocked
**Fix**: Connected App → IP Relaxation → "Relax IP restrictions"

**Full guide**: See `SALESFORCE_SETUP_GUIDE.md`

---

## ✅ Success Criteria

You've successfully set up Salesforce geocoding when:
- ✓ Test command runs without errors
- ✓ Sees "Salesforce authentication successful"
- ✓ Properties are geocoded with accuracy scores
- ✓ Results show Irish coordinates (51.4-55.5 N, -10.7--5.4 W)

**If all checkmarks are ✓, you're ready to go!** 🎉
