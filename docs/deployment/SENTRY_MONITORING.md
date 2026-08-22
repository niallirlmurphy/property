# Sentry Monitoring - Valuation API

**Date:** June 23, 2026  
**Status:** ✅ Complete  
**Task:** 14

---

## What Was Added

Enhanced error tracking in `backend/valuation/api.py` with Sentry context for all failure scenarios:

### 1. Geocoding Failures (HTTP 400)
**Context captured:**
- Address input
- Eircode (if provided)
- Error message

**Tag:** `error_type: geocoding_failed`  
**Level:** warning

**Example:** "Could not geocode address: Invalid Eircode format"

---

### 2. No Comparables Found (HTTP 404)
**Context captured:**
- Address input
- Geocoded coordinates (lat/lon)
- Error message

**Tag:** `error_type: no_comparables`  
**Level:** info

**Example:** "No sales found within 20km radius"

---

### 3. Insufficient Comparables (HTTP 404)
**Context captured:**
- Address input
- Comparable count found
- Geocoded coordinates

**Tag:** `error_type: insufficient_comparables`  
**Level:** info

**Example:** "2 comparables found (need 3+)"

---

### 4. Calculation Failures (HTTP 500)
**Context captured:**
- Address input
- Eircode (if provided)
- Valuation date

**Tag:** `error_type: valuation_calculation`  
**Level:** error

**Example:** Database timeout, price index missing, etc.

---

### 5. Successful Valuations (Monitoring)
**Context captured:**
- Address input
- Estimated value
- Confidence level (high/medium/low)
- Number of comparables used
- Processing time (ms)

**Tag:** `valuation_confidence: high|medium|low`  
**Measurements:**
- `processing_time_ms`
- `n_comparables`

**Purpose:** Track performance and quality metrics

---

## Sentry Dashboard Views

### Recommended Filters

**High-priority issues:**
```
error_type:geocoding_failed OR error_type:valuation_calculation
level:error OR level:warning
```

**Data quality monitoring:**
```
error_type:no_comparables OR error_type:insufficient_comparables
```

**Performance tracking:**
```
measurement.processing_time_ms:>2000
```

**Success metrics:**
```
valuation_confidence:high
valuation_confidence:medium
valuation_confidence:low
```

---

## Example Sentry Event

```json
{
  "message": "Geocoding failed: Invalid Eircode format",
  "level": "warning",
  "tags": {
    "error_type": "geocoding_failed",
    "environment": "production"
  },
  "contexts": {
    "geocoding_failure": {
      "address": "123 Main Street",
      "eircode": "INVALID",
      "error": "Invalid Eircode format"
    }
  }
}
```

---

## Benefits

**Debugging:**
- See exact input that caused error
- Filter by error type
- Track error frequency

**Quality Monitoring:**
- Track geocoding success rate
- Monitor comparable availability by area
- Identify data gaps

**Performance:**
- Monitor response times
- Alert on slow requests (>2s)
- Track algorithm improvements

**Product Insights:**
- Which areas get most requests?
- What's the typical confidence level?
- How many comparables are being used?

---

## Configuration

Sentry is already configured in `backend/main.py`:

```python
# Sentry DSN in backend/.env
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

No additional configuration needed. Errors are automatically captured when:
1. Exception is raised
2. `sentry_sdk.capture_exception()` called
3. `sentry_sdk.capture_message()` called

---

## Next Steps

After deployment (Task 15-16):
1. Log into Sentry dashboard
2. Create alert rules:
   - Email on error rate spike
   - Slack notification for HTTP 500 errors
3. Set up weekly digest email
4. Review performance metrics after 1 week

---

**Status:** Ready for deployment ✅
