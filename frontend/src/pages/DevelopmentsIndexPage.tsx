import { Link, useLoaderData } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import type { DevelopmentIndexEntry } from "../routeLoaders";

export default function DevelopmentsIndexPage() {
  const developments = (useLoaderData() as DevelopmentIndexEntry[] | null) ?? [];
  const crumbs = [{ name: "Developments", url: "/developments" }];
  const meta = usePageMeta(
    "Property Prices in Dublin Apartment and Housing Developments",
    "Sold prices, price trends, bedroom breakdowns, schools and transport for named Dublin developments, from the Property Price Register.",
    crumbs,
  );

  return (
    <>
      {meta}
      <PageHeader title="Developments" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Property Prices by Development</h1>
        <p className="content-intro">
          Price guides for named apartment and housing developments, built from every sale
          recorded in each scheme on the Property Price Register, with nearby schools and
          transport links.
        </p>
        <section className="content-section">
          <ul className="street-index-list">
            {developments.map(d => (
              <li key={d.slug}>
                <Link to={`/development/${d.slug}`}>{d.name}, {d.area}</Link>
                <p>{d.description}</p>
              </li>
            ))}
          </ul>
        </section>
        <Footer />
      </div>
    </>
  );
}
