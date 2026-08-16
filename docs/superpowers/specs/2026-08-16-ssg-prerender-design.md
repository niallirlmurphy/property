# SSG Prerendering for homeiq.ie — Design

**Date:** 2026-08-16
**Status:** Approved (design), pending implementation plan
**Scope:** SEO recommendation #1 — get correct, per-page HTML to crawlers. Content fattening (#2) and crawl-hygiene fixes (#3) are explicitly out of scope.

## Problem

homeiq.ie is a pure client-side-rendered Vite + React Router SPA. `vercel.json` rewrites every route to a single empty `index.html` shell, and all titles, meta descriptions, canonicals, JSON-LD, and visible content are injected by JavaScript after load.

Verified ground truth (raw HTML before JS, fetched via curl):

- The homepage, `/county/dublin`, `/valuation`, `/eircode/D02`, and a blog post all return the **byte-for-byte identical 7,175-byte HTML shell**.
- Every URL carries the same `<title>` and `<meta name="description">`.
- Every URL carries `<link rel="canonical" href="https://homeiq.ie/">` — i.e. every page tells Google it is a duplicate of the homepage.
- Zero `<h1>` and no body content in the raw HTML.
- Unknown URLs return HTTP 200 (soft-404) — noted, but fixed under #3, not here.

Google does execute JS, but on a delayed, unreliable second wave, and the hardcoded homepage canonical actively suppresses indexing of the other routes. This is the single largest SEO constraint on the site.

## Goal

Every route serves real, per-page HTML at request time — correct `<title>`, `<meta description>`, self-referencing `<link rel="canonical">`, OG/Twitter tags, JSON-LD, and visible body content — **before** any JavaScript runs, while preserving the existing interactive SPA behaviour for users after hydration.

## Approach: vite-react-ssg (build-time SSG)

Chosen over headless-browser snapshotting (needs Chromium in CI, flaky on map pages, unmaintained tooling) and a Next/Astro migration (large, risky rewrite for what is fundamentally an HTML-delivery problem).

`vite-react-ssg` walks a `routes` array, renders each route through `renderToString` in Node at build time, and writes a real `.html` file per URL (`dist/county/dublin.html`, `dist/blog/<slug>.html`, …) with content baked in. In the browser those same files **hydrate** into the identical interactive SPA. Runtime behaviour (search, maps, live API data) is unchanged; crawlers now receive real HTML.

### Scope: all routes (map pages guarded)

Prerender every route, including the four interactive map/tool pages (`/`, `/polygon`, `/s1`, `/valuation`), so the homepage and tools also get correct static shells + meta. Leaflet is deferred to the client via a client-only boundary (see below).

## Components & changes

### 1. Entry point (`frontend/src/main.tsx`)

- Stop calling `ReactDOM.createRoot(...).render(...)`.
- Export a `routes` array (same paths and components as the current `<Routes>/<Route>` JSX) and call `ViteReactSSG(...)`.
- `vercel.json` unchanged: Vercel still serves `dist/`; the catch-all rewrite remains as the fallback for client-navigated deep links, but real prerendered files now take precedence.

### 2. Build script (`frontend/package.json`)

- `build`: `tsc && vite-react-ssg build` (was `tsc && vite build`).
- Add `vite-react-ssg` (and its peer, `@unhead/react`, if not transitive) to dependencies.
- Output dir unchanged.

### 3. Dynamic route expansion

Use vite-react-ssg's `includedRoutes` hook to expand parameterised routes from existing data:

- `/county/:slug` ← `COUNTIES` (26) from `frontend/src/areas.ts`
- `/area/:slug` ← `AREAS` (20) from `areas.ts`
- `/eircode/:code` ← `DUBLIN_EIRCODE_AREAS` (~22) from `areas.ts`
- `/blog/:slug` ← `BLOG_POSTS` from `BlogListPage.tsx`
- Static routes prerendered as-is.

### 4. Meta tags (`frontend/src/hooks/usePageMeta.ts`)

The current hook is a `useEffect` DOM-mutator — it runs only in a live browser and produces nothing during the server render pass. Convert it to emit into the server-rendered `<head>` via vite-react-ssg's `<Head>` component (`@unhead/react`), which serializes at build time **and** updates the document on the client.

- **Call sites do not change.** Every page keeps calling `usePageMeta(title, description, breadcrumbs, ogImage)`; only the hook internals change.
- Baked into each page's static HTML: per-page `<title>`, `<meta name="description">`, **self-referencing `<link rel="canonical">`** (computed from the route path, not `window.location`), per-page `og:title`/`og:description`/`og:url` + Twitter tags, and `BreadcrumbList` JSON-LD (currently browser-only).
- Static JSON-LD in `index.html` (WebApplication, Dataset, FAQPage) stays as-is.

### 5. Map/tool page guarding (`/`, `/polygon`, `/s1`, `/valuation`)

Leaflet / `react-leaflet` reference `window` at module-eval time and crash the Node render pass. Guard the **map widget**, not the page:

- Convert Leaflet-bearing subtrees to `React.lazy` (dynamic `import()`), rendered only after a mounted flag (`useState`/`useEffect`) flips true. Server: flag false → map subtree skipped, no `window` access; surrounding shell/headings/prose/meta render normally with a sized placeholder to avoid layout shift. Browser: flag flips on mount → map loads as today.
- Use vite-react-ssg's `ClientOnly` wrapper as the explicit boundary (or a tiny equivalent on version mismatch).
- `recharts` renders a placeholder server-side; gate it the same way only if the build surfaces `window`/ResizeObserver issues — driven by build output, not assumed.

## Error handling & failure mode

The risk concentrates entirely in the prerender pass. If any route throws during `renderToString`, `vite-react-ssg build` exits non-zero → **Vercel marks the deploy failed and keeps the current production build live.** Failure is safe-by-default; a broken build cannot ship silently.

## Verification

**Constraint (stated honestly):** there is no local Node in the working environment, so the build cannot be run locally. The **Vercel build is the verification oracle.** Work happens on branch `feat/ssg-prerender`; Vercel produces a **preview deployment** per push, verified before any merge to production.

Checklist against the preview URL (mirrors how the problem was diagnosed):

- `curl` raw HTML of `/`, `/county/dublin`, `/county/mayo` (thin fallback county), an `/area/...`, `/eircode/D02`, and a blog post. Assert each has a **distinct** `<title>`, its own `<meta description>`, a **self-referencing** `<link rel="canonical">`, and real body text / `<h1>` present before JS.
- Map pages return HTML (shell + heading + meta); map mounts in-browser and search works (drive via browser tool).
- No React hydration-mismatch errors on a content page and a map page.
- Spot-check interactive parity on the preview: a search, a trends chart, a valuation.

## Rollout

branch → push → Vercel preview → verify checklist → merge to main → re-verify production. Sitemap refresh and soft-404 fix (recommendation #3) are a separate follow-up.

## Out of scope

- Content fattening of thin county/area pages (recommendation #2).
- Sitemap regeneration, soft-404 fix, inconsistent-stats cleanup, robots.txt path fix (recommendation #3).
- Any change to backend, API, or interactive behaviour.
