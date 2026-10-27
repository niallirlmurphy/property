import { Link } from "react-router-dom";
import type { CsoRollingFigures, CsoSlice } from "../types";

// Official CSO figures shown beside our PPR figures on county, area and Eircode
// pages. Data is baked at build time by the route loaders (data/cso.json).

export const CSO_POST = "/blog/property-price-register-vs-cso-house-prices";

const price = (n: number | null | undefined) => (n == null ? "—" : "€" + Math.round(n).toLocaleString("en-IE"));
const count = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString("en-IE"));

function change(f: CsoRollingFigures) {
  if (!f.median_12m || !f.median_12m_prev) return "—";
  const pct = (f.median_12m / f.median_12m_prev - 1) * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

// "Dublin - houses" -> "houses in Dublin"; "Mid-East - houses" -> "houses in the Mid-East region".
function rppiLabel(label: string) {
  const [place, what] = label.split(" - ");
  const where = place === "National" ? "nationally" : place === "Dublin" ? "in Dublin" : `in the ${place} region`;
  return `${what === "all residential properties" ? "all homes" : what} ${where}`;
}

const pctText = (v: number | null) => (v == null ? "n/a" : `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`);

interface Props {
  cso: CsoSlice;
  place: string;          // e.g. "County Cork", "Monkstown"
  areaNote?: boolean;     // routing keys cover more than the page's search radius
}

export default function CsoFigures({ cso, place, areaNote }: Props) {
  const regions = cso.regions ?? [];
  const keys = cso.routing_keys ?? [];
  if (!regions.length && !keys.length) return null;
  const period = `12 months to ${cso.latest_month}`;

  return (
    <section className="content-section">
      <h2>Official CSO Figures for {place}</h2>
      <p>
        The Central Statistics Office publishes its own property price statistics from the same stamp duty
        returns as the Property Price Register. It counts only market-price purchases by households, and
        its new-home prices include VAT. <Link to={CSO_POST}>Why the two sets of figures differ</Link>.
      </p>

      {cso.rppi && cso.rppi.length > 0 && (
        <p>
          The CSO's mix-adjusted Residential Property Price Index for{" "}
          {cso.rppi.map((r, i) => (
            <span key={r.label}>
              {i > 0 && (i === cso.rppi!.length - 1 ? " and " : ", ")}
              {rppiLabel(r.label)} changed <strong>{pctText(r.change_12m)}</strong>
            </span>
          ))}{" "}
          in the 12 months to {cso.rppi_month}.
        </p>
      )}

      {regions.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table className="sales-table">
            <thead>
              <tr>
                <th>Area</th><th>Median ({period})</th><th>Change on year before</th><th>Sales</th>
                <th>Houses ({cso.annual_year})</th><th>Apartments ({cso.annual_year})</th>
              </tr>
            </thead>
            <tbody>
              {regions.map(r => (
                <tr key={r.name}>
                  <td>{r.name}</td>
                  <td>{price(r.median_12m)}</td>
                  <td>{change(r)}</td>
                  <td>{count(r.volume_12m)}</td>
                  <td>{price(r.house?.median)}</td>
                  <td>{price(r.apartment?.median)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {keys.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table className="sales-table">
            <thead>
              <tr>
                <th>Eircode area</th><th>Median ({period})</th><th>Change on year before</th>
                <th>Second-hand</th><th>New (incl. VAT)</th><th>Sales</th>
              </tr>
            </thead>
            <tbody>
              {keys.map(k => (
                <tr key={k.key}>
                  <td>{k.key} {k.name}</td>
                  <td>{price(k.median_12m)}</td>
                  <td>{change(k)}</td>
                  <td>{price(k.existing_12m)}</td>
                  <td>{price(k.new_12m)}</td>
                  <td>{count(k.volume_12m)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="table-note">
        {areaNote && "CSO figures cover the whole Eircode routing area, which is larger than this page's search area. "}
        Source: <a href={cso.source_url} target="_blank" rel="noopener noreferrer">Central Statistics Office</a>,
        Residential Property Price Index, licensed under CC BY 4.0. Market-based household purchases by date of
        sale; the latest months are revised as late returns are filed.
      </p>
    </section>
  );
}
