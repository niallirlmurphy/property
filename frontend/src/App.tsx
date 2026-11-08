import { Suspense, lazy, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ClientOnly } from "vite-react-ssg";
import { fetchSuggestions, fetchTrends, searchExactAddress, searchProperties } from "./api";
import type { SearchSuggestion } from "./api";
import dublinData from "./data/counties/dublin.json";
import corkData from "./data/counties/cork.json";
import galwayData from "./data/counties/galway.json";
import limerickData from "./data/counties/limerick.json";
import kildareData from "./data/counties/kildare.json";
import meathData from "./data/counties/meath.json";
import TrendsChart from "./components/TrendsChart";
import SiteHeader from "./components/SiteHeader";
import SiteFooter from "./components/SiteFooter";
import HomeIntro from "./components/HomeIntro";
import { usePageMeta } from "./hooks/usePageMeta";
import EmailAlertModal from "./components/EmailAlertModal";
import { AREAS, COUNTIES, countySlug } from "./areas";
import { publishedPosts } from "./blogPosts";
import { SITE_STATS as S } from "./siteStats";
import type { Property, SearchResponse, SearchSort, TrendPoint } from "./types";
import "./styles/theme.css";
import "./styles/site-chrome.css";
import "./styles/home.css";


const MapView = lazy(() => import("./components/MapView"));

const RECENT_KEY = "homeiq_recent_searches";
const PAGE_SIZE = 10;
// Two Dublin streets, two full addresses elsewhere, then an area, an Eircode and a town.
// Each address has a recorded sale, so the example shows an exact match.
const EXAMPLES = [
  "28 Mountain View Road",
  "125 Tritonville Road",
  "41 Fearann Ri, Doughiska, Galway",
  "171 Dooradoyle Park, Dooradoyle, Limerick",
  "Rathmines, Dublin",
  "D06",
  "Kenmare",
];
const RADII = [0.5, 1, 2, 5, 10];
const SORTS: { key: SearchSort; label: string }[] = [
  { key: "date", label: "Date" },
  { key: "distance", label: "Distance" },
  { key: "price", label: "Value" },
];
const POPULAR_AREAS = ["rathmines", "ranelagh", "clontarf", "howth", "malahide", "blackrock", "swords", "bray", "cork-city", "galway-city", "limerick-city", "drogheda"];
const SNAPSHOT_COUNTIES = ["Dublin", "Cork", "Galway", "Limerick", "Kildare", "Meath"];
// The county card reads the monthly baked county page data (generate_page_data.py), so it
// renders in the prerendered page with no API calls. Only the median and 3 latest sales are kept.
const SNAPSHOTS: Record<string, { latest: TrendPoint | null; recent: Property[] }> = Object.fromEntries(
  Object.entries({ Dublin: dublinData, Cork: corkData, Galway: galwayData, Limerick: limerickData, Kildare: kildareData, Meath: meathData })
    .map(([c, d]) => [c, { latest: d.trends.length ? d.trends[d.trends.length - 1] : null, recent: (d.recent as Property[]).slice(0, 3) }]),
);

const eur = (n: number | null | undefined) => (n == null ? "–" : "€" + Math.round(n).toLocaleString("en-IE"));
const shortEur = (n: number) => (n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(2)}m` : `€${Math.round(n / 1000)}k`);
const fmtDate = (s: string) => {
  const [y, m, d] = s.slice(0, 10).split("-");
  return `${d}-${m}-${y}`;
};
const fmtDist = (m: number) => (m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(1)} km`);
const isCoords = (q: string) => /^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$/.test(q);
const looksLikeAddress = (q: string) => /^\d+[a-z]?\s/i.test(q.trim());
const foldName = (s: string) => s.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/['’]/g, "").replace(/[^a-z0-9]+/g, " ").trim();

// Area guides a failed query or its suggestions point to: an area whose name appears
// as whole words in the query ("the chase stillorgan" -> Stillorgan) or a suggestion.
function areaGuidesFor(q: string, suggestions: SearchSuggestion[]) {
  const texts = [q, ...suggestions.map((x) => x.label)].map((t) => ` ${foldName(t)} `);
  return AREAS.filter((a) => texts.some((t) => t.includes(` ${foldName(a.name)} `))).slice(0, 4);
}

function loadRecent(): string[] {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]"); } catch { return []; }
}
function saveRecent(q: string): string[] {
  const next = [q, ...loadRecent().filter((s) => s !== q)].slice(0, 5);
  try { localStorage.setItem(RECENT_KEY, JSON.stringify(next)); } catch { /* private mode */ }
  return next;
}

