/**
 * County content data structure
 *
 * Edit these files to update county page content.
 * No React knowledge needed - just edit the data!
 */

export interface FAQ {
  question: string;
  answer: string;
}

export interface PopularArea {
  name: string;
  slug: string;
  description: string;
}

export interface CountyContent {
  name: string;
  slug: string;

  // SEO
  metaTitle: string;
  metaDescription: string;

  // Page content
  intro: string;  // 150-200 words
  marketOverview: string;  // 200-300 words
  trendsCommentary: string;  // 100-150 words

  // Structured data
  popularAreas: PopularArea[];
  faqs: FAQ[];
  neighboringCounties: string[];  // slugs

  // Optional: custom stats or features
  highlights?: string[];  // Bullet points for key features
}

// Helper to get county display name from slug
export function countyDisplayName(slug: string): string {
  return slug.charAt(0).toUpperCase() + slug.slice(1);
}
