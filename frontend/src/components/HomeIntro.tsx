import { Link } from "react-router-dom";
import { Head } from "vite-react-ssg";
import { AREAS, COUNTIES, DUBLIN_EIRCODE_AREAS, PROVINCES, countyFromSlug } from "../areas";
import { STREETS } from "../streets";
import { publishedPosts } from "../blogPosts";
import { SITE_STATS as S } from "../siteStats";
import Footer from "./Footer";

// Shown in the results pane before the first search. Static data only, so it is
// baked into the prerendered homepage: crawlers get real text and links into the
// county/area/eircode/street pages instead of an empty app shell.

const POPULAR_AREAS = [
  "rathmines", "ranelagh", "clontarf", "howth", "malahide", "blackrock", "dun-laoghaire",
  "sandymount", "swords", "lucan", "tallaght", "bray", "cork-city", "galway-city",
  "limerick-city", "waterford-city", "kilkenny-city", "drogheda", "navan", "naas",
];

const TOOLS = [
  { to: "/valuation", label: "Property valuation" },
  { to: "/heatmap", label: "Price change heatmap" },
  { to: "/polygon", label: "Draw-on-map search" },
  { to: "/property-price-register", label: "Property Price Register guide" },
  { to: "/mortgage", label: "Mortgage calculator" },
];

// Visible on the page and mirrored in the FAQPage structured data below; Google
// requires the two to match, so edit questions here only.
const FAQ: { q: string; a: string }[] = [
  {
    q: "Where does the data come from?",
    a: `Every sale comes from the Property Price Register, the official record of residential property sales in Ireland published by the Property Services Regulatory Authority (PSRA). It holds ${S.totalSales} sales from ${S.firstMonth} to ${S.lastMonth}. HomeIQ adds map locations, price trends and area summaries on top.`,
  },
  {
    q: "How often is it updated?",
    a: "We add new sales from the register every two weeks. A sale only reaches the register once stamp duty is filed with Revenue, usually a few weeks to a few months after the sale closes, so the most recent months always look quieter than they will end up.",
  },
  {
    q: "How accurate are the map locations?",
    a: `The register lists addresses but not coordinates, so we work out each location from the address and Eircode. ${S.mappedPct}% of sales are on the map. Some are placed at street or town level rather than the exact house, and locations we can't verify are left out of map searches and valuations.`,
  },
  {
    q: "What does \u201cnot full market price\u201d mean?",
    a: "The register flags sales where the price paid was not the full market value, for example a transfer between family members. We show these sales but leave them out of median prices and trends so they don't drag the figures down.",
  },
  {
    q: "Can I search by Eircode?",
    a: "Yes. Enter a full Eircode or a routing key such as D06 or H91 in the search box to see sales in that area, with prices, dates and map locations.",
  },
  {
    q: "Is HomeIQ free?",
    a: "Yes. Searching, price trends, area pages and the valuation tool are free, with no sign-up.",
  },
];

// Homepage-only structured data, built from the same figures as the page text
const STRUCTURED_DATA = JSON.stringify([
  {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `Ireland Residential Property Price Register (${S.totalSales} sales)`,
    description: `Residential property sales in Ireland from ${S.firstMonth} to ${S.lastMonth}, from the Property Price Register, with ${S.mappedPct}% of sales mapped across all ${S.counties} counties.`,
    url: "https://homeiq.ie",
    license: "https://creativecommons.org/licenses/by/4.0/",
    isAccessibleForFree: true,
    creator: {
      "@type": "Organization",
      name: "Property Services Regulatory Authority",
      url: "https://www.propertypriceregister.ie",
    },
    temporalCoverage: `${S.first_sale_date}/${S.last_sale_date}`,
    spatialCoverage: { "@type": "Country", name: "Ireland" },
    variableMeasured: ["Sale Price", "Sale Date", "Property Type", "Geographic Coordinates", "Eircode", "County", "Address"],
  },
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  },
]);

