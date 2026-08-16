# SSG Prerendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve real per-page HTML (title, description, self-referencing canonical, OG/Twitter, JSON-LD, body content) to crawlers for every route, before JS runs, without changing the interactive SPA behaviour after hydration.

**Architecture:** Adopt `vite-react-ssg` to prerender all React Router routes to static HTML at build time; the same files hydrate into the existing SPA in the browser. Meta moves from a browser-only `useEffect` DOM-mutator to `vite-react-ssg`'s built-in `<Head>` component (backed by `react-helmet-async`; serializes server-side + updates client-side). Leaflet map subtrees are extracted into child components and loaded via `React.lazy` behind `vite-react-ssg`'s exported `ClientOnly` boundary so the Node render pass never imports Leaflet.

**Tech Stack:** Vite 5, React 18, **react-router-dom 6 (downgraded from 7)**, vite-react-ssg 0.9.1, react-helmet-async (bundled with vite-react-ssg), Leaflet/react-leaflet, recharts. Deploy: Vercel (frontend), Railway (backend, untouched).

> **CRITICAL COMPATIBILITY NOTE (revised 2026-08-16 after Task 1 review):** `vite-react-ssg` (every published version, including latest 0.9.2) declares peer `react-router-dom: ^6.14.1` and its SSG renderer imports `react-router-dom/server.js` — a subpath that **react-router-dom v7 removed** (v7's `exports` map exposes only `.` and `./package.json`). The project was on `react-router-dom ^7.15.0`, which would crash the prerender for **every** route. Resolution (approved): **downgrade `react-router-dom` to `^6.30.4`.** Verified safe — the app uses only v6-compatible APIs (`Link`, `Navigate`, `useLocation`, `useNavigate`, `useParams`, `useSearchParams`; zero v7-only data-router APIs like `createBrowserRouter`/loaders/actions). Also: `vite-react-ssg` uses `react-helmet-async` internally (NOT `@unhead/react`, which additionally has no published 1.x); and it **exports its own `Head` and `ClientOnly`** — so no custom `ClientOnly.tsx` and no `@unhead` dependency are needed.

## Global Constraints

- **No local Node in the working environment.** The build cannot be run locally. The **Vercel preview deployment for branch `feat/ssg-prerender` is the verification oracle.** Each verification step = push, read the Vercel build log, then `curl`/browser-check the preview URL. A prerender crash fails the deploy and leaves production untouched — a broken build cannot ship silently.
- **All work on branch `feat/ssg-prerender`** (already created; design doc already committed there).
- **Interactive behaviour after hydration must be unchanged** — same components, same API calls, same UX.
- **Pinned dependency versions (exact):** `react-router-dom@^6.30.4`, `react-dom` stays `^18.3.1`, `react` stays `^18.3.1`, `vite` stays `^5.4.11`, and **`vite-react-ssg@0.9.1`** (exact pin — 0.9.2 requires Vite 6). Do NOT add `@unhead/react`. Do NOT hand-edit `package-lock.json`; Vercel's `npm install` resolves it.
- **`usePageMeta` return contract changes (unavoidable with the library switch):** `<Head>` must be *rendered* in the React tree, so the hook can no longer be a fire-and-forget `useEffect`. The hook is renamed-in-behaviour to return a JSX element (`<Head>…</Head>`), and every one of the **16 call sites** changes from a bare statement `usePageMeta(...)` to rendering the result: `const meta = usePageMeta(...)` then `{meta}` in the returned JSX (or `return <>{usePageMeta(...)}<PageBody/></>`). This is the one place the original "call sites don't change" promise cannot hold — it is a direct consequence of using vite-react-ssg's `<Head>` instead of `@unhead`'s imperative `useHead`. The signature (`title?, description?, breadcrumbs?, ogImage?`) is otherwise unchanged.
- **Scope is HTML delivery only.** Do NOT fatten content, regenerate the sitemap, fix the soft-404, or touch the backend — those are separate follow-ups.
- **Leaflet-importing pages (must be guarded):** `frontend/src/App.tsx` (`/`), `frontend/src/pages/PolygonSearchPage.tsx` (`/polygon`), `frontend/src/pages/ManualGeocodePage.tsx` (`/geocodes`). Pages `/valuation` and `/s1` do NOT import Leaflet and need no guarding.
- **Data sources for dynamic routes (exact export names):** `COUNTIES` (string[]), `AREAS` (AreaConfig[] with `.slug`), `DUBLIN_EIRCODE_AREAS` (Record<string,string>), `countySlug(county)` — all in `frontend/src/areas.ts`; `BLOG_POSTS` (with `.slug`) in `frontend/src/pages/BlogListPage.tsx`.

---

## File structure

- **Modify** `frontend/package.json` — add deps, change build script.
- **Modify** `frontend/src/main.tsx` — replace `createRoot` with `ViteReactSSG`, export `routes` + `includedRoutes`.
- **Modify** `frontend/src/hooks/usePageMeta.ts` — re-implement to return a `<Head>` element.
- **Modify** the 16 files that call `usePageMeta(...)` — render the returned element.
- **Create** `frontend/src/components/MapView.tsx` — extracted Leaflet map from App.tsx.
- **Create** `frontend/src/pages/PolygonMap.tsx` — extracted Leaflet map from PolygonSearchPage.tsx.
- **Create** `frontend/src/pages/ManualGeocodeMap.tsx` — extracted Leaflet map from ManualGeocodePage.tsx.
- **Modify** `frontend/src/App.tsx`, `PolygonSearchPage.tsx`, `ManualGeocodePage.tsx` — remove top-level Leaflet imports; lazy-load the extracted maps.

---

### Task 1: Install vite-react-ssg and switch the build entry (no route changes yet)

Get the SSG toolchain in and prove the app still builds/hydrates as an unchanged SPA *before* adding meta or map complexity. This isolates "does the toolchain work" from every later change.

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Produces: `export const createRoot = ViteReactSSG(...)` entry in `main.tsx`; a `routes` array (RouteRecord[]) consumed by later tasks; `vite-react-ssg` binary available to the build script.

- [ ] **Step 1: Set dependencies (verified against the npm registry)**

In `frontend/package.json` dependencies:
```json
"vite-react-ssg": "0.9.1",
"react-router-dom": "^6.30.4"
```
- `vite-react-ssg` is pinned to **exactly `0.9.1`** (no caret): 0.9.1 supports Vite 5, but 0.9.2 dropped to Vite 6+, and the project stays on Vite 5.
- `react-router-dom` is **downgraded** from `^7.15.0` to `^6.30.4`. This is mandatory: vite-react-ssg's SSG renderer imports `react-router-dom/server.js`, which v7 removed. The app uses only v6-compatible APIs, so this is behaviour-neutral.
- Do **NOT** add `@unhead/react` (no published 1.x exists, and vite-react-ssg uses react-helmet-async internally). If a prior commit added it, remove it here.
- Do not hand-edit `package-lock.json`; Vercel's `npm install` resolves it.

- [ ] **Step 2: Change the build script**

In `frontend/package.json`:
```json
"build": "tsc && vite-react-ssg build",
"dev": "vite"
```
(`dev` stays on plain `vite` — SSG only matters for the production build.)

- [ ] **Step 3: Convert `main.tsx` to a routes array + ViteReactSSG entry**

Replace the `ReactDOM.createRoot(...).render(<BrowserRouter><Routes>…)` block with a route-object array and the SSG entry. Keep every path/component identical to the current JSX (lines 34–59 of the current file):
```tsx
import { ViteReactSSG } from "vite-react-ssg";
import { Navigate } from "react-router-dom";
import { inject } from "@vercel/analytics";
import App from "./App";
// ...all existing page imports unchanged...
import "leaflet/dist/leaflet.css";
import "./index.css";

export const routes = [
  { path: "/", element: <App /> },
  { path: "/s1", element: <ExactSearchPage /> },
  { path: "/polygon", element: <PolygonSearchPage /> },
  { path: "/valuation", element: <ValuationPage /> },
  { path: "/area/:slug", element: <AreaPage /> },
  { path: "/county/dublin", element: <DublinCountyPage /> },
  { path: "/county/:slug", element: <CountyPage /> },
  { path: "/eircode/:code", element: <EircodePage /> },
  { path: "/mortgage", element: <MortgagePage /> },
  { path: "/mortgages", element: <Navigate to="/mortgage" replace /> },
  { path: "/energy", element: <EnergyPage /> },
  { path: "/ber-ratings", element: <Navigate to="/energy" replace /> },
  { path: "/about", element: <AboutPage /> },
  { path: "/contact", element: <ContactPage /> },
  { path: "/property-price-register", element: <PropertyPriceRegisterPage /> },
  { path: "/geocodes", element: <ManualGeocodePage /> },
  { path: "/camino", element: <CaminoIndexPage /> },
  { path: "/camino/french-way", element: <FrenchWayPage /> },
  { path: "/camino/spanish-way", element: <SpanishWayPage /> },
  { path: "/camino/before-you-go", element: <BeforeYouGoPage /> },
  { path: "/blog", element: <BlogListPage /> },
  { path: "/blog/:slug", element: <BlogPostPage /> },
  { path: "*", element: <Navigate to="/" replace /> },
];

export const createRoot = ViteReactSSG(
  { routes },
  ({ router, isClient }) => {
    if (isClient) inject();
  }
);
```
Note: `ViteReactSSG` supplies the router internally from `routes` — do NOT also wrap in `<BrowserRouter>` (double-router). Analytics `inject()` is gated to client only.

- [ ] **Step 4: Push and verify on Vercel preview**

```bash
git add frontend/package.json frontend/src/main.tsx
git commit -m "build: switch frontend to vite-react-ssg entry (SPA parity)"
git push -u origin feat/ssg-prerender
```
Then, against the Vercel **preview** URL for this branch:
- Confirm `npm install` succeeds (the react-router-dom v6 + vite-react-ssg 0.9.1 versions resolve cleanly — this was the original failure point).
- Confirm the Vercel build **succeeds** (read the build log; the SSG step must exit 0). At this point Leaflet pages may still error during prerender — if the build fails on `window is not defined` from App/Polygon/ManualGeocode, that is EXPECTED and is fixed in Tasks 3–5. If it fails there, proceed to Task 3 and treat Task 1 verification as "toolchain installed, SPA entry compiles"; confirm by checking the build reached the prerender stage.
- If the build completes, `curl -s <preview>/about` and confirm it returns HTML (About has no Leaflet, so it should prerender). Expect real `<h2>`/body text in the raw HTML.

- [ ] **Step 5: Commit** (already committed in Step 4).

---

### Task 2: Re-implement `usePageMeta` to return a `<Head>` element so meta serializes server-side

This is the task that actually delivers the SEO payload. Convert the hook from a `useEffect` DOM-mutator into one that returns a `<Head>` element (vite-react-ssg's export, backed by react-helmet-async). Because `<Head>` must be *rendered* in the tree, every call site changes to render the returned element — 16 files. No head provider needs wiring: vite-react-ssg mounts the `HelmetProvider` itself.

**Files:**
- Modify: `frontend/src/hooks/usePageMeta.ts`
- Modify: all 16 files calling `usePageMeta(...)` (render the returned element).

**Interfaces:**
- Consumes: `routes` entry from Task 1.
- Produces: `usePageMeta(title?, description?, breadcrumbs?, ogImage?, path?): JSX.Element` — returns a `<Head>` element. Callers must render it.

> **API facts (verified from vite-react-ssg 0.9.1 type declarations):** `import { Head } from "vite-react-ssg"`. `Head` is `react-helmet-async`'s Helmet — it takes **JSX children**, e.g. `<Head><title>…</title><meta name="description" content="…"/></Head>`, NOT a config object. There is no `useHead`. `HelmetProvider` is mounted internally by vite-react-ssg, so no provider wiring is needed in `main.tsx`.

- [ ] **Step 1: Rewrite the hook to return a `<Head>`**

Rewrite `usePageMeta.ts`:
```tsx
import { Head } from "vite-react-ssg";

const BASE_TITLE = "HomeIQ — Ireland Property Price Search";
const BASE_DESC  = "Search 785,000 residential property sales in Ireland (2010-2026). 85% geocoded with interactive maps, price trends, and Eircode lookup. Free property price data.";
const SITE = "https://homeiq.ie";

interface BreadcrumbItem { name: string; url: string; }

export function usePageMeta(
  title?: string,
  description?: string,
  breadcrumbs?: BreadcrumbItem[],
  ogImage?: string,
  path?: string,        // optional explicit route path for canonical (SSR-safe)
): JSX.Element {
  const fullTitle = title ? `${title} | HomeIQ` : BASE_TITLE;
  const desc = description ?? BASE_DESC;
  // Canonical: prefer explicit path; fall back to window at runtime; default "/".
  const canonicalPath =
    path ?? (typeof window !== "undefined" ? window.location.pathname : "/");
  const canonical = `${SITE}${canonicalPath}`;

  const breadcrumbJson =
    breadcrumbs && breadcrumbs.length > 0
      ? JSON.stringify({
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: [
            { "@type": "ListItem", position: 1, name: "Home", item: SITE },
            ...breadcrumbs.map((c, i) => ({
              "@type": "ListItem", position: i + 2, name: c.name, item: `${SITE}${c.url}`,
            })),
          ],
        })
      : null;

  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:url" content={canonical} />
      {ogImage && <meta property="og:image" content={ogImage} />}
      {ogImage && <meta name="twitter:image" content={ogImage} />}
      <link rel="canonical" href={canonical} />
      {breadcrumbJson && (
        <script type="application/ld+json">{breadcrumbJson}</script>
      )}
    </Head>
  );
}
```
Notes: the file becomes `.tsx` is NOT required — a `.ts` file can hold JSX only if the project's tsconfig allows it; to be safe, **rename the file to `usePageMeta.tsx`** (JSX in a `.ts` file fails `tsc`). Update the import extension nowhere else — TS import paths are extensionless, so call sites' `import { usePageMeta } from "../hooks/usePageMeta"` keep working after the rename. react-helmet-async dedupes by tag, so the old manual cleanup is unnecessary; when a page unmounts, Helmet restores prior head state automatically.

- [ ] **Step 2: Render the returned element at all 16 call sites**

Each call site currently invokes the hook as a bare statement. Change each to render the result. The 16 files (find them with `grep -rl "usePageMeta(" frontend/src --include="*.tsx"`) are page components; for each:

Pattern A — hook result stored then rendered (preferred, works for multi-return components):
```tsx
export default function AboutPage() {
  const meta = usePageMeta("About HomeIQ", "…");
  return (
    <>
      {meta}
      {/* existing page JSX unchanged */}
    </>
  );
}
```
Pattern B — inline when the component already returns a single fragment/root:
```tsx
return (
  <>
    {usePageMeta("About HomeIQ", "…")}
    {/* existing JSX */}
  </>
);
```
Rules for this mechanical pass:
- Do NOT change the arguments passed to `usePageMeta` at any call site — only render its return value.
- If a component returns early (e.g. loading/error branches) and you want meta on those too, place `{meta}` in each returned branch; otherwise placing it in the main return is sufficient for SEO (crawlers get the resolved page).
- Preserve each file's existing structure; wrap in a `<>…</>` fragment only if there isn't already a single root to attach `{meta}` to.
- `main.tsx` needs NO head-provider change (vite-react-ssg mounts HelmetProvider itself).

- [ ] **Step 3: Push and verify per-page meta on Vercel preview**

```bash
git add frontend/src/hooks/usePageMeta.tsx frontend/src/**/*.tsx
git rm frontend/src/hooks/usePageMeta.ts   # if the rename left the old file
git commit -m "feat: emit per-page meta via vite-react-ssg Head so it serializes into static HTML"
git push
```
Against the preview URL, `curl -s` these and assert **distinct** values in the RAW HTML (before JS):
- `/about` → title contains "About"; canonical `href="https://homeiq.ie/about"`.
- `/property-price-register` → its own title + description; self-referencing canonical.
- `/blog/does-living-near-a-good-school-add-value` → post title; canonical to that path.
Failure signal to watch: canonical still `https://homeiq.ie/` on a sub-page, or meta missing entirely from raw HTML → the `<Head>` element isn't being rendered at that call site; fix Step 2 for that page.
(Leaflet pages may still fail the build here; that's Tasks 3–5.)

---

### Task 3: Extract App.tsx's Leaflet map into a lazy, client-only child

App.tsx (`/`) imports `react-leaflet` + `leaflet` and runs `L.Icon`/`L.Marker.prototype` mutations at module top level (lines ~3, 19–26 of current file). Static import = crash on server. Extract the map subtree into its own module and lazy-load it so the Node pass never imports Leaflet.

**Files:**
- Create: `frontend/src/components/MapView.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `ClientOnly` from `vite-react-ssg` (library export — no custom component needed).
- Produces: `MapView` default export receiving the same props App currently passes to its inline `<MapContainer>` subtree.

> **API fact (verified from vite-react-ssg 0.9.1 types):** `import { ClientOnly } from "vite-react-ssg"`. Its signature is exactly `ClientOnly({ children, fallback }: { children?: () => React.ReactNode; fallback?: React.ReactNode })` — `children` is a **function** (called only after mount, so the Leaflet subtree is never constructed on the server). No custom `ClientOnly.tsx` is written; use the library's.

- [ ] **Step 1: Extract the map into `MapView.tsx`**

Move the entire `react-leaflet` / `leaflet` import block and the `<MapContainer>…</MapContainer>` JSX (and the module-level `L.Icon.Default`/marker setup, lines ~19–26) out of `App.tsx` into `frontend/src/components/MapView.tsx` as a default-exported component. Define a props interface for every value the map subtree currently reads from App's scope (center, zoom, markers/results, selected handlers, circle radius, etc. — copy the exact prop set from the current inline usage). No behaviour change; pure move.

- [ ] **Step 2: Lazy-load MapView in App.tsx behind ClientOnly**

In `App.tsx`, remove all `leaflet`/`react-leaflet` imports. Add:
```tsx
import { lazy, Suspense } from "react";
import { ClientOnly } from "vite-react-ssg";
const MapView = lazy(() => import("./components/MapView"));
```
Replace the old inline `<MapContainer>…</MapContainer>` with:
```tsx
<ClientOnly fallback={<div style={{ width: "100%", height: "100%", background: "#eef2f6" }} aria-hidden="true" />}>
  {() => (
    <Suspense fallback={<div style={{ width: "100%", height: "100%", background: "#eef2f6" }} />}>
      <MapView {/* …the exact props extracted in Step 1… */} />
    </Suspense>
  )}
</ClientOnly>
```
The fallback is a same-size box to avoid layout shift.

- [ ] **Step 3: Push and verify homepage prerenders + map still works**

```bash
git add frontend/src/components/MapView.tsx frontend/src/App.tsx
git commit -m "feat: lazy client-only map on homepage so / prerenders"
git push
```
Against the preview:
- Vercel build succeeds (no `window is not defined` from `/`).
- `curl -s <preview>/` → raw HTML contains the homepage `<h1>` and the correct title/canonical (`https://homeiq.ie/`), NOT just an empty shell.
- Load `<preview>/` in the browser tool → the Leaflet map renders and a search returns results (interactive parity).

---

### Task 4: Guard PolygonSearchPage's map the same way

Same pattern as Task 3 for `/polygon`.

**Files:**
- Create: `frontend/src/pages/PolygonMap.tsx`
- Modify: `frontend/src/pages/PolygonSearchPage.tsx`

**Interfaces:**
- Consumes: `ClientOnly` from `vite-react-ssg` (library export).
- Produces: `PolygonMap` default export (extracted Leaflet + leaflet-draw subtree with a props interface mirroring current inline usage).

- [ ] **Step 1: Extract the map into `PolygonMap.tsx`**

Move the `react-leaflet`, `leaflet`, `leaflet-draw`, and the two Leaflet CSS/`"leaflet-draw"` side-effect imports (lines 2–6 of current file) plus the `<MapContainer>` drawing-tools subtree into `frontend/src/pages/PolygonMap.tsx` (default export). Props interface = every value the map reads from the page (draw handlers, results, setters). Pure move.

- [ ] **Step 2: Lazy-load behind ClientOnly in PolygonSearchPage.tsx**

Remove Leaflet imports from `PolygonSearchPage.tsx`. Add `import { lazy, Suspense } from "react";`, `import { ClientOnly } from "vite-react-ssg";`, and `const PolygonMap = lazy(() => import("./PolygonMap"));`. Replace the inline map with the same `ClientOnly` + `Suspense` wrapper shape as Task 3 Step 2, passing the extracted props, with a same-size grey fallback box.

- [ ] **Step 3: Push and verify**

```bash
git add frontend/src/pages/PolygonMap.tsx frontend/src/pages/PolygonSearchPage.tsx
git commit -m "feat: lazy client-only map on /polygon so it prerenders"
git push
```
Preview: build succeeds; `curl -s <preview>/polygon` returns the page shell + heading in raw HTML; in the browser the draw tools work and a polygon search returns results.

---

### Task 5: Guard ManualGeocodePage's map (admin route)

Same pattern for `/geocodes`. Lower SEO value (admin), but it imports Leaflet at module top level so it MUST be guarded or it crashes the whole prerender build.

**Files:**
- Create: `frontend/src/pages/ManualGeocodeMap.tsx`
- Modify: `frontend/src/pages/ManualGeocodePage.tsx`

**Interfaces:**
- Consumes: `ClientOnly` from `vite-react-ssg` (library export).
- Produces: `ManualGeocodeMap` default export.

- [ ] **Step 1: Extract the map into `ManualGeocodeMap.tsx`**

Move `react-leaflet`/`leaflet`/CSS imports (lines 3–4, 8 of current file) and the `<MapContainer>` (with `useMapEvents`/`useMap` click-to-place subtree) into `frontend/src/pages/ManualGeocodeMap.tsx` (default export) with a props interface mirroring current usage. Pure move.

- [ ] **Step 2: Lazy-load behind ClientOnly in ManualGeocodePage.tsx**

Remove Leaflet imports; add `import { lazy, Suspense } from "react";`, `import { ClientOnly } from "vite-react-ssg";`, and `const ManualGeocodeMap = lazy(() => import("./ManualGeocodeMap"));`; wrap as in Task 3 Step 2.

- [ ] **Step 3: Push and verify full build prerenders every route**

```bash
git add frontend/src/pages/ManualGeocodeMap.tsx frontend/src/pages/ManualGeocodePage.tsx
git commit -m "feat: lazy client-only map on /geocodes so full SSG build succeeds"
git push
```
Preview: **build succeeds with no `window` errors on any route** (all three Leaflet pages now guarded). `curl -s <preview>/geocodes` returns HTML.

---

### Task 6: Prerender the dynamic routes (counties, areas, eircodes, blog)

Until now only static routes emit files; the `:slug`/`:code` routes need explicit URL lists. Feed vite-react-ssg's `includedRoutes` from existing data.

**Files:**
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: `COUNTIES`, `AREAS`, `DUBLIN_EIRCODE_AREAS`, `countySlug` from `areas.ts`; `BLOG_POSTS` from `BlogListPage.tsx`.

- [ ] **Step 1: Add `includedRoutes` to the ViteReactSSG options**

```tsx
import { COUNTIES, AREAS, DUBLIN_EIRCODE_AREAS, countySlug } from "./areas";
import { BLOG_POSTS } from "./pages/BlogListPage";

export const createRoot = ViteReactSSG(
  { routes },
  ({ isClient }) => { if (isClient) inject(); },
  {
    async includedRoutes(paths) {
      // Drop the dynamic templates and the catch-all; add concrete URLs.
      const staticPaths = paths.filter(
        p => !p.includes(":") && p !== "*"
      );
      const counties = COUNTIES
        .filter(c => c.toLowerCase() !== "dublin")   // /county/dublin is its own static-style route
        .map(c => `/county/${countySlug(c)}`);
      const areas = AREAS.map(a => `/area/${a.slug}`);
      const eircodes = Object.keys(DUBLIN_EIRCODE_AREAS).map(k => `/eircode/${k}`);
      const posts = BLOG_POSTS.map(p => `/blog/${p.slug}`);
      return [...staticPaths, ...counties, ...areas, ...eircodes, ...posts];
    },
  }
);
```
Note: confirm the exact `includedRoutes` signature/position against the installed vite-react-ssg version (third arg vs option key). Adjust placement, not logic.

- [ ] **Step 2: Push and verify dynamic pages emit distinct HTML**

```bash
git add frontend/src/main.tsx
git commit -m "feat: prerender county/area/eircode/blog routes from existing data"
git push
```
Against the preview, `curl -s` and assert distinct raw-HTML title + self-referencing canonical + body content for:
- `/county/mayo` (thin fallback county — proves the generic template prerenders)
- `/county/dublin` (dedicated page)
- `/area/<a real slug from AREAS>`
- `/eircode/D02`
- a blog post
Also confirm the Vercel build log lists the expected number of prerendered pages (~static + 25 counties + 20 areas + ~22 eircodes + 7 posts).

---

### Task 7: Final production verification & merge

**Files:** none (verification + merge only).

- [ ] **Step 1: Full preview checklist (mirrors the diagnosis)**

Against the preview URL, confirm ALL of:
- Raw HTML of `/`, `/county/dublin`, `/county/mayo`, an `/area/...`, `/eircode/D02`, a blog post each have a **distinct** `<title>`, own `<meta name="description">`, **self-referencing** `<link rel="canonical">`, and real `<h1>`/body text before JS. (Compare byte sizes — they must NOT all be identical 7,175-byte shells.)
- Map pages (`/`, `/polygon`) render the map in-browser and search/draw works.
- No React hydration-mismatch errors in the browser console on one content page and one map page.
- Interactive spot-check: a homepage search, a trends chart, a valuation on `/valuation`.

- [ ] **Step 2: Merge to main and re-verify production**

```bash
git checkout main
git merge --no-ff feat/ssg-prerender -m "Merge: SSG prerendering for per-page crawlable HTML"
git push origin main
```
After Vercel deploys production, re-run the Step 1 curl assertions against `https://homeiq.ie/...`. Confirm `/county/dublin` and a blog post now return distinct HTML with self-referencing canonicals (the original bug is gone).

- [ ] **Step 3: Report outcome**

Summarise: which routes prerender, verified distinct meta/canonical, interactive parity confirmed. Note that sitemap refresh + soft-404 (recommendation #3) remain a separate follow-up.

---

## Self-review notes

- **Spec coverage:** entry switch (Task 1) ✓; meta serialization + self-referencing canonical (Task 2) ✓; all-routes scope with map guarding (Tasks 3–5) ✓; dynamic route expansion from areas.ts/BLOG_POSTS (Task 6) ✓; Vercel-preview verification oracle + no-local-Node constraint (Global Constraints + every verify step) ✓; safe failure mode / branch+preview rollout (Tasks 1–7) ✓; out-of-scope items excluded ✓.
- **Reality correction vs spec:** spec listed `/valuation` and `/s1` among map pages; verified they do NOT import Leaflet, so only `/`, `/polygon`, `/geocodes` are guarded. Documented in Global Constraints.
- **Compatibility revision (2026-08-16, after Task 1 review):** the code review caught — and controller independently confirmed against the npm registry and vite-react-ssg's published type declarations — that vite-react-ssg is incompatible with react-router-dom v7 (removed `/server.js` subpath), `@unhead/react` has no 1.x, and vite-react-ssg ships its own `Head`/`ClientOnly` (react-helmet-async). Resolution (user-approved): downgrade react-router-dom to `^6.30.4`, pin vite-react-ssg `0.9.1`, drop `@unhead/react`, use the library's `Head`/`ClientOnly`. Consequence: `usePageMeta` now returns a `<Head>` element and its 16 call sites must render it (documented in Global Constraints + Task 2).
- **No-test-loop honesty:** there is no local runtime, so tasks use build-log + curl/browser assertions as the test, not runnable unit tests. This is stated, not hidden.
- **Type/name consistency:** `ClientOnly` is vite-react-ssg's export (`{ children: () => ReactNode, fallback }` — verified from types), used in Tasks 3–5; `Head` is vite-react-ssg's export used in Task 2; `usePageMeta` arg signature preserved, return type changed to `JSX.Element`; `includedRoutes` is the 3rd arg to `ViteReactSSG` with signature `(paths, routes) => string[]` (verified from types); data export names verified against source.
