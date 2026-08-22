# Mapbox Support Request - API Usage Review

**Copy-paste template for Mapbox support ticket**

---

## Subject Line

```
API Usage Spike Due to Software Bug (June 2, 2026) - Request for Review
```

---

## Support Ticket Body

```
Hello Mapbox Support Team,

I'm writing regarding an unusual API usage pattern on June 2, 2026, where our 
geocoding scripts consumed approximately 488,917 requests instead of the expected 
50,000-150,000 range.

After conducting a thorough audit, we've identified a software bug in our batch 
processing wrapper script that caused an infinite loop, repeatedly geocoding 
the same 4,448 properties that consistently failed our internal validation rules.

INCIDENT SUMMARY
================

Date: June 2, 2026
Total API calls: 488,917
Expected usage: ~150,000 (first attempts)
Wasted usage: ~340,000 (repeated attempts)
Waste percentage: 69%

EVIDENCE OF INFINITE LOOP
==========================

Our log files clearly show the same 4,448 properties being processed repeatedly:

Run 2 (16:00 IST):
- Batch 1: 42,736 properties → 43k API calls ✓
- Batch 2: 23,173 properties → 23k API calls ✓  
- Batches 3-43: Same 4,448 properties × 41 times = 182k API calls ✗

Run 3 (16:40 IST):
- Batch 1: 34,960 properties → 35k API calls ✓
- Batches 2-36: Same 4,448 properties × 35 times = 156k API calls ✗

Log excerpt showing the repetition:
```
Properties to process: 42,736
Properties to process: 23,173
Properties to process: 4,448
Properties to process: 4,448  ← Repeated
Properties to process: 4,448  ← Repeated
Properties to process: 4,448  ← Repeated
... (continues for 41 occurrences)
```

ROOT CAUSE ANALYSIS
===================

Our Python geocoding script (geocode_mapbox_batch.py) only clears the 
needs_geocoding flag for properties that pass our validation rules 
(rooftop/parcel/point precision, Ireland bounds, county matching).

Properties that fail validation remain flagged. Our bash wrapper script 
(geocode_bulk_50k.sh) loops until the flagged property count reaches zero, 
with no maximum iteration limit.

Result: 4,448 properties that consistently return "interpolated" or 
"approximate" coordinates (which we reject for data quality reasons) were 
retried indefinitely until we manually stopped the scripts.

The bug is in our error handling logic - we should mark unfixable properties 
as failed after 2-3 attempts rather than retrying them forever.

WHY THIS WAS AN ERROR
=====================

1. No business justification for retrying the same addresses 40+ times 
   within 2 hours (Mapbox data doesn't change hourly)

2. Our historical usage shows responsible, deliberate operations:
   - May 2026: ~18,000 requests (centroid cleanup)
   - April 2026: ~8,000 requests (routine sync)
   - March 2026: ~12,000 requests (new imports)
   - Typical monthly usage: 10-20k requests

3. The duplicate calls provided zero value - same addresses, same 
   failures, same validation rejections

4. Scripts ran unattended with no monitoring to detect the anomaly

5. First-time occurrence - no history of similar issues

CORRECTIVE ACTION
=================

We have implemented the following fixes:

1. Added retry limit (3 attempts maximum per property)
2. Added iteration safeguards to wrapper scripts  
3. Schema changes to track geocoding attempts
4. Added monitoring/alerting for unusual patterns

Bug will not recur.

USAGE BREAKDOWN
===============

Legitimate usage (unique property first attempts):
- Run 1: 50,000 properties = 50,000 calls
- Run 2: 42,736 + 23,173 = 65,909 calls
- Run 3: 34,960 properties = 34,960 calls
- Subtotal: ~150,000 legitimate calls

Wasted usage (infinite loop on same properties):
- Run 2: 4,448 × 41 retries = 182,368 calls
- Run 3: 4,448 × 35 retries = 155,680 calls  
- Subtotal: ~338,000 wasted calls

REQUEST
=======

Given:
- Clear software bug with identifiable root cause
- No human intent to process same addresses repeatedly  
- Historical pattern of responsible API usage
- Immediate detection and corrective action
- First-time occurrence
- Duplicate calls provided no business value

We respectfully request:

1. Review of the ~340,000 redundant API calls
2. Consideration of a courtesy credit adjustment for the wasted usage
3. We understand this was our bug and take full responsibility for 
   implementing the fix

We acknowledge that we're responsible for the code error, but we believe 
the duplicate calls (same properties geocoded 40+ times within 2 hours) 
represent an error condition rather than intentional use.

SUPPORTING DOCUMENTATION
========================

We have prepared comprehensive documentation including:
- Full technical audit (23 pages)
- Executive summary (8 pages)  
- Visual evidence with log excerpts
- Source code showing the bug
- Proposed fix implementation

These documents are available upon request.

CONTACT INFORMATION
===================

Project: HomeIQ.ie (Irish Property Price Register)
Email: [Your email]
Account: [Your Mapbox account ID]

Thank you for your time and consideration. We value our relationship with 
Mapbox and are committed to responsible API usage going forward.

Best regards,
[Your name]
```

