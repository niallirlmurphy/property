import { useState } from "react";
import type { SearchParams } from "../types";

const MAX_RECENT = 5;
const RECENT_KEY = "homeiq_recent_searches";

function loadRecent(): string[] {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]"); }
  catch { return []; }
}

function saveRecent(q: string): string[] {
  const prev = loadRecent().filter(s => s !== q);
  const next = [q, ...prev].slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  return next;
}

const CURRENT_YEAR = new Date().getFullYear();

export const PERIOD_OPTIONS = [
  { label: "All time",          minYear: undefined },
  { label: "Previous 10 years", minYear: CURRENT_YEAR - 10 },
  { label: "Previous 5 years",  minYear: CURRENT_YEAR - 5 },
  { label: "Previous 2 years",  minYear: CURRENT_YEAR - 2 },
];

interface Props {
  counties: string[];
  loading: boolean;
  error: string | null;
  onSearch: (params: SearchParams) => void;
  onEircode?: (code: string) => void;
  resultSummary?: { count: number; radius_km: number } | null;
  defaultValues?: { q?: string; radius_km?: number; county?: string; period?: number };
  onOpenEmailAlert?: () => void;
}

export default function SearchPanel({ counties, loading, error, onSearch, resultSummary, defaultValues, onOpenEmailAlert }: Props) {
  const [q, setQ] = useState(defaultValues?.q ?? "");
  const [radiusKm, setRadiusKm] = useState(defaultValues?.radius_km ?? 0.5);
  const [period, setPeriod] = useState(defaultValues?.period ?? 2);
  const [county, setCounty] = useState(defaultValues?.county ?? "Dublin");
  const [recentSearches, setRecentSearches] = useState<string[]>(loadRecent);
  const [showRecent, setShowRecent] = useState(false);

  const submit = (query: string) => {
    if (!query.trim()) return;
    setQ(query);
    setShowRecent(false);
    setRecentSearches(saveRecent(query.trim()));
    onSearch({
      q: query.trim(),
      radius_km: radiusKm,
      min_year: PERIOD_OPTIONS[period].minYear,
      county: county || undefined,
    });
  };

  return (
    <form className="search-panel" onSubmit={e => { e.preventDefault(); submit(q); }}>
      <div style={{ position: "relative" }}>
        <label>Address</label>
        <input
          type="text"
          value={q}
          onChange={e => setQ(e.target.value)}
          onFocus={() => recentSearches.length > 0 && setShowRecent(true)}
          onBlur={() => setTimeout(() => setShowRecent(false), 150)}
          placeholder="e.g. D14, Rathmines, 53.33,-6.26"
          autoComplete="off"
        />
        {showRecent && recentSearches.length > 0 && (
          <div className="recent-searches">
            <div className="recent-searches-label">Recent</div>
            {recentSearches.map(s => (
              <div key={s} className="recent-search-item" onMouseDown={() => submit(s)}>
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, color: "#aaa" }}>
                  <polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/>
                </svg>
                {s}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="radius-row">
        <div>
          <label>Radius</label>
          <select value={radiusKm} onChange={e => setRadiusKm(Number(e.target.value))}>
            <option value={0.5}>0.5 km</option>
            <option value={1}>1 km</option>
            <option value={2}>2 km</option>
            <option value={5}>5 km</option>
            <option value={10}>10 km</option>
          </select>
        </div>
        <div>
          <label>Period</label>
          <select value={period} onChange={e => setPeriod(Number(e.target.value))}>
            {PERIOD_OPTIONS.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label>County</label>
        <select value={county} onChange={e => setCounty(e.target.value)}>
          <option value="">All counties</option>
          {counties.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <button type="submit" className="btn-search" disabled={loading || !q.trim()}>
        {loading && <span className="spinner" />}
        {loading ? "Searching…" : "Search"}
      </button>

      {resultSummary && !loading && (
        <div className="result-summary-line">
          {resultSummary.count.toLocaleString()} {resultSummary.count === 1 ? "result" : "results"} within {resultSummary.radius_km} km
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {onOpenEmailAlert && (
        <button
          type="button"
          onClick={onOpenEmailAlert}
          className="btn-email-alert"
          style={{
            width: "100%",
            padding: "0.75rem",
            marginTop: "1rem",
            backgroundColor: "#f8f9fa",
            border: "2px solid #1a3c5e",
            borderRadius: "4px",
            color: "#1a3c5e",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "0.95rem",
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = "#1a3c5e";
            e.currentTarget.style.color = "white";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = "#f8f9fa";
            e.currentTarget.style.color = "#1a3c5e";
          }}
        >
          📧 Property Email Alert
        </button>
      )}
    </form>
  );
}
