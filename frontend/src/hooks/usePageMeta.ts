import { useEffect } from "react";

const BASE_TITLE = "HomeIQ — Ireland Property Price Search";
const BASE_DESC  = "Search 785,000 residential property sales in Ireland (2010-2026). 85% geocoded with interactive maps, price trends, and Eircode lookup. Free property price data.";

interface BreadcrumbItem {
  name: string;
  url: string;
}

export function usePageMeta(title?: string, description?: string, breadcrumbs?: BreadcrumbItem[], ogImage?: string) {
  useEffect(() => {
    document.title = title ? `${title} | HomeIQ` : BASE_TITLE;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute("content", description ?? BASE_DESC);

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute("content", document.title);
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) ogDesc.setAttribute("content", description ?? BASE_DESC);

    // Set og:image if provided
    if (ogImage) {
      const ogImageMeta = document.querySelector('meta[property="og:image"]');
      if (ogImageMeta) {
        ogImageMeta.setAttribute("content", ogImage);
      }
      const twitterImage = document.querySelector('meta[name="twitter:image"]');
      if (twitterImage) {
        twitterImage.setAttribute("content", ogImage);
      }
    }

    // Add breadcrumb schema if provided
    let breadcrumbScript: HTMLScriptElement | null = null;
    if (breadcrumbs && breadcrumbs.length > 0) {
      breadcrumbScript = document.createElement('script');
      breadcrumbScript.type = 'application/ld+json';
      breadcrumbScript.id = 'breadcrumb-schema';

      const schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
          {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "https://homeiq.ie"
          },
          ...breadcrumbs.map((crumb, idx) => ({
            "@type": "ListItem",
            "position": idx + 2,
            "name": crumb.name,
            "item": `https://homeiq.ie${crumb.url}`
          }))
        ]
      };

      breadcrumbScript.textContent = JSON.stringify(schema);
      document.head.appendChild(breadcrumbScript);
    }

    return () => {
      document.title = BASE_TITLE;
      if (metaDesc) metaDesc.setAttribute("content", BASE_DESC);
      if (ogTitle) ogTitle.setAttribute("content", BASE_TITLE);
      if (ogDesc) ogDesc.setAttribute("content", BASE_DESC);

      // Clean up breadcrumb schema
      if (breadcrumbScript) {
        document.head.removeChild(breadcrumbScript);
      }
    };
  }, [title, description, breadcrumbs, ogImage]);
}
