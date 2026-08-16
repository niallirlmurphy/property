# Area Guides Navigation Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate navigation dead ends across the county/area/eircode area-guide pages and add a master `/areaguides` hub, all driven from a single place-relationship data model.

**Architecture:** Add a `county` field + `PROVINCES` map + helper functions to `frontend/src/areas.ts` (single source of truth), then a shared `Breadcrumbs` component, a new `/areaguides` hub page, and wire every guide page to link up/sideways/to-hub. All new routes prerender via the existing `ssgOptions.includedRoutes` in `vite.config.ts`.

**Tech Stack:** React 18 + TypeScript, react-router-dom v6, vite-react-ssg 0.9.1 (build-time SSG), Vercel (nested dirStyle → clean URLs). Python/httpx production test suite.

## Global Constraints

- **No local Node/npm/tsc/vite.** This environment has no Node runtime; do NOT run `npm`, `tsc`, `vite`, or any build/test command for frontend code. The Vercel preview build is the verification oracle. Implementers make edits + commit ONLY.
- **Never bypass the pre-commit security hook** (no `git commit --no-verify`).
- **Never commit secrets.**
- **Commit message trailer:** every commit message ends with exactly:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Do NOT push** unless the human asks.
- **TypeScript strict:** the project compiles under strict mode on Vercel. All new/edited code must be fully typed — no `any`, no unused imports (unused imports/vars break the build).
- **County slugs** are produced by `countySlug(c) = c.toLowerCase().replace(/\s+/g,"-")`. Area/eircode/province slugs are lowercase literals as defined in `areas.ts`.
- **Reuse existing CSS classes** (`content-page`, `content-intro`, `content-section`, `stats-grid`, `stat-card`, `areas-grid`, `area-card`, `county-links`, `county-link-btn`, `postcode-badge`, `sales-table`, `postcode-table`) wherever they fit; add new classes to `frontend/src/index.css` only when no existing class works, and match the file's existing style conventions.
- **Route precedence is load-bearing:** in `main.tsx`, `/county/dublin` MUST remain before `/county/:slug`. Any new static route (e.g. `/areaguides`) goes with the other static routes, before dynamic `:slug`/`:code`/`*` routes.

---

## File Structure

- `frontend/src/areas.ts` — MODIFY: add `county` to `AreaConfig`, add `county` to all 20 existing entries, add 11 new area entries, add `D6W` to `DUBLIN_EIRCODE_AREAS`, add `PROVINCES`, add `areasForCounty`/`provinceForCounty`/`countyForArea`. (Layer 1 — foundation for everything.)
- `frontend/src/components/Breadcrumbs.tsx` — CREATE: shared visible breadcrumb trail. (Layer 2.)
- `frontend/src/pages/AreaGuidesPage.tsx` — CREATE: the `/areaguides` hub. (Layer 3.)
- `frontend/src/main.tsx` — MODIFY: register the `/areaguides` route + import.
- `frontend/src/pages/DublinCountyPage.tsx` — MODIFY: link postcode badges, breadcrumbs, hub link.
- `frontend/src/pages/AreaPage.tsx` — MODIFY: breadcrumbs, parent-county link, hub link.
- `frontend/src/pages/EircodePage.tsx` — MODIFY: breadcrumbs, county link, sibling postcodes, hub link.
- `frontend/src/pages/CountyPage.tsx` — MODIFY: breadcrumbs, areas-in-county, nearby-counties, hub link.
- `frontend/src/components/CountyPageTemplate.tsx` — MODIFY: breadcrumbs, hub link.
- `frontend/src/components/WaffleMenu.tsx` — MODIFY: repoint "Area Guides".
- `tests/test_production_suite.py` — MODIFY: add `/areaguides` + new-area-page reachability checks.

Task order respects dependencies: Task 1 (data model) unblocks all others; Task 2 (Breadcrumbs) is consumed by Tasks 4-8.

---

### Task 1: Place-relationship data model in `areas.ts`

**Files:**
- Modify: `frontend/src/areas.ts`

**Interfaces:**
- Consumes: nothing (leaf data module, no imports).
- Produces:
  - `AreaConfig` now has `county: string`.
  - `PROVINCES: { name: string; counties: string[] }[]`
  - `areasForCounty(countySlug: string): AreaConfig[]`
  - `provinceForCounty(countySlug: string): string | undefined`
  - `countyForArea(areaSlug: string): string | undefined`
  - `DUBLIN_EIRCODE_AREAS` gains key `D6W`.
  - New area slugs available for prerender: douglas, ballincollig, carrigaline, cobh, midleton, kinsale, salthill, oranmore, athenry, tuam, connemara.

- [ ] **Step 1: Add `county` to the `AreaConfig` interface**

Replace the interface (lines 1-7) with:

