import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — HomeIQ analysis of 214,888 full-market Dublin residential sales on the
// Property Price Register, Jan 2010 – Jul 2026 (price trimmed to the 1st–99th
// percentile, €80k–€2.2m). Distance to each institution type computed by PostGIS
// nearest-neighbour against 45 geocoded key Dublin schools/universities.
// Adjusted premiums: hedonic regression of log(price) with Eircode-area and
// year fixed effects (89,169 sales, 35 areas).
// ---------------------------------------------------------------------------

// Palette — dataviz reference categorical slots 1–3 (pre-validated all-pairs).
const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";   // Primary
const ORANGE = "#eb6834"; // Secondary
const AQUA = "#1baf7a";   // University / college
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";

const LEVELS = [
  { key: "primary", label: "Primary school", color: BLUE },
  { key: "secondary", label: "Secondary school", color: ORANGE },
  { key: "tertiary", label: "University / college", color: AQUA },
];

const RAW_GAP = { primary: 31.9, secondary: 31.9, tertiary: -11.0 };   // %
const ADJ_PREMIUM = { primary: 10.1, secondary: 8.9, tertiary: -5.9 }; // %

const BANDS = ["0–250m", "250–500m", "500m–1km", "1–2km", ">2km"];
const DOSE: Record<string, number[]> = {
  primary: [568, 475, 465, 415, 350],
  secondary: [500, 488, 455, 408, 333],
  tertiary: [308, 320, 340, 405, 367],
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
      {LEVELS.map((l) => (
        <span key={l.key} style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ width: 14, height: 14, background: l.color, borderRadius: 3, display: "inline-block" }} /> {l.label}
        </span>
      ))}
    </div>
  );
}

