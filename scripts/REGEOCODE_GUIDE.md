# Re-geocoding Guide

Complete guide to re-geocoding HIGH priority properties and monitoring progress.

## Quick Start

```bash
# 1. View current state
python3 scripts/geocoding_dashboard.py

# 2. Test re-geocoding (dry-run, 50 properties)
python3 scripts/regeocode_high_priority.py --limit 50

# 3. Apply re-geocoding (start small)
python3 scripts/regeocode_high_priority.py --limit 100 --apply

# 4. Monitor progress
python3 scripts/geocoding_dashboard.py --watch

# 5. Run tests
pytest tests/test_data_quality.py -v
```

## Current Status (2026-05-18)

### Problem Scale
- **172 centroid coordinates** with 100+ addresses each
- **235,405 properties affected** (30% of all geocoded properties!)
- **Top offender**: Limerick with 7,867 addresses at one point

### Progress
- ✅ Nobber, Meath: FIXED (27 properties corrected)
- 🟡 Re-geocoding infrastructure: READY
- 🔴 Bulk re-geocoding: NOT STARTED

---

## Re-geocoding Script: `regeocode_high_priority.py`

### Features
✅ **Resumable**: Tracks progress in SQLite, can resume after interruption  
✅ **Rate-limited**: Respects API limits (Nominatim: 1 req/s, Mapbox: 10 req/s)  
✅ **Prioritized**: Processes properties with eircodes first (easiest to geocode)  
✅ **Safe**: Dry-run by default, validates coordinates are in Ireland  
✅ **Batched**: Can process by county for efficiency  

### Usage

#### Dry-Run (Test Mode)
```bash
# Test with 10 properties
python3 scripts/regeocode_high_priority.py --limit 10

# Test specific county
python3 scripts/regeocode_high_priority.py --county Dublin --limit 50

# See what would be done
python3 scripts/regeocode_high_priority.py --limit 100
```

#### Apply Changes
```bash
# Re-geocode 100 properties
python3 scripts/regeocode_high_priority.py --limit 100 --apply

# Re-geocode all Dublin properties
python3 scripts/regeocode_high_priority.py --county Dublin --apply

# Re-geocode all HIGH priority (WARNING: 235k properties, takes hours)
python3 scripts/regeocode_high_priority.py --apply
```

#### Check Progress
```bash
# View statistics from previous runs
python3 scripts/regeocode_high_priority.py --stats

# Query the progress database
sqlite3 regeocode_progress.db "
    SELECT status, COUNT(*), AVG(new_lat IS NOT NULL)
    FROM regeocode_log
    GROUP BY status
"

# See recent successes
sqlite3 regeocode_progress.db "
    SELECT property_id, method, timestamp
    FROM regeocode_log
    WHERE status = 'success'
    ORDER BY timestamp DESC
    LIMIT 10
"
```

### Geocoding Strategy

The script tries multiple methods in order:

1. **Nominatim with eircode** (best accuracy)
   - If property has eircode: search for eircode
   - OSM has good Irish eircode coverage
   - Restricted to Ireland with bounding box

2. **Nominatim with full address**
   - Search: "address, county, Ireland"
   - Country code: IE
   - Bounded to Ireland

3. **Mapbox** (if MAPBOX_TOKEN set)
   - Better for street addresses without eircodes
   - Faster rate limits
   - Requires API key in backend/.env

### Expected Success Rates

Based on initial testing:
- **With eircode**: ~90% success rate
- **Street addresses (no eircode)**: ~60% success rate
- **Rural townlands (no eircode)**: ~40% success rate

### Performance

- **With Nominatim only**: ~1 property/second (3,600/hour)
- **With Mapbox fallback**: ~2 properties/second (7,200/hour)
- **To re-geocode 235k properties**: ~65 hours (Nominatim only) or ~33 hours (with Mapbox)

### Recommendations

**Phase 1: Quick Wins** (1-2 hours)
```bash
# Counties with highest impact, properties with eircodes only
python3 scripts/regeocode_high_priority.py --county Dublin --apply
python3 scripts/regeocode_high_priority.py --county Cork --apply
python3 scripts/regeocode_high_priority.py --county Galway --apply
python3 scripts/regeocode_high_priority.py --county Limerick --apply
```

