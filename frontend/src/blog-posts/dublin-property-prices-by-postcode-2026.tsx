import { Link } from "react-router-dom";

export function DublinPostcodesContent() {
  return (
    <div style={{
      fontSize: "1.125rem",
      lineHeight: "1.75",
      color: "#374151"
    }}>
      <p style={{ marginBottom: "2rem" }}>
        Dublin's property market varies dramatically by postcode, with prices ranging from €250,000
        to over €1 million depending on location. This comprehensive guide breaks down property
        prices across all Dublin postcodes to help you understand the market in 2026.
      </p>

      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Most Expensive Dublin Postcodes
      </h2>

      <p style={{ marginBottom: "1rem" }}>
        Based on median property prices from 2024-2026 sales:
      </p>

      <ol style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "decimal"
      }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Dublin 4</strong> - €780,000 median
          <span style={{ display: "block", color: "#6b7280", fontSize: "1rem", marginTop: "0.25rem" }}>
            (Ballsbridge, Donnybrook, Sandymount)
          </span>
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Dublin 6</strong> - €685,000 median
          <span style={{ display: "block", color: "#6b7280", fontSize: "1rem", marginTop: "0.25rem" }}>
            (Ranelagh, Rathmines, Milltown)
          </span>
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Dublin 6W</strong> - €650,000 median
          <span style={{ display: "block", color: "#6b7280", fontSize: "1rem", marginTop: "0.25rem" }}>
            (Terenure, Templeogue)
          </span>
        </li>
      </ol>

      <p style={{ marginBottom: "2rem", fontStyle: "italic", color: "#6b7280" }}>
        Full article content coming soon with detailed breakdowns for all 24 Dublin postcodes.
      </p>

      <div style={{
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "0.5rem",
        padding: "1.5rem",
        marginTop: "2rem"
      }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Explore now:</strong> View property prices for{" "}
          <Link to="/county/dublin" style={{ color: "#3b82f6", textDecoration: "underline" }}>
            all Dublin postcodes
          </Link>
          {" "}on our interactive map.
        </p>
      </div>
    </div>
  );
}
