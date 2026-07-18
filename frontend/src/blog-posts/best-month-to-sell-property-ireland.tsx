import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — derived from analysis of 749,031 full-market PPR sales, Jan 2010 – Jul 2026.
// Volume index: each month's average share of its own year's sales (2010–2025),
//   expressed relative to an even split (8.33%/month = index 1.00).
// Price index: each month's median as a fraction of that year's annual median,
//   averaged across 2010–2025 (detrended, so it isolates the month-of-year effect).
// ---------------------------------------------------------------------------
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const VOLUME_SHARE = [5.64,6.69,7.42,6.86,7.62,8.01,9.16,8.23,8.81,9.52,9.50,12.54]; // % of annual sales
const PRICE_INDEX  = [98.35,96.53,96.33,97.22,96.97,100.39,101.07,102.96,102.64,103.11,102.03,100.39]; // vs annual median (100)

// Dublin vs rest-of-country price index (median vs own annual median, 2010–2025)
const PRICE_DUBLIN = [99.0,96.9,98.1,98.1,98.1,99.0,101.9,104.9,103.4,101.8,102.2,97.4];
const PRICE_REST   = [96.7,97.1,95.2,96.5,96.5,99.9,100.9,102.2,101.6,102.6,102.5,102.6];

// Palette (validated: blue↔amber diverging pair, CVD ΔE 81–151; every mark also
// carries a direct value label so identity never relies on color alone).
const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2563eb";      // above annual median / magnitude
const AMBER = "#b45309";     // below annual median (darkened from #f59e0b for text-adjacent contrast)
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

