import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapClickHandlerProps {
  onMapClick: (lat: number, lon: number) => void;
}

function MapClickHandler({ onMapClick }: MapClickHandlerProps) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

interface MapCenterUpdaterProps {
  center: [number, number] | null;
}

function MapCenterUpdater({ center }: MapCenterUpdaterProps) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 15, { animate: true });
    }
  }, [center, map]);
  return null;
}

interface ManualGeocodeMapProps {
  mapCenter: [number, number];
  markerPosition: [number, number] | null;
  onMapClick: (lat: number, lon: number) => void;
}

export default function ManualGeocodeMap({
  mapCenter,
  markerPosition,
  onMapClick,
}: ManualGeocodeMapProps) {
  return (
    <MapContainer
      center={mapCenter}
      zoom={13}
      style={{ width: "100%", height: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapClickHandler onMapClick={onMapClick} />
      <MapCenterUpdater center={markerPosition} />
      {markerPosition && <Marker position={markerPosition} />}
    </MapContainer>
  );
}
