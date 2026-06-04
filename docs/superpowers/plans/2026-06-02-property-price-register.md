# Property Price Register Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an SEO-optimized landing page explaining Ireland's Property Price Register, its limitations as taxation data, and HomeIQ's data quality enhancements.

**Architecture:** Single static page component following existing AboutPage pattern. Uses PageHeader component, usePageMeta hook for SEO, and reuses existing CSS classes. Includes structured data for breadcrumbs and internal/external links for SEO value.

**Tech Stack:** React 18, TypeScript, React Router, existing component library

---

## File Structure

**New Files:**
- `frontend/src/pages/PropertyPriceRegisterPage.tsx` - Main page component with full content

**Modified Files:**
- `frontend/src/main.tsx:34` - Add route after `/about` route
- `frontend/src/pages/AboutPage.tsx:50-57` - Update PPR source description with link

---

## Task 1: Create PropertyPriceRegisterPage Component

**Files:**
- Create: `frontend/src/pages/PropertyPriceRegisterPage.tsx`

- [ ] **Step 1: Create page component with imports and metadata**

```tsx
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";

export default function PropertyPriceRegisterPage() {
  usePageMeta(
    "Property Price Register Ireland | Complete Guide & Enhanced Data",
    "Understand Ireland's Property Price Register, its limitations as a taxation record, and how HomeIQ enhances the data with geocoding validation and address normalization for better property search.",
  );
```

- [ ] **Step 2: Add structured data script and opening markup**

```tsx
  return (
    <div className="static-page">
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://homeiq.ie"},
            {"@type": "ListItem", "position": 2, "name": "Property Price Register", "item": "https://homeiq.ie/property-price-register"}
          ]
        })}
      </script>
      <PageHeader title="Understanding Ireland's Property Price Register" />
      <main className="static-content">
```

- [ ] **Step 3: Add hero section with lead paragraph**

```tsx
        <section className="about-section">
          <p className="about-lead">
            Ireland's Property Price Register (PPR) is the official government record of every 
            residential property sale in the country since 2010. Created under the Finance Act 2010 
            and managed by the Property Services Regulatory Authority (PSRA), it provides unprecedented 
            transparency into the Irish housing market with over 784,000 recorded transactions. This 
            guide explains what the PPR is, how it works, its limitations as a taxation-based system, 
            and how HomeIQ transforms this raw data into powerful property intelligence tools.
          </p>
        </section>
```

- [ ] **Step 4: Add "What is the Property Price Register?" section**

```tsx
        <section className="about-section">
          <h2>What is the Property Price Register?</h2>
          <p>
            The{" "}
            <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer">
              Property Price Register
            </a>{" "}
            is Ireland's comprehensive database of residential property sales. Established following 
            the 2008 financial crisis to bring transparency to the property market, it is a legal 
            requirement that all property sales over €100,000 be registered.
          </p>
          <p>
            Managed by the{" "}
            <a href="https://www.psprauth.ie" target="_blank" rel="noopener noreferrer">
              Property Services Regulatory Authority (PSRA)
            </a>, the register contains detailed information about every qualifying residential sale 
            including the property address, sale price, date of sale, and whether it represents a full 
            market price transaction. This public dataset provides the foundation for understanding 
            Irish property market trends, regional variations, and long-term price movements.
          </p>
        </section>
```

- [ ] **Step 5: Add "How the PPR Works: A Taxation Record" section**

```tsx
        <section className="about-section">
          <h2>How the PPR Works: A Taxation Record</h2>
          <p>
            Understanding the origins of PPR data is crucial to understanding both its strengths and 
            limitations. The Property Price Register doesn't collect data directly from property sales. 
            Instead, it receives information from Ireland's Revenue Commissioners as part of the stamp 
            duty collection process. When a property transaction is completed, solicitors submit sales 
            details to Revenue as part of stamp duty compliance, and this information flows into the PPR.
          </p>
          <p>
            This taxation connection creates comprehensive coverage—since stamp duty is legally required, 
            virtually all qualifying sales are captured. However, it also means the system was designed 
            primarily for tax collection, not property research. The data structure reflects taxation 
            requirements rather than the needs of property buyers, investors, or market analysts.
          </p>
          <p><strong>What's included in PPR data:</strong></p>
          <ul>
            <li>Property address (text format)</li>
            <li>Sale price in euros</li>
            <li>Date of sale</li>
            <li>Property description (new/secondhand)</li>
            <li>Market status (full market price / not full market price)</li>
            <li>VAT exclusivity indicator</li>
          </ul>
          <p><strong>What's NOT included in raw PPR data:</strong></p>
          <ul>
            <li>Geographic coordinates (latitude/longitude for mapping)</li>
            <li>Eircodes for properties sold before 2015</li>
            <li>Standardized address formatting</li>
            <li>Property size, bedrooms, or features</li>
            <li>Seller or buyer information (privacy protected)</li>
          </ul>
        </section>
```

