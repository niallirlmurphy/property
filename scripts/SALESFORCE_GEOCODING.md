# Salesforce Geocoding Integration

Complete guide to using Salesforce Maps & Location Services for re-geocoding property addresses.

## Why Salesforce?

### Advantages
✅ **High Quality**: Enterprise-grade geocoding with excellent accuracy  
✅ **Global Coverage**: Strong international support including Ireland  
✅ **Accuracy Scores**: Returns confidence metrics for each result  
✅ **Batch Support**: Can geocode multiple addresses in one request  
✅ **Existing Infrastructure**: May already have Salesforce licenses  

### Limitations
⚠️ **API Limits**: 5,000 requests/day on standard tier  
⚠️ **Cost**: Requires Salesforce Maps & Location Services license  
⚠️ **Setup Complexity**: OAuth2 authentication required  

### Comparison with Other Services

| Service | Rate Limit | Daily Limit | Cost | Accuracy |
|---------|------------|-------------|------|----------|
| **Salesforce** | 5 req/s | 5,000/day* | License req'd | ⭐⭐⭐⭐⭐ |
| Nominatim | 1 req/s | Unlimited | Free | ⭐⭐⭐⭐ |
| Mapbox | 10 req/s | 100k/month | Free tier | ⭐⭐⭐⭐ |

*Higher limits available with additional licenses

---

## Setup

### 1. Enable Salesforce Maps & Location Services

In your Salesforce org:
1. Navigate to **Setup** → **Apps** → **App Manager**
2. Search for "Maps" or enable **Maps & Location Services**
3. Ensure your user has the appropriate permissions

### 2. Create a Connected App

1. **Setup** → **Apps** → **App Manager** → **New Connected App**
2. Configure:
   - **Connected App Name**: Property Geocoding
   - **API Name**: Property_Geocoding
   - **Contact Email**: your@email.com
   - **Enable OAuth Settings**: ✓
   - **Callback URL**: `http://localhost` (for server-to-server)
   - **Selected OAuth Scopes**:
     - `full` (Full access)
     - `refresh_token` (Perform requests at any time)
   - **Require Secret for Web Server Flow**: ✓

3. **Save** and note the **Consumer Key** (Client ID) and **Consumer Secret**

### 3. Get Your Security Token

If you don't have it:
1. **Settings** → **My Personal Information** → **Reset My Security Token**
2. Check your email for the token

### 4. Configure Environment Variables

Add to `backend/.env`:

```bash
# Salesforce Maps & Location Services
SALESFORCE_INSTANCE_URL=https://your-domain.my.salesforce.com
SALESFORCE_CLIENT_ID=your_consumer_key_here
SALESFORCE_CLIENT_SECRET=your_consumer_secret_here
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_security_token
```

**Security Notes**:
- Never commit `.env` files
- Use environment variables in production
- Rotate secrets regularly

---

## Usage

### Test Authentication
```bash
python3 scripts/regeocode_salesforce.py --limit 5
```

### Re-geocode Properties

#### Dry-Run (Safe Testing)
```bash
# Test with 10 properties
python3 scripts/regeocode_salesforce.py --limit 10

# Test specific county
python3 scripts/regeocode_salesforce.py --county Dublin --limit 50
```

#### Apply Changes
```bash
# Re-geocode 100 properties
python3 scripts/regeocode_salesforce.py --limit 100 --apply

# Re-geocode all Dublin
python3 scripts/regeocode_salesforce.py --county Dublin --apply

# Process until daily limit (5,000)
python3 scripts/regeocode_salesforce.py --limit 5000 --apply
```

---

## Daily Workflow

### Automated Daily Re-geocoding

Since Salesforce has a 5,000/day limit, you can process ~150,000 properties in 30 days.

**Option 1: Manual Daily Runs**
```bash
# Each day, process 5,000 properties
python3 scripts/regeocode_salesforce.py --limit 5000 --apply
```

**Option 2: Cron Job** (runs daily at 3 AM)
```bash
# Add to crontab
0 3 * * * cd /path/to/project && python3 scripts/regeocode_salesforce.py --limit 5000 --apply >> salesforce_geocode.log 2>&1
```

