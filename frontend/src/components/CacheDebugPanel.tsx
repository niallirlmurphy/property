import { useState, useEffect } from "react";
import {
  getCacheInfo,
  clearAllCountyCaches,
  formatCacheSize,
  getCacheSizeBytes,
} from "../utils/countyDataCache";

/**
 * Debug panel for cache management
 * Add to any page with: <CacheDebugPanel />
 * Or press Ctrl+Shift+C to toggle
 */
export default function CacheDebugPanel() {
  const [visible, setVisible] = useState(false);
  const [cacheInfo, setCacheInfo] = useState<ReturnType<typeof getCacheInfo>>([]);
  const [totalSize, setTotalSize] = useState(0);

  const refreshInfo = () => {
    setCacheInfo(getCacheInfo());
    setTotalSize(getCacheSizeBytes());
  };

  useEffect(() => {
    refreshInfo();

    // Keyboard shortcut: Ctrl+Shift+C
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "C") {
        setVisible((v) => !v);
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);

  if (!visible) return null;

  const handleClearAll = () => {
    if (confirm("Clear all county data caches?")) {
      clearAllCountyCaches();
      refreshInfo();
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        bottom: "20px",
        right: "20px",
        background: "white",
        border: "2px solid #3b82f6",
        borderRadius: "8px",
        padding: "16px",
        maxWidth: "400px",
        maxHeight: "80vh",
        overflow: "auto",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        zIndex: 9999,
        fontSize: "13px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
        <h3 style={{ margin: 0, fontSize: "16px" }}>County Data Cache</h3>
        <button
          onClick={() => setVisible(false)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "20px",
            lineHeight: "1",
          }}
        >
          ×
        </button>
      </div>

      <div style={{ marginBottom: "12px", color: "#6b7280" }}>
        <strong>Total:</strong> {cacheInfo.length} counties cached
        <br />
        <strong>Size:</strong> {formatCacheSize(totalSize)}
        <br />
        <strong>Cache duration:</strong> 45 days
      </div>

      {cacheInfo.length > 0 && (
        <div style={{ marginBottom: "12px" }}>
          <table style={{ width: "100%", fontSize: "12px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
                <th style={{ textAlign: "left", padding: "4px" }}>County</th>
                <th style={{ textAlign: "right", padding: "4px" }}>Age (days)</th>
                <th style={{ textAlign: "right", padding: "4px" }}>Size</th>
              </tr>
            </thead>
            <tbody>
              {cacheInfo.map((info) => (
                <tr key={info.county} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "4px", textTransform: "capitalize" }}>
                    {info.county}
                  </td>
                  <td
                    style={{
                      padding: "4px",
                      textAlign: "right",
                      color: info.ageInDays > 30 ? "#f59e0b" : "#10b981",
                    }}
                  >
                    {info.ageInDays}
                  </td>
                  <td style={{ padding: "4px", textAlign: "right", color: "#6b7280" }}>
                    {formatCacheSize(info.size)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ display: "flex", gap: "8px" }}>
        <button
          onClick={refreshInfo}
          style={{
            flex: 1,
            padding: "6px 12px",
            background: "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Refresh
        </button>
        <button
          onClick={handleClearAll}
          style={{
            flex: 1,
            padding: "6px 12px",
            background: "#ef4444",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Clear All
        </button>
      </div>

      <div
        style={{
          marginTop: "12px",
          padding: "8px",
          background: "#f3f4f6",
          borderRadius: "4px",
          fontSize: "11px",
          color: "#6b7280",
        }}
      >
        <strong>Tip:</strong> Press Ctrl+Shift+C to toggle this panel
      </div>
    </div>
  );
}
