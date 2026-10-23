import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data: HomeIQ analysis of the Property Price Register (sales dated 1 Jan 2010 to
// 2 Oct 2026) combined with CSO population, migration, income, earnings and housing
// completions tables, retrieved 23 Oct 2026.
// Raw outputs: docs/blog_market_drivers_ppr_raw.json, docs/blog_market_drivers_cso_raw.json.
//
// PPR cleaning (same rules as the /heatmap price index and the 36-month health post):
//   • full-market-price sales only; €50k ≤ price ≤ €3m; bulk "Units 1-76" rows removed
//   • medians are SECOND-HAND (resale) homes only, so new schemes don't pose as price change
// Regions: Dublin; commuter belt = Kildare, Meath, Wicklow, Louth; cities = the whole
// counties of Cork, Galway, Limerick, Waterford; rest of Ireland = the other 17 counties.
//
// Household income: the CSO only publishes a median household income for 2022 (GPIIA05).
// Other years are estimated by moving that 2022 figure in line with CSO average annual
// earnings (EHA05, national) or with disposable income per person (RAA02, regions; latest
// year 2024, rolled to 2025 with earnings growth). These are estimates, flagged as such.
// "Homes needed" = yearly population change (PEA01, April) / 2.74, the average household
// size at Census 2011, 2016 and 2022. It ignores obsolescence, vacancy and second homes.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const ORANGE = "#eb6834";
const AQUA = "#1baf7a";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";
const PURPLE = "#7c5cc4";

const YEARS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];

// National median second-hand price, €k (PPR, cleaned).
const PRICE = [220, 185, 165, 160, 166, 178.5, 190, 210, 220, 229, 230, 250, 275, 290, 318, 350];
// CSO EHA05: average annual earnings per employee, €.
const EARN = [36277, 35826, 36065, 35951, 36037, 36457, 36933, 37637, 38851, 40280, 42364, 44388, 45949, 47751, 50369, 52587];
// CSO RAA02: disposable household income per person, €. 2025 not yet published.
const DISP: (number | null)[] = [18114, 17874, 18260, 18205, 18250, 19186, 19918, 20950, 21477, 22713, 23553, 24470, 25698, 27986, 30139, null];

const index = (vals: (number | null)[]) => vals.map((v) => (v == null ? null : (v / (vals[0] as number)) * 100));

// Median household gross income 2022 (CSO GPIIA05), moved by earnings growth.
const HH_INCOME_2022 = 60123;
const EARN_2022 = 45949;
const PTI = PRICE.map((pr, i) => (pr * 1000) / ((HH_INCOME_2022 * EARN[i]) / EARN_2022));

// PPR cleaned sales by year: [year, all, of which new build]. 2026 runs to early October.
const SALES: [number, number, number][] = [
  [2010, 19465, 5137], [2011, 16592, 2765], [2012, 21920, 2852], [2013, 25432, 3115], [2014, 38295, 4829],
  [2015, 43198, 5648], [2016, 44514, 6396], [2017, 49675, 8917], [2018, 52006, 10400], [2019, 53547, 10262],
  [2020, 45288, 8438], [2021, 55437, 8755], [2022, 58691, 10229], [2023, 58737, 11043], [2024, 56614, 11694],
  [2025, 57929, 13266], [2026, 35118, 8332],
];

// CSO NDA05: new dwelling completions, State.
const COMPLETIONS: Record<number, number> = {
  2012: 4911, 2013: 4575, 2014: 5518, 2015: 7219, 2016: 9720, 2017: 14218, 2018: 17777,
  2019: 21012, 2020: 20483, 2021: 20443, 2022: 29609, 2023: 32463, 2024: 30124, 2025: 36215,
};
// CSO PEA01: population in April.
const POP: Record<number, number> = {
  2010: 4554800, 2011: 4574900, 2012: 4593700, 2013: 4614700, 2014: 4645400, 2015: 4687800, 2016: 4739600,
  2017: 4810900, 2018: 4884900, 2019: 4958500, 2020: 5029900, 2021: 5074700, 2022: 5184000, 2023: 5281600,
  2024: 5380300, 2025: 5458600, 2026: 5525600,
};
const HOUSEHOLD_SIZE = 2.74;
const SUPPLY_YEARS = Object.keys(COMPLETIONS).map(Number);
const NEEDED = SUPPLY_YEARS.map((y) => (POP[y] - POP[y - 1]) / HOUSEHOLD_SIZE);

// CSO PEA03: net migration, year to April.
const NET_MIGRATION: [number, number][] = [
  [2010, -27500], [2011, -27400], [2012, -25700], [2013, -18700], [2014, -8500], [2015, 5900], [2016, 16200],
  [2017, 39200], [2018, 44400], [2019, 44000], [2020, 44700], [2021, 21800], [2022, 51700], [2023, 77700],
  [2024, 79300], [2025, 59700], [2026, 48100],
];

// Estimated price-to-income ratio by region (resale median / estimated median household income).
const REGION_PTI = [
  { label: "Dublin", color: BLUE, values: [6.12, 5.49, 4.71, 5.12, 5.58, 5.7, 5.7, 6.06, 5.94, 5.54, 5.53, 5.62, 5.67, 5.29, 5.39, 5.52] },
  { label: "Cities", color: PURPLE, values: [4.8, 4.16, 3.63, 3.41, 3.29, 3.32, 3.61, 3.79, 3.92, 3.92, 3.82, 4.1, 4.35, 4.29, 4.3, 4.55] },
  { label: "Commuter belt", color: ORANGE, values: [4.89, 4.08, 3.43, 3.42, 3.71, 3.86, 3.95, 4.08, 4.21, 4.07, 4.01, 4.35, 4.48, 4.25, 4.11, 4.27] },
  { label: "Rest of Ireland", color: AQUA, values: [4.03, 3.48, 3.04, 2.82, 2.75, 2.85, 3.01, 3.11, 3.31, 3.33, 3.26, 3.58, 3.79, 3.67, 3.78, 3.94] },
];

