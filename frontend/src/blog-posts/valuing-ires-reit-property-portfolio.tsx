import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ valuation of the IRES REIT plc residential portfolio (IRES-owned
// units only), run through the same engine that powers /valuation. Portfolio
// holdings captured from iresreit.ie on 2026-09-27 (docs/ires_reit_portfolio.md);
// valuation per development × bedroom type against PPR resale comparables, last
// 3 years, time-adjusted to today, weighted by distance + recency + bedroom
// match + property-type match (docs/ires_reit_valuation.md,
// docs/ires_valuation_raw.json). Figures are an indicative model estimate, not
// a valuation of record.
//
// IRES financials are IRES REIT plc's own reported figures as at 30 June 2026
// (H1 2026 Interim Report, published 14 Aug 2026): IFRS investment property fair
// value €1,276.7m; IFRS NAV €727.9m (138.8c/share); net debt €533.6m; Net LTV
// 42.6%; 524,442,218 shares in issue. FY2025 disposals ran ~25%+ above book;
// H1 2026 disposals ~30% above book.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const ORANGE = "#eb6834";
const AQUA = "#1baf7a";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";

// Estimated value by region (€ millions) — docs/ires_reit_valuation.md
const REGIONS = [
  { label: "South Dublin", devs: 12, units: 1086, value: 498 },
  { label: "North Dublin", devs: 9, units: 841, value: 344 },
  { label: "West Dublin", devs: 4, units: 805, value: 308 },
  { label: "City Centre", devs: 7, units: 474, value: 219 },
  { label: "West City", devs: 3, units: 409, value: 153 },
];

// Property-type weighting multipliers used by the engine.
const TYPE_WEIGHTS = [
  { label: "Same type", sub: "apartment ↔ apartment", mult: 3.0, color: BLUE },
  { label: "Unknown type", sub: "no label on the sale", mult: 0.35, color: NEUTRAL },
  { label: "Different type", sub: "a house vs an apartment", mult: 0.05, color: ORANGE },
];

// Per-scheme indicative unit values (€). null where the scheme has no unit of
// that size. Ordered roughly by region. Some adjacent schemes share a valuation
// coordinate and therefore an estimate (see note under the table).
const SCHEMES: { name: string; region: string; oneBed: number | null; twoBed: number | null }[] = [
  { name: "The Marker", region: "City Centre", oneBed: null, twoBed: 456331 },
  { name: "Xavier Court", region: "City Centre", oneBed: 253147, twoBed: 318024 },
  { name: "Richmond Gardens", region: "City Centre", oneBed: 395344, twoBed: 496664 },
  { name: "Bakers Yard", region: "City Centre", oneBed: 459858, twoBed: 577711 },
  { name: "Kings Court", region: "City Centre", oneBed: 319796, twoBed: 401754 },
  { name: "City Square", region: "City Centre", oneBed: 383191, twoBed: 481396 },
  { name: "The School Yard", region: "City Centre", oneBed: 409937, twoBed: 514996 },
  { name: "Rockbrook South Central", region: "South Dublin", oneBed: 328139, twoBed: 412235 },
  { name: "Tara View", region: "South Dublin", oneBed: 436621, twoBed: 548519 },
  { name: "The Maple", region: "South Dublin", oneBed: 357139, twoBed: 448667 },
  { name: "The Forum", region: "South Dublin", oneBed: 400853, twoBed: 503585 },
  { name: "Rockbrook Grande Central", region: "South Dublin", oneBed: 328139, twoBed: 412235 },
  { name: "Grande Central", region: "South Dublin", oneBed: 328139, twoBed: 412235 },
  { name: "Elmpark Green", region: "South Dublin", oneBed: 436621, twoBed: 548519 },
  { name: "Beacon South Quarter", region: "South Dublin", oneBed: 357139, twoBed: 448667 },
  { name: "Bessboro", region: "South Dublin", oneBed: 393466, twoBed: 494304 },
  { name: "Belville Court", region: "South Dublin", oneBed: 358657, twoBed: 450574 },
  { name: "Beechwood Court", region: "South Dublin", oneBed: 474680, twoBed: 596332 },
  { name: "Time Place", region: "South Dublin", oneBed: 289532, twoBed: 363733 },
  { name: "The Coast", region: "North Dublin", oneBed: 307790, twoBed: 386671 },
  { name: "Carrington Park", region: "North Dublin", oneBed: 325007, twoBed: 408300 },
  { name: "Taylor Hill", region: "North Dublin", oneBed: null, twoBed: 338314 },
  { name: "Northern Cross", region: "North Dublin", oneBed: 409399, twoBed: 514321 },
  { name: "Heywood Court", region: "North Dublin", oneBed: 306374, twoBed: 384892 },
  { name: "Charlestown", region: "North Dublin", oneBed: 251905, twoBed: 316463 },
  { name: "Ashbrook", region: "North Dublin", oneBed: 382890, twoBed: 481018 },
  { name: "Waterside", region: "North Dublin", oneBed: 390626, twoBed: 490736 },
  { name: "Semple Woods", region: "North Dublin", oneBed: null, twoBed: null },
  { name: "Coldcut Park", region: "West Dublin", oneBed: 330484, twoBed: 415180 },
  { name: "Tallaght Cross West", region: "West Dublin", oneBed: 259280, twoBed: 325729 },
  { name: "Priorsgate", region: "West Dublin", oneBed: 382681, twoBed: 480755 },
  { name: "Phoenix Park Racecourse", region: "West Dublin", oneBed: 401239, twoBed: 504069 },
  { name: "Lansdowne Gate", region: "West City", oneBed: 290491, twoBed: 364939 },
  { name: "Tyrone Court", region: "West City", oneBed: 336446, twoBed: 422671 },
  { name: "Camac Crescent", region: "West City", oneBed: 249889, twoBed: 313932 },
];

// NAV-per-share scenarios (as at 30 June 2026 reported base). Debt (€533.6m) and
// share count (524.4m) held constant, so ΔNAV = Δportfolio value.
const NAV_ROWS = [
  { label: "IRES reported (IFRS)", portfolio: "€1,276.7m", nav: "€727.9m", perShare: 138.8, delta: "—" },
  { label: "Our open-market estimate", portfolio: "€1,522.9m", nav: "€974.1m", perShare: 185.7, delta: "+34%" },
  { label: "At IRES's realised +25% resale premium", portfolio: "€1,595.9m", nav: "€1,047.1m", perShare: 199.7, delta: "+44%" },
];

function euro(v: number | null): string {
  if (v === null) return "—";
  if (v >= 1_000_000) return `€${(v / 1_000_000).toFixed(2)}m`;
  return `€${Math.round(v / 1000)}k`;
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function StatCards() {
  const cards = [
    { big: "35", small: "developments" },
    { big: "3,615", small: "IRES-owned units" },
    { big: "≈ €1.52bn", small: "modelled gross value" },
    { big: "€421k", small: "average per unit" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "1rem", margin: "1.5rem 0 2rem" }}>
      {cards.map((c) => (
        <div key={c.small} style={{ background: SURFACE, border: `1px solid ${GRID}`, borderRadius: "0.5rem", padding: "1.1rem 1rem", textAlign: "center" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "#111827" }}>{c.big}</div>
          <div style={{ fontSize: "0.85rem", color: INK_MUTED, marginTop: "0.25rem" }}>{c.small}</div>
        </div>
      ))}
    </div>
  );
}

// --- Chart 1: estimated value by region --------------------------------------
function RegionValueChart() {
  const W = 720, H = 340, padL = 130, padR = 64, padT = 20, padB = 34;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 600;
  const rowH = plotH / REGIONS.length;
  const barH = rowH * 0.56;
  const x = (v: number) => padL + (v / hi) * plotW;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Horizontal bar chart of estimated IRES portfolio value by Dublin region. South Dublin is largest at about 498 million euro, then North Dublin 344 million, West Dublin 308 million, City Centre 219 million, and West City 153 million."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[0, 200, 400, 600].map((g) => (
          <g key={g}>
            <line x1={x(g)} x2={x(g)} y1={padT} y2={padT + plotH} stroke={GRID} strokeWidth={1} />
            <text x={x(g)} y={H - padB + 22} textAnchor="middle" fontSize={11} fill={INK_MUTED}>€{g}m</text>
          </g>
        ))}
        {REGIONS.map((r, i) => {
          const cy = padT + i * rowH + rowH / 2;
          return (
            <g key={r.label}>
              <text x={padL - 12} y={cy + 4} textAnchor="end" fontSize={12.5} fontWeight={600} fill={INK}>{r.label}</text>
              <rect x={padL} y={cy - barH / 2} width={x(r.value) - padL} height={barH} rx={4} fill={BLUE} opacity={0.85}>
                <title>{`${r.label}: €${r.value}m across ${r.devs} developments, ${r.units.toLocaleString()} units`}</title>
              </rect>
              <text x={x(r.value) + 8} y={cy + 4} fontSize={12} fontWeight={600} fill={INK}>€{r.value}m</text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Estimated gross value of the IRES-owned units by region. South Dublin — anchored by big Sandyford and
        Dublin&nbsp;4 schemes — carries roughly a third of the book. Source: HomeIQ valuation of the Property Price
        Register.
      </figcaption>
    </figure>
  );
}

// --- Chart 2: property-type weighting explainer ------------------------------
function TypeWeightChart() {
  const W = 720, H = 300, padL = 150, padR = 70, padT = 20, padB = 30;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 3.2;
  const rowH = plotH / TYPE_WEIGHTS.length;
  const barH = rowH * 0.5;
  const x = (v: number) => padL + (v / hi) * plotW;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart of how much weight the valuation engine gives a comparable sale by property-type match. A same-type sale gets a 3.0 times multiplier, an unlabelled sale 0.35 times, and a different-type sale 0.05 times — near exclusion."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[0, 1, 2, 3].map((g) => (
          <g key={g}>
            <line x1={x(g)} x2={x(g)} y1={padT} y2={padT + plotH} stroke={GRID} strokeWidth={1} />
            <text x={x(g)} y={H - padB + 20} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{g}×</text>
          </g>
        ))}
        {TYPE_WEIGHTS.map((t, i) => {
          const cy = padT + i * rowH + rowH / 2;
          return (
            <g key={t.label}>
              <text x={padL - 12} y={cy - 1} textAnchor="end" fontSize={12.5} fontWeight={600} fill={INK}>{t.label}</text>
              <text x={padL - 12} y={cy + 14} textAnchor="end" fontSize={10.5} fill={INK_MUTED}>{t.sub}</text>
              <rect x={padL} y={cy - barH / 2} width={Math.max(2, x(t.mult) - padL)} height={barH} rx={4} fill={t.color} opacity={0.85}>
                <title>{`${t.label}: ${t.mult}× weight`}</title>
              </rect>
              <text x={x(t.mult) + 8} y={cy + 4} fontSize={12} fontWeight={700} fill={t.color}>{t.mult.toFixed(2)}×</text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        How the engine weights a comparable sale by property type. An apartment is valued almost entirely off other
        apartments; a nearby house is all but ignored. Sales with no type label sit in between so sparse areas still
        return an estimate.
      </figcaption>
    </figure>
  );
}

// --- Chart 3: NAV per share scenarios ----------------------------------------
function NavScenarioChart() {
  const W = 720, H = 320, padL = 48, padR = 16, padT = 24, padB = 74;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 250;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const groupW = plotW / NAV_ROWS.length;
  const barW = groupW * 0.44;
  const colors = [NEUTRAL, BLUE, AQUA];

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart of IFRS NAV per share under three bases. Reported at 30 June 2026 is 138.8 cents; at our open-market estimate it rises to 186 cents; at IRES's realised 25 percent resale premium it rises to 200 cents."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[0, 100, 200].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}c</text>
          </g>
        ))}
        {NAV_ROWS.map((r, i) => {
          const cx = padL + i * groupW + groupW / 2;
          const top = y(r.perShare);
          return (
            <g key={r.label}>
              <rect x={cx - barW / 2} y={top} width={barW} height={padT + plotH - top} rx={4} fill={colors[i]} opacity={0.85}>
                <title>{`${r.label}: ${r.perShare}c per share`}</title>
              </rect>
              <text x={cx} y={top - 8} textAnchor="middle" fontSize={13} fontWeight={700} fill={colors[i]}>{r.perShare}c</text>
              <text x={cx} y={H - padB + 20} textAnchor="middle" fontSize={11.5} fontWeight={600} fill={INK}>
                {i === 0 ? "Reported" : i === 1 ? "Our estimate" : "IRES's +25% resale"}
              </text>
              <text x={cx} y={H - padB + 38} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>
                {i === 0 ? "30 Jun 2026" : r.delta + " vs reported"}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        IFRS NAV per share as reported, versus what it would be if the portfolio were marked to our open-market estimate,
        or to the ~25% premium IRES itself realises when it sells individual vacant units — holding IRES's ~€534m net debt
        and 524.4m shares constant. Reported figure: IRES H1 2026 Interim Report (30 June 2026).
      </figcaption>
    </figure>
  );
}

// --- Per-scheme indicative value table ---------------------------------------
function SchemeTable() {
  const th: React.CSSProperties = {
    textAlign: "left", padding: "0.5rem 0.75rem", fontSize: "0.8rem", fontWeight: 700,
    color: INK, borderBottom: `2px solid ${GRID}`, position: "sticky", top: 0, background: "#fff",
  };
  const thR: React.CSSProperties = { ...th, textAlign: "right" };
  const td: React.CSSProperties = { padding: "0.45rem 0.75rem", fontSize: "0.9rem", color: INK, borderBottom: `1px solid ${GRID}` };
  const tdR: React.CSSProperties = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };

  return (
    <figure style={{ margin: "1.5rem 0 2rem" }}>
      <div style={{ maxHeight: 460, overflowY: "auto", border: `1px solid ${GRID}`, borderRadius: "0.5rem" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
          <thead>
            <tr>
              <th style={th}>Development</th>
              <th style={th}>Region</th>
              <th style={thR}>1-bed</th>
              <th style={thR}>2-bed</th>
            </tr>
          </thead>
          <tbody>
            {SCHEMES.map((s, i) => (
              <tr key={s.name} style={{ background: i % 2 ? SURFACE : "#fff" }}>
                <td style={{ ...td, fontWeight: 600 }}>{s.name}</td>
                <td style={{ ...td, color: INK_MUTED }}>{s.region}</td>
                <td style={tdR}>{euro(s.oneBed)}</td>
                <td style={tdR}>{euro(s.twoBed)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Indicative open-market value of a one-bed and a two-bed unit in each scheme, from HomeIQ's comparable-sales
        model (rounded). "—" means the scheme has no unit of that size in IRES's ownership (e.g. Semple Woods and Taylor
        Hill are houses). A few adjacent schemes sharing one street or complex resolve to a shared valuation point and so
        return the same figures — the three Rockbrook blocks, Elmpark Green with Tara View (both on Merrion Road), and The
        Maple with Beacon South Quarter (both in Sandyford).
      </figcaption>
    </figure>
  );
}

export function IresReitValuationContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        We built HomeIQ to answer one deceptively hard question: <em>what is a specific home actually worth today?</em> Our{" "}
        <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>instant valuation tool</Link> answers it for any
        Irish address using real sold prices from the Property Price Register (PPR). To show what the engine can do at
        scale, we pointed it at one of the most-watched residential landlords in the country — <strong>IRES REIT plc</strong>{" "}
        — and valued its <strong>entire Dublin apartment portfolio, unit by unit</strong>.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The headline:</strong> across <strong>35 developments</strong> and <strong>3,615 IRES-owned units</strong>,
          our model puts the open-market resale value of the portfolio at roughly <strong>€1.52 billion</strong> — an average
          of about <strong>€421,000 per unit</strong>. That is around <strong>19% above</strong> the €1.28bn IRES carries on
          its own balance sheet — and, as we'll show, it would lift the group's net asset value per share by about a{" "}
          <strong>third</strong>. Strikingly, that 19% premium is <em>smaller</em> than the 25–30% IRES itself achieves when
          it sells vacant units individually — so if anything our independent estimate is on the conservative side.
        </p>
      </div>

      <SectionHeading>Who is IRES REIT plc?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Irish Residential Properties REIT plc (<strong>IRES</strong>) is Ireland's largest private residential landlord and
        is listed on Euronext Dublin. A <strong>REIT</strong> — Real Estate Investment Trust — is a company that owns and
        rents out property and passes most of its rental income to shareholders as dividends. IRES's business is almost
        entirely <strong>residential rental</strong>: it owns roughly <strong>3,600 apartments</strong>, largely across
        Dublin, and lets them to tenants.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        Because it is a public company, IRES publishes the value of its portfolio in its financial statements — but that
        figure is an accounting (IFRS) valuation of the assets as a rented, income-producing <em>block</em>. We wanted to
        approach it from the opposite direction: <strong>from the outside, using only public sold-price data</strong>, as
        if someone were selling each apartment individually on the open market. That is a genuinely different — and useful —
        lens, and it is exactly the lens our valuation tool applies to any home.
      </p>

      <SectionHeading>The portfolio: what IRES actually owns</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        We catalogued IRES's holdings from its own property pages, counting <strong>only the units IRES owns</strong> in
        each scheme (many developments are mixed-ownership). That gives <strong>35 developments</strong> spread across five
        broad Dublin regions, totalling <strong>3,615 units</strong> — essentially the whole of IRES's reported 3,611-unit
        residential book.
      </p>
      <StatCards />
      <p style={{ marginBottom: "1rem" }}>
        It is overwhelmingly an <strong>apartment</strong> book. By bedroom mix, roughly <strong>64% are two-bed</strong>{" "}
        and <strong>22% one-bed</strong>, with three-beds (~13%) and a handful of studios and four-beds making up the rest.
        Only two schemes are traditional family <strong>houses</strong> — Taylor Hill in Balbriggan and Semple Woods in
        Donabate. The biggest single schemes are <strong>Tallaght Cross West</strong> (460 units),{" "}
        <strong>Charlestown</strong> in Finglas (237), <strong>Lansdowne Gate</strong> in Drimnagh (224) and{" "}
        <strong>Beacon South Quarter</strong> in Sandyford (213).
      </p>
      <p style={{ marginBottom: "2rem" }}>
        Grouped by area, South Dublin dominates — its Sandyford cluster (Rockbrook, The Maple, Beacon South Quarter, Time
        Place) plus the Dublin&nbsp;4 schemes on Merrion Road make it comfortably the most valuable region in the book.
      </p>
      <RegionValueChart />

      <SectionHeading>How we valued it — and why property type matters</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Every figure here comes from the same engine behind our public{" "}
        <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>valuation tool</Link>. For each development, and
        for each bedroom type it contains, we run the following pipeline:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Locate the scheme.</strong> We pin each development to a coordinate — matching its street against the PPR,
          or falling back to its Eircode routing-key centre — never to a marketing name (those don't appear in PPR data).
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Find comparable sales.</strong> We pull genuine, arm's-length resale transactions nearby, expanding the
          search radius from 1&nbsp;km outward until we have enough, restricted to the last three years. Bulk/multi-unit
          filings and out-of-band prices are stripped out.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Bring every sale to today's money.</strong> Each comparable is time-adjusted to the present using
          county-level price indices, so a 2023 sale is expressed in 2026 terms.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Weight the comparables.</strong> Closer, more recent, and more similar sales count for more. A sale's
          weight combines distance, recency, <strong>bedroom match</strong> and — newly — <strong>property-type match</strong>.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        That last factor is the important upgrade this project prompted. <strong>Apartments and houses are effectively
        separate markets</strong> — valuing a two-bed apartment off nearby three-bed semis gives a badly inflated number.
        So the engine now weights a same-type comparable (apartment against apartment) <strong>3× as heavily</strong>, and
        all but discards an opposite-type one — a house counts for just <strong>0.05×</strong> when valuing an apartment.
      </p>
      <TypeWeightChart />
      <p style={{ marginBottom: "1rem" }}>
        Type weighting alone isn't enough, though, because the PPR leaves property type <strong>blank on about 69% of
        sales</strong>. In a house-heavy area an expensive but <em>unlabelled</em> semi slips past the type filter and quietly
        inflates an apartment estimate. So this project drove three further upgrades to the engine — all of which now run on
        every valuation, not just this one:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>A bedroom price ladder.</strong> Every comparable is first converted to a "two-bed equivalent" using
          Dublin apartment bedroom ratios, then re-expanded to the size we're valuing. This produces one consistent base per
          location and <strong>guarantees a larger unit is never valued below a smaller one</strong> in the same scheme — the
          per-bedroom ladder you see in the table.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>A local outlier trim.</strong> A statistical fence removes lone extreme sales — a trophy home, or a
          multi-unit deal recorded among ordinary transactions — before anything is averaged.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>An apartment-price ceiling.</strong> For apartment schemes the engine now <em>learns what an apartment
          actually costs locally</em>, from confirmed nearby apartment sales, and discards any comparable priced like a
          house — catching exactly the unlabelled houses the type filter misses. Crucially the ceiling adapts to the area: it
          sits tight in uniform suburbs but stays generous in genuinely premium districts, so it trims house contamination
          without capping real luxury flats.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        Finally, we ran a <strong>coordinate audit</strong>. Cross-checking each scheme's map pin against its own PPR sales
        and against Mapbox geocoding exposed nine developments that had drifted into the wrong district — three of them onto a
        single shared geocoder-fallback point. Left uncorrected, that drift can be dramatic: Phoenix Park Racecourse had
        landed 1.3&nbsp;km away in Castleknock's detached-house belt, pushing its two-beds to a false €0.87m before the
        ceiling and a corrected coordinate brought them back to a credible €0.50m. All nine are now pinned to verified
        coordinates.
      </p>
      <p style={{ marginBottom: "2rem" }}>
        Together these changes stripped out the implausible seven-figure apartment values our earlier, cruder run contained
        and brought the portfolio total down from about €2.0&nbsp;billion to <strong>€1.52&nbsp;billion</strong> — with the
        per-unit estimates now sitting in a tight, believable €0.31m–€0.60m band right across the book.
      </p>

      <SectionHeading>The results — scheme by scheme</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Rolling the per-unit estimates back up across all 35 developments gives an open-market resale value of
        approximately <strong>€1.52&nbsp;billion</strong>. But the more interesting output is the per-scheme detail. The table
        below shows our indicative value for a <strong>one-bed</strong> and a <strong>two-bed</strong> apartment in each
        development — the two sizes that make up ~86% of the portfolio.
      </p>
      <SchemeTable />
      <p style={{ marginBottom: "2rem" }}>
        The spread is coherent from top to bottom: a two-bed runs from about <strong>€314k</strong> in Camac Crescent
        (Inchicore) and Charlestown (Finglas) up to roughly <strong>€550k–€600k</strong> in the Dublin&nbsp;4 schemes
        (Elmpark Green, Tara View) and at Beechwood Court in Stillorgan. There are no seven-figure apartments any more — the
        apartment-price ceiling removed them — leaving a clean picture of a mid-market apartment book with a modest premium
        tail in Dublin&nbsp;4 and the affluent southside.
      </p>

      <SectionHeading>How our figure compares to IRES's own books</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        In its <strong>H1 2026 interim report</strong> (as at 30 June 2026), IRES carried its investment property at an IFRS
        fair value of <strong>€1,276.7 million</strong>. Our open-market model comes out at <strong>€1,522.9 million</strong>{" "}
        — a difference of <strong>€246 million</strong>, or roughly <strong>19% higher</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        A 19% premium is exactly the kind of gap you'd expect between a rented-block accounting value and the sum of what
        each flat would fetch sold individually — and there's a clean external check on it. IRES has been quietly selling
        individual units, and it discloses what it gets: in FY2025 it sold 315 units at over <strong>25% above book
        value</strong>, and in H1 2026 a further tranche at around <strong>30% above book</strong>. In other words,{" "}
        <strong>IRES's own vacant-unit sales fetch a larger premium than our whole-portfolio estimate implies</strong>. Our
        independent, comparable-based figure therefore sits <em>below</em> what IRES actually realises unit by unit — a
        reassuring sign that, if anything, we're being conservative rather than exuberant.
      </p>

      <SectionHeading>Why the accounting value is lower: a note on IFRS</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The two numbers aren't measuring quite the same thing. Under <strong>IAS 40 (Investment Property)</strong>, a
        landlord like IRES can hold property at <strong>fair value</strong>, remeasured every reporting period with the gains
        or losses running through the income statement. Fair value itself is defined by <strong>IFRS 13</strong> as the
        price to sell an asset in an orderly transaction between market participants at the measurement date — an{" "}
        <em>exit price</em>, assessed at the property's highest and best use, and signed off by independent external valuers.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        For a tenanted residential portfolio, valuers assess that exit price on an <strong>investment basis</strong>: the
        block is worth the income stream it produces, capitalised at a market yield, reflecting sitting tenants and — in
        Ireland — <strong>Rent Pressure Zone (RPZ)</strong> caps that limit how fast rents can rise. That is structurally
        <em> lower</em> than the sum of what each flat would fetch sold individually with vacant possession, which is closer
        to what our comparable-sales model measures. The difference between "value as a rented block" and "value broken up
        and sold flat by flat" is real, well known in the sector, and precisely the gap IRES crystallises when it sells a
        unit at a 25–30% premium to book.
      </p>

      <SectionHeading>What it would mean for NAV per share</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Here is where it gets interesting for shareholders. IRES funds its portfolio with a mix of equity and debt. At 30
        June 2026 it had <strong>net debt of about €533.6 million</strong> (a Net loan-to-value of <strong>42.6%</strong>),
        against an IFRS <strong>net asset value of €727.9 million</strong> — equivalent to <strong>138.8 cents per
        share</strong> across its 524.4 million shares.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        Debt is fixed in euros, so <strong>every euro of change in property value flows straight through to equity</strong>.
        With the portfolio (€1.28bn) worth about 1.75× the NAV (€0.73bn), that leverage <em>amplifies</em> any revaluation:
        a given percentage rise in the property is magnified roughly 1.75× in NAV per share. So if the portfolio were marked
        closer to our open-market estimate — holding debt and the share count constant — the effect on NAV is dramatic:
      </p>

      <figure style={{ margin: "1.5rem 0 1.5rem" }}>
        <div style={{ overflowX: "auto", border: `1px solid ${GRID}`, borderRadius: "0.5rem" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.92rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Basis</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Portfolio value</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Implied NAV</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>NAV / share</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>vs reported</th>
              </tr>
            </thead>
            <tbody>
              {NAV_ROWS.map((r, i) => (
                <tr key={r.label} style={{ background: i === 0 ? "#fff" : (i % 2 ? SURFACE : "#fff") }}>
                  <td style={{ padding: "0.5rem 0.85rem", color: INK, borderBottom: `1px solid ${GRID}`, fontWeight: i === 0 ? 700 : 600 }}>{r.label}</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: INK, borderBottom: `1px solid ${GRID}`, fontVariantNumeric: "tabular-nums" }}>{r.portfolio}</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: INK, borderBottom: `1px solid ${GRID}`, fontVariantNumeric: "tabular-nums" }}>{r.nav}</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: "#111827", borderBottom: `1px solid ${GRID}`, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{r.perShare.toFixed(1)}c</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: i === 0 ? INK_MUTED : "#15803d", borderBottom: `1px solid ${GRID}`, fontWeight: 600 }}>{r.delta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
          NAV bridge holding net debt (€533.6m) and shares (524.4m) constant. As an Irish REIT, IRES is largely exempt from
          tax on rental profits and gains, so a revaluation flows to NAV without a deferred-tax drag. Reported figures: IRES
          H1 2026 Interim Report (30 June 2026).
        </figcaption>
      </figure>

      <NavScenarioChart />

      <p style={{ marginBottom: "2rem" }}>
        Gearing does the amplifying: a <strong>€246m</strong> uplift in the property — only about 19% — lifts NAV per share by
        roughly a <strong>third, to ~186 cents</strong>, because that gain lands entirely on the smaller equity slice. And
        because our estimate is more conservative than IRES's own disposal record, the realistic ceiling is arguably higher
        still: marking the book to the ~25% premium IRES actually achieves on unit sales would put NAV per share near{" "}
        <strong>200 cents</strong>. Either way the direction is clear — the shares' <strong>138.8-cent</strong> reported NAV
        looks conservative against what the underlying flats would fetch sold individually.
      </p>

      <SectionHeading>Read the number honestly</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        We would rather show the limitations than bury them. Our <strong>€1.52bn</strong> is a specific construct — the sum of
        what each flat would fetch sold individually, with vacant possession, on the open market today — and a few things
        shape how to read it:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>No block discount.</strong> We value each apartment as an individual resale. A single buyer taking a whole
          scheme — or the whole portfolio in one line — would normally pay <em>less</em> per unit. This is genuinely a
          sum-of-parts figure, not a block-sale price.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Incomplete type labels — now largely handled.</strong> The PPR omits property type on about 69% of sales,
          which used to let expensive unlabelled houses inflate apartment estimates. The apartment-price ceiling now catches
          those, which is why the earlier seven-figure Dublin&nbsp;4 apartment values have disappeared. It isn't perfect in
          the very sparsest areas, but it removes the largest source of upward bias.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Different valuation bases.</strong> Our sum-of-individual-resales is not the same construct as an IAS 40
          investment-basis fair value; the two answer related but distinct questions, which is exactly why a gap between them
          is expected.
        </li>
      </ul>
      <p style={{ marginBottom: "2rem" }}>
        None of that is a flaw unique to this exercise — it's the honest texture of any comparable-based valuation, and it's
        why our tool always shows you the comparables, the confidence level and the distance behind every estimate rather
        than a single magic number.
      </p>

      <SectionHeading>The takeaway</SectionHeading>
      <p style={{ marginBottom: "2rem" }}>
        With nothing but public sold-price data, we independently valued a <strong>€1.52&nbsp;billion</strong>, 3,615-unit
        residential portfolio right down to the individual apartment — landing about <strong>19% above</strong> IRES's book
        value, comfortably inside the 25–30% premiums IRES itself realises on unit sales, and implying a NAV per share nearer{" "}
        <strong>186 cents</strong> than the <strong>139 cents</strong> on its books. The apartment-price intelligence that
        made those estimates credible — the bedroom ladder, the type weighting and the local apartment ceiling — is the very
        same logic that runs when you value <em>your</em> home. If our engine can take on a listed REIT's entire book, it can
        certainly price a single address.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Want the same analysis for your own home?</strong> Get a free instant valuation built from real comparable
          sales near you — with the comparables and confidence shown, and apartments valued off apartments.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        IRES financial figures are IRES REIT plc's own reported numbers as at 30 June 2026 (H1 2026 Interim Report,
        published 14 August 2026). HomeIQ valuations are an indicative statistical model based on Property Price Register
        resale comparables and are not a valuation of record, investment advice, or a recommendation regarding any
        security. Do your own research.
      </p>
    </div>
  );
}
