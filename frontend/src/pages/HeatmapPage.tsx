import { useEffect, useState, lazy, Suspense } from "react";
import { ClientOnly } from "vite-react-ssg";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import type { HeatmapData } from "./HeatmapMap";

const HeatmapMap = lazy(() => import("./HeatmapMap"));

const mapFallback = (
  <div style={{ height: "100%", width: "100%", position: "absolute", background: "#eef2f6" }} aria-hidden="true" />
);

// Compact euro label for the legend, e.g. 170000 -> "€170k", 1250000 -> "€1.25m".
function shortEuro(n: number): string {
  if (n >= 1_000_000) return `€${(n / 1_000_000).toFixed(2).replace(/\.?0+$/, "")}m`;
  return `€${Math.round(n / 1000)}k`;
}

// Build human labels for each palette bucket from the interior breaks.
function bucketLabels(breaks: number[]): string[] {
  const labels: string[] = [];
  for (let i = 0; i <= breaks.length; i++) {
    if (i === 0) labels.push(`< ${shortEuro(breaks[0])}`);
    else if (i === breaks.length) labels.push(`${shortEuro(breaks[i - 1])}+`);
    else labels.push(`${shortEuro(breaks[i - 1])}–${shortEuro(breaks[i])}`);
  }
  return labels;
}

export default function HeatmapPage() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/heatmap.json")
      .then(r => {
        if (!r.ok) throw new Error(`Failed to load heat-map data (${r.status})`);
        return r.json();
      })
      .then(setData)
      .catch(e => setError(e.message));
  }, []);

  const crumbs = [{ name: "House Price Heat Map", url: "/heatmap" }];
  const meta = usePageMeta(
    "Ireland House Price Heat Map",
    "An interactive heat map of residential property prices across Ireland, showing the median sale price in every area from the Property Price Register. See at a glance where it is cheapest and most expensive to buy.",
    crumbs,
  );

  const labels = data ? bucketLabels(data.breaks) : [];

  return (
    <>
      {meta}
      <PageHeader title="Ireland House Price Heat Map" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Ireland House Price Heat Map</h1>
        <p className="content-intro">
          Every coloured square shows the <strong>median sale price</strong> of homes in that
          area, drawn from residential sales on Ireland's Property Price Register. Darker means
          more expensive. Hover a square for the exact figure. Zoom and pan to explore anywhere
          in the country.
        </p>

        {error && <div className="error-msg">{error}</div>}

        {data && (
          <div className="heatmap-legend" aria-label="Price scale">
            {data.palette.map((c, i) => (
              <div className="heatmap-legend-item" key={i}>
                <span className="heatmap-legend-swatch" style={{ background: c }} />
                <span className="heatmap-legend-label">{labels[i]}</span>
              </div>
            ))}
          </div>
        )}

        <div style={{ position: "relative", height: "72vh", minHeight: 460, borderRadius: 8, overflow: "hidden", margin: "0.75rem 0 1rem" }}>
          <ClientOnly fallback={mapFallback}>
            {() => (
              <Suspense fallback={mapFallback}>
                {data ? <HeatmapMap data={data} /> : mapFallback}
              </Suspense>
            )}
          </ClientOnly>
        </div>

        {data && (
          <p className="area-info">
            Based on {data.total_sales.toLocaleString()} full-market sales from {data.since_year}
            {" "}onward, grouped into {data.count.toLocaleString()} areas (each roughly one square
            kilometre, minimum {data.min_count} sales). Sparse areas are omitted so every figure is
            a stable median rather than a single sale. Prices reflect recent sales only, so the map
            shows current values rather than historical ones.
          </p>
        )}
      </div>
      <Footer />
    </>
  );
}
