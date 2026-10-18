import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { COUNTIES, AREAS, DUBLIN_EIRCODE_AREAS, countySlug } from "./src/areas";
import { publishedPosts } from "./src/blogPosts";
import { STREET_CONFIGS, STREET_LINK_FIELDS } from "./src/streetRegistry";
import { DEVELOPMENT_CONFIGS, DEVELOPMENT_LINK_FIELDS } from "./src/developmentRegistry";

// vite-react-ssg evaluates this config separately for its client and SSR builds.
// Pin the build instant in the environment on first load so both builds share
// it; otherwise a minute boundary between them makes __BUILD_TIME__ differ and
// every page fails hydration.
process.env.HOMEIQ_BUILD_INSTANT ??= new Date().toISOString();
const BUILD_INSTANT = new Date(process.env.HOMEIQ_BUILD_INSTANT);

const dataFile = (name: string) => fileURLToPath(new URL(`./src/data/${name}`, import.meta.url));

// `virtual:street-links` / `virtual:development-links`: a registry with only the
// link fields, for client pages that list or link to its entries. Dropping the
// description/info text keeps it out of the bundle (~56 KB for streets); the
// detail pages get their full entry from their loader.
function registryLinks(id: string, file: string, fields: readonly string[]): Plugin {
  return {
    name: id.replace("virtual:", ""),
    resolveId: (source) => (source === id ? "\0" + id : undefined),
    load(resolved) {
      if (resolved !== "\0" + id) return;
      this.addWatchFile(file);
      const registry: Record<string, unknown>[] = JSON.parse(readFileSync(file, "utf8"));
      const links = registry.map((s) => Object.fromEntries(fields.map((f) => [f, s[f]])));
      return `export default ${JSON.stringify(links)};`;
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    registryLinks("virtual:street-links", dataFile("streets_registry.json"), STREET_LINK_FIELDS),
    registryLinks("virtual:development-links", dataFile("developments_registry.json"), DEVELOPMENT_LINK_FIELDS),
  ],
  define: {
    // Formatted once at build time so the prerendered HTML and the hydrated
    // client render the same string (a render-time `new Date()` mismatches).
    __BUILD_TIME__: JSON.stringify(
      BUILD_INSTANT.toLocaleString("en-IE", { dateStyle: "medium", timeStyle: "short", timeZone: "Europe/Dublin" })
    ),
    // YYYY-MM-DD, for content gated on a date (e.g. links to scheduled posts)
    __BUILD_DATE__: JSON.stringify(BUILD_INSTANT.toISOString().slice(0, 10)),
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
      const developments = DEVELOPMENT_CONFIGS.map((d) => `/development/${d.slug}`);
      // "/404" renders the catch-all NotFoundPage; the build script copies it to
      // dist/404.html, which Vercel serves (status 404) for unmatched URLs.
      return [...staticPaths, ...counties, ...areas, ...eircodes, ...posts, ...streets, ...developments, "/404"];
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
