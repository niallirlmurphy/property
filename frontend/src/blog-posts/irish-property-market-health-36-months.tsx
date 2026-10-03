import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ analysis of the Property Price Register, sales dated
// 1 Oct 2023 – 25 Sep 2026 (PPR snapshot of 30 Sep 2026, imported 3 Oct 2026).
// Raw query output: docs/blog_market_health_36m_raw.json.
//
// Outlier stripping (same rules as the /heatmap price index):
//   • full-market-price sales only (PPR "not full market price" = No)
//   • €50k ≤ price ≤ €3m (drops share transfers / parking and trophy/portfolio deals)
//   • bulk unit-range rows removed ("Apt 1-10 …", "Units 1 to 76 …")
//   ⇒ 166,166 of 178,994 rows kept (92.8%).
// Price growth is measured on SECOND-HAND (resale) homes only, so a new scheme
// completing in one area can't masquerade as a price change. New-build prices are
// shown VAT-inclusive (PPR records them ex-VAT; grossed up at 13.5%).
// "Years" are Oct–Sep: Y1 = Oct 2023–Sep 2024, Y2 = Oct 2024–Sep 2025,
// Y3 = Oct 2025–Sep 2026. PPR filings lag completions, so Jul–Sep 2026 volumes
// are provisional; volume comparisons use Oct–Jun in each year.
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

// [month, total clean sales, of which new-build, resale median €k, resale average €k]
const MONTHLY: [string, number, number, number, number][] = [
  ["2023-10", 5199, 808, 300.0, 365.7], ["2023-11", 5271, 1196, 295.8, 350.8], ["2023-12", 6522, 1801, 295.0, 361.5],
  ["2024-01", 3185, 437, 311.5, 370.5], ["2024-02", 3923, 648, 300.0, 362.3], ["2024-03", 4089, 684, 303.5, 365.8],
  ["2024-04", 4008, 739, 295.0, 348.8], ["2024-05", 4842, 907, 305.0, 355.4], ["2024-06", 4517, 1136, 320.0, 377.7],
  ["2024-07", 5256, 1199, 322.0, 391.3], ["2024-08", 4578, 736, 320.0, 396.2], ["2024-09", 4788, 887, 330.0, 398.7],
  ["2024-10", 5845, 1350, 333.0, 400.2], ["2024-11", 5204, 1156, 330.0, 393.6], ["2024-12", 6380, 1815, 325.0, 392.2],
  ["2025-01", 3334, 528, 340.0, 415.1], ["2025-02", 3817, 668, 335.0, 397.9], ["2025-03", 4183, 864, 335.0, 396.7],
  ["2025-04", 4332, 962, 330.0, 398.2], ["2025-05", 4798, 1149, 335.0, 394.7], ["2025-06", 4603, 1081, 346.0, 406.2],
  ["2025-07", 5515, 1247, 352.5, 417.5], ["2025-08", 4661, 954, 360.0, 418.1], ["2025-09", 5282, 1142, 356.5, 421.3],
  ["2025-10", 5529, 1144, 351.6, 412.8], ["2025-11", 4950, 1275, 360.0, 430.4], ["2025-12", 6926, 2252, 355.0, 422.1],
  ["2026-01", 3369, 688, 371.0, 437.8], ["2026-02", 3892, 890, 354.3, 419.5], ["2026-03", 4584, 1068, 350.0, 412.9],
  ["2026-04", 4293, 1053, 350.0, 411.8], ["2026-05", 4545, 1165, 355.0, 415.7], ["2026-06", 4551, 1163, 365.0, 427.7],
  ["2026-07", 3855, 938, 365.0, 430.7], ["2026-08", 3120, 732, 375.0, 445.3], ["2026-09", 2420, 542, 375.0, 438.2],
];
const PROVISIONAL_FROM = "2026-07";
const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthLabel = (m: string) => `${MONTH_ABBR[Number(m.slice(5)) - 1]} ${m.slice(2, 4)}`;

// Year-on-year change in the monthly resale median (month vs same month a year earlier).
const YOY = MONTHLY.slice(12).map(([m, , , med], i) => ({ m, pct: (med / MONTHLY[i][3] - 1) * 100 }));

// Resale median (€k) by Oct–Sep year and region.
const REGIONS = [
  { name: "Dublin", y: [437, 475, 490] },
  { name: "Commuter belt", sub: "Kildare, Meath, Wicklow, Louth", y: [335, 365, 395] },
  { name: "Cork, Galway, Limerick, Waterford", y: [281, 310.25, 330] },
  { name: "Rest of Ireland", y: [215, 240, 260] },
];

