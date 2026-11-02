# SEO strategy & traffic growth

Moved out of CLAUDE.md on 2026-11-02. Parts predate the sitemap/robots.txt work and may be out of date.


## Current SEO Status
**Domain:** homeiq.ie (production on Vercel)
**Current State:** Low traffic, recently launched
**Target Audience:** Irish property buyers, sellers, investors, estate agents, mortgage advisors

## Implemented SEO Foundation
- ✅ **Meta tags**: All pages use `usePageMeta()` hook for dynamic titles/descriptions
- ✅ **Structured data**: WebApplication and Dataset schema in `index.html`
- ✅ **Open Graph**: Facebook/LinkedIn sharing optimization
- ✅ **Twitter Cards**: Twitter sharing optimization
- ✅ **Sitemap**: Need to generate (see recommendations below)
- ✅ **robots.txt**: Need to create (see recommendations below)
- ✅ **Performance**: Fast loading (Railway + Vercel), mobile-responsive
- ✅ **Security**: HTTPS, CORS configured, RLS enabled

## High-Priority Traffic Growth Recommendations

### 1. Technical SEO (Quick Wins - Implement First)
**Generate XML sitemap:**
```bash
# Create frontend/public/sitemap.xml with all key pages
# Include: counties (26), major areas (~50), Dublin postcodes (22), main pages
```

**Create robots.txt:**
```
User-agent: *
Allow: /
Sitemap: https://homeiq.ie/sitemap.xml

# Block internal tools
Disallow: /manual-geocode
```

**Submit to search engines:**
- Google Search Console: https://search.google.com/search-console
- Bing Webmaster Tools: https://www.bing.com/webmasters
- Submit sitemap URLs directly
- Monitor indexing status weekly

