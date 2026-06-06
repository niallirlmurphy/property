import { Link } from "react-router-dom";

export function HowToUsePPRContent() {
  return (
    <div style={{
      fontSize: "1.125rem",
      lineHeight: "1.75",
      color: "#374151"
    }}>
      {/* Introduction */}
      <p style={{ marginBottom: "1.5rem" }}>
        Ireland's <strong>Property Price Register (PPR)</strong> is a public database of all residential
        property sales in Ireland since January 2010. Whether you're buying your first home, selling a property,
        or just curious about local property values, the PPR is an invaluable free resource.
      </p>

      <p style={{ marginBottom: "2rem" }}>
        This guide will show you how to search the PPR effectively using both the official government website
        and modern tools like <Link to="/" style={{ color: "#3b82f6" }}>HomeIQ.ie</Link>.
      </p>

      {/* What is PPR */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        What is the Property Price Register?
      </h2>

      <p style={{ marginBottom: "1rem" }}>
        The PPR contains details of <strong>all residential property sales</strong> in Ireland, including:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li style={{ marginBottom: "0.5rem" }}>Sale date</li>
        <li style={{ marginBottom: "0.5rem" }}>Full property address</li>
        <li style={{ marginBottom: "0.5rem" }}>Sale price (in euros)</li>
        <li style={{ marginBottom: "0.5rem" }}>Whether the sale was at full market price</li>
        <li style={{ marginBottom: "0.5rem" }}>Whether VAT was excluded</li>
        <li style={{ marginBottom: "0.5rem" }}>Property description (new/second-hand)</li>
        <li style={{ marginBottom: "0.5rem" }}>Property size (if available)</li>
      </ul>

      <div style={{
        backgroundColor: "#fef3c7",
        border: "1px solid #fbbf24",
        borderRadius: "0.5rem",
        padding: "1rem",
        marginBottom: "2rem"
      }}>
        <p style={{ fontSize: "1rem", color: "#78350f", margin: 0 }}>
          <strong>Important:</strong> The PPR is updated twice monthly (around the 1st and 15th of each month)
          with recent sales. There's typically a 1-2 week delay between a sale completing and appearing in the register.
        </p>
      </div>

      {/* How to search */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        How to Search the PPR
      </h2>

      <h3 style={{
        fontSize: "1.5rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Method 1: Official PPR Website
      </h3>

      <p style={{ marginBottom: "1rem" }}>
        Visit <a href="https://www.propertypriceregister.ie" target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6" }}>propertypriceregister.ie</a>
        and use the search form:
      </p>

      <ol style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "decimal"
      }}>
        <li style={{ marginBottom: "1rem" }}>
          <strong>Enter an address</strong> - Type the property address or area
        </li>
        <li style={{ marginBottom: "1rem" }}>
          <strong>Select date range</strong> - Choose the time period (default is last 12 months)
        </li>
        <li style={{ marginBottom: "1rem" }}>
          <strong>Filter options</strong> - Refine by price range, property type, or county
        </li>
        <li style={{ marginBottom: "1rem" }}>
          <strong>Search</strong> - Click the search button to view results
        </li>
      </ol>

      <p style={{ marginBottom: "2rem", fontStyle: "italic", color: "#6b7280" }}>
        Note: The official website can be slow and doesn't show properties on a map.
      </p>

      <h3 style={{
        fontSize: "1.5rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Method 2: HomeIQ.ie (Recommended)
      </h3>

      <p style={{ marginBottom: "1rem" }}>
        <Link to="/" style={{ color: "#3b82f6", fontWeight: "500" }}>HomeIQ.ie</Link> provides
        a modern, map-based interface to search the same PPR data:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>Interactive maps</strong> - See properties on a map with radius search
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>85% geocoded</strong> - Most properties have accurate coordinates
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>Price trends charts</strong> - Visualize price changes over time
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>Eircode search</strong> - Find properties by postcode
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>Fast search</strong> - Instant results, no waiting
        </li>
      </ul>

      {/* Search tips */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Search Tips & Tricks
      </h2>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        1. Be Flexible with Addresses
      </h3>

      <p style={{ marginBottom: "1.5rem" }}>
        Try different variations:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li>"5 Main Street" vs "5 Main St"</li>
        <li>"Ballsbridge" vs "Ballsbridge, Dublin 4"</li>
        <li>"Apartment 3" vs "Apt 3" vs "Unit 3"</li>
      </ul>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        2. Use Radius Search
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        On <Link to="/" style={{ color: "#3b82f6" }}>HomeIQ</Link>, search for an address and
        adjust the radius to see all nearby sales. Great for understanding area pricing.
      </p>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        3. Check "Not Full Market Price"
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        Some sales are marked as "Not full market price" - these include:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li>Family transfers</li>
        <li>Divorce settlements</li>
        <li>Distressed sales</li>
        <li>Sales with unusual circumstances</li>
      </ul>

      <p style={{ marginBottom: "2rem" }}>
        Filter these out when researching typical market prices.
      </p>

      {/* What PPR doesn't show */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        What the PPR Doesn't Show
      </h2>

      <p style={{ marginBottom: "1rem" }}>
        The PPR has limitations:
      </p>

      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>No photos</strong> - You won't see what the property looks like
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>No bedroom count</strong> - Property size details are limited
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>No condition info</strong> - Was it renovated? Original condition?
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>No rental properties</strong> - Only covers sales, not rentals
        </li>
        <li style={{ marginBottom: "0.5rem" }}>
          <strong>No asking prices</strong> - Only shows final sale price
        </li>
      </ul>

      {/* Use cases */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Common Use Cases
      </h2>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Buying a Property
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        Research recent sales in the area before making an offer. See what similar properties
        sold for in the last 6-12 months to gauge fair market value.
      </p>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Selling a Property
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        Set a realistic asking price by checking comparable sales on your street and surrounding area.
      </p>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Market Research
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        Track price trends over time. Are prices rising or falling in your target area?
        Use the <Link to="/" style={{ color: "#3b82f6" }}>trends charts on HomeIQ</Link> to visualize this.
      </p>

      <h3 style={{
        fontSize: "1.25rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Property Valuation
      </h3>

      <p style={{ marginBottom: "2rem" }}>
        Estimate your property's current value based on recent comparable sales in the neighborhood.
      </p>

      {/* Conclusion */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Start Searching Today
      </h2>

      <p style={{ marginBottom: "2rem" }}>
        The Property Price Register is a powerful tool for anyone interested in Irish property prices.
        Whether you use the official website or a modern tool like HomeIQ, you now have the knowledge
        to search effectively and make informed property decisions.
      </p>

      <div style={{
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "0.5rem",
        padding: "1.5rem",
        marginTop: "2rem"
      }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Try it now:</strong> Search 785,000 Irish property sales on our{" "}
          <Link to="/" style={{ color: "#3b82f6", textDecoration: "underline" }}>
            interactive map
          </Link>
          . Free, fast, and easy to use.
        </p>
      </div>
    </div>
  );
}
