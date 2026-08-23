"""Generate static JSON for area / eircode / county landing pages by calling the
backend API (parity with the frontend's fetchAreaSummary / fetchEircode /
fetchCountySummary). Run after the PPR sync, then rebuild + redeploy the frontend.

Usage:
  python3 scripts/generate_page_data.py [--api-url http://localhost:8000] \
                                        [--only areas,eircodes,counties]

Targets are parsed from frontend/src/areas.ts so they cannot drift from the
routes the frontend prerenders. If that parsing ever breaks, fall back to a
committed frontend/src/data/page_targets.json (see spec).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
AREAS_TS = os.path.join(ROOT, "frontend", "src", "areas.ts")
DATA_DIR = os.path.join(ROOT, "frontend", "src", "data")


def _areas_src():
    with open(AREAS_TS, encoding="utf-8") as fh:
        return fh.read()


def _split_top_level_objects(array_body):
    """Yield each top-level {...} object string from a JS array body.
    Relies on the fact that field VALUES in areas.ts contain no braces."""
    depth, buf = 0, []
    for ch in array_body:
        if ch == "{":
            depth += 1
        if depth > 0:
            buf.append(ch)
        if ch == "}":
            depth -= 1
            if depth == 0:
                yield "".join(buf)
                buf = []


def area_targets():
    src = _areas_src()
    anchor = src.index("export const AREAS")
    start = src.index("[", src.index("=", anchor))
    depth = 0
    end = start
    for i in range(start, len(src)):
        if src[i] == "[":
            depth += 1
        elif src[i] == "]":
            depth -= 1
            if depth == 0:
                end = i
                break
    body = src[start + 1:end]

    targets = []
    for obj in _split_top_level_objects(body):
        slug = re.search(r'slug:\s*"([^"]+)"', obj).group(1)
        query = re.search(r'query:\s*"([^"]+)"', obj).group(1)
        radius = float(re.search(r"radius_km:\s*([\d.]+)", obj).group(1))
        match = re.findall(r'"([^"]+)"', re.search(r"match:\s*\[([^\]]*)\]", obj).group(1))
        rk = re.search(r"routing_keys:\s*\[([^\]]*)\]", obj)
        routing_keys = re.findall(r'"([^"]+)"', rk.group(1)) if rk else []
        targets.append({
            "slug": slug, "query": query, "radius_km": radius,
            "match": match, "routing_keys": routing_keys,
        })
    return targets


def eircode_targets():
    src = _areas_src()
    block = re.search(r"DUBLIN_EIRCODE_AREAS[^=]*=\s*\{([^}]*)\}", src).group(1)
    return re.findall(r'(\w+):\s*"', block)


def county_targets():
    src = _areas_src()
    block = re.search(r"export const COUNTIES\s*=\s*\[([^\]]*)\]", src).group(1)
    return re.findall(r'"([^"]+)"', block)


def county_slug(name):
    return re.sub(r"\s+", "-", name.lower())


def _get(api_url, path, params):
    clean = {k: v for k, v in params.items() if v is not None}
    url = api_url.rstrip("/") + path + "?" + urllib.parse.urlencode(clean)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


RECENT_LIMIT = 10  # matches the live fetch* limits in frontend/src/api.ts


def build_area(api_url, target):
    locality = ",".join(target["match"]) if target["match"] else None
    routing_keys = ",".join(target["routing_keys"]) if target["routing_keys"] else None
    search = _get(api_url, "/search", {
        "q": target["query"], "radius_km": target["radius_km"],
        "limit": RECENT_LIMIT, "locality": locality, "routing_keys": routing_keys,
    })
    trends = _get(api_url, "/trends", {
        "q": target["query"], "radius_km": target["radius_km"],
        "locality": locality, "routing_keys": routing_keys,
    }).get("data", [])

    prices = [r["price"] for r in search["results"]]
    years = [t["year"] for t in trends]
    return {
        "name": target["query"],
        "slug": target["slug"],
        "center": search["center"],
        "radius_km": target["radius_km"],
        "total_count": search["count"],
        "median_price": trends[-1]["median_price"] if trends else None,
        "avg_price": round(sum(prices) / len(prices)) if prices else None,
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
        "recent": search["results"],
        "trends": trends,
    }


def build_eircode(api_url, code):
    eircode = _get(api_url, "/eircode", {"code": code, "limit": RECENT_LIMIT})
    county = eircode["results"][0]["county"] if eircode["results"] else None
    trends = _get(api_url, "/trends", {"radius_km": 5, "county": county}).get("data", []) if county else []
    return {"eircode": eircode, "trends": trends}


def build_county(api_url, name, counties):
    trends = _get(api_url, "/trends", {"county": name}).get("data", [])
    # /county-recent returns the latest sales across the whole county (no radius,
    # unlike /search which is capped at 20km). A transient failure raises so
    # main() warns and skips rather than baking empty recent.
    search = _get(api_url, "/county-recent", {"county": name, "limit": RECENT_LIMIT})
    row = next((c for c in counties if c["county"].lower() == name.lower()), None)
    if row and row["count"] > 0 and not trends:
        raise ValueError(f"{name}: /counties count={row['count']} but /trends returned empty")
    latest = trends[-1] if trends else None
    return {
        "county": name,
        "total_count": row["count"] if row else 0,
        "median_price": latest["median_price"] if latest else None,
        "avg_price": latest["avg_price"] if latest else None,
        "trends": trends,
        "recent": search["results"],
    }


def _write(subdir, slug, obj):
    out_dir = os.path.join(DATA_DIR, subdir)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, slug + ".json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description="Generate static area/eircode/county page JSON.")
    ap.add_argument("--api-url", default=os.getenv("PAGE_DATA_API_URL", "http://localhost:8000"))
    ap.add_argument("--only", help="comma list of: areas,eircodes,counties")
    args = ap.parse_args()
    only = set(s.strip() for s in args.only.split(",")) if args.only else {"areas", "eircodes", "counties"}

    written = 0
    if "areas" in only:
        for t in area_targets():
            try:
                _write("areas", t["slug"], build_area(args.api_url, t))
                written += 1
            except Exception as e:  # noqa: BLE001 - per-target isolation
                print(f"WARNING: area {t['slug']} failed: {e}")

    if "eircodes" in only:
        for code in eircode_targets():
            try:
                _write("eircodes", code, build_eircode(args.api_url, code))
                written += 1
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: eircode {code} failed: {e}")

    if "counties" in only:
        try:
            counties = _get(args.api_url, "/counties", {})
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: could not fetch /counties from {args.api_url}: {e}")
            return 1
        for name in county_targets():
            try:
                _write("counties", county_slug(name), build_county(args.api_url, name, counties))
                written += 1
            except Exception as e:  # noqa: BLE001
                print(f"WARNING: county {name} failed: {e}")

    print(f"wrote {written} page data files under {DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
