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
  DUBLIN_POSTCODE_NEIGHBOURHOODS,
} from "../areas";
import { hasCountyContent } from "../content/counties";
import { STREETS } from "../streets";
import { DEVELOPMENTS } from "../developments";
import type { AreaGuidesData, GuideFigure } from "../routeLoaders";

const SECTIONS = [
  { id: "counties", label: "Counties" },
  { id: "towns", label: "Towns & Suburbs" },
  { id: "developments", label: "Developments" },
  { id: "postcodes", label: "Dublin Postcodes" },
  { id: "streets", label: "Streets" },
];

// Counties with at least this many town guides get their own group; the rest
// share one "Rest of Ireland" grid.
const MIN_GROUP_TOWNS = 3;

// D6W sorts after D06, and Dublin's D keys before the county's A/K keys.
const postcodeOrder = (key: string) => (key.startsWith("D") ? "0" : "1") + key.replace("D6W", "D06W");

function shortPrice(n: number) {
  const k = Math.round(n / 1000);
  return k >= 1000 ? `€${(k / 1000).toFixed(2).replace(/\.?0+$/, "")}m` : `€${k}k`;
}

function Change({ pct }: { pct?: number }) {
  if (pct == null) return null;
  const cls = pct > 0 ? "guide-up" : pct < 0 ? "guide-down" : "";
  return <span className={`guide-change ${cls}`}>{pct > 0 ? "+" : ""}{pct.toFixed(1)}%</span>;
}

function TownCard({ slug, name, county, fig, year }: {
  slug: string; name: string; county?: string; fig?: GuideFigure; year?: number;
}) {
  return (
    <Link to={`/area/${slug}`} className="guide-town">
      <strong>{name}</strong>
      {county && <span className="guide-town-county">Co. {county}</span>}
      {fig && year
        ? <span className="guide-town-stat">{shortPrice(fig.median)} median · {fig.count.toLocaleString("en-IE")} sales in {year}</span>
        : <span className="guide-town-stat guide-muted">Prices, trends &amp; recent sales</span>}
    </Link>
  );
}

