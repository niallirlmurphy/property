#!/usr/bin/env python3
"""
Known-good coordinates for named developments, reused for every sale in them.

Mapbox can't place named apartment schemes ("Apt 21, The Oak, Parkview, Stepaside"):
it falls back to the road or a random point, and re-geocoding them only burns credits
(2026-10-17: 0 of 13 Parkview rows placed; the 99 Parkview rows had sat a median 12km
from the development). A pin is a hand-checked coordinate plus a full-text rule saying
which addresses belong to the development. Applying pins is free and runs before any
Mapbox call, so new sales in a pinned development are placed with zero requests.

Where pins are used:
  - geocode_mapbox_batch.py applies pins first (--apply), then drops pinned rows from
    the Mapbox batch, whichever mode selected them (worklist, --centroid, --ids-file).
  - flag_bad_geocodes.py never flags a pinned row. A pin puts every unit on one point,
    which the cluster rule (>=50 distinct addresses on a coordinate) would otherwise
    treat as a fallback centroid and hide.

The match rule is a to_tsquery('simple', ...) expression over address_normalized
(the project bans LIKE). Include misspellings and the block names, and exclude
neighbouring schemes that share a word, e.g. for Parkview, Stepaside:
    parkview & (ash | cedar | elm | oak | sycamore | willow ...)
             & (stepaside | setpaside | belarmine | enniskerry | dublin <-> 18) & !belfry

Usage:
    python3 scripts/development_pins.py list
    python3 scripts/development_pins.py add --name "Parkview, Stepaside" --county Dublin \\
        --match "<tsquery>" --lat 53.2596962 --lon -6.2247187 [--keep-within 800] \\
        [--notes "..."] [--apply]
    python3 scripts/development_pins.py apply [--apply]

--keep-within suits estates of streets (e.g. Honeypark), where good street-level
geocodes are finer than one pin: only rows with no, hidden or far-off coordinates move.

add and apply are dry runs unless --apply is given; add shows the matched addresses
and any rows already claimed by another pin.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from county_validator import COUNTY_BOUNDS

# Same padding as flag_bad_geocodes.COUNTY_MARGIN_DEG: the boxes are tight and
# edge-of-county towns sit just outside them.
COUNTY_MARGIN_DEG = 0.2

# Must match the expression of idx_properties_address_fts so the GIN index is used.
ADDRESS_TSV = "to_tsvector('simple', COALESCE(p.address_normalized, p.address))"

PIN_MATCH = f"p.county = d.county AND {ADDRESS_TSV} @@ to_tsquery('simple', d.match_query)"

# ids of every row that belongs to a pinned development
PINNED_IDS_SQL = f"SELECT p.id FROM properties p JOIN development_pins d ON {PIN_MATCH}"

# A pin with keep_within_m covers a spread-out estate: rows already geocoded, visible
# and within that radius of the pin keep their own (finer) coordinates; only missing,
# hidden or far-off rows are moved. NULL means every matching row goes on the pin.
_KEEPS_OWN = """d.keep_within_m IS NOT NULL AND p.geog IS NOT NULL
      AND p.geocode_suspect IS NOT TRUE
      AND ST_DWithin(p.geog, ST_MakePoint(d.longitude, d.latitude)::geography, d.keep_within_m)"""

# Pinned rows not yet on their pin (or still flagged). Re-applying is a cheap no-op.
_NEEDS_PIN = f"""{PIN_MATCH}
      AND NOT ({_KEEPS_OWN})
      AND (p.latitude IS DISTINCT FROM d.latitude
           OR p.longitude IS DISTINCT FROM d.longitude
           OR p.geog IS NULL
           OR p.geocode_suspect IS TRUE
           OR p.needs_geocoding IS TRUE
           OR p.geocode_quality_issue IS TRUE)"""

# Move pinned rows onto their pin and mark them good.
APPLY_SQL = f"""
    UPDATE properties p
    SET latitude = d.latitude, longitude = d.longitude,
        geog = ST_SetSRID(ST_MakePoint(d.longitude, d.latitude), 4326)::geography,
        geocode_suspect = FALSE, needs_geocoding = FALSE, geocode_quality_issue = FALSE
    FROM development_pins d
    WHERE {_NEEDS_PIN}
"""

PENDING_SQL = f"SELECT COUNT(*) FROM properties p JOIN development_pins d ON {_NEEDS_PIN}"

CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS development_pins (
        id           SERIAL PRIMARY KEY,
        name         TEXT NOT NULL,
        county       TEXT NOT NULL,
        match_query  TEXT NOT NULL,
        latitude     DOUBLE PRECISION NOT NULL,
        longitude    DOUBLE PRECISION NOT NULL,
        source       TEXT NOT NULL DEFAULT 'manual',
        notes        TEXT,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (county, match_query)
    );
    ALTER TABLE development_pins ADD COLUMN IF NOT EXISTS keep_within_m DOUBLE PRECISION
"""

_ALLOWED = re.compile(r"^[\w\s&|!()<>\-]+$")


