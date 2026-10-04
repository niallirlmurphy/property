// Full street registry, including the long description/info text. Build-time
// only: imported by vite.config.ts and (dynamically, during prerender) by the
// street route loader. Client code should use ./streets, which carries just the
// link fields, so the description text never ships in a JS bundle.
import registry from "./data/streets_registry.json";

export interface StreetConfig {
  slug: string;
  name: string;
  area: string;
  county: string;
  countySlug: string;
  category: "value" | "volume";
  rank: number;
  normalizedKey: string;
  description: string;
  info?: string;
  image?: string;
  imageAlt?: string;
}

// The fields client pages get (via `virtual:street-links`) to list and link to streets.
export const STREET_LINK_FIELDS = ["slug", "name", "area", "county", "countySlug", "category", "rank"] as const;

export type StreetLink = Pick<StreetConfig, (typeof STREET_LINK_FIELDS)[number]>;

export const STREET_CONFIGS: StreetConfig[] = registry as StreetConfig[];

export function streetConfigFromSlug(slug: string): StreetConfig | undefined {
  return STREET_CONFIGS.find(s => s.slug === slug);
}