interface Outcome {
  q: string;
  county?: string;
  search: SearchResponse;
  trends: TrendPoint[];
  exact: Property[];
}

type Status = "idle" | "loading" | "done" | "error";

const Icon = {
  cal: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3 4h10v9H3zM3 7h10M6 2.5V5M10 2.5V5" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /></svg>,
  bed: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M2 12V4M2 9h12v3M14 9V7a2 2 0 0 0-2-2H7v4" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  home: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M2.5 8 8 3l5.5 5M4 7v6h8V7" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  pin: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M8 14s4.5-4 4.5-7.5a4.5 4.5 0 0 0-9 0C3.5 10 8 14 8 14z" fill="none" stroke="currentColor" strokeWidth="1.3" /><circle cx="8" cy="6.5" r="1.5" fill="currentColor" /></svg>,
};

function PropertyCard({ p, badge }: { p: Property; badge?: string }) {
  return (
    <li className={`hm-card${badge ? " hm-card-exact" : ""}`}>
      <div className="hm-card-top">
        <span className="hm-card-price">{eur(p.price)}</span>
        {badge && <span className="hm-badge">{badge}</span>}
      </div>
      <div className="hm-card-addr">{p.address}</div>
      <div className="hm-card-meta">
        <span>{Icon.cal}{fmtDate(p.sale_date)}</span>
        {p.bedrooms ? <span>{Icon.bed}{p.bedrooms} bed</span> : null}
        {p.property_type ? <span>{Icon.home}{p.property_type}</span> : null}
        {p.distance_m != null && <span>{Icon.pin}{fmtDist(p.distance_m)} away</span>}
        {p.not_full_market_price && <span className="hm-warn" title="Not a full market price sale (e.g. family transfer or VAT-exclusive new build)">Not full market price</span>}
      </div>
    </li>
  );
}

