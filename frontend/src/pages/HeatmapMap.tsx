import { MapContainer, TileLayer, Rectangle, Tooltip } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";

export interface HeatmapData {
  generated_at: string;
  since_year: number;
  cell_deg: number;
  cell_half_deg: number;
  min_count: number;
  count: number;
  total_sales: number;
  palette: string[];
  breaks: number[];               // 6 interior breakpoints -> 7 buckets
  cells: [number, number, number, number][]; // [lat, lon, median_price, sale_count]
}

// Bucket a median price into a palette colour using the pre-computed breaks.
export function colorFor(median: number, breaks: number[], palette: string[]): string {
  for (let i = 0; i < breaks.length; i++) {
    if (median < breaks[i]) return palette[i];
  }
  return palette[palette.length - 1];
}

const euro = (n: number) =>
  new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

// Ireland, roughly centred. A conservative default view; users can pan/zoom.
const CENTER: [number, number] = [53.4, -7.9];

export default function HeatmapMap({ data }: { data: HeatmapData }) {
  const half = data.cell_half_deg;
  return (
    <MapContainer center={CENTER} zoom={7} minZoom={6} maxZoom={15} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {data.cells.map(([lat, lon, median, n], i) => {
        const bounds: LatLngBoundsExpression = [
          [lat - half, lon - half],
          [lat + half, lon + half],
        ];
        const fill = colorFor(median, data.breaks, data.palette);
        return (
          <Rectangle
            key={i}
            bounds={bounds}
            pathOptions={{ color: fill, fillColor: fill, fillOpacity: 0.6, weight: 0, stroke: false }}
          >
            <Tooltip sticky>
              <strong>{euro(median)}</strong> median
              <br />
              {n.toLocaleString()} sale{n === 1 ? "" : "s"} since {data.since_year}
            </Tooltip>
          </Rectangle>
        );
      })}
    </MapContainer>
  );
}
