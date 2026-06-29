import { useState, useEffect, useRef } from "react";
import { Link, useLocation } from "react-router-dom";

const ITEMS = [
  {
    href: "/",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    label: "Property Search",
    desc: "Search sales by address or area",
  },
  {
    href: "/valuation",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
        <circle cx="17" cy="7" r="3" fill="currentColor"/>
      </svg>
    ),
    label: "Property Valuation",
    desc: "Free automated valuations",
  },
  {
    href: "/s1",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    ),
    label: "Single Property",
    desc: "View sales history for one address",
  },
  {
    href: "/county/dublin",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
      </svg>
    ),
    label: "Area Guides",
    desc: "Price trends by county & area",
  },
  {
    href: "/mortgage",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
    ),
    label: "Mortgage Calculator",
    desc: "Estimate your repayments",
  },
  {
    href: "/blog",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
        <line x1="9" y1="15" x2="15" y2="15"/><line x1="9" y1="11" x2="12" y2="11"/>
      </svg>
    ),
    label: "Blog",
    desc: "Property market insights & news",
  },
  {
    href: "/ber-ratings",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
    ),
    label: "BER Ratings",
    desc: "Energy ratings and retrofit trends",
  },
  {
    href: "/about",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    ),
    label: "About",
    desc: "Our data sources and mission",
  },
];

export default function WaffleMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const location = useLocation();

  // Close on route change
  useEffect(() => { setOpen(false); }, [location.pathname]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  return (
    <div className="waffle-wrap" ref={ref}>
      <button
        className={`waffle-btn${open ? " waffle-btn--open" : ""}`}
        onClick={() => setOpen(v => !v)}
        aria-label="Site navigation"
        aria-expanded={open}
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <rect x="3"  y="3"  width="4" height="4" rx="1"/>
          <rect x="10" y="3"  width="4" height="4" rx="1"/>
          <rect x="17" y="3"  width="4" height="4" rx="1"/>
          <rect x="3"  y="10" width="4" height="4" rx="1"/>
          <rect x="10" y="10" width="4" height="4" rx="1"/>
          <rect x="17" y="10" width="4" height="4" rx="1"/>
          <rect x="3"  y="17" width="4" height="4" rx="1"/>
          <rect x="10" y="17" width="4" height="4" rx="1"/>
          <rect x="17" y="17" width="4" height="4" rx="1"/>
        </svg>
      </button>

      {open && (
        <div className="waffle-dropdown" role="menu">
          <div className="waffle-grid">
            {ITEMS.map(item => (
              <Link
                key={item.href}
                to={item.href}
                className={`waffle-item${location.pathname === item.href ? " waffle-item--active" : ""}`}
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                <div className="waffle-item-icon">{item.icon}</div>
                <div className="waffle-item-label">{item.label}</div>
                <div className="waffle-item-desc">{item.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