const REGION_TABLE = [
  { region: "Dublin", pop: 14.5, hh: 52031, built: 50587, p13: 239.65, p25: 481, r13: 5.12, r25: 5.52 },
  { region: "Commuter belt", pop: 16.8, hh: 34671, built: 33911, p13: 165, p25: 372, r13: 3.42, r25: 4.27 },
  { region: "Cork, Galway, Limerick, Waterford", pop: 11.5, hh: 45853, built: 31751, p13: 145, p25: 320, r13: 3.41, r25: 4.55 },
  { region: "Rest of Ireland", pop: 9.0, hh: 54389, built: 39105, p13: 108, p25: 245, r13: 2.82, r25: 3.94 },
];

// Town resale medians, €k. Tullamore yearly (51-262 sales a year); Skibbereen is a
// 3-year rolling median because single years have only 21-80 sales.
const TULLAMORE = [185, 135, 127, 120, 127.5, 128.5, 128.5, 160, 175, 177, 179, 190, 220, 232, 245, 280];
const SKIBBEREEN = [170, 160, 147.5, 146.25, 149.75, 152.95, 160, 168, 185, 185, 200, 230, 250, 260, 285, 286.25];

const p = { marginBottom: "1.25rem" };
const link = { color: BLUE, textDecoration: "underline" };
const fmtK = (v: number) => `€${Math.round(v)}k`;

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function StatCards() {
  const cards = [
    { big: "+119%", small: "second-hand median since the 2013 low (€160k → €350k)" },
    { big: "+46%", small: "average earnings over the same years" },
    { big: "+971k", small: "more people, 2010 → 2026 (+21%)" },
    { big: "8×", small: "new homes completed, 2013 → 2025 (4,575 → 36,215)" },
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

function Figure({ label, caption, children }: { label: string; caption: React.ReactNode; children: React.ReactNode }) {
  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      {children}
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }} title={label}>
        {caption}
      </figcaption>
    </figure>
  );
}

