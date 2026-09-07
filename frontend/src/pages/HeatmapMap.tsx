import { MapContainer, TileLayer, Rectangle, Tooltip } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";

export interface HeatmapData {
  generated_at: string;
  metric: string;                 // "price_growth_pct"
  early_window: string;           // e.g. "2020–2022"
  late_window: string;            // e.g. "2023–2026"
  cell_deg: number;
  cell_half_deg: number;
  min_count: number;
  price_floor: number;
  price_ceil: number;
  count: number;
  total_sales: number;
  palette: string[];
  breaks: number[];               // 6 interior breakpoints (% change) -> 7 buckets
  // [lat, lon, pct_change, early_median_k, late_median_k, late_sale_count]
  cells: [number, number, number, number, number, number][];
  loc_min_count: number;
  // [name, county, pct_change, early_median_k, late_median_k, late_sale_count]
  top_localities: LocalityRow[];
  bottom_localities: LocalityRow[];
}

export type LocalityRow = [string, string, number, number, number, number];

// Bucket a value into a palette colour using the pre-computed breaks.
export function colorFor(value: number, breaks: number[], palette: string[]): string {
  for (let i = 0; i < breaks.length; i++) {
    if (value < breaks[i]) return palette[i];
  }
  return palette[palette.length - 1];
}

// €thousands -> "€185k" / "€1.25m"
export function euroK(k: number): string {
  if (k >= 1000) return `€${(k / 1000).toFixed(2).replace(/\.?0+$/, "")}m`;
  return `€${Math.round(k)}k`;
}

const pct = (n: number) => `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;

// Default view zoomed in on Greater Dublin / the Leinster east, where transaction
// volume — and so the number of cells that clear the min-count in both windows —
// is highest and the map is most information-dense. Users can pan/zoom out to the
// rest of the country.
const CENTER: [number, number] = [53.36, -6.32];

export default function HeatmapMap({ data }: { data: HeatmapData }) {
  const half = data.cell_half_deg;
  return (
    <MapContainer center={CENTER} zoom={10} minZoom={6} maxZoom={15} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {data.cells.map(([lat, lon, change, earlyK, lateK, n], i) => {
        const bounds: LatLngBoundsExpression = [
          [lat - half, lon - half],
          [lat + half, lon + half],
        ];
        const fill = colorFor(change, data.breaks, data.palette);
        return (
          <Rectangle
            key={i}
            bounds={bounds}
            pathOptions={{ color: fill, fillColor: fill, fillOpacity: 0.6, weight: 0, stroke: false }}
          >
            <Tooltip sticky>
              <strong>{pct(change)}</strong> price change
              <br />
              {euroK(earlyK)} ({data.early_window}) → {euroK(lateK)} ({data.late_window})
              <br />
              {n.toLocaleString()} recent sale{n === 1 ? "" : "s"}
            </Tooltip>
          </Rectangle>
        );
      })}
    </MapContainer>
  );
}
