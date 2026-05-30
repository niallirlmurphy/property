# Salesforce OAuth Connected App Setup Guide

Complete step-by-step instructions for setting up Salesforce Maps & Location Services with OAuth2 authentication.

---

## Prerequisites

- Salesforce account (any edition: Developer, Professional, Enterprise, Unlimited)
- System Administrator access or equivalent permissions
- Maps & Location Services enabled (included in most editions)

**Time Required**: ~15 minutes

---

## Part 1: Enable Maps & Location Services (5 minutes)

### Step 1: Check if Maps is Already Enabled

1. **Log in to Salesforce**
   - Go to https://login.salesforce.com
   - Enter your username and password

2. **Open Setup**
   - Click the **gear icon** ⚙️ in the top-right corner
   - Select **Setup**

3. **Check Maps Status**
   - In the Quick Find box (left sidebar), type: `Maps`
   - Look for **Maps & Location Services** or **Einstein Maps and Location**
   
   ✅ If you see it listed and can access it → Maps is enabled, skip to Part 2
   
   ⚠️ If you don't see it → Continue below

### Step 2: Enable Maps & Location Services

**Option A: If Maps is Available but Not Enabled**

1. In Setup, search for: `App Manager`
2. Click **App Manager** under Apps
3. Look for **Maps** or **Einstein Maps** in the list
4. Click the dropdown arrow → **Enable**

**Option B: If Maps is Not Available**

This means your Salesforce edition doesn't include Maps by default:

1. Go to **Setup** → Quick Find → `AppExchange`
2. Or visit: https://appexchange.salesforce.com
3. Search for: `Salesforce Maps`
4. Install the appropriate Maps package for your edition

**Option C: Developer Edition (Free)**

If using a free Developer Edition:
1. Maps & Location Services should be included by default
2. If not, contact Salesforce support or use the Developer Community

---

## Part 2: Create a Connected App (10 minutes)

### Step 1: Navigate to Connected Apps

1. **Open Setup** (gear icon ⚙️ → Setup)

2. **Quick Find** (left sidebar)
   - Type: `App Manager`
   - Click **App Manager** under **Apps**

3. **Create New Connected App**
   - Click **New Connected App** button (top-right)

### Step 2: Fill in Basic Information

#### **Connected App Name** (required)
```
Property Geocoding API
```
*This is what you'll see in the App Manager list*

#### **API Name** (auto-filled)
```
Property_Geocoding_API
```
*Auto-generated from the name, you can leave as-is*

#### **Contact Email** (required)
```
your-email@example.com
```
*Use your actual email address*

#### **Description** (optional but recommended)
```
OAuth2 Connected App for property address geocoding using Maps & Location Services API
```

### Step 3: Configure API (Enable OAuth Settings)

Scroll down to **API (Enable OAuth Settings)** section:

1. **Enable OAuth Settings** ✓
   - Check this box

2. **Callback URL** (required)
   ```
   http://localhost:8080/callback
   ```
   *For server-to-server authentication, the URL doesn't matter, but it's required*

3. **Use digital signatures**
   - Leave UNCHECKED

4. **Selected OAuth Scopes** (required)
   
   Click **Add** to move these from Available to Selected:
   
   - ✅ **Access and manage your data (api)**
   - ✅ **Perform requests on your behalf at any time (refresh_token, offline_access)**
   - ✅ **Provide access to your data via the Web (web)**
   
   *These three scopes are essential for server-to-server API access*

5. **Require Secret for Web Server Flow**
   - ✓ Check this box
   - *This enables the OAuth2 password grant we'll use*

6. **Require Secret for Refresh Token Flow**
   - ✓ Check this box (if available)

### Step 4: Configure Additional Settings

Scroll down further:

#### **Refresh Token Policy** (optional)
- Leave as default: "Refresh token is valid until revoked"

#### **IP Relaxation** (recommended)
- Select: **Relax IP restrictions**
- *Allows API calls from any IP (your server IP may change)*

#### **Permitted Users** (optional)
- Leave as default: "All users may self-authorize"
- Or select "Admin approved users are pre-authorized" for tighter security

### Step 5: Save the Connected App

1. **Click "Save"** button at the bottom

2. **You'll see a warning:**
   ```
   "It will take 2-10 minutes for your changes to take effect"
   ```
   - Click **Continue**

3. **You'll be redirected to the Connected App detail page**

---

## Part 3: Retrieve API Credentials (5 minutes)

### Step 1: Get Consumer Key and Secret

After saving, you're on the Connected App detail page:

1. **Find "API (Enable OAuth Settings)" section**

2. **Consumer Key (Client ID)**
   - You'll see a long string like:
   ```
   3MVG9fTLmJ60pJ5.abc123xyz789...
   ```
   - Click **Copy** icon or select and copy the entire key
   - Save this - you'll need it as `SALESFORCE_CLIENT_ID`