**Add canonical URLs:** Prevent duplicate content issues
```tsx
// In usePageMeta hook
<link rel="canonical" href={`https://homeiq.ie${window.location.pathname}`} />
```

**Implement breadcrumbs with schema:**
```tsx
// Add to County/Area pages for better crawlability
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [...]
}
</script>
```

### 2. Content SEO (High Impact)
**Add dedicated landing pages for high-volume searches:**
- `/property-price-register` - Target "property price register ireland"
- `/house-prices-ireland` - Target "house prices ireland"
- `/dublin-house-prices` - Target "dublin house prices"
- `/property-price-trends` - Target "irish property price trends"
- `/mortgage-calculator-ireland` (already exists at `/mortgage`)
- `/eircode-property-search` - Target "eircode property search"

**County pages need more content:**
Current county pages are thin. Add to each:
- Market overview paragraph (200-300 words)
- Key statistics (total sales, median price, YoY change)
- Popular areas within county (link to area pages)
- Recent trends commentary
- FAQs section (3-5 Q&A pairs)

**Blog/Resources section:** `/blog` or `/guides`
Content ideas:
- "How to Use the Property Price Register" (evergreen, high-volume)
- "Understanding Eircode for Property Search"
- "Dublin Property Prices by Postcode - 2025 Guide"
- "Cork vs Galway vs Limerick: Property Price Comparison"
- "First Time Buyer's Guide to Irish Property Prices"
- Monthly market reports: "Irish Property Prices - [Month] 2025"
- County deep-dives: "Complete Guide to [County] Property Prices"

**Internal linking strategy:**
- Link county pages to area pages
- Link area pages to nearby areas
- Add "You might also like" sections
- Create hub pages: "Leinster Property Prices" linking to all Leinster counties

### 3. Link Building & Authority (Medium-Term)
**Get listed in directories:**
- PropertyPrice.ie mentions
- MyHome.ie (partner/data provider discussions?)
- Daft.ie (competitor but may link to public data)
- Irish property forums (boards.ie, Reddit r/ireland, r/irishpersonalfinance)
- Irish tech/startup directories

**Media outreach:**
- Press release: "New Free Tool for Irish Property Price Search"
- Pitch to TheJournal.ie, BreakingNews.ie, Irish Times property section
- Offer data insights: "Analysis: Where Irish Property Prices Rose Most in 2025"
- Quote property price statistics with "Source: HomeIQ.ie analysis of PPR data"

**Data journalism opportunities:**
- Publish monthly/quarterly market reports
- Create shareable infographics (price heat maps, trend charts)
- Offer API access for journalists/researchers (consideration for future)

**Community engagement:**
- Answer property price questions on boards.ie with links to relevant searches
- Create helpful Reddit posts in r/irishpersonalfinance with tool demonstrations
- Engage on Twitter/X with Irish property hashtags

### 4. Local SEO
**Google Business Profile:**
- If applicable (depends on business structure)
- Claim and optimize listing

**Local schema markup:**
Already have country-level, expand to county-level:
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

### 5. User Experience & Engagement (Affects SEO Indirectly)
**Add "Share" functionality:**
- Share search results via social media
- Share specific property listings
- Share price trend charts

**Email newsletter:**
- "Dublin Property Price Digest - Weekly"
- Builds return visitors (positive SEO signal)
- Already have email alert modal - extend it

**Property price alerts:**
- Already implemented in EmailAlertModal.tsx
- Promote this feature prominently (unique value proposition)

**Add more interactive features:**
- Price prediction tool
- Stamp duty calculator (link to revenue.ie)
- Affordability calculator (income vs price)
- Compare areas side-by-side

### 6. Performance & Mobile SEO
**Already strong, but monitor:**
- Core Web Vitals (use Google PageSpeed Insights)
- Mobile usability in Search Console
- Map loading speed (lazy load if needed)

### 7. Keyword Optimization
**Primary keywords to target:**
- "property price register ireland" (high volume)
- "house prices ireland" (very high volume)
- "dublin house prices" (high volume)
- "property prices [county name]" (medium volume × 26 counties)
- "eircode property search" (medium volume)
- "[area name] property prices" (long-tail × hundreds of areas)
- "irish property price trends" (medium volume)
- "property price register search" (medium volume)

**Long-tail opportunities:**
- "property prices in [specific area]"
- "average house price [town name]"
- "[eircode] property prices"
- "property sold prices [address]"
- "house price trends [county]"

### 8. Analytics & Monitoring
**Set up if not already:**
- Google Analytics 4
- Google Search Console
- Track: organic search traffic, top landing pages, bounce rate, search queries

**Monitor weekly:**
- Indexing status (Search Console)
- Top performing pages
- Search queries driving traffic
- Click-through rates from search results

**A/B test meta descriptions:**
- Improve CTR from search results
- Test different value propositions

## Implementation Priority
**Week 1 (Immediate):**
1. Generate sitemap.xml
2. Create robots.txt
3. Submit to Google Search Console & Bing Webmaster
4. Add canonical URLs to usePageMeta hook
5. Fix any meta tag issues found

**Week 2-3 (High Impact):**
1. Expand county pages with more content
2. Create 3-5 landing pages for high-volume keywords
3. Add breadcrumb navigation
4. Improve internal linking

**Month 2 (Content & Authority):**
1. Launch blog section with 5-10 initial articles
2. Publish first market report
3. Start media outreach
4. Begin community engagement

**Ongoing:**
- Publish 2-4 blog posts per month
- Monitor analytics weekly
- Build backlinks through outreach
- Update market reports monthly

## Measuring Success
**3 months:** 
- 500-1000 organic visitors/month
- 50+ pages indexed in Google
- 5-10 quality backlinks

**6 months:**
- 2,000-5,000 organic visitors/month
- Top 10 rankings for 3-5 primary keywords
- 20+ quality backlinks

**12 months:**
- 10,000+ organic visitors/month
- Top 3 rankings for primary keywords
- Established as authoritative Irish property data source

## Content Ideas Bank
Keep a running list of content to create:
- County comparison tools
- Property price FAQs per county
- Historical price analysis pieces
- First-time buyer resources
- Investment property guides
- Market trend commentary
