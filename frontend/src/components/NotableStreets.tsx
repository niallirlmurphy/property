import { Link } from "react-router-dom";
import { streetsForCounty } from "../streets";

/**
 * Renders the "Notable Streets in {county}" internal-links section.
 * Returns null when the county has no notable streets, so it is safe to
 * drop into any county render path. County display name is derived from
 * the matched street configs (all share the same county).
 */
export default function NotableStreets({ countySlug }: { countySlug: string }) {
  const streets = streetsForCounty(countySlug);
  if (streets.length === 0) return null;
  const countyName = streets[0].county;
  return (
    <section className="content-section">
      <h2>Notable Streets in {countyName}</h2>
      <ul className="street-links">
        {streets.map(s => (
          <li key={s.slug}>
            <Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link>
          </li>
        ))}
      </ul>
      <p><Link to="/streets">Browse all notable streets in Ireland →</Link></p>
    </section>
  );
}
