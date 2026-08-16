import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  PROVINCES,
  countyFromSlug,
  areasForCounty,
  AREAS,
  DUBLIN_EIRCODE_AREAS,
} from "../areas";
import { hasCountyContent } from "../content/counties";

export default function AreaGuidesPage() {
  const meta = usePageMeta(
    "Area Guides — Ireland Property Prices by County, Area & Postcode",
    "Browse HomeIQ's property price area guides: every Irish county, popular towns and suburbs, and all Dublin postcodes. Median prices, trends and recent sales from the Property Price Register.",
    [{ name: "Area Guides", url: "/areaguides" }]
  );

  // Counties that have at least one linkable area guide, for the areas block.
  const countiesWithAreas = PROVINCES
    .flatMap(p => p.counties)
    .filter(slug => areasForCounty(slug).length > 0);

  return (
    <>
      {meta}
      <PageHeader title="Property Price Area Guides" />
      <div className="content-page">
        <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }]} />

        <p className="content-intro">
          Explore Irish residential property prices by location. Every guide draws on
          Ireland's Property Price Register, with median and average prices, yearly trends
          and recent sales. Browse by county, jump to a popular town or suburb, or drill into
          a Dublin postcode.
        </p>

        {PROVINCES.map(province => (
          <section className="content-section" key={province.name}>
            <h2>{province.name}</h2>
            <div className="county-links">
              {province.counties.map(slug => {
                const name = countyFromSlug(slug) ?? slug;
                return (
                  <Link key={slug} to={`/county/${slug}`} className="county-link-btn">
                    County {name}
                    {hasCountyContent(slug) && (
                      <span className="guide-badge">Detailed guide</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </section>
        ))}

        <section className="content-section">
          <h2>Dublin Postcodes</h2>
          <p>Property prices for each Dublin postal district.</p>
          <div className="postcode-link-grid">
            {Object.entries(DUBLIN_EIRCODE_AREAS).map(([code, label]) => (
              <Link key={code} to={`/eircode/${code}`} className="postcode-link">
                <span className="postcode-badge">{code}</span> {label}
              </Link>
            ))}
          </div>
        </section>

        <section className="content-section">
          <h2>Popular Towns &amp; Suburbs</h2>
          {countiesWithAreas.map(slug => {
            const name = countyFromSlug(slug) ?? slug;
            return (
              <div key={slug} className="area-county-group">
                <h3>County {name}</h3>
                <div className="areas-grid">
                  {areasForCounty(slug).map(area => (
                    <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
                      <h3>{area.name}</h3>
                      <p>{area.description}</p>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
          <p className="table-note">
            {AREAS.length} area guides available and growing.
          </p>
        </section>

        <Footer />
      </div>
    </>
  );
}
