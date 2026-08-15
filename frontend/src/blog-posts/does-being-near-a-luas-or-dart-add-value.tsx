import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ analysis of 214,888 full-market Dublin residential sales on the
// Property Price Register, Jan 2010 – Jul 2026 (price trimmed to the 1st–99th
// percentile, €80k–€2.2m, to remove bulk/commercial records). Distance to each
// transport type computed by PostGIS nearest-neighbour against 122 geocoded
// Dublin transport points. Adjusted premiums come from a hedonic regression of
// log(price) with Eircode-area and year fixed effects (89,169 sales, 35 areas).
// ---------------------------------------------------------------------------

// Palette — dataviz reference categorical slots 1–3 (pre-validated all-pairs,
// worst CVD ΔE 9.2). Deliberately NOT literal green/red, which the line names
// invite but which fails colour-blind separation.
const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";   // Green Line Luas
const ORANGE = "#eb6834"; // Red Line Luas
const AQUA = "#1baf7a";   // DART
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";

const LINES = [
  { key: "green", label: "Green Line Luas", color: BLUE },
  { key: "red", label: "Red Line Luas", color: ORANGE },
  { key: "dart", label: "DART", color: AQUA },
];

// Raw near(<1km) vs far(>=1km) median gap, and adjusted premium (within area+year)
const RAW_GAP = { green: 13.1, red: -21.5, dart: 17.0 };       // %
const ADJ_PREMIUM = { green: 3.5, red: -14.9, dart: 2.0 };      // %

// Median price (€000s) by nearest-distance band
const BANDS = ["0–250m", "250–500m", "500m–1km", "1–2km", ">2km"];
const DOSE: Record<string, number[]> = {
  green: [395, 385, 421, 415, 352],
  red: [305, 300, 300, 350, 387],
  dart: [426, 430, 412, 415, 348],
};

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", margin: "0 0 0.5rem", fontSize: "0.9rem", color: INK }}>
      {LINES.map((l) => (
        <span key={l.key} style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ width: 14, height: 14, background: l.color, borderRadius: 3, display: "inline-block" }} /> {l.label}
        </span>
      ))}
    </div>
  );
}

// --- Chart 1: Raw gap vs adjusted premium (the confounding story) -------------
function RawVsAdjustedChart() {
  const W = 720, H = 380, padL = 56, padR = 16, padT = 28, padB = 56;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = -25, hi = 20;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const base = y(0);
  const groupW = plotW / LINES.length;
  const barW = groupW / 2 - 14;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Grouped bar chart comparing the raw near-versus-far price gap with the adjusted premium for each line. The DART's raw gap of plus 17 percent falls to plus 2 percent when adjusted; the Green Line's plus 13 percent falls to plus 3.5 percent; the Red Line stays negative, minus 21 percent raw and minus 15 percent adjusted."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[-25, -15, -5, 5, 15].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g > 0 ? "+" : ""}{g}%</text>
          </g>
        ))}
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke={INK} strokeWidth={1.5} />
        {LINES.map((l, i) => {
          const gx = padL + i * groupW + 12;
          const raw = RAW_GAP[l.key as keyof typeof RAW_GAP];
          const adj = ADJ_PREMIUM[l.key as keyof typeof ADJ_PREMIUM];
          const bar = (x: number, v: number, solid: boolean) => {
            const top = v >= 0 ? y(v) : base;
            const h = Math.abs(y(v) - base);
            return (
              <g>
                <rect x={x} y={top} width={barW} height={h} rx={4}
                      fill={solid ? l.color : SURFACE} stroke={l.color} strokeWidth={solid ? 0 : 2}
                      opacity={solid ? 0.45 : 1}>
                  <title>{`${l.label} — ${solid ? "raw gap" : "adjusted"}: ${v > 0 ? "+" : ""}${v}%`}</title>
                </rect>
                <text x={x + barW / 2} y={v >= 0 ? top - 6 : top + h + 14} textAnchor="middle"
                      fontSize={11} fontWeight={600} fill={l.color}>{v > 0 ? "+" : ""}{v}%</text>
              </g>
            );
          };
          return (
            <g key={l.key}>
              {bar(gx, raw, true)}
              {bar(gx + barW + 8, adj, false)}
              <text x={gx + barW + 4} y={H - padB + 20} textAnchor="middle" fontSize={12} fontWeight={600} fill={INK}>{l.label}</text>
            </g>
          );
        })}
        {/* raw vs adjusted key */}
        <g transform={`translate(${padL}, ${H - 14})`}>
          <rect x={0} y={-9} width={13} height={13} rx={3} fill={NEUTRAL} opacity={0.45} />
          <text x={18} y={2} fontSize={11} fill={INK_MUTED}>Raw gap (near vs far)</text>
          <rect x={190} y={-9} width={13} height={13} rx={3} fill={SURFACE} stroke={NEUTRAL} strokeWidth={2} />
          <text x={208} y={2} fontSize={11} fill={INK_MUTED}>Adjusted (same area & year)</text>
        </g>
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Solid bars: the raw difference in median price between homes within 1&nbsp;km of a line and those further away.
        Outlined bars: the premium left once we compare like-with-like homes in the <em>same Eircode area and year</em>.
        Most of the raw gap is <strong>where the line runs</strong>, not the line itself. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