```ts
export interface AreaConfig {
  slug: string;
  name: string;
  query: string;  // what to pass to the search API
  radius_km: number;
  description: string;
  county: string;  // parent county slug (e.g. "dublin", "cork")
}
```

- [ ] **Step 2: Add `county` to every existing `AREAS` entry and append the 11 new areas**

Replace the entire `AREAS` array (current lines 9-30) with:

```ts
export const AREAS: AreaConfig[] = [
  { slug: "rathmines",      name: "Rathmines",       query: "Rathmines, Dublin",       radius_km: 1.5, description: "a popular inner-city suburb on Dublin's southside", county: "dublin" },
  { slug: "ranelagh",       name: "Ranelagh",         query: "Ranelagh, Dublin",        radius_km: 1,   description: "one of Dublin's most sought-after residential villages", county: "dublin" },
  { slug: "blackrock",      name: "Blackrock",        query: "Blackrock, Dublin",       radius_km: 1.5, description: "a coastal suburb south of Dublin city centre", county: "dublin" },
  { slug: "dun-laoghaire",  name: "Dún Laoghaire",   query: "Dún Laoghaire, Dublin",   radius_km: 2,   description: "a coastal town and harbour south of Dublin", county: "dublin" },
  { slug: "clontarf",       name: "Clontarf",         query: "Clontarf, Dublin",        radius_km: 1.5, description: "a seaside suburb on Dublin's northside", county: "dublin" },
  { slug: "howth",          name: "Howth",            query: "Howth, Dublin",           radius_km: 2,   description: "a picturesque fishing village and peninsula north of Dublin", county: "dublin" },
  { slug: "malahide",       name: "Malahide",         query: "Malahide, Dublin",        radius_km: 2,   description: "a coastal village north of Dublin known for its castle and marina", county: "dublin" },
  { slug: "stillorgan",     name: "Stillorgan",       query: "Stillorgan, Dublin",      radius_km: 1.5, description: "a suburban area in south County Dublin", county: "dublin" },
  { slug: "sandymount",     name: "Sandymount",       query: "Sandymount, Dublin",      radius_km: 1,   description: "a coastal village close to Dublin city centre", county: "dublin" },
  { slug: "portobello",     name: "Portobello",       query: "Portobello, Dublin",      radius_km: 1,   description: "a vibrant canalside neighbourhood in Dublin 8", county: "dublin" },
  { slug: "galway-city",    name: "Galway City",      query: "Galway City",             radius_km: 3,   description: "the cultural capital of the west of Ireland", county: "galway" },
  { slug: "salthill",       name: "Salthill",         query: "Salthill, Galway",        radius_km: 1.5, description: "a seaside suburb of Galway city with a popular promenade", county: "galway" },
  { slug: "oranmore",       name: "Oranmore",         query: "Oranmore, Galway",        radius_km: 2,   description: "a growing commuter town east of Galway city", county: "galway" },
  { slug: "athenry",        name: "Athenry",          query: "Athenry, Galway",         radius_km: 2,   description: "a historic walled town in County Galway", county: "galway" },
  { slug: "tuam",           name: "Tuam",             query: "Tuam, Galway",            radius_km: 2,   description: "a market town in north County Galway", county: "galway" },
  { slug: "connemara",      name: "Connemara",        query: "Clifden, Galway",         radius_km: 5,   description: "a scenic rural region on Galway's western coast", county: "galway" },
  { slug: "cork-city",      name: "Cork City",        query: "Cork City",               radius_km: 3,   description: "Ireland's second city on the River Lee", county: "cork" },
  { slug: "douglas",        name: "Douglas",          query: "Douglas, Cork",           radius_km: 1.5, description: "an upscale suburb on Cork city's southside", county: "cork" },
  { slug: "ballincollig",   name: "Ballincollig",     query: "Ballincollig, Cork",      radius_km: 2,   description: "a large commuter town west of Cork city", county: "cork" },
  { slug: "carrigaline",    name: "Carrigaline",      query: "Carrigaline, Cork",       radius_km: 2,   description: "a growing town south of Cork city", county: "cork" },
  { slug: "cobh",           name: "Cobh",             query: "Cobh, Cork",              radius_km: 2,   description: "a historic port town on Cork harbour", county: "cork" },
  { slug: "midleton",       name: "Midleton",         query: "Midleton, Cork",          radius_km: 2,   description: "a market town and distillery gateway in East Cork", county: "cork" },
  { slug: "kinsale",        name: "Kinsale",          query: "Kinsale, Cork",           radius_km: 2,   description: "a coastal gourmet destination and sailing hub in County Cork", county: "cork" },
  { slug: "limerick-city",  name: "Limerick City",    query: "Limerick City",           radius_km: 3,   description: "a vibrant city on the River Shannon", county: "limerick" },
  { slug: "waterford-city", name: "Waterford City",   query: "Waterford City",          radius_km: 3,   description: "Ireland's oldest city on the River Suir", county: "waterford" },
  { slug: "kilkenny-city",  name: "Kilkenny City",    query: "Kilkenny",                radius_km: 2,   description: "the medieval capital of Ireland", county: "kilkenny" },
  { slug: "drogheda",       name: "Drogheda",         query: "Drogheda, Louth",         radius_km: 2,   description: "a major town on the River Boyne in County Louth", county: "louth" },
  { slug: "dundalk",        name: "Dundalk",          query: "Dundalk, Louth",          radius_km: 2,   description: "the largest town in County Louth", county: "louth" },
  { slug: "navan",          name: "Navan",            query: "Navan, Meath",            radius_km: 2,   description: "the county town of Meath", county: "meath" },
  { slug: "naas",           name: "Naas",             query: "Naas, Kildare",           radius_km: 2,   description: "the county town of Kildare", county: "kildare" },
  { slug: "bray",           name: "Bray",             query: "Bray, Wicklow",           radius_km: 2,   description: "a seaside town at the foot of the Wicklow Mountains", county: "wicklow" },
];
```

