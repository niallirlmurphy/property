// Writes dist/spa.html: the built index.html with the homepage's prerendered
// content and page-specific head tags removed. Vercel rewrites routes that have
// no prerendered file (non-Dublin /eircode/:code, scheduled /blog/:slug) to it.
// Without data-server-rendered, vite-react-ssg renders instead of hydrating, so
// those pages no longer fail hydration against the homepage's HTML.
import { readFileSync, writeFileSync } from "node:fs";

const src = new URL("../dist/index.html", import.meta.url);
let html = readFileSync(src, "utf8");

function replace(pattern, replacement, what) {
  const next = html.replace(pattern, replacement);
  if (next === html) throw new Error(`spa-shell: couldn't find ${what} in dist/index.html`);
  html = next;
}

// Homepage title/description/canonical/og tags (Helmet marks them data-rh);
// the rendered page sets its own.
replace(/<title data-rh="true">[^<]*<\/title>/, "<title>HomeIQ</title>", "the Helmet <title>");
replace(/\s*<(meta|link) data-rh="true"[^>]*>/g, "", "Helmet meta/link tags");
// Prerendered homepage markup plus its router hydration data, which sit inside #root.
replace(
  /<div id="root" data-server-rendered="true">[\s\S]*?<\/div>(\s*<script>window\.__VITE_REACT_SSG_HASH__)/,
  '<div id="root"></div>$1',
  "the prerendered #root",
);

writeFileSync(new URL("../dist/spa.html", import.meta.url), html);
console.log("wrote dist/spa.html");
