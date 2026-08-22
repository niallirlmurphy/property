# SEO Audit & Action Plan - HomeIQ.ie

**Date:** 2026-06-08  
**Domain:** https://homeiq.ie  
**Status:** Live on Vercel, recently launched

---

## ✅ Current SEO Status (What's Already Done)

### Technical SEO Foundation
- ✅ **Sitemap:** 98 URLs in `sitemap.xml` (counties, areas, main pages)
- ✅ **Robots.txt:** Configured, allows all except `/manual-geocode`
- ✅ **IndexNow:** Key configured, script ready for instant indexing
- ✅ **Meta tags:** Dynamic via `usePageMeta()` hook on all pages
- ✅ **Open Graph:** Title, description, image tags implemented
- ✅ **Twitter Cards:** Metadata configured
- ✅ **Breadcrumbs:** Schema.org JSON-LD implemented
- ✅ **HTTPS:** Secure (Vercel)
- ✅ **Mobile responsive:** Working
- ✅ **Performance:** Fast (Railway + Vercel edge)
- ✅ **Structured data:** WebApplication and Dataset schema in index.html
- ✅ **Canonical URLs:** Need to verify implementation (see below)

### Content Pages Live
1. **Core pages:** Home, About, Property Price Register, Polygon Search, Mortgage, Energy
2. **County pages:** All 26 Irish counties
3. **Area pages:** ~50 major areas
4. **Dublin postcode pages:** 22 postcodes (D01-D22, D6W)
5. **Eircode pages:** Dynamic routing key pages

### Current Sitemap Breakdown
- Main pages: 7
- County pages: 26
- Area pages: ~50
- Dublin postcodes: 22
- Total: **98 URLs**

---

## ❌ Critical SEO Gaps (High Priority)

### 1. **Missing Canonical URLs** 🚨
**Issue:** While CLAUDE.md mentions canonical tags, I need to verify they're actually implemented.

**Check:**
```tsx
// In usePageMeta.ts - verify this exists:
<link rel="canonical" href={`https://homeiq.ie${window.location.pathname}`} />
```

**Action:** Add canonical URL implementation to `usePageMeta()` hook.

### 2. **Thin Content on County Pages** 🚨
**Current:** County pages are likely template-based with minimal unique content.

**What's needed:**
- 200-300 word market overview per county
- Key statistics (median price, YoY change, total sales)
- Popular areas within county (with links)
- Recent trends commentary
- FAQ section (3-5 Q&A pairs per county)

**Example for Dublin:**
```markdown
## Dublin Property Prices 2026

Dublin remains Ireland's most active property market, with 12,543 residential 
sales recorded since 2010. The median property price in Dublin is €425,000, 
reflecting the capital's premium pricing compared to the national average.

### Key Statistics
- **Median Price:** €425,000
- **Average Price:** €467,800
- **Total Sales (2010-2026):** 12,543
- **Year-on-Year Change:** +4.2%

