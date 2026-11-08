import { useState, useMemo } from "react";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from "recharts";

// ---------------------------------------------------------------------------
// Maths helpers
// ---------------------------------------------------------------------------

interface AmortRow {
  year: number;
  openingBalance: number;
  principalPaid: number;
  interestPaid: number;
  closingBalance: number;
  cumulativePrincipal: number;
  cumulativeInterest: number;
}

function buildSchedule(principal: number, annualRate: number, years: number): AmortRow[] {
  const r = annualRate / 100 / 12;
  const n = years * 12;
  // Monthly payment formula — handle 0% rate edge case
  const monthlyPayment = r === 0
    ? principal / n
    : (principal * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);

  const rows: AmortRow[] = [];
  let balance = principal;
  let cumPrincipal = 0;
  let cumInterest = 0;

  for (let y = 1; y <= years; y++) {
    let yearPrincipal = 0;
    let yearInterest = 0;
    const opening = balance;

    for (let m = 0; m < 12; m++) {
      if (balance <= 0) break;
      const interestCharge = balance * r;
      const principalCharge = Math.min(monthlyPayment - interestCharge, balance);
      yearInterest += interestCharge;
      yearPrincipal += principalCharge;
      balance -= principalCharge;
    }

    cumPrincipal += yearPrincipal;
    cumInterest += yearInterest;

    rows.push({
      year: y,
      openingBalance: Math.max(0, opening),
      principalPaid: Math.max(0, yearPrincipal),
      interestPaid: Math.max(0, yearInterest),
      closingBalance: Math.max(0, balance),
      cumulativePrincipal: Math.max(0, cumPrincipal),
      cumulativeInterest: Math.max(0, cumInterest),
    });
  }

  return rows;
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

function euro(n: number, decimals = 0) {
  return "€" + n.toLocaleString("en-IE", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function euroK(n: number) {
  if (n >= 1_000_000) return `€${(n / 1_000_000).toFixed(2)}m`;
  if (n >= 1000) return `€${(n / 1000).toFixed(0)}k`;
  return euro(n);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface SliderInputProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: (n: number) => string;
  onChange: (n: number) => void;
  inputSuffix?: string;
}

function SliderInput({ label, value, min, max, step, format, onChange, inputSuffix }: SliderInputProps) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="mc-field">
      <div className="mc-field-header">
        <label>{label}</label>
        <div className="mc-field-value">{format(value)}</div>
      </div>
      <div className="mc-slider-wrap">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{ "--pct": `${pct}%` } as React.CSSProperties}
        />
        <div className="mc-slider-bounds">
          <span>{format(min)}</span>
          <span>{format(max)}</span>
        </div>
      </div>
      <div className="mc-number-row">
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={e => {
            const v = Number(e.target.value);
            if (!isNaN(v)) onChange(Math.min(max, Math.max(min, v)));
          }}
        />
        {inputSuffix && <span className="mc-suffix">{inputSuffix}</span>}
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="mc-tooltip">
      <div className="mc-tooltip-title">Year {label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="mc-tooltip-row">
          <span className="mc-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}</span>
          <strong>{euro(p.value)}</strong>
        </div>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function MortgagePage() {
  const meta = usePageMeta(
    "Mortgage Calculator Ireland",
    "Calculate your Irish mortgage repayments, see a full amortisation schedule, and understand the total interest cost over the life of your loan.",
  );
  const [principal, setPrincipal] = useState(350_000);
  const [rate, setRate] = useState(3.5);
  const [years, setYears] = useState(30);
  const [tableView, setTableView] = useState<"annual" | "chart">("chart");
  const [showFullTable, setShowFullTable] = useState(false);

  const schedule = useMemo(() => buildSchedule(principal, rate, years), [principal, rate, years]);

  const r = rate / 100 / 12;
  const n = years * 12;
  const monthlyPayment = r === 0
    ? principal / n
    : (principal * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);

  const totalPaid = monthlyPayment * n;
  const totalInterest = totalPaid - principal;
  const last = schedule[schedule.length - 1];

  // Chart data — cumulative remaining balance + cumulative interest
  const balanceData = schedule.map(r => ({
    year: r.year,
    "Remaining Balance": Math.round(r.closingBalance),
    "Cumulative Interest": Math.round(r.cumulativeInterest),
  }));

  // Annual repayment breakdown
  const breakdownData = schedule.map(r => ({
    year: r.year,
    "Principal": Math.round(r.principalPaid),
    "Interest": Math.round(r.interestPaid),
  }));

  const displayRows = showFullTable ? schedule : schedule.slice(0, 10);

  return (
    <div className="mc-page">
      {meta}
      <PageHeader title="Mortgage Calculator" />
      <div className="mc-page-subtitle">
        <p className="mc-subtitle">
          Estimate your monthly repayments and see the full amortisation schedule for any Irish mortgage.
        </p>
      </div>

      <div className="mc-layout">
        {/* ── Inputs ── */}
        <aside className="mc-inputs">
          <h2>Loan Details</h2>

          <SliderInput
            label="Property / Loan Value"
            value={principal}
            min={50_000}
            max={2_000_000}
            step={5_000}
            format={euroK}
            onChange={setPrincipal}
          />
          <SliderInput
            label="Annual Interest Rate"
            value={rate}
            min={0.5}
            max={12}
            step={0.05}
            format={v => v.toFixed(2) + "%"}
            onChange={setRate}
            inputSuffix="%"
          />
          <SliderInput
            label="Mortgage Term"
            value={years}
            min={5}
            max={35}
            step={1}
            format={v => v + " yrs"}
            onChange={setYears}
            inputSuffix="yrs"
          />

          {/* Summary stats */}
          <div className="mc-stats">
            <div className="mc-stat mc-stat--highlight">
              <span>Monthly repayment</span>
              <strong>{euro(monthlyPayment, 2)}</strong>
            </div>
            <div className="mc-stat">
              <span>Total repaid</span>
              <strong>{euro(totalPaid)}</strong>
            </div>
            <div className="mc-stat">
              <span>Total interest</span>
              <strong>{euro(totalInterest)}</strong>
            </div>
            <div className="mc-stat">
              <span>Interest / loan ratio</span>
              <strong>{((totalInterest / principal) * 100).toFixed(1)}%</strong>
            </div>
          </div>
        </aside>

        {/* ── Output ── */}
        <main className="mc-output">
          {/* View toggle */}
          <div className="mc-view-toggle">
            <button
              className={tableView === "chart" ? "active" : ""}
              onClick={() => setTableView("chart")}
            >Charts</button>
            <button
              className={tableView === "annual" ? "active" : ""}
              onClick={() => setTableView("annual")}
            >Year-by-year</button>
          </div>

          {tableView === "chart" && (
            <div className="mc-charts">
              {/* Balance vs cumulative interest */}
              <div className="mc-chart-block">
                <h3>Outstanding balance &amp; cumulative interest</h3>
                <p className="mc-chart-desc">
                  How the remaining loan balance decreases alongside the total interest paid over time.
                </p>
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={balanceData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gradBalance" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10302b" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#10302b" stopOpacity={0.02} />
                      </linearGradient>
                      <linearGradient id="gradInterest" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#a86a00" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#a86a00" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} label={{ value: "Year", position: "insideBottom", offset: -2, fontSize: 11 }} height={36} />
                    <YAxis tickFormatter={euroK} tick={{ fontSize: 11 }} width={60} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Area type="monotone" dataKey="Remaining Balance" stroke="#10302b" strokeWidth={2} fill="url(#gradBalance)" />
                    <Area type="monotone" dataKey="Cumulative Interest" stroke="#a86a00" strokeWidth={2} fill="url(#gradInterest)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Annual principal vs interest */}
              <div className="mc-chart-block">
                <h3>Annual principal vs interest repaid</h3>
                <p className="mc-chart-desc">
                  Each year's repayment split — more interest early in the term, more principal later.
                </p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={breakdownData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} label={{ value: "Year", position: "insideBottom", offset: -2, fontSize: 11 }} height={36} />
                    <YAxis tickFormatter={euroK} tick={{ fontSize: 11 }} width={60} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Principal" stackId="a" fill="#10302b" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="Interest" stackId="a" fill="#a86a00" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {tableView === "annual" && (
            <div className="mc-table-wrap">
              <table className="mc-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Opening balance</th>
                    <th>Principal paid</th>
                    <th>Interest paid</th>
                    <th>Closing balance</th>
                    <th>Cum. interest</th>
                  </tr>
                </thead>
                <tbody>
                  {displayRows.map(row => (
                    <tr key={row.year}>
                      <td>{row.year}</td>
                      <td>{euro(row.openingBalance)}</td>
                      <td className="mc-td-principal">{euro(row.principalPaid)}</td>
                      <td className="mc-td-interest">{euro(row.interestPaid)}</td>
                      <td>{euro(row.closingBalance)}</td>
                      <td className="mc-td-cuminterest">{euro(row.cumulativeInterest)}</td>
                    </tr>
                  ))}
                </tbody>
                {!showFullTable && schedule.length > 10 && (
                  <tfoot>
                    <tr>
                      <td colSpan={6}>
                        <button className="mc-show-more" onClick={() => setShowFullTable(true)}>
                          Show all {schedule.length} years ↓
                        </button>
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          )}
        </main>
      </div>

      {/* Rate guide */}
      <section className="mc-guide">
        <h2>Which interest rate should I enter?</h2>
        <p>
          Irish lenders show at least two figures beside every mortgage: the borrowing rate and the APRC.
          They measure different things, so it matters which one you put into the calculator.
        </p>
        <dl>
          <dt>Interest rate (borrowing rate)</dt>
          <dd>
            The annual rate charged on what you owe, often labelled the &ldquo;borrowing rate&rdquo;, &ldquo;fixed
            rate&rdquo; or &ldquo;variable rate&rdquo;. Your monthly repayment is worked out from this figure.{" "}
            <strong>This is the one to enter in the calculator.</strong>
          </dd>
          <dt>APRC (Annual Percentage Rate of Charge)</dt>
          <dd>
            The total cost of the mortgage expressed as a yearly rate. On top of interest it includes charges you
            must pay the lender to get the loan, such as a valuation fee, and it assumes you keep the mortgage for
            the full term. On a fixed rate, the APRC also assumes you move to the lender&rsquo;s variable rate
            when the fixed period ends. That is why the APRC is usually higher than the borrowing rate. Use it to
            compare offers from different lenders, not to work out your repayment.
          </dd>
          <dt>APR (Annual Percentage Rate)</dt>
          <dd>
            The older name for the same idea, still used for personal loans, car finance and credit cards. Irish
            mortgages quote the APRC instead. If you see an &ldquo;APR&rdquo; on a mortgage, treat it like the
            APRC: a cost-comparison figure, not the rate your repayments are based on.
          </dd>
        </dl>
        <h3>Fixed periods</h3>
        <p>
          The calculator applies one rate for the whole term. Most Irish mortgages start on a rate fixed for a few
          years and then roll on to a variable rate. To see what that means for you, run the calculator at the
          fixed rate, then again at the lender&rsquo;s current variable rate, for the balance and years that would
          remain when the fixed period ends.
        </p>
        <p>
          Example: an offer might read &ldquo;3.50% fixed for 4 years, APRC 4.10%&rdquo;. Enter 3.50%. The
          4.10% is the figure to compare with other lenders&rsquo; APRCs.
        </p>
      </section>

      {/* Disclosure */}
      <p className="mc-disclaimer">
        This page is for educational and informational purposes only. Your mortgage provider may have additional terms or fees not taken into consideration here.
      </p>
      <Footer />
    </div>
  );
}
