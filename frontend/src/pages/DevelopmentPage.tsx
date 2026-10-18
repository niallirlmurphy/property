import { useLoaderData, Link } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import MapSearchThumb from "../components/MapSearchThumb";
import { usePageMeta } from "../hooks/usePageMeta";
import type { DevelopmentPageData } from "../routeLoaders";
import type { DevelopmentTransaction } from "../types";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

function formatDistance(m: number) {
  const dist = m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`;
  // ~80 m a minute on foot; past 2 km a walking time isn't useful
  return m <= 2000 ? `${dist} (~${Math.max(1, Math.round(m / 80))} min walk)` : dist;
}

function SalesTable({ rows }: { rows: DevelopmentTransaction[] }) {
  return (
    <table className="sales-table">
      <thead><tr><th>Address</th><th>Date</th><th>Beds</th><th>Type</th><th>Price</th></tr></thead>
      <tbody>
        {rows.map((t, i) => (
          <tr key={i}>
            <td>{t.address}</td>
            <td>{t.date}</td>
            <td>{t.bedrooms ?? "—"}</td>
            <td>{t.propertyType ?? "—"}{t.newHome ? " (new)" : ""}</td>
            <td>{formatPrice(t.price)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function DevelopmentPage() {
  const loaded = useLoaderData() as DevelopmentPageData | null;
  const config = loaded?.development;
  const data = loaded?.data;

  const crumbs = config
    ? [
        { name: `County ${config.county}`, url: `/county/${config.countySlug}` },
        { name: "Developments", url: "/developments" },
        { name: config.name, url: `/development/${config.slug}` },
      ]
    : [];

  const title = config ? `${config.name}, ${config.area}: Property Prices` : undefined;
  const meta = usePageMeta(
    title,
    config?.description,
    crumbs,
  );

  if (!config || !data) {
    return (
      <>
        <PageHeader title="Development not found" />
        <div className="content-page"><h1>Development not found</h1></div>
      </>
    );
  }

  const { stats, development, amenities } = data;
  const nearestStop = amenities.transport[0];
  const faqs = [
    {
      q: `What is the average price in ${config.name}?`,
      a: `The average sale price recorded in ${config.name}, ${config.area} is ${formatPrice(stats.avg)}, and the median is ${formatPrice(stats.median)}, based on ${stats.count} sales on the Property Price Register${stats.firstYear ? ` since ${stats.firstYear}` : ""}.`,
    },
    ...(stats.recentMedian != null
      ? [{
          q: `What have homes in ${config.name} sold for recently?`,
          a: `Over the last two years the median sale price in ${config.name} was ${formatPrice(stats.recentMedian)}, across ${stats.recentCount} sales.`,
        }]
      : []),
    {
      q: `How many homes in ${config.name} have sold?`,
      a: `${stats.count} individual sales in ${config.name} are on the Property Price Register: ${development.newHomeSales} new homes and ${development.resales} resales.${data.bulkSales.length ? ` ${data.bulkSales.length === 1 ? "One bulk sale is" : `${data.bulkSales.length} bulk sales are`} listed separately.` : ""}`,
    },
    ...(nearestStop
      ? [{
          q: `What is the nearest public transport to ${config.name}?`,
          a: `The nearest station is ${nearestStop.name} (${nearestStop.mode}), about ${formatDistance(nearestStop.distance_m)} from ${config.name}.`,
        }]
      : []),
  ];
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map(f => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  return (
    <>
      {meta}
      <PageHeader title={title!} titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>{config.name}, {config.area}: Property Prices</h1>
        <p className="content-intro">{config.description}</p>

        <div className="stats-grid">
          <div className="stat-card"><span>Median price</span><strong>{formatPrice(stats.median)}</strong></div>
          <div className="stat-card"><span>Average price</span><strong>{formatPrice(stats.avg)}</strong></div>
          <div className="stat-card">
            <span>Median, last 2 years</span>
            <strong>{stats.recentMedian != null ? formatPrice(stats.recentMedian) : "Too few sales"}</strong>
          </div>
          <div className="stat-card"><span>Sales on record</span><strong>{stats.count.toLocaleString()}</strong></div>
        </div>

        <section className="content-section">
          <h2>About {config.name}</h2>
          <p>{config.info}</p>
          <ul>
            {development.firstSaleYear && <li>First sale on the register: {development.firstSaleYear}</li>}
            <li>New-home sales: {development.newHomeSales.toLocaleString()}</li>
            <li>Resales: {development.resales.toLocaleString()}</li>
            <li>Price range: {formatPrice(stats.min)} – {formatPrice(stats.max)}</li>
          </ul>
          {data.bulkSales.length > 0 && (
            <>
              <h3>Bulk sales</h3>
              <p>
                Sales of many units at one price, left out of the statistics on this page
                because their price covers more than one home.
              </p>
              <SalesTable rows={data.bulkSales} />
            </>
          )}
        </section>

        {data.trends.length > 0 && (
          <section className="content-section">
            <h2>Price Trends in {config.name}</h2>
            <p>Median and average sale prices by year, {stats.firstYear}–{stats.lastYear}.</p>
            <div style={{ position: "relative", height: 240 }}>
              <TrendsChart data={data.trends} onClose={() => {}} inline />
            </div>
          </section>
        )}

        {(data.bedrooms.length > 0 || data.types.length > 0) && (
          <section className="content-section">
            <h2>Prices by Home Size and Type</h2>
            {data.bedrooms.length > 0 && (
              <>
                <table className="sales-table">
                  <thead><tr><th>Bedrooms</th><th>Sales</th><th>Median</th><th>Average</th></tr></thead>
                  <tbody>
                    {data.bedrooms.map(b => (
                      <tr key={b.bedrooms}>
                        <td>{b.bedrooms === 0 ? "Studio" : `${b.bedrooms}-bed`}</td>
                        <td>{b.count}</td>
                        <td>{formatPrice(b.median)}</td>
                        <td>{formatPrice(b.avg)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="content-note">
                  The register doesn't record bedrooms; these figures cover the{" "}
                  {development.bedroomsKnown} of {stats.count} sales whose bedroom count we know,
                  mostly recent ones. Sizes with fewer than 5 sales are not shown.
                </p>
              </>
            )}
            {data.types.length > 0 && (
              <table className="sales-table">
                <thead><tr><th>Type</th><th>Sales</th><th>Median</th><th>Average</th></tr></thead>
                <tbody>
                  {data.types.map(t => (
                    <tr key={t.type}>
                      <td>{t.type}</td>
                      <td>{t.count}</td>
                      <td>{formatPrice(t.median)}</td>
                      <td>{formatPrice(t.avg)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {amenities.transport.length > 0 && (
          <section className="content-section">
            <h2>Transport Links</h2>
            <table className="sales-table">
              <thead><tr><th>Station / stop</th><th>Service</th><th>Distance</th></tr></thead>
              <tbody>
                {amenities.transport.map(t => (
                  <tr key={t.name}><td>{t.name}</td><td>{t.mode}</td><td>{formatDistance(t.distance_m)}</td></tr>
                ))}
              </tbody>
            </table>
            <p className="content-note">Straight-line distances from the centre of the development.</p>
          </section>
        )}

        {amenities.schools.length > 0 && (
          <section className="content-section">
            <h2>Local Schools</h2>
            <table className="sales-table">
              <thead><tr><th>School</th><th>Level</th><th>Distance</th></tr></thead>
              <tbody>
                {amenities.schools.map(s => (
                  <tr key={s.name}><td>{s.name}</td><td>{s.level}</td><td>{formatDistance(s.distance_m)}</td></tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="content-section">
          <h2>The Area</h2>
          <p>{config.areaInfo}</p>
          <p>
            More local prices:{" "}
            {config.relatedAreas.map((a, i) => (
              <span key={a.slug}>
                {i > 0 && ", "}
                <Link to={`/area/${a.slug}`}>{a.name}</Link>
              </span>
            ))}
            {config.eircode && <>, <Link to={`/eircode/${config.eircode}`}>{config.eircode} postcode</Link></>}
            {" "}and <Link to={`/county/${config.countySlug}`}>County {config.county}</Link>.
          </p>
        </section>

        {data.transactions.length > 0 && (
          <section className="content-section">
            <h2>Recent Sales in {config.name}</h2>
            <SalesTable rows={data.transactions} />
            {data.totalTransactions > data.transactions.length && (
              <p className="content-note">Showing the {data.transactions.length} most recent of {data.totalTransactions} recorded sales.</p>
            )}
          </section>
        )}

        <section className="content-section">
          <h2>Frequently Asked Questions</h2>
          {faqs.map((f, i) => (
            <div key={i} className="faq-item">
              <h3>{f.q}</h3>
              <p>{f.a}</p>
            </div>
          ))}
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd).replace(/</g, "\\u003c") }} />
        </section>

        <section className="content-section">
          <h2>Search Nearby Properties</h2>
          <MapSearchThumb
            to={`/?q=${encodeURIComponent(`${config.latitude},${config.longitude}`)}`}
            label={`Search around ${config.name} on the map`}
          />
          <p>Browse <Link to="/developments">other developments</Link> or value a home with the <Link to="/valuation">valuation tool</Link>.</p>
        </section>

        <Footer />
      </div>
    </>
  );
}
