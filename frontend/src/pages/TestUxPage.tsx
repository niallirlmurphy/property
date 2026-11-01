import { Suspense, lazy, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ClientOnly, Head } from "vite-react-ssg";
import { fetchCounties, fetchCountySummary, fetchTrends, searchExactAddress, searchProperties } from "../api";
import TrendsChart from "../components/TrendsChart";
import EmailAlertModal from "../components/EmailAlertModal";
import { AREAS, COUNTIES, countySlug } from "../areas";
import { publishedPosts } from "../blogPosts";
import { SITE_STATS as S } from "../siteStats";
import type { CountySummary, Property, SearchResponse, TrendPoint } from "../types";
import "./TestUxPage.css";

// Prototype of the reviewed home/search UX (docs/ux_review_testux.md). Self-contained:
// own CSS (tux- prefix), own recent-search key, noindex. Every number on screen comes
// from the backend (/search, /trends, /county-recent, /search/exact); nothing is
// filtered or aggregated here.

const MapView = lazy(() => import("../components/MapView"));

const RECENT_KEY = "homeiq_tux_recent";
const PAGE_SIZE = 10;
const EXAMPLES = ["Rathmines, Dublin", "D06", "Cork city", "Galway city", "Swords", "Limerick city"];
const RADII = [0.5, 1, 2, 5, 10];
const POPULAR_AREAS = ["rathmines", "ranelagh", "clontarf", "howth", "malahide", "blackrock", "swords", "bray", "cork-city", "galway-city", "limerick-city", "drogheda"];
const SNAPSHOT_COUNTIES = ["Dublin", "Cork", "Galway", "Limerick", "Kildare", "Meath"];

const eur = (n: number | null | undefined) => (n == null ? "–" : "€" + Math.round(n).toLocaleString("en-IE"));
const shortEur = (n: number) => (n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(2)}m` : `€${Math.round(n / 1000)}k`);
const fmtDate = (s: string) => {
  const [y, m, d] = s.slice(0, 10).split("-");
  return `${d}-${m}-${y}`;
};
const fmtDist = (m: number) => (m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(1)} km`);
const isCoords = (q: string) => /^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$/.test(q);
const looksLikeAddress = (q: string) => /^\d+[a-z]?\s/i.test(q.trim());

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

const NAV = [
  { to: "/valuation", label: "Valuation" },
  { to: "/areaguides", label: "Area guides" },
  { to: "/heatmap", label: "Price heatmap" },
  { to: "/polygon", label: "Draw on map" },
  { to: "/mortgage", label: "Mortgage" },
  { to: "/blog", label: "Analysis" },
];

function Mark() {
  return (
    <svg className="tux-mark" viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#f2c230" />
      <path d="M7 16.5 16 8l9 8.5" fill="none" stroke="#10302b" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10.5 15v8.5h11V15" fill="none" stroke="#10302b" strokeWidth="2.6" strokeLinejoin="round" />
      <circle cx="16" cy="19.5" r="1.9" fill="#10302b" />
    </svg>
  );
}

// Own sticky header (the shared PageHeader/WaffleMenu stay untouched)
function TuxHeader() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <header className="tux-header">
      <div className="tux-header-in">
        <Link to="/testux" className="tux-brand" onClick={() => setOpen(false)}>
          <Mark /><span>Home<b>IQ</b></span>
        </Link>
        <nav className="tux-nav" aria-label="Main">
          {NAV.map((n) => <Link key={n.to} to={n.to}>{n.label}</Link>)}
        </nav>
        <Link to="/valuation" className="tux-cta">Value my home</Link>
        <button
          className="tux-burger"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="tux-menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span /><span /><span />
        </button>
      </div>
      {open && (
        <nav id="tux-menu" className="tux-menu" aria-label="Menu">
          {NAV.map((n) => <Link key={n.to} to={n.to} onClick={() => setOpen(false)}>{n.label}</Link>)}
          <Link to="/valuation" className="tux-cta tux-cta-wide" onClick={() => setOpen(false)}>Value my home</Link>
        </nav>
      )}
    </header>
  );
}