const svgStyle = { background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` };

// --- Yearly line chart with direct end labels ----------------------------------
type Series = { label: string; color: string; values: (number | null)[]; dashed?: boolean };

function YearLineChart({ series, lo, hi, ticks, fmt, aria, height = 300, refLines = [] }: {
  series: Series[]; lo: number; hi: number; ticks: number[]; fmt: (v: number) => string; aria: string; height?: number;
  refLines?: { v: number; label: string }[];
}) {
  const W = 720, H = height, padL = 52, padR = 140, padT = 18, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const x = (i: number) => padL + (i / (YEARS.length - 1)) * plotW;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  // End labels sit at each series' last point, pushed apart so they never overlap.
  const ends = series.map((s, k) => {
    let i = s.values.length - 1;
    while (s.values[i] == null) i--;
    return { k, i, v: s.values[i] as number, ly: y(s.values[i] as number) };
  }).sort((a, b) => a.ly - b.ly);
  ends.forEach((e, j) => { if (j > 0) e.ly = Math.max(e.ly, ends[j - 1].ly + 15); });
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={aria} style={svgStyle}>
      {ticks.map((g) => (
        <g key={g}>
          <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
          <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{fmt(g)}</text>
        </g>
      ))}
      {refLines.map((r) => (
        <g key={r.label}>
          <line x1={padL} x2={W - padR} y1={y(r.v)} y2={y(r.v)} stroke={NEUTRAL} strokeDasharray="5 4" />
          {r.label && <text x={W - padR - 4} y={y(r.v) + 15} textAnchor="end" fontSize={10.5} fill={INK_MUTED}>{r.label}</text>}
        </g>
      ))}
      {YEARS.map((yr, i) => (i % 3 === 0 || i === YEARS.length - 1) && (
        <text key={yr} x={x(i)} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{yr}</text>
      ))}
      {series.map((s, k) => {
        const pts = s.values.map((v, i) => (v == null ? null : { i, v })).filter((q): q is { i: number; v: number } => q != null);
        const end = ends.find((e) => e.k === k)!;
        return (
          <g key={s.label}>
            <polyline fill="none" stroke={s.color} strokeWidth={2} strokeDasharray={s.dashed ? "6 4" : undefined}
                      points={pts.map((q) => `${x(q.i)},${y(q.v)}`).join(" ")} />
            {pts.map((q) => (
              <circle key={q.i} cx={x(q.i)} cy={y(q.v)} r={4} fill={s.color} stroke={SURFACE} strokeWidth={1.5}>
                <title>{`${YEARS[q.i]}, ${s.label}: ${fmt(q.v)}`}</title>
              </circle>
            ))}
            <text x={x(end.i) + 9} y={end.ly + 4} fontSize={11.5} fontWeight={600} fill={INK}>
              {s.label} {fmt(end.v)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function IndexChart() {
  return (
    <>
      <YearLineChart
        lo={60} hi={180} ticks={[60, 80, 100, 120, 140, 160, 180]} fmt={(v) => `${Math.round(v)}`}
        aria="Line chart indexing three series to 2010 equals 100. The median second-hand price falls to 73 in 2013, passes 100 again in 2018 and reaches 159 in 2025. Average earnings stay flat near 100 until 2016 and reach 145 in 2025. Disposable income per person is flat until 2014 and reaches 166 in 2024."
        series={[
          { label: "Price", color: BLUE, values: index(PRICE) },
          { label: "Income/person", color: AQUA, values: index(DISP) },
          { label: "Earnings", color: ORANGE, values: index(EARN) },
        ]}
      />
      <Legend items={[
        { label: "Median second-hand price (PPR)", color: BLUE },
        { label: "Disposable income per person (CSO RAA02, to 2024)", color: AQUA },
        { label: "Average annual earnings (CSO EHA05)", color: ORANGE },
      ]} />
    </>
  );
}

function SalesChart() {
  const W = 720, H = 300, padL = 52, padR = 12, padT = 18, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 60000;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const step = plotW / SALES.length;
  const barW = step * 0.7;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Stacked bar chart of yearly residential sales on the Property Price Register after cleaning, 2010 to 2026, split into second-hand and new build. Sales rise from about 17,000 in 2011 to 58,000 to 59,000 in 2022 and 2023, then hold at 57,000 to 58,000. New builds grow from about 2,800 in 2011 to 13,300 in 2025. 2026 is a partial year to early October.">
        {[0, 20000, 40000, 60000].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g === 0 ? "0" : `${g / 1000}k`}</text>
          </g>
        ))}
        {SALES.map(([yr, n, nNew], i) => {
          const bx = padL + i * step + (step - barW) / 2;
          const partial = yr === 2026;
          return (
            <g key={yr} opacity={partial ? 0.45 : 1}>
              <rect x={bx} y={y(n - nNew)} width={barW} height={y(0) - y(n - nNew)} fill={BLUE}>
                <title>{`${yr}: ${(n - nNew).toLocaleString()} second-hand${partial ? " (to early Oct)" : ""}`}</title>
              </rect>
              <rect x={bx} y={y(n) + 1} width={barW} height={Math.max(0, y(n - nNew) - y(n) - 2)} rx={3} fill={ORANGE}>
                <title>{`${yr}: ${nNew.toLocaleString()} new build (${Math.round((nNew / n) * 100)}% of sales)`}</title>
              </rect>
              {(i % 2 === 0 || partial) && (
                <text x={bx + barW / 2} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{partial ? "2026*" : yr}</text>
              )}
            </g>
          );
        })}
      </svg>
      <Legend items={[{ label: "Second-hand", color: BLUE }, { label: "New build", color: ORANGE }]} />
    </>
  );
}

function SupplyNeedChart() {
  const W = 720, H = 310, padL = 52, padR = 12, padT = 18, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 40000;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const step = plotW / SUPPLY_YEARS.length;
  const barW = step * 0.62;
  const cx = (i: number) => padL + i * step + step / 2;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Bar chart of new homes completed each year from 2012 to 2025, with a line showing the homes needed to house that year's population growth at 2.74 people per home. Completions are far below need from 2014 to 2019 and from 2022 to 2024. Completions exceed need only in 2021 and 2025.">
        {[0, 10000, 20000, 30000, 40000].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g === 0 ? "0" : `${g / 1000}k`}</text>
          </g>
        ))}
        {SUPPLY_YEARS.map((yr, i) => (
          <g key={yr}>
            <rect x={cx(i) - barW / 2} y={y(COMPLETIONS[yr])} width={barW} height={y(0) - y(COMPLETIONS[yr])} rx={3} fill={BLUE}>
              <title>{`${yr}: ${COMPLETIONS[yr].toLocaleString()} homes completed`}</title>
            </rect>
            {i % 2 === 0 && (
              <text x={cx(i)} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{yr}</text>
            )}
          </g>
        ))}
        <polyline fill="none" stroke={ORANGE} strokeWidth={2} points={NEEDED.map((v, i) => `${cx(i)},${y(v)}`).join(" ")} />
        {NEEDED.map((v, i) => (
          <circle key={i} cx={cx(i)} cy={y(v)} r={4} fill={ORANGE} stroke={SURFACE} strokeWidth={1.5}>
            <title>{`${SUPPLY_YEARS[i]}: ~${Math.round(v / 100) * 100} homes needed (population +${(POP[SUPPLY_YEARS[i]] - POP[SUPPLY_YEARS[i] - 1]).toLocaleString()})`}</title>
          </circle>
        ))}
      </svg>
      <Legend items={[{ label: "Homes completed (CSO)", color: BLUE }, { label: "Homes needed for population growth (÷ 2.74)", color: ORANGE }]} />
    </>
  );
}

function MigrationChart() {
  const W = 720, H = 260, padL = 52, padR = 12, padT = 18, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = -40000, hi = 80000;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const step = plotW / NET_MIGRATION.length;
  const barW = step * 0.66;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Bar chart of net migration into Ireland in the year to April, 2010 to 2026. Net emigration of about 27,000 a year in 2010 and 2011 shrinks to 8,500 in 2014. Inflows turn positive in 2015, run at about 44,000 a year from 2018 to 2020, peak at 79,300 in 2024 and ease to 48,100 in 2026.">
        {[-40000, 0, 40000, 80000].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={g === 0 ? NEUTRAL : GRID} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g === 0 ? "0" : `${g > 0 ? "+" : "−"}${Math.abs(g) / 1000}k`}</text>
          </g>
        ))}
        {NET_MIGRATION.map(([yr, v], i) => {
          const bx = padL + i * step + (step - barW) / 2;
          return (
            <g key={yr}>
              <rect x={bx} y={Math.min(y(v), y(0))} width={barW} height={Math.abs(y(v) - y(0))} rx={3} fill={v < 0 ? ORANGE : BLUE}>
                <title>{`Year to April ${yr}: net migration ${v > 0 ? "+" : ""}${v.toLocaleString()}`}</title>
              </rect>
              {i % 2 === 0 && (
                <text x={bx + barW / 2} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{yr}</text>
              )}
            </g>
          );
        })}
      </svg>
      <Legend items={[{ label: "Net inflow", color: BLUE }, { label: "Net outflow", color: ORANGE }]} />
    </>
  );
}

function AffordabilityChart() {
  return (
    <YearLineChart
      lo={2.5} hi={6.5} ticks={[3, 4, 5, 6]} fmt={(v) => `${v.toFixed(1)}×`} height={290}
      refLines={[{ v: 4, label: "Central Bank first-time-buyer limit: 4× income" }]}
      aria="Line chart of the estimated national ratio of the median second-hand price to median household income, 2010 to 2025. It falls from 4.6 in 2010 to 3.4 in 2013, rises to about 4.3 in 2017 to 2019, dips to 4.2 in 2020 and climbs to 5.1 in 2025. A dashed reference line marks the Central Bank's 4 times income limit for first-time buyers."
      series={[{ label: "Ireland", color: BLUE, values: PTI }]}
    />
  );
}

function RegionAffordabilityChart() {
  return (
    <>
      <YearLineChart
        lo={2.5} hi={6.5} ticks={[3, 4, 5, 6]} fmt={(v) => `${v.toFixed(1)}×`} height={320}
        refLines={[{ v: 4, label: "" }]}
        aria="Line chart of the estimated ratio of median second-hand price to median household income by region, 2010 to 2025. Dublin stays highest, between 4.7 and 6.1, ending at 5.5. The cities rise from 3.3 in 2014 to 4.55. The commuter belt rises from 3.4 in 2013 to 4.3. The rest of Ireland rises from 2.75 in 2014 to 3.9, the largest relative increase."
        series={REGION_PTI}
      />
      <Legend items={REGION_PTI.map((s) => ({ label: s.label, color: s.color }))} />
    </>
  );
}

function TownsChart() {
  return (
    <>
      <YearLineChart
        lo={100} hi={400} ticks={[100, 200, 300, 400]} fmt={fmtK} height={300}
        aria="Line chart of median second-hand prices, 2010 to 2025, for Ireland, Tullamore and Skibbereen. Tullamore falls to 120 thousand euro in 2013, is flat near 128 thousand until 2016, then rises to 280 thousand in 2025. Skibbereen, as a three-year rolling median, bottoms near 146 thousand in 2013 and reaches 286 thousand. Ireland goes from 160 thousand in 2013 to 350 thousand."
        series={[
          { label: "Ireland", color: NEUTRAL, values: PRICE, dashed: true },
          { label: "Skibbereen", color: ORANGE, values: SKIBBEREEN },
          { label: "Tullamore", color: BLUE, values: TULLAMORE },
        ]}
      />
      <Legend items={[
        { label: "Ireland (national median)", color: NEUTRAL, dashed: true },
        { label: "Tullamore (yearly median)", color: BLUE },
        { label: "Skibbereen (3-year rolling median)", color: ORANGE },
      ]} />
    </>
  );
}

const th = { textAlign: "left" as const, padding: "0.5rem 0.6rem", borderBottom: `2px solid ${GRID}`, fontWeight: 600, color: "#111827" };
const td = { padding: "0.5rem 0.6rem", borderBottom: `1px solid ${GRID}` };
const tdNum = { ...td, textAlign: "right" as const, fontVariantNumeric: "tabular-nums" as const };

function RegionTable() {
  return (
    <div style={{ overflowX: "auto", margin: "1.5rem 0 0.5rem" }}>
      <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.92rem" }}>
        <thead>
          <tr>
            <th style={th}>Region</th>
            <th style={{ ...th, textAlign: "right" }}>Population growth 2011–22</th>
            <th style={{ ...th, textAlign: "right" }}>Households added 2011–22</th>
            <th style={{ ...th, textAlign: "right" }}>Homes built 2012–22</th>
            <th style={{ ...th, textAlign: "right" }}>Second-hand median 2013 → 2025</th>
            <th style={{ ...th, textAlign: "right" }}>Price ÷ income 2013 → 2025</th>
          </tr>
        </thead>
        <tbody>
          {REGION_TABLE.map((r) => (
            <tr key={r.region}>
              <td style={{ ...td, fontWeight: 600 }}>{r.region}</td>
              <td style={tdNum}>+{r.pop.toFixed(1)}%</td>
              <td style={tdNum}>{r.hh.toLocaleString()}</td>
              <td style={tdNum}>{r.built.toLocaleString()}</td>
              <td style={tdNum}>{fmtK(r.p13)} → {fmtK(r.p25)} (+{Math.round((r.p25 / r.p13 - 1) * 100)}%)</td>
              <td style={tdNum}>{r.r13.toFixed(1)}× → {r.r25.toFixed(1)}×</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const SOURCES: { name: string; detail: string; url: string }[] = [
  { name: "Property Price Register", detail: "Property Services Regulatory Authority. Every residential sale, 2010 to 2 Oct 2026 (snapshot imported Oct 2026).", url: "https://www.propertypriceregister.ie/" },
  { name: "CSO FY003B", detail: "Census population by county, 2011, 2016, 2022.", url: "https://data.cso.ie/table/FY003B" },
  { name: "CSO FY011B", detail: "Census private households and average household size by county, 2011, 2016, 2022.", url: "https://data.cso.ie/table/FY011B" },
  { name: "CSO PEA01", detail: "Population estimates (April), 2010–2026.", url: "https://data.cso.ie/table/PEA01" },
  { name: "CSO PEA03", detail: "Estimated migration (year to April), 2010–2026.", url: "https://data.cso.ie/table/PEA03" },
  { name: "CSO RAA02", detail: "County incomes: disposable household income per person, 2010–2024.", url: "https://data.cso.ie/table/RAA02" },
  { name: "CSO EHA05", detail: "Average annual earnings per employee, 2010–2025.", url: "https://data.cso.ie/table/EHA05" },
  { name: "CSO GPIIA05", detail: "Geographical Profiles of Income in Ireland 2022: median household income by county.", url: "https://data.cso.ie/table/GPIIA05" },
  { name: "CSO GPIIA02", detail: "Geographical Profiles of Income in Ireland 2022: median household income by town.", url: "https://data.cso.ie/table/GPIIA02" },
  { name: "CSO IIA14", detail: "Geographical Profiles of Income in Ireland 2016: median household income by town.", url: "https://data.cso.ie/table/IIA14" },
  { name: "CSO NDA05", detail: "New dwelling completions by Local Electoral Area, 2012–2025 (summed to counties and regions; Tullamore and Skibbereen–West Cork LEAs).", url: "https://data.cso.ie/table/NDA05" },
  { name: "CSO NDA02", detail: "New dwelling completions by type (single, scheme, apartment), 2011–2025.", url: "https://data.cso.ie/table/NDA02" },
  { name: "CSO NDQ09", detail: "New dwelling completions by quarter, 2026.", url: "https://data.cso.ie/table/NDQ09" },
  { name: "CSO SAP2022T1T1TOWN22 and Census 2011/2016 small area statistics", detail: "Census town populations for Tullamore and Skibbereen.", url: "https://data.cso.ie/table/SAP2022T1T1TOWN22" },
  { name: "CSO URLIA31", detail: "Urban and Rural Life in Ireland: price-to-income ratio, 2024.", url: "https://data.cso.ie/table/URLIA31" },
  { name: "CSO HPA06", detail: "Residential Property Price Index, annual change.", url: "https://data.cso.ie/table/HPA06" },
  { name: "CSO HPA09", detail: "Residential dwelling property transactions, new and existing.", url: "https://data.cso.ie/table/HPA09" },
  { name: "Central Bank of Ireland", detail: "Mortgage measures: loan-to-income and loan-to-value limits (2015, revised 2023).", url: "https://www.centralbank.ie/financial-system/financial-stability/macro-prudential-policy/mortgage-measures" },
  { name: "European Central Bank", detail: "Key ECB interest rates (rises July 2022 – September 2023, cuts from June 2024).", url: "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html" },
  { name: "Revenue", detail: "Help to Buy incentive for buyers of new homes.", url: "https://www.revenue.ie/en/property/help-to-buy-incentive/index.aspx" },
];

export function MarketDrivers2010To2026Content() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        The <strong>Property Price Register</strong> now covers more than <strong>sixteen years</strong> of Irish home sales,
        from the bottom of the crash in 2010 to this autumn. On its own it tells you what homes sold for. Put it next to the
        CSO's figures on <strong>population</strong>, <strong>incomes</strong> and <strong>house building</strong> and it can
        answer a bigger question: <em>what is actually driving the market?</em> Is it demand, is it a lack of supply, and can
        people still afford it? We looked at the national picture, the four regions, and two towns: Tullamore and
        Skibbereen.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The headline:</strong> this is a <strong>demand-led market running into a supply wall</strong>. Since 2010
          Ireland has added <strong>971,000 people</strong>. House building collapsed to <strong>4,575 homes in 2013</strong>{" "}
          and took a decade to recover. In most years it fell well short of what population growth alone required. So the extra demand went
          into <strong>prices</strong>, not into more sales. The typical second-hand home more than doubled from its 2013 low
          (<strong>€160k → €350k</strong>) while average earnings rose <strong>46%</strong>. Prices have gone from about{" "}
          <strong>3.4×</strong> to about <strong>5.1×</strong> the typical household income, above the Central Bank's 4×
          lending limit. Affordability has worsened fastest <strong>outside Dublin</strong>.
        </p>
      </div>

      <StatCards />

      <SectionHeading>How we built this</SectionHeading>
      <p style={p}>
        For prices we used the same cleaned register as our{" "}
        <Link to="/blog/irish-property-market-health-36-months" style={link}>36-month market health report</Link>. That means
        full-market-price sales only, prices between <strong>€50,000 and €3 million</strong>, and bulk "Units 1–76"-style
        rows removed. Price levels are the <strong>median second-hand sale</strong>, so a new scheme opening in one area
        can't pass itself off as a price rise. Everything else comes from the CSO, listed in full at the end.
      </p>
      <p style={p}>
        We split the country into the <strong>four regions</strong> used across HomeIQ. They are <strong>Dublin</strong>; the{" "}
        <strong>commuter belt</strong> (Kildare, Meath, Wicklow, Louth); the counties containing the four other{" "}
        <strong>cities</strong> (Cork, Galway, Limerick, Waterford); and the <strong>rest of Ireland</strong>, the other 17
        counties. The CSO doesn't publish yearly population or household income by county, so some numbers below are census
        snapshots or estimates. We say so where they are.
      </p>

      <SectionHeading>1. The long view: prices against incomes</SectionHeading>
      <Figure label="Price and income index"
              caption={<>Median second-hand price, average annual earnings and disposable income per person, each indexed to
                2010 = 100. Price: HomeIQ analysis of the PPR. Incomes: CSO EHA05 and RAA02 (2025 not yet published for RAA02).</>}>
        <IndexChart />
      </Figure>
      <p style={p}>
        Measured from 2010, prices and incomes look roughly in step. Prices are up <strong>59%</strong>, earnings{" "}
        <strong>45%</strong>, and disposable income per person <strong>66%</strong> (to 2024). But 2010 is a misleading
        starting point. Prices were still falling out of the bubble then, and dropped another <strong>27%</strong> to a
        low of <strong>€160,000 in 2013</strong>. From that low the picture changes completely. Prices rose{" "}
        <strong>119%</strong> by 2025. Average earnings rose <strong>46%</strong>, and income per person{" "}
        <strong>66%</strong> to 2024.
      </p>
      <p style={p}>
        Incomes did not move for the first five years. Average earnings were <strong>€36,277 in 2010 and €36,457 in
        2015</strong>. They only started rising meaningfully in 2017, and fastest after 2020 (+24% from 2020 to 2025). Prices started
        rising in 2014, about three years before wages did. That timing is the first clue: the early recovery was not driven by
        people earning more.
      </p>

      <SectionHeading>2. Demand: a population boom, powered by migration</SectionHeading>
      <Figure label="Net migration"
              caption={<>Net migration into Ireland, year to April. Source: CSO PEA03.</>}>
        <MigrationChart />
      </Figure>
      <p style={p}>
        In 2010 and 2011, about <strong>27,000 more people left Ireland than arrived</strong> each year. Net inflows
        returned in 2015 and have not stopped since. They ran at around <strong>44,000 a year</strong> before Covid and
        jumped to <strong>77,700 and 79,300</strong> in 2023 and 2024, partly reflecting arrivals from Ukraine. They have
        eased to <strong>48,100</strong> in the year to April 2026. Add natural increase (births minus deaths) and the
        population went from <strong>4.55 million in 2010 to 5.53 million in 2026</strong>, about <strong>+21%</strong>. In
        2022–2024 alone it grew by roughly <strong>100,000 people a year</strong>.
      </p>
      <p style={p}>
        Most new arrivals are working-age adults, and most rent first. That pushes up rents. Higher rents then make buying
        look better value and lift prices. Population growth is only part of the demand, though. The other part is{" "}
        <strong>household formation</strong>: young adults moving out, separated couples setting up two homes, older people
        living alone. Across most of Europe average household size has fallen for decades. In Ireland it was{" "}
        <strong>2.73 in 2011, 2.75 in 2016 and 2.74 in 2022</strong>. It stood still, which is unusual. Households that
        would have formed didn't, because there was nowhere to put them. That is <strong>hidden demand</strong>. It doesn't
        show up in sales, but it is still waiting for homes.
      </p>

      <SectionHeading>3. Supply: building recovered, but from almost nothing</SectionHeading>
      <Figure label="Completions vs need"
              caption={<>New homes completed each year (CSO NDA05) against the number needed to house that year's population
                growth at the average household size of 2.74 people (CSO PEA01 and Census). This is a floor on demand. It
                ignores replacing old homes, vacancy, second homes, and any fall in household size.</>}>
        <SupplyNeedChart />
      </Figure>
      <p style={p}>
        After the crash Ireland nearly stopped building. Completions bottomed at <strong>4,575 in 2013</strong>. They rose
        steadily to about <strong>21,000 in 2019</strong>, stalled through Covid, then climbed to <strong>36,215 in
        2025</strong>, eight times the low point. 2026 is on a similar pace, with <strong>16,679</strong> in the first half.
      </p>
      <p style={p}>
        Measured against population growth, the recovery came late. Between 2014 and 2019 the population needed around{" "}
        <strong>11,000–27,000 extra homes a year</strong>. From 2014 to 2017 building delivered only about half of that. In 2022–2024, with ~100,000 more people a year, Ireland needed about{" "}
        <strong>36,000–40,000 homes a year</strong> and built 29,600–32,500. Over the whole period 2012–2025, population
        growth alone called for about <strong>323,000 homes</strong>. <strong>254,000</strong> were built, a gap of roughly{" "}
        <strong>70,000</strong>. That is before replacing any old homes, and before any of the hidden households from the
        last section.
      </p>
      <p style={p}>
        There is one hopeful sign. In <strong>2025</strong>, completions (36,215) clearly exceeded the homes needed for that
        year's population growth (about 28,600). That has happened in only one other year in the series, 2021, when Covid
        cut migration. With migration easing, the latest figures suggest building is finally <strong>starting to eat into
        the backlog</strong>.
      </p>
      <p style={p}>
        One caveat needs saying clearly: <strong>sales are not supply</strong>. A completed home only appears on the Property
        Price Register if it is sold to a private buyer. Of 2025's completions, <strong>5,874</strong> were one-off houses
        people built for themselves, and many others were social, cost-rental or build-to-rent homes sold in bulk or never
        sold at all. That's why the register's <strong>13,266</strong> clean new-build sales in 2025 are far below the CSO's
        36,215 completions.
      </p>

      <Figure label="PPR sales by year"
              caption={<>Residential sales on the Property Price Register each year after cleaning, second-hand vs new build.
                *2026 is a partial year (to early October), and late filings will add to it.</>}>
        <SalesChart />
      </Figure>
      <p style={p}>
        The register shows how the market responded. Sales roughly <strong>tripled</strong>, from about 17,000 in 2011 to
        58,000–59,000 in 2022 and 2023, and have <strong>flat-lined since</strong>. New builds grew from{" "}
        <strong>12% of sales in 2013 to 23% in 2025</strong>. The more telling line is <strong>second-hand sales</strong>.
        They peaked at about <strong>48,500 in 2022</strong> and have since slipped to about <strong>44,700</strong>. Fewer
        existing owners are putting their homes up for sale. Moving is expensive, and the next home is hard to find, so
        people stay put. Prices kept rising through all of this, by <strong>8.5% in 2024 and 7.5% in 2025</strong> on the
        CSO's index. When prices rise faster while sales stay flat, buyers are competing for a fixed number of homes.
      </p>

      <SectionHeading>4. Affordability: prices have outrun incomes</SectionHeading>
      <Figure label="Price-to-income ratio"
              caption={<>Estimated ratio of the national median second-hand price to median gross household income. The CSO's
                2022 median household income (€60,123, GPIIA05) is moved back and forward with average earnings growth (EHA05),
                so years other than 2022 are estimates.</>}>
        <AffordabilityChart />
      </Figure>
      <p style={p}>
        The ratio of price to household income is the simplest affordability test. On our estimate it fell from{" "}
        <strong>4.6 in 2010 to 3.4 in 2013</strong>. Homes were cheap relative to incomes, but almost nobody could get a
        mortgage. It rose to about <strong>4.3 by 2017–2019</strong>, dipped slightly in 2020, and then climbed again to
        about <strong>5.1 in 2025</strong>. The CSO's own measure for 2024, which uses a different income basis, puts the
        national ratio at <strong>4.7</strong>. Using disposable income per person instead of earnings gives about 4.75 for
        2025. Whichever measure you take, the typical home now costs <strong>more than the 4× income</strong> the Central
        Bank lets a first-time buyer borrow.
      </p>
      <p style={p}>
        That lending limit matters for reading this chart. The Central Bank's mortgage rules came in in{" "}
        <strong>2015</strong> and capped most loans at 3.5× income. Look at what happened next. By 2017 the ratio
        had levelled off near 4.3, and it stayed there until 2020. Banks could only lend a fixed multiple of
        income, so incomes effectively capped prices. The ratio started rising again after 2020. Several things happened at
        once. Savings built up during Covid and became deposits. More buyers were two-income households. The limit for
        first-time buyers rose to <strong>4×</strong> in <strong>2023</strong>. Government help for new-build buyers grew,
        such as <strong>Help to Buy</strong>. Each of these lets buyers pay more on the same income. When the number of homes
        can't grow quickly, that extra money goes into higher prices.
      </p>
      <p style={p}>
        Interest rates show the same thing working in reverse. The ECB raised rates from <strong>July 2022 to September
        2023</strong>. Price growth fell from <strong>12.3% in 2022 to 3.1% in 2023</strong>. When rates started falling
        in mid-2024, it picked back up to 8.5%. Higher borrowing costs cut what buyers could pay, and prices
        reacted within a year.
      </p>

      <SectionHeading>5. The regions: the squeeze has spread outward</SectionHeading>
      <RegionTable />
      <p style={{ fontSize: "0.9rem", color: INK_MUTED, marginBottom: "1.5rem" }}>
        Population and households: Census 2011 and 2022 (CSO FY003B, FY011B). Homes built: CSO NDA05. Prices: PPR second-hand
        medians. Price ÷ income: estimated (see method notes).
      </p>
      <p style={p}>
        The <strong>commuter belt grew fastest</strong>: its population rose 16.8% between the 2011 and 2022 censuses, against
        14.5% in Dublin. It is also one of two regions where building kept pace with new households (33,900 homes for 34,700 new
        households). That is consistent with what we found in our{" "}
        <Link to="/blog/irish-property-market-health-36-months" style={link}>36-month report</Link>: two sales in five in
        Kildare are now new builds. Dublin roughly matched its new households too (50,600 homes for 52,000). The{" "}
        <strong>cities and the rest of Ireland</strong> added far more households than homes. The gap was filled by the
        large number of homes left empty after the crash, and that spare stock has now largely been used up.
      </p>
      <Figure label="Regional price-to-income ratio"
              caption={<>Estimated price-to-income ratio by region. Each region's 2022 median household income (from county
                figures in CSO GPIIA05, weighted by households) is moved with that region's disposable income per person
                (CSO RAA02). Dashed line: 4× income. Estimates, not official figures.</>}>
        <RegionAffordabilityChart />
      </Figure>
      <p style={p}>
        <strong>Dublin is still the least affordable</strong>, at about <strong>5.5× income</strong>. But its ratio is barely
        higher than in 2013 (5.1×), because Dublin incomes have grown faster than those in the cities or rural counties. The real change is everywhere
        else. Since 2013 the ratio has gone from <strong>3.4× to 4.3×</strong> in the commuter belt and from{" "}
        <strong>3.4× to 4.55×</strong> in the city counties. In the <strong>rest of Ireland</strong> it rose from{" "}
        <strong>2.8× to 3.9×</strong>, a 40% worsening in affordability and the largest of any region. Second-hand
        prices there rose <strong>127%</strong> from the 2013 low, more than in Dublin (101%), even though their population
        grew the least.
      </p>
      <p style={p}>
        This is the <strong>ripple effect</strong>. When Dublin gets too expensive, buyers move to the next cheapest place
        they can reach: first the commuter counties, then the cities, then the towns beyond. Remote working since 2020 has
        stretched how far that can go. Local wages in Offaly or West Cork haven't changed much. Buyers bringing Dublin
        salaries and savings have, and they are bidding against local buyers for the same homes.
      </p>

      <SectionHeading>6. Two towns up close: Tullamore and Skibbereen</SectionHeading>
      <Figure label="Towns"
              caption={<>Median second-hand price in Tullamore (yearly) and Skibbereen (3-year rolling, because single years
                have only 21–80 sales), against the national median. Town sales matched by address on the PPR.</>}>
        <TownsChart />
      </Figure>
      <p style={p}>
        <strong>Tullamore</strong> (population <strong>15,598</strong> in 2022, up 8.6% since 2011) is a good example of a
        midlands commuter town. Prices bottomed at <strong>€120,000 in 2013</strong> and stayed flat at around €128,000
        until 2016. The recovery reached Tullamore about three years after Dublin. Then it accelerated, to{" "}
        <strong>€280,000 in 2025</strong> (+133% from the low) and about €295,000 so far in 2026. Building there had almost
        stopped. The Tullamore electoral area completed only <strong>16–39 homes a year</strong> from 2012 to 2018, rising
        to <strong>221–283 a year</strong> in 2022–2024 before dropping to 100 in 2025. The CSO puts the town's median
        household income at <strong>€38,423 in 2016 and €53,484 in 2022</strong>. On those figures the price-to-income ratio
        went from about <strong>3.3× in 2016 to 4.1× in 2022</strong>, and on our estimate to about 4.6× by 2025.
      </p>
      <p style={p}>
        <strong>Skibbereen</strong> (population <strong>2,903</strong>) shows a different pattern. Its median household
        income is low, <strong>€37,096</strong> in 2022, yet its typical second-hand home now costs around{" "}
        <strong>€285,000</strong>, close to the national figure. That is a ratio of about <strong>6.7× local income</strong>,
        higher than Dublin. Local wages can't explain that. Prices are set by buyers whose money was earned somewhere else:
        holiday-home buyers, retirees, returning emigrants and remote workers. Skibbereen's prices jumped{" "}
        <strong>15% in the 2021 rolling figure alone</strong>, as remote working took off. For local first-time buyers,
        this is affordability at its worst. The town's buyers are competing with people who earn their incomes
        elsewhere. (Skibbereen's sample is small. Treat its figures as an indication, not a precise measure.)
      </p>

      <SectionHeading>So what is the data telling us?</SectionHeading>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem", margin: "1rem 0 1.5rem" }}>
        <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#1e40af", marginTop: 0, marginBottom: "0.6rem" }}>What's driving it</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>Demand, mostly from population growth.</strong> 971,000 more people since 2010, more than half of it net migration since 2015.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Supply that couldn't respond quickly.</strong> A decade of under-building left a gap of about 70,000 homes, plus households that never got to form.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Prices doing the adjusting.</strong> Sales volumes flat-lined after 2022 while prices kept rising, so buyers were competing for a fixed number of homes.</li>
            <li><strong>Credit setting the ceiling.</strong> Lending limits tie prices to incomes. Growth is fastest when those limits loosen or rates fall.</li>
          </ul>
        </div>
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#b91c1c", marginTop: 0, marginBottom: "0.6rem" }}>Is it affordable?</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>Less so every year since 2020.</strong> About 5× household income nationally, above the 4× lending limit.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Worst in Dublin, worsening fastest elsewhere.</strong> Rural counties went from 2.8× to 3.9× income.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Towns depend on outside money.</strong> Skibbereen's prices are 6.7× local income.</li>
            <li><strong>Not a credit bubble.</strong> Unlike 2006, loans are capped at a multiple of income, so the strain shows up as larger deposits and fewer buyers who qualify, not as risky lending.</li>
          </ul>
        </div>
      </div>
      <p style={p}>
        Our reading is that Ireland's property market is <strong>demand-driven and supply-constrained</strong>. The
        increase in prices since 2013 is about what you'd expect when a fast-growing population meets housing supply that
        takes years to respond. The register gives no sign that prices are being pushed up by easy credit, as they were
        before 2008. Lending rules limit how far prices can run ahead of incomes. Within those limits, any extra buying
        power has gone into higher prices.
      </p>
      <p style={{ marginBottom: "2rem" }}>
        What would change the picture? <strong>Supply has to stay ahead of demand for several years running.</strong>{" "}
        2025 was the first clear year of that, helped by migration easing from its peak. If completions hold above 35,000 a
        year while population growth stays near today's ~67,000, the register should show it in two ways. More second-hand
        homes would come up for sale, and the price-to-income ratio would stop rising. Those are the two things to watch in
        next year's data.
      </p>

      <SectionHeading>What this data can and can't tell us</SectionHeading>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.5rem" }}><strong>Sales are not supply.</strong> The register records sales to private buyers, not completions. Social, cost-rental, build-to-rent and self-built homes are mostly missing, and bulk sales are excluded by our cleaning.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Medians reflect the mix of what sold.</strong> The register doesn't record size or type, so a year with more apartments or more large houses shifts the median. We use second-hand homes only to reduce this.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Starting year matters.</strong> 2010 was mid-crash, so "since 2010" and "since the 2013 low" give very different growth figures. We show both.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Household income is estimated outside 2022.</strong> The CSO publishes median household income for 2022 only (and 2016 for towns, on a slightly different basis). Other years are moved with earnings or income-per-person growth, so treat the ratios as estimates. Different income measures give answers about ±0.3× apart.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>"Homes needed" is a floor.</strong> Dividing population growth by 2.74 ignores replacing old homes, empty homes and second homes, and assumes household size doesn't fall. The large stock of vacant homes after the crash also met some demand in the early 2010s.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Regional population is census-only.</strong> The CSO has no yearly county population series, so regional demand compares 2011 and 2022.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Town figures are small samples.</strong> Towns are matched by address text, Skibbereen has only 21–80 second-hand sales a year, and the Skibbereen–West Cork electoral area is much larger than the town.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>2026 is incomplete.</strong> Sales run to early October and recent months fill in as late filings arrive.</li>
        <li><strong>Lining up trends is not proof.</strong> We use standard economic reasoning to explain why these series move together, but this is not a formal model.</li>
      </ul>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>See how your area compares.</strong> Search any address, Eircode or town to see every recorded sale nearby
          with price trends since 2010, or get an instant estimate for your own home.{" "}
          <Link to="/" style={link}>Search sold prices →</Link>{" · "}
          <Link to="/valuation" style={link}>Value your property →</Link>
        </p>
      </div>

      <SectionHeading>Sources</SectionHeading>
      <ol style={{ paddingLeft: "1.25rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
        {SOURCES.map((s) => (
          <li key={s.name + s.detail} style={{ marginBottom: "0.4rem" }}>
            <a href={s.url} style={link} target="_blank" rel="noopener noreferrer">{s.name}</a>: {s.detail}
          </li>
        ))}
      </ol>
      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "1.5rem", fontStyle: "italic" }}>
        Price analysis by HomeIQ from the Property Services Regulatory Authority's Property Price Register. CSO data is used
        under the Creative Commons Attribution 4.0 licence (Source: CSO), retrieved 23 October 2026. Regional and yearly
        household incomes, price-to-income ratios and "homes needed" are HomeIQ estimates built from CSO figures, not
        official statistics. This is market analysis, not financial advice.
      </p>
    </div>
  );
}