**Phase 2: Bulk Processing** (overnight)
```bash
# All HIGH priority properties
nohup python3 scripts/regeocode_high_priority.py --apply > regeocode.log 2>&1 &

# Monitor progress in another terminal
tail -f regeocode.log
# OR
python3 scripts/geocoding_dashboard.py --watch
```

**Phase 3: Validation** (1 hour)
```bash
# Run tests
pytest tests/test_data_quality.py -v

# Check dashboard
python3 scripts/geocoding_dashboard.py

# Verify specific areas
# (search for properties in known problem areas)
```

---

## Monitoring Dashboard: `geocoding_dashboard.py`

Real-time monitoring of geocoding quality.

### Usage

```bash
# One-time snapshot
python3 scripts/geocoding_dashboard.py

# Auto-refresh every 60 seconds
python3 scripts/geocoding_dashboard.py --watch
```

### Dashboard Sections

1. **Overall Statistics**: Total properties, geocoded %, missing coords
2. **Centroid Issues**: HIGH/MEDIUM priority counts, affected properties
3. **Top 5 Problem Coordinates**: Worst offenders
4. **Re-geocoding Progress**: Success rate, processed count
5. **Known Problem Locations**: Nobber and other tracked fixes
6. **Status Summary**: Health score and alerts

### Health Scores

- 🟢 **EXCELLENT**: No major issues
- 🟡 **GOOD**: Minor issues, monitoring recommended
- 🟠 **FAIR**: Some issues need attention
- 🔴 **NEEDS ATTENTION**: Multiple issues require action

---

## Test Suite Monitoring

### New Tests Added

1. **`test_duplicate_geocodes_centroid_detection`**
   - Threshold: Max 50 centroid coordinates
   - Currently: **FAILING** (172 found)
   - Will pass after re-geocoding

2. **`test_medium_priority_clusters`**
   - Threshold: Max 200 medium clusters
   - Currently: **FAILING** (5,287 found)
   - Informational - many are legitimate (apartment buildings)

3. **`test_regeocode_progress`**
   - Threshold: Min 70% success rate
   - Currently: **PASSING** (100% on 10 properties)
   - Tracks ongoing re-geocoding efforts

4. **`test_known_problem_locations`**
   - Checks Nobber coordinates
   - Currently: **PASSING** ✓
   - Will add more locations as issues are discovered

5. **`test_geocoding_improvement_trend`**
   - Tracks progress over time
   - Baseline: 50 centroids, 150k affected (2025-05-18)
   - Currently: 172 centroids, 235k affected (regression from initial count)

### Running Tests

```bash
# All data quality tests
pytest tests/test_data_quality.py -v

# Specific test
pytest tests/test_data_quality.py::test_duplicate_geocodes_centroid_detection -v

# With detailed output
pytest tests/test_data_quality.py -v -s

# Generate HTML report
pytest tests/test_data_quality.py --html=report.html
```

### CI/CD Integration

GitHub Actions workflow created at `.github/workflows/data-quality-tests.yml`:

- **Triggers**:
  - Daily at 2 AM UTC (scheduled)
  - On push to main (if data files change)
  - Manual trigger (workflow_dispatch)

- **Actions**:
  - Runs full test suite
  - Creates GitHub issue if tests fail
  - Uploads test results as artifacts

**Setup**:
1. Add `DATABASE_URL` to GitHub Secrets
2. Workflow will run automatically

---

## Progress Tracking

### SQLite Database: `regeocode_progress.db`

Tracks all re-geocoding attempts.

**Tables**:
- `regeocode_log`: Individual property results
- `session_stats`: Aggregate statistics

**Queries**:

```sql
-- Overall progress
SELECT * FROM session_stats;

-- Success rate by method
SELECT method, COUNT(*), 100.0*COUNT(*)/SUM(COUNT(*)) OVER () as pct
FROM regeocode_log
WHERE status = 'success'
GROUP BY method;

-- Recent failures
SELECT property_id, error
FROM regeocode_log
WHERE status = 'failed'
ORDER BY timestamp DESC
LIMIT 10;

-- Properties by old coordinate (which centroid)
SELECT old_lat, old_lon, COUNT(*)
FROM regeocode_log
WHERE status = 'success'
GROUP BY old_lat, old_lon
ORDER BY COUNT(*) DESC;
```

### Resumability

