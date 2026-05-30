import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchEircode, fetchTrends } from "../api";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import type { EircodeResponse, TrendPoint } from "../types";
import { DUBLIN_EIRCODE_AREAS } from "../areas";
import { usePageMeta } from "../hooks/usePageMeta";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

export default function EircodePage() {
  const { code } = useParams<{ code: string }>();
  const upperCode = code?.toUpperCase() ?? "";
  const friendlyName = DUBLIN_EIRCODE_AREAS[upperCode] ?? upperCode;

  // SEO meta tags
  usePageMeta(
    `${friendlyName} Property Prices (${upperCode})`,
    `View all residential property sales in ${friendlyName} (${upperCode} Eircode area). Browse recent transactions, median prices, and price trends from Ireland's Property Price Register.`
  );

  const [data, setData] = useState<EircodeResponse | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!upperCode) return;
    setLoading(true);
    Promise.all([
      fetchEircode(upperCode, { limit: 10 }),
      fetchTrends(undefined, 5, data?.results[0]?.county ?? undefined),
    ])
      .then(([eircodeData, trendData]) => {
        setData(eircodeData);
        // Fetch county trends once we have the county
        const county = eircodeData.results[0]?.county;
        if (county) return fetchTrends(undefined, 5, county).then(setTrends);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [upperCode]);

  return (
    <>
      <PageHeader title={`Property Prices — ${friendlyName}`} />
      <div className="content-page">
      <p className="content-intro">
        All residential property sales recorded under Eircode routing key <strong>{upperCode}</strong> in
        Ireland's Property Price Register, from 2010 to present.
      </p>

      {loading && <div className="content-loading">Loading data…</div>}
      {error && <div className="error-msg">{error}</div>}

      {data && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span>Median price</span>
              <strong>{formatPrice(data.stats.median_price)}</strong>
            </div>
            <div className="stat-card">
              <span>Average price</span>
              <strong>{formatPrice(data.stats.avg_price)}</strong>
            </div>
            <div className="stat-card">
              <span>Total sales</span>
              <strong>{data.stats.total_count.toLocaleString()}</strong>
            </div>
            <div className="stat-card">
              <span>Period</span>
              <strong>
                {data.stats.earliest_sale?.slice(0, 4)} – {data.stats.latest_sale?.slice(0, 4)}
              </strong>
            </div>
          </div>

          {trends.length > 0 && (
            <section className="content-section">
              <h2>Price Trends — {data.results[0]?.county ?? upperCode}</h2>
              <p>County-level median and average sale prices by year.</p>
              <div style={{ position: "relative", height: 240 }}>
                <TrendsChart data={trends} onClose={() => {}} inline />
              </div>
            </section>
          )}

          {data.results.length > 0 && (
            <section className="content-section">
              <h2>Recent Sales — {upperCode}</h2>
              <table className="sales-table">
                <thead>
                  <tr><th>Address</th><th>Date</th><th>Price</th></tr>
                </thead>
                <tbody>
                  {data.results.map(p => (
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
            <h2>Search by Eircode</h2>
            <p>
              Use the <Link to="/">interactive map</Link> to search by full Eircode,
              filter by price range, and view properties on a map.
            </p>
          </section>
        </>
      )}
    </div>
    </>
  );
}