- [ ] **Step 3: Add `D6W` to `DUBLIN_EIRCODE_AREAS`**

In the `DUBLIN_EIRCODE_AREAS` object, add `D6W: "Dublin 6W"` immediately after the `D06: "Dublin 6"` entry so the map reflects the 22 postcodes shown on the Dublin page. Final object:

```ts
export const DUBLIN_EIRCODE_AREAS: Record<string, string> = {
  D01: "Dublin 1", D02: "Dublin 2", D03: "Dublin 3", D04: "Dublin 4",
  D05: "Dublin 5", D06: "Dublin 6", D6W: "Dublin 6W", D07: "Dublin 7",
  D08: "Dublin 8", D09: "Dublin 9", D10: "Dublin 10", D11: "Dublin 11",
  D12: "Dublin 12", D13: "Dublin 13", D14: "Dublin 14", D15: "Dublin 15",
  D16: "Dublin 16", D17: "Dublin 17", D18: "Dublin 18", D20: "Dublin 20",
  D22: "Dublin 22", D24: "Dublin 24",
};
```

- [ ] **Step 4: Add `PROVINCES` and the three helper functions**

Append to the end of `areas.ts`:

```ts
// Provinces of the Republic of Ireland → county slugs (display order).
// Covers all 26 counties in COUNTIES.
export const PROVINCES: { name: string; counties: string[] }[] = [
  { name: "Leinster", counties: ["carlow", "dublin", "kildare", "kilkenny", "laois", "longford", "louth", "meath", "offaly", "westmeath", "wexford", "wicklow"] },
  { name: "Munster",  counties: ["clare", "cork", "kerry", "limerick", "tipperary", "waterford"] },
  { name: "Connacht", counties: ["galway", "leitrim", "mayo", "roscommon", "sligo"] },
  { name: "Ulster",   counties: ["cavan", "donegal", "monaghan"] },
];

// All AREAS whose parent county matches the given county slug.
export function areasForCounty(countySlug: string): AreaConfig[] {
  return AREAS.filter(a => a.county === countySlug);
}

// The province name a county slug belongs to (undefined if unknown).
export function provinceForCounty(countySlug: string): string | undefined {
  return PROVINCES.find(p => p.counties.includes(countySlug))?.name;
}

// The parent county slug for an area slug (undefined if unknown).
export function countyForArea(areaSlug: string): string | undefined {
  return AREAS.find(a => a.slug === areaSlug)?.county;
}
```

- [ ] **Step 5: Self-verify (no build available)**

Re-read the diff and confirm:
- `AreaConfig` has `county`; all 31 `AREAS` entries include a `county` value.
- The 11 new slugs are present and unique; no duplicate slugs across the array.
- `PROVINCES` counties are all lowercase and total exactly 26 across the four provinces (12 + 6 + 5 + 3), matching `COUNTIES` when slugified.
- `DUBLIN_EIRCODE_AREAS` has 22 keys including `D6W`.
- No syntax errors (matched braces, trailing commas consistent with file style).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/areas.ts
git commit -m "$(cat <<'EOF'
feat: place-relationship data model in areas.ts

Add county field to AreaConfig, 11 new Cork/Galway areas, D6W eircode,
PROVINCES map, and areasForCounty/provinceForCounty/countyForArea helpers.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Shared `Breadcrumbs` component

**Files:**
- Create: `frontend/src/components/Breadcrumbs.tsx`

**Interfaces:**
- Consumes: react-router-dom `Link`.
- Produces: `export default function Breadcrumbs({ items }: { items: Crumb[] })` where `interface Crumb { name: string; url: string }`. Renders "Home" + items; last item is plain text.

- [ ] **Step 1: Create the component**

Create `frontend/src/components/Breadcrumbs.tsx`:

