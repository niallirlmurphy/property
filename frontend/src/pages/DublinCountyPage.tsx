import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";

function formatPrice(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

interface PostcodeRow {
  postcode: string;
  label: string;
  txCount: number;
  medianPrice: number;
  avgPrice: number;
}

// 2025 data from PPR (full market price sales only, Jan–May 2025)
const POSTCODE_DATA: PostcodeRow[] = [
  { postcode: "D01", label: "Dublin 1",   txCount:  338, medianPrice:  350500, avgPrice:  818708 },
  { postcode: "D02", label: "Dublin 2",   txCount:  257, medianPrice:  460000, avgPrice:  585432 },
  { postcode: "D03", label: "Dublin 3",   txCount:  587, medianPrice:  541850, avgPrice:  635433 },
  { postcode: "D04", label: "Dublin 4",   txCount:  760, medianPrice:  669802, avgPrice:  931739 },
  { postcode: "D05", label: "Dublin 5",   txCount:  586, medianPrice:  495000, avgPrice:  538130 },
  { postcode: "D06", label: "Dublin 6",   txCount:  475, medianPrice:  760000, avgPrice: 1003945 },
  { postcode: "D6W", label: "Dublin 6W",  txCount:  284, medianPrice:  709000, avgPrice:  800305 },
  { postcode: "D07", label: "Dublin 7",   txCount:  623, medianPrice:  475000, avgPrice:  548895 },
  { postcode: "D08", label: "Dublin 8",   txCount:  653, medianPrice:  419000, avgPrice:  668353 },
  { postcode: "D09", label: "Dublin 9",   txCount:  630, medianPrice:  494000, avgPrice:  571475 },
  { postcode: "D10", label: "Dublin 10",  txCount:  166, medianPrice:  327000, avgPrice:  612152 },
  { postcode: "D11", label: "Dublin 11",  txCount:  537, medianPrice:  350000, avgPrice:  397342 },
  { postcode: "D12", label: "Dublin 12",  txCount:  605, medianPrice:  465000, avgPrice:  479403 },
  { postcode: "D13", label: "Dublin 13",  txCount:  698, medianPrice:  528302, avgPrice:  626991 },
  { postcode: "D14", label: "Dublin 14",  txCount:  558, medianPrice:  732139, avgPrice:  825696 },
  { postcode: "D15", label: "Dublin 15",  txCount: 1515, medianPrice:  436123, avgPrice:  475027 },
  { postcode: "D16", label: "Dublin 16",  txCount:  534, medianPrice:  640000, avgPrice:  664638 },
  { postcode: "D17", label: "Dublin 17",  txCount:  180, medianPrice:  350000, avgPrice:  495752 },
  { postcode: "D18", label: "Dublin 18",  txCount: 1046, medianPrice:  612335, avgPrice:  694336 },
  { postcode: "D20", label: "Dublin 20",  txCount:  111, medianPrice:  436298, avgPrice:  461029 },
  { postcode: "D22", label: "Dublin 22",  txCount:  673, medianPrice:  400000, avgPrice:  559365 },
  { postcode: "D24", label: "Dublin 24",  txCount:  929, medianPrice:  389000, avgPrice:  420481 },
];

const TOTAL_TX = POSTCODE_DATA.reduce((s, r) => s + r.txCount, 0);
const ALL_MEDIANS = POSTCODE_DATA.map(r => r.medianPrice);
const OVERALL_MEDIAN = ALL_MEDIANS.sort((a, b) => a - b)[Math.floor(ALL_MEDIANS.length / 2)];
const MOST_EXPENSIVE = [...POSTCODE_DATA].sort((a, b) => b.medianPrice - a.medianPrice)[0];
const MOST_AFFORDABLE = [...POSTCODE_DATA].sort((a, b) => a.medianPrice - b.medianPrice)[0];
const MOST_ACTIVE = [...POSTCODE_DATA].sort((a, b) => b.txCount - a.txCount)[0];

export default function DublinCountyPage() {
  return (
    <>
      <PageHeader title="Property Prices in County Dublin" />
      <div className="content-page">
      <p className="content-intro">
        Explore residential property sale prices across Dublin from Ireland's Property Price Register.
        Every sale since 2010 is included. Postcode breakdown figures are for 2025 full market price sales.
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Median price (2025)</span>
          <strong>{formatPrice(OVERALL_MEDIAN)}</strong>
        </div>
        <div className="stat-card">
          <span>2025 transactions</span>
          <strong>{TOTAL_TX.toLocaleString()}</strong>
        </div>
        <div className="stat-card">
          <span>Most expensive postcode</span>
          <strong>{MOST_EXPENSIVE.label} · {formatPrice(MOST_EXPENSIVE.medianPrice)}</strong>
        </div>
        <div className="stat-card">
          <span>Most affordable postcode</span>
          <strong>{MOST_AFFORDABLE.label} · {formatPrice(MOST_AFFORDABLE.medianPrice)}</strong>
        </div>
      </div>

      <section className="content-section">
        <h2>2025 Dublin Postcode Breakdown</h2>
        <p>
          Median and average sale prices by Dublin postcode for 2025, based on full market price
          sales recorded in the Property Price Register. The most active area was{" "}
          <strong>{MOST_ACTIVE.label}</strong> with {MOST_ACTIVE.txCount.toLocaleString()} transactions.
        </p>
        <div className="postcode-table-wrap">
          <table className="postcode-table">
            <thead>
              <tr>
                <th>Postcode</th>
                <th>Area</th>
                <th className="num-col">Transactions</th>
                <th className="num-col">Median price</th>
                <th className="num-col">Average price</th>
              </tr>
            </thead>
            <tbody>
              {POSTCODE_DATA.map(row => (
                <tr key={row.postcode}>
                  <td><span className="postcode-badge">{row.postcode}</span></td>
                  <td>{row.label}</td>
                  <td className="num-col">{row.txCount.toLocaleString()}</td>
                  <td className="num-col median-col">{formatPrice(row.medianPrice)}</td>
                  <td className="num-col">{formatPrice(row.avgPrice)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="table-note">
          Data source: Property Price Register 2025. Full market price sales only. Last updated May 2025.
        </p>
      </section>

      <section className="content-section">
        <h2>How Have Dublin Prices Changed?</h2>
        <p>
          Dublin property prices have risen significantly since 2010 when the Property Price Register began.
          The most expensive areas remain Dublin 4, Dublin 6, and Dublin 14 — traditional premium southside
          postcodes — while Dublin 11, Dublin 24, and Dublin 10 remain the most affordable.
        </p>
        <p>
          Dublin 15 and Dublin 18 are the highest-volume markets, reflecting large residential developments
          in Blanchardstown and Sandyford/Foxrock.
        </p>
      </section>

      <section className="content-section">
        <h2>Search Dublin Properties</h2>
        <p>
          Use the <Link to="/?county=Dublin">interactive map</Link> to search by address or
          Eircode within County Dublin, or explore a specific{" "}
          <Link to="/area/rathmines">Dublin neighbourhood</Link>.
        </p>
      </section>
    </div>
    </>
  );
}
