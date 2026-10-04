import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import { usePageMeta } from "../hooks/usePageMeta";
import { BLOG_POSTS, isPublished } from "../blogPosts";
import { SITE_STATS as S } from "../siteStats";

declare const __BUILD_DATE__: string;

// Gated on the build date, not the visitor's clock, so the prerendered HTML and
// the hydrated page agree; the link appears on the first deploy after it's live.
const methodologyPost = BLOG_POSTS.find((p) => p.slug === "how-homeiq-values-a-home");
const showMethodology = methodologyPost != null && isPublished(methodologyPost, new Date(__BUILD_DATE__));

export default function AboutPage() {
  const meta = usePageMeta(
    "About HomeIQ.ie",
    "HomeIQ.ie uses open data from the Property Price Register, CSO, SEAI BER, and other public Irish datasets to make the property market transparent and accessible.",
  );
  return (
    <div className="static-page">
      {meta}
      <PageHeader title="About HomeIQ.ie" />
      <main className="static-content">
        <section className="about-section">
          <p className="about-lead">
            At HomeIQ.ie, we believe that transparency is the foundation of a fair and efficient
            property market. The evolution of Open Data—the practice of making government-held
            information freely available to the public—has transformed how we understand real estate.
            By removing financial and technical barriers to information, open data empowers homeowners,
            buyers, and investors to move beyond guesswork and make decisions rooted in objective facts.
          </p>
          <p>
            HomeIQ.ie harnesses these vast public resources to provide a clear, data-driven window
            into the Irish housing market. We synthesize complex datasets to help you understand not
            just what a property is worth today, but how regional trends, historical cycles, and local
            developments influence future value.
          </p>
        </section>

        <section className="about-section" id="data-sources">
          <h2>Data Sources &amp; Methodology</h2>
          <h3>Where the sales come from</h3>
          <p>
            Every sale on HomeIQ comes from the{" "}
            <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer">Property Price Register</a>,
            published by the Property Services Regulatory Authority (PSRA). It records the date, address,
            county and price of every residential property sale in Ireland since January 2010, and the
            Eircode for many recent sales. HomeIQ currently holds {S.totalSales} sales from {S.firstMonth} to {S.lastMonth}.
          </p>
          <h3>How often it's updated</h3>
          <p>
            We add new sales from the register every two weeks. A sale only appears on the register once
            stamp duty is filed with Revenue, usually a few weeks to a few months after the sale closes, so
            the latest months always undercount and fill in over later updates.
          </p>
          <h3>How locations are found</h3>
          <p>
            The register lists addresses but not map coordinates. We work out each location from the
            Eircode where there is one, and from the address otherwise, then check the result: it must fall
            inside Ireland, inside the right county, and near its Eircode area. {S.mappedPct}% of sales are
            on the map. Some are placed at street or town level rather than the exact house, and locations
            that fail our checks are left out of map searches and valuations until they're fixed.
          </p>
          <h3>How prices and trends are calculated</h3>
          <p>
            Area and street figures use median prices, which are less affected by a few very expensive
            sales than averages. We leave out sales the register marks as not full market price (such as
            transfers within a family), extreme price outliers, and bulk sales of several homes for one
            combined price, as these would distort the figures. The register doesn't record bedrooms or
            property type; where we show them, they come from public listing information for that sale.
          </p>
          {showMethodology && methodologyPost && (
            <p>
              For a closer look at how estimates are built, read{" "}
              <Link to={`/blog/${methodologyPost.slug}`} style={{ color: "#1a3c5e", textDecoration: "underline" }}>
                {methodologyPost.title}
              </Link>.
            </p>
          )}
        </section>

        <section className="about-section">
          <h2>How We Use Data.gov.ie for Market Insights</h2>
          <p>
            Through the integration of Ireland's national open data portal,{" "}
            <a href="https://data.gov.ie" target="_blank" rel="noopener noreferrer">data.gov.ie</a>,
            HomeIQ.ie provides deep-dive analytics into property valuations and national trends. By leveraging
            machine learning and historical analysis, we transform raw spreadsheets into insights on
            market volatility, regional "inflation gaps," and the specific features—from energy
            efficiency to urban proximity—that drive property premiums in the Irish landscape.
          </p>
        </section>

        <section className="about-section">
          <h2>Our Core Data Sources</h2>
          <p>
            To ensure the highest level of accuracy and transparency, HomeIQ.ie utilises a suite of
            essential public datasets, including:
          </p>
          <dl className="about-sources">
            <div className="about-source">
              <dt>
                <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer">
                  The Property Price Register
                </a>
              </dt>
              <dd>
                The primary source for all residential sales in Ireland since 2010. This allows us
                to track every transaction, providing the baseline for our valuation models.{" "}
                <Link to="/property-price-register" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
                  Learn more about the Property Price Register
                </Link>
                .
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://www.cso.ie/en/statistics/prices/residentialpropertyprice/" target="_blank" rel="noopener noreferrer">
                  CSO Residential Property Price Index (RPPI)
                </a>
              </dt>
              <dd>
                We use official Central Statistics Office data to measure monthly market momentum
                and track inflation across different property types and regions.
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://ndber.seai.ie/BERResearchTool/Register/RegisterSearch.aspx" target="_blank" rel="noopener noreferrer">
                  National BER Public Search
                </a>
              </dt>
              <dd>
                By analysing Building Energy Rating data from the SEAI, we provide insights into how energy
                efficiency correlates with modern property valuations.
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://data.gov.ie/dataset?theme=Geospatial" target="_blank" rel="noopener noreferrer">
                  Geospatial &amp; Planning Data
                </a>
              </dt>
              <dd>
                Integration of local authority planning records helps our users identify future
                supply shifts and infrastructure developments that impact neighbourhood desirability.
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://www.cso.ie/en/census/census2022/" target="_blank" rel="noopener noreferrer">
                  Census Housing Statistics
                </a>
              </dt>
              <dd>
                Demographic data from Census 2022 allows us to contextualise property trends within
                the broader framework of Irish population growth and housing stock age.
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://data.gov.ie/organization/ordnance-survey-ireland" target="_blank" rel="noopener noreferrer">
                  GeoHive &amp; OSI Geospatial Data
                </a>
              </dt>
              <dd>
                We use Ordnance Survey Ireland's open geospatial datasets, including Eircode boundaries,
                small area statistics, and building footprints, to provide accurate location-based search
                and mapping. This enables precise geocoding of Irish addresses and Eircode routing keys.
              </dd>
            </div>
            <div className="about-source">
              <dt>
                <a href="https://www.openstreetmap.org/about" target="_blank" rel="noopener noreferrer">
                  OpenStreetMap
                </a>
              </dt>
              <dd>
                For addresses not found in official datasets, we fall back to OpenStreetMap's
                community-maintained geospatial database via the Nominatim geocoding service,
                ensuring comprehensive coverage of Irish locations.
              </dd>
            </div>
          </dl>
        </section>

        <section className="about-section about-closing">
          <p>
            HomeIQ.ie is dedicated to turning public data into your personal property advantage.
            Whether you are tracking the "Commuter Belt" rebound or researching rural market
            stability, we provide the intelligence you need to navigate the Irish property market
            with confidence.
          </p>
          <p>
            Have a suggestion or question?{" "}
            <span style={{ color: "#1a3c5e", cursor: "default" }}>
              Use the Feedback or Contact buttons on the right side of this page.
            </span>
          </p>
        </section>
      </main>
      <Footer />
    </div>
  );
}
