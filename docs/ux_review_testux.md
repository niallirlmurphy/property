# UX review and `/testux` prototype

Scope: how a first-time visitor (mostly from Google) and a returning visitor experience homeiq.ie, what likely drives bounce, and what to change. Based on a read of the code (`main.tsx`, `App.tsx`, `HomeIntro.tsx`, `SearchPanel.tsx`, `ResultsList.tsx`, `TrendsChart.tsx`, county/area/eircode/street pages, `index.css`) and a single fetch of the live homepage HTML. No analytics were available, so everything below is code-derived judgement, not measured. Check it against Search Console landing pages and Vercel Analytics before committing effort.

## What a visitor sees today

Entry points split in two. Most organic traffic should land on the prerendered county/area/eircode/street/development pages; the home page serves brand and generic queries ("house prices ireland", "property price register").

Home page (`App.tsx`):
- Desktop: a 300px sidebar holding a 4-control form (Address, Radius, Period, County defaulting to Dublin) plus an "Email Alert" button, with the intro text and ~100 links squeezed into the same sidebar below it. The big area to the right is an empty Ireland map.
- Mobile (<640px): the form fills the first screen (address, two selects in a row, county select, Search button, then the Email Alert button). The value proposition (`h2` "Every Irish home sale since 2010, on a map") is below the fold, under the form. The header `h1` is a small 13px line: "Ireland Property Price Valuation and Trend Insights".

## Bounce drivers found

1. **Form before value.** Four inputs and an email-alert CTA stand between the visitor and an answer. Radius, Period and County are decisions most people cannot make before seeing anything (`SearchPanel.tsx`). The placeholder `D14, Rathmines, 53.33,-6.26` mixes formats and suggests the box is for experts.
2. **No answer without typing.** Nothing useful appears until a search is run. There is no example, no "latest sales", no median for anywhere. Time to first useful answer for a cold visitor is: understand form, type, submit, wait.
3. **Search result has no summary.** `App.tsx` computes trends client-side (`calculateTrendsFromProperties`), and the chart was removed from the page because that series was wrong (comment in `App.tsx`). So results are a bare list: no median, no change over time, no count in the headline. The backend `/trends` endpoint already returns the correct series.
4. **Dead ends after results.** `ResultsList.tsx` cards link nowhere. The only onward link is the valuation link in the "no exact match" note. No path to the area/county/Eircode pages, mortgage calculator or alerts based on what was just searched.
5. **Mobile result flow.** After a search the form is hidden (`.app[data-tab="map"] .search-wrapper {display:none}`) and the user lands on the map with the list behind a tab. Refining a search means going back to the Search tab. The map arrives before the numbers.
6. **Weak empty and error states.** "No properties found. Try widening the radius, adjusting the date range, or clearing the county filter" is advice with no buttons. The default county of Dublin silently narrows searches for everyone outside Dublin; the recovery path is hidden in a dropdown.
7. **Home page is a link directory.** `HomeIntro.tsx` is good for crawlers, but for a human it is ~100 small text links in 13px type inside a sidebar. Good SEO, poor scan-ability and tap targets on mobile.
8. **Return-visit hooks are thin.** Only the last five searches (in a dropdown that appears on focus) and the email alert modal. No "latest sales", no saved places, no reason to come back that the home page shows.
9. **Footer uses plain `<a href>`** (`Footer.tsx`), so every footer click is a full page reload and skips client routing and the lazy chunk preload.
10. **Console noise and error copy.** `api.ts` logs every request and response to the console; errors can surface as "Network error: ... Backend URL: ...", which is developer text, not user text.
11. **Content pages end abruptly.** County/area pages (`AreaPage.tsx` etc.) have a search box nowhere on them; the only way back to searching is the header home icon. Visitors landing from Google on an area page who want a specific street have no inline search.

## Recommendations, ranked by impact / effort