function TuxFooter() {
  return (
    <footer className="tux-footer">
      <div className="tux-footer-in">
        <div>
          <div className="tux-brand tux-brand-foot"><Mark /><span>Home<b>IQ</b></span></div>
          <p>Every Irish home sale on the Property Price Register, mapped. Free, with no sign-up.</p>
        </div>
        <div>
          <h4>Search</h4>
          <Link to="/valuation">Valuation</Link>
          <Link to="/polygon">Draw on map</Link>
          <Link to="/heatmap">Price heatmap</Link>
          <Link to="/s1">Single property</Link>
        </div>
        <div>
          <h4>Places</h4>
          <Link to="/areaguides">Area guides</Link>
          <Link to="/streets">Streets</Link>
          <Link to="/developments">Developments</Link>
          <Link to="/county/dublin">Dublin</Link>
        </div>
        <div>
          <h4>About</h4>
          <Link to="/about">About HomeIQ</Link>
          <Link to="/about#data-sources">Data sources</Link>
          <Link to="/blog">Analysis</Link>
          <Link to="/contact">Contact</Link>
        </div>
      </div>
      <p className="tux-footer-note">Source: Property Price Register (PSRA). Prototype page, not indexed.</p>
    </footer>
  );
}

const Icon = {
  cal: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3 4h10v9H3zM3 7h10M6 2.5V5M10 2.5V5" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /></svg>,
  bed: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M2 12V4M2 9h12v3M14 9V7a2 2 0 0 0-2-2H7v4" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  home: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M2.5 8 8 3l5.5 5M4 7v6h8V7" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  pin: <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M8 14s4.5-4 4.5-7.5a4.5 4.5 0 0 0-9 0C3.5 10 8 14 8 14z" fill="none" stroke="currentColor" strokeWidth="1.3" /><circle cx="8" cy="6.5" r="1.5" fill="currentColor" /></svg>,
};

function PropertyCard({ p, badge }: { p: Property; badge?: string }) {
  return (
    <li className={`tux-card${badge ? " tux-card-exact" : ""}`}>
      <div className="tux-card-top">
        <span className="tux-card-price">{eur(p.price)}</span>
        {badge && <span className="tux-badge">{badge}</span>}
      </div>
      <div className="tux-card-addr">{p.address}</div>
      <div className="tux-card-meta">
        <span>{Icon.cal}{fmtDate(p.sale_date)}</span>
        {p.bedrooms ? <span>{Icon.bed}{p.bedrooms} bed</span> : null}
        {p.property_type ? <span>{Icon.home}{p.property_type}</span> : null}
        {p.distance_m != null && <span>{Icon.pin}{fmtDist(p.distance_m)} away</span>}
        {p.not_full_market_price && <span className="tux-warn" title="Not a full market price sale (e.g. family transfer or VAT-exclusive new build)">Not full market price</span>}
      </div>
    </li>
  );
}

