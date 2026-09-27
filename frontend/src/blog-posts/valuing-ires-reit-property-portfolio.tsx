import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ valuation of the IRES REIT residential portfolio (IRES-owned
// units only), run through the same engine that powers /valuation. Portfolio
// holdings captured from iresreit.ie on 2026-09-27 (docs/ires_reit_portfolio.md);
// valuation per development × bedroom type against PPR resale comparables, last
// 3 years, time-adjusted to today, weighted by distance + recency + bedroom
// match + property-type match (docs/ires_reit_valuation.md,
// docs/ires_valuation_raw.json). Figures are an indicative model estimate, not
// a valuation of record.
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
  { label: "South Dublin", devs: 12, units: 1086, value: 757 },
  { label: "North Dublin", devs: 9, units: 841, value: 393 },
  { label: "West Dublin", devs: 4, units: 805, value: 355 },
  { label: "City Centre", devs: 7, units: 474, value: 348 },
  { label: "West City", devs: 3, units: 409, value: 151 },
];

// Property-type weighting multipliers used by the engine.
const TYPE_WEIGHTS = [
  { label: "Same type", sub: "apartment ↔ apartment", mult: 3.0, color: BLUE },
  { label: "Unknown type", sub: "no label on the sale", mult: 0.35, color: NEUTRAL },
  { label: "Different type", sub: "a house vs an apartment", mult: 0.05, color: ORANGE },
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
    { big: "35", small: "developments" },
    { big: "3,615", small: "IRES-owned units" },
    { big: "≈ €2.0bn", small: "modelled gross value" },
    { big: "€554k", small: "average per unit" },
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
  const hi = 800;
  const rowH = plotH / REGIONS.length;
  const barH = rowH * 0.56;
  const x = (v: number) => padL + (v / hi) * plotW;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Horizontal bar chart of estimated IRES portfolio value by Dublin region. South Dublin is largest at about 757 million euro, then North Dublin 393 million, West Dublin 355 million, City Centre 348 million, and West City 151 million."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[0, 200, 400, 600, 800].map((g) => (
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
        Dublin&nbsp;4 schemes — carries more than a third of the book. Source: HomeIQ valuation of the Property Price
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

export function IresReitValuationContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        We built HomeIQ to answer one deceptively hard question: <em>what is a specific home actually worth today?</em> Our{" "}
        <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>instant valuation tool</Link> answers it for any
        Irish address using real sold prices from the Property Price Register (PPR). To show what the engine can do at
        scale, we pointed it at one of the most-watched residential landlords in the country — <strong>IRES REIT</strong> —
        and valued its <strong>entire Dublin apartment portfolio, unit by unit</strong>.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The headline:</strong> across <strong>35 developments</strong> and <strong>3,615 IRES-owned units</strong>,
          our model puts the open-market resale value of the portfolio at roughly <strong>€2.0 billion</strong> — an average
          of about <strong>€554,000 per unit</strong>. This is an indicative, sum-of-the-parts estimate built from
          comparable second-hand sales, not IRES's own book value — more on why that distinction matters below.
        </p>
      </div>

      <SectionHeading>Who is IRES REIT?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Irish Residential Properties REIT plc (<strong>IRES</strong>) is Ireland's largest private residential landlord and
        is listed on Euronext Dublin. A <strong>REIT</strong> — Real Estate Investment Trust — is a company that owns and
        rents out property and passes most of its rental income to shareholders as dividends. IRES's business is almost
        entirely <strong>residential rental</strong>: it buys and builds apartment schemes, largely across Dublin, and lets
        them to tenants.
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
        broad Dublin regions, totalling <strong>3,615 units</strong>.
      </p>
      <StatCards />
      <p style={{ marginBottom: "1rem" }}>
        It is overwhelmingly an <strong>apartment</strong> book. By bedroom mix, roughly <strong>64% are two-bed</strong>{" "}
        and <strong>22% one-bed</strong>, with three-beds (~13%) and a handful of studios and four-beds making up the rest.
        Only two schemes are traditional family <strong>houses</strong> — Taylor Hill in Balbriggan and Semple Woods in
        Donabate — and just two developments contribute studios. The biggest single schemes are{" "}
        <strong>Tallaght Cross West</strong> (460 units), <strong>Charlestown</strong> in Finglas (237),{" "}
        <strong>Lansdowne Gate</strong> in Drimnagh (224) and <strong>Beacon South Quarter</strong> in Sandyford (213).
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
      <p style={{ marginBottom: "2rem" }}>
        The effect is exactly what you'd want: apartment schemes that used to borrow value from expensive nearby houses came
        down to earth. Under our earlier type-blind model the portfolio came out at €2.10&nbsp;billion; with type-aware
        weighting it falls to <strong>€2.00&nbsp;billion</strong>, with the biggest corrections on apartment schemes sitting
        among pricey houses (The Marker dropped from €555k to €461k per unit, for example).
      </p>

      <SectionHeading>The results</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Rolling the per-unit estimates back up across all 35 developments gives an open-market resale value of
        approximately <strong>€2.0&nbsp;billion</strong>. South Dublin accounts for about <strong>€757m</strong>, North
        Dublin <strong>€393m</strong>, West Dublin <strong>€355m</strong>, the City Centre <strong>€348m</strong> and West
        City <strong>€151m</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        The most valuable individual schemes are the Dublin&nbsp;4 developments on Merrion Road — Elmpark Green (~€217m) and
        Tara View (~€70m) — where even apartments command well over €1m, alongside the sheer scale of Tallaght Cross West
        (~€145m over 460 units) and Charlestown (~€84m). At the affordable end, the west-Dublin and west-city schemes —
        Tallaght Cross West, Priorsgate, Lansdowne Gate, Camac Crescent — sit around €310k–€375k per unit.
      </p>

      <SectionHeading>Read the number honestly</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        A €2.0&nbsp;billion sum-of-the-units figure is <strong>not</strong> what IRES would fetch if it sold the portfolio
        tomorrow, and it isn't the value IRES carries on its own balance sheet. Three things pull in different directions,
        and we'd rather show them than bury them:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>No block discount.</strong> We value each apartment as an individual open-market resale. A single buyer
          taking a whole scheme — or the whole portfolio — normally pays <em>less</em> per unit, not more. So our figure is
          an <em>upper</em> bound in that respect.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Type labels are incomplete.</strong> The PPR doesn't record property type for about 69% of sales. Where
          an apartment scheme sits in an area where the unlabelled sales are mostly expensive houses (classic Dublin&nbsp;4),
          the estimate is still pulled up. Richmond Gardens (~€1.48m/unit) is the clearest outlier and should be read as an
          upper bound, not a real apartment price.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Coordinate sharing.</strong> A few adjacent schemes (the Rockbrook/Sandyford cluster, Elmpark Green and
          Tara View) resolve to the same point and so share a per-unit estimate.
        </li>
      </ul>
      <p style={{ marginBottom: "2rem" }}>
        None of that is a flaw unique to this exercise — it's the honest texture of any comparable-based valuation, and it's
        why our tool always shows you the comparables, the confidence level and the distance behind every estimate rather
        than a single magic number.
      </p>

      <SectionHeading>The takeaway</SectionHeading>
      <p style={{ marginBottom: "2rem" }}>
        With nothing but public sold-price data, we independently valued a €2&nbsp;billion, 3,615-unit residential portfolio
        down to the individual apartment — and the property-type-aware logic that made those apartment estimates credible is
        the very same logic that runs when you value <em>your</em> home. If our engine can take on a listed REIT's entire
        book, it can certainly price a single address.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Want the same analysis for your own home?</strong> Get a free instant valuation built from real comparable
          sales near you — with the comparables and confidence shown, and apartments valued off apartments.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>
    </div>
  );
}
