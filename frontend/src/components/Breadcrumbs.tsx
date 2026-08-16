import { Link } from "react-router-dom";

export interface Crumb {
  name: string;
  url: string;
}

/**
 * Visible, clickable breadcrumb trail. Always prepends a "Home" crumb.
 * The final crumb renders as plain text (the current page). Feed this the
 * same array passed to usePageMeta's `breadcrumbs` arg so the visible trail
 * and the BreadcrumbList JSON-LD stay in sync.
 */
export default function Breadcrumbs({ items }: { items: Crumb[] }) {
  const trail: Crumb[] = [{ name: "Home", url: "/" }, ...items];
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol>
        {trail.map((crumb, i) => {
          const isLast = i === trail.length - 1;
          return (
            <li key={crumb.url}>
              {isLast ? (
                <span aria-current="page">{crumb.name}</span>
              ) : (
                <Link to={crumb.url}>{crumb.name}</Link>
              )}
              {!isLast && <span className="breadcrumb-sep" aria-hidden="true"> › </span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
