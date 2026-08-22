# Data Quality Assessment & Traffic Growth Strategy
**Date:** June 13, 2026  
**Database:** 784,854 properties (2010-2026)

---

## Executive Summary

**Current State:**
- 90.8% geocoding coverage (712,910 properties with coordinates)
- 29.8% Eircode coverage overall (74-79% for 2022-2026)
- 1.6% enriched with bedroom data (12,265 properties)
- 1.8% enriched with property type (14,284 properties)
- **Near-zero organic user engagement** (0 real feedback, ~1 email signup)

**Key Opportunity:**
The 12k enriched properties (2026 focus with 60-70% coverage) represent a **competitive moat** - property type and bedroom data that MyHome.ie and Daft.ie don't have for historical sales. Scale enrichment to 10%+ (78k properties) to drive unique traffic.

---

## Data Quality Assessment

### Overall Database Stats

```
Total properties:        784,854
Geocoded:               712,910  (90.8%)
With Eircode:           233,703  (29.8%)
With bedrooms:           12,265  ( 1.6%)
With property_type:      14,284  ( 1.8%)
Not full market price:   39,967  ( 5.1%)
At centroids (low qual): 50,944  ( 6.5%)
```

### Coverage by Year (2020-2026)

| Year | Total   | Geocoded | Eircode | Bedrooms | Property Type |
|------|---------|----------|---------|----------|---------------|
| 2026 | 16,731  | 99%      | 79%     | 60.3%    | 70.4%         |
| 2025 | 61,951  | 100%     | 74%     | 3.5%     | 4.0%          |
| 2024 | 61,542  | 100%     | 75%     | 0.0%     | 0.0%          |
| 2023 | 63,373  | 100%     | 76%     | 0.0%     | 0.0%          |
| 2022 | 62,742  | 100%     | 77%     | 0.0%     | 0.0%          |
| 2021 | 59,602  | 99%      | 51%     | 0.0%     | 0.0%          |
| 2020 | 49,553  | 99%      | 1%      | 0.0%     | 0.0%          |

**Insights:**
- Near-perfect geocoding for recent years (2021+)
- Eircode coverage strong for 2022+ (system maturity)
- Enrichment only started in 2026 - massive backfill opportunity for 2020-2025

### Geographic Coverage

**Top 15 Counties by Sales Volume:**

| County     | Total Sales | Geocoded |
|------------|-------------|----------|
| Dublin     | 245,654     | 92%      |
| Cork       | 86,916      | 90%      |
| Kildare    | 42,623      | 94%      |
| Galway     | 37,933      | 90%      |
| Meath      | 32,656      | 92%      |
| Limerick   | 28,831      | 88%      |
| Wexford    | 27,421      | 88%      |
| Wicklow    | 26,522      | 92%      |
| Louth      | 21,928      | 91%      |
| Waterford  | 21,484      | 90%      |
| Kerry      | 21,419      | 89%      |
| Tipperary  | 21,009      | 92%      |
| Donegal    | 20,836      | 86%      |
| Mayo       | 18,744      | 92%      |
| Clare      | 17,588      | 88%      |

**Top Eircode Routing Keys:**
- V94 (8,438), H91 (7,306), T12 (6,706) - Cork/Galway/Cork
- Dublin routing keys: D15 (6,585), D24 (4,664), D18 (4,134), D08 (3,674)
- 301 routing key areas total with centroids mapped

### Price Distribution (Full Market Sales Only)

| Price Range  | Properties |
|--------------|------------|
| <€100k       | 101,111    |
| €100-200k    | 182,194    |
| €200-300k    | 180,232    |
| €300-400k    | 126,437    |
| €400-500k    | 66,993     |
| €500-750k    | 55,806     |
| €750k-1M     | 16,834     |
| >€1M         | 15,280     |

**Insight:** Strong distribution across all price ranges, with peak at €100-300k (typical Irish housing market).

### Property Type Distribution (Enriched Data)

