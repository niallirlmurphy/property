import { useState } from "react";
import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, Cell, PieChart, Pie,
} from "recharts";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";

// ---------------------------------------------------------------------------
// Data — sourced from SEAI BER Public Search dataset (1,403,166 assessments)
// ---------------------------------------------------------------------------

const RATING_COLOURS: Record<string, string> = {
  A1: "#1a6b2e", A2: "#2d9e47", A3: "#56bc6d",
  B1: "#8fcf3a", B2: "#b5e33a", B3: "#d4ed35",
  C1: "#f5e835", C2: "#f5c935", C3: "#f5a935",
  D1: "#f57c35", D2: "#f55535",
  E1: "#d63020", E2: "#b01818",
  F: "#8a1010", G: "#5c0808",
};

const RATINGS = ["A1","A2","A3","B1","B2","B3","C1","C2","C3","D1","D2","E1","E2","F","G"];

// Overall national distribution
const OVERALL_DIST = [
  { rating: "A1", count: 20987,  pct: 1.5 },
  { rating: "A2", count: 172226, pct: 12.3 },
  { rating: "A3", count: 90091,  pct: 6.4 },
  { rating: "B1", count: 44524,  pct: 3.2 },
  { rating: "B2", count: 70478,  pct: 5.0 },
  { rating: "B3", count: 124262, pct: 8.9 },
  { rating: "C1", count: 143176, pct: 10.2 },
  { rating: "C2", count: 146734, pct: 10.5 },
  { rating: "C3", count: 132554, pct: 9.4 },
  { rating: "D1", count: 123032, pct: 8.8 },
  { rating: "D2", count: 104364, pct: 7.4 },
  { rating: "E1", count: 60485,  pct: 4.3 },
  { rating: "E2", count: 47469,  pct: 3.4 },
  { rating: "F",  count: 49089,  pct: 3.5 },
  { rating: "G",  count: 73695,  pct: 5.3 },
];

// A/B rate trend over time
const AB_TREND = [
  { year: 2009, abPct: 21.7, upgradedPct: 5.3 },
  { year: 2010, abPct: 13.5, upgradedPct: 36.8 },
  { year: 2011, abPct: 9.5,  upgradedPct: 53.6 },
  { year: 2012, abPct: 11.5, upgradedPct: 34.6 },
  { year: 2013, abPct: 11.3, upgradedPct: 14.8 },
  { year: 2014, abPct: 11.7, upgradedPct: 10.2 },
  { year: 2015, abPct: 14.4, upgradedPct: 15.0 },
  { year: 2016, abPct: 18.9, upgradedPct: 18.1 },
  { year: 2017, abPct: 25.9, upgradedPct: 16.2 },
  { year: 2018, abPct: 30.5, upgradedPct: 17.8 },
  { year: 2019, abPct: 37.1, upgradedPct: 20.1 },
  { year: 2020, abPct: 43.6, upgradedPct: 16.7 },
  { year: 2021, abPct: 46.2, upgradedPct: 11.8 },
  { year: 2022, abPct: 52.1, upgradedPct: 15.2 },
  { year: 2023, abPct: 56.6, upgradedPct: 18.4 },
  { year: 2024, abPct: 55.8, upgradedPct: 17.2 },
  { year: 2025, abPct: 56.1, upgradedPct: 16.0 },
];

