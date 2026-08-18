import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { COUNTIES, AREAS, DUBLIN_EIRCODE_AREAS, countySlug } from "./src/areas";
import { BLOG_POSTS } from "./src/blogPosts";
import { STREETS } from "./src/streets";

export default defineConfig({
  plugins: [react()],
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
      const posts = BLOG_POSTS.map((p) => `/blog/${p.slug}`);
      const streets = STREETS.map((s) => `/street/${s.slug}`);
      return [...staticPaths, ...counties, ...areas, ...eircodes, ...posts, ...streets];
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