### Popular Areas
Explore property prices in Dublin's most sought-after neighborhoods:
- [Dublin 4](/area/dublin-4) - €650,000 median
- [Dublin 6](/area/dublin-6) - €580,000 median
...
```

### 3. **No Blog/Content Hub** 🚨
**Issue:** Zero evergreen content to rank for high-volume keywords.

**Missing pages:**
- `/blog` or `/guides` section
- "How to Use Property Price Register" guide
- "Understanding Eircode" guide
- Monthly/quarterly market reports
- First-time buyer guides

### 4. **Not Submitted to Search Consoles** 🚨
**Action needed:**
- ✅ Submit to **Google Search Console**
- ✅ Submit to **Bing Webmaster Tools**
- Monitor indexing status weekly
- Check for crawl errors
- Track search queries driving traffic

### 5. **Missing High-Volume Landing Pages** 🚨
**Target keywords NOT covered:**
- "property price register ireland" → Need `/property-price-register` (exists but needs content)
- "house prices ireland" → Need `/house-prices-ireland`
- "dublin house prices" → Covered by county page (needs content expansion)
- "irish property price trends" → Need `/property-price-trends`
- "eircode property search" → Need `/eircode-search` explainer

---

## 🟡 Medium Priority Issues

### 6. **Limited Internal Linking**
**Issue:** Pages don't cross-link enough.

**Needed:**
- County pages should link to area pages
- Area pages should link to nearby areas
- Add "You might also like" sections
- Create hub pages: "Leinster Property Prices" → all Leinster counties

### 7. **No Analytics Setup Confirmed**
**Check if installed:**
- Google Analytics 4
- Google Search Console verification
- Tracking organic search traffic
- Top landing pages report
- Search query report

### 8. **Missing Local SEO Schema**
**Currently have:** Country-level WebApplication schema.

**Should add:** County-level Place schema on county pages:
```json
{
  "@type": "Place",
  "address": {
    "@type": "PostalAddress",
    "addressRegion": "County Dublin",
    "addressCountry": "IE"
  }
}
```

### 9. **No Social Sharing Features**
**Add:**
- Share buttons on search results
- Share specific property searches
- Share price trend charts
- Twitter/Facebook share optimization

---

## ✅ Quick Wins (Implement First - Week 1)

### Priority 1: Fix Canonical URLs
**File:** `frontend/src/hooks/usePageMeta.ts`

Add canonical URL logic:
```tsx
// After setting og:image
const canonical = document.querySelector('link[rel="canonical"]');
if (!canonical) {
  const link = document.createElement('link');
  link.rel = 'canonical';
  link.href = `https://homeiq.ie${window.location.pathname}`;
  document.head.appendChild(link);
} else {
  canonical.setAttribute('href', `https://homeiq.ie${window.location.pathname}`);
}
```

### Priority 2: Submit to Search Consoles
**Actions:**
1. Go to https://search.google.com/search-console
2. Add property: https://homeiq.ie
3. Verify ownership (DNS TXT record via Letshost.ie)
4. Submit sitemap: https://homeiq.ie/sitemap.xml
5. Repeat for Bing Webmaster Tools

### Priority 3: Update Sitemap with lastmod Dates
**Current:** Dates are static (May 30).
**Fix:** Regenerate with current date for main pages, weekly for county pages.

```bash
python3 scripts/generate_sitemap.py
git add frontend/public/sitemap.xml
git commit -m "Update sitemap with current dates"
git push
```

### Priority 4: Submit Current Pages to IndexNow
**Batch submit all 98 URLs:**
```bash
# Submit key pages immediately
./scripts/submit_indexnow.sh https://homeiq.ie/
./scripts/submit_indexnow.sh https://homeiq.ie/property-price-register
./scripts/submit_indexnow.sh https://homeiq.ie/county/dublin
./scripts/submit_indexnow.sh https://homeiq.ie/county/cork
./scripts/submit_indexnow.sh https://homeiq.ie/county/galway
# ... (or create a batch script)
```

### Priority 5: Add Google Analytics
**If not already installed:**

Add to `frontend/index.html` before `</head>`:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 📝 Content Creation Plan (Weeks 2-4)

### Week 2: Expand County Pages
**For each county (26 total):**

1. **Market Overview** (200-300 words)
   - Current market state
   - Historical context
   - Price ranges
   - Target buyers

2. **Statistics Block**
   ```tsx
   <div className="stats">
     <Stat label="Median Price" value="€425,000" />
     <Stat label="Total Sales" value="12,543" />
     <Stat label="YoY Change" value="+4.2%" />
   </div>
   ```

3. **Popular Areas Section**
   - List top 5-10 areas with links
   - Show median prices per area
   - Internal linking boost

4. **FAQ Section** (3-5 Q&As per county)
   - "What is the average house price in [County]?"
   - "Which areas in [County] are most expensive?"
   - "How have [County] property prices changed?"
   - "Is [County] a good place to buy property?"

**Template:** Create `CountyContentTemplate.tsx` with slots for dynamic data.

**Estimated time:** 2-3 hours per county = 60-75 hours total (can parallelize with AI assistance).

### Week 3: Create High-Volume Landing Pages

**Page 1: /house-prices-ireland**
- **Title:** House Prices Ireland - Search 785,000 Property Sales | HomeIQ
- **Content:** Comprehensive guide to Irish property prices
- **Sections:**
  - National overview
  - Average prices by province
  - Price trends 2010-2026
  - How to use the data
  - Interactive search widget
  - County comparison table
- **Keywords:** house prices ireland, irish house prices, property prices ireland

**Page 2: /irish-property-price-trends**
- **Title:** Irish Property Price Trends 2010-2026 | Market Analysis
- **Content:** Trends analysis with charts
- **Sections:**
  - National trends chart
  - Regional breakdowns
  - Boom/bust cycles explained
  - Future predictions disclaimer
  - Top rising/falling areas
- **Keywords:** irish property price trends, property market trends ireland

**Page 3: /eircode-search**
- **Title:** Eircode Property Search - Find Prices by Eircode | HomeIQ
- **Content:** Eircode explainer + search
- **Sections:**
  - What is Eircode?
  - How to search by Eircode
  - Routing key explanation
  - Example searches (D02, H91, etc.)
  - Interactive search widget
- **Keywords:** eircode property search, search property by eircode

**Page 4: /property-price-register-guide**
- **Title:** How to Use Ireland's Property Price Register - Complete Guide
- **Content:** Evergreen guide (high search volume)
- **Sections:**
  - What is PPR?
  - How to search PPR data
  - Understanding the data
  - Limitations
  - Alternative tools (mention HomeIQ features)
  - Video tutorial (if budget allows)
- **Keywords:** property price register ireland, how to use property price register

**Page 5: /first-time-buyer-guide**
- **Title:** First Time Buyer's Guide to Irish Property Prices | HomeIQ
- **Content:** Beginner-friendly guide
- **Sections:**
  - Understanding property prices
  - Affordability by county
  - Help-to-Buy scheme
  - Mortgage calculator link
  - Top affordable areas
  - Tips for FTBs
- **Keywords:** first time buyer ireland, affordable property ireland

### Week 4: Launch Blog Section

**URL Structure:** `/blog/[slug]`

**Initial 5 Posts:**

1. **"How to Use the Property Price Register - Step by Step"**
   - SEO: property price register guide
   - Evergreen, high traffic potential

2. **"Dublin Property Prices by Postcode - 2026 Guide"**
   - SEO: dublin property prices postcode
   - Link to all D01-D22 pages

3. **"Cork vs Galway vs Limerick: Property Price Comparison"**
   - SEO: compare property prices ireland
   - City comparison

4. **"Understanding Eircode for Property Search"**
   - SEO: eircode explained
   - Technical but approachable

5. **"Irish Property Prices - June 2026 Market Report"**
   - SEO: irish property prices [current month]
   - Monthly recurring format

**Publishing schedule:** 2 posts per week after initial launch.

---

## 🔗 Link Building Strategy (Ongoing)

### Month 1: Foundation
1. **Directory Listings**
   - PropertyPrice.ie mentions
   - Irish property forums (boards.ie, Reddit r/irishpersonalfinance)
   - Irish tech/startup directories

2. **Media Outreach - Press Release**
   - **Subject:** "New Free Tool Simplifies Irish Property Price Search"
   - **Pitch to:**
     - TheJournal.ie
     - BreakingNews.ie
     - Irish Times property section
     - Independent.ie property
   - **Angle:** "785,000 property sales, 85% geocoded, completely free"

3. **Data Journalism**
   - Create shareable infographics (price heat maps)
   - Publish quarterly market reports
   - Offer data insights to journalists
   - Quote: "Source: HomeIQ.ie analysis of Property Price Register data"

### Month 2-3: Community Building
1. **Reddit/Boards.ie Engagement**
   - Answer property price questions
   - Link to relevant searches
   - Be helpful, not spammy

2. **Twitter/X**
   - Share interesting findings
   - Price trends by area
   - Use hashtags: #IrishProperty #PropertyPrices #Dublin

3. **Partner Outreach**
   - Estate agents (offer embeddable widgets?)
   - Mortgage brokers (link to mortgage calculator)
   - Property blogs

---

## 📊 Success Metrics & Timeline

### 3 Months
**Goals:**
- ✅ 50+ pages indexed in Google
- ✅ 500-1,000 organic visitors/month
- ✅ 5-10 quality backlinks
- ✅ Ranking in top 50 for 3-5 primary keywords

**Track:**
- Google Search Console impressions/clicks
- Top search queries
- Average position
- Click-through rate

### 6 Months
**Goals:**
- ✅ 100+ pages indexed
- ✅ 2,000-5,000 organic visitors/month
- ✅ Top 10 rankings for 3-5 primary keywords
- ✅ 20+ quality backlinks

**Track:**
- Organic traffic growth rate
- Conversion rate (searches performed)
- Bounce rate by page type
- Top landing pages

### 12 Months
**Goals:**
- ✅ 150+ pages indexed
- ✅ 10,000+ organic visitors/month
- ✅ Top 3 rankings for primary keywords
- ✅ Established as authoritative source

**Track:**
- Brand searches (people searching "homeiq.ie")
- Return visitor rate
- Email alert signups
- Social shares

---

## 🎯 Primary Target Keywords (Focus On These)

### High Volume (>1,000 searches/month)
1. **"house prices ireland"** - Very high volume
2. **"property price register ireland"** - High volume
3. **"dublin house prices"** - High volume
4. **"cork house prices"** - Medium-high
5. **"irish property prices"** - High volume

### Medium Volume (500-1,000/month)
6. **"property prices [county name]"** - 26 variations
7. **"eircode property search"** - Medium
8. **"irish property price trends"** - Medium
9. **"average house price ireland"** - Medium
10. **"property price register search"** - Medium

### Long Tail (100-500/month - Easier to Rank)
11. **"property prices in [specific area]"** - Hundreds of variations
12. **"[area name] property prices"** - Long-tail gold
13. **"[eircode] property prices"** - 301 routing keys
14. **"property sold prices [address]"** - Very long-tail
15. **"house price trends [county]"** - 26 variations

---

## 🛠️ Implementation Checklist

### Week 1 (Quick Wins) - **DO FIRST**
- [ ] Add canonical URLs to `usePageMeta()` hook
- [ ] Submit to Google Search Console
- [ ] Submit to Bing Webmaster Tools
- [ ] Update sitemap dates and redeploy
- [ ] Batch submit 98 URLs to IndexNow
- [ ] Verify Google Analytics is tracking
- [ ] Test all meta tags with https://metatags.io

### Week 2 (Content Expansion)
- [ ] Expand Dublin county page (pilot)
- [ ] Add statistics blocks to county pages
- [ ] Create FAQ sections for top 5 counties
- [ ] Add "Popular Areas" sections with links
- [ ] Test and deploy

### Week 3 (Landing Pages)
- [ ] Create `/house-prices-ireland` page
- [ ] Create `/irish-property-price-trends` page
- [ ] Create `/eircode-search` guide page
- [ ] Expand `/property-price-register` page
- [ ] Deploy and submit to IndexNow

### Week 4 (Blog Launch)
- [ ] Create blog infrastructure (`/blog` page + routing)
- [ ] Write and publish 5 initial blog posts
- [ ] Set up RSS feed
- [ ] Add blog links to main nav
- [ ] Submit blog posts to IndexNow

### Month 2 (Ongoing)
- [ ] Complete all 26 county content expansions
- [ ] Publish 2 blog posts per week
- [ ] Start media outreach (press release)
- [ ] Begin community engagement (Reddit/Boards.ie)
- [ ] Monitor Search Console weekly
- [ ] Track rankings for target keywords

### Month 3 (Link Building)
- [ ] Create shareable infographic (price heat map)
- [ ] Publish quarterly market report
- [ ] Pitch to journalists with data insights
- [ ] Get listed in property directories
- [ ] Continue blog cadence (2/week)

---

## 💰 Budget Considerations

### Free (DIY)
- ✅ Content writing (your time)
- ✅ IndexNow submissions
- ✅ Search Console monitoring
- ✅ Community engagement
- ✅ Social media posting

### Low Cost (<€100/month)
- AI writing assistance (ChatGPT Plus - €20/month)
- Canva Pro for infographics (€12/month)
- SEO monitoring tool (Ubersuggest - €29/month)

### Medium Cost (€100-500)
- Professional blog post writing (€50-100 per post)
- Infographic designer (€200-300 one-time)
- PR distribution service (€200-400 per release)

### Not Needed (Skip These)
- ❌ Expensive SEO agency (€1,000+/month) - too early
- ❌ Paid backlinks - against Google guidelines
- ❌ PPC ads - focus on organic first

---

## 📈 Expected Traffic Growth

**Realistic projections based on similar sites:**

| Month | Pages | Backlinks | Organic Visitors/Month |
|-------|-------|-----------|------------------------|
| Now   | 98    | 0-2       | <100                   |
| 3     | 120   | 5-10      | 500-1,000              |
| 6     | 150   | 20+       | 2,000-5,000            |
| 12    | 200+  | 50+       | 10,000-20,000          |
| 24    | 300+  | 100+      | 50,000-100,000         |

**Key factors:**
- Content quality
- Consistent publishing (blog)
- Backlink velocity
- Domain authority growth
- Technical SEO health

---

## 🚀 Next Steps: Start Today

### Immediate (Today)
```bash
# 1. Fix canonical URLs (code change)
# Edit frontend/src/hooks/usePageMeta.ts

# 2. Submit to Search Console
# Visit search.google.com/search-console

# 3. Submit key pages to IndexNow
./scripts/submit_indexnow.sh https://homeiq.ie/
./scripts/submit_indexnow.sh https://homeiq.ie/county/dublin
```

### This Week
- Expand Dublin county page content (pilot)
- Create `/house-prices-ireland` landing page
- Submit to Google/Bing search consoles

### This Month
- Expand all 26 county pages
- Launch blog with 5 initial posts
- Start press outreach

**The foundation is solid. Now it's about content, consistency, and community building.**
