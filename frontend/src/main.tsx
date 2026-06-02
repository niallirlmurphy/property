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
import PropertyPriceRegisterPage from "./pages/PropertyPriceRegisterPage";
import ManualGeocodePage from "./pages/ManualGeocodePage";
import PolygonSearchPage from "./pages/PolygonSearchPage";
import CaminoPage from "./pages/CaminoPage";
import "leaflet/dist/leaflet.css";
import "./index.css";

inject();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/polygon" element={<PolygonSearchPage />} />
        <Route path="/area/:slug" element={<AreaPage />} />
        <Route path="/county/dublin" element={<DublinCountyPage />} />
        <Route path="/county/:slug" element={<CountyPage />} />
        <Route path="/eircode/:code" element={<EircodePage />} />
        <Route path="/mortgages" element={<MortgagePage />} />
        <Route path="/energy" element={<EnergyPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/property-price-register" element={<PropertyPriceRegisterPage />} />
        <Route path="/geocodes" element={<ManualGeocodePage />} />
        <Route path="/camino" element={<CaminoPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