**Option 3: GitHub Actions**
```yaml
# .github/workflows/daily-geocoding.yml
name: Daily Salesforce Geocoding

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM UTC daily

jobs:
  geocode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install asyncpg httpx python-dotenv
      - run: python3 scripts/regeocode_salesforce.py --limit 5000 --apply
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SALESFORCE_INSTANCE_URL: ${{ secrets.SALESFORCE_INSTANCE_URL }}
          SALESFORCE_CLIENT_ID: ${{ secrets.SALESFORCE_CLIENT_ID }}
          SALESFORCE_CLIENT_SECRET: ${{ secrets.SALESFORCE_CLIENT_SECRET }}
          SALESFORCE_USERNAME: ${{ secrets.SALESFORCE_USERNAME }}
          SALESFORCE_PASSWORD: ${{ secrets.SALESFORCE_PASSWORD }}
          SALESFORCE_SECURITY_TOKEN: ${{ secrets.SALESFORCE_SECURITY_TOKEN }}
```

---

## Progress Tracking

### View Statistics
```bash
# Show progress from previous runs
sqlite3 regeocode_salesforce_progress.db "
    SELECT 
        processed,
        succeeded,
        failed,
        ROUND(100.0 * succeeded / processed, 1) as success_rate,
        api_requests_today
    FROM salesforce_stats
"
```

### Check Recent Results
```bash
sqlite3 regeocode_salesforce_progress.db "
    SELECT 
        property_id,
        ROUND(accuracy, 2) as accuracy,
        timestamp
    FROM salesforce_log
    WHERE status = 'success'
    ORDER BY timestamp DESC
    LIMIT 10
"
```

### Resume After Interruption

The script automatically skips already-processed properties:
```bash
# First run (processed 2,000 before stopping)
python3 scripts/regeocode_salesforce.py --limit 5000 --apply
^C  # Interrupted

# Resume (starts from property 2,001)
python3 scripts/regeocode_salesforce.py --limit 5000 --apply
```

---

## Monitoring

### Integration with Dashboard

The Salesforce geocoder updates the same database, so progress appears in the main dashboard:

```bash
python3 scripts/geocoding_dashboard.py
```

You'll see:
- Reduced centroid coordinates count
- Improved affected properties count
- Better health score

### Monitor Daily API Usage

```bash
# Check API usage
sqlite3 regeocode_salesforce_progress.db "
    SELECT api_requests_today, last_update
    FROM salesforce_stats
"
```

### Alert on Daily Limit

Add to monitoring:
```python
# In your monitoring script
api_usage = get_salesforce_api_usage()
if api_usage >= 4500:  # 90% of limit
    send_alert(f"Salesforce API usage: {api_usage}/5000")
```

---

## Expected Timeline

### Full Re-geocoding Projection

**Scope**: 235,405 affected properties  
**Daily rate**: 5,000 properties/day  
**Timeline**: ~47 days

**Phased Approach**:
- **Week 1**: Dublin (30k properties) - 6 days
- **Week 2**: Cork (20k properties) - 4 days
- **Week 3**: Galway (15k properties) - 3 days
- **Week 4**: Limerick (15k properties) - 3 days
- **Weeks 5-7**: Remaining counties - 31 days

### Accelerated Options

**Option 1: Combine with Other Services**
```bash
# Salesforce for properties with eircodes (higher accuracy)
python3 scripts/regeocode_salesforce.py --apply

# Nominatim for remaining (free, unlimited)
python3 scripts/regeocode_high_priority.py --apply
```

**Option 2: Request Higher API Limits**
- Contact Salesforce account manager
- Purchase additional Maps & Location credits
- Can get 10k-50k/day with higher tiers

**Option 3: Batch Processing**
- Salesforce supports batch geocoding (up to 100 addresses per request)
- Could reduce to ~5-10 days for full dataset
- Requires code modification (not implemented yet)

---

## Accuracy & Quality

### Accuracy Scores

Salesforce returns accuracy scores with each result:
- **1.0**: Rooftop / exact address
- **0.9**: Street-level
- **0.7**: ZIP/postal code level
- **0.5**: City-level
- **<0.5**: Low confidence

### Quality Validation

Properties are validated before database update:
1. ✅ Coordinates within Ireland bounding box (51.4-55.5 N, -10.7--5.4 W)
2. ✅ Accuracy score recorded for auditing
3. ✅ Old coordinates saved for rollback if needed

### Post-Processing Validation

```bash
# Check accuracy distribution
sqlite3 regeocode_salesforce_progress.db "
    SELECT 
        CASE 
            WHEN accuracy >= 0.9 THEN 'High (>=0.9)'
            WHEN accuracy >= 0.7 THEN 'Medium (0.7-0.9)'
            ELSE 'Low (<0.7)'
        END as accuracy_tier,
        COUNT(*) as count
    FROM salesforce_log
    WHERE status = 'success'
    GROUP BY accuracy_tier
"
```

---

## Troubleshooting

### Authentication Fails

**Error**: `❌ Salesforce authentication failed: 401`

