// Street links for client code: the registry trimmed to the fields needed to
// list and link to streets (see the street-links plugin in vite.config.ts).
// The full entries, with description text, are in ./streetRegistry.
import links from "virtual:street-links";
import type { StreetLink } from "./streetRegistry";

export type { StreetLink };

export const STREETS: StreetLink[] = links;

export function streetsForCounty(countySlug: string): StreetLink[] {
  return STREETS.filter(s => s.countySlug === countySlug);
}

// Other streets to link from a street page: same area first, then the same county.
export function nearbyStreets(street: StreetLink, limit = 6): StreetLink[] {
  const others = STREETS.filter(s => s.countySlug === street.countySlug && s.slug !== street.slug);
  return [...others.filter(s => s.area === street.area), ...others.filter(s => s.area !== street.area)].slice(0, limit);
}

// Streets with pages whose area is one of `localities` (an area page's match terms).
export function streetsInLocalities(localities: string[], countySlug: string): StreetLink[] {
  const names = new Set(localities.map(l => l.toLowerCase()));
  return STREETS.filter(s => s.countySlug === countySlug && names.has(s.area.toLowerCase()));
}