```tsx
import { Link } from "react-router-dom";

export interface Crumb {
  name: string;
  url: string;
}

/**
 * Visible, clickable breadcrumb trail. Always prepends a "Home" crumb.
 * The final crumb renders as plain text (the current page). Feed this the
 * same array passed to usePageMeta's `breadcrumbs` arg so the visible trail
 * and the BreadcrumbList JSON-LD stay in sync.
 */
export default function Breadcrumbs({ items }: { items: Crumb[] }) {
  const trail: Crumb[] = [{ name: "Home", url: "/" }, ...items];
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol>
        {trail.map((crumb, i) => {
          const isLast = i === trail.length - 1;
          return (
            <li key={crumb.url}>
              {isLast ? (
                <span aria-current="page">{crumb.name}</span>
              ) : (
                <Link to={crumb.url}>{crumb.name}</Link>
              )}
              {!isLast && <span className="breadcrumb-sep" aria-hidden="true"> › </span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
```

- [ ] **Step 2: Add minimal styles**

Append to `frontend/src/index.css` (match existing formatting):

```css
.breadcrumbs { padding: 0.75rem 0 0; font-size: 0.85rem; }
.breadcrumbs ol { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; align-items: center; gap: 0.15rem; }
.breadcrumbs li { display: inline-flex; align-items: center; }
.breadcrumbs a { color: #1a3c5e; text-decoration: none; }
.breadcrumbs a:hover { text-decoration: underline; }
.breadcrumbs span[aria-current="page"] { color: #6b7280; }
.breadcrumb-sep { color: #9ca3af; }
```

- [ ] **Step 3: Self-verify**

Confirm: default export present, `Crumb` exported, `key` uses `crumb.url`, last item is a `<span aria-current>`, no unused imports.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Breadcrumbs.tsx frontend/src/index.css
git commit -m "$(cat <<'EOF'
feat: shared Breadcrumbs component

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `/areaguides` hub page + route

**Files:**
- Create: `frontend/src/pages/AreaGuidesPage.tsx`
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: `PROVINCES`, `COUNTIES`, `countySlug`, `countyFromSlug`, `AREAS`, `DUBLIN_EIRCODE_AREAS` from `../areas`; `hasCountyContent` from `../content/counties`; `Breadcrumbs` (Task 2); `usePageMeta`; `PageHeader`; `Footer`.
- Produces: default-exported `AreaGuidesPage`; new static route `/areaguides` (prerenders to `/areaguides/index.html`).

- [ ] **Step 1: Create the hub page**

Create `frontend/src/pages/AreaGuidesPage.tsx`:

```tsx
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  PROVINCES,
  countySlug,
  countyFromSlug,
  areasForCounty,
  AREAS,
  DUBLIN_EIRCODE_AREAS,
} from "../areas";
import { hasCountyContent } from "../content/counties";

export default function AreaGuidesPage() {
  const meta = usePageMeta(
    "Area Guides — Ireland Property Prices by County, Area & Postcode",
    "Browse HomeIQ's property price area guides: every Irish county, popular towns and suburbs, and all Dublin postcodes. Median prices, trends and recent sales from the Property Price Register.",
    [{ name: "Area Guides", url: "/areaguides" }]
  );

  // Counties that have at least one linkable area guide, for the areas block.
  const countiesWithAreas = PROVINCES
    .flatMap(p => p.counties)
    .filter(slug => areasForCounty(slug).length > 0);

  return (
    <>
      {meta}
      <PageHeader title="Property Price Area Guides" />
      <div className="content-page">
        <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }]} />

        <p className="content-intro">
          Explore Irish residential property prices by location. Every guide draws on
          Ireland's Property Price Register, with median and average prices, yearly trends
          and recent sales. Browse by county, jump to a popular town or suburb, or drill into
          a Dublin postcode.
        </p>

        {PROVINCES.map(province => (
          <section className="content-section" key={province.name}>
            <h2>{province.name}</h2>
            <div className="county-links">
              {province.counties.map(slug => {
                const name = countyFromSlug(slug) ?? slug;
                return (
                  <Link key={slug} to={`/county/${slug}`} className="county-link-btn">
                    County {name}
                    {hasCountyContent(slug) && (
                      <span className="guide-badge">Detailed guide</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </section>
        ))}

        <section className="content-section">
          <h2>Dublin Postcodes</h2>
          <p>Property prices for each Dublin postal district.</p>
          <div className="postcode-link-grid">
            {Object.entries(DUBLIN_EIRCODE_AREAS).map(([code, label]) => (
              <Link key={code} to={`/eircode/${code}`} className="postcode-link">
                <span className="postcode-badge">{code}</span> {label}
              </Link>
            ))}
          </div>
        </section>

        <section className="content-section">
          <h2>Popular Towns &amp; Suburbs</h2>
          {countiesWithAreas.map(slug => {
            const name = countyFromSlug(slug) ?? slug;
            return (
              <div key={slug} className="area-county-group">
                <h3>County {name}</h3>
                <div className="areas-grid">
                  {areasForCounty(slug).map(area => (
                    <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
                      <h3>{area.name}</h3>
                      <p>{area.description}</p>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
          <p className="table-note">
            {AREAS.length} area guides available and growing.
          </p>
        </section>

        <Footer />
      </div>
    </>
  );
}
```

