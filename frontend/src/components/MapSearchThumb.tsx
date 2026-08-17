import { Link } from "react-router-dom";

interface MapSearchThumbProps {
  /** Search route to open when the map is clicked (e.g. `/?q=Clare&county=Clare`). */
  to: string;
  /** Accessible label / tooltip, e.g. "Search County Clare on the map". */
  label: string;
}

/**
 * A small clickable map of Ireland that links to the interactive map search
 * for a given location. Used at the end of county and area guide pages to make
 * jumping to the map search more obvious.
 */
export default function MapSearchThumb({ to, label }: MapSearchThumbProps) {
  return (
    <Link to={to} className="map-search-thumb" title={label} aria-label={label}>
      <img
        src="/images/ireland-map.svg"
        alt={label}
        width={120}
        height={120}
        loading="lazy"
      />
      <span>Open map search</span>
    </Link>
  );
}
