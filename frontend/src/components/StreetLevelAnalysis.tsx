import { Link } from "react-router-dom";
import { streetsForCounty } from "../streets";

/**
 * Renders the "Street Level Analysis in {county}" internal-links section.
 * Returns null when the county has no covered streets, so it is safe to
 * drop into any county render path. County display name is derived from
 * the matched street configs (all share the same county).
 */
export default function StreetLevelAnalysis({ countySlug }: { countySlug: string }) {
  const streets = streetsForCounty(countySlug);
  if (streets.length === 0) return null;
  const countyName = streets[0].county;
  return (
    <section className="content-section">
      <h2>Street Level Analysis in {countyName}</h2>
      <p className="street-links-intro">
        Dedicated price guides for {streets.length} notable {countyName} street{streets.length === 1 ? "" : "s"} —
        median prices, yearly trends and recent sales from the Property Price Register.
      </p>
      <div className="street-links-grid">
        {streets.map(s => (
          <Link key={s.slug} to={`/street/${s.slug}`} className="street-link-card">
            <span className="street-link-name">{s.name}</span>
            <span className="street-link-area">{s.area}</span>
          </Link>
        ))}
      </div>
      <p><Link to="/streets">Browse street level analysis for all Ireland →</Link></p>
    </section>
  );
}
