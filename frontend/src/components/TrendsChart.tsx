import { useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from "recharts";
import type { TrendPoint } from "../types";
import { fetchTrends } from "../api";

interface Props {
  data: TrendPoint[];
  onClose: () => void;
  inline?: boolean;
  county?: string;
}

function formatK(n: number) {
  return n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(1)}m` : n >= 1000 ? `€${(n / 1000).toFixed(0)}k` : `€${n}`;
}

function formatFull(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="trends-tooltip">
      <div className="trends-tooltip-year">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="trends-tooltip-row">
          <span className="trends-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <strong>{formatFull(p.value)}</strong>
        </div>
      ))}
    </div>
  );
};

export default function TrendsChart({ data, onClose, inline = false, county }: Props) {
  const [countyData, setCountyData] = useState<TrendPoint[] | null>(null);
  const [loadingCounty, setLoadingCounty] = useState(false);
  const [showCounty, setShowCounty] = useState(false);

  if (!data.length) return null;

  const handleCountyToggle = async () => {
    if (!county) return;
    if (!showCounty && !countyData) {
      setLoadingCounty(true);
      try {
        const cd = await fetchTrends(undefined, 5, county);
        setCountyData(cd);
      } finally {
        setLoadingCounty(false);
      }
    }
    setShowCounty(v => !v);
  };

  // Merge area + county data by year for the chart
  const chartData = data.map(d => {
    const base: Record<string, any> = { year: d.year, median_price: d.median_price, avg_price: d.avg_price };
    if (showCounty && countyData) {
      const cRow = countyData.find(c => c.year === d.year);
      if (cRow) base.county_median = cRow.median_price;
    }
    return base;
  });

  const totalSales = data.reduce((s, d) => s + d.count, 0);

  return (
    <div className={inline ? "trends-inline" : "trends-panel"}>
      <div className="trends-header">
        {!inline && <h3>Median sale price by year</h3>}
        <div className="trends-actions">
          {county && (
            <button
              className={`trends-county-btn${showCounty ? " active" : ""}`}
              onClick={handleCountyToggle}
              disabled={loadingCounty}
              title={showCounty ? `Hide County ${county} comparison` : `Compare with County ${county}`}
            >
              {loadingCounty ? "…" : `vs ${county}`}
            </button>
          )}
          {!inline && (
            <button onClick={onClose} className="trends-close" aria-label="Close trends">✕</button>
          )}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={252}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={formatK} tick={{ fontSize: 11 }} width={50} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="median_price" name="Median" stroke="#1a3c5e" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="avg_price"    name="Average" stroke="#e07b39" strokeWidth={2} dot={false} strokeDasharray="4 2" />
          {showCounty && countyData && (
            <Line type="monotone" dataKey="county_median" name={`${county} median`} stroke="#6b9e3c" strokeWidth={1.5} dot={false} strokeDasharray="2 2" />
          )}
        </LineChart>
      </ResponsiveContainer>
      <div className="trends-footer">
        {totalSales.toLocaleString()} sales (full market price)
      </div>
    </div>
  );
}
