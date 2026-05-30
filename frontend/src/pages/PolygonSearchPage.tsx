import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import WaffleMenu from "../components/WaffleMenu";
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";
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

// Maximum allowed search area width (4km)
const MAX_SEARCH_WIDTH_KM = 4;
const MAX_RESULTS = 50;

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

// Tips overlay component
function MapTips() {
  const [isOpen, setIsOpen] = useState(true);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        style={{
          position: 'absolute',
          bottom: '5rem',
          left: '0.5rem',
          zIndex: 1000,
          backgroundColor: 'white',
          border: '2px solid #1a3c5e',
          borderRadius: '4px',
          padding: '0.5rem 0.75rem',
          cursor: 'pointer',
          fontSize: '0.85rem',
          fontWeight: 600,
          color: '#1a3c5e',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
        }}
      >
        ? Tips
      </button>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '5rem',
        left: '0.5rem',
        zIndex: 1000,
        backgroundColor: 'white',
        borderRadius: '6px',
        padding: '1rem',
        maxWidth: '280px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.15)',
        border: '1px solid #e5e7eb',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: '#1a3c5e' }}>
          How to use Map Search
        </h4>
        <button
          onClick={() => setIsOpen(false)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '1.25rem',
            cursor: 'pointer',
            color: '#999',
            padding: 0,
            lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>

      <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', lineHeight: 1.6, color: '#4b5563' }}>
        <li style={{ marginBottom: '0.5rem' }}>
          Use drawing tools (top-left) to select an area
        </li>
        <li style={{ marginBottom: '0.5rem' }}>
          Draw polygon, rectangle, or circle
        </li>
        <li style={{ marginBottom: '0.5rem' }}>
          Maximum search area: 4km width
        </li>
        <li style={{ marginBottom: '0.5rem' }}>
          Shows 50 most recent sales
        </li>
        <li style={{ marginBottom: '0.5rem' }}>
          Use region dropdown to jump to areas
        </li>
        <li>Click property markers or list items for details</li>
      </ul>
    </div>
  );
}

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
  const [activeProperty, setActiveProperty] = useState<Property | null>(null);
  const [error, setError] = useState<string | null>(null);

  // SEO meta tags
  usePageMeta(
    "Map Based Property Search | Ireland Property Prices",
    "Interactive map search for residential property sales in Ireland. Draw custom search areas to find properties sold in specific locations. View property prices, sale dates, and trends from Ireland's Property Price Register."
  );

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
    setActiveProperty(null);
    setError(null);
  };

  const calculatePolygonBounds = (coordinates: number[][]): number => {
    // Calculate width in kilometers
    const lats = coordinates.map(c => c[0]);
    const lngs = coordinates.map(c => c[1]);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    // Rough calculation: 1 degree lat ≈ 111km, 1 degree lng ≈ 85km at Ireland latitude
    const latWidth = (maxLat - minLat) * 111;
    const lngWidth = (maxLng - minLng) * 85;

    return Math.max(latWidth, lngWidth);
  };

  const searchInPolygon = async (coordinates: [number, number][]) => {
    setLoading(true);
    setError(null);
    setActiveProperty(null);

    try {
      // Check polygon width
      const width = calculatePolygonBounds(coordinates);
      if (width > MAX_SEARCH_WIDTH_KM) {
        setError(`Search area too large (${width.toFixed(1)}km). Maximum width is ${MAX_SEARCH_WIDTH_KM}km.`);
        setSearchResults([]);
        setLoading(false);
        return;
      }

      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/search/polygon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          coordinates,
          limit: MAX_RESULTS
        }),
      });

      if (!response.ok) throw new Error('Polygon search failed');

      const data = await response.json();
      setSearchResults(data.results || []);

      if (data.results.length === 0) {
        setError('No properties found in this area.');
      }
    } catch (error) {
      console.error('Search error:', error);
      setError('Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const searchInCircle = async (lat: number, lng: number, radiusKm: number) => {
    setLoading(true);
    setError(null);
    setActiveProperty(null);

    try {
      // Check radius
      if (radiusKm * 2 > MAX_SEARCH_WIDTH_KM) {
        setError(`Search radius too large (${radiusKm.toFixed(1)}km). Maximum radius is ${MAX_SEARCH_WIDTH_KM / 2}km.`);
        setSearchResults([]);
        setLoading(false);
        return;
      }

      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/search?q=${lat},${lng}&radius_km=${radiusKm}&limit=${MAX_RESULTS}`);

      if (!response.ok) throw new Error('Circle search failed');

      const data = await response.json();
      setSearchResults(data.results || []);

      if (data.results.length === 0) {
        setError('No properties found in this area.');
      }
    } catch (error) {
      console.error('Search error:', error);
      setError('Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return "€" + Math.round(price).toLocaleString("en-IE");
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-IE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <PageHeader title="Map Based Search - Select an area to see sold properties in that area" />

      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
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

          <DrawTools
            onShapeCreated={handleShapeCreated}
            onShapeDeleted={handleShapeDeleted}
          />

          {/* Property markers */}
          {searchResults
            .filter(p => p.latitude !== null && p.longitude !== null)
            .map(p => (
              <Marker
                key={p.id}
                position={[p.latitude!, p.longitude!]}
                icon={p.id === activeProperty?.id ? activeIcon : new L.Icon.Default()}
                eventHandlers={{
                  click: () => setActiveProperty(p),
                }}
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

          <MapController selectedRegion={selectedRegion} />
        </MapContainer>

        <MapTips />
        <MapControls onRegionSelect={handleRegionSelect} />

        {/* Loading overlay */}
        {loading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1001,
            }}
          >
            <div
              style={{
                backgroundColor: 'white',
                padding: '1.5rem 2rem',
                borderRadius: '8px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              }}
            >
              <div style={{ fontSize: '1.1rem' }}>Searching...</div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && !loading && (
          <div
            style={{
              position: 'absolute',
              top: '1rem',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '6px',
              padding: '0.75rem 1rem',
              color: '#c33',
              zIndex: 1000,
              maxWidth: '90%',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Results list below map */}
      {searchResults.length > 0 && (
        <div
          style={{
            backgroundColor: 'white',
            borderTop: '2px solid #e5e7eb',
            maxHeight: '40vh',
            overflowY: 'auto',
          }}
        >
          <div style={{ padding: '1rem' }}>
            <h3 style={{ margin: 0, marginBottom: '1rem', fontSize: '1.1rem', fontWeight: 600 }}>
              {searchResults.length} {searchResults.length === 1 ? 'Property' : 'Properties'} Found
              {searchResults.length === MAX_RESULTS && ' (showing 50 most recent)'}
            </h3>

            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {searchResults.map((prop) => (
                <div
                  key={prop.id}
                  onClick={() => setActiveProperty(prop)}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    backgroundColor: prop.id === activeProperty?.id ? '#eff6ff' : 'white',
                    borderColor: prop.id === activeProperty?.id ? '#3b82f6' : '#e5e7eb',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (prop.id !== activeProperty?.id) {
                      e.currentTarget.style.backgroundColor = '#f9fafb';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (prop.id !== activeProperty?.id) {
                      e.currentTarget.style.backgroundColor = 'white';
                    }
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                        {prop.address}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                        {formatDate(prop.sale_date)}
                        {prop.eircode && ` · ${prop.eircode}`}
                      </div>
                    </div>
                    <div style={{ fontWeight: 600, color: '#1a3c5e', whiteSpace: 'nowrap' }}>
                      {formatPrice(prop.price)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <WaffleMenu />
    </div>
  );
}