// Rating by age band (A/B %, D-G %, avg kWh/m²/yr)
const BY_AGE = [
  { band: "Pre-1900",  n: 36495,  ab: 9.1,  dg: 78.2, avgBer: 401 },
  { band: "1900–29",   n: 76740,  ab: 9.9,  dg: 77.0, avgBer: 398 },
  { band: "1930–49",   n: 63059,  ab: 13.0, dg: 67.3, avgBer: 338 },
  { band: "1950–69",   n: 116165, ab: 15.1, dg: 62.8, avgBer: 295 },
  { band: "1970–79",   n: 137614, ab: 15.6, dg: 53.8, avgBer: 253 },
  { band: "1980–89",   n: 123272, ab: 17.6, dg: 44.0, avgBer: 224 },
  { band: "1990–99",   n: 179357, ab: 21.0, dg: 35.9, avgBer: 209 },
  { band: "2000–05",   n: 268316, ab: 28.2, dg: 18.3, avgBer: 183 },
  { band: "2006–10",   n: 152160, ab: 53.0, dg: 8.6,  avgBer: 153 },
  { band: "2011–15",   n: 19419,  ab: 96.0, dg: 1.0,  avgBer: 79  },
  { band: "2016+",     n: 230569, ab: 99.8, dg: 0.0,  avgBer: 43  },
];

// Rating distribution by dwelling type (top 5 types, grouped A/B/C/D/E-G)
const BY_DWELLING = [
  {
    type: "Detached",
    label: "Detached house",
    n: 427418,
    ab: 20.1, c: 28.6, d: 16.1, eg: 15.2,
    distribution: { A1:2.2,A2:6.8,A3:6.0,B1:5.1,B2:6.7,B3:9.6,C1:9.4,C2:9.6,C3:9.2,D1:8.6,D2:7.5,E1:4.3,E2:3.4,F:3.9,G:7.7 }
  },
  {
    type: "Semi-D",
    label: "Semi-detached house",
    n: 372959,
    ab: 20.1, c: 30.3, d: 16.4, eg: 9.0,
    distribution: { A1:1.4,A2:12.9,A3:7.5,B1:2.8,B2:3.8,B3:8.2,C1:11.1,C2:12.2,C3:10.8,D1:9.3,D2:7.1,E1:4.0,E2:3.1,F:3.0,G:2.8 }
  },
  {
    type: "Mid-terrace",
    label: "Mid-terrace house",
    n: 190588,
    ab: 18.3, c: 28.2, d: 16.5, eg: 14.8,
    distribution: { A1:1.5,A2:11.7,A3:5.6,B1:1.9,B2:4.4,B3:9.4,C1:11.1,C2:10.3,C3:8.7,D1:8.6,D2:7.9,E1:5.2,E2:4.2,F:4.3,G:5.3 }
  },
  {
    type: "End of terrace",
    label: "End of terrace house",
    n: 106851,
    ab: 25.7, c: 24.6, d: 15.9, eg: 14.3,
    distribution: { A1:2.0,A2:15.8,A3:7.9,B1:2.3,B2:2.8,B3:6.4,C1:9.2,C2:10.2,C3:9.0,D1:8.4,D2:7.5,E1:4.6,E2:4.0,F:4.4,G:5.4 }
  },
  {
    type: "Apartment",
    label: "Mid-floor apartment",
    n: 106390,
    ab: 34.9, c: 26.7, d: 10.3, eg: 4.9,
    distribution: { A1:0.8,A2:29.0,A3:5.0,B1:3.0,B2:7.9,B3:10.6,C1:10.2,C2:8.9,C3:7.0,D1:6.0,D2:4.3,E1:2.3,E2:1.6,F:1.4,G:1.9 }
  },
];

