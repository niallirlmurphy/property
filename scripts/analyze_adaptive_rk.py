#!/usr/bin/env python3
"""Analysis (read-only) for adaptive routing-key flagging (Task A).

The flat 40km routing-key rule in flag_bad_geocodes.py misses compact urban keys:
A96 (Dun Laoghaire) is ~5km across, so a row geocoded 12.6km away (the Howth bug)
sits well outside the key but under 40km and is never flagged. A flat *tight*
threshold instead mis-flags genuinely sprawling rural keys (A82/Kells: Nobber is
19km from centroid at its CORRECT coords).

Fix: derive a per-key threshold from each key's OWN distance distribution, then flag
eircode rows beyond it. This script computes the distributions, previews a candidate
formula, spot-checks A96 (should flag ~12.6km) and A82 (should NOT flag ~19km), and
counts how many currently-unflagged rows the rule would newly flag (to size the sweep).
No writes."""
import asyncio, os
import asyncpg
from dotenv import load_dotenv
load_dotenv("backend/.env")

# Candidate formula: threshold = clamp(p75 * MULT, FLOOR, CEIL).
# p75 (not p90/max) as the "core extent" so a key polluted with far outliers doesn't
# inflate its own threshold and hide its errors. FLOOR protects compact keys from
# noise; CEIL keeps the largest rural keys from becoming un-flaggable.
MULT, FLOOR, CEIL = 2.0, 8.0, 45.0

def threshold(p75):
    return max(FLOOR, min(CEIL, p75 * MULT))

async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=20)
    await conn.execute("SET statement_timeout='900s'")

    rows = await conn.fetch("""
        WITH d AS (
            SELECT p.routing_key AS rk,
                   ST_Distance(
                       ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,
                       ST_SetSRID(ST_MakePoint(k.centroid_lon,k.centroid_lat),4326)::geography
                   )/1000.0 AS dist_km
            FROM properties p
            JOIN routing_key_stats k ON k.routing_key = p.routing_key
            WHERE p.latitude IS NOT NULL
              AND k.geocoded_count >= 20 AND k.centroid_lat IS NOT NULL
        )
        SELECT rk,
               COUNT(*) AS n,
               percentile_cont(0.50) WITHIN GROUP (ORDER BY dist_km) AS p50,
               percentile_cont(0.75) WITHIN GROUP (ORDER BY dist_km) AS p75,
               percentile_cont(0.90) WITHIN GROUP (ORDER BY dist_km) AS p90,
               MAX(dist_km) AS maxd
        FROM d GROUP BY rk
    """)
    by_rk = {r["rk"]: r for r in rows}

    print(f"Formula: threshold = clamp(p75 * {MULT}, {FLOOR}, {CEIL}) km\n")
    print("Keys analysed:", len(rows))

    # Spot-checks
    for rk in ("A96", "A82", "D13", "H91"):
        r = by_rk.get(rk)
        if r:
            print(f"  {rk}: n={r['n']:6d} p50={r['p50']:.1f} p75={r['p75']:.1f} "
                  f"p90={r['p90']:.1f} max={r['maxd']:.1f} -> threshold={threshold(r['p75']):.1f}km")

    # Distribution of thresholds
    ths = sorted(threshold(r["p75"]) for r in rows)
    at_floor = sum(1 for t in ths if t <= FLOOR + 0.01)
    at_ceil = sum(1 for t in ths if t >= CEIL - 0.01)
    print(f"\nThresholds: min={ths[0]:.1f} median={ths[len(ths)//2]:.1f} max={ths[-1]:.1f}; "
          f"{at_floor} keys at floor({FLOOR}), {at_ceil} at ceil({CEIL})")

    # Newly-flagged count: rows beyond per-key adaptive threshold, currently NOT suspect.
    # Build a VALUES table of (rk, threshold_km) and join.
    vals = ",".join(f"('{r['rk']}',{threshold(r['p75'])})" for r in rows)
    stat = await conn.fetchrow(f"""
        WITH th(rk, tkm) AS (VALUES {vals})
        SELECT
          COUNT(*) FILTER (WHERE dist_km > tkm) AS beyond,
          COUNT(*) FILTER (WHERE dist_km > tkm AND NOT suspect) AS newly,
          COUNT(*) FILTER (WHERE dist_km > tkm AND NOT suspect AND has_ec) AS newly_ec
        FROM (
          SELECT p.geocode_suspect AS suspect,
                 (p.eircode IS NOT NULL AND p.eircode <> '') AS has_ec,
                 ST_Distance(
                     ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,
                     ST_SetSRID(ST_MakePoint(k.centroid_lon,k.centroid_lat),4326)::geography
                 )/1000.0 AS dist_km,
                 t.tkm
          FROM properties p
          JOIN routing_key_stats k ON k.routing_key = p.routing_key
          JOIN th t ON t.rk = p.routing_key
          WHERE p.latitude IS NOT NULL
            AND k.geocoded_count >= 20 AND k.centroid_lat IS NOT NULL
        ) q
    """)
    print(f"\nRows beyond adaptive threshold (total):        {stat['beyond']:,}")
    print(f"  of which NOT already geocode_suspect (new):  {stat['newly']:,}")
    print(f"  of which have an eircode (proximity-fixable): {stat['newly_ec']:,}")

    # For comparison: how many the OLD flat 40km would newly flag
    old = await conn.fetchrow("""
        SELECT COUNT(*) AS newly FROM (
          SELECT p.geocode_suspect AS suspect,
                 ST_Distance(
                     ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,
                     ST_SetSRID(ST_MakePoint(k.centroid_lon,k.centroid_lat),4326)::geography
                 )/1000.0 AS dist_km
          FROM properties p
          JOIN routing_key_stats k ON k.routing_key = p.routing_key
          WHERE p.latitude IS NOT NULL
            AND k.geocoded_count >= 20 AND k.centroid_lat IS NOT NULL
        ) q WHERE dist_km > 40 AND NOT suspect
    """)
    print(f"\n(Old flat 40km would newly flag: {old['newly']:,})")
    await conn.close()

asyncio.run(main())
