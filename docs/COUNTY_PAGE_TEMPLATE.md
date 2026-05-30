# County Page Content Template

Use this template to expand each county page with SEO-optimized content.

## Template Structure

```tsx
// In CountyPage.tsx, add after PageHeader:

<div className="county-content">
  {/* SEO-optimized intro */}
  <section className="county-intro">
    <h2>Property Prices in County {countyName}</h2>
    <p>
      [150-200 word intro paragraph with key statistics and context]
      Example: "County {name} property prices in 2024 showed [trend]. 
      The median property price reached €[amount], with [X] residential 
      sales recorded. Popular areas include [list 3-5 areas]. 
      This represents a [X]% [increase/decrease] compared to 2023..."
    </p>
  </section>

  {/* Key statistics box */}
  <section className="county-stats">
    <h3>Market Statistics (2024)</h3>
    <div className="stats-grid">
      <div className="stat">
        <span className="stat-label">Total Sales</span>
        <span className="stat-value">{totalSales}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Median Price</span>
        <span className="stat-value">€{medianPrice}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Average Price</span>
        <span className="stat-value">€{avgPrice}</span>
      </div>
      <div className="stat">
        <span className="stat-label">YoY Change</span>
        <span className="stat-value">{yoyChange}%</span>
      </div>
    </div>
  </section>

  {/* Market overview */}
  <section className="county-overview">
    <h3>Market Overview</h3>
    <p>
      [200-300 words about the county's property market]
      Include:
      - Current market conditions
      - Price trends over past 1-2 years
      - Types of properties common in the area
      - Factors affecting prices (commuter towns, local economy, amenities)
      - Notable developments or changes
    </p>
  </section>

  {/* Popular areas */}
  <section className="popular-areas">
    <h3>Popular Areas in County {countyName}</h3>
    <ul>
      <li><Link to="/area/{area1}">{Area1Name}</Link> - Brief description</li>
      <li><Link to="/area/{area2}">{Area2Name}</Link> - Brief description</li>
      <li><Link to="/area/{area3}">{Area3Name}</Link> - Brief description</li>
      {/* Add 5-10 total */}
    </ul>
  </section>

  {/* Price trends chart */}
  <section className="county-trends">
    <h3>Price Trends</h3>
    <TrendsChart data={trendsData} />
    <p>[50-100 word commentary on the chart]</p>
  </section>

  {/* FAQs */}
  <section className="county-faqs">
    <h3>Frequently Asked Questions</h3>
    
    <div className="faq-item">
      <h4>What is the average house price in County {countyName}?</h4>
      <p>[Answer with specific data and context]</p>
    </div>

    <div className="faq-item">
      <h4>Which areas in County {countyName} are most affordable?</h4>
      <p>[List 3-5 affordable areas with approximate prices]</p>
    </div>

    <div className="faq-item">
      <h4>How have property prices changed in County {countyName}?</h4>
      <p>[5-year trend summary with key statistics]</p>
    </div>

    <div className="faq-item">
      <h4>What types of properties are common in County {countyName}?</h4>
      <p>[Describe common property types: detached, semi-detached, apartments, etc.]</p>
    </div>

    <div className="faq-item">
      <h4>Is County {countyName} a good place to invest in property?</h4>
      <p>[Balanced answer discussing factors like price growth, rental demand, location]</p>
    </div>
  </section>

  {/* Related counties */}
  <section className="related-counties">
    <h3>Nearby Counties</h3>
    <div className="county-links">
      <Link to="/county/{neighbor1}">{Neighbor1}</Link>
      <Link to="/county/{neighbor2}">{Neighbor2}</Link>
      <Link to="/county/{neighbor3}">{Neighbor3}</Link>
    </div>
  </section>
</div>
```

## County-Specific Content Examples

### County Dublin
**Intro:** "County Dublin property prices continue to lead Ireland's property market, with a median price of €520,000 in 2024. Over 15,000 residential sales were recorded across Dublin's 22 postal districts. Popular areas include Ballsbridge, Dalkey, and Howth on the southside, while Clontarf, Drumcondra, and Malahide attract buyers on the northside. Dublin prices increased 4.2% year-on-year, driven by limited supply and strong demand from both domestic buyers and returning emigrants."

**Popular Areas:**
- Ballsbridge - Prestigious D4 location, Victorian homes, embassy district
- Dalkey - Coastal village, period properties, celebrity residents
- Clontarf - Seafront living, family homes, excellent schools
- Ranelagh - Village atmosphere, cafes, period terraces
- Howth - Coastal town, harbor views, strong community
- Drumcondra - Near city center, good value, transport links
- Dundrum - Shopping center, new developments, family-friendly
- Blackrock - South Dublin, period homes, coastal walks

**FAQs:**
Q: What is the average house price in Dublin?
A: The average house price in Dublin is approximately €520,000 (2024), though this varies significantly by postal district. Dublin 4, 6, and 14 command premium prices (€700k-€1m+), while Dublin 10, 11, and 22 offer more affordable options (€300k-€400k).

