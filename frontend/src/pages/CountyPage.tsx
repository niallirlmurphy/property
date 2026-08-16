import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchCountySummary } from "../api";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import CountyPageTemplate from "../components/CountyPageTemplate";
import type { CountySummary } from "../types";
import { countyFromSlug, areasForCounty, provinceForCounty, PROVINCES } from "../areas";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import { getCountyContent } from "../content/counties";
import {
  getCachedCountyData,
  setCachedCountyData,
} from "../utils/countyDataCache";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

// Optional hero photo per county slug (used on the default dynamic page).
// Counties with a custom template (Cork/Galway/Dublin) manage their own imagery.
const COUNTY_HERO_IMAGES: Record<string, { src: string; alt: string }> = {
  westmeath: {
    src: "/images/westmeath-athlone-bridge.jpg",
    alt: "The town bridge over the River Shannon at Athlone, County Westmeath, with the twin towers of SS Peter and Paul's Church at sunset",
  },
};

export default function CountyPage() {
  const { slug } = useParams<{ slug: string }>();
  const county = countyFromSlug(slug ?? "");

  // Check if we have custom content for this county
  const customContent = getCountyContent(slug ?? "");

  // If custom content exists, use the template
  if (customContent) {
    return <CountyPageTemplate content={customContent} />;
  }

  // Otherwise, fall back to the default dynamic page
  const [data, setData] = useState<CountySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!county) return;

    // Try cache first
    const cached = getCachedCountyData(county);

    if (cached) {
      setData(cached);
      setLoading(false);
    } else {
      setLoading(true);
      fetchCountySummary(county)
        .then((freshData) => {
          setData(freshData);
          setCachedCountyData(county, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [county, slug]);

  if (!county) return (
    <>
      <PageHeader title="County not found" />
      <div className="content-page"><h1>County not found</h1></div>
    </>
  );

  const meta = usePageMeta(
    county ? `Property Prices in County ${county}` : undefined,
    county ? `Browse every residential sale in County ${county} since 2010. View price trends, median values, and recent sales from Ireland's Property Price Register.` : undefined,
    county ? [{ name: "Area Guides", url: "/areaguides" }, { name: `County ${county}`, url: `/county/${slug ?? ""}` }] : undefined,
  );

  const latestTrend = data?.trends[data.trends.length - 1];
  const earliestTrend = data?.trends[0];

  const slugStr = slug ?? "";
  const countyAreas = areasForCounty(slugStr);
  const province = provinceForCounty(slugStr);
  const siblingCountySlugs = province
    ? (PROVINCES.find(p => p.name === province)?.counties ?? []).filter(s => s !== slugStr)
    : [];

  return (
    <>
      {meta}
      <PageHeader title={`Property Prices in County ${county}`} titleAsHeading={false} />
      <div className="content-page">
      <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: `County ${county}`, url: `/county/${slugStr}` }]} />
      <h1>Property Prices in County {county}</h1>
      {COUNTY_HERO_IMAGES[slugStr] && (
        <img
          className="area-hero"
          src={COUNTY_HERO_IMAGES[slugStr].src}
          alt={COUNTY_HERO_IMAGES[slugStr].alt}
          width={2000}
          height={1500}
          loading="lazy"
        />
      )}
      <p className="content-intro">
        Explore residential property sale prices across County {county} from{" "}
        <Link to="/property-price-register" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
          Ireland's Property Price Register
        </Link>. Every sale since 2010 is included.
      </p>

      {loading && <div className="content-loading">Loading data…</div>}
      {error && <div className="error-msg">{error}</div>}

      {data && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span>Median price ({latestTrend?.year ?? "latest"})</span>
              <strong>{formatPrice(latestTrend?.median_price ?? null)}</strong>
            </div>
            <div className="stat-card">
              <span>Average price ({latestTrend?.year ?? "latest"})</span>
              <strong>{formatPrice(latestTrend?.avg_price ?? null)}</strong>
            </div>
            <div className="stat-card">
              <span>Total sales on record</span>
              <strong>{data.total_count.toLocaleString()}</strong>
            </div>
            <div className="stat-card">
              <span>Data from</span>
              <strong>{earliestTrend?.year ?? "—"} – {latestTrend?.year ?? "—"}</strong>
            </div>
          </div>

          {data.trends.length > 0 && (
            <section className="content-section">
              <h2>House Price Trends in County {county}</h2>
              <p>
                Median and average residential sale prices in County {county} by year,
                based on full market price sales only.
              </p>
              <div style={{ position: "relative", height: 240 }}>
                <TrendsChart data={data.trends} onClose={() => {}} inline />
              </div>
            </section>
          )}

          {data.trends.length > 1 && latestTrend && earliestTrend && (
            <section className="content-section">
              <h2>How Have Prices Changed?</h2>
              <p>
                The median sale price in County {county} was{" "}
                <strong>{formatPrice(earliestTrend.median_price)}</strong> in {earliestTrend.year},
                rising to <strong>{formatPrice(latestTrend.median_price)}</strong> in {latestTrend.year}.
              </p>
            </section>
          )}

          {data.recent.length > 0 && (
            <section className="content-section">
              <h2>Recent Sales in County {county}</h2>
              <table className="sales-table">
                <thead>
                  <tr><th>Address</th><th>Date</th><th>Price</th></tr>
                </thead>
                <tbody>
                  {data.recent.map(p => (
                    <tr key={p.id}>
                      <td>{p.address}</td>
                      <td>{p.sale_date.slice(0, 10)}</td>
                      <td>{formatPrice(p.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {countyAreas.length > 0 && (
            <section className="content-section">
              <h2>Areas in County {county}</h2>
              <div className="areas-grid">
                {countyAreas.map(area => (
                  <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
                    <h3>{area.name}</h3>
                    <p>{area.description}</p>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {siblingCountySlugs.length > 0 && (
            <section className="content-section">
              <h2>Nearby Counties in {province}</h2>
              <div className="county-links">
                {siblingCountySlugs.map(sib => (
                  <Link key={sib} to={`/county/${sib}`} className="county-link-btn">
                    County {countyFromSlug(sib) ?? sib}
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="content-section">
            <h2>Search County {county} Properties</h2>
            <p>
              Use the <Link to={`/?q=${encodeURIComponent(county)}&county=${encodeURIComponent(county)}`}>interactive map</Link> to
              search by address or Eircode within County {county}.
            </p>
            <p>
              Browse <Link to="/areaguides">all area guides</Link>.
            </p>
          </section>
        </>
      )}
      <Footer />
    </div>
    </>
  );
}
