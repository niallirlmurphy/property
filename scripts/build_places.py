#!/usr/bin/env python3
"""Build the `places` table (place name -> centre point) used by the backend to
resolve searches like "Swords, Dublin" or "Ranelagh" without Nominatim.

For each (place name, county) found in geocoded addresses (see
backend/places.py:address_place_names), the centre is the median position of the
sales within CLUSTER_KM of its densest ~2km cell, kept only when the sales cluster:
at least MIN_SALES, with CLUSTER_SHARE of them near that cell (or CORE_SALES in the
cell itself, for postal towns). The densest cell
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
from places import address_place_names, county_of  # noqa: E402

MIN_SALES = 10
CLUSTER_KM = 5.0
CLUSTER_SHARE = 0.5
# A postal town's rural addresses ("Townland, Mallow, Co Cork") spread its sales
# over 20km+, so it can miss CLUSTER_SHARE. A densest cell this busy is a town
# anyway; a name shared by many towns ("Main Street") never gets near it.
CORE_SALES = 300
TOP_CELLS = 5

# Places too small to cluster from sales (MIN_SALES), with hand-checked centres:
# (name as normalize_place gives it, county, lat, lon). Written with sales = 0.
MANUAL_PLACES = [
    ("drumlaney", "Cavan", 54.11159, -7.35314),     # townland, Redhills (2026-10-25)
    ("achill", "Mayo", 53.930, -9.939),             # "Achill" alone -> Achill Sound village
    ("dugort", "Mayo", 54.00965, -10.02500),        # village on Achill Island; both spellings
    ("doogort", "Mayo", 54.00965, -10.02500),
    ("staplestown", "Kildare", 53.3299, -6.7684),   # village near Donadea; 15 sales (2026-10-31)
]

SAMPLE = ["swords", "malahide", "tuam", "limerick city", "ranelagh", "dun laoghaire",
          "elm park", "nobber", "dublin 2", "main street", "cork", "galway", "kilkenny", "sligo"]


def _km(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371.0 * math.hypot(dlat, dlon)


def cluster_centre(points: list, core_ok: bool = True) -> "tuple[float, float, int] | None":
    """(lat, lon, sales) for a place's sale positions, or None if they don't cluster.
    core_ok=False for county names: "Mayo" ends addresses county-wide, so its busiest
    cell (Castlebar) isn't a place called Mayo."""
    if len(points) < MIN_SALES:
        return None
    cells = Counter((round(la * 50) / 50, round(lo * 30) / 30) for la, lo in points)
    # Of the busiest few cells, the one with the most sales within CLUSTER_KM. Ties
    # in cell count otherwise go to whichever row the scan met first, so a rebuild
    # could drop a village at random (Achill Island: three cells of 7).
    ranked = sorted(cells.items(), key=lambda kv: (-kv[1], kv[0]))
    core = ranked[0][1]
    near = []
    for (lat, lon), _ in ranked[:TOP_CELLS]:
        here = [p for p in points if _km(lat, lon, *p) <= CLUSTER_KM]
        if len(here) > len(near):
            near = here
    if len(near) < CLUSTER_SHARE * len(points) and not (core_ok and core >= CORE_SALES):
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
        c = cluster_centre(pts, core_ok=county_of(name) is None)
        if c:
            places.append((name, county, *c, spread[name]))
    print(f"{len(points):,} candidate names, {len(places):,} clustered places")
    manual = {(n, c) for n, c, *_ in MANUAL_PLACES}
    places = [p for p in places if (p[0], p[1]) not in manual]
    places += [(n, c, la, lo, 0, spread[n] or 1) for n, c, la, lo in MANUAL_PLACES]
    by_name = defaultdict(list)
    for p in places:
        by_name[p[0]].append(p)
    for s in SAMPLE:
        print(f"  {s:15} {[(c, round(la, 5), round(lo, 5), n) for _, c, la, lo, n, _ in by_name.get(s, [])]}")

    if not args.apply:
        cur = conn.cursor()
        cur.execute("SELECT name, county FROM places")
        current = set(cur.fetchall())
        new = sorted((p for p in places if (p[0], p[1]) not in current), key=lambda p: -p[4])
        gone = current - {(p[0], p[1]) for p in places}
        print(f"{len(new)} new, {len(gone)} dropped vs the current table")
        for name, county, la, lo, n, _ in new[:40]:
            print(f"  + {name:25} {county:10} {la:.5f} {lo:.5f} {n:6,} sales")
        for name, county in sorted(gone)[:20]:
            print(f"  - {name} ({county})")
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