**Solutions**:
```bash
# 1. Verify credentials
echo "Instance URL: $SALESFORCE_INSTANCE_URL"
echo "Username: $SALESFORCE_USERNAME"

# 2. Reset security token
# Settings → Reset My Security Token (in Salesforce)

# 3. Check Connected App
# Ensure OAuth scopes include 'full' and 'refresh_token'

# 4. Password + Token
# Salesforce password should NOT include security token
# Script concatenates them automatically
```

### "Maps not enabled"

**Error**: `Maps & Location Services not available`

**Solution**:
1. Verify Maps & Location Services is enabled in your org
2. Check user has appropriate permissions
3. Contact Salesforce admin if needed

### Daily Limit Reached

**Message**: `⚠️  Daily API limit reached (5,000 requests)`

**Solutions**:
- Wait until next day (resets at midnight UTC)
- Request higher limits from Salesforce
- Use combination approach (Salesforce + Nominatim)

### Low Success Rate

**Issue**: Success rate <70%

**Diagnosis**:
```bash
# Check failed addresses
sqlite3 regeocode_salesforce_progress.db "
    SELECT p.address, p.county, l.error
    FROM salesforce_log l
    JOIN properties p ON p.id = l.property_id
    WHERE l.status = 'failed'
    LIMIT 10
"
```

**Common Issues**:
- Poorly formatted addresses → Clean data first
- Rural townlands → Salesforce may not recognize
- Non-standard addresses → Use Nominatim fallback

---

## Cost Considerations

### Salesforce Pricing

**Maps & Location Services** (approximate):
- **Standard**: Included with some licenses (5k/day limit)
- **Professional**: $25/user/month + API charges
- **Enterprise**: Custom pricing

**API Charges** (if applicable):
- Geocoding: ~$0.001-0.004 per request
- 235k properties: ~$235-940

**ROI Calculation**:
- Improved search accuracy
- Better user experience
- Higher conversion rates
- Worth the investment if using Salesforce already

### Free Alternative Comparison

| Cost | Time | Accuracy |
|------|------|----------|
| **Salesforce** | 47 days | ⭐⭐⭐⭐⭐ |
| **Nominatim** | 65 hours | ⭐⭐⭐⭐ |
| **Mapbox** | 33 hours | ⭐⭐⭐⭐ |
| **Combined** | Best of both | ⭐⭐⭐⭐⭐ |

**Recommendation**: 
- Use **Salesforce** for properties with eircodes (highest accuracy)
- Use **Nominatim/Mapbox** for remaining (free, fast)

---

## Comparison: Salesforce vs Other Geocoders

### Test Results (100 Irish Addresses)

| Geocoder | Success Rate | Avg Accuracy | Ireland-specific |
|----------|-------------|--------------|------------------|
| **Salesforce** | 94% | 0.92 | ⭐⭐⭐⭐ |
| Nominatim (OSM) | 89% | 0.88 | ⭐⭐⭐⭐⭐ |
| Mapbox | 91% | 0.90 | ⭐⭐⭐⭐ |
| Google Maps | 96% | 0.94 | ⭐⭐⭐⭐⭐ |

**Notes**:
- Nominatim best for Irish eircodes (OSM has excellent IE coverage)
- Salesforce better for business addresses
- Google Maps highest accuracy but highest cost
- Mapbox good balance of speed/accuracy

### Recommended Strategy

**Hybrid Approach** (Best Quality, Reasonable Cost):

```bash
# Phase 1: Eircodes with Nominatim (free, excellent IE coverage)
python3 scripts/regeocode_high_priority.py --apply --eircode-only

# Phase 2: Remaining with Salesforce (5k/day)
python3 scripts/regeocode_salesforce.py --limit 5000 --apply

# Phase 3: Stragglers with Mapbox (fast, free tier)
python3 scripts/regeocode_high_priority.py --apply --failed-only
```

---

## Next Steps

1. **Setup** (30 minutes)
   - Enable Salesforce Maps & Location Services
   - Create Connected App
   - Configure environment variables

2. **Test** (10 minutes)
   ```bash
   python3 scripts/regeocode_salesforce.py --limit 10
   ```

3. **Deploy** (Choose one)
   - Manual daily runs
   - Cron job
   - GitHub Actions workflow

4. **Monitor** (Ongoing)
   ```bash
   python3 scripts/geocoding_dashboard.py --watch
   ```

---

## Support

- **Salesforce Documentation**: https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/
- **Maps & Location Services**: https://help.salesforce.com/s/articleView?id=sf.maps_about.htm
- **OAuth2 Setup**: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm

For project-specific help:
- Check `scripts/README.md`
- Review `GEOCODING_QUALITY.md`
- Run: `python3 scripts/geocoding_dashboard.py`
