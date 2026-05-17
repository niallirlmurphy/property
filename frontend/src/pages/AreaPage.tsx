import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchAreaSummary } from "../api";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import type { AreaSummary } from "../types";
import { areaFromSlug } from "../areas";
import { usePageMeta } from "../hooks/usePageMeta";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

export default function AreaPage() {
  const { slug } = useParams<{ slug: string }>();
  const config = areaFromSlug(slug ?? "");
  const [data, setData] = useState<AreaSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTrends, setShowTrends] = useState(true);

  useEffect(() => {
    if (!config) return;
    setLoading(true);
    fetchAreaSummary(config.slug, config.query, config.radius_km)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);

  if (!config) return (
    <>
      <PageHeader title="Area not found" />
      <div className="content-page"><h1>Area not found</h1></div>
    </>
  );

  usePageMeta(
    config ? `Property Prices in ${config.name}` : undefined,
    config ? `View every residential property sale in ${config.name}, ${config.description}. Historical price trends and recent sales from Ireland's Property Price Register.` : undefined,
  );

  const latestTrend = data?.trends[data.trends.length - 1];

  return (
    <>
      <PageHeader title={`Property Prices in ${config.name}`} />
      <div className="content-page">
      <p className="content-intro">
        {config.name} is {config.description}. This page shows residential property
        sale prices from Ireland's Property Price Register, updated regularly.
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
              <strong>{data.total_count.toLocaleString()}+</strong>
            </div>
            <div className="stat-card">
              <span>Data from</span>
              <strong>{data.min_year} – {data.max_year}</strong>
            </div>
          </div>

          {data.trends.length > 0 && (
            <section className="content-section">
              <h2>Price Trends in {config.name}</h2>
              <p>Median and average sale prices by year within {config.radius_km} km of {config.name}.</p>
              <div style={{ position: "relative", height: 240 }}>
                <TrendsChart data={data.trends} onClose={() => setShowTrends(false)} inline />
              </div>
            </section>
          )}

          {data.recent.length > 0 && (
            <section className="content-section">
              <h2>Recent Sales in {config.name}</h2>
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
            <h2>Search {config.name} Properties</h2>
            <p>
              Use the <Link to={`/?q=${encodeURIComponent(config.query)}&radius_km=${config.radius_km}`}>interactive map</Link> to
              filter by price range, year, and radius.
            </p>
          </section>
        </>
      )}
    </div>
    </>
  );
}