| Property Type  | Count  |
|----------------|--------|
| Apartment      | 4,531  |
| Semi-Detached  | 3,703  |
| Detached       | 3,304  |
| Terraced       | 2,594  |
| House          | 115    |
| Bungalow       | 21     |
| Duplex         | 11     |
| Cottage        | 5      |

### Bedroom Distribution (Enriched Data)

| Bedrooms | Count  |
|----------|--------|
| 1 bed    | 344    |
| 2 bed    | 2,275  |
| 3 bed    | 4,547  |
| 4 bed    | 4,009  |
| 5 bed    | 878    |
| 6+ bed   | 212    |

**Insight:** 3-4 bedroom properties dominate (69% of enriched data), typical for Irish family homes.

---

## Strengths ✅

### 1. Excellent Core Coverage (90.8% geocoded)
- 712,910 properties with coordinates
- Near-perfect coverage for 2021-2026 (99-100%)
- Strong distribution across all 26 counties
- PostGIS spatial indexing enables fast radius/polygon queries

### 2. Comprehensive Price Data
- 16+ years of transaction history (2010-2026)
- 745k full market price transactions (95%)
- Good distribution across all price ranges
- Enables robust trend analysis

### 3. Strong Eircode Coverage (Recent Years)
- 233k properties with Eircodes (29.8% overall)
- 74-79% coverage for 2022-2026 sales
- 301 routing key areas mapped with centroids
- Enables routing key validation and fallback geocoding

### 4. Rich Time Series Data
- 784k+ transactions spanning 16 years
- Monthly granularity for trend analysis
- Supports YoY, MoM, seasonal analysis
- Automated biweekly sync keeps data fresh

### 5. Unique Enrichment Data (Competitive Moat)
- 12k properties with bedroom counts
- 14k properties with property types
- 2026 data: 60-70% enriched (growing)
- **No competitor has this for historical sales**

---

## Weaknesses ⚠️

### 1. Limited Property Enrichment (MAJOR OPPORTUNITY)
- Only 1.6% have bedroom counts (12,265 / 784,854)
- Only 1.8% have property types (14,284 / 784,854)
- 2026: 60-70% enriched, but 2020-2025: 0-4% enriched
- **Gap:** 772k properties missing bedroom/type data

**Impact:** Limits usefulness of bedroom/type filters until coverage scales to 10%+ (78k properties).

### 2. Centroid Geocoding Issues
- 50,944 properties at low-quality centroid coordinates (6.5%)
- Multiple properties sharing same generic coordinates
- Affects search accuracy for radius queries
- Primarily older properties (pre-2021)

**Mitigation:** Ongoing Mapbox re-geocoding (17,813 fixed as of May 2026, 57,144 remaining).

### 3. Missing Coordinates
- 71,944 properties still need geocoding (9.2%)
- Primarily older properties (pre-2021)
- Prevents these properties from appearing in map searches

**Mitigation:** Monthly Mapbox batch geocoding using free tier (100k requests/month).

### 4. Low Eircode Coverage (Historical)
- Only 1% of 2020 sales have Eircodes (system was new)
- 51% of 2021 sales have Eircodes (transition year)
- Limits routing key validation for older properties

**Impact:** Lower confidence in geocode accuracy for pre-2022 properties.

### 5. No Property Size Data
- PPR doesn't include square meters/feet
- Prevents price per sqm analysis (sophisticated metric)
- Would require scraping from Daft.ie/MyHome.ie or user contribution

---

## User Engagement Analysis

### Current Engagement: NEAR-ZERO ⚠️

**Feedback/Contact Forms:** 23 submissions
- **Real submissions:** 0 (all automated tests)
- Test data: "Test Runner", spam tests with long strings
- Most recent: May 17, 2026 (automated test runs)

**Email Alerts:** 5 subscriptions
- **Real subscriptions:** ~1 (niall.murphy@gmail.com)
- Test data: test@example.com, test2@example.com, etc.
- Created: May 30, 2026
- All active, but email service likely not running yet

