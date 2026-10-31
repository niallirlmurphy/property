import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Follow-up to blog: barings-ires-reit-takeover-offer-fair-value (28 Sep 2026).
// Status as at 31 October 2026: still a Rule 2.4 possible offer; no Rule 2.7 firm
// offer announced. Rule 2.6(a) "put up or shut up" deadline 5.00pm 9 Nov 2026.
//
// Offer: €1.386 cash per share × 524,442,218 shares ≈ €726.9m equity.
// Undisturbed share price €1.06 ⇒ premium 1.386 / 1.06 − 1 = 30.75%.
// EPRA NTA / IFRS NAV ≈ 138.8c (H1 2026, 30 Jun 2026) ⇒ offer ≈ −0.1% vs NAV.
// HomeIQ sum-of-parts (earlier posts): portfolio €1,522.9m vs €1.28bn book (+19%),
//   net debt €533.6m ⇒ NAV €974.1m = 185.7c ⇒ offer 25.4% below. Break-up gap
//   185.7 − 138.6 = 47.1c × 524.4m ≈ €247m. At IRES's +25% resale: 199.7c.
//
// VAT: the September run (scripts/value_ires_portfolio.py) priced comparables at
// the register price, which is ex-VAT for new homes. Valuations have added VAT
// back since 27 Oct 2026 (backend/price_vat.py: 13.5%; 9% on new apartments sold
// 8 Oct 2025–2030). Not re-run; direction only (up).
// CSO (frontend/src/data/cso.json, blog: property-price-register-vs-cso-house-prices):
//   2025 second-hand medians, register vs CSO: Dublin −1.2%; typical routing key ±1.2%.
//   RPPI 12-month change to Aug 2026: Dublin apartments +5.7%, Dublin houses +3.3%.
// Holdings: TR-1 notifications on IRES's regulatory news page (otp.tools.investis.com
// ires_reit2), 20 Aug–30 Oct 2026. FMR 6.9836% → 3.6271% on 8 Oct = 3.3565% × 524.44m
// ≈ 17.6m shares. Starwood, Janus Henderson and Vision Capital: no filing in that window.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const ORANGE = "#eb6834";
const AQUA = "#1baf7a";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";
const NEUTRAL = "#9ca3af";

// The offer measured against each yardstick (percent premium, negative = discount).
const PREMIA = [
  { label: "Undisturbed share price (€1.06)", pct: 30.75, color: AQUA },
  { label: "Reported NAV (138.8c)", pct: -0.1, color: NEUTRAL },
  { label: "Our open-market estimate (185.7c)", pct: -25.4, color: BLUE },
  { label: "At IRES's +25% resale (199.7c)", pct: -30.6, color: ORANGE },
];

