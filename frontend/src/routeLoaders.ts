// Build-time route loaders for the data-driven landing pages.
//
// They live here, not in the page modules, so main.tsx can attach them to the
// route statically while the page components themselves load lazily (a page's
// code is only downloaded when it's visited).
//
// Each glob is lazy and is only read at prerender time: vite-react-ssg inlines
// the loader result into each page's HTML and serves it as a per-page JSON file
// on client navigation, so none of this data is in the JS bundle. On the client
// the loaders are replaced by that static-data fetch. A missing file → null →
// the page's live-API fallback.
import type { LoaderFunctionArgs } from "react-router-dom";
import { AREAS, COUNTIES, areaFromSlug, countySlug } from "./areas";
import type {
  AreaSummary, CountySummary, CsoRegion, CsoRollingFigures, CsoSlice, DevelopmentData, EircodePageData, StreetData, TrendPoint,
} from "./types";
import type { DevelopmentConfig } from "./developmentRegistry";
import type { StreetConfig } from "./streetRegistry";

const AREA_DATA = import.meta.glob<{ default: AreaSummary }>("./data/areas/*.json");
const COUNTY_DATA = import.meta.glob<{ default: CountySummary }>("./data/counties/*.json");
const EIRCODE_DATA = import.meta.glob<{ default: EircodePageData }>("./data/eircodes/*.json");
const STREET_DATA = import.meta.glob<{ default: StreetData }>("./data/streets/*.json");
const DEVELOPMENT_DATA = import.meta.glob<{ default: DevelopmentData }>("./data/developments/*.json");

// Official CSO figures (data/cso.json, scripts/generate_cso_data.py), sliced per page.
interface CsoFile {
  latest_month: string;
  rppi_month: string;
  annual_year: string;
  source_url: string;
  rppi: Record<string, { index: number | null; change_12m: number | null }>;
  regions: Record<string, CsoRollingFigures & Record<string, unknown>>;
  routing_keys: Record<string, CsoRollingFigures & { name: string }>;
  counties: Record<string, { regions: string[]; rppi_series: string; rppi_region: string }>;
}

const monthName = (m: string) => m.split(" ").reverse().join(" ");   // "2026 August" -> "August 2026"

async function csoSlice(pick: (cso: CsoFile) => Partial<CsoSlice>): Promise<CsoSlice> {
  const cso = (await import("./data/cso.json")).default as unknown as CsoFile;
  return {
    latest_month: monthName(cso.latest_month), rppi_month: monthName(cso.rppi_month),
    annual_year: cso.annual_year, source_url: cso.source_url, ...pick(cso),
  };
}

function csoRoutingKeys(keys: string[]) {
  return csoSlice(cso => ({
    routing_keys: keys.filter(k => cso.routing_keys[k]).map(k => ({ key: k, ...cso.routing_keys[k] })),
  }));
}

function csoCounty(slug: string) {
  return csoSlice(cso => {
    const county = cso.counties[slug];
    if (!county) return {};
    const y = cso.annual_year;
    const regions: CsoRegion[] = county.regions.filter(r => cso.regions[r]).map(name => {
      const r = cso.regions[name];
      const { median_12m, median_12m_prev, existing_12m, new_12m, volume_12m } = r;
      return {
        name, median_12m, median_12m_prev, existing_12m, new_12m, volume_12m,
        house: r[`house_${y}`] as CsoRegion["house"], apartment: r[`apartment_${y}`] as CsoRegion["apartment"],
      };
    });
    const series = slug === "dublin"
      ? ["Dublin - all residential properties", "Dublin - houses", "Dublin - apartments"]
      : [county.rppi_series];
    series.push("National - all residential properties");
    return { regions, rppi: series.map(label => ({ label, change_12m: cso.rppi[label]?.change_12m ?? null })) };
  });
}

async function read<T>(load: (() => Promise<{ default: T }>) | undefined | null | false): Promise<T | null> {
  return load ? (await load()).default : null;
}

export async function areaLoader({ params }: LoaderFunctionArgs): Promise<AreaSummary | null> {
  if (!import.meta.env.SSR) return null;
  const config = areaFromSlug(params.slug ?? "");
  const data = await read(config && AREA_DATA[`./data/areas/${config.slug}.json`]);
  return data && config ? { ...data, cso: await csoRoutingKeys(config.routing_keys ?? []) } : data;
}

// Also serves the custom-template counties (CountyPageTemplate reads the same loader data).
export async function countyLoader({ params }: LoaderFunctionArgs): Promise<CountySummary | null> {
  if (!import.meta.env.SSR) return null;
  const data = await read(COUNTY_DATA[`./data/counties/${params.slug ?? ""}.json`]);
  return data ? { ...data, cso: await csoCounty(params.slug ?? "") } : data;
}

// /county/dublin has its own page (no PPR summary), just the CSO figures.
export async function dublinCountyLoader(): Promise<{ cso: CsoSlice } | null> {
  if (!import.meta.env.SSR) return null;
  return { cso: await csoCounty("dublin") };
}

export async function eircodeLoader({ params }: LoaderFunctionArgs): Promise<EircodePageData | null> {
  if (!import.meta.env.SSR) return null;
  const code = (params.code ?? "").toUpperCase();
  const data = await read(EIRCODE_DATA[`./data/eircodes/${code}.json`]);
  return data ? { ...data, cso: await csoRoutingKeys([code]) } : data;
}