- [ ] **Step 2: Add supporting styles**

Append to `frontend/src/index.css`:

```css
.guide-badge { display: inline-block; margin-left: 0.4rem; font-size: 0.7rem; font-weight: 600; color: #1a3c5e; background: #e8f0f7; padding: 0.1rem 0.4rem; border-radius: 0.25rem; }
.postcode-link-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.postcode-link { display: inline-flex; align-items: center; gap: 0.4rem; color: #1a3c5e; text-decoration: none; padding: 0.35rem 0.6rem; border: 1px solid #e5e7eb; border-radius: 0.375rem; }
.postcode-link:hover { background: #f8f9fa; }
.area-county-group { margin-bottom: 1.5rem; }
.area-county-group > h3 { margin: 0 0 0.5rem; color: #1a3c5e; }
```

- [ ] **Step 3: Register the route in `main.tsx`**

Add the import alongside the other page imports:

```tsx
import AreaGuidesPage from "./pages/AreaGuidesPage";
```

Add the route to the `routes` array, grouped with the static routes and BEFORE the dynamic `/area/:slug` / `/county/:slug` entries (place it right after the `{ path: "/valuation", ... }` line):

```tsx
  { path: "/areaguides", element: <AreaGuidesPage /> },
```

Do NOT touch the `/county/dublin` → `/county/:slug` ordering.

- [ ] **Step 4: Self-verify**

Confirm: `/areaguides` is a concrete path (no `:`), so `includedRoutes`'s `staticPaths` filter in `vite.config.ts` will include it automatically. All imports used, no `any`. County counts render for all 26 counties.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/AreaGuidesPage.tsx frontend/src/main.tsx frontend/src/index.css
git commit -m "$(cat <<'EOF'
feat: /areaguides hub page organised by province

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Link Dublin postcode badges + breadcrumbs + hub link

**Files:**
- Modify: `frontend/src/pages/DublinCountyPage.tsx`

**Interfaces:**
- Consumes: `Breadcrumbs` (Task 2). (`Link` already imported.)
- Produces: postcode badges now link to `/eircode/{postcode}`; visible breadcrumb trail; hub link.

- [ ] **Step 1: Import Breadcrumbs**

Add after the existing `Footer` import:

```tsx
import Breadcrumbs from "../components/Breadcrumbs";
```

- [ ] **Step 2: Render breadcrumbs**

Immediately inside `<div className="content-page">` (before `<p className="content-intro">`), add:

```tsx
<Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: "Dublin", url: "/county/dublin" }]} />
```

- [ ] **Step 3: Make each postcode badge a link**

In the table body (current lines 107-114), replace the badge cell so the postcode links to its eircode page. Change:

```tsx
<td><span className="postcode-badge">{row.postcode}</span></td>
```

to:

```tsx
<td>
  <Link to={`/eircode/${row.postcode}`} className="postcode-badge-link">
    <span className="postcode-badge">{row.postcode}</span>
  </Link>
</td>
```

- [ ] **Step 4: Add hub link to the "Search Dublin Properties" section**

In the final `<section className="content-section">` (the "Search Dublin Properties" one), after the existing `<p>...</p>`, add:

```tsx
<p>
  Browse <Link to="/areaguides">all area guides</Link> for other counties, towns and postcodes.
</p>
```

- [ ] **Step 5: Add badge-link style**

Append to `frontend/src/index.css`:

```css
.postcode-badge-link { text-decoration: none; }
```

- [ ] **Step 6: Self-verify**

Confirm every `row.postcode` (D01…D24 incl. D6W) has a matching `DUBLIN_EIRCODE_AREAS` key (from Task 1) so the eircode pages prerender. No unused imports.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/DublinCountyPage.tsx frontend/src/index.css
git commit -m "$(cat <<'EOF'
feat: link Dublin postcode badges to eircode pages + breadcrumbs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `AreaPage` — parent-county link, breadcrumbs, hub link

**Files:**
- Modify: `frontend/src/pages/AreaPage.tsx`

**Interfaces:**
- Consumes: `countyForArea`, `countyFromSlug`, `countySlug` from `../areas`; `Breadcrumbs`.
- Produces: area page links to its parent county and the hub; breadcrumb trail.

- [ ] **Step 1: Update imports**

Change the areas import (line 8) to add the helpers, and add the Breadcrumbs import:

```tsx
import { areaFromSlug, countyForArea, countyFromSlug } from "../areas";
import Breadcrumbs from "../components/Breadcrumbs";
```

- [ ] **Step 2: Compute the parent county inside the component**

After `const config = areaFromSlug(slug ?? "");` (line 18), add:

```tsx
const parentCountySlug = countyForArea(config?.slug ?? "");
const parentCountyName = parentCountySlug ? countyFromSlug(parentCountySlug) : undefined;
```

- [ ] **Step 3: Render breadcrumbs**

Immediately inside `<div className="content-page">` (before `<p className="content-intro">`), add a breadcrumb trail that includes the county crumb only when it resolves:

```tsx
<Breadcrumbs
  items={[
    { name: "Area Guides", url: "/areaguides" },
    ...(parentCountySlug && parentCountyName
      ? [{ name: `County ${parentCountyName}`, url: `/county/${parentCountySlug}` }]
      : []),
    { name: config.name, url: `/area/${config.slug}` },
  ]}
/>
```

- [ ] **Step 4: Add parent-county + hub links to the "Search" section**

In the final `<section className="content-section">` (the "Search {config.name} Properties" one), after the existing `<p>...</p>`, add:

```tsx
<p>
  {parentCountySlug && parentCountyName && (
    <>
      {config.name} is in{" "}
      <Link to={`/county/${parentCountySlug}`}>County {parentCountyName}</Link>. {" "}
    </>
  )}
  Browse <Link to="/areaguides">all area guides</Link>.
</p>
```

- [ ] **Step 5: Self-verify**

Confirm `parentCountySlug`/`parentCountyName` guards prevent rendering a broken county link for areas whose county isn't in `COUNTIES`. All new imports used.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/AreaPage.tsx
git commit -m "$(cat <<'EOF'
feat: area pages link to parent county and area-guides hub + breadcrumbs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: `EircodePage` — county link, sibling postcodes, breadcrumbs, hub link

**Files:**
- Modify: `frontend/src/pages/EircodePage.tsx`

**Interfaces:**
- Consumes: `DUBLIN_EIRCODE_AREAS` (already imported), `countySlug` from `../areas`; `Breadcrumbs`.
- Produces: county name links to `/county/{slug}`; sibling-postcode list; breadcrumb trail; hub link.

- [ ] **Step 1: Update imports**

Change the areas import (line 8) and add Breadcrumbs:

```tsx
import { DUBLIN_EIRCODE_AREAS, countySlug } from "../areas";
import Breadcrumbs from "../components/Breadcrumbs";
```

- [ ] **Step 2: Render breadcrumbs**

Immediately inside `<div className="content-page">` (before `<p className="content-intro">`), add:

```tsx
<Breadcrumbs
  items={[
    { name: "Area Guides", url: "/areaguides" },
    { name: "Dublin", url: "/county/dublin" },
    { name: friendlyName, url: `/eircode/${upperCode}` },
  ]}
/>
```

- [ ] **Step 3: Link the county name in the trends heading**

In the trends section (current line 89), replace the plain county text:

```tsx
<h2>Price Trends — {data.results[0]?.county ?? upperCode}</h2>
```

with a linked version when a county is known:

```tsx
<h2>
  Price Trends —{" "}
  {data.results[0]?.county ? (
    <Link to={`/county/${countySlug(data.results[0].county)}`}>
      {data.results[0].county}
    </Link>
  ) : (
    upperCode
  )}
</h2>
```

- [ ] **Step 4: Add sibling-postcode links + hub link to the "Search by Eircode" section**

In the final `<section className="content-section">` (the "Search by Eircode" one), after the existing `<p>...</p>`, add a list of the other Dublin postcodes and a hub link:

```tsx
<p>Other Dublin postcodes:</p>
<div className="postcode-link-grid">
  {Object.entries(DUBLIN_EIRCODE_AREAS)
    .filter(([code]) => code !== upperCode)
    .map(([code, label]) => (
      <Link key={code} to={`/eircode/${code}`} className="postcode-link">
        <span className="postcode-badge">{code}</span> {label}
      </Link>
    ))}
</div>
<p>
  Browse <Link to="/areaguides">all area guides</Link>.
</p>
```

(`.postcode-link-grid` / `.postcode-link` were added in Task 3.)

- [ ] **Step 5: Self-verify**

Confirm `countySlug` is applied to the API-returned county string (which is a display name like "Dublin"/"Cork"), producing a slug that matches `/county/:slug`. Note the sibling grid renders inside the `data &&` block, so it only shows once data loads — acceptable. No unused imports.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/EircodePage.tsx
git commit -m "$(cat <<'EOF'
feat: eircode pages link county, sibling postcodes, hub + breadcrumbs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Generic `CountyPage` — areas-in-county, nearby counties, breadcrumbs, hub link