// County A/B rates (top 10 and bottom 10 combined, for a ranked bar chart)
const COUNTY_RANKINGS = [
  { county: "Dublin 18",   ab: 70.3, n: 21388 },
  { county: "Dublin 13",   ab: 50.8, n: 13212 },
  { county: "Co. Meath",   ab: 50.5, n: 57129 },
  { county: "Co. Kildare", ab: 50.4, n: 67472 },
  { county: "Co. Dublin",  ab: 50.2, n: 111516 },
  { county: "Dublin 15",   ab: 47.5, n: 32898 },
  { county: "Co. Wicklow", ab: 46.4, n: 45779 },
  { county: "Dublin 20",   ab: 44.9, n: 4062 },
  { county: "Dublin 22",   ab: 42.8, n: 14186 },
  { county: "Dublin 16",   ab: 42.5, n: 13749 },
  // bottom
  { county: "Dublin 12",   ab: 27.2, n: 16511 },
  { county: "Dublin 3",    ab: 25.7, n: 12201 },
  { county: "Co. Mayo",    ab: 25.2, n: 36889 },
  { county: "Co. Donegal", ab: 25.0, n: 42303 },
  { county: "Co. Roscommon", ab: 25.0, n: 16816 },
  { county: "Dublin 5",    ab: 24.4, n: 12751 },
  { county: "Co. Leitrim", ab: 23.4, n: 10398 },
  { county: "Dublin 6",    ab: 22.1, n: 11463 },
  { county: "Cork City",   ab: 21.0, n: 20092 },
  { county: "Dublin 7",    ab: 18.8, n: 16738 },
].sort((a, b) => b.ab - a.ab);

// Home improvements (among 260,603 HES-grant upgraded homes)
const IMPROVEMENTS = [
  { name: "Attic / roof insulation",      count: 251551, pct: 96.5 },
  { name: "Cavity wall insulation",        count: 35750,  pct: 13.7 },
  { name: "High-performance windows",      count: 20129,  pct: 7.7  },
  { name: "Solar hot water",               count: 12204,  pct: 4.7  },
  { name: "Underfloor heating (all homes)",count: 82085,  pct: 5.8, note: "all" },
  { name: "External wall insulation",      count: 3159,   pct: 1.2  },
];

// Heating fuel breakdown
const HEATING_FUEL = [
  { fuel: "Mains Gas",    pct: 33.6, count: 470882 },
  { fuel: "Heating Oil",  pct: 33.1, count: 464610 },
  { fuel: "Electricity",  pct: 26.8, count: 376043 },
  { fuel: "Solid fuel",   pct: 2.4,  count: 33863  },
  { fuel: "LPG",          pct: 1.2,  count: 16720  },
  { fuel: "Other",        pct: 2.9,  count: 40048  },
];

