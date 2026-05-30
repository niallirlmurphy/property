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

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

interface CountyPageTemplateProps {
  content: CountyContent;
}

export default function CountyPageTemplate({ content }: CountyPageTemplateProps) {
  const [data, setData] = useState<CountySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingCache, setUsingCache] = useState(false);

  // SEO meta tags
  usePageMeta(content.metaTitle, content.metaDescription);

  useEffect(() => {
    // Try to get cached data first
    const cached = getCachedCountyData(content.name);

    if (cached) {
      // Use cached data immediately
      setData(cached);
      setLoading(false);
      setUsingCache(true);
    } else {
      // No cache or expired - fetch from API
      setLoading(true);
      setUsingCache(false);

      fetchCountySummary(content.name)
        .then((freshData) => {
          setData(freshData);
          // Save to cache for next time
          setCachedCountyData(content.name, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [content.name]);

  const latestTrend = data?.trends[data.trends.length - 1];
  const earliestTrend = data?.trends[0];

  return (
    <>
      <PageHeader title={`Property Prices in County ${content.name}`} />
      <div className="content-page">
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
                Use the <Link to={`/?county=${content.name}`}>interactive map</Link> to search
                by address or Eircode within County {content.name}.
              </p>
            </section>
          </>
        )}
      </div>
    </>
  );
}