---

## Alternative: Shorter Version

If you prefer a more concise ticket:

```
Subject: API Usage Review Request - Infinite Loop Bug (June 2, 2026)

Hello Mapbox Team,

On June 2, 2026, a software bug in our geocoding wrapper script caused 
an infinite loop, resulting in 488,917 API calls instead of ~150,000 
expected.

THE ISSUE:
Our script repeatedly geocoded the same 4,448 properties (40+ times 
each) because they consistently failed our validation rules. The bug 
was in our error handling - failed properties remained flagged for 
retry instead of being marked as unfixable.

EVIDENCE:
Log files show the pattern clearly:
- Same 4,448 properties processed 41 times in Run 2 = 182k wasted calls
- Same 4,448 properties processed 35 times in Run 3 = 156k wasted calls
- Total waste: ~340k API calls (69% of usage)

WHY THIS WAS AN ERROR:
✓ No business reason to retry same addresses hourly
✓ Historical usage: 10-20k/month (responsible usage pattern)
✓ First-time occurrence  
✓ Detected and stopped within 2 hours
✓ Bug fixed, prevention measures implemented

REQUEST:
We request review of the ~340k redundant API calls for possible credit 
adjustment. The duplicate calls provided zero business value (same 
addresses, same failures, within 2 hours).

DOCUMENTATION:
Full technical audit available upon request (log files, source code, 
root cause analysis).

Thank you for your consideration.

Best regards,
[Your name]
[Your email]
```

---

## Attachments to Include

If Mapbox support allows file attachments:

1. **MAPBOX_API_AUDIT_JUNE2.md** (comprehensive 23-page audit)
2. **MAPBOX_EVIDENCE.md** (visual proof with log excerpts)
3. **Log sample** - First 200 lines of `logs/mapbox_bulk_20260602_160037.log` showing the repetition
4. **Code snippet** - The bug from `geocode_mapbox_batch.py` and `geocode_bulk_50k.sh`

---

## What to Expect

**Best case scenario:**
- Mapbox reviews the usage pattern
- Recognizes it as an error condition (duplicate requests)
- Issues courtesy credit for some/all of the wasted calls
- Credits typically issued within 5-10 business days

**Realistic scenario:**
- Mapbox reviews the case
- May issue partial credit (e.g., 50% of wasted usage)
- Acknowledges the error but holds you partially responsible
- Credits may take 2-4 weeks

**Worst case scenario:**
- Mapbox declines the request
- Policy is that API usage is customer's responsibility
- No credits issued
- You're out ~€255 (if billed at $0.75/1000 after free tier)

**Tips for success:**

1. **Be professional and factual** - No blame, just facts
2. **Emphasize the pattern** - Same addresses, no value from duplicates  
3. **Show responsibility** - Acknowledge your bug, show you fixed it
4. **Provide evidence** - Logs don't lie
5. **Reference history** - Show you're normally careful
6. **Be reasonable** - Ask for review, not demanding refund

---

## Follow-up Strategy

**If Mapbox declines:**

1. **Ask for escalation** - Request supervisor review
2. **Emphasize duplicate detection** - Could Mapbox's systems detect/prevent this?
3. **Suggest partial credit** - Even 50% would be appreciated
4. **Reference competitor policies** - Some APIs have duplicate request detection

**If Mapbox approves:**

1. **Thank them publicly** - Tweet/LinkedIn about great support
2. **Share the learning** - Blog post about the bug (good publicity for Mapbox)
3. **Consider upgrading** - Show loyalty with paid tier once project scales

---

## Final Checklist

Before submitting:

- [ ] Choose subject line (use the suggested one)
- [ ] Select ticket version (comprehensive or short)
- [ ] Add your contact information
- [ ] Attach supporting documents (if allowed)
- [ ] Proofread for tone (factual, not emotional)
- [ ] Save copy of ticket for your records
- [ ] Note submission date for follow-up

**Expected response time:** 2-5 business days for initial reply

---

**Pro tip:** Submit during Mapbox business hours (PST/PDT timezone) for faster 
initial response. Monday-Wednesday mornings tend to get quickest attention.

Good luck! 🤞
