import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { ClientOnly } from "vite-react-ssg";
import type { TopSalePoint } from "../components/TopSalesMap";

const TopSalesMap = lazy(() => import("../components/TopSalesMap"));

// ---------------------------------------------------------------------------
// Data: the 21 highest full-market prices paid for a single second-hand home on
// the Property Price Register, Jan 2010 – Oct 2026 (one entry per house, its
// highest sale). Bulk sales, new-build schemes and development land left out.
// Map points are street-level: some come from the register geocode, the rest
// were placed by hand (Walford and Lissadell share a Shrewsbury Road point).
// Strancally Castle (No. 1) is a late filing: sold 17 Aug 2026, published in October.
// ---------------------------------------------------------------------------
interface Sale {
  rank: number;
  name: string;
  place: string;
  price: number;
  date: string;   // register sale date
  lat: number;
  lon: number;
}

const SALES: Sale[] = [
  { rank: 1,  name: "Strancally Castle",    place: "Knockanore, Co Waterford",       price: 51_171_155, date: "17 Aug 2026", lat: 52.0671,   lon: -7.8746 },
  { rank: 2,  name: "Inniscorrig",          place: "Coliemore Road, Dalkey",         price: 14_956_300, date: "29 Jun 2026", lat: 53.275599, lon: -6.094864 },
  { rank: 3,  name: "Walford",              place: "Shrewsbury Road, Dublin 4",      price: 14_250_000, date: "15 Dec 2016", lat: 53.3218,   lon: -6.2234 },
  { rank: 4,  name: "Lissadell",            place: "9 Shrewsbury Road, Dublin 4",    price: 13_250_000, date: "19 May 2021", lat: 53.3218,   lon: -6.2234 },
  { rank: 5,  name: "St Kilda",             place: "Sandycove Avenue East",          price: 12_500_000, date: "12 Sep 2022", lat: 53.288,    lon: -6.113 },
  { rank: 6,  name: "Coolbeg",              place: "14 Shrewsbury Road, Dublin 4",   price: 12_230_000, date: "15 Nov 2024", lat: 53.32315,  lon: -6.22308 },
  { rank: 7,  name: "Lyons Estate",         place: "Celbridge, Co Kildare",          price: 12_073_334, date: "4 Oct 2016",  lat: 53.30111,  lon: -6.545 },
  { rank: 8,  name: "Dalguise",             place: "Monkstown Road, Monkstown",      price: 12_000_000, date: "26 Jan 2022", lat: 53.295025, lon: -6.16307 },
  { rank: 9,  name: "73 Ailesbury Road",    place: "Dublin 4",                       price: 11_700_000, date: "16 Feb 2022", lat: 53.31945,  lon: -6.22575 },
  { rank: 10, name: "Luggala",              place: "Roundwood, Co Wicklow",          price: 11_585_000, date: "30 Oct 2019", lat: 53.108,    lon: -6.273 },
  { rank: 11, name: "Carrickbrack House",   place: "Old Carrickbrack Road, Howth",   price: 11_500_000, date: "25 May 2020", lat: 53.36627,  lon: -6.07684 },
  { rank: 12, name: "Abbey Leix",           place: "Abbeyleix, Co Laois",            price: 11_500_000, date: "15 Jul 2021", lat: 52.8962,   lon: -7.375 },
  { rank: 13, name: "Martinstown Stud House", place: "Kilmallock, Co Limerick",      price: 10_800_000, date: "23 Dec 2025", lat: 52.4083,   lon: -8.4828 },
  { rank: 14, name: "Sorrento House",       place: "1 Sorrento Terrace, Dalkey",     price: 10_650_000, date: "2 Jul 2021",  lat: 53.27449,  lon: -6.09818 },
  { rank: 15, name: "6 Raglan Road",        place: "Ballsbridge, Dublin 4",          price: 10_400_000, date: "2 Apr 2026",  lat: 53.330711, lon: -6.237665 },
  { rank: 16, name: "Victoria House",       place: "81 Ailesbury Road, Dublin 4",    price: 10_000_000, date: "23 Sep 2024", lat: 53.31929,  lon: -6.22767 },
  { rank: 17, name: "Seagrange",            place: "Sandycove Avenue East",          price: 9_750_000,  date: "31 Jan 2025", lat: 53.288,    lon: -6.112 },
  { rank: 18, name: "Gorse Hill",           place: "Vico Road, Killiney",            price: 9_500_000,  date: "10 Jul 2017", lat: 53.268944, lon: -6.104174 },
  { rank: 19, name: "Cedar Lodge",          place: "98 Merrion Road, Dublin 4",      price: 9_400_000,  date: "27 Jul 2022", lat: 53.325485, lon: -6.222796 },
  { rank: 20, name: "Bushy Park House",     place: "Enniskerry, Co Wicklow",         price: 9_399_000,  date: "28 Jun 2023", lat: 53.174477, lon: -6.16709 },
  { rank: 21, name: "Kenah Hill",           place: "St George's Avenue, Killiney",   price: 9_000_000,  date: "27 Nov 2015", lat: 53.260,    lon: -6.120 },
];