**Real subscription details:**
```
Email: niall.murphy@gmail.com
Area: D14 XT52 (Dublin)
Radius: 1.0km
Created: 2026-05-30
Status: Active ✓
```

### What This Means

**You're at the perfect stage to:**
1. ✅ Build features before marketing - no technical debt from users yet
2. ✅ Pivot strategy without breaking existing workflows
3. ✅ Validate assumptions before heavy investment

**Critical Finding:**
The site is live and functional, but has not yet achieved product-market fit or organic traction. Traffic acquisition is now the priority.

---

## Recommended Use Cases to Drive Traffic

### 🎯 HIGH IMPACT - Build These First

#### 1. Property Type & Bedroom Search
**Why:** You have 12k enriched properties - unique competitive advantage!

**Features:**
- Search by bedrooms: "3-bed houses in Dublin under €400k"
- Filter by type: apartments, semi-detached, detached, terraced
- Bedroom price trends: "How much does an extra bedroom cost in Cork?"
- Type-specific analytics: "Apartment vs house prices in Galway"

**SEO keywords:**
- "3 bedroom house prices dublin" (high volume)
- "apartment prices galway" (medium volume)
- "semi detached house prices cork" (medium volume)
- "4 bed house prices ireland" (medium volume)

**API endpoints to build:**
```python
GET /search/bedrooms?bedrooms=3&county=Dublin&max_price=400000
GET /search/property-type?type=apartment&county=Cork
GET /trends/by-bedrooms?county=Dublin
```

**Priority:** HIGH - Competitive moat, differentiates from MyHome.ie/Daft.ie

**Effort:** 2-3 weeks (frontend filters + API changes)

---

#### 2. Investment Property Calculator
**Why:** Attracts high-value users (investors, landlords, estate agents).

**Features:**
- Rental yield estimator (property price vs rental income)
- Capital appreciation tracker (historical price growth)
- Stamp duty calculator (already exists at `/mortgage`)
- Investment hotspots: "Best areas for rental yield in Ireland"
- Buy-to-let affordability: mortgage + rental income calculator

**SEO keywords:**
- "rental yield calculator ireland" (high volume)
- "best investment properties ireland" (high volume)
- "buy to let calculator ireland" (medium volume)
- "property investment returns ireland" (medium volume)
- "rental property prices cork" (long-tail)

**API endpoints:**
```python
GET /investment/yield?address=...&rental_income=1500
GET /investment/appreciation?address=...&years_back=5
GET /investment/hotspots?county=Dublin&sort=yield
```

**Priority:** HIGH - Drives repeat visits, high engagement

**Effort:** 2-3 weeks

---

#### 3. Neighborhood Comparison Tool
**Why:** Users compare multiple areas before buying.

**Features:**
- Side-by-side comparison (2-4 areas)
- Metrics: median price, price trends, sales volume, price/sqm (future)
- Map view showing both areas
- "Similar neighborhoods" recommender based on price/location

**SEO keywords:**
- "dublin 4 vs dublin 6 property prices" (long-tail, high intent)
- "cork city vs cork county house prices"
- "compare property prices ireland"
- "best value neighborhoods dublin"

**Technical:**
```typescript
// Frontend component
<NeighborhoodComparison areas={['Dublin 4', 'Dublin 6', 'Dublin 8']} />

// API endpoint
POST /compare
{
  "areas": [
    {"county": "Dublin", "routing_key": "D04"},
    {"county": "Dublin", "routing_key": "D06"}
  ]
}
```

**Priority:** HIGH - High engagement, drives repeat visits

**Effort:** 1-2 weeks

---

#### 4. First-Time Buyer Hub
**Why:** Large audience (25-35 age group), high search volume.

**Features:**
- Affordability calculator (income → max price with Help to Buy, First Home schemes)
- Starter home search (<€350k filter)
- First-time buyer trends: "What are FTBs actually paying?"
- Guide: "How much deposit do I need?"
- Mortgage approval calculator

