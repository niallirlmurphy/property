import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchCountySummary } from "../api";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import CountyPageTemplate from "../components/CountyPageTemplate";
import type { CountySummary } from "../types";
import { countyFromSlug } from "../areas";
import { usePageMeta } from "../hooks/usePageMeta";
import { getCountyContent } from "../content/counties";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

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
    setLoading(true);
    fetchCountySummary(county)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);

  if (!county) return (
    <>
      <PageHeader title="County not found" />
      <div className="content-page"><h1>County not found</h1></div>
    </>
  );

  usePageMeta(
    county ? `Property Prices in County ${county}` : undefined,
    county ? `Browse every residential sale in County ${county} since 2010. View price trends, median values, and recent sales from Ireland's Property Price Register.` : undefined,
  );

  const latestTrend = data?.trends[data.trends.length - 1];
  const earliestTrend = data?.trends[0];

  return (
    <>
      <PageHeader title={`Property Prices in County ${county}`} />
      <div className="content-page">
      <p className="content-intro">
        Explore residential property sale prices across County {county} from Ireland's
        Property Price Register. Every sale since 2010 is included.
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

          <section className="content-section">
            <h2>Search County {county} Properties</h2>
            <p>
              Use the <Link to={`/?county=${encodeURIComponent(county)}`}>interactive map</Link> to
              search by address or Eircode within County {county}.
            </p>
          </section>
        </>
      )}
    </div>
    </>
  );
}
