/**
 * County content registry
 *
 * Import and export all county content here.
 * To add a new county, create the file and add it to this index.
 */

import { corkContent } from "./cork";
import { galwayContent } from "./galway";
import type { CountyContent } from "../countyData";

export const countyContent: Record<string, CountyContent> = {
  cork: corkContent,
  galway: galwayContent,
  // Add more counties here as you create them
};

/**
 * Get county content by slug
 */
export function getCountyContent(slug: string): CountyContent | undefined {
  return countyContent[slug.toLowerCase()];
}

/**
 * Check if a county has custom content
 */
export function hasCountyContent(slug: string): boolean {
  return slug.toLowerCase() in countyContent;
}

/**
 * List all counties with custom content
 */
export function listCountiesWithContent(): string[] {
  return Object.keys(countyContent);
}