export default function HomeIntro() {
  const areas = POPULAR_AREAS
    .map((slug) => AREAS.find((a) => a.slug === slug))
    .filter((a): a is NonNullable<typeof a> => a != null);
  const topValue = STREETS.filter((s) => s.category === "value").sort((a, b) => a.rank - b.rank).slice(0, 5);
  const topVolume = STREETS.filter((s) => s.category === "volume").sort((a, b) => a.rank - b.rank).slice(0, 5);
  const posts = [...publishedPosts()].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);

  return (
    <>
      <Head>
        <script type="application/ld+json">{STRUCTURED_DATA}</script>
      </Head>
      <section className="home-intro">
        <p className="home-trust">
          <strong>{S.totalSales} sales</strong> · {S.firstMonth} – {S.lastMonth} · Source:{" "}
          <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer">Property Price Register</a>
          {" "}· updated every two weeks
          <span className="home-trust-links">
            <a href="#how-it-works">How it works</a>
            <Link to="/about#data-sources">Data sources</Link>
          </span>
        </p>
        <h2>Every Irish home sale since {S.firstYear}, on a map</h2>
        <p>
          HomeIQ maps every residential sale on the Property Price Register — over {S.totalSalesRounded} sales
          across all {COUNTIES.length} counties since {S.firstYear}. Search an address, Eircode or area above
          to see what nearby homes sold for, when they sold, and how prices have moved.
        </p>
        <p>
          Or browse sold prices by county, Dublin postcode, town or street below. Each page shows
          median prices, sales volumes and recent sales from the register.
        </p>

        <h3>Tools</h3>
        <ul className="home-intro-links">
          {TOOLS.map((t) => (
            <li key={t.to}><Link to={t.to}>{t.label}</Link></li>
          ))}
        </ul>

        <h3>House prices by county</h3>
        {PROVINCES.map((p) => (
          <div key={p.name} className="home-intro-group">
            <span className="home-intro-group-name">{p.name}</span>
            <ul className="home-intro-links">
              {p.counties.map((slug) => (
                <li key={slug}><Link to={`/county/${slug}`}>{countyFromSlug(slug)}</Link></li>
              ))}
            </ul>
          </div>
        ))}

        <h3>Dublin property prices by postcode</h3>
        <ul className="home-intro-links">
          {Object.entries(DUBLIN_EIRCODE_AREAS).map(([code, name]) => (
            <li key={code}><Link to={`/eircode/${code}`}>{name}</Link></li>
          ))}
        </ul>

        <h3>Popular areas</h3>
        <ul className="home-intro-links">
          {areas.map((a) => (
            <li key={a.slug}><Link to={`/area/${a.slug}`}>{a.name}</Link></li>
          ))}
          <li><Link to="/areaguides">All {AREAS.length} area guides →</Link></li>
        </ul>

        <h3>Streets</h3>
        <div className="home-intro-group">
          <span className="home-intro-group-name">Highest value</span>
          <ul className="home-intro-links">
            {topValue.map((s) => (
              <li key={s.slug}><Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link></li>
            ))}
          </ul>
        </div>
        <div className="home-intro-group">
          <span className="home-intro-group-name">Most sales</span>
          <ul className="home-intro-links">
            {topVolume.map((s) => (
              <li key={s.slug}><Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link></li>
            ))}
            <li><Link to="/streets">All {STREETS.length} streets →</Link></li>
          </ul>
        </div>

        {posts.length > 0 && (
          <>
            <h3>Latest analysis</h3>
            <ul className="home-intro-posts">
              {posts.map((p) => (
                <li key={p.slug}><Link to={`/blog/${p.slug}`}>{p.title}</Link></li>
              ))}
            </ul>
            <p><Link to="/blog">All articles →</Link></p>
          </>
        )}

        <h3 id="how-it-works">How it works</h3>
        <dl className="home-faq">
          {FAQ.map((f) => (
            <div key={f.q}>
              <dt>{f.q}</dt>
              <dd>{f.a}</dd>
            </div>
          ))}
        </dl>
        <p><Link to="/about#data-sources">More on our data sources and methods →</Link></p>
      </section>
      <Footer />
    </>
  );
}
