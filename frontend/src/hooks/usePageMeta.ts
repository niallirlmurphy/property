import { useEffect } from "react";

const BASE_TITLE = "HomeIQ — Ireland Property Price Search";
const BASE_DESC  = "Search every residential property sale in Ireland since 2010. Explore prices by address, Eircode, or area with interactive maps and price trend charts.";

export function usePageMeta(title?: string, description?: string) {
  useEffect(() => {
    document.title = title ? `${title} | HomeIQ` : BASE_TITLE;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute("content", description ?? BASE_DESC);

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute("content", document.title);
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) ogDesc.setAttribute("content", description ?? BASE_DESC);

    return () => {
      document.title = BASE_TITLE;
      if (metaDesc) metaDesc.setAttribute("content", BASE_DESC);
      if (ogTitle) ogTitle.setAttribute("content", BASE_TITLE);
      if (ogDesc) ogDesc.setAttribute("content", BASE_DESC);
    };
  }, [title, description]);
}