**Files:**
- Modify: `frontend/src/pages/CountyPage.tsx`

**Interfaces:**
- Consumes: `countyFromSlug` (already imported), `countySlug`, `areasForCounty`, `provinceForCounty`, `PROVINCES` from `../areas`; `Breadcrumbs`.
- Produces: generic county pages link to their areas, province-sibling counties, and the hub; breadcrumb trail.

Note: this task only affects the generic branch (counties WITHOUT custom content). Cork/Galway/Dublin delegate to `CountyPageTemplate` (Task 8) / `DublinCountyPage` (Task 4).

- [ ] **Step 1: Update imports**

Change the areas import (line 9) and add Breadcrumbs:

```tsx
import { countyFromSlug, countySlug, areasForCounty, provinceForCounty, PROVINCES } from "../areas";
import Breadcrumbs from "../components/Breadcrumbs";
```

- [ ] **Step 2: Compute related places**

The custom-content early return happens at lines 30-32. In the generic branch, after `const meta = usePageMeta(...)` (ends line 70), add:

```tsx
const slugStr = slug ?? "";
const countyAreas = areasForCounty(slugStr);
const province = provinceForCounty(slugStr);
const siblingCountySlugs = province
  ? (PROVINCES.find(p => p.name === province)?.counties ?? []).filter(s => s !== slugStr)
  : [];
```

- [ ] **Step 3: Render breadcrumbs**

Immediately inside `<div className="content-page">` (before `<p className="content-intro">`), add:

```tsx
<Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: `County ${county}`, url: `/county/${slugStr}` }]} />
```

- [ ] **Step 4: Add "Areas in County X" section (only when non-empty)**

Inside the `{data && (...)}` block, immediately after the "Recent Sales" section (current lines 135-153), add:

```tsx
{countyAreas.length > 0 && (
  <section className="content-section">
    <h2>Areas in County {county}</h2>
    <div className="areas-grid">
      {countyAreas.map(area => (
        <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
          <h3>{area.name}</h3>
          <p>{area.description}</p>
        </Link>
      ))}
    </div>
  </section>
)}
```

- [ ] **Step 5: Add "Nearby Counties" section**

After the block from Step 4, add:

```tsx
{siblingCountySlugs.length > 0 && (
  <section className="content-section">
    <h2>Nearby Counties in {province}</h2>
    <div className="county-links">
      {siblingCountySlugs.map(sib => (
        <Link key={sib} to={`/county/${sib}`} className="county-link-btn">
          County {countyFromSlug(sib) ?? sib}
        </Link>
      ))}
    </div>
  </section>
)}
```

- [ ] **Step 6: Add hub link to the "Search" section**

In the "Search County {county} Properties" section, after the existing `<p>...</p>`, add:

```tsx
<p>
  Browse <Link to="/areaguides">all area guides</Link>.
</p>
```

- [ ] **Step 7: Self-verify**

Confirm the new sections are inside the `{data && (...)}` fragment (so they render with data). Confirm `slugStr` is defined before use in breadcrumbs (Step 2 runs before the `return`). `countySlug` import is used only if referenced — if Step 2/3 don't use `countySlug`, REMOVE it from the import to avoid an unused-import build error. (Review: Steps 2-6 use `areasForCounty`, `provinceForCounty`, `PROVINCES`, `countyFromSlug`, `slug`/`slugStr` — `countySlug` is NOT used, so do not import it.)

Corrected import for Step 1:

```tsx
import { countyFromSlug, areasForCounty, provinceForCounty, PROVINCES } from "../areas";
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/CountyPage.tsx
git commit -m "$(cat <<'EOF'
feat: generic county pages link areas, nearby counties, hub + breadcrumbs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: `CountyPageTemplate` — breadcrumbs + hub link

**Files:**
- Modify: `frontend/src/components/CountyPageTemplate.tsx`

**Interfaces:**
- Consumes: `Breadcrumbs`; `countySlug` from `../areas`.
- Produces: rich county pages (Cork/Galway) get breadcrumbs + hub link. (Dead `popularAreas` links are already fixed by Task 1 adding the areas.)

- [ ] **Step 1: Add imports**

After the existing imports, add:

```tsx
import Breadcrumbs from "./Breadcrumbs";
import { countySlug } from "../areas";
```

- [ ] **Step 2: Render breadcrumbs**

Immediately inside `<div className="content-page">` (before the hero-images block / `content.intro`), add:

```tsx
<Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: `County ${content.name}`, url: `/county/${countySlug(content.name)}` }]} />
```

- [ ] **Step 3: Add hub link to the "Search Properties" section**

In the "Search Properties in County {content.name}" section, after the existing `<p>...</p>`, add:

```tsx
<p>
  Browse <Link to="/areaguides">all area guides</Link>.
