import { useEffect, useState, lazy, Suspense } from "react";
import { ClientOnly } from "vite-react-ssg";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import type { HeatmapData, LocalityRow } from "./HeatmapMap";

const HeatmapMap = lazy(() => import("./HeatmapMap"));

const mapFallback = (
  <div style={{ height: "100%", width: "100%", position: "absolute", background: "#eef2f6" }} aria-hidden="true" />
);

// Whole-percent label for the legend, e.g. 19.6 -> "20%".
const pctLabel = (n: number) => `${Math.round(n)}%`;

// €thousands -> "€185k" / "€1.25m" (local copy so this page stays out of the
// Leaflet bundle that HeatmapMap pulls in).
function euroK(k: number): string {
  if (k >= 1000) return `€${(k / 1000).toFixed(2).replace(/\.?0+$/, "")}m`;
  return `€${Math.round(k)}k`;
}

const signedPct = (n: number) => `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;

// A ranked table of localities (top or bottom price growth).
function LocalityTable({ title, rows }: { title: string; rows: LocalityRow[] }) {
  return (
    <div className="heatmap-loc-table">
      <h3>{title}</h3>
      <table>
        <thead>
          <tr>
            <th>Locality</th>
            <th>County</th>
            <th style={{ textAlign: "right" }}>Change</th>
            <th style={{ textAlign: "right" }}>Median</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const [name, county, pct, early, late] = r;
            return (
              <tr key={i}>
                <td>{name}</td>
                <td>{county}</td>
                <td style={{ textAlign: "right", color: pct >= 0 ? "#b2182b" : "#2166ac", fontWeight: 600 }}>
                  {signedPct(pct)}
                </td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  {euroK(early)} → {euroK(late)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

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

        {data && (data.top_localities?.length > 0 || data.bottom_localities?.length > 0) && (
          <>
            <h2 style={{ marginTop: "1.5rem" }}>Fastest- and slowest-growing localities</h2>
            <p className="area-info" style={{ marginTop: 0 }}>
              Named places ranked by the change in median full-market sale price between
              {" "}{data.early_window} and {data.late_window}, limited to localities with at least
              {" "}{data.loc_min_count} sales in <em>both</em> periods so each figure is a stable
              comparison. A locality is attributed from each sale's address; entries where no clean
              place name could be resolved are excluded.
            </p>
            <div className="heatmap-loc-tables">
              <LocalityTable title="Highest price growth" rows={data.top_localities} />
              <LocalityTable title="Lowest price growth" rows={data.bottom_localities} />
            </div>
          </>
        )}
      </div>
      <Footer />
    </>
  );
}
