import type { ComponentType } from "react";
import { ViteReactSSG } from "vite-react-ssg";
import { Navigate } from "react-router-dom";
import { inject } from "@vercel/analytics";
import App from "./App";
import { areaLoader, countyLoader, eircodeLoader, streetLoader } from "./routeLoaders";
import ScrollToTopLayout from "./components/ScrollToTopLayout";
import "leaflet/dist/leaflet.css";
import "./index.css";
import "./styles/county-template.css";

// Pages other than the homepage load lazily, so each visit downloads only that
// page's code. vite-react-ssg resolves the matched lazy route before hydrating
// and adds a modulepreload for it to the prerendered HTML; it finds the chunk by
// scanning the lazy function's source, so keep a literal import("...") in each.
const page = (m: { default: ComponentType }) => ({ Component: m.default });

export const routes = [
  {
    // Pathless layout: scrolls to top on every navigation, renders route via <Outlet />
    element: <ScrollToTopLayout />,
    children: [
  { path: "/", element: <App /> },
  { path: "/s1", lazy: () => import("./pages/ExactSearchPage").then(page) },
  { path: "/polygon", lazy: () => import("./pages/PolygonSearchPage").then(page) },
  { path: "/heatmap", lazy: () => import("./pages/HeatmapPage").then(page) },
  { path: "/valuation", lazy: () => import("./pages/ValuationPage").then(page) },
  { path: "/areaguides", lazy: () => import("./pages/AreaGuidesPage").then(page) },
  { path: "/area/:slug", lazy: () => import("./pages/AreaPage").then(page), loader: areaLoader },
  { path: "/streets", lazy: () => import("./pages/StreetsIndexPage").then(page) },
  { path: "/street/:slug", lazy: () => import("./pages/StreetPage").then(page), loader: streetLoader },
  { path: "/county/dublin", lazy: () => import("./pages/DublinCountyPage").then(page) },
  { path: "/county/:slug", lazy: () => import("./pages/CountyPage").then(page), loader: countyLoader },
  { path: "/eircode/:code", lazy: () => import("./pages/EircodePage").then(page), loader: eircodeLoader },
  { path: "/mortgage", lazy: () => import("./pages/MortgagePage").then(page) },
  // Redirect the legacy plural path so old links/bookmarks keep working
  { path: "/mortgages", element: <Navigate to="/mortgage" replace /> },
  { path: "/energy", lazy: () => import("./pages/EnergyPage").then(page) },
  // Redirect legacy/menu BER path so old links keep working
  { path: "/ber-ratings", element: <Navigate to="/energy" replace /> },
  { path: "/about", lazy: () => import("./pages/AboutPage").then(page) },
  { path: "/contact", lazy: () => import("./pages/ContactPage").then(page) },
  { path: "/property-price-register", lazy: () => import("./pages/PropertyPriceRegisterPage").then(page) },
  { path: "/geocodes", lazy: () => import("./pages/ManualGeocodePage").then(page) },
  { path: "/camino", lazy: () => import("./pages/CaminoIndexPage").then(page) },
  { path: "/camino/french-way", lazy: () => import("./pages/FrenchWayPage").then(page) },
  { path: "/camino/spanish-way", lazy: () => import("./pages/SpanishWayPage").then(page) },
  { path: "/camino/before-you-go", lazy: () => import("./pages/BeforeYouGoPage").then(page) },
  { path: "/blog", lazy: () => import("./pages/BlogListPage").then(page) },
  { path: "/blog/:slug", lazy: () => import("./pages/BlogPostPage").then(page) },
  // Catch-all: a real "not found" page (prerendered as /404 → dist/404.html)
  { path: "*", lazy: () => import("./pages/NotFoundPage").then(page) },
    ],
  },
];

// NOTE: the SSG route list (which dynamic county/area/eircode/blog URLs get
// prerendered) is configured via `ssgOptions.includedRoutes` in vite.config.ts,
// not here — it is a build-time option, not a ViteReactSSG() runtime argument.
export const createRoot = ViteReactSSG(
  { routes },
  ({ isClient }) => {
    if (isClient) inject();
  }
);
