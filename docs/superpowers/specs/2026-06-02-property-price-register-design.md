# Property Price Register Landing Page Design

**Date:** 2026-06-02  
**Status:** Design Review  
**Route:** `/property-price-register`

## Overview

Create a dedicated landing page that explains Ireland's Property Price Register (PPR), its origins as a taxation record, its limitations, and how HomeIQ enhances the raw data to provide better search and mapping capabilities.

## Goals

1. **SEO Target:** Rank for "property price register ireland", "PPR ireland", "property price register search"
2. **Education:** Help users understand what the PPR is and where the data comes from
3. **Transparency:** Honestly explain limitations of the source data
4. **Differentiation:** Showcase HomeIQ's data quality improvements
5. **Conversion:** Guide users to try the enhanced search tools

## Target Audience

- Property buyers researching Irish housing market
- Estate agents and property professionals
- Investors seeking historical transaction data
- Users who know about the official PPR site but want better search tools
- SEO traffic searching for information about the Property Price Register

## Page Structure

### 1. Page Metadata & SEO

- **Title:** "Property Price Register Ireland | Complete Guide & Enhanced Data"
- **Meta Description:** "Understand Ireland's Property Price Register, its limitations as a taxation record, and how HomeIQ enhances the data with geocoding validation and address normalization for better property search."
- **Canonical URL:** `https://homeiq.ie/property-price-register`
- **Target Keywords:**
  - Primary: "property price register ireland"
  - Secondary: "PPR ireland", "property price register search", "irish property price data"

### 2. Hero Section

**H1:** Understanding Ireland's Property Price Register

**Lead Paragraph (150-200 words):**
Introduce the PPR as Ireland's official record of residential property sales since 2010. Establish this page as a comprehensive guide that explains both the source data and HomeIQ's enhancements. Set the tone: informative, transparent, and practical.

### 3. What is the Property Price Register?

**Content Points:**
- Official government register of all residential property sales in Ireland
- Established in 2010 under Finance Act 2010
- Managed by the Property Services Regulatory Authority (PSRA)
- Contains over 784,000 transactions from 2010 to present
- Publicly accessible at propertypriceregister.ie
- Legal requirement: all property sales over €100,000 must be registered
- Provides baseline transparency for Irish property market

**Link to official site:** https://www.propertypriceregister.ie

### 4. How the PPR Works: The Taxation Connection

**H2:** How the PPR Works: A Taxation Record

**Content Points:**
- Data originates from Revenue's stamp duty collection system
- Solicitors submit property sale details as part of stamp duty compliance
- This taxation origin creates comprehensive coverage (legal requirement)
- But also creates limitations (system designed for tax, not property search)

**What's Included in PPR Data:**
- Property address
- Sale price (€)
- Sale date
- Property description (new/secondhand)
- Market status (full market price / not full market price)

**What's NOT Included in Raw PPR:**
- Geographic coordinates (latitude/longitude)
- Eircodes for older properties (pre-2015)
- Standardized address formatting
- Property size or features
- Seller/buyer information

### 5. Limitations of Raw PPR Data

**H2:** Understanding the Limitations

Explain practical challenges users face with raw PPR data:

**No Geographic Coordinates**
- Original PPR contains only text addresses, no mapping data
- Users cannot search "properties near me" or visualize market patterns
- No way to do radius-based searches or area comparisons on official site

**Inconsistent Address Formatting**
- Varying capitalization (MAIN STREET vs Main Street vs main street)
- Different abbreviations (Rd, Road, RD)
- Extra spaces and punctuation inconsistencies
- Makes text searching unreliable—you might miss results

**Missing Eircodes for Older Properties**
- Ireland's Eircode system launched in 2015
- Properties sold 2010-2015 typically have no postcode in PPR
- Difficult to pinpoint exact locations for older sales

**Limited Search Capabilities**
- Official website offers basic text search only
- No filtering by distance, map-based selection, or area drawing
- Cannot easily analyze price trends for specific neighborhoods
- Difficult to compare nearby properties

**"Not Full Market Price" Transactions**
- Family transfers, equity releases, and non-arms-length sales included
- Users need to manually filter these to get accurate market trends
- Not obvious which transactions represent true market prices

**Real-World Impact:** These limitations mean you can't easily answer questions like "What are properties selling for within 3km of this address?" or "Show me all sales in this neighborhood on a map."

### 6. How HomeIQ Enhances PPR Data

**H2:** How HomeIQ Enhances the Data

Brief intro paragraph: "At HomeIQ, we take the raw PPR data and apply extensive validation, geocoding, and normalization to make it more accurate, searchable, and useful for property research."

**Our Data Quality Improvements:**

- **Address Normalization**  
  Standardized formatting for all 784k properties: consistent capitalization, abbreviations, and structure for more reliable search results.

- **Geocoding & Coordinate Validation**  
  Added geographic coordinates to 78% of properties (614,200+ locations) with multi-layer validation to ensure accuracy. Recent properties have 89-91% geocoding coverage.

- **Quality Scoring System**  
  Every geocoded property receives a quality score based on precision level (rooftop, parcel, street, locality) to ensure reliable map positioning.

- **Eircode Enrichment**  
  Enhanced postcode coverage through daily enrichment, bringing Eircode data to 30% of all properties and 74-79% of recent sales.

