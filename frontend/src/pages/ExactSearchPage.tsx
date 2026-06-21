import { useState, FormEvent, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import { searchProperties, fetchTrends } from "../api";
import type { Property, TrendPoint } from "../types";
import "./ExactSearchPage.css";

export default function ExactSearchPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [results, setResults] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [center, setCenter] = useState<{ lat: number; lon: number } | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    console.log("[S1 Search] Starting search for:", query);
    setLoading(true);
    setError(null);
    setResults([]);
    setTrends([]);
    setCenter(null);

    try {
      // Use existing search endpoint with very small radius (50m)
      console.log("[S1 Search] Calling searchProperties with params:", {
        q: query,
        radius_km: 0.05,
      });

      const response = await searchProperties({
        q: query,
        radius_km: 0.05, // 50 meters for exact address matching
        county: undefined,
      });

      console.log("[S1 Search] Search response:", {
        resultCount: response.results.length,
        center: response.center,
      });

      setResults(response.results);
      setCenter(response.center);

      // Update URL
      navigate(`/s1?q=${encodeURIComponent(query)}`, { replace: true });

      // Load trends if we found results
      if (response.results.length > 0 && response.center) {
        console.log("[S1 Search] Loading trends for:", response.center);
        setTrendsLoading(true);
        try {
          const trendsData = await fetchTrends(
            `${response.center.lat},${response.center.lon}`,
            0.5, // 500m radius for trends
            response.results[0].county || undefined
          );
          console.log("[S1 Search] Trends loaded:", trendsData.length, "data points");
          setTrends(trendsData);
        } catch (err) {
          console.error("[S1 Search] Trends error:", err);
          if (err instanceof Error) {
            console.error("[S1 Search] Trends error message:", err.message);
            console.error("[S1 Search] Trends error stack:", err.stack);
          }
        } finally {
          setTrendsLoading(false);
        }
      }
    } catch (err) {
      console.error("[S1 Search] Main search error:", err);
      console.error("[S1 Search] Error type:", typeof err);
      console.error("[S1 Search] Error constructor:", err?.constructor?.name);

      let errorMsg = "An error occurred. Please try again.";

      if (err instanceof Error) {
        console.error("[S1 Search] Error message:", err.message);
        console.error("[S1 Search] Error stack:", err.stack);
        errorMsg = err.message;
      } else if (typeof err === 'string') {
        errorMsg = err;
      } else if (err && typeof err === 'object') {
        console.error("[S1 Search] Error object keys:", Object.keys(err));
        console.error("[S1 Search] Error JSON:", JSON.stringify(err, null, 2));

        // Try to extract meaningful error message
        if ('message' in err) {
          errorMsg = String(err.message);
        } else if ('detail' in err) {
          errorMsg = String(err.detail);
        } else if ('error' in err) {
          errorMsg = String(err.error);
        }
      }

      console.error("[S1 Search] Final error message:", errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Auto-search if query param present on mount (only once)
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && query === "") {
      // Only auto-search if we haven't set a query yet (first load)
      setQuery(q);
      // Trigger search after a brief delay to allow state to settle
      setTimeout(() => {
        const form = document.querySelector("form");
        if (form) form.requestSubmit();
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setQuery("");
    setResults([]);
    setError(null);
    setTrends([]);
    setCenter(null);
    navigate("/s1", { replace: true });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IE", {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-IE", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatPropertyType = (type: string) => {
    const formatted = type
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join('-');

    if (formatted === 'Semi-detached' || formatted === 'Detached' || formatted === 'Terraced') {
      return `${formatted} House`;
    }

    return formatted.charAt(0).toUpperCase() + formatted.slice(1);
  };

  const hasResults = results.length > 0;

  // Calculate statistics from results
  const stats = hasResults ? {
    total_sales: results.length,
    latest_sale: results[results.length - 1].sale_date,
    latest_price: results[results.length - 1].price,
    price_range: {
      min: Math.min(...results.map(r => r.price)),
      max: Math.max(...results.map(r => r.price)),
      median: results.map(r => r.price).sort((a, b) => a - b)[Math.floor(results.length / 2)],
    },
  } : null;

  return (
    <div className="exact-search-page">
      {/* Logo and Search Box */}
      <div className={`search-container ${hasResults ? "has-results" : "centered"}`}>
        <div className="logo">
          <a href="/s1" onClick={handleLogoClick}>HomeIQ</a>
        </div>

        <form onSubmit={handleSubmit} className="search-form">
          <div className="search-input-wrapper">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter exact address (e.g., 26 Slane Road, Crumlin, Dublin 12)"
              className="search-input"
              autoFocus
            />
            <button type="submit" className="search-button" disabled={loading}>
              {loading ? (
                <span className="spinner-small" />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {/* Results Section */}
      {hasResults ? (
        <div className="results-section">
          <div className="results-content">
            {/* Property Header */}
            <div className="property-header">
              <h1 className="property-address">{results[0].address}</h1>
              <div className="property-meta">
                <span>{results[0].county}</span>
                {results[0].eircode && (
                  <>
                    <span className="separator">•</span>
                    <span>{results[0].eircode}</span>
                  </>
                )}
              </div>
            </div>

            {/* Property Details Card */}
            {(results[0].bedrooms || results[0].property_type) && (
              <div className="details-card">
                <h2>Property Details</h2>
                <div className="details-grid">
                  {results[0].bedrooms && (
                    <div className="detail-item">
                      <span className="detail-label">Bedrooms</span>
                      <span className="detail-value">{results[0].bedrooms}</span>
                    </div>
                  )}
                  {results[0].property_type && (
                    <div className="detail-item">
                      <span className="detail-label">Property Type</span>
                      <span className="detail-value">{formatPropertyType(results[0].property_type)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Price Statistics */}
            {stats && (
              <div className="stats-card">
                <h2>Price History</h2>
                <div className="stats-grid">
                  <div className="stat-item highlight">
                    <span className="stat-label">Latest Sale</span>
                    <span className="stat-value">{formatPrice(stats.latest_price)}</span>
                    <span className="stat-date">{formatDate(stats.latest_sale)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Median Price</span>
                    <span className="stat-value">{formatPrice(stats.price_range.median)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Price Range</span>
                    <span className="stat-value">
                      {formatPrice(stats.price_range.min)} - {formatPrice(stats.price_range.max)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Sales</span>
                    <span className="stat-value">{stats.total_sales}</span>
                    <span className="stat-date">Since 2010</span>
                  </div>
                </div>
              </div>
            )}

            {/* Sales History Table */}
            <div className="sales-card">
              <h2>Sales History ({results.length} sales)</h2>
              <div className="sales-table-wrapper">
                <table className="sales-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Price</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((sale) => (
                      <tr key={sale.id}>
                        <td>{formatDate(sale.sale_date)}</td>
                        <td className="price-cell">
                          {formatPrice(sale.price)}
                          {sale.not_full_market_price && <span className="badge">Not Full Price</span>}
                          {sale.vat_exclusive && <span className="badge vat">VAT Excl.</span>}
                        </td>
                        <td className="details-cell">
                          {sale.bedrooms && <span>{sale.bedrooms} bed</span>}
                          {sale.property_type && <span>{sale.property_type}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Local Property Trends */}
            {trends.length > 0 && (
              <div className="trends-card">
                <h2>Local Property Trends</h2>
                <TrendsChart
                  data={trends}
                  onClose={() => {}}
                  inline={true}
                  county={results[0].county || undefined}
                />
                <div className="trends-note">
                  <p>
                    <strong>What am I looking at?</strong> This chart shows median and average property prices
                    for all properties within 500 meters (0.5km) of this address from 2010 to present.
                    Use this to understand local market trends in the immediate area.
                  </p>
                </div>
              </div>
            )}

            {trendsLoading && (
              <div className="trends-loading">
                <span className="spinner" />
                <span>Loading local property trends...</span>
              </div>
            )}
          </div>
        </div>
      ) : !loading && query && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h2>No Sales Found</h2>
          <p>No sales records found for this address within 50 meters.</p>
          <div className="no-results-help">
            <strong>Suggestions:</strong>
            <ul>
              <li>Check the spelling of the address</li>
              <li>Include the area name (e.g., "Crumlin" in "26 Slane Road, Crumlin")</li>
              <li>Try the <a href="/">main search</a> with a larger radius</li>
            </ul>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="search-footer">
        <p>
          <a href="/">Standard Search</a>
          <span className="separator">•</span>
          <a href="/s1">Single Property Search</a>
          <span className="separator">•</span>
          <a href="/polygon">Map Search</a>
          <span className="separator">•</span>
          <a href="/about">About</a>
        </p>
      </div>
    </div>
  );
}
