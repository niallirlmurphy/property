import { Link } from "react-router-dom";

export function EircodeGuideContent() {
  return (
    <div style={{
      fontSize: "1.125rem",
      lineHeight: "1.75",
      color: "#374151"
    }}>
      <p style={{ marginBottom: "2rem" }}>
        Eircode is Ireland's postcode system, introduced in 2015. Understanding how Eircodes work
        can help you search for property prices more effectively and understand geographic patterns
        in the property market.
      </p>

      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        What is an Eircode?
      </h2>

      <p style={{ marginBottom: "1rem" }}>
        An Eircode is a unique 7-character postcode assigned to every address in Ireland. For example:
      </p>

      <div style={{
        backgroundColor: "#f3f4f6",
        padding: "1rem",
        borderRadius: "0.375rem",
        fontFamily: "monospace",
        marginBottom: "2rem",
        fontSize: "1.25rem",
        textAlign: "center"
      }}>
        D02 XY45
      </div>

      <p style={{ marginBottom: "2rem" }}>
        The code has two parts:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Routing Key (D02)</strong> - The first 3 characters identify a geographic area
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Unique Identifier (XY45)</strong> - The last 4 characters identify a specific address
        </li>
      </ul>

      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Routing Keys for Property Search
      </h2>

      <p style={{ marginBottom: "2rem" }}>
        The <strong>routing key</strong> (first 3 characters) is most useful for property searches
        because it represents a geographic area containing approximately 15,000 addresses.
      </p>

      <p style={{ marginBottom: "2rem", fontStyle: "italic", color: "#6b7280" }}>
        Full article content coming soon with examples and search tips.
      </p>

      <div style={{
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "0.5rem",
        padding: "1.5rem",
        marginTop: "2rem"
      }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Try it now:</strong> Search by Eircode on our{" "}
          <Link to="/" style={{ color: "#3b82f6", textDecoration: "underline" }}>
            homepage
          </Link>
          {" "}(e.g., D02, H91, V94).
        </p>
      </div>
    </div>
  );
}
