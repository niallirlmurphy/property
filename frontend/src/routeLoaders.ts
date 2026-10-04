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
import { streetFromSlug } from "./streets";
import type { AreaSummary, CountySummary, EircodePageData, StreetData } from "./types";

const AREA_DATA = import.meta.glob<{ default: AreaSummary }>("./data/areas/*.json");
const COUNTY_DATA = import.meta.glob<{ default: CountySummary }>("./data/counties/*.json");
const EIRCODE_DATA = import.meta.glob<{ default: EircodePageData }>("./data/eircodes/*.json");
const STREET_DATA = import.meta.glob<{ default: StreetData }>("./data/streets/*.json");

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

export async function streetLoader({ params }: LoaderFunctionArgs): Promise<StreetData | null> {
  if (!import.meta.env.SSR) return null;
  const config = streetFromSlug(params.slug ?? "");
  return read(config && STREET_DATA[`./data/streets/${config.slug}.json`]);
}
