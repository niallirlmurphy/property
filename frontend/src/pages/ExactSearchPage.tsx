import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import TrendsChart from "../components/TrendsChart";
import { searchProperties, fetchTrends } from "../api";
import type { Property, TrendPoint } from "../types";
import "./ExactSearchPage.css";

export default function ExactSearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Property[]>([]); // Filtered results for display
  const [allResults, setAllResults] = useState<Property[]>([]); // All results for trends
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [center, setCenter] = useState<{ lat: number; lon: number } | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    console.log("[S1 Search] handleSubmit called, loading:", loading, "query:", query);

    if (loading) {
      console.log("[S1 Search] Already loading, ignoring submit");
      return;
    }

    if (!query.trim()) {
      console.log("[S1 Search] Empty query, ignoring submit");
      return;
    }

    console.log("[S1 Search] Starting search for:", query);
    console.log("[S1 Search] API Base URL:", import.meta.env.VITE_API_URL || "/api");
    setLoading(true);
    setError(null);
    setResults([]);
    setAllResults([]);
    setTrends([]);
    setCenter(null);

    try {
      // Detect county from query or default to Dublin
      const queryLower = query.toLowerCase();
      let county = "Dublin"; // Default assumption

      // Check if county is mentioned in query
      const counties = ["Dublin", "Cork", "Galway", "Limerick", "Waterford", "Wicklow", "Meath", "Kildare", "Louth", "Kerry", "Clare", "Tipperary", "Donegal", "Mayo", "Sligo", "Wexford", "Carlow", "Kilkenny", "Laois", "Offaly", "Westmeath", "Cavan", "Monaghan", "Longford", "Roscommon", "Leitrim"];
      for (const c of counties) {
        if (queryLower.includes(c.toLowerCase())) {
          county = c;
          break;
        }
      }

      console.log("[S1 Search] Using county:", county);
      console.log("[S1 Search] Calling searchProperties with params:", {
        q: query,
        radius_km: 0.5,
        county,
      });

      // Search with 500m radius, full database history, specified/assumed county
      const response = await searchProperties({
        q: query,
        radius_km: 0.5, // 500m radius
        county: county,
        min_year: undefined, // Full history
      });

      console.log("[S1 Search] Search response:", {
        totalResults: response.results.length,
        center: response.center,
      });

      // Store all results for trends
      setAllResults(response.results);
      setCenter(response.center);

      // Filter for exact address match using token matching
      const exactMatches = response.results.filter(prop =>
        isExactMatch(prop.address, query)
      );

      console.log("[S1 Search] Exact matches:", exactMatches.length, "of", response.results.length);

      if (exactMatches.length === 0 && response.results.length > 0) {
        console.log("[S1 Search] Sample addresses from search:");
        response.results.slice(0, 5).forEach(r => {
          const tokens = extractAddressTokens(r.address);
          console.log(`  ${r.address} -> number: "${tokens.number}", street: "${tokens.street}"`);
        });
        const queryTokens = extractAddressTokens(query);
        console.log("[S1 Search] Query tokens -> number: \"" + queryTokens.number + "\", street: \"" + queryTokens.street + "\"");
      }

      setResults(exactMatches);

      // Update URL
      navigate(`/s1?q=${encodeURIComponent(query)}`, { replace: true });

      // Load trends using all results (not just exact matches)
      if (response.results.length > 0 && response.center) {
        console.log("[S1 Search] Loading trends for all results");
        setTrendsLoading(true);
        try {
          const trendsData = await fetchTrends(
            `${response.center.lat},${response.center.lon}`,
            0.5, // 500m radius for trends (matches search)
            county
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

  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setQuery("");
    setResults([]);
    setAllResults([]);
    setError(null);
    setTrends([]);
    setCenter(null);
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
