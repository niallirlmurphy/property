import ContactSidebar from "./ContactModals";
import SiteHeader from "./SiteHeader";

interface Props {
  title: string;
  /**
   * When false, no title band is rendered: the page shows its own prominent in-content
   * <h1> (e.g. the area-guide pages), so the page has exactly one <h1>. Defaults to
   * true: the title is rendered as the page <h1> in a band under the site header.
   */
  titleAsHeading?: boolean;
}

export default function PageHeader({ title, titleAsHeading = true }: Props) {
  return (
    <>
      <SiteHeader />
      {titleAsHeading && (
        <div className="page-title-band">
          <div className="page-title-band-in"><h1>{title}</h1></div>
        </div>
      )}
      <ContactSidebar />
    </>
  );
}
