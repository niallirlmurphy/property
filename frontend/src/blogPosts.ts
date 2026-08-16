// Blog post metadata (pure data — no React imports).
// Kept separate from BlogListPage.tsx so build tooling (vite.config.ts
// `ssgOptions.includedRoutes`) can import the post list without pulling
// React components/CSS into the esbuild-bundled config graph.

export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  date: string;
  author: string;
  tags: string[];
  readTime: string;
}

// Blog posts index - add new posts here
export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "does-living-near-a-good-school-add-value",
    title: "Does Living Near a Good School Add Value to Your Home?",
    description: "We analysed 214,888 Dublin sales to measure the property price premium for being near a school or university. The school-catchment effect is real — and bigger than the transport one.",
    date: "2026-08-16",
    author: "HomeIQ Team",
    tags: ["Analysis", "Dublin", "Schools", "Education", "Property Value"],
    readTime: "9 min read"
  },
  {
    slug: "does-being-near-a-luas-or-dart-add-value",
    title: "Does Living Near a Luas or DART Add Value to Your Home?",
    description: "We analysed 214,888 Dublin sales to see whether being near the Luas Green Line, Red Line or DART raises property prices. The honest answer surprises most people.",
    date: "2026-08-16",
    author: "HomeIQ Team",
    tags: ["Analysis", "Dublin", "Transport", "Luas", "DART"],
    readTime: "9 min read"
  },
  {
    slug: "best-month-to-sell-property-ireland",
    title: "Which Month Is the Best Month to Sell Your Property in Ireland?",
    description: "We analysed 749,031 property sales since 2010 to find the best time to sell a home in Ireland. Autumn brings the highest prices and the busiest market — here's the data.",
    date: "2026-07-18",
    author: "HomeIQ Team",
    tags: ["Analysis", "Selling", "Market Trends", "Seasonality"],
    readTime: "10 min read"
  },
  {
    slug: "irelands-longest-greenway",
    title: "Ireland's Longest Greenway",
    description: "Guide to Ireland's Longest Greenway - the 125km Royal Canal Greenway and Old Rail Trail route from Leixlip to Athlone.",
    date: "2026-06-22",
    author: "HomeIQ Team",
    tags: ["Greenway", "Midlands", "Amenities", "Cycling"],
    readTime: "5 min read"
  },
  {
    slug: "how-to-use-property-price-register",
    title: "How to Use Ireland's Property Price Register - Complete Guide",
    description: "Learn how to search and interpret data from Ireland's Property Price Register, including tips for finding accurate property sale prices.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Guide", "PPR", "Property Search"],
    readTime: "8 min read"
  },
  {
    slug: "dublin-property-prices-by-postcode-2026",
    title: "Dublin Property Prices by Postcode - 2026 Guide",
    description: "Complete breakdown of property prices across all Dublin postcodes, from D01 to D22 and D6W. Find the most and least expensive areas.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Dublin", "Analysis", "Postcodes"],
    readTime: "10 min read"
  },
  {
    slug: "understanding-eircode-property-search",
    title: "Understanding Eircode for Property Search",
    description: "What are Eircodes? How do routing keys work? Learn how to use Eircode data to search for property prices in your area.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Guide", "Eircode", "Tutorial"],
    readTime: "6 min read"
  },
];
