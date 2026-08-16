import { Link } from "react-router-dom";
import WaffleMenu from "./WaffleMenu";
import ContactSidebar from "./ContactModals";

interface Props {
  title: string;
  /**
   * When false, the header title is rendered as a plain <span> instead of an
   * <h1>. Use this on pages that render their own prominent in-content <h1>
   * (e.g. the area-guide pages) so the page has exactly one <h1>. Defaults to
   * true to preserve the header-as-h1 behaviour every other page relies on.
   */
  titleAsHeading?: boolean;
}

export default function PageHeader({ title, titleAsHeading = true }: Props) {
  return (
    <>
      <header className="app-header">
        <Link to="/" className="app-header-home" aria-label="Home">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
        </Link>
        <Link to="/" className="app-header-title">
          {titleAsHeading ? <h1>{title}</h1> : <span className="app-header-title-text">{title}</span>}
        </Link>
        <WaffleMenu />
      </header>
      <ContactSidebar />
    </>
  );
}
