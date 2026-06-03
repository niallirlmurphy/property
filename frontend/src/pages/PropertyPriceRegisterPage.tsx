import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";

export default function PropertyPriceRegisterPage() {
  usePageMeta(
    "Property Price Register Ireland | Complete Guide & Enhanced Data",
    "Understand Ireland's Property Price Register, its limitations as a taxation record, and how HomeIQ enhances the data with geocoding validation and address normalization for better property search.",
    undefined,
    "https://homeiq.ie/images/ppr-og-image.jpg"
  );

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
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "What is the Property Price Register Ireland?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The Property Price Register (PPR) is Ireland's official government database of all residential property sales since 2010. Managed by the Property Services Regulatory Authority (PSRA), it records every sale over €100,000 as a legal requirement, providing transparency into the Irish housing market with over 784,000 recorded transactions."
              }
            },
            {
              "@type": "Question",
              "name": "Is the Property Price Register accurate?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The PPR data is comprehensive but has limitations. It originates from stamp duty tax records, so addresses may have inconsistent formatting and lack geographic coordinates. HomeIQ enhances this data through address normalization, geocoding validation, and quality scoring to improve accuracy. We've added coordinates to 78% of properties with 89-91% coverage for recent sales."
              }
            },
            {
              "@type": "Question",
              "name": "How do I search the Property Price Register?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "You can search the official PPR website at propertypriceregister.ie with basic text search, or use HomeIQ.ie for enhanced search capabilities including radius-based search, interactive map tools, polygon drawing, county filtering, and Eircode lookup. HomeIQ provides geocoded property locations and price trend analysis not available on the official site."
              }
            },
            {
              "@type": "Question",
              "name": "Does the Property Price Register include all property sales?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The PPR includes all residential property sales over €100,000 in Ireland since January 2010. It covers houses, apartments, and residential units. However, it includes both full market price sales and non-market transactions like family transfers, which should be filtered out for accurate price analysis."
              }
            },
            {
              "@type": "Question",
              "name": "Why doesn't the Property Price Register have coordinates?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The PPR was designed as a taxation record, not a property search tool, so it only contains text addresses without geographic coordinates. This makes map-based searching impossible on the official site. HomeIQ addresses this by geocoding addresses and validating coordinates against Ireland's boundaries, county borders, and Eircode routing keys."
              }
            },
            {
              "@type": "Question",
              "name": "How far back does the Property Price Register go?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The Property Price Register contains property sales data from January 1, 2010 to the present. It was established under the Finance Act 2010 following the 2008 financial crisis to bring transparency to Ireland's property market. All qualifying sales since then are legally required to be registered."
              }
            }
          ]
        })}
      </script>
      <PageHeader title="Understanding Ireland's Property Price Register" />
      <main className="static-content">
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

        <section className="about-section">
          <h2>What Information Does the PPR Contain?</h2>
          <p>Each registered property sale includes the following details:</p>
          <ul>
            <li><strong>Sale Date:</strong> The date the property transaction was completed</li>
            <li><strong>Sale Price:</strong> The transaction value in euros</li>
            <li><strong>Full Address:</strong> The complete postal address including Eircode (where available)</li>
            <li><strong>Not Full Market Price Flag:</strong> Indicates if the sale was not at open market value (e.g., family transfers, distressed sales)</li>
            <li><strong>VAT Exclusive Flag:</strong> Shows whether VAT is included in the stated price</li>
            <li><strong>Property Description:</strong> New or second-hand dwelling</li>
            <li><strong>Property Size:</strong> Apartment, semi-detached, detached, terraced, etc.</li>
          </ul>
          <p>
            Importantly, the PPR was designed primarily as a <strong>taxation administration tool</strong>,
            not a property search or mapping platform. This distinction is crucial to understanding both
            its strengths and limitations.
          </p>
        </section>

        <section className="about-section">
          <h2>Why the PPR Exists: A Taxation Tool, Not a Property Database</h2>
          <p>
            The Property Price Register was created under the Finance Act 2010 to combat stamp duty
            evasion and tax avoidance following the 2008 financial crisis. Revenue Commissioners required
            transparency into property transactions to ensure accurate tax collection. The system was
            designed with this <strong>compliance and taxation perspective</strong>—not with property
            buyers, researchers, or mapping tools in mind.
          </p>
          <p>This taxation-first design explains many of the register's current limitations:</p>
          <ul>
            <li><strong>Text-only addresses:</strong> No coordinates, no map integration, no spatial search capability</li>
            <li><strong>Minimal validation:</strong> Addresses are accepted as submitted; inconsistent formatting and spelling errors are common</li>
            <li><strong>Basic search interface:</strong> Designed for tax officials verifying specific transactions, not for market research or property comparison</li>
            <li><strong>No property metadata:</strong> No dwelling size (square meters), number of bedrooms, property condition, or other characteristics</li>
          </ul>
          <p>
            For tax collection purposes, this level of detail is sufficient. For property buyers, sellers,
            researchers, and estate agents trying to understand local market dynamics, it presents significant
            challenges.
          </p>
        </section>

        <section className="about-section">
          <h2>Key Limitations of the Raw PPR Data</h2>
          <p>
            While the PPR is an invaluable public resource, users should be aware of several important
            limitations when working with the raw dataset:
          </p>

          <h3>1. No Geographic Coordinates</h3>
          <p>
            Properties are recorded as text addresses only. There is no latitude/longitude data, which
            means the official PPR website cannot offer map-based search, radius queries, or spatial
            analysis. Users searching for "properties within 2km of this location" or "all sales in this
            area" must rely on manual address matching.
          </p>

          <h3>2. Inconsistent Address Formatting</h3>
          <p>
            Because the register was designed for taxation rather than searchability, address data is
            accepted as submitted by solicitors and conveyancers. This leads to:
          </p>
          <ul>
            <li>Inconsistent capitalization ("DUBLIN 2" vs "Dublin 2" vs "dublin 2")</li>
            <li>Abbreviation variations ("St." vs "Street", "Rd" vs "Road")</li>
            <li>Extra whitespace and formatting inconsistencies</li>
            <li>Spelling variations in place names and street names</li>
          </ul>
          <p>
            These inconsistencies make it difficult to aggregate data for a specific street or compare
            properties in the same development.
          </p>

          <h3>3. Limited Eircode Coverage</h3>
          <p>
            While Eircode was introduced in 2015, older property sales (2010-2015) have no Eircode
            associated with them. Even post-2015 sales show variable Eircode recording—approximately
            <strong> 30% of all PPR records</strong> include an Eircode, with coverage improving to
            74-79% for sales from 2022 onward. This partial coverage limits the usefulness of Eircode-based
            search for historical analysis.
          </p>

          <h3>4. No Property Characteristics</h3>
          <p>
            The register records only basic property type (detached, semi-detached, terraced, apartment)
            and whether it is new or second-hand. There is no information about:
          </p>
          <ul>
            <li>Floor area (square meters or square feet)</li>
            <li>Number of bedrooms or bathrooms</li>
            <li>Building Energy Rating (BER)</li>
            <li>Property condition or recent renovations</li>
            <li>Garden or parking availability</li>
          </ul>
          <p>
            This makes price-per-square-meter analysis or comparisons between similar-sized properties
            impossible using PPR data alone.
          </p>

          <h3>5. Non-Market Price Transactions</h3>
          <p>
            While the register flags transactions that are "Not Full Market Price" (such as family
            transfers or distressed sales), these still appear in search results and can skew average
            price calculations if not filtered properly.
          </p>
        </section>

        <section className="about-section">
          <h2>How HomeIQ Transforms PPR Data</h2>
          <p>
            HomeIQ.ie addresses these limitations by <strong>enriching, validating, and structuring</strong>
            the raw Property Price Register data to create a powerful property intelligence platform. Here's how:
          </p>

          <h3>1. Complete Geocoding with Quality Validation</h3>
          <p>
            Every property in the PPR has been processed through our geocoding pipeline using Mapbox's
            professional geocoding API and OpenStreetMap data. This adds latitude and longitude coordinates
            to each property, enabling:
          </p>
          <ul>
            <li><strong>Map-based search:</strong> Visualize properties on an interactive map</li>
            <li><strong>Radius queries:</strong> Find all sales within 1km, 2km, 5km of any location</li>
            <li><strong>Polygon search:</strong> Draw custom boundaries on the map to analyze specific neighborhoods</li>
            <li><strong>Spatial analysis:</strong> Identify price gradients, hot spots, and regional trends</li>
          </ul>
          <p>
            Critically, our geocoding includes <strong>multi-layer validation</strong>:
          </p>
          <ul>
            <li><strong>Ireland boundary check:</strong> Reject coordinates outside Irish territory</li>
            <li><strong>County validation:</strong> Verify coordinates match the stated county</li>
            <li><strong>Precision scoring:</strong> Rate geocoding quality from rooftop-level (100/100) to locality-level (70/100)</li>
            <li><strong>Eircode cross-validation:</strong> For properties with Eircodes, verify coordinates are within 5km of the official routing key centroid</li>
          </ul>
          <p>
            As of May 2026, we have successfully geocoded <strong>78.3% of all PPR properties</strong>
            (614,200 out of 784,464), with success rates exceeding 90% for sales from 2022 onward.
          </p>

          <h3>2. Address Normalization</h3>
          <p>
            Every property address has been normalized to enable accurate searching and aggregation:
          </p>
          <ul>
            <li>Consistent title case formatting</li>
            <li>Standardized abbreviations (St → Street, Rd → Road)</li>
            <li>Whitespace cleanup and trimming</li>
            <li>Removal of redundant prefixes ("No." before apartment numbers)</li>
          </ul>
          <p>
            This allows HomeIQ to group sales from the same street, development, or building—something
            that is difficult or impossible with the raw PPR data.
          </p>

          <h3>3. Eircode Routing Key Intelligence</h3>
          <p>
            We extract and index the first three characters of every Eircode (the "routing key"), which
            represents a geographic area. For the 30% of properties with Eircodes, this enables:
          </p>
          <ul>
            <li><strong>Routing key pages:</strong> Browse all sales in{" "}
              <Link to="/eircode/D02">D02</Link>, <Link to="/eircode/A94">A94</Link>, or any of Ireland's 301 routing key areas
            </li>
            <li><strong>Quick regional search:</strong> Find properties using partial Eircodes</li>
            <li><strong>Cross-validation:</strong> Flag properties where coordinates and Eircode don't align</li>
          </ul>

          <h3>4. Quality Flagging and Centroid Detection</h3>
          <p>
            Our system automatically identifies and flags geocoding quality issues:
          </p>
          <ul>
            <li><strong>Centroid detection:</strong> Properties that fall exactly on town or county centers (100+ addresses at the same coordinate) are flagged for re-geocoding</li>
            <li><strong>Precision tracking:</strong> Users can see geocoding quality scores and filter by precision level</li>
            <li><strong>Continuous improvement:</strong> We regularly re-process low-quality geocodes using updated mapping data</li>
          </ul>

          <h3>5. Market-Focused Data Filters</h3>
          <p>
            HomeIQ automatically applies sensible defaults for property market analysis:
          </p>
          <ul>
            <li>Exclude "Not Full Market Price" transactions from price statistics by default</li>
            <li>County and area-based filtering that works reliably</li>
            <li>Price trend analysis with median and average calculations</li>
          </ul>
        </section>

        <section className="about-section">
          <h2>What This Means for You</h2>
          <p>The PPR and enhanced versions like HomeIQ are valuable resources for:</p>
          <ul>
            <li><strong>Property Buyers:</strong> Research fair market value for target areas before making an offer</li>
            <li><strong>Property Sellers:</strong> Understand recent comparable sales to price your home competitively</li>
            <li><strong>Estate Agents:</strong> Provide clients with data-backed price guidance and market insights</li>
            <li><strong>Property Investors:</strong> Identify emerging markets, price trends, and investment opportunities</li>
            <li><strong>Mortgage Advisors:</strong> Verify property valuations and assess loan-to-value ratios</li>
            <li><strong>Researchers & Journalists:</strong> Analyze Irish housing market trends with comprehensive historical data</li>
            <li><strong>Policy Makers:</strong> Understand regional property market dynamics to inform housing policy</li>
          </ul>
        </section>

        <section className="about-section">
          <h2>Understanding Property Price Trends</h2>
          <p>
            One of the most powerful uses of PPR data is analyzing price trends over time. HomeIQ provides
            interactive price trend charts for every county and area, showing both median and average prices
            by year. This reveals:
          </p>
          <ul>
            <li>Long-term market cycles (the 2010-2013 post-crisis trough, the 2014-2019 recovery, the 2020-2023 pandemic surge)</li>
            <li>Regional variations (Dublin vs rural markets, commuter belt dynamics)</li>
            <li>Local hot spots where prices are rising faster than the national average</li>
          </ul>
          <p>
            You can explore these trends on our{" "}
            <Link to="/county/dublin">county pages</Link> and{" "}
            <Link to="/polygon">map-based search tool</Link>.
          </p>
        </section>

        <section className="about-section">
          <h2>Frequently Asked Questions</h2>

          <h3>What is the Property Price Register Ireland?</h3>
          <p>
            The Property Price Register (PPR) is Ireland's official government database of all residential
            property sales since 2010. Managed by the Property Services Regulatory Authority (PSRA), it
            records every sale over €100,000 as a legal requirement, providing transparency into the Irish
            housing market with over 784,000 recorded transactions.
          </p>

          <h3>Is the Property Price Register accurate?</h3>
          <p>
            The PPR data is comprehensive but has limitations. It originates from stamp duty tax records,
            so addresses may have inconsistent formatting and lack geographic coordinates. HomeIQ enhances
            this data through address normalization, geocoding validation, and quality scoring to improve
            accuracy. We've added coordinates to 78% of properties with 89-91% coverage for recent sales.
          </p>

          <h3>How do I search the Property Price Register?</h3>
          <p>
            You can search the official PPR website at{" "}
            <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer">
              propertypriceregister.ie
            </a>{" "}
            with basic text search, or use HomeIQ.ie for enhanced search capabilities including radius-based
            search, interactive map tools, polygon drawing, county filtering, and Eircode lookup. HomeIQ
            provides geocoded property locations and price trend analysis not available on the official site.
          </p>

          <h3>Does the Property Price Register include all property sales?</h3>
          <p>
            The PPR includes all residential property sales over €100,000 in Ireland since January 2010.
            It covers houses, apartments, and residential units. However, it includes both full market price
            sales and non-market transactions like family transfers, which should be filtered out for accurate
            price analysis.
          </p>

          <h3>Why doesn't the Property Price Register have coordinates?</h3>
          <p>
            The PPR was designed as a taxation record, not a property search tool, so it only contains text
            addresses without geographic coordinates. This makes map-based searching impossible on the official
            site. HomeIQ addresses this by geocoding addresses and validating coordinates against Ireland's
            boundaries, county borders, and Eircode routing keys.
          </p>

          <h3>How far back does the Property Price Register go?</h3>
          <p>
            The Property Price Register contains property sales data from January 1, 2010 to the present.
            It was established under the Finance Act 2010 following the 2008 financial crisis to bring
            transparency to Ireland's property market. All qualifying sales since then are legally required
            to be registered.
          </p>
        </section>

        <section className="about-section about-closing">
          <h2>Start Exploring Irish Property Prices</h2>
          <p>
            The Property Price Register is a remarkable public resource, but its raw form has significant
            limitations for practical property search and market analysis. HomeIQ bridges these gaps by
            adding geocoding, validation, normalization, and spatial search capabilities—all while keeping
            the data free and accessible.
          </p>
          <p>
            Whether you're buying your first home, researching investment opportunities, or simply curious
            about Irish property market trends, HomeIQ gives you the tools to explore over 784,000 residential
            sales with confidence.
          </p>
          <p>
            Want to learn about our other data sources?{" "}
            <Link to="/about" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
              Visit our About page
            </Link>{" "}
            to see how we integrate CSO statistics, BER energy ratings, and geospatial data for
            comprehensive property intelligence.
          </p>
          <p>
            <strong>Ready to start?</strong>
          </p>
          <ul>
            <li><Link to="/">Search by address, Eircode, or coordinates</Link></li>
            <li><Link to="/polygon">Draw a custom area on the map</Link></li>
            <li><Link to="/county/dublin">Browse sales by county</Link></li>
          </ul>
        </section>
      </main>
    </div>
  );
}