export default function TestUxPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const [radius, setRadius] = useState(1);
  const [county, setCounty] = useState<string>("Dublin");
  const [refineOpen, setRefineOpen] = useState(false);
  const [counties, setCounties] = useState<string[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [shown, setShown] = useState(PAGE_SIZE);
  const [view, setView] = useState<"list" | "map">("list");
  const [recent, setRecent] = useState<string[]>([]);
  const [snapshotCounty, setSnapshotCounty] = useState("Dublin");
  const [snapshot, setSnapshot] = useState<CountySummary | null>(null);
  const [alertOpen, setAlertOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [locating, setLocating] = useState(false);
  const gen = useRef(0);
  const resultsRef = useRef<HTMLDivElement | null>(null);

  const run = async (query: string, opts: { radius?: number; county?: string | null } = {}) => {
    const text = query.trim();
    if (!text) return;
    const r = opts.radius ?? radius;
    const c = opts.county === undefined ? county : opts.county;
    const countyParam = isCoords(text) || !c ? undefined : c;
    const id = ++gen.current;
    setQ(text);
    setRadius(r);
    if (opts.county !== undefined) setCounty(opts.county ?? "");
    setStatus("loading");
    setError("");
    setShown(PAGE_SIZE);
    setView("list");
    setRecent(saveRecent(text));
    const next: Record<string, string> = { q: text, radius_km: String(r) };
    if (countyParam) next.county = countyParam;
    setParams(next, { replace: true });
    requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    try {
      const sp = { q: text, radius_km: r, county: countyParam };
      const [search, trends, exact] = await Promise.all([
        searchProperties(sp),
        fetchTrends(text, r, countyParam).catch(() => [] as TrendPoint[]),
        looksLikeAddress(text) ? searchExactAddress(text, countyParam).catch(() => null) : Promise.resolve(null),
      ]);
      if (gen.current !== id) return;
      setOutcome({ q: text, county: countyParam, search, trends, exact: exact?.results ?? [] });
      setStatus("done");
    } catch (e: any) {
      if (gen.current !== id) return;
      const msg: string = e?.message ?? "";
      setError(msg.includes("Could not") || msg.includes("find")
        ? `We couldn't find "${text}". Try adding the area or county, or use an Eircode.`
        : msg || "Something went wrong. Please try again.");
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
      setQ(urlQ);
      run(urlQ, { radius: r, county: c ?? null });
    }
  }, []);

  useEffect(() => {
    if (!refineOpen || counties.length) return;
    fetchCounties().then(setCounties).catch(() => setCounties([...COUNTIES]));
  }, [refineOpen]);

  // First useful answer without typing: latest sales and median for a county
  useEffect(() => {
    let live = true;
    setSnapshot(null);
    fetchCountySummary(snapshotCounty).then((s) => live && setSnapshot(s)).catch(() => {});
    return () => { live = false; };
  }, [snapshotCounty]);

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
  const snapLatest = snapshot?.trends.length ? snapshot.trends[snapshot.trends.length - 1] : null;

  return (
    <>
      <Head>
        <title>HomeIQ — Test UX prototype</title>
        <meta name="robots" content="noindex,nofollow" />
      </Head>
      <TuxHeader />
      <div className="tux">

        <section className="tux-hero">
          <svg className="tux-contours" viewBox="0 0 800 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((i) => (
              <ellipse key={i} cx={560 - i * 6} cy={250 + i * 3} rx={60 + i * 34} ry={34 + i * 22} transform={`rotate(${-18 + i * 2.5} 560 250)`} />
            ))}
            {[0, 1, 2, 3, 4].map((i) => (
              <ellipse key={`b${i}`} cx={90 + i * 4} cy={470 - i * 2} rx={40 + i * 30} ry={26 + i * 18} transform={`rotate(${12 - i * 3} 90 470)`} />
            ))}
          </svg>
          <div className="tux-hero-in">
            <div className="tux-hero-copy">
              <h1>Know what it sold for.</h1>
              <p className="tux-sub">
                {S.totalSales} Irish home sales since {S.firstYear}, searchable by address, Eircode or town. Free, no sign-up.
              </p>
              <form className="tux-search" role="search" onSubmit={(e) => { e.preventDefault(); run(q); }}>
                <label htmlFor="tux-q" className="tux-sr">Address, Eircode or area</label>
                <div className="tux-search-row">
                  <svg className="tux-search-ico" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" strokeWidth="2" /><path d="m15.5 15.5 5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                  <input
                    id="tux-q"
                    type="search"
                    inputMode="search"
                    enterKeyHint="search"
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="Address, Eircode or town"
                    autoComplete="off"
                    autoCapitalize="off"
                  />
                  <button type="submit" className="tux-go" disabled={status === "loading" || !q.trim()}>
                    {status === "loading" ? "Searching…" : "Search"}
                  </button>
                </div>
                <div className="tux-search-tools">
                  <button type="button" className="tux-link-btn" onClick={locate} disabled={locating}>
                    {locating ? "Locating…" : "Use my location"}
                  </button>
                  <button type="button" className="tux-link-btn" aria-expanded={refineOpen} onClick={() => setRefineOpen((v) => !v)}>
                    {refineOpen ? "Hide options" : "Radius and county"}
                  </button>
                </div>
                {refineOpen && (
                  <div className="tux-refine">
                    <label>
                      Radius
                      <select value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
                        {RADII.map((r) => <option key={r} value={r}>{r} km</option>)}
                      </select>
                    </label>
                    <label>
                      County
                      <select value={county} onChange={(e) => setCounty(e.target.value)}>
                        <option value="">All counties</option>
                        {(counties.length ? counties : [...COUNTIES]).map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </label>
                  </div>
                )}
              </form>
              <div className="tux-chips" aria-label="Try an example">
                {recent.map((s) => (
                  <button key={s} type="button" className="tux-chip tux-chip-recent" onClick={() => run(s)}>{s}</button>
                ))}
                {EXAMPLES.map((s) => (
                  <button key={s} type="button" className="tux-chip" onClick={() => run(s)}>{s}</button>
                ))}
              </div>
            </div>

            <aside className="tux-live" aria-label="Latest on the register">
              <div className="tux-live-tabs" role="tablist" aria-label="County">
                {SNAPSHOT_COUNTIES.map((c) => (
                  <button key={c} role="tab" aria-selected={c === snapshotCounty} className={c === snapshotCounty ? "on" : ""} onClick={() => setSnapshotCounty(c)}>{c}</button>
                ))}
              </div>
              {!snapshot ? (
                <div className="tux-live-skel" aria-busy="true"><span /><span /><span /></div>
              ) : (
                <>
                  <div className="tux-live-big">
                    <span className="tux-live-label">Median price in {snapshotCounty}{snapLatest ? `, ${snapLatest.year}` : ""}</span>
                    <strong>{eur(snapLatest?.median_price)}</strong>
                  </div>
                  <ul className="tux-live-list">
                    {snapshot.recent.slice(0, 3).map((p) => (
                      <li key={p.id}>
                        <span className="tux-live-price">{eur(p.price)}</span>
                        <span className="tux-live-addr">{p.address}</span>
                        <span className="tux-live-date">{fmtDate(p.sale_date)}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to={`/county/${countySlug(snapshotCounty)}`} className="tux-live-link">All {snapshotCounty} prices</Link>
                </>
              )}
            </aside>
          </div>
        </section>

        <div ref={resultsRef} className="tux-results-anchor" />

        {status === "loading" && (
          <section className="tux-section" aria-busy="true" aria-live="polite">
            <div className="tux-skel tux-skel-head" />
            <div className="tux-stats">
              {[0, 1, 2].map((i) => <div key={i} className="tux-skel tux-skel-stat" />)}
            </div>
            {[0, 1, 2, 3].map((i) => <div key={i} className="tux-skel tux-skel-card" />)}
          </section>
        )}

        {status === "error" && (
          <section className="tux-section tux-empty" role="alert">
            <h2>We couldn't complete that search</h2>
            <p>{error}</p>
            <div className="tux-actions">
              {q.trim() && !isCoords(q) && <button className="tux-btn" onClick={() => run(q)}>Try again</button>}
              <button className="tux-btn tux-btn-ghost" onClick={() => run(q, { county: null })} disabled={!q.trim()}>Search all counties</button>
            </div>
            <p className="tux-hint">Tip: a full Eircode (e.g. D06 X123) or a routing key (D06) always works best.</p>
          </section>
        )}

        {status === "done" && o && o.search.count === 0 && o.exact.length === 0 && (
          <section className="tux-section tux-empty">
            <h2>No sales found within {radius} km of "{o.q}"</h2>
            <p>That can mean a quiet area, not that nothing sold. Try a wider search:</p>
            <div className="tux-actions">
              {RADII.filter((r) => r > radius).map((r) => (
                <button key={r} className="tux-btn tux-btn-ghost" onClick={() => run(o.q, { radius: r })}>{r} km</button>
              ))}
              {o.county && <button className="tux-btn tux-btn-ghost" onClick={() => run(o.q, { county: null })}>All counties</button>}
            </div>
            <p className="tux-hint">Or <Link to={valuationHref}>get a valuation estimate</Link>, or browse <Link to="/areaguides">area guides</Link>.</p>
          </section>
        )}

        {status === "done" && o && (o.search.count > 0 || o.exact.length > 0) && (
          <section className="tux-section" aria-live="polite">
            <div className="tux-result-head">
              <h2>Sales near {isCoords(o.q) ? "your location" : o.q}</h2>
              <div className="tux-result-tools">
                <button className="tux-link-btn" onClick={copyLink}>{copied ? "Link copied" : "Share"}</button>
                <button className="tux-link-btn" onClick={() => setAlertOpen(true)}>Get price alerts</button>
              </div>
            </div>
            {widened && (
              <p className="tux-note">We widened the search to {o.search.radius_km} km to find enough sales.</p>
            )}

            <div className="tux-stats">
              <div className="tux-stat">
                <span>Median price{latest ? ` (${latest.year}${latest.year === Number(S.lastYear) ? " so far" : ""})` : ""}</span>
                <strong>{eur(latest?.median_price)}</strong>
                {yoy != null && prev && (
                  <em className={yoy >= 0 ? "tux-up" : "tux-down"}>
                    {yoy >= 0 ? "▲" : "▼"} {Math.abs(yoy).toFixed(1)}% vs {prev.year}
                  </em>
                )}
              </div>
              <div className="tux-stat">
                <span>Sales found</span>
                <strong>{o.search.count.toLocaleString()}</strong>
                <em>within {o.search.radius_km} km</em>
              </div>
              <div className="tux-stat">
                <span>Typical range{latest ? ` (${latest.year})` : ""}</span>
                <strong>{latest ? `${shortEur(latest.min_price)} – ${shortEur(latest.max_price)}` : "–"}</strong>
                <em>lowest to highest</em>
              </div>
            </div>

            {o.exact.length === 0 && looksLikeAddress(o.q) && (
              <div className="tux-callout">
                <strong>No recorded sale for {o.q}.</strong> The register only lists homes sold since 2010, so these are
                neighbouring sales. <Link to={valuationHref}>Get an estimate for this home →</Link>
              </div>
            )}

            <div className="tux-tabs" role="tablist">
              <button role="tab" aria-selected={view === "list"} className={view === "list" ? "on" : ""} onClick={() => setView("list")}>List</button>
              <button role="tab" aria-selected={view === "map"} className={view === "map" ? "on" : ""} onClick={() => setView("map")}>Map</button>
            </div>

            {view === "list" ? (
              <>
                <ul className="tux-cards">
                  {list.slice(0, shown).map((p) => (
                    <PropertyCard key={p.id} p={p} badge={exactIds.has(p.id) ? "This address" : undefined} />
                  ))}
                </ul>
                {shown < list.length && (
                  <button className="tux-btn tux-btn-ghost tux-more" onClick={() => setShown((n) => n + PAGE_SIZE)}>
                    Show more ({list.length - shown} left)
                  </button>
                )}
                {o.search.count >= 200 && <p className="tux-hint">Showing the 200 most recent. Narrow the radius to see fewer.</p>}
              </>
            ) : (
              <div className="tux-map">
                <ClientOnly fallback={<div className="tux-map-ph" />}>
                  {() => (
                    <Suspense fallback={<div className="tux-map-ph" />}>
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
              <div className="tux-trend">
                <h3>Price trend in this area</h3>
                <TrendsChart data={o.trends} onClose={() => {}} inline />
              </div>
            )}

            <div className="tux-next">
              <h3>What next?</h3>
              <div className="tux-next-grid">
                <Link to={valuationHref} className="tux-next-card tux-next-primary">
                  <strong>Value a home here</strong>
                  <span>Estimate from comparable sales</span>
                </Link>
                {areaMatch && (
                  <Link to={`/area/${areaMatch.slug}`} className="tux-next-card">
                    <strong>{areaMatch.name} guide</strong><span>Prices, streets, nearby areas</span>
                  </Link>
                )}
                {countyName && (
                  <Link to={`/county/${countySlug(countyName)}`} className="tux-next-card">
                    <strong>{countyName} prices</strong><span>County trends and recent sales</span>
                  </Link>
                )}
                {routingKey && (
                  <Link to={`/eircode/${routingKey}`} className="tux-next-card">
                    <strong>All sales in {routingKey}</strong><span>Eircode area overview</span>
                  </Link>
                )}
                <Link to="/polygon" className="tux-next-card">
                  <strong>Draw your own area</strong><span>Map search with shapes</span>
                </Link>
                <Link to="/mortgage" className="tux-next-card">
                  <strong>What can I borrow?</strong><span>Mortgage calculator</span>
                </Link>
              </div>
            </div>
          </section>
        )}

        {status !== "loading" && (
          <>
            <section className="tux-section">
              <h2>Browse by place</h2>
              <div className="tux-pills">
                {areas.map((a) => <Link key={a.slug} to={`/area/${a.slug}`}>{a.name}</Link>)}
                <Link to="/areaguides" className="tux-pill-more">All area guides →</Link>
              </div>
              <h3 className="tux-h3">Counties</h3>
              <div className="tux-pills">
                {COUNTIES.map((c) => <Link key={c} to={`/county/${countySlug(c)}`}>{c}</Link>)}
              </div>
            </section>

            <section className="tux-section tux-how">
              <h2>How it works</h2>
              <ol>
                <li><strong>Search</strong> an address, Eircode or town.</li>
                <li><strong>See</strong> what nearby homes sold for, when, and how prices moved.</li>
                <li><strong>Decide</strong> with a valuation, alerts or a deeper area guide.</li>
              </ol>
              <p className="tux-hint">
                Data: Property Price Register, {S.firstMonth} to {S.lastMonth}, {S.mappedPct}% of sales mapped, updated every
                two weeks. <Link to="/about#data-sources">How we handle the data →</Link>
              </p>
            </section>

            {posts.length > 0 && (
              <section className="tux-section">
                <h2>Latest analysis</h2>
                <ul className="tux-posts">
                  {posts.map((p) => <li key={p.slug}><Link to={`/blog/${p.slug}`}>{p.title}</Link></li>)}
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
        counties={counties.length ? counties : [...COUNTIES]}
      />
      <TuxFooter />
    </>
  );
}
