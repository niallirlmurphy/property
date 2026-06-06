import { useEffect, useRef } from "react";
import type { Property } from "../types";

const SEARCH_LIMIT = 200;

interface Props {
  results: Property[];
  activeId: number | null;
  onSelect: (p: Property) => void;
  exactMatchIds?: Set<number>;
  hasSearched?: boolean;
  loading?: boolean;
}

function formatPrice(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

function formatDist(m: number) {
  return m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(2)} km`;
}

function formatDate(dateString: string): string {
  // Convert YYYY-MM-DD to DD-MM-YYYY
  const [year, month, day] = dateString.slice(0, 10).split('-');
  return `${day}-${month}-${year}`;
}

export default function ResultsList({ results, activeId, onSelect, exactMatchIds, hasSearched, loading }: Props) {
  const activeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeId]);

  if (!results.length) {
    if (!hasSearched || loading) return null;
    return (
      <div className="results-empty">
        <div className="results-empty-icon">🏠</div>
        <div className="results-empty-title">No properties found</div>
        <div className="results-empty-hint">Try widening the radius, adjusting the date range, or clearing the county filter.</div>
      </div>
    );
  }

  const hasExact = exactMatchIds && exactMatchIds.size > 0;

  return (
    <div className="results-panel">
      <div className="results-summary">
        {results.length} {results.length === 1 ? "property" : "properties"} found
        {results.length >= SEARCH_LIMIT && (
          <span className="results-truncated" title="Reduce the search radius to see all results">
            {" "}· showing first {SEARCH_LIMIT}
          </span>
        )}
      </div>
      {hasExact && (
        <div className="exact-match-header">Exact address matches</div>
      )}
      {results.map((p, i) => {
        const isExact = exactMatchIds?.has(p.id) ?? false;
        const prevIsExact = i > 0 ? (exactMatchIds?.has(results[i - 1].id) ?? false) : false;
        const showDivider = hasExact && !isExact && prevIsExact;
        return (
          <div key={p.id}>
            {showDivider && <div className="exact-match-divider">Nearby results</div>}
            <div
              ref={p.id === activeId ? activeRef : null}
              className={`result-card ${p.id === activeId ? "active" : ""} ${isExact ? "exact-match" : ""}`}
              onClick={() => onSelect(p)}
            >
              {isExact && <span className="exact-match-badge">Exact match</span>}
              <div className="result-price">{formatPrice(p.price)}</div>
              <div className="result-address">
                {p.address}
                {(p.bedrooms || p.property_type) && (
                  <span className="property-details">
                    {p.bedrooms && `${p.bedrooms} bed`}
                    {p.bedrooms && p.property_type && " · "}
                    {p.property_type}
                  </span>
                )}
              </div>
              <div className="result-meta">
                <span>{formatDate(p.sale_date)}</span>
                {p.eircode && <span>{p.eircode}</span>}
                {p.distance_m != null && <span>{formatDist(p.distance_m)}</span>}
                {p.not_full_market_price && (
                  <span className="nmp-flag" title="Not a Full Market Price sale — may be a new build (VAT exclusive), transfer between connected parties, or social housing transaction">
                    ⚠ Not market price
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
