import { useState, useEffect } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  defaultAddress?: string;
  defaultRadius?: number;
  defaultCounty?: string;
  counties: string[];
}

export default function EmailAlertModal({
  isOpen,
  onClose,
  defaultAddress = "",
  defaultRadius = 2,
  defaultCounty = "Dublin",
  counties,
}: Props) {
  const [address, setAddress] = useState(defaultAddress);
  const [radius, setRadius] = useState(defaultRadius);
  const [county, setCounty] = useState(defaultCounty);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    address?: string;
    radius?: string;
    email?: string;
  }>({});

  // Update form when defaults change (when user fills search and opens modal)
  useEffect(() => {
    setAddress(defaultAddress);
    setRadius(defaultRadius);
    setCounty(defaultCounty);
  }, [defaultAddress, defaultRadius, defaultCounty, isOpen]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSuccess(false);
      setError(null);
      setEmail("");
      setValidationErrors({});
    }
  }, [isOpen]);

  const validateForm = (): boolean => {
    const errors: typeof validationErrors = {};

    // Validate address (minimum 3 characters)
    if (!address || address.trim().length < 3) {
      errors.address = "Please enter an address or area (minimum 3 characters)";
    }

    // Validate radius (must be positive number)
    if (!radius || radius <= 0 || radius > 20) {
      errors.radius = "Radius must be between 0.5 and 20 km";
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      errors.email = "Please enter a valid email address";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setValidationErrors({});

    // Validate form before submitting
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const BASE = import.meta.env.VITE_API_URL ?? "/api";
      const response = await fetch(`${BASE}/email-alerts/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          address: address.trim(),
          radius_km: radius,
          county: county || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Failed to subscribe (${response.status})`);
      }

      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      console.error("Email alert subscription error:", err);
      setError(err instanceof Error ? err.message : "Failed to subscribe. Please try again.");
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
              Successfully subscribed! You'll receive monthly alerts when new properties match your criteria.
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
                onChange={(e) => {
                  setAddress(e.target.value);
                  setValidationErrors((prev) => ({ ...prev, address: undefined }));
                }}
                placeholder="e.g. D14, Rathmines, Dublin 2"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: validationErrors.address ? "1px solid #ef4444" : "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              />
              {validationErrors.address && (
                <div style={{ marginTop: "0.25rem", fontSize: "0.85rem", color: "#ef4444" }}>
                  {validationErrors.address}
                </div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Radius
                </label>
                <select
                  value={radius}
                  onChange={(e) => {
                    setRadius(Number(e.target.value));
                    setValidationErrors((prev) => ({ ...prev, radius: undefined }));
                  }}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: validationErrors.radius ? "1px solid #ef4444" : "1px solid #ddd",
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
                {validationErrors.radius && (
                  <div style={{ marginTop: "0.25rem", fontSize: "0.85rem", color: "#ef4444" }}>
                    {validationErrors.radius}
                  </div>
                )}
              </div>

              <div>
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
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Your Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setValidationErrors((prev) => ({ ...prev, email: undefined }));
                }}
                placeholder="your.email@example.com"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: validationErrors.email ? "1px solid #ef4444" : "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              />
              {validationErrors.email && (
                <div style={{ marginTop: "0.25rem", fontSize: "0.85rem", color: "#ef4444" }}>
                  {validationErrors.email}
                </div>
              )}
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
