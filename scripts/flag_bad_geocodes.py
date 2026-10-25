#!/usr/bin/env python3
"""
Flag bad/missing geocodes for re-geocoding and hide the harmful ones from search.

Root cause (2026-08): the geocoder matched generic street names ("Main Street",
"Harbour Road") and ignored town/county, piling unrelated addresses from all over
Ireland onto a single street centroid (e.g. Howth). The validation gap that let
these through is fixed in geocode_mapbox_batch.py; this script cleans up the
existing rows.

Two flags, two purposes:

  needs_geocoding = TRUE   -> the re-geocode worklist (drives geocode_mapbox_batch.py)
                             union of: no coordinates
                                       coordinate outside its stored county's box
                                       eircode beyond its routing-key's adaptive extent
                                       numbered address far from its town's other sales
                                       on a coordinate shared by >=30 distinct addresses

  geocode_suspect = TRUE   -> hide from /search and /trends until re-geocoded
                             (coordinate is known-wrong / untrustworthy)
                             union of: coordinate outside its stored county's box
                                       eircode beyond its routing-key's adaptive extent
                                       numbered address far from its town's other sales
                                       on a coordinate shared by >=50 distinct addresses
                             (only rows that HAVE coordinates)

  Why county-first: a routing-key centroid is a single point but keys are AREAS —
  rural ones sprawl (Nobber is 19km from the A82 centroid at its CORRECT coords), so a
  flat distance-from-centroid conflated key-size with error. The county-box check is the
  reliable wrong-town signal; the per-key adaptive distance rule and the cluster check
  catch the rest.

Rows matching a development pin (scripts/development_pins.py) are never flagged.

Idempotent: safe to re-run. Use --apply to write; default is dry-run.

--add-only (with --apply): only ADD flags to rows not already suspect, without the
full reset/reconcile. Run it after every geocoding sweep: geocode_mapbox_batch.py
clears geocode_suspect on rows it places, so a wrong Mapbox answer stays visible until
re-flagged (2026-10: ~13k wrong rows had gone unflagged since the 23 Aug full run, e.g.
Parkview, Stepaside D18 placed near Malahide). The full run would also re-queue rows
that already failed (suspect + needs_geocoding = FALSE), so add-only leaves those alone.
"""
import math
import os
import re
import statistics
import sys
from collections import defaultdict

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from county_validator import COUNTY_BOUNDS
from development_pins import PINNED_IDS_SQL

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

# A routing key is an AREA, not a point, and areas vary hugely in size. A single flat
# distance threshold can't fit both: 40km misses errors inside compact urban keys
# (A96/Dun Laoghaire is ~2km p75, so a row geocoded 12.6km away -- the Howth bug --
# slips under 40km and is never flagged), while a tight threshold mis-flags genuinely
# sprawling rural keys (A82/Kells: Nobber is ~19km from centroid at its CORRECT coords).
# Fix: derive each key's threshold from its OWN distance distribution --
#   threshold_km = clamp(p75_of_member_distances * RK_MULT, RK_FLOOR_KM, RK_CEIL_KM)
# p75 (not max) is the robust "core extent": far outliers don't inflate a key's own
# threshold and so can't hide its errors. Floor protects compact keys from noise; ceiling
# keeps the largest keys from becoming un-flaggable. Verified: A96 -> 8km (flags 12.6km),
# A82 -> 31km (spares 19km). See scripts/analyze_adaptive_rk.py.
RK_MULT = 2.0            # multiple of a key's p75 extent that counts as misplaced
RK_FLOOR_KM = 8.0        # minimum threshold (compact urban keys)
RK_CEIL_KM = 45.0        # maximum threshold (largest sprawling keys)

# County bounding boxes (county_validator.COUNTY_BOUNDS) are the strongest wrong-town
# signal: a Kerry-county row sitting in Dublin is wrong regardless of eircode/cluster.
# The boxes are tight, so we pad them by this margin before treating "outside the box"
# as a hide signal — this spares genuine edge-of-county towns (e.g. Fingal reaches
# ~53.63N, above County Dublin's 53.50 box) while still catching cross-region matches.
COUNTY_MARGIN_DEG = 0.2

