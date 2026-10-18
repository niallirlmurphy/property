#!/usr/bin/env python3
"""Build the `places` table (place name -> centre point) used by the backend to
resolve searches like "Swords, Dublin" or "Ranelagh" without Nominatim.

For each (place name, county) found in geocoded addresses (see
backend/places.py:address_place_names), the centre is the median position of the
sales within CLUSTER_KM of its densest ~2km cell, kept only when the sales cluster:
at least MIN_SALES, with CLUSTER_SHARE of them near that cell. The densest cell
rather than the overall median, so stray wrong-town geocodes (Tuam sales placed in
Galway city) don't drag the centre. Spread-out names ("Main Street") are left out
and fall through to Mapbox.

Re-run occasionally (e.g. yearly) as new estates appear:
    python3 scripts/build_places.py            # dry run: counts and a sample
    python3 scripts/build_places.py --apply    # replace the table's contents
"""
import argparse
import math
import os
import sys
from collections import Counter, defaultdict
from statistics import median

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "backend"))
from places import address_place_names  # noqa: E402

MIN_SALES = 10
CLUSTER_KM = 5.0
CLUSTER_SHARE = 0.5

SAMPLE = ["swords", "malahide", "tuam", "limerick city", "ranelagh", "dun laoghaire",
          "elm park", "nobber", "dublin 2", "main street", "cork", "galway", "kilkenny", "sligo"]


def _km(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371.0 * math.hypot(dlat, dlon)


def cluster_centre(points: list) -> "tuple[float, float, int] | None":
    """(lat, lon, sales) for a place's sale positions, or None if they don't cluster."""
    if len(points) < MIN_SALES:
        return None
    cells = Counter((round(la * 50) / 50, round(lo * 30) / 30) for la, lo in points)
    (lat, lon), _ = cells.most_common(1)[0]
    near = [p for p in points if _km(lat, lon, *p) <= CLUSTER_KM]
    if len(near) < CLUSTER_SHARE * len(points):
        return None
    return median(p[0] for p in near), median(p[1] for p in near), len(points)


def main():
    ap = argparse.ArgumentParser(description="Build the places table.")
    ap.add_argument("--apply", action="store_true", help="write the table (default: dry run)")
    args = ap.parse_args()

    import psycopg2
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, "backend", ".env"))
    conn = psycopg2.connect(os.environ["DATABASE_URL"])

    points = defaultdict(list)          # (name, county) -> [(lat, lon)]
    cur = conn.cursor(name="stream")
    cur.itersize = 20000
    cur.execute("""
        SELECT COALESCE(address_normalized, address), county, latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL AND county IS NOT NULL AND geocode_suspect IS NOT TRUE
    """)
    for addr, county, lat, lon in cur:
        for name in address_place_names(addr):
            points[(name, county)].append((lat, lon))
    cur.close()

    # How many counties use each name: with no county in the query, the backend only
    # trusts a non-Dublin row when its name belongs to one county ("Tuam", not "Main Street").
    spread = Counter(name for (name, _), pts in points.items() if len(pts) >= MIN_SALES)
    places = []
    for (name, county), pts in points.items():
        c = cluster_centre(pts)
        if c:
            places.append((name, county, *c, spread[name]))
    print(f"{len(points):,} candidate names, {len(places):,} clustered places")
    by_name = defaultdict(list)
    for p in places:
        by_name[p[0]].append(p)
    for s in SAMPLE:
        print(f"  {s:15} {[(c, round(la, 5), round(lo, 5), n) for _, c, la, lo, n, _ in by_name.get(s, [])]}")

    if not args.apply:
        print("dry run: pass --apply to write the table")
        return
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS places (
            name       TEXT NOT NULL,
            county     TEXT NOT NULL,
            latitude   DOUBLE PRECISION NOT NULL,
            longitude  DOUBLE PRECISION NOT NULL,
            sales      INTEGER NOT NULL,
            counties   INTEGER NOT NULL,
            PRIMARY KEY (name, county)
        )""")
    cur.execute("TRUNCATE places")
    cur.executemany("INSERT INTO places VALUES (%s, %s, %s, %s, %s, %s)", places)
    conn.commit()
    conn.close()
    print(f"wrote {len(places):,} places. Run scripts/enable_rls_security.py if the table is new.")


if __name__ == "__main__":
    main()
