import { useEffect, useRef } from "react";
import type { Property } from "../types";

const SEARCH_LIMIT = 200;

interface Props {
  results: Property[];
  activeId: number | null;
  onSelect: (p: Property) => void;
  exactMatchIds?: Set<number>;
  partialMatchIds?: Set<number>;
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

export default function ResultsList({ results, activeId, onSelect, exactMatchIds, partialMatchIds, hasSearched, loading }: Props) {
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

  const hasPartial = partialMatchIds && partialMatchIds.size > 0;
  const hasExact = exactMatchIds && exactMatchIds.size > 0;
  const hasMatches = hasPartial || hasExact;

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
      {hasMatches && (
        <div className="exact-match-header">Comparable sales</div>
      )}
      {results.map((p, i) => {
        const isPartial = partialMatchIds?.has(p.id) ?? false;
        const isExact = exactMatchIds?.has(p.id) ?? false;
        const isMatch = isPartial || isExact;
        const prevIsMatch = i > 0 ? (
          (partialMatchIds?.has(results[i - 1].id) ?? false) ||
          (exactMatchIds?.has(results[i - 1].id) ?? false)
        ) : false;
        const showDivider = hasMatches && !isMatch && prevIsMatch;
        return (
          <div key={p.id}>
            {showDivider && <div className="exact-match-divider">Nearby results</div>}
            <div
              ref={p.id === activeId ? activeRef : null}
              className={`result-card ${p.id === activeId ? "active" : ""} ${isMatch ? "exact-match" : ""}`}
              onClick={() => onSelect(p)}
            >
              {isPartial && <span className="exact-match-badge">Same street</span>}
              {isExact && <span className="exact-match-badge">Exact match</span>}
              <div className="result-price">{formatPrice(p.price)}</div>
              <div className="result-address">{p.address}</div>
              {(p.bedrooms || p.property_type) && (
                <div className="result-enriched">
                  {p.bedrooms && (
                    <span className="enriched-badge">
                      <span className="enriched-icon">🛏️</span>
                      {p.bedrooms} {p.bedrooms === 1 ? 'bed' : 'beds'}
                    </span>
                  )}
                  {/* Show property type, but filter out misclassified apartments
                      Heuristic: Properties €1M-€3M with 3+ beds are likely houses, not apartments
                      (Over €3M could be genuine luxury apartments, under €1M keep as-is) */}
                  {p.property_type && !(
                    p.property_type.toLowerCase() === 'apartment' &&
                    p.price > 1000000 &&
                    p.price < 3000000 &&
                    (p.bedrooms || 0) > 2
                  ) && (
                    <span className="enriched-badge">
                      <span className="enriched-icon">
                        {p.property_type.toLowerCase() === 'apartment' ? '🏢' : '🏠'}
                      </span>
                      {p.property_type}
                    </span>
                  )}
                </div>
              )}
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