- **Centroid Cleanup**  
  Identified and re-geocoded properties stuck at generic town/county center coordinates to provide accurate property-specific locations.

**The Result:**
- Map-based radius search (2km, 5km, 10km, 20km)
- Interactive polygon drawing tools for custom area selection
- Accurate location markers showing actual property positions
- County and area filtering with smart auto-detection
- Price trend charts by precise geographic area
- Eircode-based search for newer properties

### 7. Practical Benefits for Users

**H2:** What This Means for You

Short, benefit-focused section tying technical improvements to user value:

**With HomeIQ's Enhanced PPR Data, You Can:**
- Search properties within walking distance of a specific location
- Draw custom search areas on an interactive map
- View accurate price trends for specific neighborhoods, not just counties
- Filter by county, property type, date range, and market status
- Trust that map markers show actual property locations, not generic centroids
- Compare prices across different areas with visual map tools

### 8. Call-to-Action

**Primary CTA:** Link to main search page  
Button text: "Search Property Prices Now"

**Secondary CTA:** Link to polygon search page  
Button text: "Try Advanced Map Search"

**Tertiary:** Link back to About page for broader context on all data sources

## Component Requirements

**Component:** `PropertyPriceRegisterPage.tsx`

**Props:** None

**Structure:**
```tsx
- PageHeader (title: "Understanding Ireland's Property Price Register")
- Main content sections wrapped in semantic HTML
- Links to external PPR site, PSRA, Revenue
- Internal links to search pages and About page
- CSS classes follow AboutPage.tsx pattern
```

**Styling:**
- Reuse existing classes from `AboutPage.tsx`: `.static-page`, `.static-content`, `.about-section`, `.about-lead`
- Add new class `.about-sources` for definition list styling (already exists in AboutPage)
- Maintain consistent typography and spacing with other static pages

## Routing

**Add to router configuration:**
```tsx
<Route path="/property-price-register" element={<PropertyPriceRegisterPage />} />
```

## Internal Linking Strategy

**Link FROM this page TO:**
- Main search page (/) - primary CTA
- Polygon search page (/polygon) - secondary CTA
- About page (/about) - broader data sources context
- Official PPR site (external) - https://www.propertypriceregister.ie
- PSRA site (external) - https://www.psprauth.ie

**Link TO this page FROM:**
- About page: Update PPR source description to say "Learn more about the Property Price Register"
- Footer (if exists): Add to resources/documentation links
- Site header/nav: Consider adding to a "Resources" dropdown

## SEO Implementation

**On-Page SEO:**
- H1: "Understanding Ireland's Property Price Register"
- H2s for each major section (5-6 H2s total)
- Target keyword in first 100 words
- Natural keyword variations throughout
- Internal links using keyword-rich anchor text
- External authoritative links (propertypriceregister.ie, psprauth.ie)

**Structured Data:**
Include BreadcrumbList schema:
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://homeiq.ie"},
    {"@type": "ListItem", "position": 2, "name": "Property Price Register", "item": "https://homeiq.ie/property-price-register"}
  ]
}
```

**After Launch:**
- Submit URL to Google Search Console for indexing
- Add to sitemap.xml
- Use IndexNow for instant indexing (Bing, Yandex)
- Monitor Search Console for ranking keywords

## Content Guidelines

**Tone:**
- Professional but accessible
- Transparent about limitations (builds trust)
- Educational, not marketing-heavy
- Factual about government data sources
- Confident but not boastful about improvements

**Word Count Target:**
- Total: 1,200-1,500 words
- Hero + What is PPR: 300-400 words
- Taxation Connection: 200-250 words
- Limitations: 300-400 words
- HomeIQ Enhancements: 250-350 words
- Benefits + CTA: 150-200 words

**Key Messaging:**
1. The PPR is Ireland's official, comprehensive property sales record
2. It originates from taxation records, which affects its structure and limitations
3. Raw PPR data is public but difficult to search and map effectively
4. HomeIQ enhances this data through geocoding, validation, and normalization
5. Users get more powerful search and visualization tools as a result

## Success Metrics

**Launch metrics (first 30 days):**
- Page indexed by Google within 7 days
- Organic search impressions for target keywords
- Click-through rate from search results: target >3%
- Time on page: target >2 minutes (indicates content engagement)
- Conversion to search tools: target >20% click through to main search

**3-month goals:**
- Rank in top 20 for "property price register ireland"
- 100+ organic sessions per month
- 5+ backlinks from property/real estate sites
- Featured in "People Also Ask" boxes for PPR-related queries

## Implementation Notes

**File Structure:**
```
frontend/src/pages/PropertyPriceRegisterPage.tsx (new)
frontend/src/App.tsx (update routes)
```

**External Links to Include:**
- https://www.propertypriceregister.ie - Official PPR website
- https://www.psprauth.ie - Property Services Regulatory Authority
- https://data.gov.ie - National open data portal (context)

**Dependencies:**
- Existing `PageHeader` component
- Existing `usePageMeta` hook
- Existing CSS from AboutPage (reuse classes)

## Out of Scope

This landing page does NOT include:
- Interactive data visualizations or charts
- Live PPR data integration or API calls
- Property search functionality (links to search pages instead)
- Comparison tool with official PPR site
- Historical timeline/infographic of PPR evolution
- User comments or community features

These could be future enhancements but are not part of the initial launch.

## Open Questions

None - design is ready for implementation pending user approval.