The script automatically skips properties already processed:
```bash
# First run (interrupted after 1000)
python3 scripts/regeocode_high_priority.py --apply
^C  # Ctrl+C

# Resume (skips first 1000)
python3 scripts/regeocode_high_priority.py --apply
# Continues from property 1001
```

To start fresh:
```bash
rm regeocode_progress.db
```

---

## Troubleshooting

### Issue: Low Success Rate (<70%)

**Possible causes**:
- API rate limiting
- Incorrect address formats
- Missing MAPBOX_TOKEN

**Solutions**:
```bash
# Check API responses
python3 scripts/regeocode_high_priority.py --limit 10 2>&1 | grep error

# Add Mapbox fallback
export MAPBOX_TOKEN="your_token_here"
# Or add to backend/.env

# Try specific county known to have good data
python3 scripts/regeocode_high_priority.py --county Dublin --limit 50
```

### Issue: Script Slow/Stalled

**Causes**:
- Rate limiting (Nominatim is 1 req/s)
- Database connection issues

**Solutions**:
```bash
# Check if making progress
tail -f regeocode.log

# Use dashboard to monitor
python3 scripts/geocoding_dashboard.py --watch

# Check database connectivity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM properties"
```

### Issue: Coordinates Still Wrong After Re-geocoding

**Diagnosis**:
```bash
# Check what method was used
sqlite3 regeocode_progress.db "
    SELECT property_id, old_lat, old_lon, new_lat, new_lon, method
    FROM regeocode_log
    WHERE property_id = 12345
"

# Check if coordinate is in Ireland
SELECT latitude, longitude FROM properties WHERE id = 12345;
```

**Solutions**:
- Manually verify address
- Add to fix_specific_locations.py script
- Report to geocoding service if their data is wrong

### Issue: Tests Failing After Re-geocoding

This is expected! Tests will fail until enough properties are re-geocoded.

**Expected timeline**:
- After 1,000 properties: Still failing
- After 10,000 properties: Getting better
- After 50,000 properties: Should start passing
- After 100,000+ properties: Clean pass

---

## Next Steps

### Immediate (Next 2 hours)
1. ✅ Review dashboard and understand scope
2. ⏳ Test re-geocoding with `--limit 100`
3. ⏳ Apply fixes to one county (Dublin recommended)
4. ⏳ Verify improvements in dashboard

### Short-term (This week)
1. ⏳ Re-geocode all HIGH priority properties with eircodes
2. ⏳ Set up CI/CD monitoring
3. ⏳ Document any new problem locations discovered
4. ⏳ Reach 50% re-geocoding completion

### Medium-term (This month)
1. ⏳ Complete HIGH priority re-geocoding
2. ⏳ Review MEDIUM priority clusters
3. ⏳ Address remaining properties without eircodes
4. ⏳ Achieve <30 centroid coordinates (passing tests)

### Long-term (Ongoing)
1. ⏳ Monitor for regressions (daily CI/CD)
2. ⏳ Improve geocoding pipeline to prevent future issues
3. ⏳ Add validation before caching geocode results
4. ⏳ Build alerting for geocoding quality degradation

---

## API Keys & Rate Limits

### Nominatim (OpenStreetMap)
- **Cost**: Free
- **Rate limit**: 1 request/second
- **Usage policy**: https://operations.osmfoundation.org/policies/nominatim/
- **Configuration**: None needed (public endpoint)
- **Best for**: Eircodes, Irish addresses

### Mapbox
- **Cost**: Free tier (100k requests/month), then $0.75/1k
- **Rate limit**: 600 requests/minute (10/s)
- **Configuration**: Set `MAPBOX_TOKEN` in `backend/.env`
- **Best for**: Street addresses, faster processing
- **Get token**: https://account.mapbox.com/

### Recommended Setup
```bash
# backend/.env
DATABASE_URL=postgresql://...
MAPBOX_TOKEN=pk.eyJ1...  # Optional but recommended
```

---

## Support

- **Dashboard not working?** Check `DATABASE_URL` in `backend/.env`
- **Tests not running?** Ensure `tests/.env.test` has `DATABASE_URL`
- **Re-geocoding failing?** Check internet connection and API rate limits
- **Need help?** Check `scripts/README.md` or `GEOCODING_QUALITY.md`
