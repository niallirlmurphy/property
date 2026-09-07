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
            Every coloured square shows how much the <strong>median resale price changed</strong> in
            that area between {data.early_window} and {data.late_window}, drawn from second-hand
            residential sales on Ireland's Property Price Register. <span style={{ color: "#b2182b", fontWeight: 600 }}>Red</span> areas
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
            Change in median <strong>second-hand</strong> sale price between {data.early_window} and
            {" "}{data.late_window}, across {data.count.toLocaleString()} areas (each roughly 4&nbsp;km)
            with at least {data.min_count} sales in <em>both</em> periods —
            {" "}{data.total_sales.toLocaleString()} sales in the later window. See the
            {" "}<a href="#methodology">methodology</a> below for how new-builds and outliers are
            handled.
          </p>
        )}

        {data && (data.top_localities?.length > 0 || data.bottom_localities?.length > 0) && (
          <>
            <h2 style={{ marginTop: "1.5rem" }}>Fastest- and slowest-growing localities</h2>
            <p className="area-info" style={{ marginTop: 0 }}>
              Named places ranked by the change in median second-hand sale price between
              {" "}{data.early_window} and {data.late_window}, on the same resale-only basis as the
              map above and limited to localities with at least {data.loc_min_count} sales in
              {" "}<em>both</em> periods so each figure is a stable comparison rather than the swing
              of a few sales. A locality is attributed from each sale's address; entries where no
              clean place name could be resolved are excluded.
            </p>
            <div className="heatmap-loc-tables">
              <LocalityTable title="Highest price growth" rows={data.top_localities} />
              <LocalityTable title="Lowest price growth" rows={data.bottom_localities} />
            </div>
          </>
        )}

        {data && (
          <section className="heatmap-methodology" id="methodology">
            <h2>Methodology</h2>
            <p>
              This map and the tables above measure price <em>movement</em>, not a change in the
              type of property that happened to sell. To do that they use a like-for-like
              second-hand price index built from Ireland's Property Price Register, with the
              following steps:
            </p>
            <ol>
              <li>
                <strong>Two time windows.</strong> The median sale price in an early window
                ({data.early_window}) is compared with a late window ({data.late_window}); growth is
                the percentage change between the two medians.
              </li>
              <li>
                <strong>Second-hand sales only.</strong> New-build sales are excluded. A new
                development completes and sells in bulk within a single window, which would swamp a
                small area with cheaper units and collapse its median — a change in what sold, not a
                change in prices. (For example, this is why an all-sales measure showed Donnybrook
                “falling” when its resale market actually rose.)
              </li>
              <li>
                <strong>Price extremes removed.</strong> Individual sales below {euroK(data.price_floor / 1000)}
                {" "}(car-parking spaces, share and part-interest transfers, sites) or above
                {" "}{euroK(data.price_ceil / 1000)} (trophy homes) are dropped, as they are not
                representative of a local market.
              </li>
              <li>
                <strong>Bulk sales removed.</strong> A single Register entry covering a range of
                units (“Apartments 1–10”, “Units 1 to 76”) records many dwellings at one combined
                price, so these rows are excluded rather than counted as one enormous sale.
              </li>
              <li>
                <strong>Minimum volume.</strong> A grid square appears only if it had at least
                {" "}{data.min_count} qualifying sales in <em>both</em> windows; a named locality is
                ranked only with at least {data.loc_min_count} in both. Below these thresholds a
                median swings on which few homes happened to sell, producing misleading extremes, so
                sparse rural areas do not appear.
              </li>
              <li>
                <strong>Relative colour scale.</strong> Because prices rose almost everywhere, the
                map's colour buckets are set by quantile — roughly half of areas fall on each side of
                the national median growth — so the map highlights where growth out- or
                under-performed rather than simply where prices went up.
              </li>
            </ol>
            <p className="heatmap-methodology-note">
              Limitation: within a single area the mix of houses and apartments can still shift
              between the two windows, which a median cannot fully separate from genuine price
              change. Figures are indicative of local trends, not a valuation of any individual
              property. Source: Property Services Regulatory Authority — Residential Property Price
              Register. Data regenerated after each Register update.
            </p>
          </section>
        )}
      </div>
      <Footer />
    </>
  );
}