const FUEL_COLOURS = ["#1a3c5e","#e07b39","#2d9e47","#888","#b5e33a","#aaa"];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const BerTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="ber-tooltip">
      <div className="ber-tooltip-title">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="ber-tooltip-row">
          <span className="ber-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}</span>
          <strong>{typeof p.value === "number" ? p.value.toFixed(1) + "%" : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

const AgeTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const row = BY_AGE.find(r => r.band === label);
  return (
    <div className="ber-tooltip">
      <div className="ber-tooltip-title">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="ber-tooltip-row">
          <span className="ber-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}</span>
          <strong>{p.value.toFixed(1)}{p.name.includes("kWh") ? " kWh/m²" : "%"}</strong>
        </div>
      ))}
      {row && <div className="ber-tooltip-row"><span>Assessments</span><strong>{row.n.toLocaleString()}</strong></div>}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function EnergyPage() {
  usePageMeta(
    "Home Energy Ratings Ireland — BER Statistics",
    "Explore Building Energy Rating (BER) statistics across Ireland. See how your home's energy efficiency compares and what upgrades make the biggest difference.",
  );
  const [dwellingView, setDwellingView] = useState<"stacked" | "detail">("stacked");
  const selectedDwelling = BY_DWELLING[0]; // for detail view

  const totalAssessments = OVERALL_DIST.reduce((s, r) => s + r.count, 0);
  const totalAB = OVERALL_DIST.filter(r => r.rating[0] <= "B").reduce((s, r) => s + r.count, 0);
  const totalDG = OVERALL_DIST.filter(r => ["D1","D2","E1","E2","F","G"].includes(r.rating)).reduce((s, r) => s + r.count, 0);

  // Stacked bar data: one bar per dwelling type showing A/B/C/D/EFG bands
  const stackedDwellingData = BY_DWELLING.map(d => ({
    type: d.type,
    "A–B": +(d.ab).toFixed(1),
    "C": +(d.c).toFixed(1),
    "D": +(d.d).toFixed(1),
    "E–G": +(d.eg).toFixed(1),
  }));

  // Detail distribution for a single dwelling type
  const detailData = BY_DWELLING.map(d => ({
    type: d.type,
    label: d.label,
    dist: RATINGS.map(r => ({ rating: r, pct: (d.distribution as any)[r] ?? 0 })),
  }));

  const [selectedDwellingIdx, setSelectedDwellingIdx] = useState(0);
  const detailDist = detailData[selectedDwellingIdx].dist;

  return (
    <>
      <PageHeader title="Home Energy Ratings in Ireland" />
      <div className="content-page ber-page">

        <p className="content-intro">
          Ireland's Building Energy Rating (BER) system grades homes from A1 (most efficient) to G (least).
          Based on <strong>{totalAssessments.toLocaleString()}</strong> assessments in the SEAI BER Public
          Search dataset, this page explores how Irish homes rate — and how they're improving.
        </p>

        {/* ── Headline stats ── */}
        <div className="stats-grid">
          <div className="stat-card">
            <span>Total BER assessments</span>
            <strong>{totalAssessments.toLocaleString()}</strong>
          </div>
          <div className="stat-card">
            <span>Rated A or B</span>
            <strong>{(totalAB / totalAssessments * 100).toFixed(1)}%</strong>
          </div>
          <div className="stat-card">
            <span>Rated D, E, F or G</span>
            <strong>{(totalDG / totalAssessments * 100).toFixed(1)}%</strong>
          </div>
          <div className="stat-card">
            <span>Completed upgrades (HES)</span>
            <strong>260,603</strong>
          </div>
        </div>

        {/* ── Overall distribution ── */}
        <section className="content-section">
          <h2>National BER Distribution</h2>
          <p>
            C-rated homes are the most common — the legacy of construction standards in the 1970s–1990s.
            The spike at A2 reflects Ireland's new-build standards since 2016, when nearly all new homes
            must achieve A-rated performance.
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={OVERALL_DIST} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="rating" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} width={42} />
              <Tooltip
                formatter={(v: any, name: any) => [`${v}%`, "Share of homes"]}
                labelFormatter={l => `Rating ${l}`}
              />
              <Bar dataKey="pct" name="Share of homes" radius={[3, 3, 0, 0]}>
                {OVERALL_DIST.map(entry => (
                  <Cell key={entry.rating} fill={RATING_COLOURS[entry.rating]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="ber-callout">
            <strong>56%</strong> of homes assessed in 2024–25 are now A or B rated — up from just{" "}
            <strong>10%</strong> in 2013. Tighter building regulations and retrofit grants are driving this shift.
          </p>
        </section>

        {/* ── Trend over time ── */}
        <section className="content-section">
          <h2>Ireland's Energy Upgrade Journey (2009–2025)</h2>
          <p>
            The share of A/B-rated homes at assessment has risen dramatically — from 22% in 2009 to over
            56% today. The steep rise from 2017 onwards reflects the Near Zero Energy Building (NZEB)
            standard for new homes, combined with the SEAI's Home Energy Scheme grants.
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={AB_TREND} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} width={42} domain={[0, 100]} />
              <Tooltip content={<BerTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="abPct"
                name="A/B rated (%)"
                stroke="#2d9e47"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="upgradedPct"
                name="HES grant upgrades (%)"
                stroke="#e07b39"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 4"
              />
            </LineChart>
          </ResponsiveContainer>
          <p className="ber-note">
            The 2010–2012 spike in HES upgrades reflects the government's post-recession retrofit stimulus.
            Grant support has remained steady at 15–20% of all assessments since 2016.
          </p>
        </section>

        {/* ── Rating by age band ── */}
        <section className="content-section">
          <h2>Older Homes, Lower Ratings</h2>
          <p>
            There is a stark relationship between construction era and energy performance.
            Pre-1900 homes average <strong>401 kWh/m²/year</strong> — nearly 10× the energy
            demand of a modern A-rated home built after 2016 (<strong>43 kWh/m²/year</strong>).
          </p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={BY_AGE} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="band" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" height={60} />
              <YAxis tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} width={42} domain={[0, 100]} />
              <Tooltip content={<AgeTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="ab"  name="A/B rated (%)"  stackId="a" fill="#2d9e47" />
              <Bar dataKey="dg"  name="D–G rated (%)"  stackId="b" fill="#e07b39" />
            </BarChart>
          </ResponsiveContainer>
          <div className="ber-age-table-wrap">
            <table className="ber-age-table">
              <thead>
                <tr>
                  <th>Era</th>
                  <th className="num-col">Homes</th>
                  <th className="num-col">A/B rated</th>
                  <th className="num-col">D–G rated</th>
                  <th className="num-col">Avg kWh/m²</th>
                </tr>
              </thead>
              <tbody>
                {BY_AGE.map(row => (
                  <tr key={row.band}>
                    <td>{row.band}</td>
                    <td className="num-col">{row.n.toLocaleString()}</td>
                    <td className="num-col" style={{ color: "#2d9e47", fontWeight: 600 }}>{row.ab}%</td>
                    <td className="num-col" style={{ color: "#e07b39", fontWeight: 600 }}>{row.dg}%</td>
                    <td className="num-col">{row.avgBer}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Rating by dwelling type ── */}
        <section className="content-section">
          <h2>BER by Dwelling Type</h2>
          <p>
            Apartments rate significantly better than houses — mid-floor apartments benefit from heat
            retention from neighbours on all sides. Detached houses are the hardest to insulate efficiently,
            with the highest proportion of F and G ratings.
          </p>

          <div className="ber-toggle-row">
            <button
              className={dwellingView === "stacked" ? "active" : ""}
              onClick={() => setDwellingView("stacked")}
            >Overview</button>
            <button
              className={dwellingView === "detail" ? "active" : ""}
              onClick={() => setDwellingView("detail")}
            >Full breakdown</button>
          </div>

          {dwellingView === "stacked" && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={stackedDwellingData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} width={42} />
                <Tooltip content={<BerTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="A–B" stackId="a" fill="#2d9e47" />
                <Bar dataKey="C"   stackId="a" fill="#f5c935" />
                <Bar dataKey="D"   stackId="a" fill="#f57c35" />
                <Bar dataKey="E–G" stackId="a" fill="#b01818" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {dwellingView === "detail" && (
            <>
              <div className="ber-dwelling-tabs">
                {BY_DWELLING.map((d, i) => (
                  <button
                    key={d.type}
                    className={selectedDwellingIdx === i ? "active" : ""}
                    onClick={() => setSelectedDwellingIdx(i)}
                  >{d.type}</button>
                ))}
              </div>
              <p className="ber-note">
                {BY_DWELLING[selectedDwellingIdx].label} — {BY_DWELLING[selectedDwellingIdx].n.toLocaleString()} assessments
              </p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={detailData[selectedDwellingIdx].dist} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="rating" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} width={42} />
                  <Tooltip formatter={(v: any) => [`${v}%`, "Share"]} labelFormatter={l => `Rating ${l}`} />
                  <Bar dataKey="pct" name="Share" radius={[3, 3, 0, 0]}>
                    {detailDist.map(entry => (
                      <Cell key={entry.rating} fill={RATING_COLOURS[entry.rating]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          )}
        </section>

        {/* ── Home improvements ── */}
        <section className="content-section">
          <h2>Most Common Home Improvements</h2>
          <p>
            Among the <strong>260,603</strong> homes that completed a SEAI Home Energy Scheme (HES) upgrade,
            attic insulation is by far the most popular measure — present in virtually all retrofit projects.
            Cavity wall insulation is the second most common, followed by window upgrades and solar hot water.
          </p>
          <div className="ber-improvements">
            {[
              { name: "Attic / roof insulation",   count: 251551, pct: 96.5, colour: "#2d9e47" },
              { name: "Cavity wall insulation",      count: 35750,  pct: 13.7, colour: "#56bc6d" },
              { name: "High-performance windows",    count: 20129,  pct: 7.7,  colour: "#8fcf3a" },
              { name: "Solar hot water",             count: 12204,  pct: 4.7,  colour: "#f5c935" },
              { name: "External wall insulation",    count: 3159,   pct: 1.2,  colour: "#f57c35" },
            ].map(item => (
              <div className="ber-improvement-row" key={item.name}>
                <div className="ber-improvement-label">
                  <span>{item.name}</span>
                  <strong>{item.pct}%</strong>
                </div>
                <div className="ber-improvement-bar-track">
                  <div
                    className="ber-improvement-bar-fill"
                    style={{ width: `${item.pct}%`, background: item.colour }}
                  />
                </div>
                <div className="ber-improvement-count">{item.count.toLocaleString()} homes</div>
              </div>
            ))}
          </div>
          <p className="ber-note">
            Additionally, <strong>82,085</strong> homes across all assessments (5.8%) have underfloor
            heating — often paired with heat pumps in newer builds.
          </p>
        </section>

        {/* ── Heating fuel ── */}
        <section className="content-section">
          <h2>How Ireland Heats Its Homes</h2>
          <p>
            Mains gas and heating oil are almost evenly split as the dominant heating fuels, together
            accounting for two-thirds of all homes. The electricity share (27%) includes homes with
            heat pumps, storage heaters, and electric boilers — a segment that will grow as retrofits
            accelerate.
          </p>
          <div className="ber-fuel-grid">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={HEATING_FUEL}
                  dataKey="pct"
                  nameKey="fuel"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ fuel, pct }) => `${fuel} ${pct}%`}
                  labelLine={true}
                >
                  {HEATING_FUEL.map((entry, i) => (
                    <Cell key={entry.fuel} fill={FUEL_COLOURS[i]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => [`${v}%`, "Share"]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ── County rankings ── */}
        <section className="content-section">
          <h2>Best &amp; Worst Rated Counties</h2>
          <p>
            Dublin 18 (Sandyford, Foxrock, Stillorgan) leads the country with 70% of homes rated A or B —
            driven by newer, larger stock. Dublin 7 and rural western counties have the lowest share
            of high-rated homes, reflecting older housing stock with limited retrofit activity.
          </p>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart
              data={COUNTY_RANKINGS}
              layout="vertical"
              margin={{ top: 8, right: 60, left: 90, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
              <XAxis type="number" tickFormatter={v => v + "%"} tick={{ fontSize: 11 }} domain={[0, 80]} />
              <YAxis type="category" dataKey="county" tick={{ fontSize: 11 }} width={90} />
              <Tooltip formatter={(v: any) => [`${v}%`, "A/B rated"]} />
              <Bar dataKey="ab" name="A/B rated" radius={[0, 3, 3, 0]}>
                {COUNTY_RANKINGS.map((entry) => (
                  <Cell
                    key={entry.county}
                    fill={entry.ab >= 40 ? "#2d9e47" : entry.ab >= 30 ? "#f5c935" : "#e07b39"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>

        <p className="ber-disclaimer">
          Data source: SEAI BER Public Search dataset ({totalAssessments.toLocaleString()} assessments).
          Figures represent homes that received a BER assessment — not all Irish homes. New builds are
          over-represented relative to the national stock. Assessment year ranges from 2009 to 2025.
        </p>

        <section className="content-section">
          <h2>Search Property Prices</h2>
          <p>
            Use the <Link to="/">interactive map</Link> to search sale prices by address or area across Ireland,
            or check <Link to="/county/dublin">Dublin postcode price breakdowns</Link>.
          </p>
        </section>

      </div>
      <Footer />
    </>
  );
}
