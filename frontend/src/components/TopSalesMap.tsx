import L from "leaflet";
import { MapContainer, TileLayer, Marker, Tooltip } from "react-leaflet";

export interface TopSalePoint {
  label: string;   // rank, or "2·3" when two sales share a point
  name: string;
  price: string;
  lat: number;
  lon: number;
}

// Numbered pins for a ranked list of sales (higher ranks drawn on top), fitted to all of them. Client-only
// (Leaflet needs the DOM); the blog post lazy-loads it inside <ClientOnly>.
function rankIcon(label: string) {
  const w = Math.max(26, 12 + label.length * 7);   // widen the pill for "2·3", "4·16"
  return L.divIcon({
    className: "",
    html: `<div style="width:${w}px;height:26px;padding:0 4px;box-sizing:border-box;border-radius:13px;background:#1a56db;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4);color:#fff;font:600 12px/22px system-ui,sans-serif;text-align:center">${label}</div>`,
    iconSize: [w, 26],
    iconAnchor: [w / 2, 13],
  });
}

export default function TopSalesMap({ points }: { points: TopSalePoint[] }) {
  const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lon] as [number, number]));
  return (
    <MapContainer bounds={bounds} boundsOptions={{ padding: [30, 30] }} minZoom={6} maxZoom={18}
                  style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((p, i) => (
        <Marker key={p.label} position={[p.lat, p.lon]} icon={rankIcon(p.label)} zIndexOffset={points.length - i}
                title={`${p.label}. ${p.name}, ${p.price}`}>
          <Tooltip direction="top" offset={[0, -12]}>{`${p.label}. ${p.name} — ${p.price}`}</Tooltip>
        </Marker>
      ))}
    </MapContainer>
  );
}