**SEO keywords:**
- "first time buyer ireland property prices" (very high volume)
- "first home scheme prices" (high volume)
- "help to buy scheme properties" (high volume)
- "affordable homes ireland" (high volume)
- "starter homes dublin" (medium volume)

**Content pages to create:**
- `/first-time-buyer` - landing page
- `/first-time-buyer/affordability-calculator`
- `/first-time-buyer/guide`
- `/first-time-buyer/affordable-areas`

**Priority:** HIGH - Large addressable audience, clear SEO opportunity

**Effort:** 2-3 weeks

---

### 🚀 MEDIUM IMPACT - Build These Second

#### 5. Market Intelligence Reports (Automated)
**Why:** Attracts media, estate agents, investors; great for backlinks.

**Features:**
- Monthly market report: county-by-county price changes
- Hotspot detector: "Fastest growing areas this month"
- Price drop alerts: "Areas with declining prices"
- Volume trends: "Where are people buying?"
- Export to PDF for sharing

**SEO keywords:**
- "irish property market report june 2026"
- "property price trends ireland 2026"
- "fastest growing property markets ireland"

**Technical:**
```python
# Automated monthly generation
python3 scripts/generate_market_report.py --month 2026-06

# API endpoints
GET /reports/monthly?year=2026&month=6
GET /reports/hotspots?metric=price_growth
```

**Priority:** MEDIUM - Great for authority/backlinks

**Effort:** 2-3 weeks

---

#### 6. Price Alert System (Expand Existing)
**Why:** You already have `email_alerts` table - just need the service!

**Features:**
- Alert when new sales in area are below target price
- Alert on price trends: "Prices in Dublin 4 dropped 5% this month"
- Saved searches with notifications
- Weekly digest emails

**SEO keywords:**
- "property price alerts ireland"
- "house price notifications"
- "property price tracker ireland"

**Technical:**
```python
# Cron job to run daily
python3 scripts/send_price_alerts.py

# Uses existing email_alerts table
SELECT * FROM email_alerts WHERE is_active = TRUE
```

**Priority:** MEDIUM - Table exists, just need email service (SendGrid/Mailgun)

**Effort:** 1 week

---

#### 7. Price Per Square Meter Analysis
**Why:** More sophisticated metric than raw price.

**Challenge:** PPR doesn't include property size data.

**Solutions:**
- Scrape size data from Daft.ie/MyHome.ie historical listings
- User-contributed sizes (crowdsource)
- Estimate from bedrooms/type (rough heuristic)

**Features:**
- €/sqm trends by area
- €/sqm comparisons (Dublin vs Cork)
- Filter properties by €/sqm range

**SEO keywords:**
- "price per square meter dublin"
- "cost per square foot ireland"
- "property price per sqm cork"

**Priority:** MEDIUM - Requires additional data enrichment

**Effort:** 3-4 weeks (data collection is bottleneck)

---

#### 8. School Catchment Area Search
**Why:** Major decision factor for families.

**Features:**
- Search properties within X km of specific schools
- School quality ratings (integrate with Department of Education data)
- "Best schools in Dublin" + nearby properties
- Map overlay: school catchment boundaries + property prices

**SEO keywords:**
- "house prices near [school name]" (high volume × 100s of schools)
- "property prices school catchment dublin"
- "homes near good schools ireland"

**Technical:**
```python
# New table needed
CREATE TABLE schools (
  id SERIAL PRIMARY KEY,
  name TEXT,
  address TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  geog GEOGRAPHY(Point, 4326),
  rating TEXT,
  type TEXT  -- primary, secondary
);

# API endpoint
GET /search/schools?school_id=123&radius_km=2&max_price=500000
```

**Priority:** MEDIUM - Requires school database creation

**Effort:** 2-3 weeks

---

### 💡 LONGER-TERM IDEAS