// Share of resale transactions by price band, per Oct–Sep year (%).
const BANDS = [
  { year: "Oct 23–Sep 24", v: [47.4, 33.9, 15.8, 3.0] },
  { year: "Oct 24–Sep 25", v: [39.9, 36.6, 19.9, 3.7] },
  { year: "Oct 25–Sep 26", v: [35.5, 39.1, 21.3, 4.1] },
];
const BAND_LABELS = ["Under €300k", "€300k–€500k", "€500k–€1m", "€1m+"];
const BAND_COLORS = [AQUA, BLUE, PURPLE, ORANGE];

// Dublin postal districts: resale median Y1 → Y3 (€k), ≥100 resales in each year.
const DISTRICTS: { d: string; area: string; m1: number; m3: number }[] = [
  { d: "D1", area: "North inner city", m1: 315, m3: 380 },
  { d: "D20", area: "Palmerstown, Chapelizod", m1: 395, m3: 475 },
  { d: "D14", area: "Dundrum, Churchtown", m1: 650, m3: 750 },
  { d: "D3", area: "Clontarf, Fairview, Marino", m1: 460, m3: 530 },
  { d: "D15", area: "Blanchardstown, Castleknock", m1: 365, m3: 420 },
  { d: "D24", area: "Tallaght", m1: 345, m3: 395 },
  { d: "D12", area: "Crumlin, Walkinstown", m1: 420, m3: 480 },
  { d: "D22", area: "Clondalkin", m1: 323.5, m3: 367.5 },
  { d: "D16", area: "Ballinteer, Rathfarnham", m1: 570, m3: 647 },
  { d: "D4", area: "Ballsbridge, Sandymount", m1: 600, m3: 680 },
  { d: "D8", area: "Inchicore, Kilmainham", m1: 372, m3: 417.5 },
  { d: "D11", area: "Finglas", m1: 312.5, m3: 350 },
  { d: "D7", area: "Phibsborough, Cabra", m1: 430.5, m3: 482 },
  { d: "D5", area: "Artane, Raheny", m1: 467.5, m3: 523 },
  { d: "D6", area: "Ranelagh, Rathmines", m1: 680, m3: 760 },
  { d: "D10", area: "Ballyfermot", m1: 300, m3: 335 },
  { d: "D18", area: "Foxrock, Sandyford, Cabinteely", m1: 517.5, m3: 573 },
  { d: "D17", area: "Coolock, Darndale", m1: 300.5, m3: 331 },
  { d: "D9", area: "Drumcondra, Santry, Whitehall", m1: 450, m3: 490 },
  { d: "D6W", area: "Terenure, Templeogue", m1: 670, m3: 720 },
  { d: "D13", area: "Howth, Sutton, Baldoyle", m1: 480, m3: 500 },
  { d: "D2", area: "South inner city", m1: 470, m3: 470 },
];

// New-build share of all clean sales, Oct 2023–Sep 2026 (top 12 counties by share
// among those with 2,500+ sales), with median prices (€k, new VAT-inclusive).
const NEW_SHARE = [
  { county: "Kildare", share: 40.2, newMed: 450, resMed: 390 },
  { county: "Wicklow", share: 37.7, newMed: 480, resMed: 425 },
  { county: "Louth", share: 36.8, newMed: 392, resMed: 275 },
  { county: "Meath", share: 34.5, newMed: 425, resMed: 350 },
  { county: "Laois", share: 34.5, newMed: 375, resMed: 247 },
  { county: "Cork", share: 28.3, newMed: 415, resMed: 320 },
  { county: "Kilkenny", share: 26.1, newMed: 392, resMed: 280 },
  { county: "Waterford", share: 24.0, newMed: 370, resMed: 250 },
  { county: "Westmeath", share: 21.1, newMed: 375, resMed: 275 },
  { county: "Wexford", share: 20.3, newMed: 350, resMed: 270 },
  { county: "Dublin", share: 19.9, newMed: 500, resMed: 465 },
  { county: "Galway", share: 18.2, newMed: 440, resMed: 326 },
];

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function StatCards() {
  const cards = [
    { big: "+17%", small: "resale median, Y1 → Y3 (€307.5k → €360k)" },
    { big: "+5–6%", small: "current annual growth, down from 10–12%" },
    { big: "≈ flat", small: "sales volume (Oct–Jun: 41.6k → 42.6k)" },
    { big: "1 in 4", small: "sales now a new build (was 1 in 5)" },
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

// --- Chart 1: monthly sales volume, resale + new build stacked -----------------
function VolumeChart() {
  const W = 720, H = 320, padL = 48, padR = 12, padT = 20, padB = 44;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 7500;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const step = plotW / MONTHLY.length;
  const barW = step * 0.72;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Stacked bar chart of monthly residential sales from October 2023 to September 2026, split into second-hand and new-build. Volumes run between about 3,200 and 6,900 a month with a December peak each year driven by new-build completions; the final three months are provisional because of PPR filing lag.">
        {[0, 2000, 4000, 6000].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g.toLocaleString()}</text>
          </g>
        ))}
        {MONTHLY.map(([m, n, nNew], i) => {
          const x = padL + i * step + (step - barW) / 2;
          const prov = m >= PROVISIONAL_FROM;
          return (
            <g key={m} opacity={prov ? 0.45 : 1}>
              <rect x={x} y={y(n - nNew)} width={barW} height={y(0) - y(n - nNew)} fill={BLUE}>
                <title>{`${monthLabel(m)}: ${(n - nNew).toLocaleString()} second-hand`}</title>
              </rect>
              <rect x={x} y={y(n)} width={barW} height={y(n - nNew) - y(n)} fill={ORANGE}>
                <title>{`${monthLabel(m)}: ${nNew.toLocaleString()} new build${prov ? " (provisional)" : ""}`}</title>
              </rect>
              {(m.endsWith("-01") || m === "2023-10") && (
                <text x={x + barW / 2} y={H - padB + 16} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{monthLabel(m)}</text>
              )}
            </g>
          );
        })}
        <text x={padL + 33 * step + step * 1.5} y={y(4300)} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>provisional</text>
      </svg>
      <Legend items={[{ label: "Second-hand", color: BLUE }, { label: "New build", color: ORANGE }]} />
    </>
  );
}

