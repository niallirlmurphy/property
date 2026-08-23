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
