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

/**
 * A post is live once its `date` (publication date) is today or earlier.
 * Future-dated posts are "scheduled": hidden from the blog list, the sitemap and
 * prerendering, and they 404 on direct access until the date arrives. The check
 * runs at render time (string compare on YYYY-MM-DD), so a scheduled post goes
 * live on its date even without a redeploy — and bakes into the static build on
 * the next deploy after that date.
 */
export function isPublished(post: BlogPost, now: Date = new Date()): boolean {
  return post.date <= now.toISOString().slice(0, 10);
}

/** BLOG_POSTS with any future-dated (scheduled) posts removed. */
export function publishedPosts(now: Date = new Date()): BlogPost[] {
  return BLOG_POSTS.filter((p) => isPublished(p, now));
}

// Blog posts index - add new posts here
export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "irish-property-market-health-36-months",
    title: "Ireland's Property Market Is Stable but Stretched: Price Growth Has Halved and Sales Have Plateaued",
    description: "We analysed 166,000 cleaned Property Price Register sales from October 2023 to September 2026: sales volumes, median and average prices, the slowdown in growth, Dublin vs the regions, urban vs rural, Dublin postcodes and the rise of new builds — with charts.",
    date: "2026-10-03",
    author: "HomeIQ Team",
    tags: ["Analysis", "Market Report", "PPR", "Dublin", "New Builds"],
    readTime: "9 min read"
  },
  {
    slug: "barings-ires-reit-takeover-offer-fair-value",
    title: "Barings' €727m Bid for IRES REIT: Fair Price, or Is the Portfolio Undervalued?",
    description: "Barings has offered €1.386 a share in cash for IRES REIT — a ~20% premium to the share price, but almost exactly book NAV. We revisit our PPR-based valuation of the portfolio (~€1.52bn, or ~186c a share) and ask whether shareholders should accept or hold out.",
    date: "2026-09-28",
    author: "HomeIQ Team",
    tags: ["Analysis", "IRES REIT", "Takeover", "Valuation", "Dublin"],
    readTime: "8 min read"
  },
  {
    slug: "how-homeiq-values-a-home",
    title: "How HomeIQ Values a Home: From Raw PPR Data to a Number You Can Trust",
    description: "A plain-English look inside our valuation engine: why the Property Price Register is the perfect base, how we enrich it with location, property type and bedroom counts, and the recent work on outliers and size relationships that makes each estimate more trustworthy.",
    date: "2026-10-11",
    author: "HomeIQ Team",
    tags: ["Guide", "Valuation", "PPR", "Methodology"],
    readTime: "7 min read"
  },
  {
    slug: "valuing-ires-reit-property-portfolio",
    title: "Valuing the Property Portfolio of IRES REIT plc Using Our Enriched PPR Data",
    description: "We pointed our valuation engine at Ireland's largest residential landlord and valued all 3,615 IRES-owned apartments, unit by unit, from public sold-price data. The result: about €1.52 billion — roughly 19% above book, and a look at how apartment-aware valuation works.",
    date: "2026-09-27",
    author: "HomeIQ Team",
    tags: ["Analysis", "Dublin", "IRES REIT", "Apartments", "Valuation"],
    readTime: "9 min read"
  },
  {
    slug: "how-to-use-a-mortgage-calculator-affordability-interest-rates",
    title: "How to Use a Mortgage Calculator: Affordability, Interest Rates & Application Tips",
    description: "Plan your mortgage before you apply. See how to use HomeIQ's calculator to work out what you can afford, why a small interest-rate change costs tens of thousands over the term, plus the DOs and DON'Ts of a strong mortgage application.",
    date: "2026-09-21",
    author: "HomeIQ Team",
    tags: ["Guide", "Mortgage", "Affordability", "Interest Rates", "First Time Buyer"],
    readTime: "9 min read"
  },
  {
    slug: "do-solar-panels-add-value-to-your-home-ireland",
    title: "Do Solar Panels Add Value to Your Home? An Irish Guide",
    description: "Solar can genuinely add value to an Irish home — but only if it's installed and documented right. How to avoid scams, choose an SEAI-registered installer, and the paperwork checklist buyers and sellers must not skip.",
    date: "2026-08-17",
    author: "HomeIQ Team",
    tags: ["Guide", "Solar", "Energy", "Home Improvement", "Property Value"],
    readTime: "8 min read"
  },
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
