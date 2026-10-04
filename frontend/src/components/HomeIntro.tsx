import { Link } from "react-router-dom";
import { AREAS, COUNTIES, DUBLIN_EIRCODE_AREAS, PROVINCES, countyFromSlug } from "../areas";
import { STREETS } from "../streets";
import { publishedPosts } from "../blogPosts";

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

export default function HomeIntro() {
  const areas = POPULAR_AREAS
    .map((slug) => AREAS.find((a) => a.slug === slug))
    .filter((a): a is NonNullable<typeof a> => a != null);
  const topValue = STREETS.filter((s) => s.category === "value").sort((a, b) => a.rank - b.rank).slice(0, 5);
  const topVolume = STREETS.filter((s) => s.category === "volume").sort((a, b) => a.rank - b.rank).slice(0, 5);
  const posts = [...publishedPosts()].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);

  return (
    <section className="home-intro">
      <h2>Every Irish home sale since 2010, on a map</h2>
      <p>
        HomeIQ maps every residential sale on the Property Price Register — over 800,000 sales
        across all {COUNTIES.length} counties since 2010. Search an address, Eircode or area above
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
    </section>
  );
}
