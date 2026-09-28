import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Data — Barings' possible €1.386/share cash offer for IRES REIT plc, announced
// under Rule 2.4 of the Irish Takeover Rules on 28 September 2026 ("Statement
// regarding possible offer", iresreit.ie). This post revisits our earlier
// sum-of-parts valuation of the IRES portfolio (blog:
// valuing-ires-reit-property-portfolio) and sets the offer price against it.
//
// Offer facts (IRES Rule 2.4 announcement, 28 Sep 2026):
//   • Barings (Baring International Investment Limited) — all-cash offer for the
//     entire issued and to-be-issued ordinary share capital of I-RES.
//   • Price €1.386 per share (138.6c); fifth proposal; first received 5 Aug 2026.
//   • Board has unanimously concluded it would be "minded to recommend" a firm
//     offer at this price, subject to confirmatory due diligence and final terms.
//   • Not yet a firm offer (Rule 2.7). Rule 2.6(a) "put up or shut up" deadline:
//     5.00pm 9 November 2026.
//   • Shares in issue: 524,442,218 (Rule 2.12 disclosure).
//   ⇒ Equity value at the offer ≈ €1.386 × 524.442m ≈ €726.9m.
//
// IRES reported figures (H1 2026 Interim Report, as at 30 June 2026):
//   IFRS NAV €727.9m = 138.8c/share; net debt €533.6m; Net LTV 42.6%.
//
// HomeIQ sum-of-parts estimate (prior post): portfolio €1,522.9m ⇒ NAV €974.1m
//   = 185.7c/share (+34% vs reported NAV). At IRES's realised +25% unit-resale
//   premium: portfolio €1,595.9m ⇒ NAV €1,047.1m = 199.7c/share.
// Debt (€533.6m) and share count (524.4m) held constant across all bases.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const ORANGE = "#eb6834";
const AQUA = "#1baf7a";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";

