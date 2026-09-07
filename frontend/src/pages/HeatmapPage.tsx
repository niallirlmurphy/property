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

// Whole-percent label for the legend, e.g. 19.6 -> "20%".
const pctLabel = (n: number) => `${Math.round(n)}%`;

// Build human labels for each palette bucket from the interior % breaks.
function bucketLabels(breaks: number[]): string[] {
  const labels: string[] = [];
  for (let i = 0; i <= breaks.length; i++) {
    if (i === 0) labels.push(`< ${pctLabel(breaks[0])}`);
    else if (i === breaks.length) labels.push(`${pctLabel(breaks[i - 1])}+`);
    else labels.push(`${pctLabel(breaks[i - 1])}–${pctLabel(breaks[i])}`);
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

  const crumbs = [{ name: "House Price Growth Map", url: "/heatmap" }];
  const meta = usePageMeta(
    "Ireland House Price Growth Map",
    "An interactive map showing where house prices are rising fastest across Ireland. Each area is coloured by the change in median sale price between two periods of the Property Price Register — revealing the hottest and coolest local markets.",
    crumbs,
  );

  const labels = data ? bucketLabels(data.breaks) : [];

  return (
    <>
      {meta}
      <PageHeader title="Ireland House Price Growth Map" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Ireland House Price Growth Map</h1>
        {data ? (
          <p className="content-intro">
            Every coloured square shows how much the <strong>median sale price changed</strong> in
            that area between {data.early_window} and {data.late_window}, drawn from residential
            sales on Ireland's Property Price Register. <span style={{ color: "#b2182b", fontWeight: 600 }}>Red</span> areas
            are appreciating fastest; <span style={{ color: "#2166ac", fontWeight: 600 }}>blue</span> areas
            are lagging or cooling. Because prices rose almost everywhere, the scale is set relative
            to the national picture — so this shows where growth <em>out- or under-performed</em>,
            not simply where prices went up. Hover a square for the figures. Zoom and pan to explore.
          </p>
        ) : (
          <p className="content-intro">
            A map of where house prices are rising fastest across Ireland, from the Property Price Register.
          </p>
        )}

        {error && <div className="error-msg">{error}</div>}

        {data && (
          <div className="heatmap-legend" aria-label="Price-growth scale">
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
            Growth is the change in median full-market sale price between {data.early_window} and
            {" "}{data.late_window}, computed for {data.count.toLocaleString()} areas (each roughly
            4&nbsp;km across) that had at least {data.min_count} sales in <em>both</em> periods —
            {" "}{data.total_sales.toLocaleString()} sales in the later window. Requiring volume in
            both periods keeps each figure a stable comparison rather than the noise of one or two
            sales, which is why sparse rural areas do not appear. Colour buckets are set by
            quantile, so roughly half of areas fall on each side of the national median growth.
          </p>
        )}
      </div>
      <Footer />
    </>
  );
}
