import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import L from "leaflet";
import { searchProperties, fetchTrends, fetchCounties, fetchEircode, fetchGeocode, fetchNearestPins } from "./api";
import SearchPanel from "./components/SearchPanel";
import ResultsList from "./components/ResultsList";
import EircodePanel from "./components/EircodePanel";
import TrendsChart from "./components/TrendsChart";
import EmailAlertModal from "./components/EmailAlertModal";
import type { Property, SearchResponse, TrendPoint, SearchParams, EircodeResponse } from "./types";
import WaffleMenu from "./components/WaffleMenu";
import ContactSidebar from "./components/ContactModals";
import { usePageMeta } from "./hooks/usePageMeta";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const activeIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function formatPrice(n: number) {
  return "€" + Math.round(n).toLocaleString("en-IE");
}

const ABBREV_MAP: [RegExp, string][] = [
  [/\brd\b/g,   "road"],
  [/\bave?\b/g, "avenue"],
  [/\bdr\b/g,   "drive"],
  [/\btce\b/g,  "terrace"],
  [/\bterr\b/g, "terrace"],
  [/\bcres\b/g, "crescent"],
  [/\bgdns?\b/g,"gardens"],
  [/\bsq\b/g,   "square"],
  [/\bpk\b/g,   "park"],
  [/\bblvd\b/g, "boulevard"],
  [/\bmt\b/g,   "mount"],
  [/\bnth\b/g,  "north"],
  [/\bsth\b/g,  "south"],
  [/\bst\b/g,   "street"],
  [/^no\.?\s*/g,""],
  [/,?\s*co\.?\s+/g, " "],
];

function normaliseAddr(s: string): string {
  let n = s.toLowerCase().replace(/[.,\-]/g, " ").replace(/\s+/g, " ").trim();
  for (const [pat, rep] of ABBREV_MAP) n = n.replace(pat, rep);
  return n.replace(/\s+/g, " ").trim();
}

function isExactMatch(address: string, query: string): boolean {
  const a = normaliseAddr(address);
  const q = normaliseAddr(query);
  return a.startsWith(q) || a.includes(q);
}

function partitionByExactMatch(results: Property[], query: string): { exact: Property[]; rest: Property[] } {
  const exact: Property[] = [];
  const rest: Property[] = [];
  for (const p of results) {
    if (isExactMatch(p.address, query)) exact.push(p);
    else rest.push(p);
  }
  return { exact, rest };
}

function MapFlyTo({ center, radius }: { center: [number, number]; radius: number }) {
  const map = useMap();
  useEffect(() => {
    const zoom = radius <= 0.5 ? 17 : radius <= 1 ? 16 : radius <= 2 ? 15 : radius <= 5 ? 14 : 13;
    map.flyTo(center, zoom, { duration: 1 });
  }, [center, radius, map]);
  return null;
}

function MapPanTo({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.panTo(center, { animate: true, duration: 0.5 });
  }, [center, map]);
  return null;
}

type MobileTab = "map" | "list" | "trends";