SUSPECT_CLUSTER = 50     # distinct addresses on one coord -> fallback centroid (hide)
WORKLIST_CLUSTER = 30    # distinct addresses on one coord -> worth re-geocoding

# Locality consistency: a numbered address ending in a town ("52 Listoke Pines, Drogheda")
# should sit near that town's other sales. This catches wrong-town rows the routing-key
# rule can't see because they have no eircode and no "Dublin N" (2026-10: "20 the Ash,
# Parkview, Stepaside" sat 22km away, visible). Each town's reference point and extent
# come from its own visible numbered sales, with the same clamp(p75 * mult) shape as the
# routing-key rule. Unnumbered rural addresses are skipped: a townland whose postal town
# is Navan can be 15km from Navan. A row is spared if it sits near another place named in
# its own address ("48 Woodlawn, Allenwood, Naas" is in Allenwood, ~15km from Naas); if
# that village has too few sales to check, the row is only flagged beyond LOC_CEIL_KM.
LOC_MULT = 2.0
LOC_FLOOR_KM = 5.0
LOC_CEIL_KM = 30.0
LOC_MIN_REF = 20          # visible numbered sales needed before a town is checked
LOC_RESCUE_MIN_REF = 5    # ...and before a named village can spare a row

_COUNTY_WORDS = "|".join(c.lower() for c in COUNTY_BOUNDS)
_AREA_SUFFIX = re.compile(
    rf"(?:^|[\s,]+)(?:co\.?\s*\w+|county\s+\w+|dublin\s*\d{{1,2}}w?|ireland|{_COUNTY_WORDS})\.?\s*$",
    re.I)
_ROAD = re.compile(r"\b(?:road|rd|street|st|avenue|ave|lane|main|upper|lower|[nr]\d+)\b", re.I)
_NUMBERED = re.compile(r"^(?:apt|apartment|unit|flat|no)?\.?\s*\d+[a-z]?\b", re.I)


def _strip_area_suffix(part):
    prev = None
    while prev != part:
        prev, part = part, _AREA_SUFFIX.sub("", part).strip(" ,.")
    return part


def address_places(address):
    """Place names in a numbered address, most specific first, town last.

    Only the last two comma parts after the house/unit are considered, so block names
    ("the Oak") aren't treated as places. [] if unnumbered or the last part isn't a town.
    """
    if not address or not _NUMBERED.match(address):
        return []
    parts = [x.strip(" .") for x in address.split(",")]
    while parts:
        last = _strip_area_suffix(parts[-1])
        if last:
            parts[-1] = last
            break
        parts.pop()
    places = parts[max(1, len(parts) - 2):]
    ok = lambda x: len(x) >= 3 and not re.search(r"\d", x) and not _ROAD.search(x)
    if not places or not ok(places[-1]):
        return []
    return [x.lower() for x in places if ok(x)]


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def locality_bad_ids(rows):
    """ids of visible rows far from the town their address ends in.

    rows: iterable of (id, county, address_normalized, lat, lon, geocode_suspect).
    """
    rows = [(r, address_places(r[2])) for r in rows if r[3] is not None]
    ref = defaultdict(list)
    for r, places in rows:
        if places and not r[5]:
            ref[(r[1], places[-1])].append((r[3], r[4]))

    extent = {}   # (county, place) -> (lat, lon, threshold_km, n)
    for key, pts in ref.items():
        if len(pts) < LOC_RESCUE_MIN_REF:
            continue
        lat = statistics.median(p[0] for p in pts)
        lon = statistics.median(p[1] for p in pts)
        d = sorted(_km(lat, lon, *p) for p in pts)
        p75 = d[int(len(d) * 0.75)]
        extent[key] = (lat, lon, max(LOC_FLOOR_KM, min(LOC_CEIL_KM, p75 * LOC_MULT)), len(pts))

    def near(county, place, lat, lon, min_ref):
        """(within threshold, km away), or None if the place has too few sales."""
        e = extent.get((county, place))
        if e is None or e[3] < min_ref:
            return None
        d = _km(e[0], e[1], lat, lon)
        return d <= e[2], d

    bad = set()
    for r, places in rows:
        if not places or r[5]:
            continue
        town = near(r[1], places[-1], r[3], r[4], LOC_MIN_REF)
        if town is None or town[0]:
            continue
        villages = [near(r[1], x, r[3], r[4], LOC_RESCUE_MIN_REF) for x in places[:-1]]
        if any(v and v[0] for v in villages):
            continue
        # A village we can't check (too few sales) may be far from its postal town,
        # so only flag beyond the ceiling.
        if places[:-1] and not any(villages) and town[1] <= LOC_CEIL_KM:
            continue
        bad.add(r[0])
    return bad

