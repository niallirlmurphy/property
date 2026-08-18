import { useEffect } from "react";
import { useLocation, Outlet } from "react-router-dom";

/**
 * Pathless layout route that resets the window scroll position to the top on
 * every client-side navigation. Without this, React Router preserves the
 * previous page's scroll offset, so following a link near the bottom of a long
 * page (e.g. a street card on a county page) lands you partway down the next
 * page. Renders the matched route via <Outlet />.
 */
export default function ScrollToTopLayout() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return <Outlet />;
}
