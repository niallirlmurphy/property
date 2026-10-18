import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";

// Street map centred on a development's pin. Client-only (Leaflet needs the DOM);
// DevelopmentPage lazy-loads it inside <ClientOnly>.
export default function DevelopmentMap({ lat, lon, name }: { lat: number; lon: number; name: string }) {
  return (
    <MapContainer center={[lat, lon]} zoom={15} minZoom={8} maxZoom={18} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker center={[lat, lon]} radius={10} pathOptions={{ color: "#fff", weight: 3, fillColor: "#1a56db", fillOpacity: 1 }}>
        <Tooltip direction="top" offset={[0, -10]} permanent>{name}</Tooltip>
      </CircleMarker>
    </MapContainer>
  );
}
