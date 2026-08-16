import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import type { Property } from "../types";

// Fix Leaflet icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Active marker icon (red)
const activeIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Dublin city center (south and central) - default view
const DUBLIN_CITY_CENTER: [number, number] = [53.3398, -6.2603]; // Dublin 2
const DUBLIN_CITY_ZOOM = 13; // Zoomed in to city level

function formatPrice(price: number) {
  return "€" + Math.round(price).toLocaleString("en-IE");
}
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-IE', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Component to setup drawing tools
function DrawTools({
  onShapeCreated,
  onShapeDeleted
}: {
  onShapeCreated: (type: string, coordinates: number[][]) => void;
  onShapeDeleted: () => void;
}) {
  const map = useMap();
  const drawnItemsRef = useRef<L.FeatureGroup>(new L.FeatureGroup());

  useEffect(() => {
    const drawnItems = drawnItemsRef.current;
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      position: 'topleft',
      draw: {
        polyline: false,
        polygon: {
          allowIntersection: false,
          showArea: true,
          shapeOptions: {
            color: '#3b82f6',
            fillOpacity: 0.2
          }
        },
        rectangle: {
          shapeOptions: {
            color: '#3b82f6',
            fillOpacity: 0.2
          }
        },
        circle: {
          shapeOptions: {
            color: '#3b82f6',
            fillOpacity: 0.2
          }
        },
        marker: false,
        circlemarker: false,
      },
      edit: {
        featureGroup: drawnItems,
        remove: true
      }
    });

    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (e: any) => {
      const layer = e.layer;
      const type = e.layerType;

      drawnItems.addLayer(layer);

      let coordinates: number[][] = [];

      if (type === 'polygon') {
        coordinates = layer.getLatLngs()[0].map((ll: L.LatLng) => [ll.lat, ll.lng]);
      } else if (type === 'rectangle') {
        const bounds = layer.getBounds();
        coordinates = [
          [bounds.getNorth(), bounds.getWest()],
          [bounds.getNorth(), bounds.getEast()],
          [bounds.getSouth(), bounds.getEast()],
          [bounds.getSouth(), bounds.getWest()],
          [bounds.getNorth(), bounds.getWest()],
        ];
      } else if (type === 'circle') {
        const center = layer.getLatLng();
        const radius = layer.getRadius() / 1000; // Convert to km
        // For circle, we'll use center and radius differently
        coordinates = [[center.lat, center.lng, radius]];
      }

      onShapeCreated(type, coordinates);
    });

    map.on(L.Draw.Event.DELETED, () => {
      onShapeDeleted();
    });

    return () => {
      map.removeControl(drawControl);
      map.removeLayer(drawnItems);
    };
  }, [map, onShapeCreated, onShapeDeleted]);

  return null;
}

// Component to handle map events and flying to regions
function MapController({ center }: { center: [number, number] | null }) {
  const map = useMap();

  useEffect(() => {
    if (center) map.flyTo(center, 11, { duration: 1.5 });
  }, [center, map]);

  return null;
}

interface PolygonMapProps {
  searchResults: Property[];
  activeProperty: Property | null;
  onSelectProperty: (p: Property) => void;
  onShapeCreated: (type: string, coordinates: number[][]) => void;
  onShapeDeleted: () => void;
  flyToCenter: [number, number] | null;
}

export default function PolygonMap({
  searchResults,
  activeProperty,
  onSelectProperty,
  onShapeCreated,
  onShapeDeleted,
  flyToCenter,
}: PolygonMapProps) {
  return (
    <MapContainer
      center={DUBLIN_CITY_CENTER}
      zoom={DUBLIN_CITY_ZOOM}
      style={{ height: '100%', width: '100%', position: 'absolute' }}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <DrawTools onShapeCreated={onShapeCreated} onShapeDeleted={onShapeDeleted} />

      {searchResults
        .filter(p => p.latitude !== null && p.longitude !== null)
        .map(p => (
          <Marker
            key={p.id}
            position={[p.latitude!, p.longitude!]}
            icon={p.id === activeProperty?.id ? activeIcon : new L.Icon.Default()}
            eventHandlers={{ click: () => onSelectProperty(p) }}
          >
            <Popup>
              <div style={{ minWidth: '200px' }}>
                <strong style={{ fontSize: '1.1em' }}>{formatPrice(p.price)}</strong>
                <br />
                {p.address}
                <br />
                <small style={{ color: '#666' }}>
                  {formatDate(p.sale_date)}
                  {p.eircode && ` · ${p.eircode}`}
                </small>
              </div>
            </Popup>
          </Marker>
        ))}
      <MapController center={flyToCenter} />
    </MapContainer>
  );
}