### County Cork
**Intro:** "County Cork property prices in 2024 averaged €320,000, with over 4,500 sales recorded. Ireland's largest county offers diverse options from Cork city apartments to coastal homes in Kinsale and family houses in commuter towns like Carrigaline and Ballincollig. Prices rose 6.1% year-on-year, outpacing the national average as Cork's tech sector and quality of life attract relocating professionals."

**Popular Areas:**
- Cork City Centre - Urban apartments, period terraces, city living
- Douglas - Upscale suburb, large family homes, shopping
- Ballincollig - Commuter town, new estates, family-friendly
- Carrigaline - Growing town, schools, M28 motorway access
- Cobh - Historic port town, Victorian architecture, waterfront
- Midleton - Market town, distillery, East Cork gateway

### County Galway
**Intro:** "County Galway property prices averaged €285,000 in 2024 across 2,800+ sales. Galway city commands premium prices while Connemara offers rural retreats and coastal properties. Commuter towns like Oranmore and Athenry provide family homes with city access. Prices increased 5.8% year-on-year, reflecting Galway's growing reputation as a tech hub and lifestyle destination."

**Popular Areas:**
- Galway City - Urban center, compact area, high demand
- Salthill - Seaside promenade, apartments, holiday homes
- Oranmore - Commuter town, new developments, motorway access
- Tuam - Historic town, affordability, good schools
- Connemara - Rural properties, cottages, scenic locations

### County Wicklow
**Intro:** "County Wicklow, the 'Garden of Ireland,' saw median property prices of €380,000 in 2024 across 2,200+ sales. Proximity to Dublin makes coastal towns like Bray and Greystones highly sought after, while inland towns offer better value. Prices rose 5.2% year-on-year as remote workers seek quality of life outside Dublin."

**Popular Areas:**
- Bray - Largest town, seafront, DART access, Victorian terraces
- Greystones - Affluent coastal town, marina, strong prices
- Wicklow Town - County town, harbor, period properties
- Arklow - Coastal town, affordability, industrial heritage
- Enniskerry - Village charm, mountain views, tourism hub

## Writing Tips

### SEO Best Practices
1. **Use target keywords naturally:**
   - "[County] property prices"
   - "house prices in [County]"
   - "property market [County]"
   - "[County] real estate"

2. **Include specific data:**
   - Exact prices (median, average)
   - Transaction volumes
   - Year-on-year changes
   - Date ranges

3. **Write for users first:**
   - Answer common questions
   - Provide actionable information
   - Use clear, simple language
   - Break up long paragraphs

4. **Internal linking:**
   - Link to area pages
   - Link to nearby counties
   - Link to relevant features (map search, trends)

5. **Update regularly:**
   - Add "Last updated: [date]" at top
   - Refresh statistics quarterly
   - Update trends commentary

### Tone & Style
- **Informative but conversational:** "County Dublin leads Ireland's property market" not "It has been observed that Dublin..."
- **Data-driven:** Always cite specific numbers
- **Balanced:** Acknowledge both opportunities and challenges
- **Local knowledge:** Mention landmarks, transport, amenities
- **User-focused:** What does the buyer/seller need to know?

## Data Sources

Get statistics from:
```sql
-- Total sales and median price for a county in 2024
SELECT 
  COUNT(*) as total_sales,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
  AVG(price) as avg_price
FROM properties
WHERE county = 'Dublin'
  AND EXTRACT(YEAR FROM sale_date) = 2024
  AND not_full_market_price = FALSE;

-- Year-on-year comparison
SELECT 
  EXTRACT(YEAR FROM sale_date) as year,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
FROM properties
WHERE county = 'Dublin'
  AND EXTRACT(YEAR FROM sale_date) IN (2023, 2024)
  AND not_full_market_price = FALSE
GROUP BY year
ORDER BY year;

-- Popular areas in a county
SELECT 
  REGEXP_REPLACE(address, ',.*$', '') as area,
  COUNT(*) as sales,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
FROM properties
WHERE county = 'Dublin'
  AND EXTRACT(YEAR FROM sale_date) = 2024
  AND not_full_market_price = FALSE
GROUP BY area
HAVING COUNT(*) > 50
ORDER BY sales DESC
LIMIT 10;
```

## Implementation Checklist

For each county:
- [ ] Research county context (Wikipedia, local news)
- [ ] Query database for statistics
- [ ] Write intro paragraph (150-200 words)
- [ ] Create market overview (200-300 words)
- [ ] List 5-10 popular areas with descriptions
- [ ] Write 5 FAQ answers
- [ ] List 3-5 nearby counties for links
- [ ] Add last updated date
- [ ] Review for keyword usage
- [ ] Check internal links work
- [ ] Preview on mobile and desktop

## Priority Order

Start with high-traffic potential counties:
1. **Dublin** (highest search volume)
2. **Cork** (second largest city)
3. **Galway** (third largest city)
4. **Kildare** (Dublin commuter belt)
5. **Wicklow** (Dublin commuter belt)
6. **Meath** (Dublin commuter belt)
7. **Limerick** (fourth largest city)
8. **Waterford** (fifth largest city)
9. Then remaining counties alphabetically

Aim for 2-3 counties per week = all 26 counties completed in 2-3 months.
