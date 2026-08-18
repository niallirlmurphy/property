import { ViteReactSSG } from "vite-react-ssg";
import { Navigate } from "react-router-dom";
import { inject } from "@vercel/analytics";
import App from "./App";
import AreaPage from "./pages/AreaPage";
import CountyPage from "./pages/CountyPage";
import DublinCountyPage from "./pages/DublinCountyPage";
import EircodePage from "./pages/EircodePage";
import MortgagePage from "./pages/MortgagePage";
import EnergyPage from "./pages/EnergyPage";
import AboutPage from "./pages/AboutPage";
import ContactPage from "./pages/ContactPage";
import PropertyPriceRegisterPage from "./pages/PropertyPriceRegisterPage";
import ManualGeocodePage from "./pages/ManualGeocodePage";
import PolygonSearchPage from "./pages/PolygonSearchPage";
import ExactSearchPage from "./pages/ExactSearchPage";
import ValuationPage from "./pages/ValuationPage";
import AreaGuidesPage from "./pages/AreaGuidesPage";
import CaminoIndexPage from "./pages/CaminoIndexPage";
import FrenchWayPage from "./pages/FrenchWayPage";
import SpanishWayPage from "./pages/SpanishWayPage";
import BeforeYouGoPage from "./pages/BeforeYouGoPage";
import BlogListPage from "./pages/BlogListPage";
import BlogPostPage from "./pages/BlogPostPage";
import StreetPage from "./pages/StreetPage";
import StreetsIndexPage from "./pages/StreetsIndexPage";
import ScrollToTopLayout from "./components/ScrollToTopLayout";
import "leaflet/dist/leaflet.css";
import "./index.css";
import "./styles/county-template.css";

export const routes = [
  {
    // Pathless layout: scrolls to top on every navigation, renders route via <Outlet />
    element: <ScrollToTopLayout />,
    children: [
  { path: "/", element: <App /> },
  { path: "/s1", element: <ExactSearchPage /> },
  { path: "/polygon", element: <PolygonSearchPage /> },
  { path: "/valuation", element: <ValuationPage /> },
  { path: "/areaguides", element: <AreaGuidesPage /> },
  { path: "/area/:slug", element: <AreaPage /> },
  { path: "/streets", element: <StreetsIndexPage /> },
  { path: "/street/:slug", element: <StreetPage /> },
  { path: "/county/dublin", element: <DublinCountyPage /> },
  { path: "/county/:slug", element: <CountyPage /> },
  { path: "/eircode/:code", element: <EircodePage /> },
  { path: "/mortgage", element: <MortgagePage /> },
  // Redirect the legacy plural path so old links/bookmarks keep working
  { path: "/mortgages", element: <Navigate to="/mortgage" replace /> },
  { path: "/energy", element: <EnergyPage /> },
  // Redirect legacy/menu BER path so old links keep working
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
  // Catch-all: send unknown paths home instead of rendering a blank page
  { path: "*", element: <Navigate to="/" replace /> },
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
