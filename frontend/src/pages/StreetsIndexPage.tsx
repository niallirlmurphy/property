// frontend/src/pages/StreetsIndexPage.tsx
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import { STREETS } from "../streets";

export default function StreetsIndexPage() {
  const crumbs = [{ name: "Street Level Analysis", url: "/streets" }];
  const meta = usePageMeta(
    "Street Level Property Price Analysis in Ireland",
    "Street-level property price analysis for Ireland's highest-value and most active streets, based on the Property Price Register.",
    crumbs,
  );
  const value = STREETS.filter(s => s.category === "value").sort((a, b) => a.rank - b.rank);
  const volume = STREETS.filter(s => s.category === "volume").sort((a, b) => a.rank - b.rank);

  const list = (items: typeof STREETS) => (
    <ul className="street-index-list">
      {items.map(s => (
        <li key={s.slug}>
          <Link to={`/street/${s.slug}`}>{s.name}, {s.area}</Link>
          <span className="street-index-county"> · Co. {s.county}</span>
        </li>
      ))}
    </ul>
  );

  return (
    <>
      {meta}
      <PageHeader title="Street Level Analysis" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Street Level Analysis</h1>
        <p className="content-intro">
          Street-level property price analysis for Ireland's highest-value and most active
          streets, drawn from the Property Price Register (2010 onwards).
        </p>
        <section className="content-section">
          <h2>Highest-value streets</h2>
          {list(value)}
        </section>
        <section className="content-section">
          <h2>Most active streets</h2>
          {list(volume)}
        </section>
        <Footer />
      </div>
    </>
  );
}
