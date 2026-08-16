import { Head } from "vite-react-ssg";

const BASE_TITLE = "HomeIQ — Ireland Property Price Search";
const BASE_DESC  = "Search 785,000 residential property sales in Ireland (2010-2026). 85% geocoded with interactive maps, price trends, and Eircode lookup. Free property price data.";
const SITE = "https://homeiq.ie";

interface BreadcrumbItem { name: string; url: string; }

export function usePageMeta(
  title?: string,
  description?: string,
  breadcrumbs?: BreadcrumbItem[],
  ogImage?: string,
  path?: string,        // optional explicit route path for canonical (SSR-safe)
): JSX.Element {
  const fullTitle = title ? `${title} | HomeIQ` : BASE_TITLE;
  const desc = description ?? BASE_DESC;
  // Canonical: prefer explicit path; fall back to window at runtime; default "/".
  const canonicalPath =
    path ?? (typeof window !== "undefined" ? window.location.pathname : "/");
  const canonical = `${SITE}${canonicalPath}`;

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
      {ogImage && <meta property="og:image" content={ogImage} />}
      {ogImage && <meta name="twitter:image" content={ogImage} />}
      <link rel="canonical" href={canonical} />
      {breadcrumbJson && (
        <script type="application/ld+json">{breadcrumbJson}</script>
      )}
    </Head>
  );
}
