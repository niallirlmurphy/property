import { useLocation } from "react-router-dom";
import { Head } from "vite-react-ssg";

const BASE_TITLE = "HomeIQ — Ireland Property Price Search";
const BASE_DESC  = "Search 785,000 residential property sales in Ireland (2010-2026). 85% geocoded with interactive maps, price trends, and Eircode lookup. Free property price data.";
const SITE = "https://homeiq.ie";
const DEFAULT_OG_IMAGE = "https://homeiq.ie/images/ppr-og-image.jpg";

interface BreadcrumbItem { name: string; url: string; }

export function usePageMeta(
  title?: string,
  description?: string,
  breadcrumbs?: BreadcrumbItem[],
  ogImage?: string,
  path?: string,        // optional explicit route path for canonical (SSR-safe)
): JSX.Element {
  const location = useLocation();
  const fullTitle = title ? `${title} | HomeIQ` : BASE_TITLE;
  const desc = description ?? BASE_DESC;
  const canonicalPath = path ?? location.pathname;
  const canonical = `${SITE}${canonicalPath}`;
  const image = ogImage ?? DEFAULT_OG_IMAGE;

  const breadcrumbJson =
    breadcrumbs && breadcrumbs.length > 0
      ? JSON.stringify({
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: [
            { "@type": "ListItem", position: 1, name: "Home", item: SITE },
            ...breadcrumbs.map((c, i) => ({
              "@type": "ListItem", position: i + 2, name: c.name, item: `${SITE}${c.url}`,
            })),
          ],
        })
      : null;

  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:url" content={canonical} />
      <meta property="og:image" content={image} />
      <meta name="twitter:image" content={image} />
      <link rel="canonical" href={canonical} />
      {breadcrumbJson && (
        <script type="application/ld+json">{breadcrumbJson}</script>
      )}
    </Head>
  );
}
