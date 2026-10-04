import { lazy, Suspense, useEffect, useState } from "react";
import type { TrendPoint } from "../types";

// Recharts loads only when the chart nears the viewport. Recharts draws nothing
// during prerender anyway (ResponsiveContainer needs a measured width), so the
// fixed-height placeholder matches the prerendered HTML and hydration.
const TrendsPlot = lazy(() => import("./TrendsPlot"));

const PLOT_HEIGHT = 252;

interface Props {
  data: TrendPoint[];
  onClose: () => void;
  inline?: boolean;
}

// Callback ref (not useRef) so the observer attaches whenever the box mounts —
// on live-fallback pages it only appears once the fetched data arrives.
function useNearViewport<T extends Element>() {
  const [el, setEl] = useState<T | null>(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    if (!el || near) return;
    if (typeof IntersectionObserver === "undefined") return setNear(true);
    const io = new IntersectionObserver(
      (entries) => { if (entries.some((e) => e.isIntersecting)) setNear(true); },
      { rootMargin: "300px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [el, near]);
  return [setEl, near] as const;
}

export default function TrendsChart({ data, onClose, inline = false }: Props) {
  const [plotRef, showPlot] = useNearViewport<HTMLDivElement>();
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
      <div ref={plotRef} style={{ width: "100%", height: PLOT_HEIGHT }}>
        {showPlot && (
          <Suspense fallback={null}>
            <TrendsPlot data={data} />
          </Suspense>
        )}
      </div>
      <div className="trends-footer">
        {totalSales.toLocaleString()} sales (full market price)
      </div>
    </div>
  );
}