export interface StreetPageData {
  street: StreetConfig;
  data: StreetData;
}

// Returns the street's full registry entry too, so the page needn't import the
// registry (and its description text) into its bundle.
export async function streetLoader({ params }: LoaderFunctionArgs): Promise<StreetPageData | null> {
  if (!import.meta.env.SSR) return null;
  const { streetConfigFromSlug } = await import("./streetRegistry");
  const street = streetConfigFromSlug(params.slug ?? "");
  const data = await read(street && STREET_DATA[`./data/streets/${street.slug}.json`]);
  return street && data ? { street, data } : null;
}

export interface DevelopmentPageData {
  development: DevelopmentConfig;
  data: DevelopmentData;
}

export async function developmentLoader({ params }: LoaderFunctionArgs): Promise<DevelopmentPageData | null> {
  if (!import.meta.env.SSR) return null;
  const { developmentConfigFromSlug } = await import("./developmentRegistry");
  const development = developmentConfigFromSlug(params.slug ?? "");
  const data = await read(development && DEVELOPMENT_DATA[`./data/developments/${development.slug}.json`]);
  return development && data ? { development, data } : null;
}

// The /developments index gets just the link fields.
export type DevelopmentIndexEntry = Pick<DevelopmentConfig, "slug" | "name" | "area" | "description">;

export async function developmentsIndexLoader(): Promise<DevelopmentIndexEntry[] | null> {
  if (!import.meta.env.SSR) return null;
  const { DEVELOPMENT_CONFIGS } = await import("./developmentRegistry");
  return DEVELOPMENT_CONFIGS.map(({ slug, name, area, description }) => ({ slug, name, area, description }));
}

// /areaguides: headline figures for the county buttons, town and development
// cards, and each Dublin street's routing key (for grouping by postcode).
export interface DevelopmentCard {
  slug: string;
  name: string;
  area: string;
  median: number;
  count: number;
}

export interface GuideFigure {
  median: number;
  count: number;
  change?: number;   // % on the previous year; counties only
}

export interface AreaGuidesData {
  year: number;
  counties: Record<string, GuideFigure>;
  areas: Record<string, GuideFigure>;
  developments: DevelopmentCard[];
  streetKeys: Record<string, string>;
}

// Town figures need this many sales in the year: area trends are scoped by
// locality, and small samples (or undercounted towns) give misleading medians.
const MIN_AREA_SALES = 50;
const MIN_COUNTY_SALES = 100;

function yearFigure(trends: TrendPoint[], year: number, minSales: number, withChange: boolean): GuideFigure | null {
  const cur = trends.find(t => t.year === year);
  if (!cur || cur.median_price == null || cur.count < minSales) return null;
  const prev = trends.find(t => t.year === year - 1);
  const change = withChange && prev?.median_price && prev.count >= minSales
    ? Math.round(1000 * (cur.median_price / prev.median_price - 1)) / 10
    : undefined;
  return { median: cur.median_price, count: cur.count, ...(change != null && { change }) };
}

// Most common routing key among a street's sales (eircode, else "Dublin N" in the address).
function streetRoutingKey(data: StreetData): string | null {
  const keys = new Map<string, number>();
  for (const t of data.transactions) {
    let key = t.eircode?.slice(0, 3).toUpperCase();
    if (!key) {
      const m = /Dublin (\d{1,2})(W?)\b/i.exec(t.address);
      key = m ? (m[2] ? "D6W" : "D" + m[1].padStart(2, "0")) : undefined;
    }
    if (key) keys.set(key, (keys.get(key) ?? 0) + 1);
  }
  return [...keys].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
}

export async function areaGuidesLoader(): Promise<AreaGuidesData | null> {
  if (!import.meta.env.SSR) return null;
  const year = new Date().getFullYear() - 1;   // last complete year
  const [{ DEVELOPMENT_CONFIGS }, { STREET_CONFIGS }] = await Promise.all([
    import("./developmentRegistry"), import("./streetRegistry"),
  ]);

  const counties: Record<string, GuideFigure> = {};
  for (const name of COUNTIES) {
    const slug = countySlug(name);
    const data = await read(COUNTY_DATA[`./data/counties/${slug}.json`]);
    const fig = data && yearFigure(data.trends, year, MIN_COUNTY_SALES, true);
    if (fig) counties[slug] = fig;
  }
  const areas: Record<string, GuideFigure> = {};
  for (const { slug } of AREAS) {
    const data = await read(AREA_DATA[`./data/areas/${slug}.json`]);
    const fig = data && yearFigure(data.trends, year, MIN_AREA_SALES, false);
    if (fig) areas[slug] = fig;
  }
  const developments: DevelopmentCard[] = [];
  for (const { slug, name, area } of DEVELOPMENT_CONFIGS) {
    const data = await read(DEVELOPMENT_DATA[`./data/developments/${slug}.json`]);
    if (data) developments.push({ slug, name, area, median: data.stats.median, count: data.stats.count });
  }
  const streetKeys: Record<string, string> = {};
  for (const s of STREET_CONFIGS.filter(s => s.countySlug === "dublin")) {
    const data = await read(STREET_DATA[`./data/streets/${s.slug}.json`]);
    const key = data && streetRoutingKey(data);
    if (key) streetKeys[s.slug] = key;
  }
  return { year, counties, areas, developments, streetKeys };
}
