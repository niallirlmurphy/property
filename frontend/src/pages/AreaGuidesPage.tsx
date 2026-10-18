import { Link, useLoaderData } from "react-router-dom";
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
import { DEVELOPMENTS } from "../developments";
import type { DevelopmentCard } from "../routeLoaders";

const SECTIONS = [
  { id: "counties", label: "Counties" },
  { id: "towns", label: "Towns & Suburbs" },
  { id: "developments", label: "Developments" },
  { id: "postcodes", label: "Dublin Postcodes" },
  { id: "streets", label: "Streets" },
];

export default function AreaGuidesPage() {
  // Prerendered with headline figures; null in dev, where the plain links stand in.
  const developmentCards = useLoaderData() as DevelopmentCard[] | null;

  // All covered streets grouped by county: Dublin first (most streets), then
  // alphabetically; streets alphabetically within.
  const streetsByCounty = Object.entries(
    [...STREETS]
      .sort((a, b) => a.name.localeCompare(b.name))
      .reduce<Record<string, typeof STREETS>>((acc, s) => {
        (acc[s.county] ??= []).push(s);
        return acc;
      }, {})
  ).sort(([a], [b]) => Number(b === "Dublin") - Number(a === "Dublin") || a.localeCompare(b));
  const meta = usePageMeta(
    "Area Guides — Ireland Property Prices by County, Area & Postcode",
    "Browse HomeIQ's property price area guides: every Irish county, popular towns and suburbs, developments, Dublin postcodes and streets. Median prices, trends and recent sales from the Property Price Register.",
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
          and recent sales. Browse by county, jump to a town, suburb or development, or
          drill into a Dublin postcode or street.
        </p>

        <nav className="guide-jump" aria-label="Area guide sections">
          {SECTIONS.map(s => <a key={s.id} href={`#${s.id}`}>{s.label}</a>)}
        </nav>

        <section className="content-section guide-section" id="counties">
          <h2>Counties</h2>
          {PROVINCES.map(province => (
            <div key={province.name} className="area-county-group">
              <h3>{province.name}</h3>
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
            </div>
          ))}
        </section>

        <section className="content-section guide-section" id="towns">
          <h2>Towns &amp; Suburbs</h2>
          <p>{AREAS.length} area guides, grouped by county.</p>
          {countiesWithAreas.map(slug => {
            const name = countyFromSlug(slug) ?? slug;
            const areas = areasForCounty(slug);
            return (
              <details key={slug} className="guide-group" open={slug === "dublin"}>
                <summary>County {name} <span className="guide-count">{areas.length}</span></summary>
                <div className="areas-grid">
                  {areas.map(area => (
                    <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
                      <h3>{area.name}</h3>
                      <p>{area.description}</p>
                    </Link>
                  ))}
                </div>
              </details>
            );
          })}
        </section>

        <section className="content-section guide-section" id="developments">
          <h2>Developments</h2>
          <p>
            Price guides for named apartment and housing schemes, with bedroom breakdowns,
            schools and transport links. <Link to="/developments">All developments</Link>.
          </p>
          <div className="areas-grid">
            {developmentCards
              ? developmentCards.map(d => (
                  <Link key={d.slug} to={`/development/${d.slug}`} className="area-card">
                    <h3>{d.name}</h3>
                    <p>{d.area}</p>
                    <p className="guide-card-stat">
                      Median €{d.median.toLocaleString("en-IE")} · {d.count.toLocaleString("en-IE")} sales
                    </p>
                  </Link>
                ))
              : DEVELOPMENTS.map(d => (
                  <Link key={d.slug} to={`/development/${d.slug}`} className="area-card">
                    <h3>{d.name}</h3>
                    <p>{d.area}</p>
                  </Link>
                ))}
          </div>
        </section>

        <section className="content-section guide-section" id="postcodes">
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

        <section className="content-section guide-section" id="streets">
          <h2>Street Level Analysis</h2>
          <p>
            Dedicated price guides for {STREETS.length} of Ireland's highest-value and most
            active streets, grouped by county. See also the{" "}
            <Link to="/streets">ranked street list</Link>.
          </p>
          {streetsByCounty.map(([county, streets]) => (
            <details key={county} className="guide-group">
              <summary>Co. {county} <span className="guide-count">{streets.length}</span></summary>
              <ul className="guide-street-list">
                {streets.map(s => (
                  <li key={s.slug}>
                    <Link to={`/street/${s.slug}`}>{s.name}</Link>
                    <span className="street-index-county">, {s.area}</span>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </section>

        <Footer />
      </div>
    </>
  );
}