#### 9. Predictive Price Model
**Features:** ML model predicting future property values
**Challenge:** Needs 10%+ enrichment coverage for training
**Effort:** 4-6 weeks + data science expertise

#### 10. Renovation ROI Calculator
**Features:** "Should I renovate before selling?"
**Challenge:** Requires additional datasets (renovation costs, BER ratings)
**Effort:** 3-4 weeks

#### 11. Commuter-Friendly Search
**Features:** "Properties within 45min commute of Dublin"
**Challenge:** Google Maps API costs, complex implementation
**Effort:** 2-3 weeks

---

## Action Plan: Next 90 Days

### Week 1-2: Critical Infrastructure (DO FIRST)

**1. Enable Email Alert Service**
```bash
# Install email service
pip install sendgrid  # or mailgun

# Create backend/send_alerts.py
# - Query email_alerts table
# - Find new sales in user's area since last_sent_at
# - Send digest email
# - Update last_sent_at

# Add to crontab (daily at 9am)
0 9 * * * cd /path/to/project && python3 backend/send_alerts.py
```

**Why first:** You have 1-5 real signups. Don't lose them! Validates product-market fit.

**2. Generate XML Sitemap**
```bash
python3 scripts/generate_sitemap.py
# Submit to Google Search Console
# Submit to Bing Webmaster Tools
```

**3. Create robots.txt**
```
User-agent: *
Allow: /
Sitemap: https://homeiq.ie/sitemap.xml
Disallow: /manual-geocode
```

**4. Add Canonical URLs**
```tsx
// In usePageMeta hook
<link rel="canonical" href={`https://homeiq.ie${window.location.pathname}`} />
```

**5. Submit to Search Engines**
- Google Search Console: https://search.google.com/search-console
- Bing Webmaster Tools: https://www.bing.com/webmasters
- Monitor indexing status weekly

---

### Week 3-4: SEO Landing Pages (High Traffic Keywords)

**Create these pages:**

1. **`/property-price-register`** - Target "property price register ireland"
   - Explain what PPR is, how to use it
   - Embed search functionality
   - Link to county pages

2. **`/house-prices-ireland`** - Target "house prices ireland"
   - National overview with map
   - County-by-county breakdown
   - Recent trends summary

3. **`/dublin-house-prices`** - Target "dublin house prices"
   - Dublin-specific landing page
   - Postcode breakdown
   - Neighborhood comparisons

4. **`/property-price-trends`** - Target "irish property price trends"
   - Interactive trend charts
   - YoY analysis
   - Forecasting section

5. **`/eircode-property-search`** - Target "eircode property search"
   - Eircode-specific search page
   - Routing key explainer
   - Map overlay

**Template:**
```tsx
// High-value SEO content
<h1>Property Price Register Ireland - Official Sales Data</h1>
<p>Search 784,000+ Irish property sales from 2010-2026...</p>

// Embed search functionality
<SearchPanel />

// Rich content (200-300 words)
<article>
  <h2>How to Use the Property Price Register</h2>
  ...
</article>

// Internal links to county pages
<section>
  <h2>Explore by County</h2>
  <CountyLinks />
</section>
```

---

### Week 5-6: Property Type & Bedroom Search

**1. Add filters to SearchPanel.tsx:**
```tsx
<select name="bedrooms">
  <option value="">Any bedrooms</option>
  <option value="1">1 bed</option>
  <option value="2">2 bed</option>
  <option value="3">3 bed</option>
  <option value="4">4+ bed</option>
</select>

<select name="property_type">
  <option value="">Any type</option>
  <option value="apartment">Apartment</option>
  <option value="semi-detached">Semi-Detached</option>
  <option value="detached">Detached</option>
  <option value="terraced">Terraced</option>
