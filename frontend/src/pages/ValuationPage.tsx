import { useState } from "react";
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";
import { estimatePropertyValue } from "../api";
import type { ValuationResponse } from "../types";

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

function euro(n: number, decimals = 0) {
  return "€" + n.toLocaleString("en-IE", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-IE", { year: "numeric", month: "short", day: "numeric" });
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)}m`;
  return `${(meters / 1000).toFixed(2)}km`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ConfidenceBadge({ level }: { level: "high" | "medium" | "low" }) {
  const colors = {
    high: "val-badge-high",
    medium: "val-badge-medium",
    low: "val-badge-low",
  };
  return (
    <span className={`val-badge ${colors[level]}`}>
      {level === "high" && "High Confidence"}
      {level === "medium" && "Medium Confidence"}
      {level === "low" && "Low Confidence"}
    </span>
  );
}

function WarningBox({ warnings }: { warnings: Array<{ level: string; message: string }> }) {
  if (!warnings.length) return null;

  return (
    <div className="val-warnings">
      {warnings.map((w, i) => (
        <div key={i} className={`val-warning val-warning--${w.level}`}>
          <span className="val-warning-icon">
            {w.level === "error" && "⚠️"}
            {w.level === "warning" && "⚠"}
            {w.level === "info" && "ℹ"}
          </span>
          <span>{w.message}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ValuationPage() {
  usePageMeta(
    "Property Valuation - Estimate Irish Property Values",
    "Get a free property valuation estimate based on real Property Price Register sales data. Compare your property to similar sales in your area.",
  );

  const [address, setAddress] = useState("");
  const [eircode, setEircode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ValuationResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!address.trim()) {
      setError("Please enter a property address");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await estimatePropertyValue({
        address: address.trim(),
        eircode: eircode.trim() || undefined,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Valuation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="val-page">
      <PageHeader title="Property Valuation" />

      <div className="val-layout">
        {/* ── Input Form ── */}
        <aside className="val-inputs">
          <h2>Property Details</h2>

          <form onSubmit={handleSubmit}>
            <div className="val-field">
              <label htmlFor="address">Property Address *</label>
              <input
                id="address"
                type="text"
                placeholder="e.g., 26 Slane Road, Crumlin, Dublin 12"
                value={address}
                onChange={e => setAddress(e.target.value)}
                className="val-input"
                disabled={loading}
              />
            </div>

            <div className="val-field">
              <label htmlFor="eircode">Eircode (Optional)</label>
              <input
                id="eircode"
                type="text"
                placeholder="e.g., D12X567"
                value={eircode}
                onChange={e => setEircode(e.target.value.toUpperCase())}
                className="val-input"
                maxLength={8}
                disabled={loading}
              />
              <p className="val-field-hint">
                Providing an Eircode improves accuracy
              </p>
            </div>

            <button
              type="submit"
              className="val-submit"
              disabled={loading || !address.trim()}
            >
              {loading ? "Calculating..." : "Get Valuation"}
            </button>
          </form>

          {/* Info box */}
          <div className="val-info-box">
            <h3>How it works</h3>
            <ul>
              <li>We find similar properties sold nearby</li>
              <li>Prices are adjusted for time differences</li>
              <li>Weighted average based on distance &amp; recency</li>
              <li>Confidence level reflects data quality</li>
            </ul>
          </div>

          <div className="val-info-box">
            <h3>What addresses work?</h3>
            <ul>
              <li><strong>In database:</strong> Any property in the PPR (2010-present)</li>
              <li><strong>Not in database:</strong> Provide full address + Eircode</li>
              <li><strong>Tip:</strong> Include area name (e.g., "Crumlin")</li>
            </ul>
          </div>
        </aside>

        {/* ── Results ── */}
        <main className="val-output">
          {error && (
            <div className="val-error">
              <span className="val-error-icon">⚠️</span>
              <div>
                <strong>Valuation Failed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="val-loading">
              <div className="val-spinner"></div>
              <p>Analyzing comparable sales...</p>
            </div>
          )}

          {result && (
            <div className="val-results">
              {/* Estimate Card */}
              <div className="val-estimate-card">
                <div className="val-estimate-header">
                  <h2>Estimated Value</h2>
                  <ConfidenceBadge level={result.validation.confidence_level} />
                </div>

                <div className="val-estimate-value">
                  {euro(result.estimate)}
                </div>

                <div className="val-estimate-range">
                  <span>Range: {euro(result.confidence_interval.lower)} - {euro(result.confidence_interval.upper)}</span>
                  <span className="val-estimate-range-pct">±{result.confidence_interval.width_pct.toFixed(1)}%</span>
                </div>

                <div className="val-estimate-meta">
                  <div className="val-meta-item">
                    <span className="val-meta-label">Comparables</span>
                    <span className="val-meta-value">{result.validation.n_comparables}</span>
                  </div>
                  <div className="val-meta-item">
                    <span className="val-meta-label">Avg Distance</span>
                    <span className="val-meta-value">{result.validation.avg_distance_km.toFixed(2)}km</span>
                  </div>
                  <div className="val-meta-item">
                    <span className="val-meta-label">Quality Score</span>
                    <span className="val-meta-value">{(result.validation.quality_score * 100).toFixed(0)}/100</span>
                  </div>
                </div>
              </div>

              {/* Warnings */}
              <WarningBox warnings={result.validation.warnings} />

              {/* Statistics */}
              <div className="val-stats-card">
                <h3>Price Statistics</h3>
                <div className="val-stats-grid">
                  <div className="val-stat">
                    <span className="val-stat-label">Mean Price</span>
                    <span className="val-stat-value">{euro(result.statistics.mean_price)}</span>
                  </div>
                  <div className="val-stat">
                    <span className="val-stat-label">Median Price</span>
                    <span className="val-stat-value">{euro(result.statistics.median_price)}</span>
                  </div>
                  <div className="val-stat">
                    <span className="val-stat-label">Price Range</span>
                    <span className="val-stat-value">
                      {euro(result.statistics.min_price)} - {euro(result.statistics.max_price)}
                    </span>
                  </div>
                  <div className="val-stat">
                    <span className="val-stat-label">Std Deviation</span>
                    <span className="val-stat-value">{euro(result.statistics.std_dev)}</span>
                  </div>
                </div>
              </div>

              {/* Comparables Table */}
              <div className="val-comparables-card">
                <h3>Comparable Sales ({result.comparables.length})</h3>
                <div className="val-table-wrap">
                  <table className="val-table">
                    <thead>
                      <tr>
                        <th>Address</th>
                        <th>Sale Date</th>
                        <th>Original Price</th>
                        <th>Adjusted Price</th>
                        <th>Distance</th>
                        <th>Weight</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.comparables.map(comp => (
                        <tr key={comp.id}>
                          <td className="val-td-address">{comp.address}</td>
                          <td>{formatDate(comp.sale_date)}</td>
                          <td>{euro(comp.price)}</td>
                          <td className="val-td-adjusted">{euro(comp.adjusted_price)}</td>
                          <td>{formatDistance(comp.distance_m)}</td>
                          <td>{(comp.weight * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Metadata */}
              <div className="val-metadata">
                <p className="val-metadata-line">
                  <strong>Geocoded location:</strong> {result.metadata.geocoded_location.method}
                  {result.metadata.geocoded_location.address_matched &&
                    ` (${result.metadata.geocoded_location.address_matched})`}
                </p>
                <p className="val-metadata-line">
                  <strong>Valuation date:</strong> {formatDate(result.metadata.valuation_date)}
                </p>
                <p className="val-metadata-line">
                  <strong>Processing time:</strong> {(result.metadata.processing_time_ms / 1000).toFixed(2)}s
                </p>
              </div>
            </div>
          )}

          {!loading && !error && !result && (
            <div className="val-empty">
              <p>Enter a property address to get a valuation estimate</p>
            </div>
          )}
        </main>
      </div>

      {/* Footer with description and disclaimer */}
      <div className="val-footer">
        <p className="val-footer-intro">
          Get a free property valuation estimate based on comparable sales in the Property Price Register.
        </p>
        <div className="val-disclaimer">
          <h4>Important Notice</h4>
          <p>
            This valuation is a <strong>statistical estimate</strong> based on comparable sales in the Property Price Register.
            It should not be used as a formal property valuation for financial, legal, or tax purposes.
            Actual market value depends on property condition, specific features, market conditions, and other factors not captured in this analysis.
          </p>
          <p>
            For official valuations, consult a qualified property valuer or estate agent.
          </p>
        </div>
      </div>
    </div>
  );
}
