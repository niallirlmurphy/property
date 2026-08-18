import { Link, useNavigate } from "react-router-dom";
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
import { STREETS } from "../streets";

export default function AreaGuidesPage() {
  const navigate = useNavigate();

  // All covered streets grouped by county, for the Street Level Analysis
  // dropdown. Counties sorted alphabetically; streets alphabetically within.
  const streetsByCounty = [...STREETS]
    .sort((a, b) => a.county.localeCompare(b.county) || a.name.localeCompare(b.name))
    .reduce<Record<string, typeof STREETS>>((acc, s) => {
      (acc[s.county] ??= []).push(s);
      return acc;
    }, {});
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
      <PageHeader title="Property Price Area Guides" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }]} />
        <h1>Property Price Area Guides</h1>

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
          <h2>Street Level Analysis</h2>
          <p>
            Dive into individual streets with dedicated price guides for Ireland's
            highest-value and most active streets. Pick a street below, or{" "}
            <Link to="/streets">browse the full list</Link>.
          </p>
          <select
            className="street-select"
            defaultValue=""
            aria-label="Select a street for street-level analysis"
            onChange={e => {
              if (e.target.value) navigate(`/street/${e.target.value}`);
            }}
          >
            <option value="" disabled>
              Select a street…
            </option>
            {Object.entries(streetsByCounty)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([county, streets]) => (
                <optgroup key={county} label={`Co. ${county}`}>
                  {streets.map(s => (
                    <option key={s.slug} value={s.slug}>
                      {s.name}, {s.area}
                    </option>
                  ))}
                </optgroup>
              ))}
          </select>
        </section>

        <Footer />
      </div>
    </>
  );
}