// --- Chart 2: Distance dose-response ------------------------------------------
function DoseResponseChart() {
  const W = 720, H = 380, padL = 56, padR = 96, padT = 28, padB = 48;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = 280, hi = 440;
  const step = plotW / (BANDS.length - 1);
  const x = (i: number) => padL + i * step;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const path = (arr: number[]) => arr.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Line chart of median sale price by distance band to each line. Near the Green Line and DART, prices are highest in the closest bands and fall away beyond 2 kilometres. Near the Red Line the pattern is reversed: prices rise with distance."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[300, 340, 380, 420].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>€{g}k</text>
          </g>
        ))}
        {LINES.map((l) => {
          const arr = DOSE[l.key];
          return (
            <g key={l.key}>
              <path d={path(arr)} fill="none" stroke={l.color} strokeWidth={2.5} />
              {arr.map((v, i) => (
                <circle key={i} cx={x(i)} cy={y(v)} r={3.8} fill={l.color}>
                  <title>{`${l.label} — ${BANDS[i]}: €${v}k`}</title>
                </circle>
              ))}
              <text x={W - padR + 6} y={y(arr[arr.length - 1]) + 4} fontSize={12} fontWeight={600} fill={l.color}>{l.label}</text>
            </g>
          );
        })}
        {BANDS.map((b, i) => (
          <text key={b} x={x(i)} y={H - padB + 18} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{b}</text>
        ))}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Median sale price by how far the home is from the nearest stop on each line (raw, not adjusted for area).
        The Green Line and DART slope down as you move away; the Red Line slopes <em>up</em> — a giveaway that its
        corridor runs through less expensive parts of the city. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