// Earlier register sales of the same houses.
const REPEATS = [
  { name: "Coolbeg",           before: 4_400_000,  beforeYear: 2012, after: 12_230_000, afterYear: 2024 },
  { name: "Victoria House",    before: 4_410_000,  beforeYear: 2014, after: 10_000_000, afterYear: 2024 },
  { name: "Lissadell",         before: 6_000_000,  beforeYear: 2012, after: 13_250_000, afterYear: 2021 },
  { name: "73 Ailesbury Road", before: 6_000_000,  beforeYear: 2014, after: 11_700_000, afterYear: 2022 },
  { name: "Inniscorrig",       before: 7_800_000,  beforeYear: 2018, after: 14_956_300, afterYear: 2026 },
  { name: "Cedar Lodge",       before: 5_700_000,  beforeYear: 2016, after: 9_400_000,  afterYear: 2022 },
  { name: "Sorrento House",    before: 10_000_000, beforeYear: 2015, after: 10_650_000, afterYear: 2021 },
];

const INK = "#374151";
const INK_MUTED = "#6b7280";
const GRID = "#e5e7eb";

const eur = (n: number) => `€${(n / 1_000_000).toFixed(3).replace(/\.?0+$/, "")}M`;
const eurFull = (n: number) => `€${n.toLocaleString("en-IE")}`;

// Sales within ~100m of each other share a pin ("3·4" Walford and Lissadell,
// "5·17" St Kilda and Seagrange), or the numbers sit on top of each other.
function mapPoints(sales: Sale[]): TopSalePoint[] {
  const out: TopSalePoint[] = [];
  for (const s of sales) {
    const same = out.find((p) => Math.abs(p.lat - s.lat) < 0.001 && Math.abs(p.lon - s.lon) < 0.0015);
    if (same) {
      same.label += `·${s.rank}`;
      same.name += ` / ${s.name}`;
      same.price += ` / ${eur(s.price)}`;
    } else {
      out.push({ label: String(s.rank), name: s.name, price: eur(s.price), lat: s.lat, lon: s.lon });
    }
  }
  return out;
}
const ALL_POINTS = mapPoints(SALES);
const D4_POINTS = mapPoints(SALES.filter((s) => s.lat > 53.315 && s.lat < 53.34 && s.lon > -6.25 && s.lon < -6.21));
const COAST_POINTS = mapPoints(SALES.filter((s) => s.lat > 53.25 && s.lat < 53.30 && s.lon > -6.17));

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

function HomeHeading({ s }: { s: Sale }) {
  return (
    <h3 style={{ fontSize: "1.375rem", fontWeight: 600, color: "#111827", marginTop: "2.25rem", marginBottom: "0.5rem" }}>
      {s.rank}. {s.name}, {s.place}{" "}
      <span style={{ fontWeight: 500, color: INK_MUTED, fontSize: "1.05rem" }}>
        &mdash; {eurFull(s.price)} ({s.date})
      </span>
    </h3>
  );
}

const P = ({ children }: { children: React.ReactNode }) => <p style={{ marginBottom: "1rem" }}>{children}</p>;
const sale = (rank: number) => SALES[rank - 1];

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.25rem 1.5rem", margin: "1.5rem 0 2rem" }}>
      <div style={{ fontSize: "1rem", color: "#1e40af" }}>{children}</div>
    </div>
  );
}

const th: React.CSSProperties = { textAlign: "left", padding: "0.5rem 0.75rem", borderBottom: `2px solid ${GRID}`, fontWeight: 600 };
const td: React.CSSProperties = { padding: "0.45rem 0.75rem", borderBottom: `1px solid ${GRID}` };
const tdNum: React.CSSProperties = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" };

