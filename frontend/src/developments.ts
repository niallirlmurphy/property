// Development links for client code: the registry trimmed to the fields needed to
// link to developments (see the registryLinks plugin in vite.config.ts). The full
// entries, with description text, are in ./developmentRegistry.
import links from "virtual:development-links";
import type { DevelopmentLink } from "./developmentRegistry";

export type { DevelopmentLink };

export const DEVELOPMENTS: DevelopmentLink[] = links;

export function developmentsForArea(areaSlug: string): DevelopmentLink[] {
  return DEVELOPMENTS.filter(d => d.relatedAreas.some(a => a.slug === areaSlug));
}
