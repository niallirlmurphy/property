import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import L from "leaflet";
import type { Property, SearchResponse } from "../types";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const activeIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function formatPrice(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

function formatDate(dateString: string): string {
  // Convert YYYY-MM-DD to DD-MM-YYYY
  const [year, month, day] = dateString.slice(0, 10).split('-');
  return `${day}-${month}-${year}`;
}

function MapFlyTo({ center, radius }: { center: [number, number]; radius: number }) {
  const map = useMap();
  useEffect(() => {
    const zoom = radius <= 0.5 ? 17 : radius <= 1 ? 16 : radius <= 2 ? 15 : radius <= 5 ? 14 : 13;
    map.flyTo(center, zoom, { duration: 1 });
  }, [center, radius, map]);
  return null;
}

function MapPanTo({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.panTo(center, { animate: true, duration: 0.5 });
  }, [center, map]);
  return null;
}

interface PendingCenter {
  lat: number;
  lon: number;
  radius_km: number;
}

interface MapViewProps {
  initialCenter: [number, number];
  flyCenter: [number, number] | null;
  flyRadius: number;
  pendingCenter: PendingCenter | null;
  searchResult: SearchResponse | null;
  panTarget: [number, number] | null;
  mapProperties: Property[];
  activeProperty: Property | null;
  handleSelectProperty: (p: Property) => void;
}

export default function MapView({
  initialCenter,
  flyCenter,
  flyRadius,
  pendingCenter,
  searchResult,
  panTarget,
  mapProperties,
  activeProperty,
  handleSelectProperty,
}: MapViewProps) {
  return (
    <MapContainer center={initialCenter} zoom={7} style={{ width: "100%", height: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {flyCenter && <MapFlyTo center={flyCenter} radius={flyRadius} />}
      {pendingCenter && searchResult && (
        <Circle
          center={[pendingCenter.lat, pendingCenter.lon]}
          radius={pendingCenter.radius_km * 1000}
          pathOptions={{ color: "#1a3c5e", fillColor: "#1a3c5e", fillOpacity: 0.06, weight: 2 }}
        />
      )}
      <MapPanTo center={panTarget} />
      {mapProperties
        .filter(p => p.latitude !== null && p.longitude !== null)
        .map(p => (
          <Marker
            key={p.id}
            position={[p.latitude!, p.longitude!]}
            icon={p.id === activeProperty?.id ? activeIcon : new L.Icon.Default()}
            eventHandlers={{ click: () => handleSelectProperty(p) }}
          >
            <Popup>
              <strong>{formatPrice(p.price)}</strong><br />
              {p.address}<br />
              <small>{formatDate(p.sale_date)}{p.eircode ? ` · ${p.eircode}` : ""}</small>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
}
