import { Link } from "react-router-dom";
import HeatmapBody from "../components/HeatmapBody";

// The interactive price-growth map (formerly a standalone menu item at /heatmap)
// as a post. Figures load from /data/heatmap.json, regenerated after each PPR
// sync by scripts/generate_heatmap_data.py, so the prose here stays figure-free.

const INK = "#374151";
const link = { color: "#1d4ed8", fontWeight: 600 } as const;

export function HousePriceGrowthMapContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Irish house prices have risen almost everywhere in recent years, so the useful question is no longer
        <em> whether</em> prices went up in an area, but <em>by how much compared with everywhere else</em>. This map
        answers that for the whole country, using every second-hand sale on the Property Price Register.
      </p>

      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "2rem 0 0.75rem" }}>How to read the map</h2>
      <p style={{ marginBottom: "1rem" }}>
        Ireland is divided into squares roughly 4&nbsp;km across. Each square is coloured by how much its median resale
        price changed between two periods: red squares grew faster than the national picture, blue squares grew more
        slowly or fell. Hover or tap a square for its figures, and zoom in to compare neighbouring areas. Below the map,
        named localities are ranked from fastest- to slowest-growing.
      </p>
      <p style={{ marginBottom: "1.5rem" }}>
        Only resale homes are counted, and areas need enough sales in both periods to appear, so a new estate
        completing or a handful of unusual sales can't make an area look hotter or cooler than it is. The full method
        is set out after the tables.
      </p>

      <HeatmapBody />

      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "2rem 0 0.75rem" }}>Go deeper on an area</h2>
      <p style={{ marginBottom: "1.5rem" }}>
        Spotted an area worth a closer look? Our <Link to="/areaguides" style={link}>area guides</Link> show median
        prices, sales volumes and recent sales for towns, Dublin postcodes and counties, and the{" "}
        <Link to="/valuation" style={link}>valuation tool</Link> estimates what a specific home is worth today.
      </p>
    </div>
  );
}
