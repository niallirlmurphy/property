import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";

export default function AboutPage() {
  usePageMeta(
    "About HomeIQ.ie",
    "HomeIQ.ie uses open data from the Property Price Register, CSO, SEAI BER, and other public Irish datasets to make the property market transparent and accessible.",
  );
  return (
    <div className="static-page">
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
    </div>
  );
}