export default function App() {
  const [searchParams, setSearchParams] = useSearchParams();

  // SEO meta tags for home page
  usePageMeta();

  const [counties, setCounties] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [pendingCenter, setPendingCenter] = useState<{ lat: number; lon: number; radius_km: number } | null>(null);
  const [mapPins, setMapPins] = useState<Property[]>([]);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [showTrends, setShowTrends] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [lastSearchCounty, setLastSearchCounty] = useState<string | undefined>(undefined);

  const [eircodeResult, setEircodeResult] = useState<EircodeResponse | null>(null);
  const [eircodeCenter, setEircodeCenter] = useState<[number, number] | null>(null);

  const [activeProperty, setActiveProperty] = useState<Property | null>(null);
  const [lastSearchQuery, setLastSearchQuery] = useState<string>("");
  const [mobileTab, setMobileTab] = useState<MobileTab>("map");
  const [emailAlertOpen, setEmailAlertOpen] = useState(false);
  const [lastSearchParams, setLastSearchParams] = useState<SearchParams | null>(null);
  const searchGenRef = useRef(0);

  // Read initial search state from URL params
  const urlQ = searchParams.get("q") ?? "";
  const urlCounty = searchParams.get("county") ?? "Dublin";
  const urlRadius = Number(searchParams.get("radius_km") ?? "0.5");

  useEffect(() => {
    fetchCounties().then(setCounties).catch(() => {});
  }, []);

  // Fire search from URL params on initial load
  useEffect(() => {
    if (urlQ) {
      handleSearch({
        q: urlQ,
        radius_km: urlRadius || 0.5,
        county: urlCounty || undefined,
      });
    }
  }, []); // only on mount

  const handleSearch = async (params: SearchParams) => {
    const gen = ++searchGenRef.current;

    setLoading(true);
    setError(null);
    setActiveProperty(null);
    setEircodeResult(null);
    setEircodeCenter(null);
    setSearchResult(null);
    setMapPins([]);
    setTrends([]);
    setShowTrends(false);
    setLastSearchParams(params);
    setPendingCenter(null);
    setLastSearchQuery("");
    setHasSearched(true);
    setMobileTab("map");

    // Update URL so the search is bookmarkable/shareable
    const nextParams: Record<string, string> = { q: params.q };
    if (params.radius_km != null) nextParams.radius_km = String(params.radius_km);
    if (params.county) nextParams.county = params.county;
    setSearchParams(nextParams, { replace: true });

    try {
      const resolvedCenter = await fetchGeocode(params.q, params.county);
      if (searchGenRef.current !== gen) return;
      setPendingCenter({ ...resolvedCenter, radius_km: params.radius_km });
    } catch {
      // non-fatal
    }

    try {
      let [pins, result, trendData] = await Promise.all([
        fetchNearestPins(params, 10),
        searchProperties(params),
        fetchTrends(params.q, params.radius_km, params.county),
      ]);
      if (searchGenRef.current !== gen) return;

      // Auto-retry without county filter if 0 results and county was specified
      // Better UX: user likely searched for a place in a different county
      if (result.count === 0 && params.county) {
        const paramsNoCounty = { ...params, county: undefined };
        [pins, result, trendData] = await Promise.all([
          fetchNearestPins(paramsNoCounty, 10),
          searchProperties(paramsNoCounty),
          fetchTrends(params.q, params.radius_km, undefined),
        ]);
        if (searchGenRef.current !== gen) return;
      }

      const { exact, rest } = partitionByExactMatch(result.results, params.q);
      const sortedResults = [...exact, ...rest];
      const sortedResult = { ...result, results: sortedResults };

      const exactWithCoords = exact.filter(p => p.latitude != null && p.longitude != null);
      const pinIds = new Set(exactWithCoords.map(p => p.id));
      const mergedPins = [...exactWithCoords, ...pins.filter(p => !pinIds.has(p.id))];

      setMapPins(mergedPins);
      setSearchResult(sortedResult);
      setLastSearchQuery(params.q);
      setLastSearchCounty(params.county);
      setPendingCenter({ lat: result.center.lat, lon: result.center.lon, radius_km: result.radius_km });

      if (trendData.length > 0) {
        setTrends(trendData);
        setShowTrends(true);
      }
    } catch (e: any) {
      if (searchGenRef.current !== gen) return;
      setError(e.message ?? "An error occurred");
    } finally {
      if (searchGenRef.current === gen) setLoading(false);
    }
  };

  const handleEircode = async (code: string) => {
    const gen = ++searchGenRef.current;

    setLoading(true);
    setError(null);
    setActiveProperty(null);
    setSearchResult(null);
    setPendingCenter(null);
    setTrends([]);
    setShowTrends(false);
    setHasSearched(true);
    setMobileTab("map");

    try {
      const result = await fetchEircode(code);
      if (searchGenRef.current !== gen) return;
      setEircodeResult(result);

      const first = result.results.find((p) => p.latitude != null && p.longitude != null);
      if (first) setEircodeCenter([first.latitude!, first.longitude!]);

      const county = result.results[0]?.county ?? undefined;
      if (county) {
        const trendData = await fetchTrends(undefined, 5, county);
        if (searchGenRef.current !== gen) return;
        setTrends(trendData);
        setShowTrends(trendData.length > 0);
      }
    } catch (e: any) {
      if (searchGenRef.current !== gen) return;
      setError(e.message ?? "An error occurred");
    } finally {
      if (searchGenRef.current === gen) setLoading(false);
    }
  };

  const handleSelectProperty = (p: Property) => {
    setActiveProperty(p);
    setMobileTab("map");

    // Add marker for this property if it has coordinates and isn't already on the map
    // This ensures that when clicking a result, there's always a marker to pan to
    if (p.latitude != null && p.longitude != null) {
      const isAlreadyOnMap = mapPins.some(pin => pin.id === p.id);
      if (!isAlreadyOnMap) {
        setMapPins(prev => [...prev, p]);
      }
    }
  };

  const mapProperties: Property[] = eircodeResult
    ? (eircodeResult.results as Property[]).filter(p => p.latitude != null).slice(0, 10)
    : mapPins.filter(p => p.latitude != null);

  const panTarget: [number, number] | null =
    activeProperty?.latitude != null && activeProperty?.longitude != null
      ? [activeProperty.latitude, activeProperty.longitude]
      : null;

  const flyCenter: [number, number] | null = pendingCenter
    ? [pendingCenter.lat, pendingCenter.lon]
    : eircodeCenter;

  const flyRadius = pendingCenter?.radius_km ?? 1;
  const defaultCenter: [number, number] = [53.35, -7.5];
  const initialCenter: [number, number] = flyCenter ?? defaultCenter;

  const resultCount = searchResult?.count ?? eircodeResult?.stats.total_count ?? 0;

  const exactMatchIds = searchResult && lastSearchQuery
    ? new Set(searchResult.results.filter(p => isExactMatch(p.address, lastSearchQuery)).map(p => p.id))
    : new Set<number>();

  const resultSummary = searchResult
    ? { count: searchResult.count, radius_km: searchResult.radius_km }
    : null;

  const resultsPanel = eircodeResult ? (
    <EircodePanel
      result={eircodeResult}
      activeId={activeProperty?.id ?? null}
      onSelect={(p) => handleSelectProperty(p as Property)}
    />
  ) : (
    <ResultsList
      results={searchResult?.results ?? []}
      activeId={activeProperty?.id ?? null}
      onSelect={handleSelectProperty}
      exactMatchIds={exactMatchIds}
      hasSearched={hasSearched}
      loading={loading}
    />
  );

  const mapEl = (
    <MapContainer center={initialCenter} zoom={7} style={{ width: "100%", height: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {flyCenter && <MapFlyTo center={flyCenter} radius={flyRadius} />}
      {pendingCenter && searchResult && (
        <Circle
          center={[pendingCenter.lat, pendingCenter.lon]}
          radius={pendingCenter.radius_km * 1000}
          pathOptions={{ color: "#1a3c5e", fillColor: "#1a3c5e", fillOpacity: 0.06, weight: 2 }}
        />
      )}
      <MapPanTo center={panTarget} />
      {mapProperties
        .filter(p => p.latitude !== null && p.longitude !== null)
        .map(p => (
          <Marker
            key={p.id}
            position={[p.latitude!, p.longitude!]}
            icon={p.id === activeProperty?.id ? activeIcon : new L.Icon.Default()}
            eventHandlers={{ click: () => handleSelectProperty(p) }}
          >
            <Popup>
              <strong>{formatPrice(p.price)}</strong><br />
              {p.address}<br />
              <small>{p.sale_date.slice(0, 10)}{p.eircode ? ` · ${p.eircode}` : ""}</small>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );

  return (
    <div className="app" data-tab={mobileTab}>
      <header className="app-header">
        <Link to="/" className="app-header-home" aria-label="Home">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
        </Link>
        <Link to="/" className="app-header-title">
          <h1>Ireland Property Price Valuation and Trend Insights</h1>
        </Link>
        {resultCount > 0 && (
          <span className="header-count">
            {searchResult
              ? `${resultCount.toLocaleString()} results · ${searchResult.radius_km} km`
              : `${resultCount.toLocaleString()} sales · ${eircodeResult?.code}`}
          </span>
        )}
        <WaffleMenu />
      </header>

      <div className="search-wrapper">
        <SearchPanel
          counties={counties}
          loading={loading}
          error={error}
          onSearch={handleSearch}
          onEircode={handleEircode}
          resultSummary={resultSummary}
          defaultValues={{ q: urlQ, radius_km: urlRadius, county: urlCounty }}
          onOpenEmailAlert={() => setEmailAlertOpen(true)}
        />
      </div>

      <EmailAlertModal
        isOpen={emailAlertOpen}
        onClose={() => setEmailAlertOpen(false)}
        defaultAddress={lastSearchParams?.q || urlQ}
        defaultRadius={lastSearchParams?.radius_km || urlRadius}
        defaultCounty={lastSearchParams?.county || urlCounty}
        counties={counties}
      />

      <div className="results-pane">
        {resultsPanel}
      </div>

      <div className="map-container">
        {mapEl}
        {showTrends ? (
          <TrendsChart
            data={trends}
            onClose={() => setShowTrends(false)}
            county={lastSearchCounty}
          />
        ) : trends.length > 0 ? (
          <button className="trends-toggle" onClick={() => setShowTrends(true)}>
            📈 Show price trends
          </button>
        ) : null}
      </div>

      <div className="trends-pane">
        {trends.length > 0 && (
          <TrendsChart data={trends} onClose={() => {}} inline county={lastSearchCounty} />
        )}
        {resultsPanel}
      </div>

      <ContactSidebar />

      <nav className="mobile-tab-bar">
        <button
          className={mobileTab === "map" ? "active" : ""}
          onClick={() => setMobileTab("map")}
        >
          <span className="tab-icon">🗺️</span>
          Map
        </button>
        <button
          className={mobileTab === "list" ? "active" : ""}
          onClick={() => setMobileTab("list")}
        >
          <span className="tab-icon">🏠</span>
          Results
          {resultCount > 0 && (
            <span className="tab-badge">{resultCount > 999 ? "999+" : resultCount}</span>
          )}
        </button>
        <button
          className={mobileTab === "trends" ? "active" : ""}
          onClick={() => setMobileTab("trends")}
          disabled={trends.length === 0}
        >
          <span className="tab-icon">📈</span>
          Trends
        </button>
      </nav>
    </div>
  );
}
