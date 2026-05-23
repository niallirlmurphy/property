import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import { fetchNextPropertyToGeocode, updatePropertyGeocode, skipPropertyGeocode } from "../api";
import type { Property } from "../types";
import "leaflet/dist/leaflet.css";
import "../index.css";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function formatPrice(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

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

export default function ManualGeocodePage() {
  const [property, setProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");
  const [address, setAddress] = useState<string>("");
  const [eircode, setEircode] = useState<string>("");
  const [markerPosition, setMarkerPosition] = useState<[number, number] | null>(null);
  const [saving, setSaving] = useState(false);
  const [queueEmpty, setQueueEmpty] = useState(false);

  const loadNextProperty = async () => {
    setLoading(true);
    setError(null);
    setLatitude("");
    setLongitude("");
    setAddress("");
    setEircode("");
    setMarkerPosition(null);
    setQueueEmpty(false);

    try {
      const next = await fetchNextPropertyToGeocode();
      if (!next) {
        setQueueEmpty(true);
        setProperty(null);
      } else {
        setProperty(next);
        setAddress(next.address);
        setEircode(next.eircode || "");
      }
    } catch (e: any) {
      setError(e.message ?? "Failed to load property");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNextProperty();
  }, []);

  const handleMapClick = (lat: number, lon: number) => {
    setMarkerPosition([lat, lon]);
    setLatitude(lat.toFixed(6));
    setLongitude(lon.toFixed(6));
  };

  const handleAccept = async () => {
    if (!property) return;
    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lon)) {
      setError("Invalid coordinates");
      return;
    }

    // Ireland bounds validation
    if (lat < 51.4 || lat > 55.5 || lon < -10.7 || lon > -5.4) {
      setError("Coordinates outside Ireland bounds");
      return;
    }

    if (!address.trim()) {
      setError("Address is required");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await updatePropertyGeocode(property.id, lat, lon, address.trim(), eircode.trim() || undefined);
      // Load next property
      await loadNextProperty();
    } catch (e: any) {
      setError(e.message ?? "Failed to save geocode");
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = async () => {
    if (!property) return;

    setSaving(true);
    setError(null);

    try {
      await skipPropertyGeocode(property.id);
      // Load next property
      await loadNextProperty();
    } catch (e: any) {
      setError(e.message ?? "Failed to skip property");
    } finally {
      setSaving(false);
    }
  };

  const mapCenter: [number, number] = markerPosition ?? [53.35, -7.5]; // Ireland center

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Header */}
      <header style={{
        display: "flex",
        alignItems: "center",
        padding: "1rem",
        background: "#1a3c5e",
        color: "white",
        gap: "1rem"
      }}>
        <Link to="/" style={{ color: "white", textDecoration: "none", fontSize: "1.5rem" }}>
          ←
        </Link>
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>Manual Geocoding</h1>
        {property && (
          <span style={{ marginLeft: "auto", fontSize: "0.875rem", opacity: 0.9 }}>
            ID: {property.id}
          </span>
        )}
      </header>

      {loading && (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <p>Loading next property...</p>
        </div>
      )}

      {queueEmpty && (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h2>🎉 Geocoding queue is empty!</h2>
          <p>All properties have been geocoded.</p>
          <Link to="/" style={{ color: "#1a3c5e" }}>Return home</Link>
        </div>
      )}

      {error && (
        <div style={{
          padding: "1rem",
          background: "#fee",
          color: "#c00",
          borderBottom: "1px solid #fcc"
        }}>
          {error}
        </div>
      )}

      {!loading && property && (
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left panel: Address details */}
          <div style={{
            width: "400px",
            padding: "1.5rem",
            overflowY: "auto",
            borderRight: "1px solid #ddd",
            background: "#f9f9f9"
          }}>
            <h2 style={{ marginTop: 0, fontSize: "1.125rem", color: "#1a3c5e" }}>
              Property Details
            </h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.25rem", fontWeight: 600 }}>
                Address:
              </label>
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={3}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  fontSize: "0.95rem",
                  fontFamily: "inherit",
                  resize: "vertical"
                }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <strong>County:</strong>
              <div style={{ marginTop: "0.25rem" }}>{property.county ?? "—"}</div>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.25rem", fontWeight: 600 }}>
                Eircode:
              </label>
              <input
                type="text"
                value={eircode}
                onChange={(e) => setEircode(e.target.value.toUpperCase())}
                placeholder="D02 XY12"
                maxLength={8}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  fontSize: "0.95rem",
                  textTransform: "uppercase"
                }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <strong>Price:</strong>
              <div style={{ marginTop: "0.25rem" }}>{formatPrice(property.price)}</div>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <strong>Sale Date:</strong>
              <div style={{ marginTop: "0.25rem" }}>
                {new Date(property.sale_date).toLocaleDateString("en-IE")}
              </div>
            </div>

            {property.description && (
              <div style={{ marginBottom: "1rem" }}>
                <strong>Description:</strong>
                <div style={{ marginTop: "0.25rem", fontSize: "0.875rem" }}>
                  {property.description}
                </div>
              </div>
            )}

            {property.size_description && (
              <div style={{ marginBottom: "1rem" }}>
                <strong>Size:</strong>
                <div style={{ marginTop: "0.25rem" }}>{property.size_description}</div>
              </div>
            )}

            <hr style={{ margin: "1.5rem 0", borderColor: "#ddd" }} />

            <p style={{ fontSize: "0.875rem", color: "#666" }}>
              Click the map to drop a pin at the correct location for this property.
            </p>
          </div>

          {/* Right panel: Map and controls */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <MapContainer
                center={mapCenter}
                zoom={13}
                style={{ width: "100%", height: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapClickHandler onMapClick={handleMapClick} />
                <MapCenterUpdater center={markerPosition} />
                {markerPosition && <Marker position={markerPosition} />}
              </MapContainer>
            </div>

            {/* Coordinates and buttons */}
            <div style={{ padding: "1.5rem", background: "white", borderTop: "1px solid #ddd" }}>
              <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem", fontWeight: 600 }}>
                    Latitude
                  </label>
                  <input
                    type="text"
                    value={latitude}
                    onChange={(e) => {
                      setLatitude(e.target.value);
                      const lat = parseFloat(e.target.value);
                      const lon = parseFloat(longitude);
                      if (!isNaN(lat) && !isNaN(lon)) {
                        setMarkerPosition([lat, lon]);
                      }
                    }}
                    placeholder="53.350140"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      fontSize: "0.95rem"
                    }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem", fontWeight: 600 }}>
                    Longitude
                  </label>
                  <input
                    type="text"
                    value={longitude}
                    onChange={(e) => {
                      setLongitude(e.target.value);
                      const lat = parseFloat(latitude);
                      const lon = parseFloat(e.target.value);
                      if (!isNaN(lat) && !isNaN(lon)) {
                        setMarkerPosition([lat, lon]);
                      }
                    }}
                    placeholder="-6.260310"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      fontSize: "0.95rem"
                    }}
                  />
                </div>
              </div>

              <div style={{ display: "flex", gap: "1rem" }}>
                <button
                  onClick={handleAccept}
                  disabled={!latitude || !longitude || saving}
                  style={{
                    flex: 1,
                    padding: "0.75rem",
                    background: latitude && longitude ? "#2a7c4f" : "#ccc",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    fontSize: "1rem",
                    fontWeight: 600,
                    cursor: latitude && longitude ? "pointer" : "not-allowed"
                  }}
                >
                  {saving ? "Saving..." : "Accept"}
                </button>
                <button
                  onClick={handleSkip}
                  disabled={saving}
                  style={{
                    flex: 1,
                    padding: "0.75rem",
                    background: "#666",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    fontSize: "1rem",
                    fontWeight: 600,
                    cursor: "pointer"
                  }}
                >
                  Skip
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
