import { Link } from "react-router-dom";

// Prompt on landing pages (county, area, Eircode, street) to value a home there.
export default function ValuationCta({ place }: { place: string }) {
  return (
    <section className="valuation-cta">
      <div>
        <h2>What's your home in {place} worth?</h2>
        <p>
          A free instant estimate from comparable sales on the Property Price Register, with the
          comparables shown.
        </p>
      </div>
      <Link to="/valuation" className="valuation-cta-btn">Value my property</Link>
    </section>
  );
}
