import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import WaffleMenu from "../components/WaffleMenu";
import PageHeader from "../components/PageHeader";
import type { Property } from "../types";

// County and Dublin postcode centroids for quick navigation
const REGION_CENTROIDS: Record<string, [number, number]> = {
  // Counties
  "Carlow": [52.8408, -6.9261],
  "Cavan": [53.9908, -7.3606],
  "Clare": [52.9047, -8.9810],
  "Cork": [51.8985, -8.4756],
  "Donegal": [54.6540, -8.1084],
  "Dublin": [53.3498, -6.2603],
  "Galway": [53.2707, -8.9630],
  "Kerry": [52.2593, -9.5695],
  "Kildare": [53.1581, -6.9115],
  "Kilkenny": [52.6541, -7.2448],
  "Laois": [52.9949, -7.3325],
  "Leitrim": [54.0667, -8.0000],
  "Limerick": [52.6638, -8.6267],
  "Longford": [53.7278, -7.7935],
  "Louth": [53.9523, -6.5325],
  "Mayo": [53.8544, -9.3005],
  "Meath": [53.6055, -6.6564],
  "Monaghan": [54.2492, -6.9681],
  "Offaly": [53.2360, -7.6421],
  "Roscommon": [53.7597, -8.2689],
  "Sligo": [54.2766, -8.4761],
  "Tipperary": [52.4733, -8.1621],
  "Waterford": [52.2593, -7.1101],
  "Westmeath": [53.5344, -7.4653],
  "Wexford": [52.3369, -6.4633],
  "Wicklow": [52.9810, -6.3676],
  // Dublin postcodes
  "Dublin 1": [53.3519, -6.2605],
  "Dublin 2": [53.3398, -6.2588],
  "Dublin 3": [53.3618, -6.2327],
  "Dublin 4": [53.3263, -6.2329],
  "Dublin 5": [53.3844, -6.1927],
  "Dublin 6": [53.3207, -6.2685],
  "Dublin 7": [53.3588, -6.2844],
  "Dublin 8": [53.3379, -6.2794],
  "Dublin 9": [53.3833, -6.2353],
  "Dublin 10": [53.3353, -6.3533],
  "Dublin 11": [53.3866, -6.3138],
  "Dublin 12": [53.3214, -6.3156],
  "Dublin 13": [53.3933, -6.1753],
  "Dublin 14": [53.2892, -6.2612],
  "Dublin 15": [53.3833, -6.3833],
  "Dublin 16": [53.2904, -6.2766],
  "Dublin 17": [53.4000, -6.1533],
  "Dublin 18": [53.2833, -6.2167],
  "Dublin 20": [53.3500, -6.3833],
  "Dublin 22": [53.3333, -6.3667],
  "Dublin 24": [53.2833, -6.3333],
};

// Map controls component
function MapControls({ onRegionSelect }: { onRegionSelect: (region: string) => void }) {
  return (
    <div className="absolute bottom-4 left-4 right-4 z-[1000] flex items-center gap-4 bg-white p-3 rounded-lg shadow-lg">
      <select
        onChange={(e) => onRegionSelect(e.target.value)}
        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        defaultValue=""
      >
        <option value="" disabled>Select a region...</option>
        <optgroup label="Counties">
          {Object.keys(REGION_CENTROIDS)
            .filter(k => !k.includes("Dublin") || k === "Dublin")
            .sort()
            .map(county => (
              <option key={county} value={county}>{county}</option>
            ))}
        </optgroup>
        <optgroup label="Dublin Postcodes">
          {Object.keys(REGION_CENTROIDS)
            .filter(k => k.includes("Dublin") && k !== "Dublin")
            .sort((a, b) => {
              const aNum = parseInt(a.split(" ")[1]);
              const bNum = parseInt(b.split(" ")[1]);
              return aNum - bNum;
            })
            .map(postcode => (
              <option key={postcode} value={postcode}>{postcode}</option>
            ))}
        </optgroup>
      </select>
    </div>
  );
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
function MapController({ selectedRegion }: { selectedRegion: string | null }) {
  const map = useMap();

  useEffect(() => {
    if (selectedRegion && REGION_CENTROIDS[selectedRegion]) {
      const [lat, lng] = REGION_CENTROIDS[selectedRegion];
      map.flyTo([lat, lng], 11, { duration: 1.5 });
    }
  }, [selectedRegion, map]);

  return null;
}

export default function PolygonSearchPage() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);

  const handleRegionSelect = (region: string) => {
    setSelectedRegion(region);
  };

  const handleShapeCreated = async (type: string, coordinates: number[][]) => {
    if (type === 'circle' && coordinates[0] && coordinates[0].length === 3) {
      // Circle search
      const lat = coordinates[0][0];
      const lng = coordinates[0][1];
      const radius = coordinates[0][2];
      await searchInCircle(lat, lng, radius);
    } else {
      // Polygon/rectangle search - convert to proper format
      const polyCoords: [number, number][] = coordinates.map(c => [c[0], c[1]]);
      await searchInPolygon(polyCoords);
    }
  };

  const handleShapeDeleted = () => {
    setSearchResults([]);
  };

  const searchInPolygon = async (coordinates: [number, number][]) => {
    setLoading(true);
    try {
      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/search/polygon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coordinates }),
      });

      if (!response.ok) throw new Error('Polygon search failed');

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const searchInCircle = async (lat: number, lng: number, radiusKm: number) => {
    setLoading(true);
    try {
      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/search?q=${lat},${lng}&radius_km=${radiusKm}`);

      if (!response.ok) throw new Error('Circle search failed');

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <PageHeader title="Map Search" />

      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <MapContainer
          center={[53.3498, -6.2603]}
          zoom={7}
          style={{ height: '100%', width: '100%', position: 'absolute' }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <DrawTools
            onShapeCreated={handleShapeCreated}
            onShapeDeleted={handleShapeDeleted}
          />

          <MapController selectedRegion={selectedRegion} />
        </MapContainer>

        <MapControls onRegionSelect={handleRegionSelect} />

        {/* Results panel */}
        {searchResults.length > 0 && (
          <div className="absolute top-4 right-4 w-80 bg-white rounded-lg shadow-lg p-4 max-h-[calc(100vh-200px)] overflow-y-auto z-[1000]">
            <h3 className="font-semibold text-lg mb-3">
              Found {searchResults.length} properties
            </h3>
            <div className="space-y-2">
              {searchResults.slice(0, 50).map((prop, idx) => (
                <div key={idx} className="p-2 border-b border-gray-200 text-sm">
                  <div className="font-medium">{prop.address}</div>
                  <div className="text-gray-600">
                    €{prop.price.toLocaleString('en-IE')}
                  </div>
                  <div className="text-gray-500 text-xs">
                    {new Date(prop.sale_date).toLocaleDateString('en-IE')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center z-[1001]">
            <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
              <div className="text-lg">Searching...</div>
            </div>
          </div>
        )}
      </div>

      <WaffleMenu />
    </div>
  );
}
