import { useEffect, useRef } from "react";
import type { EircodeResponse } from "../types";

interface Props {
  result: EircodeResponse;
  activeId: number | null;
  onSelect: (p: EircodeResponse["results"][number]) => void;
}

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

function formatDate(dateString: string): string {
  // Convert YYYY-MM-DD to DD-MM-YYYY
  const [year, month, day] = dateString.slice(0, 10).split('-');
  return `${day}-${month}-${year}`;
}

export default function EircodePanel({ result, activeId, onSelect }: Props) {
  const { code, match_type, stats, results } = result;
  const activeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeId]);

  return (
    <div className="results-panel">
      <div className="eircode-summary">
        <div className="eircode-summary-code">
          {code}
          <span className="eircode-summary-type">
            {match_type === "routing_key" ? "routing key" : "full eircode"}
          </span>
        </div>
        <div className="eircode-stats-grid">
          <div><span>Sales</span><strong>{stats.total_count.toLocaleString()}</strong></div>
          <div><span>Median</span><strong>{formatPrice(stats.median_price)}</strong></div>
          <div><span>Average</span><strong>{formatPrice(stats.avg_price)}</strong></div>
          <div>
            <span>Period</span>
            <strong>
              {stats.earliest_sale
                ? `${stats.earliest_sale.slice(0, 4)}–${stats.latest_sale?.slice(0, 4)}`
                : "—"}
            </strong>
          </div>
        </div>
        {results.length < stats.total_count && (
          <div className="results-truncated">
            Showing {results.length} of {stats.total_count.toLocaleString()} sales
          </div>
        )}
      </div>

      {results.map((p) => (
        <div
          key={p.id}
          ref={p.id === activeId ? activeRef : null}
          className={`result-card ${p.id === activeId ? "active" : ""}`}
          onClick={() => onSelect(p)}
        >
          <div className="result-price">{"€" + Math.round(p.price).toLocaleString("en-IE")}</div>
          <div className="result-address">{p.address}</div>
          <div className="result-meta">
            <span>{formatDate(p.sale_date)}</span>
            {p.eircode && <span>{p.eircode}</span>}
            {p.not_full_market_price && <span title="Not full market price">⚠ NMP</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
