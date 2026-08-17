import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// Guide post — Irish-market advice on solar PV as a property value-add, plus a
// buyer/seller checklist. No dataset analysis; prose + checklist only.
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

export function SolarValueContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        With electricity prices among the highest in Europe and SEAI grants making the sums add up, solar panels have gone
        from a niche eco-choice to a mainstream home upgrade in Ireland. Done well, a solar PV system can lower running
        costs, lift your home's BER (Building Energy Rating) and make it stand out to buyers. Done badly &mdash; or bought
        from the wrong installer &mdash; it can leave you with an orphaned system, void warranties and missing paperwork
        that quietly <em>drags on</em> your sale price. This guide covers how to add solar as a genuine value-add, and what
        to insist on if you're buying a home that already has it.
      </p>

      <Callout>
        <strong>The short version:</strong> solar adds most value when it's installed by an SEAI-registered company, backed
        by a proper workmanship warranty, and handed over with a complete paperwork pack. The panels themselves matter far
        less to your home's value than the <em>evidence</em> that the system is legal, certified and safe.
      </Callout>

      <SectionHeading>Does solar actually add value?</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Two ways. First, directly: a well-specified system cuts a household's electricity bill and can earn money back for
        exported power under the <strong>Clean Export Guarantee (CEG)</strong>, so buyers are effectively paying for lower
        future running costs. Second, and often more importantly for resale, solar improves your{" "}
        <strong>BER</strong> &mdash; the energy rating shown on every property listing. A better BER widens your buyer pool
        (some buyers screen listings by rating) and can improve access to green mortgage rates.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        The catch: that value only materialises if the installation is documented and certified. A system with no
        paperwork behind it is treated by cautious buyers and their solicitors as a liability, not an asset. So the money
        question isn't just "should I get solar?" &mdash; it's "how do I get solar in a way that a future buyer's solicitor
        will be happy with?"
      </p>

      <SectionHeading>Don't be rushed &mdash; and know who's official</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Fake grants, high-pressure sales and deposit theft are on the rise. Treat any "limited-time deal" that pressures you
        to sign or pay a deposit today as a red flag &mdash; a legitimate installer will still be there next week. Always
        remember that the <strong>only official residential energy grants in Ireland are administered by the SEAI</strong>{" "}
        (Sustainable Energy Authority of Ireland). If someone offers you a "government grant" through any other channel,
        it isn't real.
      </p>
      <WarningBox>
        <strong>Walk away if you're being rushed.</strong> Pressure to pay a deposit "today to lock in the price," vague
        answers about grants, or reluctance to put warranty terms in writing are the classic warning signs of a pop-up
        operator or an outright scam.
      </WarningBox>

      <SectionHeading>Check the installer is properly registered</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Before you go anywhere near a contract, confirm two registrations:
      </p>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          The company is on the <strong>SEAI Register of Solar PV Installers</strong>. To claim an SEAI grant it's a{" "}
          <strong>strict legal requirement</strong> to use an SEAI-registered company &mdash; and registration binds them
          to the SEAI's <strong>Code of Practice and Quality Assurance</strong> standards, which give you a real level of
          consumer protection and a route to dispute resolution.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          Their electricians are registered with <strong>Safe Electric</strong>, the national regulatory body for
          electrical work. Anyone connecting a solar system to your home's wiring should be a Safe Electric registered
          electrical contractor.
        </li>
      </ul>

      <SectionHeading>Favour an established installer &mdash; and a real warranty</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        There are two separate warranties on any solar job: the <em>hardware</em> manufacturer's warranty (on the panels,
        inverter and battery) and the <em>installer's workmanship</em> warranty. The workmanship warranty is the one people
        forget, and it's the one that protects you when a roof mount leaks or a connection fails. Aim for a workmanship
        warranty of <strong>5 to 10 years</strong>, binding the installer to fix faults regardless of what the hardware
        manufacturer's warranty covers.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        A warranty is only as good as the company standing behind it, so favour an installer that has been{" "}
        <strong>trading for at least 5 to 7 years</strong>. Ireland didn't suffer the UK's 2019 "Feed-In Tariff crash," but
        the arrival of the Clean Export Guarantee and generous SEAI grants has created a "gold rush" of brand-new, pop-up
        installation companies. An established firm is far more likely to survive market swings and still be around to
        honour your warranty in five years' time.
      </p>

      <SectionHeading>Walk away from cheap hardware</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        The panels, inverter and battery are where corner-cutting hides. A few practical checks:
      </p>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          If you don't have a <strong>word-of-mouth recommendation</strong> for the hardware, check online reviews &mdash;
          and read them closely for fakes (bursts of five-star reviews in a short window, generic wording, no specifics).
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Check serial numbers</strong> and make sure panel details are printed on a <strong>permanent label,
          not a removable sticker</strong>. Fraudsters can re-sticker low-capacity panels to misrepresent their output.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Pay with a credit card</strong> where you can. It gives you <strong>chargeback protection</strong>{" "}
          through your bank if the supplier goes bust before the system is installed.
        </li>
      </ul>

      <SectionHeading>The paperwork that protects your home's value</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        This is the part that turns solar from a "nice feature" into documented value. Keep every document from the
        installation &mdash; and if you're <strong>buying a home that already has a system</strong>, make sure the sale
        includes all of the following before you commit:
      </p>
      <ul style={{ marginBottom: "1.5rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>SEAI Declaration of Works</strong> &mdash; proof the system met national grant standards.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>ESB Networks NC6 Form</strong> &mdash; the official micro-generation notification proving the local grid
          operator approved the connection (an <strong>NC7</strong> form is used instead for particularly large systems).
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Safe Electric Completion Certificate</strong> (usually <strong>Cert 3</strong>) &mdash; proving the
          electrical work is certified and safe.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>An updated BER certificate</strong> reflecting the solar installation &mdash; so the rating buyers see
          actually accounts for the panels.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>The manufacturer warranties</strong> for each piece of hardware &mdash; panels, inverter and battery.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        If a home you're viewing has solar but the seller can't produce these, treat it as an open question, not a done
        deal: without the NC6 and the Safe Electric certificate you can't be sure the system is grid-approved and safely
        installed, and without an updated BER you're not getting credit for it on the listing.
      </p>

      <SectionHeading>Bottom line</SectionHeading>
      <p style={{ marginBottom: "2rem" }}>
        Solar can be a real value-add in the Irish market &mdash; but the value lives in the quality of the installer and
        the completeness of the paperwork, not in the panels alone. Use an SEAI-registered installer with Safe Electric
        electricians, insist on a 5&ndash;10 year workmanship warranty from an established company, be sceptical of cheap
        hardware and pushy sales, and hold onto every certificate. Do that, and you've added value you can prove &mdash;
        which is exactly the kind a buyer will pay for.
      </p>

      <Callout>
        <strong>Thinking about how upgrades affect your home's worth?</strong> Use HomeIQ to explore real sold prices in
        your area and get a free instant valuation for any address based on comparable sales from Ireland's Property Price
        Register. <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
      </Callout>

      <p style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "1.5rem" }}>
        This article is general information, not financial, legal or engineering advice. Grant terms, forms and standards
        change &mdash; always confirm current requirements with the SEAI, ESB Networks and Safe Electric before you commit.
      </p>
    </div>
  );
}