- [ ] **Step 6: Add "Understanding the Limitations" section**

```tsx
        <section className="about-section">
          <h2>Understanding the Limitations</h2>
          <p>
            While the Property Price Register provides invaluable market transparency, its design as a 
            taxation record creates practical challenges for property research and analysis.
          </p>
          
          <h3>No Geographic Coordinates</h3>
          <p>
            The most significant limitation for modern property search is the absence of geographic 
            coordinates. The original PPR contains only text addresses—no latitude/longitude data for 
            mapping. This means users cannot search "properties near me," cannot visualize market 
            patterns on a map, and have no way to perform radius-based searches or area comparisons. 
            Questions like "What are properties selling for within 3km of this address?" are impossible 
            to answer with raw PPR data.
          </p>

          <h3>Inconsistent Address Formatting</h3>
          <p>
            Address data in the PPR reflects how solicitors entered it—with varying capitalization 
            (MAIN STREET vs Main Street vs main street), different abbreviations (Rd, Road, RD), 
            inconsistent spacing, and punctuation variations. This makes text searching unreliable. 
            You might search for "Station Road" and miss results recorded as "Station Rd" or "STATION RD."
          </p>

          <h3>Missing Eircodes for Older Properties</h3>
          <p>
            Ireland's Eircode postcode system launched in 2015. Properties sold between 2010 and 2015 
            typically have no Eircode in the PPR, making it difficult to pinpoint exact locations for 
            over 200,000 older sales. Even when addresses are provided, without a standardized postcode 
            system, identifying the precise property can be challenging, especially in rural areas or 
            streets with similar names across different towns.
          </p>

          <h3>Limited Search Capabilities</h3>
          <p>
            The official PPR website offers basic text search functionality only. There's no filtering 
            by distance, no map-based property selection, no polygon drawing tools for custom area 
            searches, and no easy way to analyze price trends for specific neighborhoods. Comparing 
            properties across nearby areas or tracking micro-market trends requires manual data export 
            and analysis.
          </p>

          <h3>"Not Full Market Price" Transactions</h3>
          <p>
            The PPR includes all registered transactions, including family transfers, equity releases, 
            and other non-arms-length sales marked as "not full market price." While this transparency 
            is valuable, it means users need to manually filter these transactions to get accurate market 
            trends. The official site doesn't make this distinction obvious, potentially skewing price 
            analyses if these sales aren't excluded.
          </p>
        </section>
```

- [ ] **Step 7: Add "How HomeIQ Enhances the Data" section**

