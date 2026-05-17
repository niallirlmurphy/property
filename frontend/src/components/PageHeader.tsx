import { Link } from "react-router-dom";
import WaffleMenu from "./WaffleMenu";
import ContactSidebar from "./ContactModals";

interface Props {
  title: string;
}

export default function PageHeader({ title }: Props) {
  return (
    <>
      <header className="page-banner">
        <div className="page-banner-inner">
          <Link to="/" className="page-banner-home" aria-label="Home">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </Link>
          <Link to="/" className="page-banner-title">{title}</Link>
          <WaffleMenu />
        </div>
      </header>
      <ContactSidebar />
    </>
  );
}
