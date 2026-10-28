import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ comparison of the Property Price Register with the CSO's
// Residential Property Price Index tables (PxStat, downloaded 27 Oct 2026).
// Raw figures: docs/blog_ppr_vs_cso_raw.json; scripts/cso_compare.py reruns the
// routing-key and county comparison.
//
//   CSO tables: HPA05 (annual medians by region and dwelling status), HPA06
//   (annual RPPI), HPA02 (annual transactions by county, buyer and sale type),
//   HPA04 (annual medians by Eircode routing key). All by "Executions" (deed
//   date), which matches the PPR's date of sale.
//   PPR yearly medians: second-hand, full market price, €50k–€3m, bulk
//   unit-range rows removed (docs/blog_market_drivers_ppr_raw.json).
//   County and routing-key comparison: all full-market-price second-hand sales
//   in 2025, compared where both sides have 30+ sales.
//   New homes: the PPR shows prices ex-VAT; the CSO includes VAT at 13.5%.
//   With VAT added (backend/price_vat.py: 13.5%, or 9% on new apartments from
//   8 Oct 2025), 2025 full-price sales, €50k–€3m, bulk rows removed: all homes
//   €361,233 -> €380,000 (CSO €387,500, HPA05); new homes €387,665 -> €435,000
//   (CSO €440,000). One aggregate query, 28 Oct 2026.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const ORANGE = "#eb6834";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";
const PURPLE = "#7c5cc4";

const p = { marginBottom: "1.25rem" };
const link = { color: BLUE, textDecoration: "underline" };

// Second-hand median sale price (€k) by year: [year, PPR, CSO]
const DUBLIN: [number, number, number][] = [
  [2010, 287.5, 290], [2011, 252.5, 252.25], [2012, 220, 225], [2013, 239.65, 242.75],
  [2014, 259, 275], [2015, 278.186, 290], [2016, 295, 305], [2017, 332.375, 340],
  [2018, 340, 350], [2019, 340, 350], [2020, 350, 368], [2021, 380, 400],
  [2022, 403, 420], [2023, 410, 421], [2024, 450, 455], [2025, 481, 487.925],
];
// National: [year, PPR, CSO, annual RPPI, HPA06]
const NATIONAL: [number, number, number, number][] = [
  [2010, 220, 222, 84.8], [2011, 185, 185, 70.3], [2012, 165, 160, 60.9], [2013, 160, 153, 61.6],
  [2014, 166, 160, 71.8], [2015, 178.5, 170, 80.1], [2016, 190, 186, 86.0], [2017, 210, 208, 95.4],
  [2018, 220, 222, 105.1], [2019, 229, 232, 107.6], [2020, 230, 235, 107.9], [2021, 250, 259.725, 116.9],
  [2022, 275, 280, 131.3], [2023, 290, 300, 135.3], [2024, 318, 325, 146.8], [2025, 350, 355, 157.9],
];

// 2025 second-hand medians by county: [county, CSO sales, CSO median, PPR sales, PPR median, gap %]
const COUNTIES: [string, number, number, number, number, number][] = [
  ["Roscommon", 529, 205000, 670, 190000, -7.3], ["Mayo", 990, 225000, 1283, 210000, -6.7],
  ["Longford", 320, 200000, 428, 186750, -6.6], ["Monaghan", 300, 235000, 388, 222500, -5.3],
  ["Cavan", 529, 242500, 687, 230000, -5.2], ["Clare", 920, 292000, 1105, 280000, -4.1],
  ["Tipperary", 1011, 250000, 1270, 240000, -4.0], ["Sligo", 552, 230000, 677, 221000, -3.9],
  ["Waterford", 998, 265000, 1184, 255000, -3.8], ["Limerick", 1370, 297000, 1694, 287750, -3.1],
  ["Laois", 621, 260000, 703, 252500, -2.9], ["Cork", 3925, 340000, 4793, 330000, -2.9],
  ["Galway", 1670, 345000, 2085, 335000, -2.9], ["Offaly", 532, 267500, 650, 260000, -2.8],
  ["Donegal", 1014, 180000, 1240, 175000, -2.8], ["Kerry", 920, 285000, 1153, 280000, -1.8],
  ["Louth", 976, 290000, 1171, 285000, -1.7], ["Westmeath", 726, 297000, 858, 292500, -1.5],
  ["Meath", 1504, 365000, 1765, 360000, -1.4], ["Dublin", 13242, 487925, 14807, 482000, -1.2],
  ["Kildare", 1735, 410000, 1973, 405000, -1.2], ["Wicklow", 1264, 445011, 1421, 440000, -1.1],
  ["Wexford", 1411, 277000, 1634, 275000, -0.7], ["Leitrim", 317, 195000, 409, 194000, -0.5],
  ["Kilkenny", 617, 290000, 727, 292000, 0.7], ["Carlow", 429, 255000, 550, 260000, 2.0],
];