</select>
```

**2. Update API:**
```python
# backend/main.py
@app.get("/search")
async def search(
    q: str,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    # ... existing params
):
    conditions = []
    
    if bedrooms:
        conditions.append(f"bedrooms = {bedrooms}")
    
    if property_type:
        conditions.append(f"property_type = '{property_type}'")
    
    # Add to WHERE clause
    where_clause = " AND ".join(conditions)
```

**3. Create dedicated pages:**
- `/bedrooms` - Bedroom-specific landing page
- `/property-type` - Type-specific landing page
- `/3-bed-houses-dublin` - Example high-traffic page

**4. Add type-specific trends:**
```python
GET /trends/by-bedrooms?county=Dublin
# Returns separate series for 1-bed, 2-bed, 3-bed, 4-bed prices
```

---

### Week 7-8: Neighborhood Comparison Tool

**1. Create `/compare` page:**
```tsx
// frontend/src/pages/ComparePage.tsx
<NeighborhoodComparison 
  areas={['Dublin 4', 'Dublin 6', 'Dublin 8']} 
/>
```

**2. Build API endpoint:**
```python
@app.post("/compare")
async def compare_areas(areas: List[AreaQuery]):
    results = []
    for area in areas:
        # Get median price, trends, sales volume
        stats = await get_area_stats(area)
        results.append(stats)
    return results
```

**3. UI components:**
- Side-by-side metrics table
- Overlay trend charts
- Map view with both areas highlighted
- Share comparison results (social media)

---

### Week 9-12: First-Time Buyer Hub

**1. Landing page: `/first-time-buyer`**
- Hero: "How Much Can You Afford?"
- Embedded affordability calculator
- Guide sections (deposit, Help to Buy, First Home)
- Starter home search (<€350k)

**2. Affordability calculator:**
```tsx
// Input: salary, deposit, loan term
// Output: max affordable price
// Consider: Help to Buy grant, First Home scheme limits
// Show: monthly repayment estimate
```

**3. Content guides:**
- "First-Time Buyer's Guide to Irish Property Prices"
- "Understanding Help to Buy Scheme"
- "How Much Deposit Do I Need?"
- "Best Areas for First-Time Buyers in Dublin"

**4. SEO optimization:**
- Rich snippets (FAQ schema)
- Internal linking to county pages
- Social share buttons

---

### Ongoing: Data Enrichment (Critical)

**Goal:** Scale enrichment from 1.6% to 10%+ (78k properties)

**Process:**
```bash
# Run daily until target reached
python3 scripts/enrich_recent_properties.py --months 24 --limit 1000

