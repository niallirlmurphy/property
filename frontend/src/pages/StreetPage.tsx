import { useParams, Link } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import MapSearchThumb from "../components/MapSearchThumb";
import { usePageMeta } from "../hooks/usePageMeta";
import { streetFromSlug } from "../streets";
import type { StreetData } from "../types";

// Eager glob: all street data is bundled so the correct file is available
// synchronously at SSG prerender time (inlined into HTML for SEO).
const DATA = import.meta.glob<{ default: StreetData }>("../data/streets/*.json", { eager: true });

function dataForSlug(slug: string): StreetData | undefined {
  const mod = DATA[`../data/streets/${slug}.json`];
  return mod?.default;
}

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

export default function StreetPage() {
  const { slug } = useParams<{ slug: string }>();
  const config = streetFromSlug(slug ?? "");
  const data = config ? dataForSlug(config.slug) : undefined;

  const crumbs = config
    ? [
        { name: `County ${config.county}`, url: `/county/${config.countySlug}` },
        { name: "Notable Streets", url: "/streets" },
        { name: config.name, url: `/street/${config.slug}` },
      ]
    : [];

  const title = config ? `Property Prices on ${config.name}, ${config.area}` : undefined;
  const meta = usePageMeta(
    title,
    config
      ? `${config.description} See recent sales and price trends for ${config.name}, ${config.area}, Co. ${config.county} from Ireland's Property Price Register.`
      : undefined,
    crumbs,
    config?.image,
  );

  if (!config || !data) {
    return (
      <>
        <PageHeader title="Street not found" />
        <div className="content-page"><h1>Street not found</h1></div>
      </>
    );
  }

  const { stats } = data;
  const q = `${config.name}, ${config.area}`;
  const faqs = [
    {
      q: `What is the average price on ${config.name}?`,
      a: `The average sale price recorded on ${config.name}, ${config.area} is ${formatPrice(stats.avg)}, based on ${stats.count} sales on the Property Price Register.`,
    },
    {
      q: `How many properties have sold on ${config.name}?`,
      a: `${stats.count} residential sales on ${config.name}, ${config.area} have been recorded on the Property Price Register${stats.firstYear ? ` since ${stats.firstYear}` : ""}.`,
    },
    {
      q: `What is the median price on ${config.name}?`,
      a: `The median sale price on ${config.name}, ${config.area} is ${formatPrice(stats.median)}, with recorded sales ranging from ${formatPrice(stats.min)} to ${formatPrice(stats.max)}.`,
    },
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
        <h1>Property Prices on {config.name}, {config.area}</h1>

        {config.image && (
          <img
            className="area-hero"
            src={config.image}
            alt={config.imageAlt ?? config.name}
            width={2000}
            height={1500}
            loading="lazy"
          />
        )}

        {config.info && <p className="area-info">{config.info}</p>}
        <p className="content-intro">{config.description}</p>

        <div className="stats-grid">
          <div className="stat-card"><span>Median price</span><strong>{formatPrice(stats.median)}</strong></div>
          <div className="stat-card"><span>Average price</span><strong>{formatPrice(stats.avg)}</strong></div>
          <div className="stat-card"><span>Sales on record</span><strong>{stats.count.toLocaleString()}</strong></div>
          <div className="stat-card"><span>Price range</span><strong>{formatPrice(stats.min)} – {formatPrice(stats.max)}</strong></div>
        </div>

        {data.trends.length > 0 && (
          <section className="content-section">
            <h2>Price Trends on {config.name}</h2>
            <p>Median and average sale prices by year, {stats.firstYear}–{stats.lastYear}.</p>
            <div style={{ position: "relative", height: 240 }}>
              <TrendsChart data={data.trends} onClose={() => {}} inline />
            </div>
          </section>
        )}

        {data.transactions.length > 0 && (
          <section className="content-section">
            <h2>Recent Sales on {config.name}</h2>
            <table className="sales-table">
              <thead><tr><th>Address</th><th>Date</th><th>Beds</th><th>Type</th><th>Price</th></tr></thead>
              <tbody>
                {data.transactions.map((t, i) => (
                  <tr key={i}>
                    <td>{t.address}</td>
                    <td>{t.date}</td>
                    <td>{t.bedrooms ?? "—"}</td>
                    <td>{t.propertyType ?? "—"}</td>
                    <td>{formatPrice(t.price)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
            to={`/?q=${encodeURIComponent(q)}`}
            label={`Search around ${config.name} on the map`}
          />
          <p>
            {config.name} is in <Link to={`/county/${config.countySlug}`}>County {config.county}</Link>.{" "}
            Browse <Link to="/streets">all notable streets</Link>.
          </p>
        </section>

        <Footer />
      </div>
    </>
  );
}
