import { useState, useEffect } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  defaultAddress?: string;
  defaultRadius?: number;
  defaultPeriod?: number;
  defaultCounty?: string;
  counties: string[];
}

const PERIOD_OPTIONS = [
  { label: "All time", minYear: undefined },
  { label: "Previous 10 years", minYear: new Date().getFullYear() - 10 },
  { label: "Previous 5 years", minYear: new Date().getFullYear() - 5 },
  { label: "Previous 2 years", minYear: new Date().getFullYear() - 2 },
];

export default function EmailAlertModal({
  isOpen,
  onClose,
  defaultAddress = "",
  defaultRadius = 2,
  defaultPeriod = 2,
  defaultCounty = "Dublin",
  counties,
}: Props) {
  const [address, setAddress] = useState(defaultAddress);
  const [radius, setRadius] = useState(defaultRadius);
  const [period, setPeriod] = useState(defaultPeriod);
  const [county, setCounty] = useState(defaultCounty);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update form when defaults change (when user fills search and opens modal)
  useEffect(() => {
    setAddress(defaultAddress);
    setRadius(defaultRadius);
    setPeriod(defaultPeriod);
    setCounty(defaultCounty);
  }, [defaultAddress, defaultRadius, defaultPeriod, defaultCounty, isOpen]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSuccess(false);
      setError(null);
      setEmail("");
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/email-alerts/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          address,
          radius_km: radius,
          min_year: PERIOD_OPTIONS[period].minYear,
          county: county || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to subscribe");
      }

      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to subscribe");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 10000,
        padding: "1rem",
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: "white",
          borderRadius: "8px",
          padding: "2rem",
          maxWidth: "500px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 600 }}>Property Email Alert</h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "1.5rem",
              cursor: "pointer",
              color: "#666",
              padding: "0.25rem",
              lineHeight: 1,
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {success ? (
          <div style={{ textAlign: "center", padding: "2rem 0" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>✓</div>
            <p style={{ fontSize: "1.1rem", color: "#22c55e", margin: 0 }}>
              Successfully subscribed! Check your email to confirm.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Address or Area
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. D14, Rathmines, Dublin 2"
                required
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Radius
                </label>
                <select
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    fontSize: "1rem",
                  }}
                >
                  <option value={0.5}>0.5 km</option>
                  <option value={1}>1 km</option>
                  <option value={2}>2 km</option>
                  <option value={5}>5 km</option>
                  <option value={10}>10 km</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Period
                </label>
                <select
                  value={period}
                  onChange={(e) => setPeriod(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    fontSize: "1rem",
                  }}
                >
                  {PERIOD_OPTIONS.map((opt, i) => (
                    <option key={i} value={i}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                County
              </label>
              <select
                value={county}
                onChange={(e) => setCounty(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              >
                <option value="">All counties</option>
                {counties.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Your Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
                required
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "0.75rem",
                backgroundColor: "#1a3c5e",
                color: "white",
                border: "none",
                borderRadius: "4px",
                fontSize: "1rem",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Subscribing..." : "Confirm Signup"}
            </button>

            {error && (
              <div
                style={{
                  marginTop: "1rem",
                  padding: "0.75rem",
                  backgroundColor: "#fee",
                  border: "1px solid #fcc",
                  borderRadius: "4px",
                  color: "#c33",
                  fontSize: "0.9rem",
                }}
              >
                {error}
              </div>
            )}

            <p
              style={{
                marginTop: "1rem",
                fontSize: "0.85rem",
                color: "#666",
                lineHeight: 1.5,
                textAlign: "center",
              }}
            >
              <strong>Privacy Notice:</strong> Your information will not be shared with third parties.
              You will receive at most one email per month with new properties matching your criteria.
              You can unsubscribe at any time.
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
