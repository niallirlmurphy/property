# Area Guides Navigation Overhaul — Design

**Date:** 2026-08-16
**Status:** Approved (pending spec review)
**Author:** Claude + Niall

## Problem

The county / area / eircode "area guide" pages are riddled with navigation dead
ends. A read-only audit of the current frontend found:

1. **Live 404s.** `CountyPageTemplate` renders `popularAreas` as `/area/{slug}`
   cards, but most slugs have no `AREAS` entry, so they hit `AreaPage`'s "Area
   not found" screen. **6 of 7 Cork cards and 5 of 6 Galway cards are dead
   links in production right now** (only `cork-city` and `galway-city` exist).
2. **Dublin postcodes shown but not linked.** `DublinCountyPage` renders 21
   postcodes as non-clickable `<span className="postcode-badge">`, linking to
   none of the `/eircode/*` pages that exist precisely for them.
3. **23 of 26 counties are total dead ends.** Only Cork/Galway/Dublin have rich
   pages. The generic `CountyPage` offers only a PPR-explainer link and the home
   map — no areas, no neighbours, no hub.
4. **Leaf pages can't navigate up or sideways.** `AreaPage` and `EircodePage`
   don't link to their parent county, siblings, or a hub. `EircodePage` shows
   its county name as plain text.
5. **No hub / index page.** Nothing lists all counties/areas/postcodes. The
   WaffleMenu's "Area Guides" item hard-links to `/county/dublin` only.
6. **No visible breadcrumbs.** `usePageMeta` accepts a `breadcrumbs` arg but
   only emits `BreadcrumbList` JSON-LD — no clickable trail is rendered.

**Root cause:** there is **no data model connecting places**. `AreaConfig` has
no `county` field; `CountyContent` has no eircode field; `DUBLIN_EIRCODE_AREAS`
is never used for linking. Every "related place" link is either hard-coded or
free-text that silently breaks.

## Goals

- A master hub page at `/areaguides` that helps users discover what area-guide
  content exists, organised by province.
- Every guide page links up (to parent), sideways (to siblings), and to the hub.
- Zero broken `/area/*` links.
- Visible breadcrumbs on every guide page.
- All new pages prerender (SSG) via the existing `vite.config.ts` mechanism.

## Non-goals

- No backend/API changes. All data shown already comes from existing endpoints.
- No redesign of the existing page layouts beyond adding navigation elements.
- No new county content files (Cork/Galway/Dublin remain the only rich counties).

## Architecture

The design is built bottom-up: fix the data model first, then everything else
derives from it.

### Layer 1 — Relationship data (`frontend/src/areas.ts`)

**Add `county` to `AreaConfig`:**

```ts
export interface AreaConfig {
  slug: string;
  name: string;
  query: string;      // what to pass to the search API
  radius_km: number;
  description: string;
  county: string;     // NEW: parent county slug (e.g. "dublin", "cork")
}
```

Every existing `AREAS` entry gains a `county` value:

| slugs | county |
|---|---|
| rathmines, ranelagh, blackrock, dun-laoghaire, clontarf, howth, malahide, stillorgan, sandymount, portobello | `dublin` |
| galway-city | `galway` |
| cork-city | `cork` |
| limerick-city | `limerick` |
| waterford-city | `waterford` |
| kilkenny-city | `kilkenny` |
| drogheda, dundalk | `louth` |
| navan | `meath` |
| naas | `kildare` |
| bray | `wicklow` |

**Add 11 new `AREAS` entries** so the Cork/Galway `popularAreas` cards resolve.
Values (name/query/radius/description/county) are specified verbatim in the
implementation plan. Slugs:

- Cork (`county: "cork"`): `douglas`, `ballincollig`, `carrigaline`, `cobh`,
  `midleton`, `kinsale`
- Galway (`county: "galway"`): `salthill`, `oranmore`, `athenry`, `tuam`,
  `connemara`

These auto-prerender: `vite.config.ts` already maps every `AREAS` entry to
`/area/${a.slug}`.

**Add `D6W` to `DUBLIN_EIRCODE_AREAS`.** `DublinCountyPage` lists 22 postcodes
including `D6W`, but `DUBLIN_EIRCODE_AREAS` has only 21 keys (no `D6W`). Once
postcode badges become links, `/eircode/D6W` must be a real, prerendered target.
Add `D6W: "Dublin 6W"` so the map is complete and the page prerenders.

**Add a `PROVINCES` map** (province name → county slugs, in display order):

```ts
export const PROVINCES: { name: string; counties: string[] }[] = [
  { name: "Leinster", counties: ["carlow","dublin","kildare","kilkenny","laois","longford","louth","meath","offaly","westmeath","wexford","wicklow"] },
  { name: "Munster",  counties: ["clare","cork","kerry","limerick","tipperary","waterford"] },
  { name: "Connacht", counties: ["galway","leitrim","mayo","roscommon","sligo"] },
  { name: "Ulster",   counties: ["cavan","donegal","monaghan"] },
];
```

(26 counties total, matching `COUNTIES`.)

**Add helper functions:**

```ts
export function areasForCounty(countySlug: string): AreaConfig[];
export function provinceForCounty(countySlug: string): string | undefined;
export function countyForArea(areaSlug: string): string | undefined;
```

### Layer 2 — Shared `Breadcrumbs` component (`frontend/src/components/Breadcrumbs.tsx`)