// --- Line chart helper ---------------------------------------------------------
function LineChart({ series, lo, hi, ticks, fmt, aria, height = 300, zeroLine }: {
  series: { label: string; color: string; values: { m: string; v: number }[]; dashed?: boolean }[];
  lo: number; hi: number; ticks: number[]; fmt: (v: number) => string; aria: string; height?: number; zeroLine?: boolean;
}) {
  const W = 720, H = height, padL = 56, padR = 16, padT = 20, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const all = series[0].values.map((p) => p.m);
  const x = (m: string) => padL + (all.indexOf(m) / (all.length - 1)) * plotW;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={aria} style={svgStyle}>
      {ticks.map((g) => (
        <g key={g}>
          <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={zeroLine && g === 0 ? NEUTRAL : GRID} />
          <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{fmt(g)}</text>
        </g>
      ))}
      {all.filter((m) => m.endsWith("-01") || m === all[0]).map((m) => (
        <text key={m} x={x(m)} y={H - padB + 18} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{monthLabel(m)}</text>
      ))}
      {series.map((s) => (
        <g key={s.label}>
          <polyline fill="none" stroke={s.color} strokeWidth={2.4} strokeDasharray={s.dashed ? "6 4" : undefined}
                    points={s.values.map((p) => `${x(p.m)},${y(p.v)}`).join(" ")} />
          {s.values.map((p) => (
            <circle key={p.m} cx={x(p.m)} cy={y(p.v)} r={2.6} fill={s.color}>
              <title>{`${monthLabel(p.m)} — ${s.label}: ${fmt(p.v)}`}</title>
            </circle>
          ))}
        </g>
      ))}
    </svg>
  );
}

function PriceChart() {
  return (
    <>
      <LineChart
        lo={250} hi={475} ticks={[250, 300, 350, 400, 450]} fmt={(v) => `€${Math.round(v)}k`}
        aria="Line chart of the monthly median and average second-hand sale price in Ireland, October 2023 to September 2026. The median rises from about 300 thousand euro to 375 thousand; the average from about 366 thousand to 438 thousand, staying roughly 60 to 70 thousand above the median throughout."
        series={[
          { label: "Average", color: ORANGE, values: MONTHLY.map(([m, , , , avg]) => ({ m, v: avg })) },
          { label: "Median", color: BLUE, values: MONTHLY.map(([m, , , med]) => ({ m, v: med })) },
        ]}
      />
      <Legend items={[{ label: "Median second-hand price", color: BLUE }, { label: "Average second-hand price", color: ORANGE }]} />
    </>
  );
}