# Monitor progress
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM properties WHERE bedrooms IS NOT NULL')
print(f'Enriched: {cur.fetchone()[0]:,}')
conn.close()
"
```

**Priority order:**
1. 2025-2026 properties (most recent, highest value)
2. Dublin properties (highest volume, most searched)
3. >€500k properties (investment audience)
4. 2022-2024 properties (backfill)

**Target milestones:**
- Week 4: 20,000 enriched (2.5%)
- Week 8: 40,000 enriched (5%)
- Week 12: 78,000 enriched (10%)

---

## Traffic Acquisition Strategy

### Phase 1: SEO Foundation (Weeks 1-4)
- ✅ Sitemap submitted to Google/Bing
- ✅ robots.txt created
- ✅ 10+ landing pages for high-volume keywords
- ✅ Canonical URLs added
- ✅ Google Search Console configured

**Expected result:** 100-200 organic visitors/month by Week 8

---

### Phase 2: Community Launch (Weeks 3-5)

**Reddit/Boards.ie posts (NOT ads, helpful content):**

Post in:
- r/irishpersonalfinance (90k members)
- r/ireland (500k members)
- boards.ie Property Forum (active community)

**Example post:**
> **"I built a free tool to search 16 years of Irish property prices - feedback welcome!"**
> 
> After getting frustrated with MyHome.ie's limited search, I built HomeIQ.ie using the public PPR data. You can:
> - Search by address/Eircode with customizable radius
> - See price trends over time (2010-2026)
> - Filter by price range, date, bedrooms, property type
> - Draw custom search areas on a map
> 
> It's completely free and covers 784k sales since 2010. Would love feedback from this community!
> 
> [Link to homeiq.ie]

**Follow-up engagement:**
- Answer questions in comments
- Take feature requests
- Share interesting findings ("TIL Dublin 4 prices dropped 5% this month")
- Weekly "Property Price Insight" posts

**Expected result:** 500-1,000 visitors from initial post, 50-100/month ongoing

---

### Phase 3: Content Marketing (Weeks 6+)

**Create `/blog` section with regular posts:**

**Monthly posts:**
- "Irish Property Market Report - [Month] 2026"
- "[County] Property Price Trends - [Month]"
- "Fastest Growing Property Markets This Month"

**Evergreen guides:**
- "Complete Guide to Dublin Property Prices by Postcode"
- "Cork vs Galway vs Limerick: Property Price Comparison"
- "Understanding the Property Price Register"
- "How to Use Eircodes for Property Search"

**Data insights:**
- "Where First-Time Buyers Are Actually Buying in 2026"
- "The Most Expensive Streets in Dublin"
- "Best Value Neighborhoods by County"

**SEO optimization:**
- 1,000+ word guides
- Internal linking to search pages
- Featured images for social sharing
- FAQ schema for rich snippets

**Expected result:** 200-500 organic visitors/month from blog content by Month 3

---

### Phase 4: Email Marketing (Weeks 6+)

**Once email alerts are working:**

**Weekly digest:**
- "Dublin Property Prices - Week of [Date]"
- Highlight interesting trends
- Featured neighborhoods
- New properties in subscriber's area

**Monthly newsletter:**
- Market overview
- County-by-county analysis
- Investment opportunities
- Feature announcements

**Viral growth:**
- "Share this with a friend" CTA
- Referral program (future)
- Social share buttons in emails

**Expected result:** 20% week-over-week growth in subscribers

---

### Phase 5: Backlink Building (Ongoing)

**Get listed in directories:**
- PropertyPrice.ie mentions
- Irish property forums
- Irish tech/startup directories

**Media outreach:**
- Press release: "New Free Tool for Irish Property Price Search"
- Pitch to TheJournal.ie, BreakingNews.ie, Irish Times
- Offer data insights: "Analysis: Where Irish Property Prices Rose Most in 2026"
- Quote property statistics: "Source: HomeIQ.ie analysis of PPR data"

**Data journalism opportunities:**
- Publish monthly/quarterly market reports
- Create shareable infographics (price heat maps)
- Offer API access for journalists/researchers (future)

**Partnership opportunities:**
- Estate agents (embed search widget)
- Mortgage brokers (affordability calculator)
- Property investment groups (ROI calculator)

**Expected result:** 5-10 quality backlinks by Month 6

---

## Success Metrics

### Next 30 Days:
- ✅ 50+ real email alert signups (currently: ~1)
- ✅ 500+ unique visitors (currently: unknown)
- ✅ 5+ real feedback submissions (currently: 0)
- ✅ Top 20 ranking for 1 target keyword in Google
- ✅ 20,000+ enriched properties (currently: 12,265)

### Next 90 Days:
- ✅ 500+ email subscribers
- ✅ 5,000+ unique visitors/month
- ✅ Top 10 ranking for 3-5 target keywords
- ✅ 1-2 backlinks from Irish property websites
- ✅ 78,000+ enriched properties (10% coverage)

### Next 6 Months:
- ✅ 2,000+ email subscribers
- ✅ 20,000+ unique visitors/month
- ✅ Top 3 ranking for primary keywords
- ✅ 5-10 quality backlinks
- ✅ 200,000+ enriched properties (25% coverage)

### Next 12 Months:
- ✅ 10,000+ email subscribers
- ✅ 100,000+ unique visitors/month
- ✅ Established as authoritative Irish property data source
- ✅ Revenue model (premium features, API access, etc.)

---

## Key Takeaways

### Your Competitive Advantages:
1. ✅ **Complete historical data** - 16 years, 784k properties
2. ✅ **High geocoding coverage** - 90.8% with coordinates
3. ✅ **Strong Eircode coverage** - 74%+ for recent sales
4. ✅ **Unique enrichment data** - 12k properties with bedrooms/type (competitors don't have this for historical sales)
5. ✅ **Fast spatial search** - PostGIS enables radius/polygon queries
6. ✅ **Free Mapbox credits** - 100k/month for continued geocoding

### Biggest Opportunities:
1. 🎯 **Scale enrichment** - 1.6% → 10%+ coverage (differentiator from MyHome.ie/Daft.ie)
2. 🎯 **SEO landing pages** - Target high-volume keywords (100k+ searches/month)
3. 🎯 **Email alert service** - Table exists, just need email service running
4. 🎯 **First-time buyer audience** - Large, underserved market
5. 🎯 **Investment calculators** - Attract high-value repeat visitors

### Critical First Steps:
1. **Week 1:** Enable email alerts (don't lose existing signups!)
2. **Week 1-2:** SEO foundation (sitemap, robots.txt, canonical URLs)
3. **Week 2-4:** 5 high-traffic landing pages
4. **Week 3-5:** Reddit/community launch posts
5. **Ongoing:** Daily enrichment runs (target 10% coverage)

### Reality Check:
You have excellent data infrastructure and product foundation, but **near-zero organic traction** yet. The next 90 days are critical for:
- Validating product-market fit (do people use email alerts?)
- Testing feature priorities (which use cases drive engagement?)
- Achieving SEO momentum (indexing takes 4-8 weeks)

Focus on **shipping features quickly** and **measuring user engagement** rather than perfecting every detail. The data quality is already strong - now you need users to validate your direction.

---

## Monitoring & Analytics

### Weekly Metrics to Track:

**Traffic:**
- Unique visitors (Vercel Analytics)
- Page views
- Top landing pages
- Traffic sources (organic, direct, referral)

**Engagement:**
- Bounce rate
- Average session duration
- Pages per session
- Search queries performed

**Conversion:**
- Email alert signups
- Feedback submissions
- Contact form submissions
- Social shares

**SEO:**
- Google Search Console impressions
- Click-through rate from search
- Average position for target keywords
- Indexed pages count

**Data Quality:**
- Enrichment coverage (% with bedrooms/type)
- Geocoding coverage
- Centroid cleanup progress
- Database size growth

### Monthly Reviews:

**Traffic analysis:**
- Which landing pages drive most traffic?
- Which search queries convert best?
- What's the user journey? (entry → search → exit)

**Feature validation:**
- Which filters are most used? (bedrooms, type, price, etc.)
- Do users engage with trends charts?
- Email alert retention rate?

**SEO performance:**
- Ranking improvements for target keywords?
- New pages indexed?
- Backlinks acquired?

**Pivot decisions:**
- Which use cases to prioritize next?
- What content to create?
- Where to invest development time?

---

## Conclusion

HomeIQ.ie has a **strong data foundation** (784k properties, 90.8% geocoded, unique enrichment data) but needs **user acquisition** to achieve product-market fit.

**The path forward:**
1. Enable email alerts immediately (validate demand)
2. Build SEO landing pages (organic traffic)
3. Scale enrichment to 10%+ (competitive moat)
4. Ship bedroom/type search (differentiator)
5. Launch on Reddit/communities (early users)
6. Measure, learn, iterate

The 12k enriched properties are your **unique competitive advantage** - no other site has bedroom/type data for historical Irish property sales. Scale this to 78k+ properties and you have a defensible moat that drives traffic.

**Next step:** Start with Week 1 action items (email alerts + SEO foundation) and measure user engagement to validate product direction.

---

**Document maintained by:** Claude Code  
**Last updated:** 2026-06-13  
**Next review:** 2026-07-13 (monthly)
