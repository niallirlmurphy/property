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
                                       eircode >40km from its routing-key centroid
                                       on a coordinate shared by >=30 distinct addresses

  geocode_suspect = TRUE   -> hide from /search and /trends until re-geocoded
                             (coordinate is known-wrong / untrustworthy)
                             union of: coordinate outside its stored county's box
                                       eircode >40km from its routing-key centroid
                                       on a coordinate shared by >=50 distinct addresses
                             (only rows that HAVE coordinates)

  Why county-first: a routing-key centroid is a single point but keys are AREAS —
  rural ones sprawl (Nobber is 19km from the A82 centroid at its CORRECT coords), so
  distance-from-centroid conflated key-size with error. The county-box check is the
  reliable wrong-town signal; the (relaxed) 40km distance and the cluster check catch
  the rest.

Idempotent: safe to re-run. Use --apply to write; default is dry-run.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from county_validator import COUNTY_BOUNDS

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

# A routing key is an AREA, not a point. Rural keys sprawl: Nobber is genuinely in
# A82 (Kells) but sits ~19km from that key's centroid at its CORRECT coordinates.
# A tight 10km threshold therefore mis-flags legitimate rural addresses (60% of the
# 10km flags fell in the 10-20km band = rural sprawl). 40km only fires on confident
# cross-region errors (an address cannot be 40km from its own eircode region).
RK_DISTANCE_KM = 40      # eircode centroid distance -> confident misplacement

# County bounding boxes (county_validator.COUNTY_BOUNDS) are the strongest wrong-town
# signal: a Kerry-county row sitting in Dublin is wrong regardless of eircode/cluster.
# The boxes are tight, so we pad them by this margin before treating "outside the box"
# as a hide signal — this spares genuine edge-of-county towns (e.g. Fingal reaches
# ~53.63N, above County Dublin's 53.50 box) while still catching cross-region matches.
COUNTY_MARGIN_DEG = 0.2

SUSPECT_CLUSTER = 50     # distinct addresses on one coord -> fallback centroid (hide)
WORKLIST_CLUSTER = 30    # distinct addresses on one coord -> worth re-geocoding

APPLY = "--apply" in sys.argv


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

    conn = psycopg2.connect(dsn)
    conn.autocommit = True  # commit each step; big updates must not share one txn
    cur = conn.cursor()
    # These aggregate/join updates exceed Supabase's default statement_timeout.
    cur.execute("SET statement_timeout = '900s'")

    print(f"Mode: {'APPLY (writing)' if APPLY else 'DRY RUN (no writes)'}")
    print(f"Thresholds: county-box margin {COUNTY_MARGIN_DEG}deg, routing-key >{RK_DISTANCE_KM}km, "
          f"suspect cluster >={SUSPECT_CLUSTER} distinct, worklist cluster >={WORKLIST_CLUSTER} distinct\n")

    # 1. Add geocode_suspect column + partial index (idempotent, committed immediately)
    if APPLY:
        cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS geocode_suspect BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_properties_geocode_suspect "
                    "ON properties (geocode_suspect) WHERE geocode_suspect = TRUE")
        print("✓ geocode_suspect column + index ensured")

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
    rk_bad AS (
        SELECT p.id
        FROM properties p
        JOIN good_keys k ON k.routing_key = p.routing_key
        WHERE p.latitude IS NOT NULL
          AND ST_Distance(
                ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(k.centroid_lon, k.centroid_lat), 4326)::geography
              ) / 1000.0 > {RK_DISTANCE_KM}
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
    suspect_ids AS (
        SELECT id FROM county_bad
        UNION SELECT id FROM rk_bad
        UNION SELECT id FROM cluster_suspect
    ),
    worklist_ids AS (
        SELECT id FROM properties WHERE latitude IS NULL
        UNION SELECT id FROM county_bad
        UNION SELECT id FROM rk_bad
        UNION SELECT id FROM cluster_worklist
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