function YoyChart() {
  const W = 720, H = 280, padL = 48, padR = 12, padT = 24, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 14;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const step = plotW / YOY.length;
  const barW = step * 0.7;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
         aria-label="Bar chart of year-on-year change in the monthly median second-hand price, October 2024 to September 2026. Growth ran at 8 to 12.5 percent through to September 2025, then slowed to between 3.5 and 6 percent for most of 2026, apart from 9 percent in November 2025 to January 2026.">
      {[0, 4, 8, 12].map((g) => (
        <g key={g}>
          <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={g === 0 ? NEUTRAL : GRID} />
          <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}%</text>
        </g>
      ))}
      {YOY.map(({ m, pct }, i) => {
        const x = padL + i * step + (step - barW) / 2;
        const second = m >= "2025-10";
        return (
          <g key={m}>
            <rect x={x} y={y(pct)} width={barW} height={y(0) - y(pct)} rx={2} fill={second ? AQUA : BLUE} opacity={0.85}>
              <title>{`${monthLabel(m)}: ${pct >= 0 ? "+" : ""}${pct.toFixed(1)}% vs ${monthLabel(MONTHLY[i][0])}`}</title>
            </rect>
            {(m.endsWith("-01") || m === "2024-10") && (
              <text x={x + barW / 2} y={H - padB + 16} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{monthLabel(m)}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// --- Chart: regional resale medians by year ------------------------------------
function RegionChart() {
  const W = 720, H = 330, padL = 52, padR = 12, padT = 28, padB = 64;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 550;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const groupW = plotW / REGIONS.length;
  const barW = groupW * 0.22;
  const colors = [NEUTRAL, BLUE, AQUA];
  const shortNames = ["Dublin", "Commuter belt", "Cork/Galway/Lim./Wat.", "Rest of Ireland"];
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Grouped bar chart of median second-hand price by region for each of the three years. Dublin 437 to 475 to 490 thousand euro, up 12 percent over two years; commuter belt 335 to 365 to 395 thousand, up 18 percent; Cork, Galway, Limerick and Waterford 281 to 310 to 330 thousand, up 17 percent; rest of Ireland 215 to 240 to 260 thousand, up 21 percent.">
        {[0, 100, 200, 300, 400, 500].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>€{g}k</text>
          </g>
        ))}
        {REGIONS.map((r, gi) => {
          const cx = padL + gi * groupW + groupW / 2;
          const growth = (r.y[2] / r.y[0] - 1) * 100;
          return (
            <g key={r.name}>
              {r.y.map((v, k) => {
                const bx = cx + (k - 1.5) * barW + k * 3 - 3;
                return (
                  <rect key={k} x={bx} y={y(v)} width={barW} height={y(0) - y(v)} rx={3} fill={colors[k]} opacity={0.9}>
                    <title>{`${r.name}, ${BANDS[k].year}: €${Math.round(v)}k`}</title>
                  </rect>
                );
              })}
              <text x={cx} y={y(r.y[2]) - 10} textAnchor="middle" fontSize={12.5} fontWeight={700} fill={INK}>+{growth.toFixed(0)}%</text>
              <text x={cx} y={H - padB + 20} textAnchor="middle" fontSize={11.5} fontWeight={600} fill={INK}>{shortNames[gi]}</text>
              <text x={cx} y={H - padB + 37} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>€{r.y[0]}k → €{Math.round(r.y[2])}k</text>
            </g>
          );
        })}
      </svg>
      <Legend items={BANDS.map((b, k) => ({ label: b.year, color: colors[k] }))} />
    </>
  );
}

// --- Chart: price-band mix (100% stacked horizontal bars) -----------------------
function BandChart() {
  const W = 720, H = 200, padL = 110, padR = 16, padT = 16, padB = 16;
  const plotW = W - padL - padR;
  const rowH = (H - padT - padB) / BANDS.length;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
           aria-label="Stacked bars showing the share of second-hand sales in each price band per year. Under 300 thousand euro fell from 47 percent to 40 percent to 35 percent. 300 to 500 thousand rose from 34 to 39 percent; 500 thousand to 1 million from 16 to 21 percent; over 1 million from 3.0 to 4.1 percent.">
        {BANDS.map((b, i) => {
          let acc = 0;
          const top = padT + i * rowH + rowH * 0.18;
          return (
            <g key={b.year}>
              <text x={padL - 10} y={top + rowH * 0.36} textAnchor="end" fontSize={11.5} fill={INK}>{b.year}</text>
              {b.v.map((v, k) => {
                const x = padL + (acc / 100) * plotW;
                acc += v;
                const w = (v / 100) * plotW;
                return (
                  <g key={k}>
                    <rect x={x} y={top} width={w} height={rowH * 0.64} fill={BAND_COLORS[k]} opacity={0.88}>
                      <title>{`${b.year}: ${BAND_LABELS[k]} ${v}%`}</title>
                    </rect>
                    {w > 40 && <text x={x + w / 2} y={top + rowH * 0.38} textAnchor="middle" fontSize={11} fontWeight={600} fill="#fff">{v.toFixed(1)}%</text>}
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <Legend items={BAND_LABELS.map((l, k) => ({ label: l, color: BAND_COLORS[k] }))} />
    </>
  );
}

// --- Chart: Dublin districts, two-year resale median growth --------------------
function DistrictChart() {
  const rows = DISTRICTS.map((r) => ({ ...r, g: (r.m3 / r.m1 - 1) * 100 }));
  const W = 720, rowH = 22, padL = 230, padR = 120, padT = 14;
  const H = padT * 2 + rows.length * rowH;
  const plotW = W - padL - padR;
  const hi = 22;
  const x = (v: number) => padL + (v / hi) * plotW;
  const dublinAvg = (490 / 437 - 1) * 100;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
         aria-label="Horizontal bars of two-year growth in the median second-hand price by Dublin postal district, October 2023 to September 2024 versus October 2025 to September 2026. Fastest: Dublin 1 and Dublin 20 at about 20 percent, then Dublin 14, 3 and 15 at about 15 percent. Slowest: Dublin 6W at 7 percent, Dublin 13 at 4 percent and Dublin 2 flat.">
      <line x1={x(dublinAvg)} x2={x(dublinAvg)} y1={padT - 4} y2={H - padT + 4} stroke={ORANGE} strokeDasharray="5 4" />
      <text x={x(dublinAvg) + 4} y={H - 4} fontSize={10} fill={ORANGE}>Co. Dublin +{dublinAvg.toFixed(0)}%</text>
      {rows.map((r, i) => {
        const cy = padT + i * rowH;
        return (
          <g key={r.d}>
            <text x={padL - 8} y={cy + rowH * 0.66} textAnchor="end" fontSize={11} fill={INK}>
              <tspan fontWeight={700}>{r.d}</tspan> <tspan fill={INK_MUTED}>{r.area}</tspan>
            </text>
            <rect x={padL} y={cy + 4} width={Math.max(1.5, x(r.g) - padL)} height={rowH - 8} rx={3} fill={r.g >= dublinAvg ? BLUE : NEUTRAL} opacity={0.88}>
              <title>{`${r.d} ${r.area}: €${Math.round(r.m1)}k → €${Math.round(r.m3)}k (${r.g >= 0 ? "+" : ""}${r.g.toFixed(1)}%)`}</title>
            </rect>
            <text x={Math.max(x(r.g), padL) + 6} y={cy + rowH * 0.66} fontSize={10.5} fill={INK}>
              +{r.g.toFixed(1)}% <tspan fill={INK_MUTED}>· €{Math.round(r.m1)}k → €{Math.round(r.m3)}k</tspan>
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// --- Chart: new-build share by county ------------------------------------------
function NewShareChart() {
  const W = 720, rowH = 24, padL = 92, padR = 190, padT = 14;
  const H = padT * 2 + NEW_SHARE.length * rowH;
  const plotW = W - padL - padR;
  const hi = 45;
  const x = (v: number) => padL + (v / hi) * plotW;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" style={svgStyle}
         aria-label="Horizontal bars of the new-build share of all residential sales by county, October 2023 to September 2026. Kildare 40 percent, Wicklow 38, Louth 37, Meath and Laois 35, Cork 28, Kilkenny 26, Waterford 24, Westmeath 21, Wexford 20, Dublin 20, Galway 18.">
      {NEW_SHARE.map((r, i) => {
        const cy = padT + i * rowH;
        return (
          <g key={r.county}>
            <text x={padL - 8} y={cy + rowH * 0.66} textAnchor="end" fontSize={11.5} fontWeight={600} fill={INK}>{r.county}</text>
            <rect x={padL} y={cy + 4} width={x(r.share) - padL} height={rowH - 8} rx={3} fill={ORANGE} opacity={0.85}>
              <title>{`${r.county}: ${r.share}% of sales were new builds`}</title>
            </rect>
            <text x={x(r.share) + 6} y={cy + rowH * 0.66} fontSize={10.5} fill={INK}>
              {r.share.toFixed(0)}% <tspan fill={INK_MUTED}>· new €{r.newMed}k vs resale €{r.resMed}k</tspan>
            </text>
          </g>
        );
      })}
    </svg>
  );
}

const p = { marginBottom: "1.25rem" };
const link = { color: "#1d4ed8", fontWeight: 600 };

export function MarketHealth36MonthsContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Every residential sale in Ireland ends up on the <strong>Property Price Register</strong>. We took the last{" "}
        <strong>36 months</strong> of it — <strong>178,994 sales</strong> from October 2023 to September 2026 — stripped out
        the deals that distort the picture, and asked a simple question: <em>how healthy is the market?</em> Are prices still
        climbing, is activity holding up, and where is the heat — Dublin or the regions, cities or towns, old stock or new?
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The headline:</strong> prices are still rising — the typical second-hand home sold for{" "}
          <strong>€360,000</strong> in the latest 12 months, <strong>17% more</strong> than two years earlier — but growth
          has <strong>roughly halved</strong>, from 10–12% a year to <strong>5–6%</strong>. The number of sales is{" "}
          <strong>flat</strong>, the cheapest homes are disappearing from the register, and the fastest growth has moved{" "}
          <strong>out of Dublin</strong> into the commuter belt and rural Ireland. New builds now make up{" "}
          <strong>one sale in four</strong>.
        </p>
      </div>

      <StatCards />

      <SectionHeading>How we cleaned the data</SectionHeading>
      <p style={p}>
        Raw register averages are easy to misread. A multi-million-euro portfolio deal, a €15,000 transfer of a share in a family
        home, or a 76-apartment block recorded as one sale can each swing a month's figure. So, using the same rules as our{" "}
        <Link to="/heatmap" style={link}>price-growth heatmap</Link>, we kept only:
      </p>
      <ul style={{ marginBottom: "1.25rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.5rem" }}>sales the register marks as <strong>full market price</strong>;</li>
        <li style={{ marginBottom: "0.5rem" }}>prices between <strong>€50,000 and €3 million</strong>;</li>
        <li style={{ marginBottom: "0.5rem" }}>single homes — <strong>bulk "Units 1–76"-style</strong> multi-unit rows removed.</li>
      </ul>
      <p style={p}>
        That leaves <strong>166,166 sales (93%)</strong>. Two more choices matter. We measure price growth on{" "}
        <strong>second-hand homes only</strong>, because a new scheme completing in one place changes <em>what</em> sold, not
        what homes are worth. And new-build prices, which the register records excluding VAT, are shown{" "}
        <strong>including 13.5% VAT</strong> so they compare fairly with resales. "Years" below run October to September.
      </p>

      <SectionHeading>1. Activity: busy, but not getting busier</SectionHeading>
      <Figure label="Monthly sales volume"
              caption={<>Monthly residential sales after outlier removal, second-hand vs new build. The December spikes are new-build
                completions rushed through before year end. Jul–Sep 2026 (faded) are provisional: sales reach the register weeks
                or months after completion, so the latest months always look weaker than they will end up.</>}>
        <VolumeChart />
      </Figure>
      <p style={p}>
        The market clears roughly <strong>4,500–5,000 homes a month</strong>, with a sharp seasonal rhythm: a January
        trough (around 3,300) and a December peak (6,400–6,900) as developers close out the year. Comparing like with like —
        October to June in each year, which avoids the filing lag — volumes went from <strong>41,556</strong> to{" "}
        <strong>42,496</strong> (+2.3%) to <strong>42,639</strong> (+0.3%). In other words, <strong>activity has
        plateaued</strong>. That is not a sign of weak demand — it is a sign of a market rationed by supply: the number of
        homes changing hands is set by how many come up for sale, not by how many people want to buy.
      </p>

      <SectionHeading>2. Prices: still rising, but the pace has halved</SectionHeading>
      <Figure label="Median and average price"
              caption={<>Monthly median and average sale price of second-hand homes. Source: HomeIQ analysis of the Property Price
                Register, outliers removed.</>}>
        <PriceChart />
      </Figure>
      <p style={p}>
        The <strong>median second-hand price</strong> — the middle sale, half above, half below — rose from about{" "}
        <strong>€300,000</strong> in late 2023 to <strong>€375,000</strong> by summer 2026. On a full-year basis it went{" "}
        <strong>€307,525 → €340,000 → €360,000</strong>. The <strong>average</strong> sits consistently €60–70k higher
        (€370.5k → €404.2k → €423.8k), because a minority of expensive homes pulls it up; the gap between the two has been
        stable, so the rise isn't just a few big-ticket sales — it is across the board.
      </p>
      <Figure label="Year-on-year growth"
              caption={<>Year-on-year change in the monthly median second-hand price (each month vs the same month a year
                earlier). Blue: Oct 2024–Sep 2025; green: Oct 2025–Sep 2026.</>}>
        <YoyChart />
      </Figure>
      <p style={p}>
        The more important story is the <strong>rate</strong>. Through to September 2025 the median was running{" "}
        <strong>8–12.5% ahead</strong> of a year earlier, month after month. Since then it has settled at{" "}
        <strong>3.5–6%</strong>, apart from a brief winter bump. Year-on-year growth for the full latest year is{" "}
        <strong>+5.9%</strong>, down from <strong>+10.6%</strong>. That's the market finding a ceiling on what buyers can
        borrow: with Central Bank rules capping most mortgages at around four times income, prices can only outrun wages for so long. For anyone
        weighing what that means for a purchase, our <Link to="/mortgage" style={link}>mortgage calculator</Link> shows how far
        a given income stretches.
      </p>

      <SectionHeading>3. The cheaper end of the market is vanishing</SectionHeading>
      <Figure label="Price band mix"
              caption={<>Share of second-hand sales in each price band, by year (Oct–Sep).</>}>
        <BandChart />
      </Figure>
      <p style={p}>
        Two years ago, <strong>almost half (47%)</strong> of second-hand homes sold for under €300,000. Now it's{" "}
        <strong>about a third (35.5%)</strong>. The €300–500k band has become the market's centre of gravity (39%), and{" "}
        <strong>one sale in four</strong> is now €500,000 or more. Sales above €1 million have edged up from 3.0% to 4.1% —
        still rare, but growing faster than the market. For first-time buyers this is the clearest health warning in the
        data: the stock of homes within reach of a typical single or modest joint income is shrinking every year.
      </p>

      <SectionHeading>4. Dublin has cooled; the regions are doing the running</SectionHeading>
      <Figure label="Regional prices"
              caption={<>Median second-hand price by region and year, with the two-year change. The commuter belt is Kildare,
                Meath, Wicklow and Louth.</>}>
        <RegionChart />
      </Figure>
      <p style={p}>
        Over two years every region grew strongly, but the <strong>ranking is the reverse of the price level</strong>. The{" "}
        <strong>rest of Ireland</strong> — the 17 mostly rural counties — rose <strong>21%</strong> (€215k → €260k). The{" "}
        <strong>commuter belt</strong> rose <strong>18%</strong>, and the counties containing Cork, Galway, Limerick and
        Waterford <strong>17%</strong>. <strong>Dublin</strong>, the most expensive market, rose <strong>12%</strong> — and in
        the latest year by only <strong>3.2%</strong> (€475k → €490k), against <strong>8%+</strong> in the commuter belt and
        rural counties.
      </p>
      <p style={p}>
        A sharper urban-versus-rural cut tells the same story. Using Eircodes (available for three-quarters of recent sales),
        homes in the <strong>five cities</strong> — Dublin's postal districts plus Cork, Galway, Limerick and Waterford city
        routing areas — went from <strong>€380k → €420k → €430k</strong>: +10.5%, then just <strong>+2.4%</strong>. Homes in{" "}
        <strong>towns and the countryside</strong> went <strong>€275k → €300k → €320k</strong>: +9.1%, then{" "}
        <strong>+6.7%</strong>. The city premium has narrowed from 38% to 34%. Buyers priced out of the cities are moving
        outwards, and their demand is showing up in town and rural prices.
      </p>

      <SectionHeading>5. Inside Dublin: from flat to +20%</SectionHeading>
      <Figure label="Dublin districts"
              caption={<>Change in median second-hand price by Dublin postal district, Oct 2023–Sep 2024 vs Oct 2025–Sep 2026
                (two years). Only districts with at least 100 resales in each year are shown. Dashed line: Co. Dublin overall
                (+12%). Districts are labelled with their best-known areas; the boundaries are wider.</>}>
        <DistrictChart />
      </Figure>
      <p style={p}>
        The <strong>fastest-growing</strong> districts were a mix of value and quality-of-life plays. <strong>Dublin 20</strong>{" "}
        (Palmerstown, Chapelizod) and <strong>Dublin 1</strong> rose about <strong>20%</strong>, followed by{" "}
        <strong>Dublin 14</strong> (Dundrum), <strong>Dublin 3</strong> (Clontarf) and <strong>Dublin 15</strong>{" "}
        (Blanchardstown, Castleknock) at around <strong>15%</strong>. Most of the west and south-west — Tallaght (D24),
        Crumlin (D12), Clondalkin (D22) — beat the county average too, as buyers stretched to the next affordable postcode.
      </p>
      <p style={p}>
        At the other end, <strong>Dublin 13</strong> (Howth, Sutton, Baldoyle) rose only <strong>4%</strong>,{" "}
        <strong>Dublin 6W</strong> (Terenure) 7%, and <strong>Dublin 2</strong> was <strong>flat</strong> at €470k. These are
        among the most expensive or most apartment-heavy parts of the city, where buyers are hitting affordability limits first.
        One caveat: within a single district the mix of apartments and houses that happens to sell can shift from year to year,
        so treat differences of a few points as noise. For district-by-district detail, see our{" "}
        <Link to="/blog/dublin-property-prices-by-postcode-2026" style={link}>Dublin prices by postcode guide</Link> or the{" "}
        <Link to="/heatmap" style={link}>heatmap</Link>.
      </p>

      <SectionHeading>6. New builds: a growing share, built where land is cheaper</SectionHeading>
      <p style={p}>
        New homes went from <strong>19.9%</strong> of sales in the first year to <strong>22.3%</strong> and then{" "}
        <strong>24.8%</strong> — about <strong>12,900 a year</strong> on the register, and the latest year's count will rise
        further once the lagged summer filings land. New builds are not where Dublin's buyers are, though: they're concentrated in the
        commuter belt.
      </p>
      <Figure label="New-build share by county"
              caption={<>New-build share of all residential sales by county, Oct 2023–Sep 2026, for the 12 counties where new
                homes form the largest share (counties with 2,500+ sales). Medians: new build (VAT-inclusive) vs second-hand.</>}>
        <NewShareChart />
      </Figure>
      <p style={p}>
        In <strong>Kildare, two sales in every five are a new home</strong>; Wicklow, Louth, Meath and Laois all exceed a
        third. In Dublin it's one in five. New builds sell at a premium: the national new-build median (VAT-inclusive) rose from{" "}
        <strong>€408k to €450k</strong>, about <strong>25% above</strong> the second-hand median. The premium is biggest
        where the new homes are going — <strong>Louth (€392k vs €275k)</strong> and <strong>Laois (€375k vs €247k)</strong>{" "}
        — because these are modern, energy-efficient family homes being built into markets where the existing stock is older
        and cheaper. Supply is being added, but at a price point well above what the local resale market has been used to.
      </p>

      <SectionHeading>So, how healthy is it?</SectionHeading>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem", margin: "1rem 0 1.5rem" }}>
        <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#15803d", marginTop: 0, marginBottom: "0.6rem" }}>Signs of strength</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>No sign of a fall.</strong> Every region and almost every Dublin district is higher than two years ago.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Steady activity.</strong> ~56–58k clean sales a year, with no drop-off.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Broad-based growth.</strong> The median and average rose together — it's not just the top end.</li>
            <li><strong>More new supply.</strong> One sale in four is now a new home, up from one in five.</li>
          </ul>
        </div>
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#b91c1c", marginTop: 0, marginBottom: "0.6rem" }}>Signs of strain</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>Affordability ceiling.</strong> Growth halved as prices met lending limits, first in Dublin.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Shrinking entry level.</strong> Sub-€300k homes fell from 47% to 35% of resales.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Volume isn't growing.</strong> Demand outstrips what comes up for sale.</li>
            <li><strong>Displacement.</strong> The fastest growth is now in rural counties and outer suburbs — buyers are being pushed outward by price.</li>
          </ul>
        </div>
      </div>
      <p style={{ marginBottom: "2rem" }}>
        Our reading: Ireland's market is <strong>stable but stretched</strong>. It isn't overheating — the spike in growth
        has passed — and nothing in the register points to a correction. But it is a market where{" "}
        <strong>prices are being held up by scarcity</strong>, and the cost of that falls on the buyers at the bottom of the
        ladder. Watch two numbers over the coming year: whether annual growth holds around 5% or keeps sliding, and whether the
        new-build share keeps climbing. If supply keeps rising while growth eases, that's a market slowly healing.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>What's happening on your street?</strong> Search any address, Eircode or area to see every recorded sale
          nearby, with price trends over time — or get an instant estimate for your own home.{" "}
          <Link to="/" style={link}>Search sold prices →</Link>{" · "}
          <Link to="/valuation" style={link}>Value your property →</Link>
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        Source: HomeIQ analysis of the Property Services Regulatory Authority's Property Price Register, sales dated 1 October
        2023 to 25 September 2026 (register snapshot of 30 September 2026). Figures exclude non-market sales, prices outside
        €50,000–€3m and bulk multi-unit transactions. Price growth uses second-hand homes only; new-build prices include VAT
        at 13.5%. The register records sale prices, not property type or size, so medians reflect the mix of homes sold in
        each period. Recent months are provisional and will be revised as late filings arrive. This is market analysis, not
        financial advice.
      </p>
    </div>
  );
}