export default function App() {
  const meta = usePageMeta();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const [radius, setRadius] = useState(1);
  const [county, setCounty] = useState<string>("Dublin");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [shown, setShown] = useState(PAGE_SIZE);
  const [view, setView] = useState<"list" | "map">("list");
  const [sort, setSort] = useState<SearchSort>("date");
  const [refining, setRefining] = useState(false);
  const [recent, setRecent] = useState<string[]>([]);
  const [snapshotCounty, setSnapshotCounty] = useState("Dublin");
  const [alertOpen, setAlertOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [locating, setLocating] = useState(false);
  const gen = useRef(0);
  const resultsRef = useRef<HTMLDivElement | null>(null);

  // refine: a radius or sort change on the results already shown. Keep them on screen
  // (dimmed) and stay where the user is instead of jumping back to the top of the results.
  const run = async (query: string, opts: { radius?: number; county?: string | null; sort?: SearchSort; refine?: boolean } = {}) => {
    const text = query.trim();
    if (!text) return;
    const r = opts.radius ?? radius;
    const so = opts.sort ?? sort;
    const c = opts.county === undefined ? county : opts.county;
    const countyParam = isCoords(text) || !c ? undefined : c;
    const id = ++gen.current;
    setQ(text);
    setRadius(r);
    setSort(so);
    if (opts.county !== undefined) setCounty(opts.county ?? "");
    setError("");
    setSuggestions([]);
    setShown(PAGE_SIZE);
    if (opts.refine) {
      setRefining(true);
    } else {
      setStatus("loading");
      setView("list");
      setRecent(saveRecent(text));
      requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
    const next: Record<string, string> = { q: text, radius_km: String(r) };
    if (countyParam) next.county = countyParam;
    if (so !== "date") next.sort = so;
    setParams(next, { replace: true });
    try {
      const sp = { q: text, radius_km: r, county: countyParam, sort: so };
      // The exact lookup gets the county only when it isn't the Dublin default: the
      // backend applies that default itself unless the address names another county
      // ("41 Fearann Ri, Doughiska, Galway"), which county=Dublin would override.
      const exactCounty = countyParam === "Dublin" ? undefined : countyParam;
      const [search, trends, exact] = await Promise.all([
        searchProperties(sp),
        fetchTrends(text, r, countyParam).catch(() => [] as TrendPoint[]),
        looksLikeAddress(text) ? searchExactAddress(text, exactCounty).catch(() => null) : Promise.resolve(null),
      ]);
      if (gen.current !== id) return;
      setOutcome({ q: text, county: countyParam, search, trends, exact: exact?.results ?? [] });
      setStatus("done");
      setRefining(false);
    } catch (e: any) {
      if (gen.current !== id) return;
      setRefining(false);
      const msg: string = e?.message ?? "";
      const notFound = msg.includes("Could not") || msg.includes("find");
      setError(notFound
        ? `We couldn't place "${text}" on the map.`
        : msg || "Something went wrong. Please try again.");
      // Couldn't be placed: ask the backend what it could mean before showing the page.
      const did = notFound && !isCoords(text) ? await fetchSuggestions(text) : [];
      if (gen.current !== id) return;
      setSuggestions(did);
      setStatus("error");
    }
  };

  // Restore a shared link, saved searches and the county list (all client-side only)
  useEffect(() => {
    setRecent(loadRecent());
    const urlQ = params.get("q");
    if (urlQ) {
      const r = Number(params.get("radius_km") ?? "1") || 1;
      const c = params.get("county");
      const so = SORTS.find((x) => x.key === params.get("sort"))?.key ?? "date";
      setQ(urlQ);
      run(urlQ, { radius: r, county: c ?? null, sort: so });
    }
  }, []);

  const locate = () => {
    if (!navigator.geolocation) { setError("Your browser can't share a location. Type an address instead."); setStatus("error"); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        run(`${pos.coords.latitude.toFixed(5)},${pos.coords.longitude.toFixed(5)}`, { county: null });
      },
      () => {
        setLocating(false);
        setError("We couldn't get your location. Type an address, town or Eircode instead.");
        setStatus("error");
      },
      { timeout: 10000 },
    );
  };

  const copyLink = () => {
    navigator.clipboard?.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  };

  const o = outcome;
  const latest = o?.trends.length ? o.trends[o.trends.length - 1] : null;
  const prev = o && o.trends.length > 1 ? o.trends[o.trends.length - 2] : null;
  const yoy = latest && prev && prev.median_price > 0 ? ((latest.median_price - prev.median_price) / prev.median_price) * 100 : null;
  const exactIds = new Set(o?.exact.map((p) => p.id));
  const list: Property[] = o ? [...o.exact, ...o.search.results.filter((p) => !exactIds.has(p.id))] : [];
  const pins = list.filter((p) => p.latitude != null && p.longitude != null).slice(0, 60);
  const center: [number, number] | null = o ? [o.search.center.lat, o.search.center.lon] : null;

  const topResult = o?.search.results[0];
  const countyName = topResult?.county ? COUNTIES.find((c) => c.toLowerCase() === topResult.county!.toLowerCase()) : undefined;
  const routingKey = topResult?.eircode ? topResult.eircode.replace(/\s+/g, "").slice(0, 3).toUpperCase() : null;
  const areaMatch = o ? AREAS.find((a) => a.name.toLowerCase() === o.q.split(",")[0].trim().toLowerCase()) : undefined;
  const valuationHref = o ? `/valuation?${new URLSearchParams({ address: o.q, ...(o.county ? { county: o.county } : {}) })}` : "/valuation";
  const widened = o && o.search.radius_km > radius;
  const posts = [...publishedPosts()].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);
  const areas = POPULAR_AREAS.map((s) => AREAS.find((a) => a.slug === s)).filter((a): a is NonNullable<typeof a> => a != null);
  // First useful answer without typing: latest sales and median for a county
  const snapshot = SNAPSHOTS[snapshotCounty];
  const snapLatest = snapshot.latest;

  return (
    <>
      {meta}
      <SiteHeader />
      <div className="hm">

        <section className="hm-hero">
          <svg className="hm-contours" viewBox="0 0 800 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((i) => (
              <ellipse key={i} cx={560 - i * 6} cy={250 + i * 3} rx={60 + i * 34} ry={34 + i * 22} transform={`rotate(${-18 + i * 2.5} 560 250)`} />
            ))}
            {[0, 1, 2, 3, 4].map((i) => (
              <ellipse key={`b${i}`} cx={90 + i * 4} cy={470 - i * 2} rx={40 + i * 30} ry={26 + i * 18} transform={`rotate(${12 - i * 3} 90 470)`} />
            ))}
          </svg>
          <div className="hm-hero-in">
            <div className="hm-hero-copy">
              <h1>Research and understand property price trends before you buy, sell or remortgage.</h1>
              <p className="hm-sub">
                Search any address, Eircode or town for actual sales data or create an up to date valuation for any
                property using sales data in its neighbourhood. {S.totalSales} sales since {S.firstYear}, free, no sign-up.
              </p>
              <form className="hm-search" role="search" onSubmit={(e) => { e.preventDefault(); run(q); }}>
                <label htmlFor="hm-q" className="hm-sr">Address, Eircode or area</label>
                <div className="hm-search-row">
                  <svg className="hm-search-ico" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" strokeWidth="2" /><path d="m15.5 15.5 5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                  <input
                    id="hm-q"
                    type="search"
                    inputMode="search"
                    enterKeyHint="search"
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="Address, Eircode or town"
                    autoComplete="off"
                    autoCapitalize="off"
                  />
                  <button type="submit" className="hm-go" disabled={status === "loading" || !q.trim()}>
                    {status === "loading" ? "Searching…" : "Search"}
                  </button>
                </div>
                <div className="hm-search-tools">
                  <button type="button" className="hm-link-btn" onClick={locate} disabled={locating}>
                    {locating ? "Locating…" : "Use my location"}
                  </button>
                  <Link to="/valuation" className="hm-link-btn">Create Property Valuation Report</Link>
                </div>
              </form>
              <div className="hm-chips" aria-label="Try an example">
                {recent.map((s) => (
                  <button key={s} type="button" className="hm-chip hm-chip-recent" onClick={() => run(s)}>{s}</button>
                ))}
                {EXAMPLES.map((s) => (
                  <button key={s} type="button" className="hm-chip" onClick={() => run(s)}>{s}</button>
                ))}
              </div>
            </div>

            <aside className="hm-live" aria-label="Latest on the register">
              <div className="hm-live-tabs" role="tablist" aria-label="County">
                {SNAPSHOT_COUNTIES.map((c) => (
                  <button key={c} role="tab" aria-selected={c === snapshotCounty} className={c === snapshotCounty ? "on" : ""} onClick={() => setSnapshotCounty(c)}>{c}</button>
                ))}
              </div>
              <div className="hm-live-big">
                <span className="hm-live-label">Median price in {snapshotCounty}{snapLatest ? `, ${snapLatest.year}` : ""}</span>
                <strong>{eur(snapLatest?.median_price)}</strong>
              </div>
              <ul className="hm-live-list">
                {snapshot.recent.slice(0, 3).map((p) => (
                  <li key={p.id}>
                    <span className="hm-live-price">{eur(p.price)}</span>
                    <span className="hm-live-addr">{p.address}</span>
                    <span className="hm-live-date">{fmtDate(p.sale_date)}</span>
                  </li>
                ))}
              </ul>
              <Link to={`/county/${countySlug(snapshotCounty)}`} className="hm-live-link">All {snapshotCounty} prices</Link>
            </aside>
          </div>
        </section>

        <div ref={resultsRef} className="hm-results-anchor" />

        {status === "loading" && (
          <section className="hm-section" aria-busy="true" aria-live="polite">
            <div className="hm-skel hm-skel-head" />
            <div className="hm-stats">
              {[0, 1, 2].map((i) => <div key={i} className="hm-skel hm-skel-stat" />)}
            </div>
            {[0, 1, 2, 3].map((i) => <div key={i} className="hm-skel hm-skel-card" />)}
          </section>
        )}

        {status === "error" && (suggestions.length > 0 || areaGuidesFor(q, []).length > 0) && (
          <section className="hm-section hm-empty" role="alert">
            <h2>Did you mean…</h2>
            <p>We couldn't place "{q}" on its own. It could be one of these:</p>
            {suggestions.length > 0 && (
              <ul className="hm-did" aria-label="Suggested searches">
                {suggestions.map((x) => (
                  <li key={`${x.label}|${x.county}`}>
                    <button className="hm-did-btn" onClick={() => run(x.query, { county: x.county })}>
                      <strong>{x.label}</strong>
                      <span>{x.kind === "place" ? "Area" : "Street or estate"} · Co. {x.county} · {x.sales.toLocaleString()} {x.sales === 1 ? "sale" : "sales"}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {areaGuidesFor(q, suggestions).length > 0 && (
              <>
                <h3>Area guides</h3>
                <div className="hm-next-grid">
                  {areaGuidesFor(q, suggestions).map((a) => (
                    <Link key={a.slug} to={`/area/${a.slug}`} className="hm-next-card">
                      <strong>{a.name} guide</strong><span>Prices, streets, nearby areas</span>
                    </Link>
                  ))}
                </div>
              </>
            )}
            <p className="hm-hint">Not here? Add the area or county ("Main Street, Tuam"), or use an Eircode (e.g. D06 X123).</p>
          </section>
        )}

        {status === "error" && suggestions.length === 0 && areaGuidesFor(q, []).length === 0 && (
          <section className="hm-section hm-empty" role="alert">
            <h2>We couldn't complete that search</h2>
            <p>{error}{error.startsWith("We couldn't place") ? " Try adding the area or county, or use an Eircode." : ""}</p>
            <div className="hm-actions">
              {q.trim() && !isCoords(q) && <button className="hm-btn" onClick={() => run(q)}>Try again</button>}
              <button className="hm-btn hm-btn-ghost" onClick={() => run(q, { county: null })} disabled={!q.trim()}>Search all counties</button>
            </div>
            <p className="hm-hint">Tip: a full Eircode (e.g. D06 X123) or a routing key (D06) always works best.</p>
          </section>
        )}

        {status === "done" && o && o.search.count === 0 && o.exact.length === 0 && (
          <section className="hm-section hm-empty">
            <h2>No sales found within {radius} km of "{o.q}"</h2>
            <p>That can mean a quiet area, not that nothing sold. Try a wider search:</p>
            <div className="hm-actions">
              {RADII.filter((r) => r > radius).map((r) => (
                <button key={r} className="hm-btn hm-btn-ghost" onClick={() => run(o.q, { radius: r })}>{r} km</button>
              ))}
              {o.county && <button className="hm-btn hm-btn-ghost" onClick={() => run(o.q, { county: null })}>All counties</button>}
            </div>
            <p className="hm-hint">Or <Link to={valuationHref}>get a valuation estimate</Link>, or browse <Link to="/areaguides">area guides</Link>.</p>
          </section>
        )}

        {status === "done" && o && (o.search.count > 0 || o.exact.length > 0) && (
          <section className="hm-section" aria-live="polite">
            <div className="hm-result-head">
              <h2>Sales near {isCoords(o.q) ? "your location" : o.q}</h2>
              <div className="hm-result-tools">
                <button className="hm-link-btn" onClick={copyLink}>{copied ? "Link copied" : "Share"}</button>
                <button className="hm-link-btn" onClick={() => setAlertOpen(true)}>Get price alerts</button>
              </div>
            </div>
            {widened && (
              <p className="hm-note">We widened the search to {o.search.radius_km} km to find enough sales.</p>
            )}

            <div className="hm-stats">
              <div className="hm-stat">
                <span>Median price{latest ? ` (${latest.year}${latest.year === Number(S.lastYear) ? " so far" : ""})` : ""}</span>
                <strong>{eur(latest?.median_price)}</strong>
                {yoy != null && prev && (
                  <em className={yoy >= 0 ? "hm-up" : "hm-down"}>
                    {yoy >= 0 ? "▲" : "▼"} {Math.abs(yoy).toFixed(1)}% vs {prev.year}
                  </em>
                )}
              </div>
              <div className="hm-stat">
                <span>Sales found</span>
                <strong>{o.search.count.toLocaleString()}</strong>
                <em>within {o.search.radius_km} km</em>
              </div>
              <div className="hm-stat">
                <span>Typical range{latest ? ` (${latest.year})` : ""}</span>
                <strong>{latest ? `${shortEur(latest.min_price)} – ${shortEur(latest.max_price)}` : "–"}</strong>
                <em>lowest to highest</em>
              </div>
            </div>

            {o.exact.length === 0 && looksLikeAddress(o.q) && (
              <div className="hm-callout">
                <strong>No recorded sale for {o.q}.</strong> The register only lists homes sold since 2010, so these are
                neighbouring sales. <Link to={valuationHref}>Get an estimate for this home →</Link>
              </div>
            )}

            <div className="hm-refine">
              <div className="hm-tabs hm-seg" role="radiogroup" aria-label="Search radius">
                {RADII.map((r) => (
                  <button key={r} role="radio" aria-checked={radius === r} className={radius === r ? "on" : ""}
                    disabled={refining} onClick={() => radius !== r && run(o.q, { radius: r, county: o.county ?? null, refine: true })}>
                    {r} km
                  </button>
                ))}
              </div>
              <div className="hm-tabs hm-seg" role="radiogroup" aria-label="Sort sales">
                {SORTS.map((x) => (
                  <button key={x.key} role="radio" aria-checked={sort === x.key} className={sort === x.key ? "on" : ""}
                    disabled={refining} onClick={() => sort !== x.key && run(o.q, { sort: x.key, county: o.county ?? null, refine: true })}>
                    {x.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="hm-tabs" role="tablist">
              <button role="tab" aria-selected={view === "list"} className={view === "list" ? "on" : ""} onClick={() => setView("list")}>List</button>
              <button role="tab" aria-selected={view === "map"} className={view === "map" ? "on" : ""} onClick={() => setView("map")}>Map</button>
            </div>

            {view === "list" ? (
              <>
                <ul className={`hm-cards${refining ? " hm-refining" : ""}`}>
                  {list.slice(0, shown).map((p) => (
                    <PropertyCard key={p.id} p={p} badge={exactIds.has(p.id) ? "This address" : undefined} />
                  ))}
                </ul>
                {shown < list.length && (
                  <button className="hm-btn hm-btn-ghost hm-more" onClick={() => setShown((n) => n + PAGE_SIZE)}>
                    Show more ({list.length - shown} left)
                  </button>
                )}
                {o.search.count >= 200 && <p className="hm-hint">Showing the 200 {sort === "price" ? "highest value" : sort === "distance" ? "nearest" : "most recent"}. Narrow the radius to see fewer.</p>}
              </>
            ) : (
              <div className="hm-map">
                <ClientOnly fallback={<div className="hm-map-ph" />}>
                  {() => (
                    <Suspense fallback={<div className="hm-map-ph" />}>
                      <MapView
                        initialCenter={center ?? [53.35, -7.5]}
                        flyCenter={center}
                        flyRadius={o.search.radius_km}
                        pendingCenter={center ? { lat: center[0], lon: center[1], radius_km: o.search.radius_km } : null}
                        searchResult={o.search}
                        panTarget={null}
                        mapProperties={pins}
                        activeProperty={null}
                        handleSelectProperty={() => {}}
                      />
                    </Suspense>
                  )}
                </ClientOnly>
              </div>
            )}

            {o.trends.length > 0 && (
              <div className="hm-trend">
                <h3>Price trend in this area</h3>
                <TrendsChart data={o.trends} onClose={() => {}} inline />
              </div>
            )}

            <div className="hm-next">
              <h3>What next?</h3>
              <div className="hm-next-grid">
                <Link to={valuationHref} className="hm-next-card hm-next-primary">
                  <strong>Value a home here</strong>
                  <span>Estimate from comparable sales</span>
                </Link>
                {areaMatch && (
                  <Link to={`/area/${areaMatch.slug}`} className="hm-next-card">
                    <strong>{areaMatch.name} guide</strong><span>Prices, streets, nearby areas</span>
                  </Link>
                )}
                {countyName && (
                  <Link to={`/county/${countySlug(countyName)}`} className="hm-next-card">
                    <strong>{countyName} prices</strong><span>County trends and recent sales</span>
                  </Link>
                )}
                {routingKey && (
                  <Link to={`/eircode/${routingKey}`} className="hm-next-card">
                    <strong>All sales in {routingKey}</strong><span>Eircode area overview</span>
                  </Link>
                )}
                <Link to="/mortgage" className="hm-next-card">
                  <strong>What can I borrow?</strong><span>Mortgage calculator</span>
                </Link>
              </div>
            </div>
          </section>
        )}

        {status === "idle" && <div className="hm-intro-wrap"><HomeIntro /></div>}

        {status !== "loading" && status !== "idle" && (
          <>
            <section className="hm-section">
              <h2>Browse by place</h2>
              <div className="hm-pills">
                {areas.map((a) => <Link key={a.slug} to={`/area/${a.slug}`}>{a.name}</Link>)}
                <Link to="/areaguides" className="hm-pill-more">All area guides →</Link>
              </div>
              <h3 className="hm-h3">Counties</h3>
              <div className="hm-pills">
                {COUNTIES.map((c) => <Link key={c} to={`/county/${countySlug(c)}`}>{c}</Link>)}
              </div>
            </section>

            <section className="hm-section hm-how">
              <h2>How it works</h2>
              <ol>
                <li><strong>Search</strong> an address, Eircode or town.</li>
                <li><strong>See</strong> what nearby homes sold for, when, and how prices moved.</li>
                <li><strong>Decide</strong> with a valuation, alerts or a deeper area guide.</li>
              </ol>
              <p className="hm-hint">
                Data: Property Price Register, {S.firstMonth} to {S.lastMonth}, {S.mappedPct}% of sales mapped, updated every
                two weeks. <Link to="/about#data-sources">How we handle the data →</Link>
              </p>
            </section>

            {posts.length > 0 && (
              <section className="hm-section">
                <h2>Latest analysis</h2>
                <ul className="hm-posts">
                  {posts.map((p) => (
                <li key={p.slug}>
                  <Link to={`/blog/${p.slug}`}>
                    <span className="hm-post-date">{new Date(p.date).toLocaleDateString("en-IE", { day: "numeric", month: "short", year: "numeric" })}</span>
                    <span className="hm-post-title">{p.title}</span>
                    <span className="hm-post-desc">{p.description}</span>
                    <span className="hm-post-more" aria-hidden="true">Read →</span>
                  </Link>
                </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>

      <EmailAlertModal
        isOpen={alertOpen}
        onClose={() => setAlertOpen(false)}
        defaultAddress={o?.q ?? q}
        defaultRadius={radius}
        defaultCounty={county || "Dublin"}
        counties={[...COUNTIES]}
      />
      {status !== "idle" && <SiteFooter />}
    </>
  );
}
