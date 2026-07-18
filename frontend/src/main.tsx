import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
import CaminoIndexPage from "./pages/CaminoIndexPage";
import FrenchWayPage from "./pages/FrenchWayPage";
import SpanishWayPage from "./pages/SpanishWayPage";
import BeforeYouGoPage from "./pages/BeforeYouGoPage";
import BlogListPage from "./pages/BlogListPage";
import BlogPostPage from "./pages/BlogPostPage";
import "leaflet/dist/leaflet.css";
import "./index.css";

inject();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/s1" element={<ExactSearchPage />} />
        <Route path="/polygon" element={<PolygonSearchPage />} />
        <Route path="/valuation" element={<ValuationPage />} />
        <Route path="/area/:slug" element={<AreaPage />} />
        <Route path="/county/dublin" element={<DublinCountyPage />} />
        <Route path="/county/:slug" element={<CountyPage />} />
        <Route path="/eircode/:code" element={<EircodePage />} />
        <Route path="/mortgages" element={<MortgagePage />} />
        <Route path="/energy" element={<EnergyPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/property-price-register" element={<PropertyPriceRegisterPage />} />
        <Route path="/geocodes" element={<ManualGeocodePage />} />
        <Route path="/camino" element={<CaminoIndexPage />} />
        <Route path="/camino/french-way" element={<FrenchWayPage />} />
        <Route path="/camino/spanish-way" element={<SpanishWayPage />} />
        <Route path="/camino/before-you-go" element={<BeforeYouGoPage />} />
        <Route path="/blog" element={<BlogListPage />} />
        <Route path="/blog/:slug" element={<BlogPostPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