```tsx
        <section className="about-section">
          <h2>How HomeIQ Enhances the Data</h2>
          <p>
            At HomeIQ, we take the raw PPR data and apply extensive validation, geocoding, and 
            normalization to make it more accurate, searchable, and useful for property research. 
            Our goal is to preserve the comprehensive coverage and transparency of the official register 
            while addressing its practical limitations for modern property search.
          </p>

          <dl className="about-sources">
            <div className="about-source">
              <dt>Address Normalization</dt>
              <dd>
                Standardized formatting for all 784,000 properties: consistent capitalization, 
                abbreviations, and structure for more reliable search results. Whether an address was 
                originally entered as "MAIN STREET," "Main St," or "main street," our system recognizes 
                them as the same location.
              </dd>
            </div>

            <div className="about-source">
              <dt>Geocoding &amp; Coordinate Validation</dt>
              <dd>
                Added geographic coordinates to 78% of properties (614,200+ locations) with multi-layer 
                validation to ensure accuracy. Recent properties (2022-2024) have 89-91% geocoding 
                coverage. Each coordinate undergoes validation against Ireland's geographic boundaries, 
                county borders, and known routing key centroids.
              </dd>
            </div>

            <div className="about-source">
              <dt>Quality Scoring System</dt>
              <dd>
                Every geocoded property receives a quality score based on precision level—rooftop, parcel, 
                street, or locality—to ensure reliable map positioning. We reject low-confidence coordinates 
                and continuously improve accuracy through batch re-geocoding when better data sources become 
                available.
              </dd>
            </div>

            <div className="about-source">
              <dt>Eircode Enrichment</dt>
              <dd>
                Enhanced postcode coverage through daily enrichment processes, bringing Eircode data to 
                30% of all properties and 74-79% of recent sales. This includes routing key extraction 
                (the first three characters of each Eircode) for area-based analysis and validation.
              </dd>
            </div>

            <div className="about-source">
              <dt>Centroid Cleanup</dt>
              <dd>
                Identified and re-geocoded properties stuck at generic town or county center coordinates 
                to provide accurate property-specific locations. Our validation systems detect when multiple 
                properties share suspiciously identical coordinates and flag them for improved geocoding.
              </dd>
            </div>
          </dl>

          <p><strong>The Result:</strong></p>
          <ul>
            <li>Map-based radius search (2km, 5km, 10km, 20km options)</li>
            <li>Interactive polygon drawing tools for custom area selection</li>
            <li>Accurate location markers showing actual property positions</li>
            <li>County and area filtering with smart auto-detection</li>
            <li>Price trend charts by precise geographic area</li>
            <li>Eircode-based search for newer properties</li>
          </ul>
        </section>
```

- [ ] **Step 8: Add "What This Means for You" section and CTAs**

```tsx
        <section className="about-section">
          <h2>What This Means for You</h2>
          <p><strong>With HomeIQ's Enhanced PPR Data, You Can:</strong></p>
          <ul>
            <li>Search properties within walking distance of a specific location</li>
            <li>Draw custom search areas on an interactive map to define your target neighborhood</li>
            <li>View accurate price trends for specific areas, not just county-wide averages</li>
            <li>Filter by county, property type, date range, and market status</li>
            <li>Trust that map markers show actual property locations, not generic town centroids</li>
            <li>Compare prices across different areas with visual map tools</li>
          </ul>
          
          <div style={{ marginTop: "2rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <Link 
              to="/" 
              style={{
                display: "inline-block",
                padding: "0.75rem 1.5rem",
                backgroundColor: "#1a3c5e",
                color: "white",
                textDecoration: "none",
                borderRadius: "4px",
                fontWeight: "600"
              }}
            >
              Search Property Prices Now
            </Link>
            <Link 
              to="/polygon" 
              style={{
                display: "inline-block",
                padding: "0.75rem 1.5rem",
                backgroundColor: "#4a90e2",
                color: "white",
                textDecoration: "none",
                borderRadius: "4px",
                fontWeight: "600"
              }}
            >
              Try Advanced Map Search
            </Link>
          </div>
        </section>
```

- [ ] **Step 9: Add closing section with link to About page**

```tsx
        <section className="about-section about-closing">
          <p>
            The Property Price Register provides the foundation for transparent property market analysis 
            in Ireland. By enhancing this official data with modern geocoding, validation, and search 
            capabilities, HomeIQ makes it easier to research property prices, understand market trends, 
            and make informed decisions.
          </p>
          <p>
            Want to learn about our other data sources?{" "}
            <Link to="/about" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
              Visit our About page
            </Link>{" "}
            to see how we integrate CSO statistics, BER energy ratings, and geospatial data for 
            comprehensive property intelligence.
          </p>
        </section>
      </main>
    </div>
  );
}
```

- [ ] **Step 10: Verify component compiles**

Run: `cd frontend && npm run build`  
Expected: No TypeScript errors, clean build

- [ ] **Step 11: Commit the page component**

```bash
git add frontend/src/pages/PropertyPriceRegisterPage.tsx
git commit -m "feat: add Property Price Register landing page component"
```

---

## Task 2: Add Route Configuration

**Files:**
- Modify: `frontend/src/main.tsx:34` (after `/about` route)

- [ ] **Step 1: Import PropertyPriceRegisterPage component**

Add to imports section at top of file:

```tsx
import PropertyPriceRegisterPage from "./pages/PropertyPriceRegisterPage";
```

- [ ] **Step 2: Add route after the About route**

After line 33 (`<Route path="/about" element={<AboutPage />} />`), add:

```tsx
        <Route path="/property-price-register" element={<PropertyPriceRegisterPage />} />
```

- [ ] **Step 3: Verify routing works locally**

Run: `cd frontend && npm run dev`  
Navigate to: `http://localhost:5173/property-price-register`  
Expected: Page renders with all sections visible, no console errors

- [ ] **Step 4: Test navigation from other pages**

In browser:
1. Go to home page (`/`)
2. Manually navigate to `/property-price-register`
3. Verify page loads correctly
4. Click "Search Property Prices Now" button → should go to `/`
5. Go back, click "Try Advanced Map Search" → should go to `/polygon`
6. Click "Visit our About page" link → should go to `/about`

Expected: All navigation works, no broken links

- [ ] **Step 5: Commit routing changes**

```bash
git add frontend/src/main.tsx
git commit -m "feat: add route for Property Price Register page"
```

---

## Task 3: Update About Page Link

**Files:**
- Modify: `frontend/src/pages/AboutPage.tsx:50-57`

- [ ] **Step 1: Read current AboutPage PPR source description**

Run: `cat frontend/src/pages/AboutPage.tsx | grep -A 7 "Property Price Register"`  
Expected: Shows the current description without link to new page

- [ ] **Step 2: Update PPR source description with link**

Replace the `<dd>` content (lines 54-57) with:

```tsx
              <dd>
                The primary source for all residential sales in Ireland since 2010. This allows us
                to track every transaction, providing the baseline for our valuation models.{" "}
                <Link to="/property-price-register" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
                  Learn more about the Property Price Register
                </Link>
                .
              </dd>
```

- [ ] **Step 3: Add Link import if not present**

Check imports at top of AboutPage.tsx. If `Link` is not imported from react-router-dom, add it:

```tsx
import { Link } from "react-router-dom";
```

- [ ] **Step 4: Verify link works**

Run: `cd frontend && npm run dev`  
Navigate to: `http://localhost:5173/about`  
Expected: "Learn more about the Property Price Register" link appears under PPR source  
Click link → should navigate to `/property-price-register`

- [ ] **Step 5: Commit About page update**

```bash
git add frontend/src/pages/AboutPage.tsx
git commit -m "feat: add link to Property Price Register page from About"
```

---

## Task 4: SEO Post-Launch Activities

**Files:**
- Modify: `frontend/public/sitemap.xml` (if exists)
- Manual: Google Search Console, IndexNow submission

- [ ] **Step 1: Deploy to production**

Run: `git push origin main`  
Expected: Vercel auto-deploys, new page accessible at `https://homeiq.ie/property-price-register`

- [ ] **Step 2: Verify production deployment**

In browser, visit: `https://homeiq.ie/property-price-register`  
Checks:
- Page loads correctly
- Meta title in browser tab: "Property Price Register Ireland | Complete Guide & Enhanced Data"
- View page source → verify meta description tag present
- All internal links work (/, /polygon, /about)
- All external links work (propertypriceregister.ie, psprauth.ie)

- [ ] **Step 3: Check structured data**

Use Google Rich Results Test: `https://search.google.com/test/rich-results`  
Enter: `https://homeiq.ie/property-price-register`  
Expected: BreadcrumbList schema detected with no errors

- [ ] **Step 4: Update sitemap.xml if exists**

Check if `frontend/public/sitemap.xml` exists:

```bash
ls -la frontend/public/sitemap.xml
```

If exists, add entry:
```xml
<url>
  <loc>https://homeiq.ie/property-price-register</loc>
  <lastmod>2026-06-02</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
```

If sitemap doesn't exist, note it for future generation.

- [ ] **Step 5: Submit to IndexNow**

Run:
```bash
./scripts/submit_indexnow.sh https://homeiq.ie/property-price-register
```

Expected: Success response from IndexNow (Bing, Yandex instant indexing)

- [ ] **Step 6: Submit to Google Search Console (manual)**

Manual steps:
1. Visit `https://search.google.com/search-console`
2. Use "URL Inspection" tool
3. Enter `https://homeiq.ie/property-price-register`
4. Click "Request Indexing"

