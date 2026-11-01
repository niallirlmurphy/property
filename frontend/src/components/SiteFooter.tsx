import { Link } from "react-router-dom";
import { SiteMark } from "./SiteHeader";
import "../styles/theme.css";
import "../styles/site-chrome.css";

declare const __BUILD_TIME__: string;

// The one site footer (components/Footer.tsx re-exports it, so every existing page uses it).
export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-in">
        <div>
          <div className="site-brand site-brand-foot"><SiteMark /><span>Home<b>IQ</b></span></div>
          <p>Every Irish home sale on the Property Price Register, mapped. Free, with no sign-up.</p>
        </div>
        <nav aria-label="Search tools">
          <h2>Search</h2>
          <Link to="/">Standard search</Link>
          <Link to="/valuation">Property valuation</Link>
          <Link to="/s1">Single property search</Link>
          <Link to="/mortgage">Mortgage calculator</Link>
        </nav>
        <nav aria-label="Places">
          <h2>Places</h2>
          <Link to="/areaguides">Area guides</Link>
          <Link to="/streets">Streets</Link>
          <Link to="/developments">Developments</Link>
          <Link to="/county/dublin">Dublin</Link>
          <Link to="/energy">BER ratings</Link>
        </nav>
        <nav aria-label="About HomeIQ">
          <h2>About</h2>
          <Link to="/about">About HomeIQ</Link>
          <Link to="/about#data-sources">Data sources</Link>
          <Link to="/property-price-register">Price Register guide</Link>
          <Link to="/blog">Blog</Link>
          <Link to="/contact">Contact</Link>
        </nav>
      </div>
      <p className="site-footer-note">Source: Property Price Register (PSRA).</p>
      <p className="site-footer-note site-build">Build: {__BUILD_TIME__}</p>
    </footer>
  );
}