| # | Change | Where | Impact | Effort |
|---|--------|-------|--------|--------|
| 1 | One search box above the fold; move Radius/County/Period into a collapsed "Radius & county" disclosure; add example chips and "Use my location" | `SearchPanel.tsx`, `App.tsx` layout | High | Low |
| 2 | Answer-first results: stats strip (median, change vs prior year, count, range) from `/trends`, then list, with the map as a tab; stop client-side trend maths | `App.tsx`, `ResultsList.tsx`, `TrendsChart.tsx` | High | Medium |
| 3 | Show something before the first search: "latest sales" with a county switcher from `/county-recent` and `/trends` | `HomeIntro.tsx` / new home | High | Low |
| 4 | "What next?" block after every result, built from the result (area guide, county, Eircode routing key, valuation prefilled with the address, mortgage, polygon, alerts) | `ResultsList.tsx` | High | Low |
| 5 | Search box on county/area/eircode/street pages that jumps to `/?q=...` (or the new flow), so organic landers who want a specific address are not stranded | `CountyPageTemplate.tsx`, `AreaPage.tsx`, `EircodePage.tsx`, `StreetPage.tsx` | High | Low |
| 6 | Recovery states with buttons: widen radius, all counties, valuation link, Eircode tip; tell the user when the radius auto-widened | `ResultsList.tsx`, `SearchPanel.tsx` | Medium | Low |
| 7 | Skeleton loading instead of an empty pane and spinner on the button | `App.tsx`, `ResultsList.tsx` | Medium | Low |
| 8 | Mobile: keep the search box visible (sticky/compact) after a search; default the post-search view to the summary and list, map on demand | `index.css` mobile block, `App.tsx` | Medium | Medium |
| 9 | Return-visit features: recent chips visible on the home page, "Share" link, alerts offered after results rather than before | `SearchPanel.tsx` | Medium | Low |
| 10 | Replace footer `<a>` with `<Link>`; remove `console.log` from `api.ts`; friendlier error messages | `Footer.tsx`, `api.ts` | Low | Low |
| 11 | Replace the 100-link wall with scannable pills (areas, counties) and keep the full directory lower on the page or on `/areaguides` (SEO value kept by keeping the links in the HTML) | `HomeIntro.tsx` | Medium | Medium |

Caution on SEO: the current prerendered homepage carries the FAQ and Dataset structured data and ~100 internal links. Any redesign of `/` must keep those in the static HTML. The prototype does not try to replace them; it leaves them out because it is noindex.

Not done / worth doing next: autocomplete (the backend only has `/routing-keys/autocomplete`; a place/address suggest endpoint would be needed, and is a backend change), per-result "value this home" links, and measuring before and after (Search Console landing-page bounce, Vercel Analytics events on search submit and next-step clicks).

## Prototype at `/testux`

Files: `frontend/src/pages/TestUxPage.tsx`, `frontend/src/pages/TestUxPage.css` (all rules `tux-` prefixed), one added route line in `frontend/src/main.tsx`.

- Hero with one search field, "Use my location", "Radius & county" disclosure (county defaults to Dublin as on the live site), example chips and the visitor's recent searches (own localStorage key `homeiq_tux_recent`, so the live site's list is untouched).
- After a search: skeleton, then a stats strip (median with change vs previous year, sales found, range), a notice if the backend widened the radius, an exact-address highlight and "no recorded sale" callout with a valuation link, List/Map tabs (existing `MapView`), 10-at-a-time list, the existing `TrendsChart` fed by `/trends`, and a "What next?" grid (valuation prefilled, area guide, county, Eircode routing key, polygon, mortgage). Share and alerts (existing `EmailAlertModal`) in the result header.
- Empty and error states with one-tap recovery (wider radius, all counties).
- Below the fold, before or after searching: latest sales and median for six counties (via `fetchCountySummary`), place pills, how it works, latest posts.
- All data comes from the real API (`searchProperties`, `fetchTrends`, `searchExactAddress`, `fetchCountySummary`, `fetchCounties`) and existing components; no mock data, no client-side filtering or statistics. Deduping the exact-address hit against the radius results mirrors what `App.tsx` already does.
- `<meta name="robots" content="noindex,nofollow">` via `Head`, no canonical, not in `sitemap.xml`, not in the waffle menu or footer.

Verification: `npm run build` passes and `dist/testux/index.html` carries the noindex tag. Not verified in a browser: the available browser tool only opens https URLs, so the dev server could not be screenshotted at desktop and mobile widths, and the live API round trip from the page was not exercised end to end. Do a manual pass with `npm run dev` and `VITE_API_URL` set.

## Final rollout

The /testux design (OS-map style: bog green and gorse) is now the whole site.
- Tokens live in `frontend/src/styles/theme.css` (CSS variables). Shared chrome and building blocks (cards, stat tiles, tables, chart containers, breadcrumbs, gorse buttons, reduced-motion) are in `styles/site-chrome.css`.
- `components/SiteHeader.tsx` and `SiteFooter.tsx` replace the old header, WaffleMenu and footer on every page (`PageHeader` and `Footer` re-export them). Footer links use router `<Link>`.
- `/` is the /testux experience (`App.tsx`, `styles/home.css`) with the indexable HomeIntro copy, meta and JSON-LD kept. /testux, /testux2 and /testux3 remain, noindex.
- Not restyled: Camino (Tailwind) pages, Leaflet internals, held files (HeatmapBody and two heatmap blog posts keep old hex colours).