APPLY = "--apply" in sys.argv
ADD_ONLY = "--add-only" in sys.argv


def _county_bounds_values():
    """SQL VALUES rows for the padded county bounding boxes."""
    m = COUNTY_MARGIN_DEG
    return ",".join(
        f"('{c}',{a - m},{b + m},{lo - m},{hi + m})"
        for c, (a, b, lo, hi) in COUNTY_BOUNDS.items()
    )


def main():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    # Keepalives: a dropped connection otherwise hangs the script forever with no
    # query running server-side (happened twice on 2026-10-23).
    conn = psycopg2.connect(dsn, keepalives=1, keepalives_idle=60,
                            keepalives_interval=15, keepalives_count=4)
    conn.autocommit = True  # commit each step; big updates must not share one txn
    cur = conn.cursor()
    # These aggregate/join updates exceed Supabase's default statement_timeout.
    cur.execute("SET statement_timeout = '900s'")
    # The 2MB default spills each run's sorts (~380MB) to temp files on disk.
    cur.execute("SET work_mem = '64MB'")

    print(f"Mode: {'APPLY (writing)' if APPLY else 'DRY RUN (no writes)'}")
    print(f"Thresholds: county-box margin {COUNTY_MARGIN_DEG}deg, routing-key adaptive "
          f"(p75*{RK_MULT}, clamp {RK_FLOOR_KM}-{RK_CEIL_KM}km), "
          f"suspect cluster >={SUSPECT_CLUSTER} distinct, worklist cluster >={WORKLIST_CLUSTER} distinct\n")

    # 1. Add geocode_suspect column + partial index (idempotent, committed immediately)
    if APPLY:
        cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS geocode_suspect BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_properties_geocode_suspect "
                    "ON properties (geocode_suspect) WHERE geocode_suspect = TRUE")
        print("✓ geocode_suspect column + index ensured")

    # Locality rule runs in Python (address parsing); its ids go to a temp table the
    # CTE below unions in. Temp tables are session-only, so this is fine in dry-run.
    cur.execute("SELECT id, county, address_normalized, latitude, longitude, "
                "geocode_suspect IS TRUE FROM properties WHERE latitude IS NOT NULL")
    loc_bad = locality_bad_ids(cur.fetchall())
    cur.execute("DROP TABLE IF EXISTS _loc_bad")
    cur.execute("CREATE TEMP TABLE _loc_bad (id BIGINT PRIMARY KEY)")
    execute_values(cur, "INSERT INTO _loc_bad (id) VALUES %s", [(i,) for i in loc_bad])
    print(f"Locality rule: {len(loc_bad):,} visible rows far from their town")

    # Reusable CTEs identifying the bad rows.
    cte = f"""
    WITH cbounds(county, minlat, maxlat, minlon, maxlon) AS (
        VALUES {_county_bounds_values()}
    ),
    county_bad AS (
        -- Coordinate falls OUTSIDE the (margin-padded) box of its own stored county.
        -- Strongest wrong-town signal; independent of eircode/cluster.
        SELECT p.id
        FROM properties p
        JOIN cbounds b ON b.county = p.county
        WHERE p.latitude IS NOT NULL
          AND NOT (p.latitude BETWEEN b.minlat AND b.maxlat
                   AND p.longitude BETWEEN b.minlon AND b.maxlon)
    ),
    good_keys AS (
        SELECT routing_key, centroid_lat, centroid_lon
        FROM routing_key_stats
        WHERE geocoded_count >= 20 AND centroid_lat IS NOT NULL
    ),
    rk_extent AS (
        -- Each key's "core extent": 75th percentile of its member-property distances
        -- from the key centroid. Robust to far outliers (they can't inflate the p75),
        -- so a key polluted with wrong-town rows still gets a tight threshold.
        SELECT p.routing_key,
               percentile_cont(0.75) WITHIN GROUP (ORDER BY
                 ST_Distance(
                   ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
                   ST_SetSRID(ST_MakePoint(k.centroid_lon, k.centroid_lat), 4326)::geography
                 ) / 1000.0
               ) AS p75_km
        FROM properties p
        JOIN good_keys k ON k.routing_key = p.routing_key
        WHERE p.latitude IS NOT NULL
        GROUP BY p.routing_key
    ),
    rk_member AS (
        -- A row's routing key: from its eircode, else (County Dublin only) from a
        -- "Dublin N" postal district in the address, so eircode-less rows such as
        -- "45 the Ash, Parkview, Stepaside Dublin 18" placed 21km away near
        -- Malahide are checked too. Extents (rk_extent) stay eircode-only.
        SELECT p.id, p.latitude, p.longitude,
               COALESCE(p.routing_key,
                 CASE WHEN m.d[2] IS NOT NULL THEN 'D' || m.d[1]::int || 'W'
                      WHEN m.d[1] IS NOT NULL THEN 'D' || lpad(m.d[1]::int::text, 2, '0')
                 END) AS routing_key
        FROM properties p
        LEFT JOIN LATERAL (
            SELECT regexp_match(p.address_normalized, '\\mDublin\\s*(\\d{{1,2}})(W)?\\M', 'i') AS d
        ) m ON p.routing_key IS NULL AND p.county = 'Dublin'
        WHERE p.latitude IS NOT NULL
    ),
    rk_bad AS (
        -- Adaptive per-key threshold = clamp(p75 * RK_MULT, RK_FLOOR_KM, RK_CEIL_KM).
        SELECT p.id
        FROM rk_member p
        JOIN good_keys k ON k.routing_key = p.routing_key
        JOIN rk_extent e ON e.routing_key = p.routing_key
        WHERE p.latitude IS NOT NULL
          AND ST_Distance(
                ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(k.centroid_lon, k.centroid_lat), 4326)::geography
              ) / 1000.0
              > GREATEST({RK_FLOOR_KM}, LEAST({RK_CEIL_KM}, e.p75_km * {RK_MULT}))
    ),
    cluster_suspect_pts AS (
        SELECT latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= {SUSPECT_CLUSTER}
    ),
    cluster_worklist_pts AS (
        SELECT latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= {WORKLIST_CLUSTER}
    ),
    cluster_suspect AS (
        SELECT p.id FROM properties p
        JOIN cluster_suspect_pts c ON p.latitude = c.latitude AND p.longitude = c.longitude
    ),
    cluster_worklist AS (
        SELECT p.id FROM properties p
        JOIN cluster_worklist_pts c ON p.latitude = c.latitude AND p.longitude = c.longitude
    ),
    pinned AS (
        -- Rows on a hand-checked development pin (development_pins.py). A pin puts
        -- every unit on one point, which the cluster rule would otherwise hide.
        {PINNED_IDS_SQL}
    ),
    suspect_ids AS (
        (SELECT id FROM county_bad
         UNION SELECT id FROM rk_bad
         UNION SELECT id FROM _loc_bad
         UNION SELECT id FROM cluster_suspect)
        EXCEPT SELECT id FROM pinned
    ),
    worklist_ids AS (
        (SELECT id FROM properties WHERE latitude IS NULL
         UNION SELECT id FROM county_bad
         UNION SELECT id FROM rk_bad
         UNION SELECT id FROM _loc_bad
         UNION SELECT id FROM cluster_worklist)
        EXCEPT SELECT id FROM pinned
    )
    """

    if not APPLY:
        cur.execute(cte + "SELECT (SELECT COUNT(*) FROM suspect_ids), (SELECT COUNT(*) FROM worklist_ids)")
        n_suspect, n_worklist = cur.fetchone()
        print(f"geocode_suspect (hide from search): {n_suspect:,}")
        print(f"needs_geocoding (re-geocode worklist): {n_worklist:,}")
        print("\nDry run complete. Re-run with --apply to write flags.")
        conn.close()
        return

    # 2. Materialize the bad-id sets into a temp table ONCE (the CTE is expensive:
    #    a full-table cluster aggregation + routing-key join). Reusing it keeps each
    #    UPDATE a fast indexed join instead of re-running the aggregation per statement.
    print("Computing bad-id sets (one aggregation pass)...")
    cur.execute("DROP TABLE IF EXISTS _bad_geo")
    cur.execute(cte + """
        SELECT
            COALESCE(s.id, w.id) AS id,
            (s.id IS NOT NULL)   AS suspect
        INTO TEMP _bad_geo
        FROM suspect_ids s
        FULL OUTER JOIN worklist_ids w ON s.id = w.id
    """)
    cur.execute("CREATE INDEX ON _bad_geo (id)")
    cur.execute("SELECT COUNT(*) FILTER (WHERE suspect), COUNT(*) FROM _bad_geo")
    n_suspect, n_worklist = cur.fetchone()
    print(f"geocode_suspect (hide from search): {n_suspect:,}")
    print(f"needs_geocoding (re-geocode worklist): {n_worklist:,}")

    if ADD_ONLY:
        # Rows not yet suspect: flag the suspect ones and queue all of them. Rows
        # already suspect (hidden, possibly failed and de-queued) are untouched.
        cur.execute("UPDATE properties p SET geocode_suspect = b.suspect, needs_geocoding = TRUE "
                    "FROM _bad_geo b WHERE p.id = b.id AND p.geocode_suspect IS NOT TRUE "
                    "AND (b.suspect OR p.needs_geocoding IS DISTINCT FROM TRUE)")
        print(f"✓ add-only: flagged/queued {cur.rowcount:,} rows not previously suspect")
        cur.execute("SELECT COUNT(*) FILTER (WHERE geocode_suspect), "
                    "COUNT(*) FILTER (WHERE needs_geocoding) FROM properties")
        print("now: geocode_suspect={:,}, needs_geocoding={:,}".format(*cur.fetchone()))
        cur.execute("DROP TABLE IF EXISTS _bad_geo")
        print("\n✅ Done.")
        conn.close()
        return

    # 3. Set geocode_suspect (reset first so re-runs reflect improved data)
    cur.execute("UPDATE properties SET geocode_suspect = FALSE WHERE geocode_suspect = TRUE")
    cur.execute("UPDATE properties p SET geocode_suspect = TRUE "
                "FROM _bad_geo b WHERE p.id = b.id AND b.suspect")
    print(f"✓ geocode_suspect set on {cur.rowcount:,} rows")

    # 4. Reconcile needs_geocoding to EXACTLY the current worklist (_bad_geo). Clearing
    #    rows that now pass avoids spending scarce Mapbox requests re-geocoding
    #    coordinates that are already acceptable (e.g. legitimate rural addresses that
    #    an earlier, stricter distance rule wrongly queued). Null-coord rows are always
    #    in _bad_geo, so they are never cleared here.
    cur.execute("UPDATE properties p SET needs_geocoding = FALSE "
                "WHERE p.needs_geocoding = TRUE "
                "AND NOT EXISTS (SELECT 1 FROM _bad_geo b WHERE b.id = p.id)")
    print(f"✓ needs_geocoding cleared on {cur.rowcount:,} now-passing rows")
    cur.execute("UPDATE properties p SET needs_geocoding = TRUE "
                "FROM _bad_geo b WHERE p.id = b.id AND p.needs_geocoding IS DISTINCT FROM TRUE")
    print(f"✓ needs_geocoding set on {cur.rowcount:,} additional rows")

    cur.execute("DROP TABLE IF EXISTS _bad_geo")
    print("\n✅ Done.")
    conn.close()


if __name__ == "__main__":
    main()
