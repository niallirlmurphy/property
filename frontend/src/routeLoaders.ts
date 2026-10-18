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
import { areaFromSlug } from "./areas";
import type { AreaSummary, CountySummary, DevelopmentData, EircodePageData, StreetData } from "./types";
import type { DevelopmentConfig } from "./developmentRegistry";
import type { StreetConfig } from "./streetRegistry";

const AREA_DATA = import.meta.glob<{ default: AreaSummary }>("./data/areas/*.json");
const COUNTY_DATA = import.meta.glob<{ default: CountySummary }>("./data/counties/*.json");
const EIRCODE_DATA = import.meta.glob<{ default: EircodePageData }>("./data/eircodes/*.json");
const STREET_DATA = import.meta.glob<{ default: StreetData }>("./data/streets/*.json");
const DEVELOPMENT_DATA = import.meta.glob<{ default: DevelopmentData }>("./data/developments/*.json");

async function read<T>(load: (() => Promise<{ default: T }>) | undefined | null | false): Promise<T | null> {
  return load ? (await load()).default : null;
}

export async function areaLoader({ params }: LoaderFunctionArgs): Promise<AreaSummary | null> {
  if (!import.meta.env.SSR) return null;
  const config = areaFromSlug(params.slug ?? "");
  return read(config && AREA_DATA[`./data/areas/${config.slug}.json`]);
}

// Also serves the custom-template counties (CountyPageTemplate reads the same loader data).
export async function countyLoader({ params }: LoaderFunctionArgs): Promise<CountySummary | null> {
  if (!import.meta.env.SSR) return null;
  return read(COUNTY_DATA[`./data/counties/${params.slug ?? ""}.json`]);
}

export async function eircodeLoader({ params }: LoaderFunctionArgs): Promise<EircodePageData | null> {
  if (!import.meta.env.SSR) return null;
  return read(EIRCODE_DATA[`./data/eircodes/${(params.code ?? "").toUpperCase()}.json`]);
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

// /areaguides development cards: link fields plus headline figures.
export interface DevelopmentCard {
  slug: string;
  name: string;
  area: string;
  median: number;
  count: number;
}

export async function areaGuidesLoader(): Promise<DevelopmentCard[] | null> {
  if (!import.meta.env.SSR) return null;
  const { DEVELOPMENT_CONFIGS } = await import("./developmentRegistry");
  const cards = await Promise.all(DEVELOPMENT_CONFIGS.map(async ({ slug, name, area }) => {
    const data = await read(DEVELOPMENT_DATA[`./data/developments/${slug}.json`]);
    return data && { slug, name, area, median: data.stats.median, count: data.stats.count };
  }));
  return cards.filter((c): c is DevelopmentCard => c !== null);
}
