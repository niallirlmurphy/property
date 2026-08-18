import registry from "./data/streets_registry.json";

export interface StreetConfig {
  slug: string;
  name: string;
  area: string;
  county: string;
  countySlug: string;
  areaSlug?: string;
  category: "value" | "volume";
  rank: number;
  normalizedKey: string;
  description: string;
  info?: string;
  image?: string;
  imageAlt?: string;
}

export const STREETS: StreetConfig[] = registry as StreetConfig[];

export function streetFromSlug(slug: string): StreetConfig | undefined {
  return STREETS.find(s => s.slug === slug);
}

export function streetsForCounty(countySlug: string): StreetConfig[] {
  return STREETS.filter(s => s.countySlug === countySlug);
}