def check_pin(county: str, match_query: str, lat: float, lon: float,
              keep_within_m: float = None) -> None:
    """Raise ValueError if a pin is malformed or lands outside its county."""
    if keep_within_m is not None and not 0 < keep_within_m <= 2000:
        raise ValueError("keep-within must be between 0 and 2000 metres")
    if county not in COUNTY_BOUNDS:
        raise ValueError(f"Unknown county {county!r}")
    if not _ALLOWED.match(match_query):
        raise ValueError("match must be a full-text (to_tsquery) expression: "
                         "words, & | ! ( ) and <-> only")
    terms = [t for t in re.findall(r"!?\w+", match_query) if not t.startswith("!")]
    if len(terms) < 2:
        raise ValueError("match needs at least two terms (development + locality)")
    minlat, maxlat, minlon, maxlon = COUNTY_BOUNDS[county]
    m = COUNTY_MARGIN_DEG
    if not (minlat - m <= lat <= maxlat + m and minlon - m <= lon <= maxlon + m):
        raise ValueError(f"({lat}, {lon}) is outside County {county}")


def _connect():
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    return conn


def cmd_list(cur, _args):
    cur.execute(f"""
        SELECT d.id, d.name, d.county, d.latitude, d.longitude, d.source, d.keep_within_m,
               (SELECT COUNT(*) FROM properties p WHERE {PIN_MATCH})
        FROM development_pins d ORDER BY d.id""")
    rows = cur.fetchall()
    if not rows:
        print("No pins.")
    for pid, name, county, lat, lon, source, keep, n in rows:
        radius = f"  keeps own geocode within {keep:.0f}m" if keep else ""
        print(f"{pid:>4}  {name} (Co. {county})  {lat:.6f},{lon:.6f}  {source}  {n} sales{radius}")


def cmd_add(cur, args):
    check_pin(args.county, args.match, args.lat, args.lon, args.keep_within)
    cur.execute(f"""SELECT p.id, p.address FROM properties p
                    WHERE p.county = %s AND {ADDRESS_TSV} @@ to_tsquery('simple', %s)
                    ORDER BY p.address""", (args.county, args.match))
    rows = cur.fetchall()
    print(f"{len(rows)} sales match {args.name!r}:")
    for _, addr in rows:
        print(f"  {addr}")
    cur.execute(f"""SELECT d.name, COUNT(*) FROM properties p
                    JOIN development_pins d ON {PIN_MATCH}
                    WHERE p.id = ANY(%s) GROUP BY d.name""", ([r[0] for r in rows],))
    overlaps = cur.fetchall()
    if overlaps:
        for name, n in overlaps:
            print(f"❌ {n} of these already belong to pin {name!r}; tighten the match")
        sys.exit(1)
    if not rows:
        print("❌ Nothing matches; check the match rule")
        sys.exit(1)
    if args.keep_within:
        cur.execute("""SELECT COUNT(*) FROM properties p WHERE p.id = ANY(%s)
                       AND p.geog IS NOT NULL AND p.geocode_suspect IS NOT TRUE
                       AND ST_DWithin(p.geog, ST_MakePoint(%s, %s)::geography, %s)""",
                    ([r[0] for r in rows], args.lon, args.lat, args.keep_within))
        kept = cur.fetchone()[0]
        print(f"{kept} already within {args.keep_within:.0f}m keep their own geocode; "
              f"{len(rows) - kept} go on the pin")
    if not args.apply:
        print("\nDry run. Re-run with --apply to save the pin and move these rows.")
        return
    cur.execute("""INSERT INTO development_pins
                       (name, county, match_query, latitude, longitude, keep_within_m, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (args.name, args.county, args.match, args.lat, args.lon,
                 args.keep_within, args.notes))
    # Without stats the planner seq-scans properties for the pin join (6s vs 0.3s).
    cur.execute("ANALYZE development_pins")
    cur.execute(APPLY_SQL)
    print(f"✓ Pin saved; {cur.rowcount} rows moved onto it")


def cmd_apply(cur, args):
    if not args.apply:
        cur.execute(PENDING_SQL)
        print(f"{cur.fetchone()[0]} pinned rows would be updated (dry run)")
        return
    cur.execute(APPLY_SQL)
    print(f"✓ {cur.rowcount} pinned rows updated")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--county", required=True)
    a.add_argument("--match", required=True, help="to_tsquery('simple', ...) expression")
    a.add_argument("--lat", type=float, required=True)
    a.add_argument("--lon", type=float, required=True)
    a.add_argument("--keep-within", type=float, metavar="METRES",
                   help="leave rows already geocoded within this radius of the pin as they are")
    a.add_argument("--notes")
    a.add_argument("--apply", action="store_true")
    p = sub.add_parser("apply")
    p.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = _connect()
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '300s'")
    cur.execute(CREATE_SQL)
    {"list": cmd_list, "add": cmd_add, "apply": cmd_apply}[args.cmd](cur, args)
    conn.close()


if __name__ == "__main__":
    main()