</p>
```

- [ ] **Step 4: Self-verify**

Confirm `countySlug(content.name)` yields the registry slug (e.g. "Cork" → "cork", matching the `/county/:slug` route). `Link` is already imported. No unused imports.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/CountyPageTemplate.tsx
git commit -m "$(cat <<'EOF'
feat: county template breadcrumbs + area-guides hub link

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Repoint WaffleMenu "Area Guides" to the hub

**Files:**
- Modify: `frontend/src/components/WaffleMenu.tsx`

**Interfaces:**
- Consumes: nothing new.
- Produces: the site-wide "Area Guides" menu item points to `/areaguides`.

- [ ] **Step 1: Change the href**

In the `ITEMS` array, the "Area Guides" entry (currently `href: "/county/dublin"`, label "Area Guides"). Change ONLY its `href`:

```tsx
    href: "/areaguides",
```

Leave the icon, label ("Area Guides"), and desc ("Price trends by county & area") unchanged.

- [ ] **Step 2: Self-verify**

Confirm exactly one `href` changed and the `key={item.href}` map still has unique keys (no other item uses `/areaguides`).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/WaffleMenu.tsx
git commit -m "$(cat <<'EOF'
feat: point WaffleMenu Area Guides at /areaguides hub

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Production test-suite reachability checks

**Files:**
- Modify: `tests/test_production_suite.py`

**Interfaces:**
- Consumes: existing `httpx.AsyncClient`, `TestResults`, `FRONTEND_URL`, `TIMEOUT` in the file.
- Produces: a new async test verifying `/areaguides` and a sample new area page return 200 (not a redirect/404), invoked from `run_all_tests`.

Note: These are post-deploy checks against the live site (the suite tests production URLs). They will only pass after the branch is merged & deployed; that's expected — the suite is run against production, and this documents the acceptance check. Follow the existing pattern of `test_frontend_loads` (lines 380-397) exactly for style (`results.add_pass`/`results.add_fail`, try/except).

- [ ] **Step 1: Add the test function**

Add after `test_frontend_api_calls` (after line 413):

```python
async def test_area_guides_navigation(client: httpx.AsyncClient, results: TestResults):
    """Test that the area-guides hub and a sample new area page are reachable."""
    checks = [
        ("/areaguides", "Area guides hub"),
        ("/area/douglas", "New area page (Douglas)"),
        ("/eircode/D6W", "Dublin 6W eircode page"),
    ]
    for path, label in checks:
        try:
            resp = await client.get(f"{FRONTEND_URL}{path}", timeout=TIMEOUT,
                                    follow_redirects=True)
            if resp.status_code == 200 and "HomeIQ" in resp.text:
                results.add_pass(label, f"{path} → 200")
            else:
                results.add_fail(label, f"{path} → {resp.status_code}")
        except Exception as e:
            results.add_fail(label, str(e))
```

- [ ] **Step 2: Invoke it from `run_all_tests`**

In the `Frontend:` block (lines 1159-1161), after `await test_frontend_api_calls(client, results)`, add:

```python
        await test_area_guides_navigation(client, results)
```

- [ ] **Step 3: Self-verify**

Confirm the function signature matches the other `client, results` tests, uses `add_pass`/`add_fail` (both exist on `TestResults`), and is invoked once. Do NOT run the suite (requires live deploy + network; production not yet updated).

- [ ] **Step 4: Commit**

```bash
git add tests/test_production_suite.py
git commit -m "$(cat <<'EOF'
test: verify /areaguides hub and new area/eircode pages are reachable

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- Fix #1 (broken Cork/Galway links) → Task 1 (adds the 11 areas). ✅
- Fix #2 (Dublin postcode badges) → Task 4. ✅
- Fix #3 (23 dead county pages) → Task 7. ✅
- Fix #4 (leaf pages up/sideways) → Tasks 5 (area) + 6 (eircode). ✅
- Fix #5 (no hub) → Task 3; WaffleMenu → Task 9. ✅
- Fix #6 (no breadcrumbs) → Task 2 (component) + Tasks 4-8 (usage). ✅
- Fix #7 (WaffleMenu) → Task 9. ✅
- `D6W` gap → Task 1 Step 3. ✅
- Hub organised by province → Task 3. ✅

**Type consistency:**
- `Crumb` interface (Task 2) matches the `items` arrays passed in Tasks 3-8.
- `AreaConfig.county` (Task 1) consumed by `countyForArea`/`areasForCounty` (Task 1) and used in Tasks 5/7.
- `provinceForCounty` returns a name; Task 7 looks the name back up in `PROVINCES` — consistent.
- `countySlug(displayName)` used in Tasks 6/8 to convert API/content county names to route slugs — matches `/county/:slug`.

**Placeholder scan:** none — all steps carry literal code.

**Known acceptable deferrals:** `dublin.ts` remains shadowed (out of scope, noted in spec). Task 10's checks only pass post-deploy (documented).