// --- Chart 1: Sales volume by month (magnitude → single-hue bars) ------------
function VolumeChart() {
  const W = 720, H = 360, padL = 44, padR = 16, padT = 24, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const maxV = 13; // % axis top
  const bw = plotW / MONTHS.length;
  const y = (v: number) => padT + plotH - (v / maxV) * plotH;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart of average share of annual property sales by month. December is highest at 12.5 percent, January lowest at 5.6 percent."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {/* gridlines + y labels */}
        {[0,3,6,9,12].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}%</text>
          </g>
        ))}
        {/* even-split reference */}
        <line x1={padL} x2={W - padR} y1={y(8.33)} y2={y(8.33)} stroke={INK_MUTED} strokeWidth={1} strokeDasharray="4 4" />
        <text x={W - padR} y={y(8.33) - 5} textAnchor="end" fontSize={10} fill={INK_MUTED}>even split (8.3%)</text>
        {/* bars */}
        {VOLUME_SHARE.map((v, i) => {
          const x = padL + i * bw + 3;
          const barW = bw - 6;
          const top = y(v);
          const isDec = i === 11;
          return (
            <g key={i}>
              <rect x={x} y={top} width={barW} height={padT + plotH - top} rx={4}
                    fill={isDec ? AMBER : BLUE} opacity={isDec ? 1 : 0.85}>
                <title>{`${MONTHS[i]}: ${v.toFixed(1)}% of annual sales`}</title>
              </rect>
              <text x={x + barW / 2} y={top - 5} textAnchor="middle" fontSize={10} fontWeight={600} fill={INK}>{v.toFixed(1)}</text>
              <text x={x + barW / 2} y={H - padB + 16} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{MONTHS[i]}</text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Average share of each year's sales that closed in a given month, 2010–2025. December (amber) is the
        busiest month in 15 of 16 years; January the quietest in 14 of 16. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

// --- Chart 2: Price vs annual median (polarity → diverging) ------------------
function PriceChart() {
  const W = 720, H = 360, padL = 52, padR = 16, padT = 24, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = 95, hi = 104; // y range around 100 = annual median
  const bw = plotW / MONTHS.length;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const base = y(100);

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart of median sale price by month relative to the annual median. Autumn months (August to November) sit above the annual median; spring months (February to May) sit below."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[96,98,100,102,104].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}</text>
          </g>
        ))}
        {/* zero/baseline = annual median */}
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke={INK} strokeWidth={1.5} />
        {PRICE_INDEX.map((v, i) => {
          const x = padL + i * bw + 3;
          const barW = bw - 6;
          const above = v >= 100;
          const top = above ? y(v) : base;
          const h = Math.abs(y(v) - base);
          return (
            <g key={i}>
              <rect x={x} y={top} width={barW} height={h} rx={4} fill={above ? BLUE : AMBER}>
                <title>{`${MONTHS[i]}: median ${v > 100 ? "+" : ""}${(v - 100).toFixed(1)}% vs annual median`}</title>
              </rect>
              <text x={x + barW / 2} y={above ? top - 5 : top + h + 12} textAnchor="middle" fontSize={9.5} fontWeight={600}
                    fill={above ? BLUE : AMBER}>{v > 100 ? "+" : ""}{(v - 100).toFixed(1)}</text>
              <text x={x + barW / 2} y={H - padB + 16} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{MONTHS[i]}</text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Median sale price by month as a percentage difference from the same year's median (100 = annual median),
        averaged 2010–2025. Blue = above the annual median, amber = below. Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

// --- Chart 3: Dublin vs rest of country (two-series line) --------------------
function DublinVsRestChart() {
  const W = 720, H = 360, padL = 52, padR = 90, padT = 24, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const lo = 94, hi = 106;
  const step = plotW / (MONTHS.length - 1);
  const x = (i: number) => padL + i * step;
  const y = (v: number) => padT + plotH - ((v - lo) / (hi - lo)) * plotH;
  const path = (arr: number[]) => arr.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Line chart comparing monthly median price index for Dublin and the rest of the country. Dublin peaks in August; the rest of the country peaks later, around October to December."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[96,98,100,102,104].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}</text>
          </g>
        ))}
        <line x1={padL} x2={W - padR} y1={y(100)} y2={y(100)} stroke={INK} strokeWidth={1.5} />
        {/* series */}
        <path d={path(PRICE_DUBLIN)} fill="none" stroke={BLUE} strokeWidth={2.5} />
        <path d={path(PRICE_REST)} fill="none" stroke={AMBER} strokeWidth={2.5} />
        {PRICE_DUBLIN.map((v, i) => (
          <circle key={`d${i}`} cx={x(i)} cy={y(v)} r={3.5} fill={BLUE}><title>{`Dublin — ${MONTHS[i]}: ${v}`}</title></circle>
        ))}
        {PRICE_REST.map((v, i) => (
          <circle key={`r${i}`} cx={x(i)} cy={y(v)} r={3.5} fill={AMBER}><title>{`Rest — ${MONTHS[i]}: ${v}`}</title></circle>
        ))}
        {/* direct series labels at the right edge */}
        <text x={W - padR + 6} y={y(PRICE_DUBLIN[11]) + 4} fontSize={12} fontWeight={600} fill={BLUE}>Dublin</text>
        <text x={W - padR + 6} y={y(PRICE_REST[11]) + 4} fontSize={12} fontWeight={600} fill={AMBER}>Rest of country</text>
        {MONTHS.map((mo, i) => (
          <text key={i} x={x(i)} y={H - padB + 16} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{mo}</text>
        ))}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Median sale price by month relative to each area's own annual median (100), averaged 2010–2025.
        Dublin's premium peaks sharply in August (+4.9%); outside Dublin the peak is flatter and later, running into December.
        Source: HomeIQ analysis of the Property Price Register.
      </figcaption>
    </figure>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", margin: "0 0 0.5rem", fontSize: "0.9rem", color: INK }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
        <span style={{ width: 14, height: 14, background: BLUE, borderRadius: 3, display: "inline-block" }} /> Above / stronger
      </span>
      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
        <span style={{ width: 14, height: 14, background: AMBER, borderRadius: 3, display: "inline-block" }} /> Below / December
      </span>
    </div>
  );
}

export function BestMonthToSellContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Is there a "best" month to sell your home in Ireland? To find out, we analysed{" "}
        <strong>749,031 full-market residential sales</strong> recorded on the Property Price Register between
        January 2010 and July 2026 &mdash; every genuine arm's-length sale in the country over more than a decade and a half.
        Two clear seasonal patterns emerge, and they point to the same answer.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The short answer:</strong> sales that close in <strong>late summer and autumn (August&ndash;November)</strong>
          {" "}fetch the highest prices relative to the rest of the year, and autumn is also when the most buyers are active.
          Because a sale typically closes 2&ndash;3 months after going on the market, that points to listing in roughly{" "}
          <strong>June&ndash;August</strong>.
        </p>
      </div>

      <SectionHeading>Transaction volume swings enormously by month</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The clearest seasonal signal is in <em>how many</em> homes change hands each month. Sales are far from evenly
        spread: the busiest month sees more than <strong>twice</strong> the volume of the quietest.
      </p>
      <Legend />
      <VolumeChart />
      <p style={{ marginBottom: "1rem" }}>
        December stands out dramatically, accounting for around <strong>12.5%</strong> of the year's sales &mdash; 50% above
        an even split &mdash; while January manages just <strong>5.6%</strong>. This is remarkably consistent: December was
        the busiest month in <strong>15 of the last 16 years</strong>, and January the quietest in 14.
      </p>
      <p style={{ marginBottom: "2rem" }}>
        A note on what this means: the Register records the <em>date of sale</em> (closing), not the listing date. The
        December bulge partly reflects buyers and solicitors pushing to complete before year-end, and sales that were
        agreed over the busy autumn selling season finally closing. The practical read for a seller is that the{" "}
        <strong>autumn&ndash;early winter window is when buyer demand and completed transactions peak.</strong>
      </p>

      <SectionHeading>Prices are highest in late summer and autumn</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Raw median prices barely move month to month &mdash; but that headline is dominated by the long-term rise in prices
        and by which areas happen to sell. To isolate the true <em>month-of-year</em> effect, we compared each month's
        median to <em>its own year's</em> median, then averaged across 2010&ndash;2025. This detrended view removes the
        overall market trend and reveals a genuine seasonal rhythm.
      </p>
      <Legend />
      <PriceChart />
      <p style={{ marginBottom: "1rem" }}>
        Sales closing in <strong>October (+3.1%), August (+3.0%) and September (+2.6%)</strong> come in above the annual
        median, while <strong>February and March (roughly &minus;3.5%)</strong> sit lowest. The peak-to-trough spread is
        about <strong>6.8%</strong> of the median price &mdash; on a €350,000 home, that's close to <strong>€24,000</strong>.
      </p>
      <p style={{ marginBottom: "2rem" }}>
        And this isn't noise from one or two years. August's median beat the annual median in <strong>14 of 16 years</strong>;
        July, September, October and November each did so in 13. Spring (February&ndash;May) landed below the annual median
        in all but two or three years. The seasonal pattern is one of the most stable findings in the whole dataset.
      </p>

      <SectionHeading>Why the seasons matter</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The two effects reinforce each other. More buyers are searching and bidding through the autumn, and competition
        among motivated buyers is what nudges sale prices above the yearly average. Spring, often assumed to be prime
        selling season, actually shows softer completed prices &mdash; likely because sales agreed in the quiet winter
        months close then.
      </p>
      <p style={{ marginBottom: "2rem" }}>
        Because a typical sale closes 2&ndash;3 months after it's agreed, aligning a <em>closing</em> in the strong
        August&ndash;October window means putting the property on the market in roughly <strong>June to August</strong> &mdash;
        listing into the autumn demand peak while buyers are active and before the winter slowdown.
      </p>

      <SectionHeading>Digging deeper: does it hold everywhere?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        A national average can hide as much as it reveals, so we split the data two ways. The seasonal pattern turns
        out to be robust &mdash; but with some interesting nuances.
      </p>

      <h3 style={{ fontSize: "1.4rem", fontWeight: 600, color: "#111827", marginTop: "2rem", marginBottom: "0.75rem" }}>
        Dublin vs the rest of the country
      </h3>
      <p style={{ marginBottom: "1rem" }}>
        Both markets are seasonal, but they peak at slightly different times. <strong>Dublin's price premium is sharpest
        and earliest</strong> &mdash; its median tops out in <strong>August at +4.9%</strong> above the annual median, an
        even bigger swing than the national figure. Outside Dublin the price peak is flatter and arrives later, holding
        up right through <strong>October to December</strong>. Volume seasonality is nearly identical in both: December
        busiest, January quietest, in each case a roughly 2.2&times; swing.
      </p>
      <Legend />
      <DublinVsRestChart />
      <p style={{ marginBottom: "2rem" }}>
        The practical implication: in Dublin the late-summer window is especially valuable, whereas sellers in the rest
        of the country have a longer autumn runway.
      </p>

      <h3 style={{ fontSize: "1.4rem", fontWeight: 600, color: "#111827", marginTop: "2rem", marginBottom: "0.75rem" }}>
        Higher-value vs lower-value sales
      </h3>
      <p style={{ marginBottom: "2rem" }}>
        Splitting each year's sales at the median price, the seasonal rhythm is <strong>strikingly consistent across
        both halves</strong>. Above-median and below-median homes both see December as the busiest month (12.4&ndash;12.7%
        of sales) and January the quietest (~5.5%), and both show their firmest prices in late summer. In other words,
        the "sell in autumn" edge isn't confined to premium or budget properties &mdash; it applies right across the price
        spectrum.
      </p>

      <SectionHeading>The bottom line</SectionHeading>
      <ul style={{ marginBottom: "2rem", paddingLeft: "1.5rem", listStyle: "disc" }}>
        <li style={{ marginBottom: "0.75rem" }}><strong>Best time to list:</strong> early summer to late summer (June&ndash;August), targeting an autumn close.</li>
        <li style={{ marginBottom: "0.75rem" }}><strong>Strongest completed prices:</strong> August&ndash;November (peak: October, +3.1% vs the annual median).</li>
        <li style={{ marginBottom: "0.75rem" }}><strong>Weakest prices:</strong> February&ndash;March (about &minus;3.5%).</li>
        <li style={{ marginBottom: "0.75rem" }}><strong>Busiest market:</strong> autumn into December; <strong>quietest:</strong> January.</li>
      </ul>
      <p style={{ marginBottom: "2rem", fontStyle: "italic", color: INK_MUTED }}>
        These are national averages across more than 749,000 sales. Local markets, property type and prevailing
        conditions can differ &mdash; a well-priced home in a sought-after area sells well in any month. Use the seasonal
        edge as a tailwind, not a rule.
      </p>

      <SectionHeading>Methodology &amp; caveats</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        For transparency, here's exactly how we produced these figures and where the limits lie:
      </p>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.5rem", listStyle: "disc", fontSize: "1.05rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Source &amp; scope.</strong> All 749,031 residential sales on Ireland's Property Price Register from
          January 2010 to July 2026, filtered to full-market transactions (we exclude sales flagged as not-full-market-price,
          which covers non-arm's-length transfers and many bulk/portfolio deals that would distort medians).
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>We use the median, not the average.</strong> A handful of multi-million-euro sales can drag a monthly
          mean around; the median (the middle sale) is far more stable and better represents a "typical" home.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Detrending &mdash; the key step.</strong> Raw monthly prices look almost flat because the long-term rise
          in prices swamps any seasonal effect. So instead of comparing January 2011 to October 2024 directly, we compare
          each month to <em>its own year's</em> median, then average those ratios across 2010&ndash;2025. That strips out
          the market trend and isolates the pure month-of-year effect. The same approach is used for volume (each month's
          share of its own year's sales). We used 16 complete calendar years (2010&ndash;2025) and excluded the partial
          2026 data from the seasonal averages.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>The biggest caveat: sale date &ne; listing date.</strong> The Register records when a sale <em>closed</em>,
          not when the home was listed or the price agreed. Since closing typically follows the agreed sale by 2&ndash;3
          months, our "list in June&ndash;August" advice is an <em>inference</em> from the strong August&ndash;October
          closing window &mdash; the data does not directly measure listing dates. The pronounced December volume spike is
          also partly an artefact of buyers and solicitors rushing to complete before year-end.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Correlation, not a guarantee.</strong> These are historical averages. They describe a consistent
          <em> tendency</em>, not a promise about any individual sale in any given year.
        </li>
      </ul>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Thinking of selling?</strong> Check what comparable homes have actually sold for in your area with a free{" "}
          <Link to="/valuation" style={{ color: "#3b82f6", textDecoration: "underline" }}>property valuation</Link>, or explore
          local sale prices and trends on the{" "}
          <Link to="/" style={{ color: "#3b82f6", textDecoration: "underline" }}>interactive map</Link>.
        </p>
      </div>
    </div>
  );
}