// Per-share value under each basis (cents). Equity in € millions.
const BASIS_ROWS = [
  { label: "Barings offer (cash)", perShare: 138.6, equity: "€726.9m", note: "the price on the table", color: ORANGE },
  { label: "IRES reported NAV (IFRS)", perShare: 138.8, equity: "€727.9m", note: "rented-block book value, 30 Jun 2026", color: NEUTRAL },
  { label: "Our open-market estimate", perShare: 185.7, equity: "€974.1m", note: "flats sold individually today", color: BLUE },
  { label: "At IRES's realised +25% resale", perShare: 199.7, equity: "€1,047.1m", note: "premium IRES itself achieves on unit sales", color: AQUA },
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
    { big: "€1.386", small: "per-share cash offer" },
    { big: "≈ €727m", small: "equity value" },
    { big: "≈ NAV", small: "0% premium to book" },
    { big: "9 Nov 2026", small: '"put up or shut up" deadline' },
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

// --- Chart: per-share value by basis ------------------------------------------
function BasisChart() {
  const W = 720, H = 340, padL = 48, padR = 16, padT = 28, padB = 82;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const hi = 220;
  const y = (v: number) => padT + plotH - (v / hi) * plotH;
  const groupW = plotW / BASIS_ROWS.length;
  const barW = groupW * 0.46;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart comparing value per IRES share under four bases. Barings' cash offer is 138.6 cents, reported IFRS NAV is 138.8 cents, our open-market estimate is 186 cents, and at IRES's realised 25 percent resale premium it is 200 cents. The offer sits level with book NAV and about 25 percent below our estimate."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[0, 50, 100, 150, 200].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={y(g)} y2={y(g)} stroke={GRID} strokeWidth={1} />
            <text x={padL - 8} y={y(g) + 4} textAnchor="end" fontSize={11} fill={INK_MUTED}>{g}c</text>
          </g>
        ))}
        {/* Offer reference line across the plot */}
        <line x1={padL} x2={W - padR} y1={y(138.6)} y2={y(138.6)} stroke={ORANGE} strokeWidth={1.5} strokeDasharray="5 4" opacity={0.7} />
        {BASIS_ROWS.map((r, i) => {
          const cx = padL + i * groupW + groupW / 2;
          const top = y(r.perShare);
          const labels = ["Barings offer", "Reported NAV", "Our estimate", "IRES's +25% resale"];
          return (
            <g key={r.label}>
              <rect x={cx - barW / 2} y={top} width={barW} height={padT + plotH - top} rx={4} fill={r.color} opacity={0.85}>
                <title>{`${r.label}: ${r.perShare}c per share`}</title>
              </rect>
              <text x={cx} y={top - 8} textAnchor="middle" fontSize={13} fontWeight={700} fill={r.color}>{r.perShare}c</text>
              <text x={cx} y={H - padB + 22} textAnchor="middle" fontSize={11.5} fontWeight={600} fill={INK}>{labels[i]}</text>
              <text x={cx} y={H - padB + 40} textAnchor="middle" fontSize={10.5} fill={INK_MUTED}>{r.equity}</text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Value per IRES share under four bases. Barings' €1.386 cash offer (dashed line) lands almost exactly on IRES's
        reported IFRS NAV — but roughly 25% below our estimate of what the flats would fetch sold individually. Sources:
        IRES Rule 2.4 announcement (28 Sep 2026) and H1 2026 Interim Report; HomeIQ valuation of the Property Price Register.
      </figcaption>
    </figure>
  );
}

export function BaringsIresTakeoverContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        On <strong>28 September 2026</strong>, Ireland's largest private residential landlord —{" "}
        <strong>IRES REIT plc</strong> — confirmed it had received a cash takeover approach from{" "}
        <strong>Barings</strong>, the global asset manager, at <strong>€1.386 per share</strong>. The IRES board said it
        would be "minded to recommend" a firm offer at that level. A few weeks earlier we had valued the entire IRES
        portfolio, apartment by apartment, using nothing but public sold-price data. So we can ask the question every IRES
        shareholder is now asking: <em>is €1.386 a fair price — or is the portfolio being bought on the cheap?</em>
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The headline:</strong> Barings' <strong>€1.386</strong> cash offer values IRES's equity at about{" "}
          <strong>€727 million</strong> — almost exactly its reported <strong>138.8-cent</strong> book NAV. That is a
          healthy premium to where the shares had been <em>trading</em> (they jumped ~20% on the news), but it is a{" "}
          <strong>0% premium to net asset value</strong> and roughly <strong>25% below</strong> our estimate of what the
          underlying flats would fetch sold individually (~<strong>186 cents</strong>). On our numbers Barings is capturing
          the break-up premium — around <strong>€247 million</strong>, or ~47c a share — rather than paying for it.
        </p>
      </div>

      <SectionHeading>What Barings has actually offered</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The 28 September statement is a <strong>Rule 2.4 "possible offer"</strong> announcement under the Irish Takeover
        Rules — not yet a firm, binding bid. The key facts:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Price:</strong> €1.386 in <strong>cash</strong> per ordinary share, for the entire issued and to-be-issued
          share capital.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Bidder:</strong> Baring International Investment Limited ("Barings"), advised by Barings; IRES is advised
          by Rothschild&nbsp;&amp;&nbsp;Co, Barclays and Davy.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>History:</strong> this is the <strong>fifth proposal</strong> from Barings; the first arrived on{" "}
          <strong>5 August 2026</strong>. Each was pitched higher — the board has clearly been negotiating the price up.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Board stance:</strong> IRES has <strong>unanimously</strong> concluded it would be "minded to recommend" a
          firm offer at €1.386, subject to satisfactory confirmatory due diligence and agreement on final terms.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Timeline:</strong> under Rule 2.6(a), Barings must either announce a firm intention to bid (Rule 2.7) or
          walk away by <strong>5.00pm on 9 November 2026</strong>. There is, as ever, "no certainty that a firm offer will
          be made".
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        With <strong>524,442,218 shares</strong> in issue, €1.386 a share puts a headline equity value of roughly{" "}
        <strong>€727 million</strong> on IRES.
      </p>
      <StatCards />

      <SectionHeading>The two benchmarks that matter</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Whether €1.386 is "fair" depends entirely on what you compare it to. There are two very different yardsticks, and the
        offer looks completely different against each.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Against the share price, it's a good premium.</strong> Like most European REITs, IRES had spent years trading
        at a persistent <em>discount</em> to its net asset value — the market simply would not pay book value for a
        rent-capped, geared residential landlord. The bid closed much of that gap in a day: the shares spiked around{" "}
        <strong>20%</strong> to roughly their 52-week high on the news. A shareholder who bought at the depressed pre-bid
        price is being offered a real, immediate cash uplift.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Against asset value, it's thin.</strong> €1.386 is almost identical to IRES's own reported IFRS NAV of{" "}
        <strong>138.8 cents</strong> (as at 30 June 2026). So Barings is offering to buy the company for essentially{" "}
        <em>book value</em> — a <strong>0% premium to NAV</strong>. Control of a whole listed portfolio usually commands a
        premium <em>above</em> NAV, not a price level with it.
      </p>

      <SectionHeading>What we think the bricks are actually worth</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        This is where our earlier work comes in. In our{" "}
        <Link to="/blog/valuing-ires-reit-property-portfolio" style={{ color: "#1d4ed8", fontWeight: 600 }}>
          portfolio valuation
        </Link>{" "}
        we ran all <strong>35 developments</strong> and <strong>3,615 IRES-owned units</strong> through the same engine that
        powers our public <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>valuation tool</Link> —
        pricing each apartment against genuine, arm's-length resale comparables from the Property Price Register,
        time-adjusted to today and weighted by distance, recency, bedroom count and property type. The sum came to about{" "}
        <strong>€1.52 billion</strong> on an open-market, sold-individually basis — roughly <strong>19% above</strong> the
        €1.28bn IRES carries on its balance sheet.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        Because IRES is geared — about <strong>€534 million</strong> of net debt sits in front of the equity — that 19%
        uplift in the <em>property</em> is amplified roughly <strong>1.75×</strong> in <em>NAV per share</em>. Marking the
        portfolio to our estimate lifts NAV from 138.8c to about <strong>185.7 cents</strong> a share (+34%). And that is
        arguably conservative: IRES's own disposals of vacant units have fetched <strong>25–30% above book</strong>, which
        would imply a NAV nearer <strong>200 cents</strong>.
      </p>

      <figure style={{ margin: "1.5rem 0 1.5rem" }}>
        <div style={{ overflowX: "auto", border: `1px solid ${GRID}`, borderRadius: "0.5rem" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.92rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Basis</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Per share</th>
                <th style={{ textAlign: "right", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>Equity value</th>
                <th style={{ textAlign: "left", padding: "0.6rem 0.85rem", fontSize: "0.8rem", fontWeight: 700, color: INK, borderBottom: `2px solid ${GRID}`, background: "#fff" }}>What it represents</th>
              </tr>
            </thead>
            <tbody>
              {BASIS_ROWS.map((r, i) => (
                <tr key={r.label} style={{ background: i % 2 ? SURFACE : "#fff" }}>
                  <td style={{ padding: "0.5rem 0.85rem", color: INK, borderBottom: `1px solid ${GRID}`, fontWeight: 600 }}>{r.label}</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: "#111827", borderBottom: `1px solid ${GRID}`, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{r.perShare.toFixed(1)}c</td>
                  <td style={{ padding: "0.5rem 0.85rem", textAlign: "right", color: INK, borderBottom: `1px solid ${GRID}`, fontVariantNumeric: "tabular-nums" }}>{r.equity}</td>
                  <td style={{ padding: "0.5rem 0.85rem", color: INK_MUTED, borderBottom: `1px solid ${GRID}`, fontSize: "0.86rem" }}>{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
          Value per IRES share on four bases, holding net debt (€533.6m) and shares (524.4m) constant. The offer matches
          reported NAV almost to the cent, and sits ~25% below our open-market sum-of-parts estimate.
        </figcaption>
      </figure>

      <BasisChart />

      <p style={{ marginBottom: "1rem" }}>
        Set the offer beside those numbers and the gap is stark. Barings is paying <strong>138.6c</strong> for something our
        model says is worth around <strong>185.7c</strong> a share broken up and sold. That difference — about{" "}
        <strong>47 cents a share</strong>, or roughly <strong>€247 million</strong> in aggregate — is the{" "}
        <strong>break-up premium</strong>: the extra value locked up in the fact that the portfolio is worth more sold flat
        by flat than held as a rented block. In this deal, that premium accrues to <em>the buyer</em>, not the selling
        shareholders.
      </p>

      <SectionHeading>Why the board can back a price at book value</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        It might look odd for a board to endorse selling at NAV when the assets arguably support more. But there is a
        coherent logic to it, and it comes down to the difference between a rented block and a broken-up portfolio.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        IRES's IFRS NAV is an <strong>investment-basis</strong> valuation: the flats are valued as a tenanted,
        income-producing block, capitalised at a market yield and constrained by Ireland's <strong>Rent Pressure Zone</strong>{" "}
        caps. Our €1.52bn is the opposite construct — the sum of what each flat would fetch sold <em>individually, with
        vacant possession</em>. Realising that higher number in practice means <strong>emptying and selling ~3,600 units one
        by one</strong> over many years: slow, costly, taxed at the point of sale for most owners, and impossible to
        guarantee. A single cash buyer taking the whole book in one line will always pay closer to block value than
        sum-of-parts. So a bid at NAV isn't irrational — but it does mean shareholders hand the break-up upside to Barings
        rather than capturing it themselves.
      </p>

      <SectionHeading>So — accept or reject?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        There is a genuine case on both sides, and reasonable long-term holders can land in different places.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem", margin: "1.25rem 0 1.75rem" }}>
        <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#15803d", marginTop: 0, marginBottom: "0.6rem" }}>The case to accept</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>Certain cash, today.</strong> A ~20% premium to the undisturbed price, in hand now, versus a discount that had persisted for years.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>REITs rarely trade at NAV.</strong> Without a bid, the shares would likely keep trading below book — the offer closes that gap.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>The break-up value is theoretical.</strong> Capturing it needs years of vacant-possession sales, with cost, tax and execution risk.</li>
            <li><strong>Rate and regulatory overhang.</strong> RPZ caps and interest-rate risk cloud the standalone outlook.</li>
          </ul>
        </div>
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem", padding: "1.1rem 1.25rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#b91c1c", marginTop: 0, marginBottom: "0.6rem" }}>The case to hold out</h3>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
            <li style={{ marginBottom: "0.5rem" }}><strong>Zero premium to NAV.</strong> Control of an entire portfolio usually commands a premium <em>above</em> book, not a price level with it.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>Barings pockets the upside.</strong> Our numbers put the sum-of-parts ~25% higher; that ~€247m gap goes to the buyer.</li>
            <li style={{ marginBottom: "0.5rem" }}><strong>IRES's own sales beat book by 25–30%.</strong> Management's disposal record undercuts the idea that NAV is the ceiling.</li>
            <li><strong>Room to move.</strong> Five rising proposals and a possible-offer structure suggest the price could still be pushed — or a rival could emerge.</li>
          </ul>
        </div>
      </div>

      <p style={{ marginBottom: "2rem" }}>
        Our reading: <strong>€1.386 is fair against the share price but light against the assets</strong>. It fully values
        IRES as a rented block and hands buyers the break-up premium for free. For a shareholder who wants out of a
        perennially discounted, rate-and-RPZ-exposed stock, a clean cash exit at a 20% pop is a perfectly rational "yes". For
        one who believes the bricks are worth what our model — and IRES's own disposals — say they are, €1.386 looks like the
        floor of a negotiation rather than the finish line. The board's "minded to recommend" is a starting position, not a
        done deal: the firm-offer deadline is <strong>9 November</strong>, and until then the price is not settled.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Curious what your own home is worth?</strong> The same engine we pointed at IRES's €1.5bn book will value a
          single Irish address in seconds — from real comparable sales, with the comparables and confidence shown.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        Offer details are from IRES REIT plc's Rule 2.4 "Statement regarding possible offer" (28 September 2026); financial
        figures are IRES's own reported numbers as at 30 June 2026 (H1 2026 Interim Report). At the date of writing this is a
        possible offer only, not a firm offer under Rule 2.7, and there is no certainty a firm offer will be made. HomeIQ
        valuations are an indicative statistical model based on Property Price Register resale comparables and are not a
        valuation of record. Nothing here is investment advice or a recommendation regarding any security; do your own
        research and, if in doubt, seek independent professional advice.
      </p>
    </div>
  );
}
