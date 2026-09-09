import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCountySummary } from "../api";
import TrendsChart from "./TrendsChart";
import PageHeader from "./PageHeader";
import type { CountySummary } from "../types";
import type { CountyContent } from "../content/countyData";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  getCachedCountyData,
  setCachedCountyData,
} from "../utils/countyDataCache";
import Breadcrumbs from "./Breadcrumbs";
import MapSearchThumb from "./MapSearchThumb";
import StreetLevelAnalysis from "./StreetLevelAnalysis";
import { countySlug } from "../areas";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

// Eager glob: county stats/trends/recent-sales are bundled so custom-template
// counties (Cork/Galway) render their full content into static HTML at SSG
// prerender time. Without this the stats block was client-fetched and gated
// behind `{data && …}`, so crawlers saw an almost-empty page.
const COUNTY_DATA = import.meta.glob<{ default: CountySummary }>("../data/counties/*.json", { eager: true });

function bakedCounty(slug: string): CountySummary | undefined {
  return COUNTY_DATA[`../data/counties/${slug}.json`]?.default;
}

interface CountyPageTemplateProps {
  content: CountyContent;
}

export default function CountyPageTemplate({ content }: CountyPageTemplateProps) {
  const slug = countySlug(content.name);
  const baked = bakedCounty(slug);
  const [fetched, setFetched] = useState<CountySummary | null>(null);
  const data = baked ?? fetched;
  const [loading, setLoading] = useState(!baked);
  const [error, setError] = useState<string | null>(null);

  // SEO meta tags
  const meta = usePageMeta(content.metaTitle, content.metaDescription, [
    { name: "Area Guides", url: "/areaguides" },
    { name: `County ${content.name}`, url: `/county/${countySlug(content.name)}` },
  ]);

  useEffect(() => {
    if (baked) return;   // fully baked at build time; no cache/fetch needed

    // localStorage cache, then a live API fallback.
    const cached = getCachedCountyData(content.name);
    if (cached) {
      setFetched(cached);
      setLoading(false);
    } else {
      setLoading(true);
      fetchCountySummary(content.name)
        .then((freshData) => {
          setFetched(freshData);
          setCachedCountyData(content.name, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content.name]);

  const latestTrend = data?.trends[data.trends.length - 1];
  const earliestTrend = data?.trends[0];

  return (
    <>
      {meta}
      <PageHeader title={`Property Prices in County ${content.name}`} />
      <div className="content-page">
        <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: `County ${content.name}`, url: `/county/${countySlug(content.name)}` }]} />
        {/* Hero Images - 3 images in a grid */}
        {content.heroImages && content.heroImages.length > 0 && (
          <div className="county-hero-images">
            {content.heroImages.map((image, idx) => (
              <div key={idx} className="county-hero-image">
                <img
                  src={image.url}
                  alt={image.alt}
                  loading={idx === 0 ? "eager" : "lazy"}
                />
                {image.credit && (
                  <p className="image-credit">{image.credit}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Intro paragraph */}
        <p className="content-intro">{content.intro}</p>

        {/* Loading state */}
        {loading && <div className="content-loading">Loading data…</div>}
        {error && <div className="error-msg">{error}</div>}

        {/* Stats grid */}
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

            {/* Market Overview */}
            <section className="content-section">
              <h2>Market Overview</h2>
              <p>{content.marketOverview}</p>
              {content.highlights && content.highlights.length > 0 && (
                <ul className="highlights-list">
                  {content.highlights.map((highlight, idx) => (
                    <li key={idx}>{highlight}</li>
                  ))}
                </ul>
              )}
            </section>

            {/* Popular Areas */}
            {content.popularAreas.length > 0 && (
              <section className="content-section">
                <h2>Popular Areas in County {content.name}</h2>
                <div className="areas-grid">
                  {content.popularAreas.map((area) => (
                    <Link
                      key={area.slug}
                      to={`/area/${area.slug}`}
                      className="area-card"
                    >
                      <h3>{area.name}</h3>
                      <p>{area.description}</p>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            <StreetLevelAnalysis countySlug={countySlug(content.name)} />

            {/* Price Trends */}
            {data.trends.length > 0 && (
              <section className="content-section">
                <h2>House Price Trends in County {content.name}</h2>
                <p>{content.trendsCommentary}</p>
                <div style={{ position: "relative", height: 240 }}>
                  <TrendsChart data={data.trends} onClose={() => {}} inline />
                </div>
              </section>
            )}

            {/* FAQs */}
            {content.faqs.length > 0 && (
              <section className="content-section">
                <h2>Frequently Asked Questions</h2>
                {content.faqs.map((faq, idx) => (
                  <div key={idx} className="faq-item">
                    <h3>{faq.question}</h3>
                    <p>{faq.answer}</p>
                  </div>
                ))}
              </section>
            )}

            {/* Neighboring Counties */}
            {content.neighboringCounties.length > 0 && (
              <section className="content-section">
                <h2>Nearby Counties</h2>
                <div className="county-links">
                  {content.neighboringCounties.map((slug) => (
                    <Link key={slug} to={`/county/${slug}`} className="county-link-btn">
                      County {slug.charAt(0).toUpperCase() + slug.slice(1)}
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* Search CTA */}
            <section className="content-section">
              <h2>Search Properties in County {content.name}</h2>
              <p>
                Use the <Link to={`/?q=${encodeURIComponent(content.name)}&county=${encodeURIComponent(content.name)}`}>interactive map</Link> to search
                by address or Eircode within County {content.name}.
              </p>
              <MapSearchThumb
                to={`/?q=${encodeURIComponent(content.name)}&county=${encodeURIComponent(content.name)}`}
                label={`Search County ${content.name} on the map`}
              />
              <p>
                Browse <Link to="/areaguides">all area guides</Link>.
              </p>
            </section>
          </>
        )}
      </div>
    </>
  );
}
