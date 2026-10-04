import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { COUNTIES, AREAS, DUBLIN_EIRCODE_AREAS, countySlug } from "./src/areas";
import { publishedPosts } from "./src/blogPosts";
import { STREET_CONFIGS, STREET_LINK_FIELDS } from "./src/streetRegistry";

const REGISTRY = fileURLToPath(new URL("./src/data/streets_registry.json", import.meta.url));

// `virtual:street-links`: the street registry with only the link fields, for
// pages that list or link to streets. Dropping description/info keeps ~56 KB of
// text out of the bundle; the street page gets its full entry from its loader.
function streetLinks(): Plugin {
  const id = "virtual:street-links";
  return {
    name: "street-links",
    resolveId: (source) => (source === id ? "\0" + id : undefined),
    load(resolved) {
      if (resolved !== "\0" + id) return;
      this.addWatchFile(REGISTRY);
      const registry: Record<string, unknown>[] = JSON.parse(readFileSync(REGISTRY, "utf8"));
      const links = registry.map((s) => Object.fromEntries(STREET_LINK_FIELDS.map((f) => [f, s[f]])));
      return `export default ${JSON.stringify(links)};`;
    },
  };
}

export default defineConfig({
  plugins: [react(), streetLinks()],
  define: {
    // Formatted once at build time so the prerendered HTML and the hydrated
    // client render the same string (a render-time `new Date()` mismatches).
    __BUILD_TIME__: JSON.stringify(
      new Date().toLocaleString("en-IE", { dateStyle: "medium", timeStyle: "short", timeZone: "Europe/Dublin" })
    ),
    // YYYY-MM-DD, for content gated on a date (e.g. links to scheduled posts)
    __BUILD_DATE__: JSON.stringify(new Date().toISOString().slice(0, 10)),
  },
  // vite-react-ssg reads its build-time SSG options from here (the plugin
  // augments vite's UserConfig with `ssgOptions`). `includedRoutes` decides
  // which concrete URLs get prerendered — it is NOT a ViteReactSSG() runtime
  // argument.
  ssgOptions: {
    // Emit nested `route/index.html` files (not flat `route.html`) so static
    // hosts serve them at the clean, extensionless URL via directory-index
    // resolution — no cleanUrls rewrite needed.
    dirStyle: "nested",
    includedRoutes(paths: string[]) {
      // Keep concrete static routes; drop the dynamic templates and catch-all.
      const staticPaths = paths.filter((p) => !p.includes(":") && p !== "*");
      const counties = COUNTIES
        .filter((c) => c.toLowerCase() !== "dublin") // /county/dublin is its own static route
        .map((c) => `/county/${countySlug(c)}`);
      const areas = AREAS.map((a) => `/area/${a.slug}`);
      const eircodes = Object.keys(DUBLIN_EIRCODE_AREAS).map((k) => `/eircode/${k}`);
      // Scheduled (future-dated) posts are not prerendered until their date.
      const posts = publishedPosts().map((p) => `/blog/${p.slug}`);
      const streets = STREET_CONFIGS.map((s) => `/street/${s.slug}`);
      // "/404" renders the catch-all NotFoundPage; the build script copies it to
      // dist/404.html, which Vercel serves (status 404) for unmatched URLs.
      return [...staticPaths, ...counties, ...areas, ...eircodes, ...posts, ...streets, "/404"];
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
