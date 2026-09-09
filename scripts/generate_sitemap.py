#!/usr/bin/env python3
"""
Generate sitemap.xml for homeiq.ie

Enumerates URLs from the actual baked data files and page sources so the
sitemap can never drift out of sync with what is really prerendered:
  - counties  -> frontend/src/data/counties/*.json
  - areas     -> frontend/src/data/areas/*.json
  - eircodes  -> frontend/src/data/eircodes/*.json
  - streets   -> frontend/src/data/streets_registry.json
  - blog      -> frontend/src/blogPosts.ts (slug + date)
  - static / tool / landing pages -> STATIC_PAGES below

<lastmod> is derived per URL (data-file mtime, or blog post date) rather than a
single build date, so it is a meaningful freshness signal to search engines.
"""

import re
from datetime import datetime, date
from pathlib import Path

BASE_URL = "https://homeiq.ie"

ROOT = Path(__file__).parent.parent
SRC = ROOT / "frontend" / "src"
DATA = SRC / "data"

TODAY = date.today().isoformat()

# Static, tool and keyword-landing pages that are prerendered but have no
# per-slug data file. (loc, changefreq, priority)
STATIC_PAGES = [
    ("/", "daily", "1.0"),
    ("/property-price-register", "monthly", "0.9"),
    ("/areaguides", "weekly", "0.8"),
    ("/streets", "weekly", "0.7"),
    ("/blog", "weekly", "0.7"),
    ("/heatmap", "weekly", "0.7"),
    ("/valuation", "monthly", "0.7"),
    ("/polygon", "monthly", "0.7"),
    ("/mortgage", "monthly", "0.7"),
    ("/energy", "monthly", "0.6"),
    ("/about", "monthly", "0.5"),
    ("/contact", "monthly", "0.4"),
]


def _mtime_date(path: Path) -> str:
    """File modification date (YYYY-MM-DD) — reflects last data regeneration."""
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    except OSError:
        return TODAY


def _slugs_from_dir(subdir: str) -> list[tuple[str, str]]:
    """Return (slug, lastmod) for every *.json in DATA/<subdir>, sorted."""
    d = DATA / subdir
    if not d.is_dir():
        return []
    return sorted(
        ((p.stem, _mtime_date(p)) for p in d.glob("*.json")),
        key=lambda t: t[0],
    )


def _street_slugs() -> list[tuple[str, str]]:
    reg = DATA / "streets_registry.json"
    if not reg.is_file():
        return []
    import json
    lastmod = _mtime_date(reg)
    return [(e["slug"], lastmod) for e in json.load(open(reg))]


def _blog_posts() -> list[tuple[str, str]]:
    """Parse (slug, date) pairs from blogPosts.ts in file order."""
    ts = SRC / "blogPosts.ts"
    if not ts.is_file():
        return []
    text = ts.read_text(encoding="utf-8")
    slugs = re.findall(r'slug:\s*"([^"]+)"', text)
    dates = re.findall(r'date:\s*"([^"]+)"', text)
    return list(zip(slugs, dates))


def _url(loc: str, lastmod: str, changefreq: str, priority: str) -> list[str]:
    return [
        "  <url>",
        f"    <loc>{BASE_URL}{loc}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        f"    <changefreq>{changefreq}</changefreq>",
        f"    <priority>{priority}</priority>",
        "  </url>",
    ]


def generate_sitemap() -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for loc, cf, pr in STATIC_PAGES:
        lines += _url(loc, TODAY, cf, pr)

    for slug, lastmod in _slugs_from_dir("counties"):
        lines += _url(f"/county/{slug}", lastmod, "weekly", "0.9")

    for slug, lastmod in _slugs_from_dir("areas"):
        lines += _url(f"/area/{slug}", lastmod, "weekly", "0.7")

    for code, lastmod in _slugs_from_dir("eircodes"):
        lines += _url(f"/eircode/{code}", lastmod, "weekly", "0.8")

    for slug, lastmod in _street_slugs():
        lines += _url(f"/street/{slug}", lastmod, "weekly", "0.6")

    for slug, post_date in _blog_posts():
        lines += _url(f"/blog/{slug}", post_date, "monthly", "0.6")

    lines.append("</urlset>")
    return "\n".join(lines)


def main():
    content = generate_sitemap()
    out = SRC.parent / "public" / "sitemap.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")

    print(f"✓ Generated sitemap with {content.count('<url>')} URLs")
    print(f"✓ Saved to: {out}")
    print("\nNext steps:")
    print("1. Deploy to production")
    print("2. Submit https://homeiq.ie/sitemap.xml to:")
    print("   - Google Search Console: https://search.google.com/search-console")
    print("   - Bing Webmaster Tools: https://www.bing.com/webmasters")


if __name__ == "__main__":
    main()
