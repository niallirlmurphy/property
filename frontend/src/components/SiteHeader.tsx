import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "../styles/theme.css";
import "../styles/site-chrome.css";

// The one site header: sticky, main action button, "More" dropdown on desktop and a
// full-screen style menu on mobile. Every page links to the same set of destinations.
export const NAV_PRIMARY = [
  { to: "/valuation", label: "Valuation" },
  { to: "/areaguides", label: "Area guides" },
  { to: "/mortgage", label: "Mortgage" },
  { to: "/blog", label: "Analysis" },
];

export const NAV_MORE = [
  { to: "/s1", label: "Single property" },
  { to: "/energy", label: "BER ratings" },
  { to: "/streets", label: "Streets" },
  { to: "/developments", label: "Developments" },
  { to: "/property-price-register", label: "Price Register guide" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" },
];

export function SiteMark() {
  return (
    <svg className="site-mark" viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#f2c230" />
      <path d="M7 16.5 16 8l9 8.5" fill="none" stroke="#10302b" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10.5 15v8.5h11V15" fill="none" stroke="#10302b" strokeWidth="2.6" strokeLinejoin="round" />
      <circle cx="16" cy="19.5" r="1.9" fill="#10302b" />
    </svg>
  );
}

export default function SiteHeader() {
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);
  const { pathname } = useLocation();

  // Close both menus on navigation
  useEffect(() => { setOpen(false); setMoreOpen(false); }, [pathname]);

  useEffect(() => {
    if (!open && !moreOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { setOpen(false); setMoreOpen(false); } };
    const onDown = (e: MouseEvent) => {
      if (moreOpen && moreRef.current && !moreRef.current.contains(e.target as Node)) setMoreOpen(false);
    };
    window.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onDown);
    return () => { window.removeEventListener("keydown", onKey); document.removeEventListener("mousedown", onDown); };
  }, [open, moreOpen]);

  return (
    <header className="site-header">
      <div className="site-header-in">
        <Link to="/" className="site-brand" aria-label="HomeIQ home">
          <SiteMark /><span>Home<b>IQ</b></span>
        </Link>
        <nav className="site-nav" aria-label="Main">
          {NAV_PRIMARY.map((n) => <Link key={n.to} to={n.to}>{n.label}</Link>)}
          <div className="site-more" ref={moreRef}>
            <button type="button" className="site-more-btn" aria-expanded={moreOpen} aria-controls="site-more-list" onClick={() => setMoreOpen((v) => !v)}>
              More <svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true"><path d="m2 4 4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
            {moreOpen && (
              <div id="site-more-list" className="site-more-list">
                {NAV_MORE.map((n) => <Link key={n.to} to={n.to}>{n.label}</Link>)}
              </div>
            )}
          </div>
        </nav>
        <Link to="/valuation" className="site-cta">Value my home</Link>
        <button
          type="button"
          className="site-burger"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="site-menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span /><span /><span />
        </button>
      </div>
      {open && (
        <nav id="site-menu" className="site-menu" aria-label="Menu">
          <Link to="/">Property search</Link>
          {NAV_PRIMARY.map((n) => <Link key={n.to} to={n.to}>{n.label}</Link>)}
          {NAV_MORE.map((n) => <Link key={n.to} to={n.to}>{n.label}</Link>)}
          <Link to="/valuation" className="site-cta site-cta-wide">Value my home</Link>
        </nav>
      )}
    </header>
  );
}
