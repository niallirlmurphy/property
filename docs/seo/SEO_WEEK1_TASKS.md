# SEO Week 1 Implementation Guide

**Start Date:** 2026-06-08  
**Goal:** Complete all quick wins to establish SEO foundation

---

## Task 1: Add Canonical URLs (30 minutes)

### Edit: `frontend/src/hooks/usePageMeta.ts`

Add after line 32 (after og:image logic):

```tsx
// Add canonical URL
const canonicalUrl = `https://homeiq.ie${window.location.pathname}`;
let canonicalLink = document.querySelector('link[rel="canonical"]');

if (!canonicalLink) {
  canonicalLink = document.createElement('link');
  canonicalLink.setAttribute('rel', 'canonical');
  document.head.appendChild(canonicalLink);
}
canonicalLink.setAttribute('href', canonicalUrl);
```

Add cleanup in the return statement (after line 72):

```tsx
// Remove canonical in cleanup
const canonicalToRemove = document.querySelector('link[rel="canonical"]');
if (canonicalToRemove) {
  document.head.removeChild(canonicalToRemove);
}
```

**Test:**
```bash
npm run dev
# Open browser, view source, check for: <link rel="canonical" href="...">
```

**Commit:**
```bash
git add frontend/src/hooks/usePageMeta.ts
git commit -m "Add canonical URLs for SEO"
git push origin main
```

---

## Task 2: Submit to Google Search Console (15 minutes)

### Steps:

1. **Go to:** https://search.google.com/search-console

2. **Add Property:**
   - Click "Add Property"
   - Choose "URL prefix"
   - Enter: `https://homeiq.ie`

3. **Verify Ownership (DNS Method):**
   - Google will show: "Add TXT record to DNS"
   - Copy the TXT record value (e.g., `google-site-verification=xxxxx`)
   - Go to https://www.letshost.ie (login)
   - Navigate to: Domain Management → homeiq.ie → DNS Settings
   - Add new record:
     - Type: TXT
     - Name: @ (or leave blank)
     - Value: `google-site-verification=xxxxx`
     - TTL: 3600
   - Save and wait 5-15 minutes
   - Return to Search Console and click "Verify"

4. **Submit Sitemap:**
   - In Search Console sidebar: Sitemaps
   - Enter: `sitemap.xml`
   - Click "Submit"

5. **Set Default URL:**
   - Settings → Site Settings
   - Preferred domain: `https://homeiq.ie` (with HTTPS)

**Expected result:** "Sitemap submitted successfully. Check back in a few days."

---

## Task 3: Submit to Bing Webmaster Tools (15 minutes)

### Steps:

1. **Go to:** https://www.bing.com/webmasters

2. **Add Site:**
   - Sign in with Microsoft account
   - Click "Add a Site"
   - Enter: `https://homeiq.ie`

3. **Verify Ownership:**
   - Option 1: Import from Google Search Console (easiest if already verified)
   - Option 2: Add DNS TXT record (same process as Google)

4. **Submit Sitemap:**
   - Sitemaps → Submit Sitemap
   - Enter: `https://homeiq.ie/sitemap.xml`
   - Submit

---

## Task 4: Update Sitemap Dates (10 minutes)

### Edit: `frontend/public/sitemap.xml`

Update `<lastmod>` dates to current date (2026-06-08) for:
- Main pages (home, about, property-price-register)
- Recently changed pages

Or regenerate if you have a script:

```bash
python3 scripts/generate_sitemap.py
```

**Commit and deploy:**
```bash
git add frontend/public/sitemap.xml
git commit -m "Update sitemap with current dates"
git push origin main
```

**Then resubmit in Search Console:**
- Google Search Console → Sitemaps → Click on `sitemap.xml` → Resubmit
- Bing Webmaster Tools → Sitemaps → Resubmit

---

## Task 5: Batch Submit to IndexNow (20 minutes)

### Create batch submission script:

**File:** `scripts/batch_submit_indexnow.sh`

```bash
#!/bin/bash
# Batch submit all important URLs to IndexNow

INDEXNOW_KEY="32cfaa418f6f4182aa77505f3f1815de"
HOST="homeiq.ie"

# Array of URLs to submit
URLS=(
  "https://homeiq.ie/"
  "https://homeiq.ie/about"
  "https://homeiq.ie/property-price-register"
  "https://homeiq.ie/polygon"
  "https://homeiq.ie/mortgage"
  "https://homeiq.ie/county/dublin"
  "https://homeiq.ie/county/cork"
  "https://homeiq.ie/county/galway"
  "https://homeiq.ie/county/limerick"
  "https://homeiq.ie/county/clare"
  "https://homeiq.ie/county/kerry"
  "https://homeiq.ie/county/waterford"
  "https://homeiq.ie/county/wicklow"
  "https://homeiq.ie/county/meath"
  "https://homeiq.ie/county/kilkenny"
)

# Submit all URLs in one batch
URL_LIST=$(printf ',"%s"' "${URLS[@]}")
URL_LIST="[${URL_LIST:1}]"

curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d "{
    \"host\": \"${HOST}\",
    \"key\": \"${INDEXNOW_KEY}\",
    \"keyLocation\": \"https://${HOST}/${INDEXNOW_KEY}.txt\",
    \"urlList\": ${URL_LIST}
  }"

echo ""
echo "✓ Submitted ${#URLS[@]} URLs to IndexNow (Bing, Yandex, Naver)"
echo ""
echo "Note: Google does not support IndexNow. Use Google Search Console for Google indexing."
```

