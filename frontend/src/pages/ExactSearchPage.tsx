import { useState, FormEvent, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import { searchProperties, searchExactAddress } from "../api";
import type { Property, TrendPoint } from "../types";
import "./ExactSearchPage.css";

function calculateTrendsFromProperties(properties: Property[]): TrendPoint[] {
  // Filter out non-market sales and group by year
  const validProperties = properties.filter(p => !p.not_full_market_price && p.sale_date);

  const byYear = new Map<number, number[]>();

  validProperties.forEach(p => {
    const year = new Date(p.sale_date).getFullYear();
    if (!byYear.has(year)) {
      byYear.set(year, []);
    }
    byYear.get(year)!.push(p.price);
  });

  const trends: TrendPoint[] = [];

  byYear.forEach((prices, year) => {
    prices.sort((a, b) => a - b);
    const count = prices.length;
    const median_price = count % 2 === 0
      ? (prices[count / 2 - 1] + prices[count / 2]) / 2
      : prices[Math.floor(count / 2)];
    const avg_price = prices.reduce((sum, p) => sum + p, 0) / count;
    const min_price = prices[0];
    const max_price = prices[count - 1];

    trends.push({
      year,
      count,
      median_price: Math.round(median_price),
      avg_price: Math.round(avg_price),
      min_price,
      max_price,
    });
  });

  return trends.sort((a, b) => a.year - b.year);
}

export default function ExactSearchPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Property[]>([]); // Filtered results for display
  const [allResults, setAllResults] = useState<Property[]>([]); // All results for trends
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [center, setCenter] = useState<{ lat: number; lon: number } | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const hasAutoSearched = useRef(false);

  // Search function that can be called from form submit or URL load
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    console.log("[S1 Search] Starting search for:", searchQuery);
    console.log("[S1 Search] API Base URL:", import.meta.env.VITE_API_URL || "/api");
    setLoading(true);
    setError(null);
    setResults([]);
    setAllResults([]);
    setTrends([]);
    setCenter(null);
    setHasSearched(true);

    try {
      // S1 search: just call the exact search API directly
      console.log("[S1 Search] Calling exact search API for:", searchQuery);
      const exactResult = await searchExactAddress(searchQuery);
      console.log("[S1 Search] Exact search returned", exactResult.count, "results");

      setResults(exactResult.results);
      setAllResults(exactResult.results);

      // Set center from first result with coordinates
      const withCoords = exactResult.results.find(r => r.latitude && r.longitude);
      if (withCoords) {
        setCenter({ lat: withCoords.latitude!, lon: withCoords.longitude! });
      }

      // Calculate trends
      if (exactResult.results.length > 0) {
        const trendsData = calculateTrendsFromProperties(exactResult.results);
        setTrends(trendsData);
      }

      // Update URL
      navigate(`/s1?q=${encodeURIComponent(searchQuery)}`, { replace: true });

      // Calculate trends from search results (all properties within 500m)
      if (response.results.length > 0) {
        console.log("[S1 Search] Calculating trends from", response.results.length, "properties");
        const trendsData = calculateTrendsFromProperties(response.results);
        console.log("[S1 Search] Trends calculated:", trendsData.length, "data points");
        setTrends(trendsData);
      }
    } catch (err) {
      console.error("[S1 Search] Search error:", err);

      let errorMsg = "Unable to search. Please try again in a moment.";

      if (err instanceof Error) {
        errorMsg = err.message; // Use the message from api.ts which has better error handling
      }

      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Form submit handler
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await performSearch(query);
  };

  // Read query from URL params and auto-search once
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery && !hasAutoSearched.current) {
      console.log("[S1 Search] Loading from URL:", urlQuery);
      setQuery(urlQuery);
      hasAutoSearched.current = true;
      performSearch(urlQuery);
    }
  }, [searchParams]);

  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setQuery("");
    setResults([]);
    setAllResults([]);
    setError(null);
    setTrends([]);
    setCenter(null);
    setHasSearched(false);
    navigate("/s1", { replace: true });
  };

  // Extract street name and number from address for matching
  const extractAddressTokens = (address: string): { number: string; street: string } => {
    const normalized = address.toLowerCase().trim();
    // Match leading number
    const numberMatch = normalized.match(/^(\d+[a-z]?)/);
    const number = numberMatch ? numberMatch[1] : "";

    // Extract street name (everything before first comma, excluding number)
    const withoutNumber = normalized.replace(/^\d+[a-z]?\s+/, "");
    const street = withoutNumber.split(",")[0].trim();

    return { number, street };
  };

  // Check if address matches the search query
  const isExactMatch = (address: string, searchQuery: string): boolean => {
    const searchTokens = extractAddressTokens(searchQuery);
    const addressTokens = extractAddressTokens(address);

    // Must match both number and street
    return searchTokens.number === addressTokens.number &&
           addressTokens.street.includes(searchTokens.street);
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
      <div className={`search-container ${(hasResults || hasSearched) ? "has-results" : "centered"}`}>
        {!hasSearched && (
          <div className="logo">
            <a href="/s1" onClick={handleLogoClick}>HomeIQ</a>
          </div>
        )}

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
                    <strong>What does this chart show?</strong> This chart displays median and average property prices
                    for <strong>all {allResults.length} properties</strong> found within 500 meters of this address.
                    The data represents the local market trends in the immediate neighborhood from 2010 to present,
                    helping you understand how property values have changed in this area over time.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : !loading && hasSearched && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h2>No Sales Found</h2>
          <p>No sales records found for this exact address.</p>
          {allResults.length > 0 && (
            <p className="nearby-info">
              Found {allResults.length} properties within 500m, but none match the exact address.
            </p>
          )}
          <div className="no-results-help">
            <strong>Suggestions:</strong>
            <ul>
              <li>Check the spelling of the address and house number</li>
              <li>Include the area name (e.g., "Crumlin" in "26 Slane Road, Crumlin")</li>
              <li>Try the <a href="/">main search</a> to see nearby properties</li>
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
        <p className="build-info">
          Build: {new Date().toLocaleString("en-IE", {
            dateStyle: "medium",
            timeStyle: "short",
          })}
        </p>
      </div>
    </div>
  );
}