Expected: Google confirms URL submitted for indexing

- [ ] **Step 7: Document completion**

Create file: `docs/launches/2026-06-02-ppr-landing-page.md`

```markdown
# Property Price Register Landing Page Launch

**Date:** 2026-06-02  
**URL:** https://homeiq.ie/property-price-register

## Deployment
- ✅ Deployed to production
- ✅ All internal links verified
- ✅ All external links verified
- ✅ Structured data validated

## SEO Submissions
- ✅ IndexNow submitted
- ✅ Google Search Console submitted
- ⏳ Sitemap update (pending sitemap generation)

## Monitoring
- [ ] Check Google Search Console in 7 days for indexing status
- [ ] Monitor organic impressions after 30 days
- [ ] Track conversions to search pages

## Target Keywords
- property price register ireland
- PPR ireland
- property price register search
- irish property price data
```

- [ ] **Step 8: Commit post-launch documentation**

```bash
git add docs/launches/2026-06-02-ppr-landing-page.md
git add frontend/public/sitemap.xml  # only if updated
git commit -m "docs: record Property Price Register page launch"
```

---

## Testing Checklist

**Manual Testing (before final deployment):**

- [ ] Page loads without errors at `/property-price-register`
- [ ] Hero section renders with correct H1 and lead paragraph
- [ ] All 6 content sections render with proper H2 headings
- [ ] External links open in new tabs (propertypriceregister.ie, psprauth.ie)
- [ ] Internal links navigate correctly (/, /polygon, /about)
- [ ] CTAs are visible and properly styled
- [ ] Breadcrumb structured data is in page source
- [ ] Meta title and description are correct (view page source)
- [ ] Page is responsive on mobile (test at 375px width)
- [ ] No TypeScript errors in build
- [ ] No console errors in browser

**SEO Validation:**

- [ ] Target keyword "Property Price Register" appears in first 100 words
- [ ] H1 contains primary keyword
- [ ] 5-6 H2 headings present
- [ ] Internal links use descriptive anchor text
- [ ] External links have rel="noopener noreferrer"
- [ ] Total word count: 1,200-1,500 words
- [ ] Structured data validates in Google Rich Results Test

---

## Success Criteria

**Immediate (launch day):**
- ✅ Page accessible at https://homeiq.ie/property-price-register
- ✅ No console errors or broken links
- ✅ Mobile responsive
- ✅ Submitted to search engines

**7 days:**
- [ ] Page indexed by Google (check Search Console)
- [ ] No indexing errors reported

**30 days:**
- [ ] Organic search impressions > 0 for target keywords
- [ ] Click-through rate from search results > 3%
- [ ] At least 5 sessions from organic search

**90 days:**
- [ ] Rank in top 20 for "property price register ireland"
- [ ] 100+ organic sessions per month
- [ ] 20%+ of page visitors click through to search tools

---

## Self-Review

**Spec Coverage Check:**

✅ **Hero Section** → Task 1, Step 3  
✅ **What is the Property Price Register?** → Task 1, Step 4  
✅ **How the PPR Works: A Taxation Record** → Task 1, Step 5  
✅ **Understanding the Limitations** → Task 1, Step 6  
✅ **How HomeIQ Enhances the Data** → Task 1, Step 7  
✅ **What This Means for You** → Task 1, Step 8  
✅ **Call-to-Action buttons** → Task 1, Step 8  
✅ **Link to About page** → Task 1, Step 9  
✅ **Routing configuration** → Task 2  
✅ **Update About page link** → Task 3  
✅ **SEO implementation (metadata, structured data)** → Task 1, Step 2  
✅ **Post-launch SEO activities** → Task 4  

**Placeholder Scan:**  
✅ No "TBD", "TODO", or incomplete sections  
✅ All code blocks contain complete, working code  
✅ All commands have expected output specified  

**Type Consistency:**  
✅ Component name: `PropertyPriceRegisterPage` (consistent throughout)  
✅ Route path: `/property-price-register` (consistent throughout)  
✅ CSS classes: `.static-page`, `.static-content`, `.about-section`, `.about-lead`, `.about-sources` (matches AboutPage)  
✅ Hook usage: `usePageMeta()` (consistent with other pages)  

All requirements from spec are covered. Plan is complete and ready for execution.
