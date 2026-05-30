## Complete Content Management Guide

This guide explains how to create and manage all content on HomeIQ.ie.

## Overview

HomeIQ uses a **hybrid content system**:
- **County pages**: TypeScript data files (no React knowledge needed)
- **Blog posts**: Markdown files (simple text format)
- **Static pages**: React/TypeScript (for complex layouts)

---

## County Pages

### Creating a New County Page

**Step 1: Generate the template**
```bash
./scripts/create-county-content.sh kerry
```

This creates `frontend/src/content/counties/kerry.ts` with all the sections pre-filled.

**Step 2: Edit the content**

Open the file and fill in all sections. You're just editing data - no code!

```typescript
export const kerryContent: CountyContent = {
  name: "Kerry",
  slug: "kerry",

  // SEO - appears in Google search results
  metaTitle: "Kerry Property Prices & Market Trends",
  metaDescription: "Explore property prices...",

  // Page content - write in plain text
  intro: "County Kerry property prices...",  // 150-200 words
  marketOverview: "Kerry's property market...",  // 200-300 words
  trendsCommentary: "Kerry prices have...",  // 100-150 words

  // Lists - add as many as needed
  popularAreas: [
    {
      name: "Killarney",
      slug: "killarney",
      description: "Tourist hub, national park, high demand"
    },
    // Add 5-10 areas
  ],

  faqs: [
    {
      question: "What is the average house price in Kerry?",
      answer: "The average house price is..."
    },
    // Add 5 FAQs
  ],

  neighboringCounties: ["cork", "limerick", "clare"],

  highlights: [
    "Major tourism economy",
    "Wild Atlantic Way appeal",
    // Add 4-6 highlights
  ]
};
```

**Step 3: Register the county**

Edit `frontend/src/content/counties/index.ts`:

```typescript
import { kerryContent } from "./kerry";

export const countyContent: Record<string, CountyContent> = {
  cork: corkContent,
  galway: galwayContent,
  kerry: kerryContent,  // Add this line
};
```

**Step 4: Test locally**
```bash
cd frontend
npm run dev
# Visit: http://localhost:5173/county/kerry
```

**Step 5: Deploy**
```bash
git add frontend/src/content/counties/kerry.ts
git add frontend/src/content/counties/index.ts
git commit -m "Add Kerry county content"
git push
```

**Step 6: Submit to search engines**
```bash
./scripts/submit_indexnow.sh https://homeiq.ie/county/kerry
```

### Content Writing Tips

**Intro (150-200 words):**
- Lead with current price: "County X property prices in 2024 averaged €XXX"
- Mention transaction volume: "with X,XXX sales recorded"
- List popular areas: "from X city to coastal Y and commuter towns like Z"
- State YoY change: "Prices rose X% year-on-year"
- Explain why: "driven by tech growth/tourism/lifestyle appeal"

**Market Overview (200-300 words):**
- Urban vs rural dynamics
- Price ranges by area
- Property types available
- Buyer demographics
- Economic drivers
- Recent developments

**Trends Commentary (100-150 words):**
- Price movement since 2010
- Which areas performed best
- Notable market events
- Future outlook

**Popular Areas (5-10 items):**
- Mix of urban, suburban, rural
- Include price context in description
- Use keywords: "affordable", "premium", "family-friendly"

**FAQs (5 questions):**
1. Average house price
2. Most affordable areas
3. Price change history
4. Investment potential
5. Common property types

**Neighboring Counties:**
- List actual geographic neighbors
- Use lowercase slugs

**Highlights (4-6 items):**
- Unique selling points
- Economic factors
- Lifestyle features
- Infrastructure
- Market strengths

### Where to Get Data

**For statistics:**
```sql
-- Connect to database and query for county stats
SELECT 
  COUNT(*) as total_sales,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median,
  AVG(price) as average
FROM properties
WHERE county = 'Kerry'
  AND EXTRACT(YEAR FROM sale_date) = 2024
  AND not_full_market_price = FALSE;
```

**For market context:**
- Wikipedia (county overview)
- Local newspapers (recent developments)
- CSO.ie (economic data)
- Your own site data (trends endpoint)

---

## Blog Posts (Coming Soon)

**Note:** Blog system not yet fully implemented. Current status:
- ✅ Example markdown file created
- ⏳ Blog list page needed
- ⏳ Markdown parser needed
- ⏳ Routing needed

**When ready, workflow will be:**