const TIMELINE = [
  { date: "5 Aug 2026", text: "Barings makes its first proposal to the IRES board.", done: true },
  { date: "Aug–Sep 2026", text: "Four more proposals follow, each pitched higher.", done: true },
  { date: "28 Sep 2026", text: "Rule 2.4 announcement: possible cash offer at €1.386; board \"minded to recommend\" a firm offer at that price.", done: true },
  { date: "8 Oct 2026", text: "FMR (Fidelity) cuts its stake from 6.98% to 3.63%, selling about 17.6 million shares into the rally.", done: true },
  { date: "9–29 Oct 2026", text: "Millennium, Goldman Sachs and Sand Grove each disclose positions above 3%.", done: true },
  { date: "31 Oct 2026", text: "No firm offer yet. Barings is still in confirmatory due diligence.", done: true },
  { date: "9 Nov 2026, 5pm", text: "Put-up-or-shut-up deadline: a Rule 2.7 firm offer, a statement that Barings won't bid, or a Panel-approved extension.", done: false },
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
    { big: "+30.75%", small: "premium to undisturbed €1.06" },
    { big: "≈ 0%", small: "premium to NAV" },
    { big: "−25%", small: "vs our open-market NAV" },
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

// --- Chart: premium / discount of the offer against each yardstick -----------
function PremiumChart() {
  const W = 720, rowH = 46, padT = 16, padB = 30, labelW = 250, padR = 60;
  const H = padT + PREMIA.length * rowH + padB;
  const lo = -40, hi = 40;
  const plotW = W - labelW - padR;
  const x = (v: number) => labelW + ((v - lo) / (hi - lo)) * plotW;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Bar chart of Barings' 1.386 euro offer against four yardsticks. It is a 30.75 percent premium to the undisturbed share price of 1.06 euro, level with reported NAV, 25.4 percent below our open-market estimate, and 30.6 percent below NAV at IRES's realised 25 percent resale premium."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {[-40, -20, 0, 20, 40].map((g) => (
          <g key={g}>
            <line x1={x(g)} x2={x(g)} y1={padT} y2={H - padB} stroke={g === 0 ? INK_MUTED : GRID} strokeWidth={1} />
            <text x={x(g)} y={H - padB + 18} textAnchor="middle" fontSize={11} fill={INK_MUTED}>{g > 0 ? `+${g}` : g}%</text>
          </g>
        ))}
        {PREMIA.map((r, i) => {
          const cy = padT + i * rowH + rowH / 2;
          const x0 = x(Math.min(0, r.pct)), x1 = x(Math.max(0, r.pct));
          return (
            <g key={r.label}>
              <text x={labelW - 10} y={cy + 4} textAnchor="end" fontSize={12} fill={INK}>{r.label}</text>
              <rect x={x0} y={cy - 12} width={Math.max(x1 - x0, 2)} height={24} rx={3} fill={r.color} opacity={0.85}>
                <title>{`${r.label}: ${r.pct > 0 ? "+" : ""}${r.pct}%`}</title>
              </rect>
              <text x={r.pct >= 0 ? x1 + 6 : x0 - 6} y={cy + 4} textAnchor={r.pct >= 0 ? "start" : "end"} fontSize={12} fontWeight={700} fill={r.color}>
                {r.pct > 0 ? "+" : ""}{r.pct}%
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Barings' €1.386 offer as a premium (right) or discount (left) to four yardsticks. Generous against the share price,
        level with book value, and a quarter below what the flats would fetch sold one by one. Sources: IRES Rule 2.4
        announcement (28 Sep 2026) and H1 2026 Interim Report; HomeIQ valuation of the Property Price Register.
      </figcaption>
    </figure>
  );
}

// Major-holding notifications (TR-1) published by IRES, 20 Aug – 30 Oct 2026.
const HOLDINGS = [
  { holder: "FMR (Fidelity)", date: "19 Aug", from: "8.90%", to: "7.95%", dir: "down" },
  { holder: "FMR (Fidelity)", date: "4–10 Sep", from: "7.95%", to: "6.98%", dir: "down" },
  { holder: "BlackRock", date: "28 Sep", from: "3.99%", to: "4.07%", dir: "up" },
  { holder: "FMR (Fidelity)", date: "8 Oct", from: "6.98%", to: "3.63%", dir: "down" },
  { holder: "Goldman Sachs", date: "8–27 Oct", from: "–", to: "2.96–3.73%", dir: "flat" },
  { holder: "Millennium (derivatives)", date: "9 Oct", from: "–", to: "3.25%", dir: "up" },
  { holder: "Sand Grove Capital", date: "29 Oct", from: "–", to: "3.20%", dir: "up" },
];

function HoldingsTable() {
  const cell = { padding: "0.5rem 0.75rem", borderBottom: `1px solid ${GRID}`, textAlign: "left" as const };
  const color = { up: AQUA, down: ORANGE, flat: INK_MUTED } as const;
  return (
    <figure style={{ margin: "1.5rem 0 2rem", overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem", background: SURFACE, border: `1px solid ${GRID}` }}>
        <thead>
          <tr style={{ color: INK_MUTED, fontSize: "0.85rem" }}>
            <th style={cell}>Holder</th><th style={cell}>Crossed on</th><th style={cell}>From</th><th style={cell}>To</th>
          </tr>
        </thead>
        <tbody>
          {HOLDINGS.map((h) => (
            <tr key={h.holder + h.date}>
              <td style={cell}>{h.holder}</td>
              <td style={cell}>{h.date}</td>
              <td style={cell}>{h.from}</td>
              <td style={{ ...cell, fontWeight: 700, color: color[h.dir as keyof typeof color] }}>{h.to}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Voting rights, including financial instruments, as a share of IRES's 524.4 million shares. Goldman Sachs filed eight
        notices around the 3% line; the range is shown. Source: TR-1 notifications published by IRES REIT plc.
      </figcaption>
    </figure>
  );
}

function Timeline() {
  return (
    <ol style={{ listStyle: "none", padding: 0, margin: "1.5rem 0 2rem", borderLeft: `2px solid ${GRID}` }}>
      {TIMELINE.map((t) => (
        <li key={t.date} style={{ position: "relative", padding: "0 0 1.1rem 1.4rem" }}>
          <span style={{
            position: "absolute", left: "-7px", top: "0.45rem", width: 12, height: 12, borderRadius: "50%",
            background: t.done ? BLUE : "#fff", border: `2px solid ${t.done ? BLUE : ORANGE}`,
          }} />
          <div style={{ fontSize: "0.9rem", fontWeight: 700, color: t.done ? "#111827" : ORANGE }}>{t.date}</div>
          <div style={{ fontSize: "1rem" }}>{t.text}</div>
        </li>
      ))}
    </ol>
  );
}

export function BaringsIresUpdateContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        A month after <strong>Barings</strong> went public with its <strong>€1.386-a-share</strong> cash approach for{" "}
        <strong>IRES REIT plc</strong>, Ireland's largest private residential landlord, the bid is still only a{" "}
        <em>possible</em> offer. Barings has until <strong>5pm on 9 November 2026</strong> to make it binding or walk away.
        Here is where things stand, what the market is signalling, and how the price still compares with{" "}
        <Link to="/blog/barings-ires-reit-takeover-offer-fair-value" style={{ color: "#1d4ed8", fontWeight: 600 }}>
          our valuation of the portfolio
        </Link>.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", marginBottom: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>The short version:</strong> €1.386 is a <strong>30.75% premium</strong> to the undisturbed €1.06 share
          price but almost exactly IRES's <strong>138.8c</strong> net asset value, and about <strong>25% below</strong> our
          open-market estimate of <strong>185.7c</strong>. Fidelity has roughly halved its stake since the approach went public, while hedge
          funds that trade takeovers have been buying: the market expects the deal to happen at €1.386, not higher. Adding VAT back
          to new-home sales and checking our figures against the CSO's both suggest our estimate, if anything, is low. The deadline is{" "}
          <strong>9 November</strong>.
        </p>
      </div>

      <StatCards />

      <SectionHeading>Recap: what we think IRES is worth</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        In September we{" "}
        <Link to="/blog/valuing-ires-reit-property-portfolio" style={{ color: "#1d4ed8", fontWeight: 600 }}>
          valued the IRES portfolio
        </Link>{" "}
        flat by flat: <strong>35 developments</strong> and <strong>3,615 IRES-owned units</strong>, each priced against
        arm's-length resales from the Property Price Register by the same engine behind our{" "}
        <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>valuation tool</Link>. (Press reports put the
        portfolio at 3,700–3,900 apartments; our count covers the units we could match to IRES's published schemes.)
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Portfolio:</strong> about <strong>€1.52 billion</strong> sold individually, 19% above the €1.28bn IRES
          carries on its balance sheet.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Per share:</strong> with <strong>€533.6m</strong> of net debt in front of the equity, that lifts NAV from
          138.8c to about <strong>185.7c</strong>, or nearly <strong>200c</strong> if IRES's own record of selling vacant units
          25% above book holds across the portfolio.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>The gap:</strong> 185.7c less 138.6c is about <strong>47c a share</strong>, or roughly{" "}
          <strong>€247 million</strong>. That is the break-up premium, and at €1.386 it goes to Barings.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        Our conclusion then still stands: <strong>fair against the share price, light against the assets.</strong> A buyer
        taking 3,600-odd tenanted flats in one go will always pay nearer block value than the sum of individual sales, but
        shareholders who accept are handing over the upside.
      </p>

      <PremiumChart />

      <p style={{ marginBottom: "1rem", fontSize: "1rem", color: INK_MUTED }}>
        <strong>A correction:</strong> our first post said the shares jumped about 20% on the news. Measured against the
        undisturbed price of €1.06, the offer is a 30.75% premium, and the shares have since traded close to it.
      </p>

      <SectionHeading>Do VAT and the official figures change the picture?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Since our first two posts we have made two changes to how HomeIQ handles prices, and both bear on the IRES numbers.
        Neither makes the offer look better.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>VAT on new homes.</strong> The Property Price Register records new homes <em>without</em> VAT: 13.5%, or 9%
        on new apartments sold since 8 October 2025. Since 27 October our medians, trends and valuations add it back,
        the same way the CSO does. Our September run of the IRES portfolio priced every comparable at the register figure,
        so any new-build sales among the comparables counted 9–13.5% too low. Second-hand resales carry no VAT and are
        unaffected. How much this matters depends on how many new-build sales were among the comparables, and we haven't
        re-run the portfolio, but the correction can only push our estimate <em>up</em>. On this count, 185.7c is
        conservative.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Our resale prices match the CSO's.</strong> The CSO's price statistics come from the same stamp duty
        returns as the register. When we{" "}
        <Link to="/blog/property-price-register-vs-cso-house-prices" style={{ color: "#1d4ed8", fontWeight: 600 }}>
          compared the two
        </Link>
        , second-hand medians agreed to within about <strong>±1.2%</strong> in a typical Eircode area, with Dublin's
        register median <strong>1.2% below</strong> the CSO's. The resale data our valuation rests on matches the official
        figures, and if anything sits slightly low.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Dublin apartment prices are still rising.</strong> On the CSO's Residential Property Price Index, Dublin
        apartment prices rose <strong>5.7%</strong> in the year to August 2026, faster than Dublin houses (3.3%). IRES's
        138.8c NAV is a 30 June figure, and the €1.386 offer is fixed. If apartment prices keep rising at anything like
        that pace, the gap between what the flats would fetch individually and what Barings is paying keeps widening.
      </p>

      <SectionHeading>Timeline: where the bid stands</SectionHeading>
      <Timeline />
      <p style={{ marginBottom: "1rem" }}>
        Under <strong>Rule 2.6(a)</strong> of the Irish Takeover Rules, by the deadline Barings must do one of three things:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Announce a firm offer (Rule 2.7).</strong> The bid becomes binding. A scheme document follows, then a
          shareholder vote and, for a scheme of arrangement, High Court approval, before IRES is taken private and delisted.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Ask for more time.</strong> The deadline can be extended only with the Takeover Panel's consent (Rule
          2.6(c)), normally at the IRES board's request. That is common when due diligence is nearly done.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Walk away.</strong> A statement that it won't bid would normally bar Barings from coming back for 12 months.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        Until one of those happens there is, in the rules' own words, no certainty that a firm offer will be made.
      </p>

      <SectionHeading>What the filings show</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Anyone holding 3% or more of IRES must tell the market each time they cross a whole percentage point. Since
        August, IRES has published sixteen of these notices. Read together, they show long-term holders handing shares to
        funds that specialise in takeovers.
      </p>
      <HoldingsTable />
      <p style={{ marginBottom: "1rem" }}>
        <strong>Fidelity is the big seller.</strong> FMR had already trimmed from 8.9% to about 7% before the bid was public.
        Ten days after the announcement it sold about another <strong>17.6 million shares</strong>, roughly half of what was
        left, with the shares trading just under €1.386. Selling slightly below the offer for cash today, instead of waiting for
        a deal that might not close, is a bet that it closes at €1.386 and not higher.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>The buyers trade takeovers.</strong> <strong>Millennium</strong> (3.25%, held entirely through derivatives),{" "}
        <strong>Sand Grove</strong> (3.20%) and <strong>Goldman Sachs</strong> have all crossed 3% since early October.
        Goldman has filed eight notices in three weeks as it moved back and forth across 3%, the pattern of a bank's trading and
        client-hedging book rather than a long-term investor. <strong>BlackRock</strong> edged above 4%. Funds like these
        buy at a small discount to the offer and earn the gap when the deal completes. They do well if it goes through at
        €1.386, and are not counting on a higher bid.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        Press reports have also named <strong>Starwood</strong> and <strong>Janus Henderson</strong> among the sellers. No
        holdings notice from either appears in IRES's announcements since August, so if they sold, their stakes stayed below
        the disclosure thresholds or their sales didn't cross one. The only director dealing in the period is a routine
        conditional share award to chief executive Eddie Byrne under the long-term incentive plan, and the directors between
        them hold about 0.24% of the company.
      </p>

      <SectionHeading>What the market is telling us</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Activists got what they asked for.</strong> The approach follows a long campaign by shareholders, most
        prominently Canada's <strong>Vision Capital</strong>, for a strategic review and an orderly sale or break-up of the
        portfolio. A sale at NAV delivers the exit, though not the break-up value activists had argued was there.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>The last of the Irish REITs.</strong> Green REIT, Hibernia REIT and Yew Grove REIT have all been taken
        private. If this deal completes, Ireland will have no major listed property trust left, and no listed vehicle that
        gives ordinary investors a stake in the country's rental housing.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Political scrutiny.</strong> As the owner of thousands of Dublin apartments, IRES is unusually visible. A
        private-equity owner has drawn questions about how rents will be managed under the <strong>Rent Pressure Zone</strong>{" "}
        rules and, more broadly, about institutional ownership of homes. None of that blocks the deal, but it shapes how a
        new owner can run, or eventually sell down, the portfolio. Selling flats individually is how a buyer would capture
        the break-up premium.
      </p>

      <SectionHeading>What to watch before 9 November</SectionHeading>
      <ul style={{ marginBottom: "2rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>A Rule 2.7 announcement</strong>, and whether the price is still €1.386. A firm offer at the same price is
          the most likely outcome, given the board's stance and where the shares are trading.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>An extension request</strong>, which would point to due diligence running late rather than a deal in trouble.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>The share price.</strong> A widening gap below €1.386 would mean the market is losing confidence; trading
          at or above it would mean someone expects more.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Dividends.</strong> Barings has reserved the right to cut its offer by the amount of any dividend IRES pays
          after 28 September, so a dividend would come out of the €1.386, not on top of it.
        </li>
        <li>
          <strong>Dealing disclosures</strong> from large holders during the offer period, which show who is still selling
          and who is buying.
        </li>
      </ul>
      <p style={{ marginBottom: "2rem" }}>
        We'll update this post when Barings makes its move.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Own an apartment in Dublin?</strong> The engine we used to value IRES's 3,615 units will value yours from
          real comparable sales, with the comparables shown.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>{" "}
          Or see{" "}
          <Link to="/blog/dublin-property-prices-by-postcode-2026" style={{ color: "#1d4ed8", fontWeight: 600 }}>
            Dublin prices by postcode
          </Link>.
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        Status as at 31 October 2026. Offer details are from IRES REIT plc's Rule 2.4 "Statement regarding possible offer"
        (28 September 2026); holdings are from TR-1 notifications and the Form 8 opening position disclosure (8 October
        2026) published by IRES between 20 August and 30 October 2026; financial figures are IRES's reported numbers as at 30 June 2026 (H1 2026 Interim Report). This
        is a possible offer only, not a firm offer under Rule 2.7, and there is no certainty a firm offer will be made. HomeIQ
        valuations are an indicative statistical model based on Property Price Register resale comparables and are not a
        valuation of record. Nothing here is investment advice or a recommendation regarding any security; do your own
        research and, if in doubt, seek independent professional advice.
      </p>
    </div>
  );
}