export function TransportPremiumContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        "Close to the Luas" and "walk to the DART" are among the most common selling points in a Dublin property ad.
        But does living near a rail line actually add to what a home sells for &mdash; and if so, how much? We analysed{" "}
        <strong>214,888 full-market Dublin sales</strong> recorded on the Property Price Register between January 2010
        and July 2026, measuring how far each home is from the nearest Luas or DART stop, with particular attention to the{" "}
        <strong>Green Line Luas, Red Line Luas and the DART</strong>.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The short answer:</strong> being within 1&nbsp;km of the <strong>Green Line Luas</strong> is linked to a
          small price premium of around <strong>3&ndash;5%</strong> once you compare similar homes in the same area. The{" "}
          <strong>DART</strong> shows only a weak effect (~2%, not statistically significant), and the <strong>Red Line
          Luas</strong> shows none. The big "near the line is worth 15&ndash;20% more" numbers you get from a naïve
          comparison are almost entirely about <em>which neighbourhoods</em> the lines run through &mdash; not the lines themselves.
        </p>
      </div>

      <SectionHeading>The headline numbers are a trap</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        If you simply compare the median price of homes within 1&nbsp;km of each line against those further away, the
        differences look enormous: homes near the DART sell for <strong>17% more</strong>, near the Green Line for{" "}
        <strong>13% more</strong> &mdash; and, oddly, homes near the Red Line sell for <strong>21% less</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        The problem is that Dublin's rail lines don't run through random places. The <strong>DART</strong> hugs the
        affluent coast (Sandymount, Blackrock, Dún&nbsp;Laoghaire, Malahide). The <strong>Green Line</strong> threads
        through wealthy south Dublin (Ranelagh, Dundrum). The <strong>Red Line</strong> serves more affordable western
        and inner-city corridors (Tallaght, Inchicore, the north inner city). So the raw gap is mostly measuring the{" "}
        <em>postcode</em>, not the train.
      </p>
      <Legend />
      <RawVsAdjustedChart />
      <p style={{ marginBottom: "2rem" }}>
        To separate the two, we compared each home only against <strong>similar homes sold in the same Eircode area in
        the same year</strong> (a standard "hedonic" approach &mdash; see the methodology below). When you do that, the
        DART's 17% shrinks to about <strong>2%</strong>, the Green Line's 13% to roughly <strong>3.5%</strong>, and the
        Red Line stays negative. In other words, most of the apparent premium was the neighbourhood all along.
      </p>

      <SectionHeading>Does getting closer help? Sometimes.</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        A genuine transport effect should show up as a <em>gradient</em>: the closer you are, the more you pay. For the{" "}
        <strong>Green Line and DART</strong>, that broadly holds &mdash; median prices in the closest bands sit clearly
        above homes more than 2&nbsp;km away. For the <strong>Red Line</strong>, the line slopes the wrong way: prices{" "}
        <em>rise</em> as you move away from it, which is exactly what you'd expect if the stops sit in less expensive areas.
      </p>
      <Legend />
      <DoseResponseChart />
      <p style={{ marginBottom: "2rem" }}>
        This is why the Red Line's negative number should <strong>not</strong> be read as "a Luas stop lowers your house
        price." It reflects the character of the corridor &mdash; busier roads, industrial land, lower-priced housing
        &mdash; that even an area-level comparison can't fully strip out.
      </p>

      <SectionHeading>What it means if you're buying or selling</SectionHeading>
      <ul style={{ marginBottom: "2rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Being near the Luas or DART is a real amenity</strong> &mdash; but as a share of a Dublin home's price,
          the standalone premium is modest (low single digits), not the 15&ndash;20% a quick comparison suggests.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't overpay on the headline.</strong> If a home near a stop is priced well above comparable homes
          <em> in the same area</em>, you're likely paying for the neighbourhood, not the transport link.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Green Line proximity is the clearest positive signal</strong> in the data; the DART effect is weak once
          area is accounted for, despite the high headline prices along the coast.
        </li>
      </ul>

      <SectionHeading>How we did it (methodology)</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        This section is for readers who want to know exactly how the numbers were produced.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Data.</strong> We used every residential sale in County Dublin on the Property Price Register from
        January 2010 to July 2026, restricted to genuine arm's-length sales (excluding those flagged "not full market
        price"). Prices were trimmed to the 1st&ndash;99th percentile (€80,000&ndash;€2.2m) to remove bulk portfolio and
        mis-recorded sales. After geocoding, this left <strong>214,888 sales</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Distances.</strong> Each home's location was matched to the nearest stop on each line using the
        geolocated positions of 122 Dublin transport points (Luas Green and Red Line stops, DART stations, and other
        rail). "Near" means the nearest stop is within 1&nbsp;km, measured as true geographic distance.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>The raw comparison</strong> is just the median price of "near" homes versus "far" homes. It is shown
        only to illustrate how misleading it is on its own.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>The adjusted premium</strong> comes from a <em>hedonic regression</em>: we model the logarithm of sale
        price as a function of whether the home is within 1&nbsp;km of each line, plus a full set of{" "}
        <strong>Eircode-area fixed effects</strong> and <strong>year fixed effects</strong>. In plain terms, the model
        only ever compares homes to other homes <em>in the same postcode area, sold in the same year</em>, so
        neighbourhood and the rising market are held constant. The coefficient on "near the line" is then the premium
        attributable to proximity itself. This model used the <strong>89,169 sales</strong> that carry an Eircode routing
        key, across 35 Dublin areas with at least 50 sales each, with standard errors clustered by area. A robustness
        check adding property-type controls (house, apartment, terraced, etc.) on the subset where type is known gave the
        same picture: Green Line +5.3%, DART +3.6%, Red Line &minus;12.6%.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Limitations.</strong> This is an association, not a proven cause. The cleanest test &mdash; watching the
        same home's value before and after a new stop opens &mdash; isn't possible here, because all three lines predate
        almost all of the data. Eircode areas are fairly large, so some within-area differences (a home beside a busy
        junction versus a quiet terrace) remain uncaptured; this is the most likely reason the Red Line stays negative.
        And Eircode coverage (44% of sales) means the adjusted model uses a subset of the full dataset. We report the raw,
        the dose-response and the adjusted figures together precisely so the confounding is visible rather than hidden.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Want to see the sales behind these numbers?</strong> Use HomeIQ to explore actual sold prices near any
          Luas or DART stop, and get a free instant valuation for any Dublin address based on comparable sales.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>
    </div>
  );
}
