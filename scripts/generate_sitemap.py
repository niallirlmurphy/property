#!/usr/bin/env python3
"""
Generate sitemap.xml for homeiq.ie
Includes all static pages, county pages, area pages, and Dublin postcodes.
"""

import os
from datetime import datetime
from pathlib import Path

# Base URL
BASE_URL = "https://homeiq.ie"

# Change frequency and priority for different page types
STATIC_PAGES = [
    {"loc": "/", "changefreq": "daily", "priority": "1.0"},
    {"loc": "/about", "changefreq": "monthly", "priority": "0.8"},
    {"loc": "/polygon", "changefreq": "monthly", "priority": "0.8"},
    {"loc": "/mortgage", "changefreq": "monthly", "priority": "0.7"},
    {"loc": "/energy", "changefreq": "monthly", "priority": "0.6"},
]

# All 26 Irish counties
COUNTIES = [
    "carlow", "cavan", "clare", "cork", "donegal", "dublin", "galway", "kerry",
    "kildare", "kilkenny", "laois", "leitrim", "limerick", "longford", "louth",
    "mayo", "meath", "monaghan", "offaly", "roscommon", "sligo", "tipperary",
    "waterford", "westmeath", "wexford", "wicklow"
]

# Dublin postcodes (Eircodes)
DUBLIN_POSTCODES = [
    "D01", "D02", "D03", "D04", "D05", "D06", "D6W", "D07", "D08", "D09",
    "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18", "D20",
    "D22", "D24"
]

# Popular areas (add more as you create area pages)
AREAS = [
    # Dublin areas
    "ballsbridge", "rathmines", "drumcondra", "clontarf", "dalkey", "howth",
    "dundrum", "blackrock", "dun-laoghaire", "ranelagh", "rathgar", "terenure",
    "castleknock", "malahide", "swords", "lucan", "tallaght", "blanchardstown",

    # Cork areas
    "cork-city", "douglas", "ballincollig", "carrigaline", "cobh", "midleton",

    # Galway areas
    "galway-city", "salthill", "oranmore",

    # Other major towns
    "limerick-city", "waterford-city", "kilkenny-city", "drogheda", "dundalk",
    "bray", "greystones", "naas", "maynooth", "celbridge", "leixlip",
    "athlone", "mullingar", "sligo-town", "tralee", "ennis"
]

def generate_sitemap():
    """Generate sitemap.xml with all pages."""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # Add static pages
    for page in STATIC_PAGES:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}{page['loc']}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>{page['changefreq']}</changefreq>",
            f"    <priority>{page['priority']}</priority>",
            "  </url>",
        ])

    # Add county pages
    for county in COUNTIES:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}/county/{county}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>weekly</changefreq>",
            f"    <priority>0.9</priority>",
            "  </url>",
        ])

    # Add Dublin postcode pages
    for postcode in DUBLIN_POSTCODES:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}/eircode/{postcode}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>weekly</changefreq>",
            f"    <priority>0.8</priority>",
            "  </url>",
        ])

    # Add area pages
    for area in AREAS:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}/area/{area}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>weekly</changefreq>",
            f"    <priority>0.7</priority>",
            "  </url>",
        ])

    lines.append("</urlset>")

    return "\n".join(lines)

def main():
    """Generate and save sitemap."""
    sitemap_content = generate_sitemap()

    # Save to frontend/public/sitemap.xml
    output_path = Path(__file__).parent.parent / "frontend" / "public" / "sitemap.xml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    print(f"✓ Generated sitemap with {sitemap_content.count('<url>')} URLs")
    print(f"✓ Saved to: {output_path}")
    print(f"\nNext steps:")
    print("1. Deploy to production")
    print("2. Submit https://homeiq.ie/sitemap.xml to:")
    print("   - Google Search Console: https://search.google.com/search-console")
    print("   - Bing Webmaster Tools: https://www.bing.com/webmasters")

if __name__ == "__main__":
    main()