export default function AreaGuidesPage() {
  // Prerendered with figures; null in dev, where the links render without them.
  const data = useLoaderData() as AreaGuidesData | null;

  const meta = usePageMeta(
    "Area Guides — Ireland Property Prices by County, Area & Postcode",
    "Browse HomeIQ's property price area guides: every Irish county, popular towns and suburbs, developments, Dublin postcodes and streets. Median prices, trends and recent sales from the Property Price Register.",
    [{ name: "Area Guides", url: "/areaguides" }]
  );

  const countiesWithAreas = PROVINCES
    .flatMap(p => p.counties)
    .filter(slug => areasForCounty(slug).length > 0);
  const groupedCounties = countiesWithAreas.filter(slug => areasForCounty(slug).length >= MIN_GROUP_TOWNS);
  const otherTowns = countiesWithAreas
    .filter(slug => areasForCounty(slug).length < MIN_GROUP_TOWNS)
    .flatMap(slug => areasForCounty(slug).map(area => ({ area, county: countyFromSlug(slug) ?? slug })))
    .sort((a, b) => a.area.name.localeCompare(b.area.name));

  // Dublin streets by routing key (D04, A94…), in postcode order; other counties' streets by county.
  const byName = [...STREETS].sort((a, b) => a.name.localeCompare(b.name));
  const dublinGroups = Object.entries(
    byName.filter(s => s.countySlug === "dublin").reduce<Record<string, typeof STREETS>>((acc, s) => {
      (acc[data?.streetKeys[s.slug] ?? "Other"] ??= []).push(s);
      return acc;
    }, {})
  ).sort(([a], [b]) => Number(a === "Other") - Number(b === "Other")
    || postcodeOrder(a).localeCompare(postcodeOrder(b)));
  const countyGroups = Object.entries(
    byName.filter(s => s.countySlug !== "dublin").reduce<Record<string, typeof STREETS>>((acc, s) => {
      (acc[s.county] ??= []).push(s);
      return acc;
    }, {})
  ).sort(([a], [b]) => a.localeCompare(b));

  const streetList = (streets: typeof STREETS, showArea: boolean) => (
    <ul className="guide-street-list">
      {streets.map(s => (
        <li key={s.slug}>
          <Link to={`/street/${s.slug}`}>{s.name}</Link>
          {showArea && <span className="street-index-county">, {s.area}</span>}
        </li>
      ))}
    </ul>
  );

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

        <form action="/" method="get" className="guide-search" role="search">
          <label htmlFor="guide-search-q">Can't see your area? Search any address, town or Eircode:</label>
          <div className="guide-search-row">
            <input id="guide-search-q" name="q" type="search" placeholder="e.g. Ranelagh, or D04" required />
            <button type="submit">Search</button>
          </div>
        </form>

        <nav className="guide-jump" aria-label="Area guide sections">
          {SECTIONS.map(s => <a key={s.id} href={`#${s.id}`}>{s.label}</a>)}
        </nav>

        <section className="content-section guide-section" id="counties">
          <h2>Counties</h2>
          {data && (
            <p>Median sale price in {data.year} and the change on {data.year - 1}.</p>
          )}
          {PROVINCES.map(province => (
            <div key={province.name} className="area-county-group">
              <h3>{province.name}</h3>
              <div className="guide-county-grid">
                {province.counties.map(slug => {
                  const fig = data?.counties[slug];
                  return (
                    <Link key={slug} to={`/county/${slug}`} className="guide-county">
                      <strong>{countyFromSlug(slug) ?? slug}</strong>
                      {fig && <span>{shortPrice(fig.median)} <Change pct={fig.change} /></span>}
                      {hasCountyContent(slug) && <span className="guide-badge">Detailed guide</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </section>

        <section className="content-section guide-section" id="towns">
          <h2>Towns &amp; Suburbs</h2>
          <p>{AREAS.length} area guides. Medians are shown where a town had at least 50 sales in the year.</p>
          {groupedCounties.map(slug => {
            const areas = areasForCounty(slug);
            return (
              <details key={slug} className="guide-group" open={slug === "dublin"}>
                <summary>County {countyFromSlug(slug) ?? slug} <span className="guide-count">{areas.length}</span></summary>
                <div className="guide-town-grid">
                  {areas.map(area => (
                    <TownCard key={area.slug} slug={area.slug} name={area.name} fig={data?.areas[area.slug]} year={data?.year} />
                  ))}
                </div>
              </details>
            );
          })}
          <details className="guide-group">
            <summary>Rest of Ireland <span className="guide-count">{otherTowns.length}</span></summary>
            <div className="guide-town-grid">
              {otherTowns.map(({ area, county }) => (
                <TownCard key={area.slug} slug={area.slug} name={area.name} county={county} fig={data?.areas[area.slug]} year={data?.year} />
              ))}
            </div>
          </details>
        </section>

        <section className="content-section guide-section" id="developments">
          <h2>Developments</h2>
          <p>
            Price guides for named apartment and housing schemes, with schools and transport
            links. <Link to="/developments">All developments</Link>.
          </p>
          <div className="guide-town-grid">
            {(data?.developments ?? DEVELOPMENTS).map(d => (
              <Link key={d.slug} to={`/development/${d.slug}`} className="guide-town">
                <strong>{d.name}</strong>
                <span className="guide-town-county">{d.area}</span>
                {"median" in d && (
                  <span className="guide-town-stat">{shortPrice(d.median)} median · {d.count.toLocaleString("en-IE")} sales</span>
                )}
              </Link>
            ))}
          </div>
        </section>

        <section className="content-section guide-section" id="postcodes">
          <h2>Dublin Postcodes</h2>
          <p>Property prices for each Dublin postal district.</p>
          <div className="guide-town-grid">
            {Object.entries(DUBLIN_EIRCODE_AREAS).map(([code, label]) => (
              <Link key={code} to={`/eircode/${code}`} className="guide-postcode">
                <span className="postcode-badge">{code}</span>
                <span>
                  <strong>{label}</strong>
                  <span className="guide-town-county">{DUBLIN_POSTCODE_NEIGHBOURHOODS[code]}</span>
                </span>
              </Link>
            ))}
          </div>
        </section>

        <section className="content-section guide-section" id="streets">
          <h2>Street Level Analysis</h2>
          <p>
            Dedicated price guides for {STREETS.length} of Ireland's highest-value and most
            active streets. See also the <Link to="/streets">ranked street list</Link>.
          </p>
          <h3 className="guide-subhead">Dublin, by postcode</h3>
          {dublinGroups.map(([key, streets]) => (
            <details key={key} className="guide-group">
              <summary>
                {key === "Other" ? "Other Dublin streets" : <>{key} <span className="guide-muted">{DUBLIN_POSTCODE_NEIGHBOURHOODS[key]}</span></>}
                <span className="guide-count">{streets.length}</span>
              </summary>
              {streetList(streets, true)}
            </details>
          ))}
          <h3 className="guide-subhead">Rest of Ireland</h3>
          {countyGroups.map(([county, streets]) => (
            <details key={county} className="guide-group">
              <summary>Co. {county} <span className="guide-count">{streets.length}</span></summary>
              {streetList(streets, true)}
            </details>
          ))}
        </section>

        <Footer />
      </div>
    </>
  );
}