A small presentational component rendering a visible, clickable trail:

```tsx
interface Crumb { name: string; url: string; }
export default function Breadcrumbs({ items }: { items: Crumb[] }): JSX.Element;
```

- Always prepends a "Home" crumb linking to `/`.
- Renders each item as a `<Link>`; the last item is plain text (current page).
- Fed the same `items` array that is passed to `usePageMeta`'s `breadcrumbs` arg,
  so the visible trail and the JSON-LD stay in sync.

### Layer 3 — The `/areaguides` hub (`frontend/src/pages/AreaGuidesPage.tsx`)

New route `{ path: "/areaguides", element: <AreaGuidesPage /> }` in
`main.tsx`, placed with the other static routes. Prerenders to
`/areaguides/index.html` (already covered by `includedRoutes`'s `staticPaths`
filter — it keeps every non-`:`/non-`*` route).

Page structure (organised **by province**):

1. `PageHeader` + `Breadcrumbs` (Home › Area Guides).
2. Intro paragraph explaining the three kinds of guide (counties, areas, Dublin
   postcodes).
3. **Four province sections.** Each lists its counties as `<Link to="/county/{slug}">`.
   Counties with rich content (`hasCountyContent(slug)`) get a "Detailed guide"
   badge so users can see where the depth is.
4. **Dublin postcodes block.** Links all `DUBLIN_EIRCODE_AREAS` keys to
   `/eircode/{key}`.
5. **Popular areas block.** Lists `AREAS` grouped by county, each linking to
   `/area/{slug}`.
6. `Footer`.
7. `usePageMeta("Area Guides — Ireland Property Prices by County, Area & Postcode", …, [{name:"Area Guides", url:"/areaguides"}])`.

Uses existing CSS classes (`content-page`, `content-section`, `county-links`,
`county-link-btn`, `areas-grid`, `area-card`, `postcode-badge`) where possible;
adds minimal new classes only if needed.

### Layer 4 — Wire up existing pages

| Page | Change |
|---|---|
| `DublinCountyPage` | Wrap each postcode badge in `<Link to={`/eircode/${row.postcode}`}>`; add `Breadcrumbs` (Home › Area Guides › Dublin); add a "Back to all area guides" link to `/areaguides` |
| `AreaPage` | Add `Breadcrumbs` (Home › Area Guides › County X › {area}); add "Part of County X" link via `countyForArea`; add `/areaguides` link. County crumb only shown when `countyForArea` resolves |
| `EircodePage` | Add `Breadcrumbs` (Home › Area Guides › Dublin › {code}); make the county name (`data.results[0]?.county`) a link to `/county/{slug}`; add a sibling-postcode list linking other `DUBLIN_EIRCODE_AREAS` keys; add `/areaguides` link |
| `CountyPage` (generic) | Add `Breadcrumbs` (Home › Area Guides › County X); add "Areas in County X" section via `areasForCounty` (only if non-empty); add "Nearby counties" — reuse province siblings via `provinceForCounty`; add `/areaguides` link |
| `CountyPageTemplate` | Cards now resolve (Layer 1). Add `Breadcrumbs`; add `/areaguides` link. (No dead-link changes needed beyond Layer 1.) |
| `WaffleMenu` | Repoint "Area Guides" item `href` from `/county/dublin` → `/areaguides` |

### Route precedence note

`/county/dublin` (bespoke `DublinCountyPage`) still wins over `/county/:slug`, so
`dublin.ts` content remains unused — that's pre-existing and out of scope. The
hub links `/county/dublin`, which correctly resolves to the bespoke page.

## Data flow

`areas.ts` becomes the single source of truth for place relationships. Pages
import helpers (`areasForCounty`, `countyForArea`, `provinceForCounty`,
`PROVINCES`) instead of hard-coding links. The hub and breadcrumbs read the same
maps, so adding a county/area/postcode later surfaces it everywhere automatically.

## Error handling

- `areaFromSlug`, `countyFromSlug` already return `undefined` for unknown slugs;
  new helpers follow the same convention. Pages guard on `undefined` (e.g. area
  page only shows the county crumb when `countyForArea` resolves).
- Unknown routes still fall through to the `*` → home redirect.

## Testing

No local Node in this environment; the Vercel preview build is the verification
oracle (same as the SSG work). Verification:

- **Prerender manifest** confirms `/areaguides/index.html` plus the 11 new
  `/area/*/index.html` and `/eircode/D6W/index.html` are emitted.
- **Production test suite** (`tests/test_production_suite.py`) extended with a
  lightweight check that `/areaguides` returns 200 and that a sample new area
  page (`/area/douglas`) returns 200 (not the "Area not found" shell). These run
  against the deployed URL.
- Manual spot-check after deploy: hub → county → area → back; Dublin postcode
  badge → eircode page → county link.

## Rollout

Single feature branch, implemented task-by-task via subagent-driven-development,
verified on a Vercel preview build, then PR to main (per the finishing-a-branch
flow used for the SSG work). After merge + deploy, submit the new `/areaguides`
URL (and any newly linkable pages) to IndexNow.

## Out of scope / deferred

- Reconciling the shadowed `dublin.ts` content (route precedence) — pre-existing.
- Adding rich `CountyContent` for the other 23 counties.
- `relatedAreas` / adjacency graph beyond province-level county grouping.