const eur = (n: number) => "€" + Math.round(n).toLocaleString("en-IE");

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function StatCards() {
  const cards = [
    { big: "Same", small: "source: both come from Revenue stamp duty returns" },
    { big: "±1.2%", small: "typical gap on second-hand medians across 132 Eircode areas" },
    { big: "+13.5%", small: "CSO new-home prices include VAT; the register's don't" },
    { big: "68%", small: "of 2025 transactions are in the CSO's headline figures" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem", margin: "1.5rem 0 2rem" }}>
      {cards.map((c) => (
        <div key={c.small} style={{ background: SURFACE, border: `1px solid ${GRID}`, borderRadius: "0.5rem", padding: "1.1rem 1rem", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "#111827" }}>{c.big}</div>
          <div style={{ fontSize: "0.85rem", color: INK_MUTED, marginTop: "0.25rem" }}>{c.small}</div>
        </div>
      ))}
    </div>
  );
}

function Legend({ items }: { items: { label: string; color: string; dashed?: boolean }[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.85rem", color: INK_MUTED, margin: "0.5rem 0 0" }}>
      {items.map((it) => (
        <span key={it.label} style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ width: 14, height: it.dashed ? 0 : 10, borderTop: it.dashed ? `2px dashed ${it.color}` : undefined, background: it.dashed ? undefined : it.color, borderRadius: 2, display: "inline-block" }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}

function Figure({ caption, children }: { caption: React.ReactNode; children: React.ReactNode }) {
  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      {children}
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>{caption}</figcaption>
    </figure>
  );
}

const svgStyle = { background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` };

// Yearly line chart, 2010–2025.
function YearChart({ series, lo, hi, ticks, fmt, aria }: {
  series: { label: string; color: string; values: number[]; dashed?: boolean }[];
  lo: number; hi: number; ticks: number[]; fmt: (v: number) => string; aria: string;
}) {
  const W = 720, H = 300, padL = 56, padR = 16, padT = 20, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const years = DUBLIN.map(([y]) => y);
  const x = (i: number) => padL + (i / (years.length - 1)) * plotW;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={aria} style={svgStyle}>
      {ticks.map((g) => (
        <g key={g}>
          <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
          <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{fmt(g)}</text>
        </g>
      ))}
      {years.map((yr, i) => i % 3 === 0 || i === years.length - 1 ? (
        <text key={yr} x={x(i)} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{yr}</text>
      ) : null)}
      {series.map((s) => (
        <g key={s.label}>
          <polyline fill="none" stroke={s.color} strokeWidth={2.4} strokeDasharray={s.dashed ? "6 4" : undefined}
                    points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(" ")} />
          {s.values.map((v, i) => (
            <circle key={i} cx={x(i)} cy={y(v)} r={2.6} fill={s.color}>
              <title>{`${years[i]} — ${s.label}: ${fmt(v)}`}</title>
            </circle>
          ))}
        </g>
      ))}
    </svg>
  );
}

const kfmt = (v: number) => `€${Math.round(v)}k`;

function DublinChart() {
  return (
    <>
      <YearChart
        lo={200} hi={500} ticks={[200, 300, 400, 500]} fmt={kfmt}
        aria="Line chart of the median second-hand sale price in Dublin each year from 2010 to 2025, from the Property Price Register and from the CSO. The two lines run almost on top of each other, from about 290 thousand euro in 2010, down to about 220 thousand in 2012, and up to about 485 thousand in 2025. The register's median is up to 6% lower in each year."
        series={[
          { label: "CSO", color: ORANGE, values: DUBLIN.map(([, , c]) => c) },
          { label: "Property Price Register", color: BLUE, values: DUBLIN.map(([, ppr]) => ppr) },
        ]}
      />
      <Legend items={[{ label: "Property Price Register", color: BLUE }, { label: "CSO", color: ORANGE }]} />
    </>
  );
}

function NationalChart() {
  return (
    <>
      <YearChart
        lo={100} hi={400} ticks={[100, 200, 300, 400]} fmt={kfmt}
        aria="Line chart of the national median second-hand sale price each year from 2010 to 2025, from the Property Price Register and from the CSO. Both fall from about 220 thousand euro in 2010 to a low of 153 to 160 thousand in 2012 and 2013, then rise to 350 to 355 thousand in 2025. The register's median is a little higher than the CSO's from 2012 to 2017 and a little lower from 2018."
        series={[
          { label: "CSO", color: ORANGE, values: NATIONAL.map(([, , c]) => c) },
          { label: "Property Price Register", color: BLUE, values: NATIONAL.map(([, ppr]) => ppr) },
        ]}
      />
      <Legend items={[{ label: "Property Price Register", color: BLUE }, { label: "CSO", color: ORANGE }]} />
    </>
  );
}

// National series rebased so 2013 = 100.
function IndexChart() {
  const base = NATIONAL[3];
  const rebase = (k: 1 | 2 | 3) => NATIONAL.map((r) => (r[k] / base[k]) * 100);
  return (
    <>
      <YearChart
        lo={50} hi={300} ticks={[50, 100, 150, 200, 250, 300]} fmt={(v) => String(Math.round(v))}
        aria="Line chart of three national measures rebased so that 2013 equals 100: the register's median second-hand price, the CSO's median second-hand price, and the CSO's mix-adjusted Residential Property Price Index. By 2025 the register's median is at 219, the CSO's median at 232 and the price index at 256."
        series={[
          { label: "CSO price index (RPPI)", color: PURPLE, values: rebase(3), dashed: true },
          { label: "CSO median", color: ORANGE, values: rebase(2) },
          { label: "Register median", color: BLUE, values: rebase(1) },
        ]}
      />
      <Legend items={[
        { label: "Register median", color: BLUE },
        { label: "CSO median", color: ORANGE },
        { label: "CSO price index (RPPI)", color: PURPLE, dashed: true },
      ]} />
    </>
  );
}

// Horizontal bars: register median vs CSO median, % gap per county.
function CountyGapChart() {
  const rowH = 22, padL = 96, padR = 56, padT = 12, padB = 30, W = 720;
  const H = padT + COUNTIES.length * rowH + padB;
  const lo = -8, hi = 3;
  const x = (v: number) => padL + ((v - lo) / (hi - lo)) * (W - padL - padR);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
         aria-label="Bar chart of the gap between the register's and the CSO's median second-hand sale price in each county in 2025. The register is lower in 24 of 26 counties. The largest gaps are Roscommon at minus 7.3%, Mayo minus 6.7%, Longford minus 6.6%, Monaghan minus 5.3% and Cavan minus 5.2%. Dublin is minus 1.2%. Kilkenny (plus 0.7%) and Carlow (plus 2.0%) are the only counties where the register is higher.">
      {[-8, -6, -4, -2, 0, 2].map((g) => (
        <g key={g}>
          <line x1={x(g)} x2={x(g)} y1={padT} y2={H - padB} stroke={g === 0 ? NEUTRAL : GRID} />
          <text x={x(g)} y={H - padB + 16} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{g > 0 ? `+${g}%` : `${g}%`}</text>
        </g>
      ))}
      {COUNTIES.map(([name, cn, cm, pn, pm, gap], i) => {
        const yy = padT + i * rowH;
        const x0 = x(Math.min(0, gap)), x1 = x(Math.max(0, gap));
        return (
          <g key={name}>
            <text x={padL - 8} y={yy + rowH / 2 + 4} textAnchor="end" fontSize={11.5} fill={INK}>{name}</text>
            <rect x={x0} y={yy + 4} width={Math.max(1, x1 - x0)} height={rowH - 8} rx={3} fill={BLUE}>
              <title>{`${name}: register ${eur(pm)} (${pn.toLocaleString()} sales), CSO ${eur(cm)} (${cn.toLocaleString()} sales)`}</title>
            </rect>
            <text x={gap < 0 ? x0 - 5 : x1 + 5} y={yy + rowH / 2 + 4} textAnchor={gap < 0 ? "end" : "start"} fontSize={10.5} fill={INK_MUTED}>
              {gap > 0 ? `+${gap.toFixed(1)}%` : `${gap.toFixed(1)}%`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

const th = { textAlign: "left" as const, padding: "0.5rem 0.75rem", borderBottom: `2px solid ${GRID}`, fontWeight: 600 };
const td = { padding: "0.45rem 0.75rem", borderBottom: `1px solid ${GRID}` };
const tdNum = { ...td, textAlign: "right" as const };

function VolumeTable() {
  const rows: [string, number, string][] = [
    ["All transactions with a stamp duty return", 74806, "€360,000"],
    ["…of which non-market (gifts, family transfers, etc.)", 11363, "—"],
    ["Market purchases", 63443, "€389,000"],
    ["…by non-household buyers (companies, councils, housing bodies)", 12874, "€390,000"],
    ["…by households: the CSO's headline figures", 50569, "€387,500"],
    ["……first-time buyers", 19703, "€395,000"],
    ["……former owner-occupiers (movers)", 25807, "€400,000"],
    ["……non-occupiers (individual landlords, second homes)", 5059, "€250,000"],
  ];
  return (
    <div style={{ overflowX: "auto", margin: "1.25rem 0 2rem" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
        <thead>
          <tr><th style={th}>2025 transactions (CSO, by date of sale)</th><th style={{ ...th, textAlign: "right" }}>Number</th><th style={{ ...th, textAlign: "right" }}>Median</th></tr>
        </thead>
        <tbody>
          {rows.map(([label, n, med]) => (
            <tr key={label}><td style={td}>{label}</td><td style={tdNum}>{n.toLocaleString("en-IE")}</td><td style={tdNum}>{med}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PprVsCsoContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Two official sources tell you what Irish homes sell for. The <strong>Property Price Register</strong>, run by the
        Property Services Regulatory Authority, lists every residential sale with its address, date and price. The{" "}
        <strong>Central Statistics Office</strong> publishes the Residential Property Price Index and median prices by
        county and Eircode area. Their figures are close but rarely identical, and headlines quote both. So which is right,
        and is the CSO working from asking prices, valuations or something else entirely?
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The short answer:</strong> both use the <strong>same data</strong>: the stamp duty returns that
          solicitors file with Revenue when a sale closes. Neither uses asking prices or valuations. The CSO keeps a
          narrower slice (market-price purchases by households that it can match to a BER certificate), adds VAT to new
          homes, and adjusts its index for the mix of homes sold. For second-hand homes the two agree to within about{" "}
          <strong>1%</strong> in a typical Eircode area.
        </p>
      </div>

      <StatCards />

      <SectionHeading>Same returns, different filters</SectionHeading>
      <p style={p}>
        When a home is sold, the buyer's solicitor files a stamp duty return with Revenue. The Property Price Register
        publishes the price "as declared to the Revenue Commissioners for stamp duty purposes", with the address and the
        date of sale. The CSO gets the same returns from Revenue and links each one to two other records: the home's{" "}
        <strong>BER certificate</strong> (floor area, dwelling type, energy rating) and its <strong>GeoDirectory</strong>{" "}
        address point (exact location). Only returns it can match to both make it into the statistics.
      </p>
      <p style={p}>
        Advertised prices are a different thing entirely. The Daft.ie and MyHome.ie reports are based on asking prices,
        not sales. Neither the register nor the CSO touches them, or bank valuations.
      </p>
      <p style={p}>Starting from the same returns, the CSO leaves out:</p>
      <ul style={{ marginBottom: "1.25rem", paddingLeft: "1.25rem" }}>
        <li><strong>Non-market sales</strong>: transfers between family members, partial shares and other deals not at
          full price. The register keeps these but flags them "not full market price".</li>
        <li><strong>Non-household buyers</strong>: companies, local authorities, approved housing bodies and investment
          funds. On the register these look like any other sale.</li>
        <li><strong>Self-builds</strong>, and returns that can't be matched to a BER and an address point.</li>
      </ul>
      <p style={p}>
        Two other differences matter. The register shows new-home prices <strong>excluding VAT</strong>; the CSO includes
        VAT at 13.5%. And the CSO publishes two dates for every sale: when the deed was signed ("executions") and when
        the return was filed. The register's date of sale is the deed date, so we compare against executions throughout.
      </p>

      <SectionHeading>Second-hand homes: almost the same answer</SectionHeading>
      <p style={p}>
        Second-hand homes are the fair comparison, because VAT and new-scheme bulk purchases don't come into it. Taking
        full-price second-hand sales from the register (excluding prices under €50,000 or over €3m and multi-unit rows),
        the yearly median tracks the CSO's closely in Dublin and nationally.
      </p>
      <Figure caption="Median second-hand sale price, Dublin, 2010–2025. Register: full-market-price sales between €50k and €3m, bulk rows removed. CSO: market-based household purchases of existing homes (table HPA05), by date of sale.">
        <DublinChart />
      </Figure>
      <Figure caption="Median second-hand sale price, Ireland, 2010–2025. Same definitions as above.">
        <NationalChart />
      </Figure>
      <p style={p}>
        Dublin's two lines are never more than about 6% apart. In 2025 the register's median second-hand price was{" "}
        <strong>€481,000</strong> against the CSO's <strong>€487,925</strong>. Nationally the figures were €350,000 and
        €355,000. The register has more sales (44,663 against 38,422 nationally in 2025) because it keeps the non-household
        buyers and the unmatched returns.
      </p>
      <p style={p}>
        The same holds at a finer level. Using the 2025 figures for Eircode routing areas (D06, A94, H91 and so on), we
        compared the second-hand median in <strong>132 areas</strong> where both sources had at least 30 sales. The typical
        gap was almost nil (<strong>−0.1%</strong>), and half the areas were within <strong>1.2%</strong>. 120 were within 5%, and only
        one was more than 10% apart: A75 Castleblayney, where the CSO's median is €265,500 and the register's €232,500.
      </p>

      <SectionHeading>Where they part: rural counties</SectionHeading>
      <p style={p}>
        By county, the register comes in lower in 24 of 26 counties. In the commuter belt and Dublin the gap is about 1%.
        In the rural north-west and midlands it's 5–7%.
      </p>
      <Figure caption="Register median vs CSO median, second-hand homes, 2025, by county. Negative means the register is lower. Hover a bar for the figures.">
        <CountyGapChart />
      </Figure>
      <p style={p}>
        The counties with the biggest gaps are also the ones where the register has the most extra sales. Roscommon has{" "}
        <strong>670</strong> second-hand sales on the register against the CSO's <strong>529</strong> (27% more), with
        medians of €190,000 and €205,000. Our best explanation is matching: rural addresses are harder to tie to a BER
        certificate and a GeoDirectory point, and the homes that drop out seem to be cheaper ones. Those sales are real.
        They just aren't in the CSO's sample.
      </p>

      <SectionHeading>New homes: VAT and missing Eircodes</SectionHeading>
      <p style={p}>
        Include new homes and the gap widens. Across all full-price 2025 sales, the register's median was{" "}
        <strong>€361,233</strong>, 7% below the CSO's <strong>€387,500</strong>. Almost all of that comes from new builds,
        for two reasons.
      </p>
      <p style={p}>
        <strong>VAT.</strong> The register's national median for a new home in 2025 was <strong>€387,665</strong>. Add VAT
        at 13.5% and you get <strong>€440,000</strong>, exactly the CSO's figure. The two sources agree; one quotes the
        price before tax and the other after.
      </p>
      <p style={p}>
        <strong>Eircodes.</strong> A newly built home often has no Eircode when its sale is filed. In 2025,{" "}
        <strong>88% of new-home sales on the register</strong> (12,788 of 14,519) had none. The CSO places them using
        GeoDirectory; anyone grouping register sales by Eircode will miss most new homes. In fast-growing towns that
        changes the answer. In A84 (Ashbourne) the CSO's median for all homes is €485,000, while register sales with an
        A84 Eircode, mostly older homes, have a median of €343,500.
      </p>

      <SectionHeading>How HomeIQ lines up with the CSO</SectionHeading>
      <p style={p}>
        HomeIQ's area and county pages place sales by address and map location rather than Eircode, so new homes without
        one are still counted. Before working out any median, trend or valuation, we add VAT back to every new-home sale
        at the rate that applied: <strong>13.5%</strong> on houses, and <strong>9%</strong> on apartments sold from 8 October
        2025. The register doesn't say which is which, so we tell an apartment from its address ("Apt", "Apartment",
        "Duplex") or its recorded property type.
      </p>
      <p style={p}>
        With VAT added, the national median for all full-price 2025 sales rises from €361,233 to{" "}
        <strong>€380,000</strong>, within 2% of the CSO's €387,500. That is about the same gap as for second-hand homes
        alone (€350,000 against €355,000), so what's left comes from the CSO's narrower sample rather than tax. For new homes
        our median is <strong>€435,000</strong> against the CSO's €440,000. Ours is a little lower because new apartments
        sold since October carry 9% rather than 13.5%.
      </p>
      <p style={p}>
        Our valuations also leave out bulk sales. When a fund or housing body buys a block of new homes, the register
        can list every unit at the same split price on the same day (24 apartments at €400,881.06 each in one Dublin
        scheme). That's the deal's average rather than what one home sold for, so those units never count as comparables.
        New-build prices in our{" "}
        <Link to="/blog/irish-property-market-health-36-months" style={link}>market analysis</Link> include VAT too.
        Individual sales are still listed at the register price, as published.
      </p>

      <SectionHeading>Median price vs price index</SectionHeading>
      <p style={p}>
        The CSO's headline number isn't a median: it's the <strong>Residential Property Price Index</strong>. The index
        compares like with like. It uses a statistical model (a rolling 12-month hedonic regression) to estimate what the
        same kind of home, with the same size, type, energy rating and location, would sell for from one month to the
        next. A median just takes the middle sale, so it moves when the mix of homes sold changes.
      </p>
      <Figure caption="National second-hand medians from both sources and the CSO's mix-adjusted price index (all residential properties, annual average, table HPA06), each rebased so 2013 = 100.">
        <IndexChart />
      </Figure>
      <p style={p}>
        From 2013 to 2025, the register's median second-hand price rose <strong>119%</strong>, the CSO's median{" "}
        <strong>132%</strong> and the price index <strong>156%</strong>. The index rose fastest because the homes selling
        now are, on average, cheaper kinds of homes than in 2013: smaller, further from city centres, or older. A plain
        median hides some of the rise in prices. For "how much has the same home gone up?", the index is the better answer.
        For "what does a typical buyer pay?", the median is.
      </p>

      <SectionHeading>Who's in the CSO's figures</SectionHeading>
      <p style={p}>
        The CSO's 2025 breakdown shows how much its headline figures leave out. Of 74,806 transactions with a stamp duty
        return, 50,569 (68%) were market purchases by households, the group its medians and index describe.
      </p>
      <VolumeTable />
      <p style={p}>
        Non-household buyers bought one market-price home in five in 2025, at a median (€390,000) close to households'.
        Many are new apartments and houses bought in bulk by funds, councils and housing bodies. On the register
        these can appear as one row covering many homes, which is one reason row counts on the two sources don't line up.
      </p>

      <SectionHeading>What this means when you look up prices</SectionHeading>
      <ul style={{ marginBottom: "1.25rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.5rem" }}><strong>For a street or estate, use the register.</strong> It lists every
          sale with an address, which is what you need to compare a specific home.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>For "how fast are prices rising?", use the CSO's index.</strong> It
          strips out changes in the mix of homes sold.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Comparing new homes? Check VAT.</strong> A register price for a new
          home excludes VAT: 13.5% on houses, and 9% on apartments sold since 8 October 2025. HomeIQ's medians,
          trends and valuations add it back for you.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Small differences are expected.</strong> A gap of 1–3% between the
          register and the CSO is normal, and up to 7% in some rural counties.</li>
      </ul>
      <p style={p}>
        HomeIQ's <Link to="/county/dublin" style={link}>county</Link>, area and Eircode pages now show the CSO's latest
        figures next to our register-based ones, including its house and apartment medians.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>See both for your area.</strong> Search any address, Eircode or area for every recorded sale nearby,
          or open a county page for the official CSO figures alongside.{" "}
          <Link to="/" style={link}>Search sold prices →</Link>{" · "}
          <Link to="/county/dublin" style={link}>Dublin prices →</Link>
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        Sources: Property Services Regulatory Authority, Property Price Register (HomeIQ analysis); Central Statistics
        Office, Residential Property Price Index tables HPA02, HPA04, HPA05 and HPA06, downloaded 27 October 2026 and used
        under CC BY 4.0. CSO figures are by date of sale (executions) and are revised as late returns are filed. Register
        figures are full-market-price sales (second-hand unless stated); medians exclude prices outside €50,000–€3m and
        bulk multi-unit rows, and VAT-inclusive figures add 13.5% (9% for new apartments from 8 October 2025) to new
        homes. Comparisons by county and Eircode area use areas with at least 30 sales on both sides.
      </p>
    </div>
  );
}