**Run:**
```bash
chmod +x scripts/batch_submit_indexnow.sh
./scripts/batch_submit_indexnow.sh
```

---

## Task 6: Verify Google Analytics (5 minutes)

### Check if GA is installed:

1. Visit https://homeiq.ie
2. Open DevTools → Network tab
3. Filter by "google-analytics" or "gtag"
4. Refresh page
5. Look for requests to `www.google-analytics.com` or `www.googletagmanager.com`

### If NOT installed:

**Edit:** `frontend/index.html`

Add before `</head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    page_path: window.location.pathname,
  });
</script>
```

**Get tracking ID:**
- Go to https://analytics.google.com
- Create property for homeiq.ie
- Copy the G-XXXXXXXXXX ID
- Replace in code above

**Deploy:**
```bash
git add frontend/index.html
git commit -m "Add Google Analytics tracking"
git push origin main
```

---

## Task 7: Test All Meta Tags (10 minutes)

### Tools to use:

1. **Meta Tags Preview:**
   - Visit: https://metatags.io
   - Enter: https://homeiq.ie
   - Check: Title, description, OG tags, Twitter cards

2. **Google Rich Results Test:**
   - Visit: https://search.google.com/test/rich-results
   - Enter: https://homeiq.ie
   - Check structured data validity

3. **Manual checks:**
   ```bash
   # Check key pages
   curl -s https://homeiq.ie | grep -i '<title>'
   curl -s https://homeiq.ie/county/dublin | grep -i '<meta name="description"'
   ```

### Fix any issues found:
- Missing descriptions
- Duplicate titles
- Broken structured data

---

## Completion Checklist

After completing all 7 tasks:

- [ ] Canonical URLs implemented and deployed
- [ ] Google Search Console verified and sitemap submitted
- [ ] Bing Webmaster Tools verified and sitemap submitted
- [ ] Sitemap dates updated to 2026-06-08
- [ ] IndexNow batch submission completed (15+ URLs)
- [ ] Google Analytics installed and tracking
- [ ] Meta tags tested and validated

---

## Verification (Day 2-3)

### Check Search Console (24-48 hours later):

**Google Search Console:**
- Coverage → See indexed pages count
- Sitemaps → Check "Discovered" count
- Performance → Check for any impressions

**Bing Webmaster Tools:**
- URL Inspection → Test a few URLs
- Reports → Site Scan → Check for errors

### Expected Results (Week 1):
- ✅ Sitemap processed: 98 URLs discovered
- ✅ 10-20 pages indexed (will grow over days)
- ✅ No critical errors in Search Console
- ✅ Google Analytics tracking visits

---

## Week 1 Deliverables

By end of week, you should have:

1. ✅ **Technical SEO foundation solid**
   - Canonical URLs
   - Search Consoles configured
   - IndexNow active
   - Analytics tracking

2. ✅ **Monitoring setup**
   - Google Search Console dashboard
   - Bing Webmaster dashboard
   - Google Analytics reports

3. ✅ **Baseline metrics**
   - Pages indexed: 10-20 (will grow)
   - Impressions: 0-10 (early days)
   - Errors: 0 critical

**Next:** Move to Week 2 - Content Expansion (county pages).

---

## Time Investment

Total time: **~2 hours**

- Task 1 (Canonical URLs): 30 min
- Task 2 (Google Console): 15 min
- Task 3 (Bing Console): 15 min
- Task 4 (Sitemap update): 10 min
- Task 5 (IndexNow batch): 20 min
- Task 6 (Analytics check): 5 min
- Task 7 (Meta testing): 10 min
- Buffer: 15 min

**ROI:** High - establishes entire SEO foundation.

---

## Questions/Issues?

**If DNS verification fails:**
- Wait 15-30 minutes for DNS propagation
- Use `nslookup -type=TXT homeiq.ie` to check if record is live
- Try alternative verification method (HTML file upload)

**If sitemap not processing:**
- Check sitemap is accessible: https://homeiq.ie/sitemap.xml
- Validate XML format: https://www.xml-sitemaps.com/validate-xml-sitemap.html
- Ensure robots.txt isn't blocking: https://homeiq.ie/robots.txt

**If IndexNow fails:**
- Check key file exists: https://homeiq.ie/32cfaa418f6f4182aa77505f3f1815de.txt
- Verify JSON format in curl command
- Try individual URL submission first (test)

**Need help?** Refer to SEO_AUDIT_AND_ACTION_PLAN.md for context.