```bash
# Create new post
cat > frontend/content/blog/my-post.md << EOF
---
title: "My Post Title"
slug: "my-post-title"
date: "2026-06-01"
author: "HomeIQ Team"
description: "Brief description for SEO"
tags: ["tag1", "tag2"]
---

# My Post Title

Content here in Markdown...
EOF

# Commit and deploy
git add frontend/content/blog/my-post.md
git commit -m "New blog post: My Post Title"
git push

# Submit to IndexNow
./scripts/submit_indexnow.sh https://homeiq.ie/blog/my-post-title
```

---

## Landing Pages

For landing pages like `/property-price-register`, `/house-prices-ireland`:

**These require React/TypeScript.** Either:
1. Ask Claude to create them
2. Duplicate an existing page and modify

**Structure:**
```typescript
// frontend/src/pages/PropertyPriceRegisterPage.tsx
import PageHeader from "../components/PageHeader";
import { usePageMeta } from "../hooks/usePageMeta";

export default function PropertyPriceRegisterPage() {
  usePageMeta(
    "Property Price Register Ireland - Complete Guide",
    "Everything you need to know about Ireland's Property Price Register..."
  );

  return (
    <>
      <PageHeader title="Property Price Register Ireland" />
      <div className="content-page">
        {/* Your content here */}
      </div>
    </>
  );
}
```

**Then add route in App.tsx.**

---

## Content Publishing Checklist

### For County Pages:
- [ ] Create file with `./scripts/create-county-content.sh <county>`
- [ ] Fill in all content sections
- [ ] Add to index.ts
- [ ] Test locally
- [ ] Commit and push
- [ ] Submit to IndexNow
- [ ] Check Google Analytics after 24 hours

### For Blog Posts (when ready):
- [ ] Create markdown file
- [ ] Write content with proper frontmatter
- [ ] Test locally
- [ ] Commit and push
- [ ] Submit to IndexNow
- [ ] Share on social media (optional)

### For Landing Pages:
- [ ] Create React component
- [ ] Add route
- [ ] Test locally
- [ ] Commit and push
- [ ] Submit to IndexNow

---

## Estimated Time per Content Type

| Content Type | Time to Create | Time to Update |
|-------------|----------------|----------------|
| County page | 30-60 mins | 10-15 mins |
| Blog post | 1-2 hours | 15-30 mins |
| Landing page | 2-4 hours | 30-60 mins |

---

## Content Calendar Recommendation

**Week 1-2:**
- Expand Dublin county page (already has data)
- Create 3 high-priority counties (Cork ✓, Galway ✓, Kildare)

**Week 3-4:**
- Create 3 landing pages
- Add FAQs to homepage

**Month 2:**
- Complete all 26 county pages (2-3 per week)
- Start blog (5-10 initial posts)

**Ongoing:**
- 2-3 blog posts per month
- Update county pages quarterly
- Add landing pages as needed

---

## Getting Help

**For county content:**
- Use Cork and Galway as examples
- Follow the template structure exactly
- ChatGPT can help write content if you provide data

**For technical issues:**
- Check that file is saved in correct location
- Verify import is added to index.ts
- Run `npm run build` to check for errors
- Check browser console for errors

**For content ideas:**
- See `docs/SEO_ACTION_PLAN.md` for topic suggestions
- See `docs/COUNTY_PAGE_TEMPLATE.md` for detailed examples

---

## Quick Reference

**File Locations:**
- County content: `frontend/src/content/counties/<slug>.ts`
- County index: `frontend/src/content/counties/index.ts`
- Blog posts: `frontend/content/blog/<slug>.md`
- Landing pages: `frontend/src/pages/<Name>Page.tsx`

**Scripts:**
- Create county: `./scripts/create-county-content.sh <slug>`
- Submit URL: `./scripts/submit_indexnow.sh <url>`
- Generate sitemap: `python3 scripts/generate_sitemap.py`

**Testing:**
- Local dev: `cd frontend && npm run dev`
- Production build: `cd frontend && npm run build`
- Run tests: `python3 tests/test_production_suite.py`

**Deployment:**
- Git push automatically deploys to Vercel
- Check deployment at: https://vercel.com/dashboard
- Changes live in 1-2 minutes

---

## Examples

See these files for complete examples:
- `frontend/src/content/counties/cork.ts` - Full county content
- `frontend/src/content/counties/galway.ts` - Another example
- `frontend/content/blog/example-post.md` - Blog post format
- `docs/COUNTY_PAGE_TEMPLATE.md` - Detailed writing guide