3. **Consumer Secret (Client Secret)**
   - Click **Click to reveal**
   - You'll see something like:
   ```
   A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
   ```
   - Click **Copy** or copy the revealed secret
   - Save this - you'll need it as `SALESFORCE_CLIENT_SECRET`

**⚠️ IMPORTANT SECURITY NOTES:**
- Treat these like passwords - never commit them to git
- Store them securely (password manager, environment variables)
- If compromised, you can regenerate them in the Connected App settings

### Step 2: Get Your Instance URL

Your Salesforce instance URL is visible in your browser:

**Example URLs:**
```
https://your-company.my.salesforce.com        ← Use this format
https://your-company--sandbox.my.salesforce.com  ← For sandbox
https://na123.salesforce.com                  ← Legacy format (still works)
```

**To find it:**
1. Look at your browser address bar when logged into Salesforce
2. Copy everything up to `.salesforce.com` (including https://)
3. Save this as `SALESFORCE_INSTANCE_URL`

### Step 3: Get Your Security Token

If you don't have your security token:

1. **Click your profile picture** (top-right)
2. Click **Settings**
3. In the left menu: **My Personal Information** → **Reset My Security Token**
4. Click **Reset Security Token** button
5. **Check your email** - you'll receive the token within a few minutes
6. Copy the security token from the email
7. Save this as `SALESFORCE_SECURITY_TOKEN`

**Notes:**
- Security tokens are sent to your primary email address
- If you change your password, the security token is automatically reset
- Check spam folder if you don't receive it

---

## Part 4: Configure Environment Variables (2 minutes)

### Step 1: Add Credentials to .env File

Open `backend/.env` and add these lines:

```bash
# Salesforce Maps & Location Services
SALESFORCE_INSTANCE_URL=https://your-company.my.salesforce.com
SALESFORCE_CLIENT_ID=3MVG9fTLmJ60pJ5.your_actual_consumer_key_here
SALESFORCE_CLIENT_SECRET=A1B2C3D4E5F6G7H8your_actual_secret_here
SALESFORCE_USERNAME=your.email@company.com
SALESFORCE_PASSWORD=YourSalesforcePassword
SALESFORCE_SECURITY_TOKEN=AbCdEfGhIjKlMnOpQrStUvWx
```

**Replace with your actual values:**
- `SALESFORCE_INSTANCE_URL` - From browser address bar (Step 2 above)
- `SALESFORCE_CLIENT_ID` - Consumer Key from Connected App
- `SALESFORCE_CLIENT_SECRET` - Consumer Secret from Connected App
- `SALESFORCE_USERNAME` - Your Salesforce login email
- `SALESFORCE_PASSWORD` - Your Salesforce password (NOT including security token)
- `SALESFORCE_SECURITY_TOKEN` - From the email (Step 3 above)

**Security Checklist:**
- ✓ File is named `.env` (with the dot)
- ✓ File is in `backend/` directory
- ✓ File is listed in `.gitignore` (never commit it)
- ✓ No spaces around the `=` sign
- ✓ No quotes around the values (unless they contain spaces)

### Step 2: Verify .gitignore

Check that `.env` is ignored:

```bash
# In .gitignore file, ensure this line exists:
.env
*.env
backend/.env
```

If not, add it now to prevent accidental commits!

---

## Part 5: Test the Connection (3 minutes)

### Step 1: Test Authentication

Run the Salesforce geocoding script in test mode:

```bash
cd "/Users/nmurphy/claude/property price project"
python3 scripts/regeocode_salesforce.py --limit 5
```

### Step 2: Verify Success

**✅ SUCCESS looks like:**
```
Fetching properties at centroid coordinates...
Found 172 centroid coordinates

======================================================================
SALESFORCE RE-GEOCODING
======================================================================
Properties to process: 5
Mode: DRY RUN
Daily API limit: 5,000 requests

⚠️  DRY RUN MODE - No database changes will be made

✓ Salesforce authentication successful

  ✓ [1/5] 185 BRU NA GRUADAN, CASTLETROY, LIMERICK
    Accuracy: 0.95 | 52.684256,-8.577379 → 52.678123,-8.573456
  ✓ [2/5] 17 RICES CORNER, THOMOND GATE, THOMONDGATE
    Accuracy: 0.89 | 52.684256,-8.577379 → 52.679234,-8.574567
...

======================================================================
COMPLETE
======================================================================
Processed: 5
✓ Success: 5 (100.0%)
✗ Failed: 0
API requests used: 5/5,000
```

**❌ FAILURE looks like:**

**Error 1: Authentication Failed**
```
❌ Salesforce authentication failed: 401
Response: {"error":"invalid_grant","error_description":"authentication failure"}
```
**Fix**: Check username, password, and security token

**Error 2: Invalid Client**
```
❌ Salesforce authentication failed: 400
Response: {"error":"invalid_client","error_description":"client identifier invalid"}
```
**Fix**: Check CLIENT_ID and CLIENT_SECRET

**Error 3: Maps Not Available**
```
❌ Salesforce API error: 403
Response: {"errorCode":"INSUFFICIENT_ACCESS","message":"Maps & Location Services not enabled"}
```
**Fix**: Verify Maps is enabled (Part 1)

---

## Troubleshooting

### Issue: "authentication failure" (401)

**Cause**: Incorrect password or security token

**Solution:**
1. Verify your password is correct (try logging into Salesforce web)
2. Reset security token:
   - Profile → Settings → Reset My Security Token
   - Check email
   - Update `SALESFORCE_SECURITY_TOKEN` in `.env`
3. Make sure password does NOT include the security token
   - The script concatenates them automatically
   - `.env` should have them as separate variables

### Issue: "invalid_client" (400)

**Cause**: Incorrect Consumer Key or Consumer Secret

**Solution:**
1. Go to Setup → App Manager
2. Find "Property Geocoding API"
3. Click dropdown → **View**
4. Scroll to "API (Enable OAuth Settings)"
5. Copy Consumer Key again (make sure you got all of it)
6. Click "Click to reveal" for Consumer Secret
7. Update `.env` with exact values

### Issue: "IP blocked" or "Login from new location"

**Cause**: Salesforce security settings

**Solution:**
1. **Option A: Relax IP Restrictions (Recommended)**
   - Go to Connected App settings
   - Set **IP Relaxation** to "Relax IP restrictions"
   
2. **Option B: Add Your IP to Trusted List**
   - Setup → Quick Find → "Network Access"
   - Add your server's IP address

3. **Option C: Verify from Security Email**
   - Check your email for "Login from New Location"
   - Click the verification link
   - Try authentication again

### Issue: "API Not Enabled"

**Cause**: API access not enabled for your user

**Solution:**
1. Setup → Quick Find → "Permission Sets"
2. Create new permission set: "API Enabled"
3. Enable: **API Enabled** checkbox
4. Assign to your user

### Issue: Maps API Returns 403

**Cause**: Maps & Location Services not enabled or no permission

**Solution:**
1. Verify Maps is enabled (Part 1)
2. Check user permissions:
   - Setup → Users → Your User
   - Edit
   - Look for "Maps" or "Location Services" permissions
3. May need admin to grant permissions

---

## Quick Reference Card

**Save this for future reference:**

### Essential URLs

| Purpose | URL |
|---------|-----|
| Login | https://login.salesforce.com |
| Setup | Click gear ⚙️ → Setup |
| App Manager | Setup → Quick Find → "App Manager" |
| Connected App | App Manager → "Property Geocoding API" |
| Reset Token | Profile → Settings → Reset My Security Token |

### Environment Variables Checklist

```bash
✓ SALESFORCE_INSTANCE_URL    # From browser: https://your-company.my.salesforce.com
✓ SALESFORCE_CLIENT_ID        # From Connected App: Consumer Key
✓ SALESFORCE_CLIENT_SECRET    # From Connected App: Consumer Secret (click to reveal)
✓ SALESFORCE_USERNAME         # Your Salesforce email
✓ SALESFORCE_PASSWORD         # Your password (NOT including token)
✓ SALESFORCE_SECURITY_TOKEN   # From email after reset
```

### Quick Test Command

```bash
python3 scripts/regeocode_salesforce.py --limit 5
```

Expected: `✓ Salesforce authentication successful`

---

## Next Steps

✅ **Setup Complete!** Now you can:

1. **Test with real data:**
   ```bash
   python3 scripts/regeocode_salesforce.py --limit 10
   ```

2. **Compare with other geocoders:**
   ```bash
   python3 scripts/compare_geocoders.py
   ```

3. **Start re-geocoding:**
   ```bash
   # Dry-run first
   python3 scripts/regeocode_salesforce.py --limit 100
   
   # Then apply
   python3 scripts/regeocode_salesforce.py --limit 100 --apply
   ```

4. **Monitor progress:**
   ```bash
   python3 scripts/geocoding_dashboard.py --watch
   ```

---

## Security Best Practices

✅ **DO:**
- Store credentials in `.env` file
- Add `.env` to `.gitignore`
- Use strong Salesforce password
- Enable 2FA on Salesforce account
- Regularly rotate secrets
- Monitor API usage

❌ **DON'T:**
- Commit credentials to git
- Share credentials in chat/email
- Use production credentials for testing
- Hard-code credentials in scripts
- Reuse passwords across services

---

## Support Resources

- **Salesforce Help**: https://help.salesforce.com
- **Developer Docs**: https://developer.salesforce.com/docs
- **OAuth2 Guide**: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm
- **Maps & Location**: https://help.salesforce.com/s/articleView?id=sf.maps_about.htm
- **Community**: https://trailblazer.salesforce.com/ideaSearch

For project-specific help:
- Review `SALESFORCE_GEOCODING.md`
- Check `scripts/README.md`
- Run: `python3 scripts/geocoding_dashboard.py`

---

**Setup Complete! 🎉**

You're now ready to use Salesforce geocoding for your property addresses.
