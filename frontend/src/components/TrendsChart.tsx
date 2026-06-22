import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from "recharts";
import type { TrendPoint } from "../types";

interface Props {
  data: TrendPoint[];
  onClose: () => void;
  inline?: boolean;
}

function formatK(n: number) {
  return n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(1)}m` : n >= 1000 ? `€${(n / 1000).toFixed(0)}k` : `€${n}`;
}

function formatFull(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  // Get the count from the first payload item's original data point
  const count = payload[0]?.payload?.count;
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
      {count !== undefined && (
        <div className="trends-tooltip-row" style={{ marginTop: '4px', paddingTop: '4px', borderTop: '1px solid #e5e7eb' }}>
          <span>Transactions:</span>
          <strong>{count.toLocaleString()}</strong>
        </div>
      )}
    </div>
  );
};

export default function TrendsChart({ data, onClose, inline = false }: Props) {
  if (!data.length) return null;

  const totalSales = data.reduce((s, d) => s + d.count, 0);

  return (
    <div className={inline ? "trends-inline" : "trends-panel"}>
      <div className="trends-header">
        {!inline && <h3>Median sale price by year</h3>}
        {!inline && (
          <button onClick={onClose} className="trends-close" aria-label="Close trends">✕</button>
        )}
      </div>
      <ResponsiveContainer width="100%" height={252}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={formatK} tick={{ fontSize: 11 }} width={50} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="median_price" name="Median" stroke="#1a3c5e" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="avg_price"    name="Average" stroke="#e07b39" strokeWidth={2} dot={false} strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>
      <div className="trends-footer">
        {totalSales.toLocaleString()} sales (full market price)
      </div>
    </div>
  );
}
