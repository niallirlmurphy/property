import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Guide post — how to use HomeIQ's mortgage calculator to plan around
// affordability and interest-rate risk, plus a 2026 mortgage-application
// checklist. Prose + real calculator screenshots; no dataset analysis.
// Figures quoted match the calculator screenshots (€350k / 30-year loan):
//   3.00% → €1,475.61/mo, €181,221 total interest
//   3.50% → €1,571.66/mo, €215,796 total interest (61.7% of the loan)
//   5.00% → €1,878.88/mo, €326,395 total interest
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function SubHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 style={{ fontSize: "1.375rem", fontWeight: 600, color: "#111827", marginTop: "2rem", marginBottom: "0.75rem" }}>
      {children}
    </h3>
  );
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", margin: "2rem 0" }}>
      <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>{children}</p>
    </div>
  );
}

function WarningBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", margin: "2rem 0" }}>
      <p style={{ fontSize: "1rem", color: "#991b1b", margin: 0 }}>{children}</p>
    </div>
  );
}

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1d4ed8", fontWeight: 600 }}>
      {children}
    </a>
  );
}

function Figure({ src, alt, caption, border = true }: { src: string; alt: string; caption: string; border?: boolean }) {
  return (
    <figure style={{ margin: "2rem 0" }}>
      <img
        src={src}
        alt={alt}
        loading="lazy"
        style={{
          width: "100%",
          height: "auto",
          borderRadius: "0.5rem",
          border: border ? "1px solid #e5e7eb" : "none",
          boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        }}
      />
      <figcaption style={{ fontSize: "0.875rem", color: INK_MUTED, marginTop: "0.6rem", textAlign: "center" }}>
        {caption}
      </figcaption>
    </figure>
  );
}

export function MortgageCalculatorGuideContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        A mortgage is the biggest financial commitment most people ever make &mdash; and the difference between a
        comfortable repayment and a stressful one often comes down to two numbers you can model in seconds:{" "}
        <strong>how much you borrow</strong> and <strong>the interest rate you pay</strong>. Before you talk to a lender
        or a broker, it's worth spending ten minutes with a mortgage calculator so you walk in knowing what you can
        realistically afford and how sensitive your repayments are to rate changes.
      </p>
      <p style={{ marginBottom: "1.5rem" }}>
        This guide shows how to use{" "}
        <Link to="/mortgage" style={{ color: "#1d4ed8", fontWeight: 600 }}>HomeIQ's free mortgage calculator</Link>{" "}
        to plan around <strong>affordability</strong> and the <strong>impact of interest rates</strong>, and finishes
        with a practical checklist for making a strong mortgage application in 2026.

      </p>

      <Callout>
        <strong>The short version:</strong> decide the monthly repayment you can comfortably live with{" "}
        <em>first</em>, then work backwards to the loan size &mdash; not the other way round. Model your loan at a
        rate a couple of points higher than today's, because over a 30-year term even a small rate rise adds tens of
        thousands of euro in interest.
      </Callout>

      <SectionHeading>Meet the calculator</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The calculator takes three inputs &mdash; the property or loan value, the annual interest rate, and the
        mortgage term &mdash; and instantly shows your monthly repayment, the total amount you'll repay over the life
        of the loan, the total interest, and the interest-to-loan ratio. It also draws out the full amortisation
        schedule so you can see exactly how each year's payment is split between principal and interest.
      </p>

      <Figure
        src="/images/mortgage-calculator-full.png"
        alt="HomeIQ mortgage calculator showing a €350,000 loan at 3.5% over 30 years with a €1,571.66 monthly repayment and amortisation charts"
        caption="The mortgage calculator: a €350,000 loan at 3.5% over 30 years repays €1,571.66 a month — and €215,796 in interest over the term."
      />

      <p style={{ marginBottom: "1rem" }}>
        In the example above, borrowing <strong>€350,000</strong> at <strong>3.5%</strong> over{" "}
        <strong>30 years</strong> costs <strong>€1,571.66 a month</strong>. Look at the panel on the left: the total
        interest is <strong>€215,796</strong> &mdash; that's an interest-to-loan ratio of <strong>61.7%</strong>. Put
        plainly, you repay the €350,000 you borrowed <em>plus</em> roughly another two-thirds of it again in interest.
        Seeing that number up front changes how you think about both the loan size and the term.
      </p>

      <SectionHeading>Start with affordability, not the asking price</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The most common mistake is to fall in love with a property, then try to make the numbers fit. Flip it around.
        Work out the monthly repayment you can <em>sustainably</em> afford &mdash; on top of your other living costs,
        savings and life &mdash; and use the calculator to find the loan size that produces it. Drag the interest-rate
        and value sliders until the monthly figure sits where you're comfortable, and you've found your realistic
        budget.
      </p>

      <SubHeading>Sanity-check against the Central Bank rules</SubHeading>
      <p style={{ marginBottom: "1rem" }}>
        In Ireland, how much you can borrow is capped by the Central Bank's mortgage measures as well as by what you
        can afford. As a rule of thumb, <strong>first-time buyers can typically borrow up to four times gross
        income</strong>, and <strong>second and subsequent buyers up to 3.5 times</strong>, with a{" "}
        <strong>10% deposit</strong> generally required (higher for certain buyers). Lenders also apply their own{" "}
        <strong>affordability stress test</strong>, checking you could still meet repayments if rates rose. Your own
        calculator sum should sit comfortably inside those limits &mdash; if it only works at the maximum, that's a
        signal to rethink.
      </p>
      <Callout>
        <strong>Tip:</strong> your proven ability to save &mdash; and, if you're renting, to pay rent &mdash; is the
        real-world affordability test lenders care about most. If your rent plus monthly savings already roughly
        matches your target repayment, you've effectively been paying that mortgage already, and you can show it.
      </Callout>

      <SectionHeading>The interest-rate effect: small rate, big number</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Interest rate is the input people underestimate most. Because a mortgage runs for decades, a change of just one
        or two percentage points compounds into an enormous difference. The calculator makes this vivid &mdash; keep
        the loan and term fixed, and move only the rate.
      </p>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", margin: "2rem 0" }}>
        <div style={{ flex: "1 1 260px", minWidth: 240 }}>
          <Figure
            src="/images/mortgage-calculator-low-rate.png"
            alt="Mortgage calculator: €350,000 over 30 years at 3.0% costs €1,475.61 a month and €181,221 total interest"
            caption="€350,000 · 30 years · 3.0% → €1,475.61/mo, €181,221 interest"
          />
        </div>
        <div style={{ flex: "1 1 260px", minWidth: 240 }}>
          <Figure
            src="/images/mortgage-calculator-high-rate.png"
            alt="Mortgage calculator: €350,000 over 30 years at 5.0% costs €1,878.88 a month and €326,395 total interest"
            caption="€350,000 · 30 years · 5.0% → €1,878.88/mo, €326,395 interest"
          />
        </div>
      </div>

      <p style={{ marginBottom: "1rem" }}>
        On the same <strong>€350,000</strong> loan over <strong>30 years</strong>, moving the rate from{" "}
        <strong>3.0%</strong> to <strong>5.0%</strong> pushes the monthly repayment from <strong>€1,475.61</strong> to{" "}
        <strong>€1,878.88</strong> &mdash; about <strong>€403 more every month</strong>, or nearly <strong>€4,840 a
        year</strong>. Over the full term, total interest jumps from <strong>€181,221</strong> to{" "}
        <strong>€326,395</strong>: an extra <strong>€145,000</strong> for the same house, purely because of the rate.
      </p>
      <WarningBox>
        <strong>Always model a higher rate than today's.</strong> If your budget only works at the lowest advertised
        rate, you're exposed. Fixed rates end, and variable rates move. Run the numbers at a rate two points higher and
        make sure you could still sleep at night &mdash; that's exactly what a lender's stress test is checking.
      </WarningBox>

      <SectionHeading>Reading the charts: where your money actually goes</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Switch to the <strong>Charts</strong> view and two things become obvious &mdash; things a single monthly figure
        hides.
      </p>

      <Figure
        src="/images/mortgage-calculator-charts.png"
        alt="Two charts: outstanding balance falling as cumulative interest rises and crosses around year 18, and a bar chart showing each year's repayment shifting from mostly interest to mostly principal"
        caption="Left: the balance falls as cumulative interest climbs — they cross around year 18. Right: early payments are mostly interest; only later does principal dominate."
      />

      <p style={{ marginBottom: "1rem" }}>
        The first chart plots your falling balance against the interest you've paid so far. Notice where the two lines
        cross &mdash; around <strong>year 18</strong> on this loan. For the first two-thirds of the term, a large slice
        of every payment is servicing interest, not shrinking what you owe.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        The second chart shows the same story year by year: early on, each repayment is <strong>mostly
        interest</strong>; only later does <strong>principal</strong> take over. This is why{" "}
        <strong>overpaying in the early years</strong> is so powerful (every extra euro comes straight off the
        principal, saving you future interest), and why a <strong>shorter term</strong> &mdash; if you can afford the
        higher monthly payment &mdash; dramatically cuts total interest. Try nudging the term slider from 30 to 25
        years and watch the total-interest figure fall.
      </p>

      <SectionHeading>Making a strong mortgage application in 2026</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Modelling the loan is half the battle; the other half is presenting yourself as a low-risk borrower. Lenders
        typically scrutinise the <strong>six months of bank statements immediately before your application</strong>, so
        good habits need to be in place well ahead of time. Here's what to focus on &mdash; and what to avoid.
      </p>

      <SubHeading>Do</SubHeading>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Save consistently.</strong> Work out an amount you can realistically put away each month, set up a
          standing order for pay day, and don't dip back into it. Lenders look closely at the six months before your
          application &mdash; don't skip a month. A steady, unbroken savings record is one of the strongest signals you
          can send.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Show your rent clearly.</strong> Rent should appear as regular, labelled transfers on your bank
          statements &mdash; avoid paying in cash. If you're renting from family, mark the transfer as{" "}
          <em>&ldquo;rent&rdquo;</em> (not &ldquo;Mam&rdquo;), so it reads as a genuine, provable housing cost.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Know your supports.</strong> For new builds, two government schemes can meaningfully boost your
          budget. <strong>Help to Buy</strong> gives first-time buyers a tax refund of up to <strong>€30,000</strong>{" "}
          (the lesser of €30,000, 10% of the price, or the Income Tax and DIRT you paid over the previous four years)
          towards your <strong>deposit</strong>. The <strong>First Home Scheme</strong> is a government shared-equity
          scheme that can cover up to <strong>30% of the price</strong> (20% if you also use Help to Buy) to{" "}
          <strong>bridge the gap</strong> between your mortgage-plus-deposit and the purchase price &mdash; though it
          can't fund the deposit itself. Eligibility and terms change, so check the current rules.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Understand your options.</strong> Rates, cashback offers and flexibility vary a lot between lenders,
          and the cheapest headline rate isn't always the cheapest overall. Compare across the market &mdash; or use a
          mortgage broker who can do it for you &mdash; before you commit.
        </li>
      </ul>

      <SubHeading>Don't</SubHeading>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't change jobs mid-application</strong> where you can help it. Most lenders want your probation
          period completed (often six months), so a job move at the wrong moment can delay or derail your approval.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't limit yourself to one lender.</strong> There are around <strong>ten mortgage lenders</strong>{" "}
          in Ireland; going to just one means ignoring most of the market. Shopping around &mdash; or using a broker
          with access to all the main lenders &mdash; is how you find the best rate for your circumstances.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't take on new debt &mdash; and keep your credit record clean.</strong> Lenders check the{" "}
          <strong>Central Credit Register</strong>, so avoid taking out car finance, personal loans or buy-now-pay-later
          (like Klarna) in the run-up to applying &mdash; each one eats into how much you can borrow and raises
          questions. Clear or reduce existing short-term debt where you can, never miss a repayment, and keep your
          statements free of red flags like gambling transactions or unauthorised overdrafts. A clean, boring credit
          history is exactly what an underwriter wants to see.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't overcomplicate your accounts.</strong> Keep your banking simple and easy to follow. A tangle of
          accounts, frequent transfers and unexplained movements makes an underwriter's job harder &mdash; and a
          harder application is a slower one.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Don't overstretch.</strong> Save what's realistic and sustainable &mdash; consistency beats
          extremes. Straining so hard that you slip into overdraft or miss commitments does more harm than a smaller,
          reliable amount. Lenders would rather see steady discipline than heroic months followed by red ones.
        </li>
      </ul>

      <SectionHeading>Bottom line</SectionHeading>
      <p style={{ marginBottom: "2rem" }}>
        A mortgage calculator turns an abstract, decades-long commitment into numbers you can actually feel. Use it to
        anchor on an affordable monthly repayment, pressure-test that figure against a higher interest rate, and see
        how much of your money goes to interest before principal. Do that before you apply &mdash; alongside a clean,
        consistent savings and rent record &mdash; and you'll approach lenders with realistic expectations and a
        genuinely strong application.
      </p>

      <Callout>
        <strong>Ready to run your own numbers?</strong> Try the{" "}
        <Link to="/mortgage" style={{ color: "#1d4ed8", fontWeight: 600 }}>HomeIQ mortgage calculator →</Link> and, when
        you've a property in mind, get a free instant valuation based on comparable sales from Ireland's Property Price
        Register with <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>HomeIQ valuations →</Link>
      </Callout>

      <SectionHeading>Useful resources (official)</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        For the authoritative detail on the rules and schemes mentioned above, go straight to the source:
      </p>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.citizensinformation.ie/en/housing/owning-a-home/help-with-buying-a-home/">
            Citizens Information &mdash; Help with buying a home
          </ExtLink>{" "}
          &mdash; plain-English overview of mortgages, schemes and the buying process.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.revenue.ie/en/property/help-to-buy-incentive/index.aspx">
            Revenue &mdash; Help to Buy (HTB) incentive
          </ExtLink>{" "}
          &mdash; official rules, eligibility and how to claim the up-to-€30,000 refund.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.citizensinformation.ie/en/housing/owning-a-home/help-with-buying-a-home/help-to-buy-scheme/">
            Citizens Information &mdash; Help to Buy Scheme
          </ExtLink>{" "}
          &mdash; a clear summary of how HTB works.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.citizensinformation.ie/en/housing/owning-a-home/help-with-buying-a-home/first-home-scheme/">
            Citizens Information &mdash; First Home Scheme
          </ExtLink>{" "}
          &mdash; how the government shared-equity scheme works and who qualifies.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.centralbank.ie/consumer-hub/explainers/what-are-the-mortgage-measures">
            Central Bank of Ireland &mdash; the mortgage measures
          </ExtLink>{" "}
          &mdash; the official loan-to-income and deposit (loan-to-value) limits.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <ExtLink href="https://www.ccpc.ie/consumers/money-tools/mortgage-comparisons/">
            CCPC &mdash; compare mortgages
          </ExtLink>{" "}
          &mdash; the statutory consumer body's independent tool for comparing lenders and rates.
        </li>
      </ul>

      <p style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "1.5rem" }}>
        This article is general information, not financial advice. Repayment figures are illustrative calculator
        outputs and exclude fees, insurance and charges your lender may apply. Central Bank mortgage measures, lending
        limits and support schemes change &mdash; always confirm current rules and get regulated advice before making a
        decision.
      </p>
    </div>
  );
}
