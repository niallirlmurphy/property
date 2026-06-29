import { Link } from "react-router-dom";
import WaffleMenu from "./WaffleMenu";
import ContactSidebar from "./ContactModals";

interface Props {
  title: string;
}

export default function PageHeader({ title }: Props) {
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
          <h1>{title}</h1>
        </Link>
        <WaffleMenu />
      </header>
      <ContactSidebar />
    </>
  );
}
