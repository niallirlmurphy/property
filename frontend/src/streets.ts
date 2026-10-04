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