function RankTable() {
  return (
    <div style={{ overflowX: "auto", margin: "1.5rem 0 2rem" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
        <thead>
          <tr><th style={th}>#</th><th style={th}>Home</th><th style={th}>Location</th><th style={{ ...th, textAlign: "right" }}>Price</th><th style={th}>Sold</th></tr>
        </thead>
        <tbody>
          {SALES.map((s) => (
            <tr key={s.rank}>
              <td style={td}>{s.rank}</td>
              <td style={{ ...td, fontWeight: 500 }}>{s.name}</td>
              <td style={td}>{s.place}</td>
              <td style={tdNum}>{eurFull(s.price)}</td>
              <td style={{ ...td, whiteSpace: "nowrap" }}>{s.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RepeatTable() {
  return (
    <div style={{ overflowX: "auto", margin: "1.5rem 0 2rem" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
        <thead>
          <tr>
            <th style={th}>Home</th>
            <th style={{ ...th, textAlign: "right" }}>Earlier sale</th>
            <th style={{ ...th, textAlign: "right" }}>Top-21 sale</th>
            <th style={{ ...th, textAlign: "right" }}>Change</th>
          </tr>
        </thead>
        <tbody>
          {REPEATS.map((r) => (
            <tr key={r.name}>
              <td style={{ ...td, fontWeight: 500 }}>{r.name}</td>
              <td style={tdNum}>{eur(r.before)} ({r.beforeYear})</td>
              <td style={tdNum}>{eur(r.after)} ({r.afterYear})</td>
              <td style={tdNum}>+{Math.round((r.after / r.before - 1) * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MapFigure({ points, height, caption, label }: { points: TopSalePoint[]; height: number; caption: string; label: string }) {
  const fallback = <div style={{ width: "100%", height: "100%", background: "#eef2f6" }} aria-hidden="true" />;
  return (
    <figure style={{ margin: "1.5rem 0 2rem" }}>
      <div role="img" aria-label={label}
           style={{ height, borderRadius: "0.5rem", overflow: "hidden", border: `1px solid ${GRID}` }}>
        <ClientOnly fallback={fallback}>
          {() => (
            <Suspense fallback={fallback}>
              <TopSalesMap points={points} />
            </Suspense>
          )}
        </ClientOnly>
      </div>
      <figcaption style={{ fontSize: "0.875rem", color: INK_MUTED, marginTop: "0.5rem" }}>{caption}</figcaption>
    </figure>
  );
}

export function TopHouseSalesContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <P>
        Since 2010, every residential sale in Ireland has been recorded on the Property Price Register. Most of its
        800,000-odd entries are ordinary family homes. At the very top, though, are a few dozen houses that sold for
        more than many apartment blocks: Victorian villas on the Dalkey coast, Edwardian mansions on Shrewsbury and
        Ailesbury Roads, and a handful of great country estates, one of them now owned by Mark Zuckerberg.
      </P>
      <P>
        We took the 21 highest prices paid for a single second-hand home and looked into each one: its size, setting,
        history and earlier sales.
      </P>

      <Callout>
        <strong>The short version:</strong> the record is <strong>{eurFull(sale(1).price)}</strong> for Strancally Castle
        in Co Waterford, bought by Mark Zuckerberg and Priscilla Chan in August 2026: more than three times any other
        home on the list. The Dublin record is {eurFull(sale(2).price)} for Inniscorrig in Dalkey, sold in June 2026. 15 of
        the 21 are in County Dublin, all but one of them south of the Liffey, and five are on just two roads in Dublin 4
        (Shrewsbury and Ailesbury). Every house on the list sold for at least €9 million.
      </Callout>

      <RankTable />

      <SectionHeading>The 21 homes</SectionHeading>

      <HomeHeading s={sale(1)} />
      <P>
        Strancally Castle is a castellated Gothic Revival house built in about 1830 for John Keily, a former MP, to
        designs by the Cork architects James and George Richard Pain. Three storeys and some 16,000 sq ft, it stands on a
        wooded slope above the River Blackwater at Knockanore in west Waterford, with a 440-acre estate. Downriver is the
        ruin of the older Desmond castle that gave the place its name and its legend: a "murdering hole" through which
        unwanted guests were said to be dropped into the river. Michael Alen-Buckley, co-founder of the investment firm
        RAB Capital, and his wife Giancarla, a daughter of the hotelier Charles Forte, owned it for 25 years, restored it,
        and are known locally for the Blackwater Valley Opera Festival. Mark Zuckerberg and Priscilla Chan bought it
        off-market in August 2026. The price first reported was €20–30 million; when the sale reached the register in
        October it showed {eurFull(sale(1).price)}, the highest price on the register for a home, bar one disputed entry
        (see <a href="#walford" style={{ color: "#3b82f6", textDecoration: "underline" }}>the Walford puzzle</a>). A spokesperson said
        the family "look forward to spending time in Ireland, where Meta maintains its international headquarters".
        James Dyson bought Ballynatray, the neighbouring 850-acre estate, in 2024.
      </P>

      <HomeHeading s={sale(2)} />
      <P>
        Inniscorrig is a castellated Gothic Revival house on the rocks at Coliemore, built in 1847 as a summer retreat
        for the physician Sir Dominic Corrigan. It has its own small harbour and six bedrooms, and it hosted two
        British kings, Edward VII and George V: a crown and star are still set in pebbles in the grounds. The sellers
        bought it for €7.8 million in 2018; The Irish Times reported the buyer as an Irish family living in the US.
        It is the most expensive Dublin home on the register.
      </P>

      <HomeHeading s={sale(3)} />
      <P>
        Walford is an Edwardian house from 1902, about 4,000 sq ft on 1.8 acres. Its 2016 sale, to a trust connected to
        Dermot Desmond, is the second-highest Dublin home price on the register, and planning permission was
        later granted to replace it with a 17,168 sq ft house. Its earlier history is the strangest on this list; see{" "}
        <a href="#walford" style={{ color: "#3b82f6", textDecoration: "underline" }}>the Walford puzzle</a> below.
      </P>

      <HomeHeading s={sale(4)} />
      <P>
        Lissadell, No. 9 Shrewsbury Road, is the only house on the list filed in Irish: the register reads{" "}
        <em>"Uimhi a Naoi, Bótha Sriúsbaire"</em>, literally "Number Nine, Shrewsbury Road". It was bought by Pat
        Crean, the developer behind Marlet, in 2021. It had last sold for €6 million in 2012.
      </P>

      <HomeHeading s={sale(5)} />
      <P>
        St Kilda is an extended villa on Sandycove Avenue East with the sea beyond the back-garden wall, past a private
        putting green, and a short walk from the Forty Foot. It was the family home of the late developer Peter
        Cosgrave, co-founder of the Cosgrave Property Group, and sold off-market. It was the top sale of 2022, and it
        was back on the market in September 2026 at €14 million.
      </P>

      <HomeHeading s={sale(6)} />
      <P>
        Coolbeg is a five-bedroom Edwardian house of 553 m² (about 5,950 sq ft) on 0.4 acres, with a one-bed guest
        lodge. It appeared in the 1992 film <em>Far and Away</em> with Tom Cruise and Nicole Kidman, and was refurbished
        and extended in 2015. It was listed at €12.5 million with Sherry FitzGerald in 2024, almost three times the
        €4.4 million it sold for in 2012.
      </P>

      <HomeHeading s={sale(7)} />
      <P>
        Lyons is one of Ireland's great Georgian houses, completed in 1797 for Nicholas Lawless, Lord Cloncurry, with
        ceiling frescoes by Gaspare Gabrielli and a 22-acre lake. UCD owned it from 1963; Tony Ryan, the Ryanair
        founder, bought it in 1996 for IR£3.5 million and reportedly spent about €100 million restoring it. After his
        death it was listed at €90 million in 2009, cut in stages to €30 million by 2013, and finally sold in 2016.
      </P>

      <HomeHeading s={sale(8)} />
      <P>
        Dalguise is a protected house on a nine-acre site in Monkstown. On the day the register records its sale, The
        Irish Times reported that the US firm Greystar was closing in on a deal of about €30 million for the site, to
        build several hundred rental apartments (a 290-home scheme already had permission, then under judicial review).
        The register's €12 million is the price recorded for the house.
      </P>

      <HomeHeading s={sale(9)} />
      <P>
        No. 73 dates from the 1920s and was designed by the architect R.M. Butler as his own home. It has 4,768 sq ft,
        seven bedrooms, a lift, and an acre of gardens with a three-hole putting green. Listed at €14 million in 2021,
        it was the most expensive home on the market that year; an Irish buyer paid €11.7 million. It had sold for
        €6 million in 2014.
      </P>

      <HomeHeading s={sale(10)} />
      <P>
        Luggala is a Gothic lodge built in 1787 for Peter La Touche, above Lough Tay in the Wicklow Mountains. It was a
        Guinness family house from 1937, home to Garech Browne until his death in 2018, and has appeared in films
        including <em>Excalibur</em> and <em>Braveheart</em> and in the series <em>Vikings</em>. It was listed at
        €28 million in 2017; the buyer, Count Padulli di Vighignolo, reportedly paid €20–25 million for the estate. See{" "}
        <a href="#register-vs-deal" style={{ color: "#3b82f6", textDecoration: "underline" }}>register price vs the real deal</a>.
      </P>

      <HomeHeading s={sale(11)} />
      <P>
        Little has been published about this sale on the Howth peninsula, the only north-Dublin house on the list.
      </P>

      <HomeHeading s={sale(12)} />
      <P>
        Abbey Leix House is the 18th-century seat of the de Vesci family, with nine bedrooms and about 1,100 acres. It
        was listed at €20 million with Colliers in 2021, and The Irish Times reported that Stripe co-founder Patrick
        Collison paid about that. The register shows €11.5 million (see below).
      </P>

      <HomeHeading s={sale(13)} />
      <P>
        The house is on the Martinstown estate near Kilmallock, home of the McManus family. The Irish Independent called
        the sale a mystery, and few details have been made public.
      </P>

      <HomeHeading s={sale(14)} />
      <P>
        Sorrento House is a protected house of 7,685 sq ft (714 m²) with six bedrooms, on two acres at the tip of the
        Dalkey headland, looking over Dalkey Sound to Bray Head and the Sugarloaf. It sold off-market, the third most
        valuable sale of 2021, only six years after an earlier €10 million sale.
      </P>

      <HomeHeading s={sale(15)} />
      <P>
        This Victorian redbrick was Denis O'Brien's, bought for €7.1 million in May 2000. It was at the centre of his
        High Court tax case: he argued successfully that it was not his permanent home, and the house was described as
        "uninhabitable", its Aga and kitchen fittings having been removed by the sellers. At stake was €57.8 million of
        capital gains tax. The €10.4 million sale is a 46% gain; as The Irish Times noted, the average second-hand
        Dublin house rose 240% over the same period.
      </P>

      <HomeHeading s={sale(16)} />
      <P>
        Victoria House is a six-bedroom semi-detached house of 550 m², refurbished in 2017, with a two-bedroom guest
        apartment, a games room and a wine cellar. It achieved its €10 million asking price through Sherry FitzGerald,
        the most expensive Dublin sale of 2024 at the time. It had sold for €4.41 million in 2014.
      </P>

      <HomeHeading s={sale(17)} />
      <P>
        Seagrange, St Kilda's neighbour on Sandycove Avenue East, was built in 1850: five bedrooms, 594 m². It was the
        top sale of 2025, which puts two houses from one short seafront road on the list.
      </P>

      <HomeHeading s={sale(18)} />
      <P>
        Gorse Hill on Vico Road, with views over Killiney Bay, was the home of the solicitor Brian O'Donnell until a
        long legal battle with its lender. It was Dublin's top sale of 2017.
      </P>

      <HomeHeading s={sale(19)} />
      <P>
        Cedar Lodge on Merrion Road sold for €5.7 million in 2016; six years later it made €9.4 million. Little else
        has been published about it.
      </P>

      <HomeHeading s={sale(20)} />
      <P>
        Chris de Burgh bought this Georgian house on 27 acres in 1996 and spent years restoring it, adding an indoor
        pool and a panic room with two-inch steel doors. It has eight en-suite bedrooms and a 600-bottle wine cellar.
        Listed at €12.5 million in 2019, then cut to €9.85 million with Lisney Sotheby's, it sold in 2023.
      </P>

      <HomeHeading s={sale(21)} />
      <P>
        Kenah Hill is an Italianate house of eight bedrooms on almost three acres, sold off-market in 2015, the
        second-highest Dublin sale that year. It has a colourful past: Francis Du Bedat, president of the Dublin Stock
        Exchange, bought it in 1889 and funded its expansion by fraud; the bank auctioned it in 1891 and he was jailed
        for seven years. It was relisted in 2024 at €12 million, later €10.75 million.
      </P>

      <SectionHeading><span id="register-vs-deal">Register price vs the real deal</span></SectionHeading>
      <P>
        For country estates and big sites the register can show far less than the reported price. It records the price
        filed for the residential property; where a deal also takes in farmland, woods or development land, that part
        can be priced separately, so the register figure can be well below what changed hands:
      </P>
      <ul style={{ paddingLeft: "1.5rem", marginBottom: "1.5rem" }}>
        <li style={{ marginBottom: "0.5rem" }}><strong>Luggala:</strong> {eur(sale(10).price)} on the register; reported €20–25 million for the estate.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Abbey Leix:</strong> {eur(sale(12).price)} on the register; reported about €20 million.</li>
        <li style={{ marginBottom: "0.5rem" }}><strong>Dalguise:</strong> {eur(sale(8).price)} on the register; reported about €30 million for the site.</li>
      </ul>
      <P>
        Ranked by reported total price, those three would all beat Inniscorrig. Strancally Castle goes the other way:
        the register shows about twice the €20–30 million first reported. We rank by the register, because that is
        the record anyone can check.
      </P>

      <SectionHeading><span id="walford">The Walford puzzle</span></SectionHeading>
      <P>
        Walford set the record for an Irish home before the register began: €58 million in 2005, at the height of the
        boom, when it was bought for Gayle Killilea. It was put on the market at €75 million
        in 2008, and withdrawn at a €15 million guide in 2011.
      </P>
      <P>
        Then, on 29 March 2013, the register records a sale of <strong>€71,950,000</strong>, described as a full-market
        sale. Taken at face value, that would be the highest home price on the register, above even Strancally Castle. But the press at the
        time reported a sale of about <strong>€14 million</strong>, to a company registered in Cyprus. Three years later
        that company sold Walford for {eurFull(sale(3).price)}, the figure we use above.
      </P>
      <P>
        We can't say why the 2013 entry reads €71.95 million: a filing error, or a figure that reflects something other
        than the price of the house. Either way, it is out of line with every other record of the house, so we leave it
        out of the ranking.
      </P>

      <SectionHeading>The same houses, sold twice</SectionHeading>
      <P>
        Seven of the 21 had sold before on the register, which lets us see how the top of the market has moved:
      </P>
      <RepeatTable />
      <P>
        Five of the seven roughly doubled or more within about a decade. Sorrento House barely moved: it was already
        priced at the top of the market when it sold in 2015.
      </P>

      <SectionHeading>Where they are</SectionHeading>
      <MapFigure
        points={ALL_POINTS}
        height={520}
        label="Map of Ireland with numbered pins for the 21 most expensive home sales; 15 are in County Dublin, with others in Waterford, Kildare, Wicklow, Laois and Limerick."
        caption="The 21 most expensive homes on the Property Price Register. Pins are approximate (street level), and homes close together share a pin."
      />
      <MapFigure
        points={D4_POINTS}
        height={420}
        label="Close-up map of Dublin 4 with pins for seven sales on Shrewsbury Road, Ailesbury Road, Merrion Road and Raglan Road."
        caption="Close-up, Dublin 4: Shrewsbury Road (3, 4, 6), Ailesbury Road (9, 16), Raglan Road (15) and Merrion Road (19)."
      />
      <MapFigure
        points={COAST_POINTS}
        height={420}
        label="Close-up map of the south Dublin coast with pins for seven sales between Monkstown and Killiney."
        caption="Close-up, the coast from Monkstown to Killiney: St Kilda and Seagrange (5, 17) are neighbours on Sandycove Avenue East."
      />

      <SectionHeading>How we built this list</SectionHeading>
      <ul style={{ paddingLeft: "1.5rem", marginBottom: "1.5rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Source:</strong> every sale on the Property Price Register from January 2010 to October 2026, full
          market price only. Sales can reach the register weeks or months after they complete: Strancally Castle
          sold in August and appeared in October, so the most recent months may still gain entries.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Single homes only:</strong> we left out bulk sales of several homes, new-build schemes and development
          land. Where a house sold more than once, we list its highest
          sale.
        </li>
        <li style={{ marginBottom: "0.75rem" }}>
          <strong>Names and histories</strong> come from published reports (The Irish Times, the Irish Independent,
          estate agents' listings and others). Where a detail couldn't be confirmed, we left it out.
        </li>
      </ul>

      <Callout>
        <strong>What did your street sell for?</strong> Look up any address on the{" "}
        <Link to="/" style={{ color: "#3b82f6", textDecoration: "underline" }}>interactive map</Link>, or get a free{" "}
        <Link to="/valuation" style={{ color: "#3b82f6", textDecoration: "underline" }}>property valuation</Link> based
        on real nearby sales.
      </Callout>
    </div>
  );
}
