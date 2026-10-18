// Development registry, including the long description/info text. Build-time
// only: imported by vite.config.ts and (dynamically, during prerender) by the
// development route loaders, so the text never ships in a JS bundle.
import registry from "./data/developments_registry.json";

export interface DevelopmentConfig {
  slug: string;
  name: string;
  area: string;
  county: string;
  countySlug: string;
  pinName: string;        // development_pins.name; decides which sales belong
  salesMatch?: string;    // optional to_tsquery narrowing the pin's sales (e.g. Honeypark: apartment blocks only)
  latitude: number;
  longitude: number;
  description: string;
  info: string;
  areaInfo: string;
  relatedAreas: { slug: string; name: string }[];
  eircode?: string;       // Dublin routing key with an /eircode page
}

// The fields client pages get (via `virtual:development-links`) to link to developments.
export const DEVELOPMENT_LINK_FIELDS = ["slug", "name", "area", "relatedAreas"] as const;

export type DevelopmentLink = Pick<DevelopmentConfig, (typeof DEVELOPMENT_LINK_FIELDS)[number]>;

export const DEVELOPMENT_CONFIGS: DevelopmentConfig[] = registry as DevelopmentConfig[];

export function developmentConfigFromSlug(slug: string): DevelopmentConfig | undefined {
  return DEVELOPMENT_CONFIGS.find(d => d.slug === slug);
}