// --- Chart 1: Raw gap vs adjusted premium -------------------------------------
function RawVsAdjustedChart() {
  const W = 720, H = 380, padL = 56, padR = 16, padT = 28, padB = 56;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = -15, hi = 35;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const base = y(0);
  const groupW = plotW / LEVELS.length;
  const barW = groupW / 2 - 14;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Grouped bar chart comparing the raw near-versus-far price gap with the adjusted premium for each school level. Primary and secondary schools show raw gaps of plus 32 percent that fall to about plus 9 to 10 percent when adjusted for area and year; universities show a negative gap in both."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[-15, -5, 5, 15, 25, 35].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g > 0 ? "+" : ""}{g}%</text>
          </g>
        ))}
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke={INK} strokeWidth={1.5} />
        {LEVELS.map((l, i) => {
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
        <g transform={`translate(${padL}, ${H - 14})`}>
          <rect x={0} y={-9} width={13} height={13} rx={3} fill={NEUTRAL} opacity={0.45} />
          <text x={18} y={2} fontSize={11} fill={INK_MUTED}>Raw gap (near vs far)</text>
          <rect x={190} y={-9} width={13} height={13} rx={3} fill={SURFACE} stroke={NEUTRAL} strokeWidth={2} />
          <text x={208} y={2} fontSize={11} fill={INK_MUTED}>Adjusted (same area & year)</text>
        </g>
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Solid bars: the raw difference in median price between homes within 1&nbsp;km of a school and those further away.
        Outlined bars: the premium left once we compare like-with-like homes in the <em>same Eircode area and year</em>.
        For schools, a real premium survives; for universities it does not. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

// --- Chart 2: Distance dose-response ------------------------------------------
function DoseResponseChart() {
  const W = 720, H = 380, padL = 56, padR = 110, padT = 28, padB = 48;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = 300, hi = 580;
  const step = plotW / (BANDS.length - 1);
  const x = (i: number) => padL + i * step;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const path = (arr: number[]) => arr.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Line chart of median sale price by distance band to each school level. Primary and secondary schools show prices falling steeply as distance increases; universities show the reverse, with prices rising with distance."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[350, 425, 500, 575].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>€{g}k</text>
          </g>
        ))}
        {LEVELS.map((l) => {
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
        Median sale price by how far the home is from the nearest institution of each type (raw, not adjusted for area).
        Homes get steadily cheaper the further they are from a primary or secondary school; near a university the pattern
        is reversed. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

export function SchoolPremiumContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Every parent knows the phrase "good school catchment," and estate agents lean on it hard. But does living close to
        a school actually push up what a home sells for &mdash; and is it schools that matter, or universities too? We
        analysed <strong>214,888 full-market Dublin sales</strong> on the Property Price Register from January 2010 to
        July 2026, measuring each home's distance to the nearest primary school, secondary school and university/college.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The short answer:</strong> yes &mdash; being within 1&nbsp;km of a school is linked to a real premium of
          about <strong>8&ndash;10%</strong>, and unlike many "location" effects it <em>survives</em> once you compare
          similar homes in the same area. Being near a <strong>university or college</strong> shows no premium (slightly
          negative). Notably, this school effect is <strong>stronger and more robust</strong> than the Luas/DART transport
          premium we found in a{" "}
          <Link to="/blog/does-being-near-a-luas-or-dart-add-value" style={{ color: "#1d4ed8", fontWeight: 600 }}>companion analysis</Link>.
        </p>
      </div>

      <SectionHeading>The raw numbers look huge &mdash; and partly mislead</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Compare the median price of homes within 1&nbsp;km of a school against those further away and the gap is dramatic:
        homes near a primary or secondary school sell for around <strong>32% more</strong>. Homes near a university,
        oddly, sell for <strong>11% less</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        Some of that is the familiar trap: sought-after schools sit in leafy, expensive suburbs, while universities and
        colleges cluster in the city centre and student areas where homes are smaller and cheaper. So part of the raw gap
        is really about the <em>neighbourhood</em>. The question is how much survives once we strip the neighbourhood out.
      </p>
      <Legend />
      <RawVsAdjustedChart />
      <p style={{ marginBottom: "2rem" }}>
        Comparing each home only against <strong>similar homes sold in the same Eircode area in the same year</strong>,
        the school premium shrinks &mdash; but crucially it <strong>does not disappear</strong>. Primary school proximity
        holds a premium of about <strong>10%</strong> and secondary about <strong>9%</strong>, both statistically
        significant. The university effect stays negative. In our transport study the DART's headline premium vanished
        after this same adjustment; here, the school premium stands its ground.
      </p>

      <SectionHeading>Closer really is dearer</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        A genuine amenity effect should show a smooth gradient &mdash; the nearer you are, the more you pay &mdash; and
        for schools it's textbook. Homes within 250&nbsp;m of a primary school have a median price of{" "}
        <strong>€568,000</strong>, easing to <strong>€465,000</strong> at 500m&ndash;1km and <strong>€350,000</strong>{" "}
        beyond 2&nbsp;km. Secondary schools show the same steady decline. Universities slope the other way &mdash; prices{" "}
        <em>rise</em> with distance &mdash; confirming that the campus effect is about location, not desirability.
      </p>
      <Legend />
      <DoseResponseChart />
      <p style={{ marginBottom: "2rem" }}>
        That clean, monotonic gradient is exactly what you'd expect if buyers genuinely value being near a school. It's a
        cleaner signal than we saw for any transport line.
      </p>

      <SectionHeading>What it means if you're buying or selling</SectionHeading>
      <ul style={{ marginBottom: "2rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>A good-school location is a genuine, sizeable premium.</strong> Roughly 8&ndash;10% of value is
          attributable to school proximity itself &mdash; more than double the Luas/DART effect.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Family homes benefit most.</strong> The premium is strongest for the primary/secondary "school run"
          radius that families walk &mdash; a walkable school is worth paying for, and worth highlighting when selling.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>"Near a university" is not a selling point for value.</strong> Campus-adjacent homes skew to smaller,
          cheaper, rental-oriented stock; proximity there doesn't lift owner-occupier prices.
        </li>
      </ul>

      <SectionHeading>How we did it (methodology)</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Data.</strong> Every residential sale in County Dublin on the Property Price Register from January 2010 to
        July 2026, restricted to genuine arm's-length sales (excluding "not full market price"), with prices trimmed to
        the 1st&ndash;99th percentile (€80,000&ndash;€2.2m) to remove bulk and mis-recorded sales. After geocoding, this
        left <strong>214,888 sales</strong>.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Distances.</strong> Each home was matched to the nearest institution of each type using the geolocated
        positions of 45 key Dublin schools and universities. "Near" means the nearest one is within 1&nbsp;km, measured as
        true geographic distance. Schools spanning both levels count as both primary and secondary.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>The adjusted premium</strong> comes from a <em>hedonic regression</em>: we model the logarithm of sale
        price against whether the home is within 1&nbsp;km of each institution type, plus a full set of{" "}
        <strong>Eircode-area fixed effects</strong> and <strong>year fixed effects</strong>. The model only ever compares
        homes to others <em>in the same postcode area, sold in the same year</em>, holding neighbourhood and the rising
        market constant. This used the <strong>89,169 sales</strong> with an Eircode routing key, across 35 areas with at
        least 50 sales each, standard errors clustered by area. Adding property-type controls (house, apartment, etc.) on
        the subset where type is known gave the same result: primary +9.4%, secondary +7.3%, university not significant.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Limitations.</strong> This is an association, not proof of cause. Most importantly, our dataset covers{" "}
        <strong>45 notable Dublin institutions, not every school</strong> &mdash; so this measures proximity to a{" "}
        <em>key</em> school, and likely overstates the effect a full schools list would show, since notable schools
        cluster in desirable areas in ways even area-level controls can't fully remove. Eircode areas are also fairly
        large, leaving some within-area differences uncaptured. We report the raw, dose-response and adjusted figures
        together so the confounding is visible rather than hidden.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Curious what homes near your school of choice actually sold for?</strong> Use HomeIQ to explore real sold
          prices in any Dublin area, and get a free instant valuation for any address based on comparable sales.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>
    </div>
  );
}
