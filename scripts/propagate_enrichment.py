#!/usr/bin/env python3
"""
Copy bedrooms / property_type onto other sales of the same dwelling.

Enrichment is stored per sale, so a house enriched on its 2026 sale shows no
details on its 2014 sale (e.g. "125 Tritonville Road, Sandymount, Dublin" vs
"..., Dublin 4"). This fills those gaps.

Two sales are the same dwelling when either
  A. their first address part ("125 Tritonville Road", or "Apt 5, Block A" for
     unit-style addresses) is identical and their points are within 25 m, or
  B. they share an Eircode and the same house number.
In both cases the Eircodes must not conflict (both present and different).

Safety:
  - Only empty fields are filled; a 'address_house_guess' type may be upgraded.
  - Never touches 'address_apartment' types (high-confidence address rule).
  - Sources must agree: if a dwelling's sales disagree on bedrooms (e.g. an
    extension) or type, nothing is copied for that field.
  - Low-confidence values are never copied: house guesses, valuation-form
    bedrooms, and values that were themselves propagated.
  - Bulk-sale addresses (ranges like "1-76", "&") and addresses without a
    house number are skipped.
  - Written rows get bedrooms_source / property_type_source = 'propagated'.

One read of the table (~817k rows, few columns), then batched UPDATEs by id.

Usage:
    python3 scripts/propagate_enrichment.py           # dry run (counts + samples)
    python3 scripts/propagate_enrichment.py --apply   # write

The enrichment scripts call propagate_from() after each property they enrich,
so new findings reach the other sales straight away (two indexed lookups, no
table scan). The full run above is only needed for one-off backfills.
"""

import math
import os
import re
import sys
from collections import defaultdict

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

MAX_DIST_M = 25.0
TYPE_SOURCES_OK = {None, "web_enrichment"}          # trusted type provenance
TYPE_TARGET_OK = {None, "address_house_guess"}      # may be (over)written
BED_SOURCES_OK = {None}                             # enrichment (legacy NULL tag)

UNIT_RE = re.compile(r"^(apt|apartment|unit|flat|no|house|site)\b", re.I)
NUM_RE = re.compile(r"\b(\d+[a-z]?)\b", re.I)
BULK_RE = re.compile(r"\d\s*(-|&|to\b|and\b)\s*\d|\bunits\b|\bsites\b", re.I)


def dist_m(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
    return 6371000 * math.hypot(x, lat2 - lat1)


def text_key(addr):
    """'125 Tritonville Road' / 'apt 5, block a'; None if no usable house id."""
    if not addr or BULK_RE.search(addr):
        return None
    parts = [p.strip().lower() for p in addr.split(",") if p.strip()]
    if not parts:
        return None
    first = parts[0]
    if UNIT_RE.match(first) or re.fullmatch(r"\d+[a-z]?", first):
        if len(parts) < 2:
            return None
        first = f"{first}, {parts[1]}"
    # Needs a number and some words: "125 tritonville road"
    if not NUM_RE.search(first) or not re.search(r"[a-z]{3,}", first):
        return None
    return re.sub(r"\s+", " ", first)


def house_no(addr):
    m = NUM_RE.search(addr or "")
    return m.group(1).lower() if m else None


def eir(e):
    return (e or "").replace(" ", "").upper() or None


def _same_dwelling(src, cand):
    """src/cand: dicts with addr, eir, pt. Same rules as the full run."""
    if src["eir"] and cand["eir"] and src["eir"] != cand["eir"]:
        return False
    if src["eir"] and src["eir"] == cand["eir"] and house_no(src["addr"]) \
            and house_no(src["addr"]) == house_no(cand["addr"]):
        return True
    k = text_key(src["addr"])
    return bool(k and k == text_key(cand["addr"]) and src["pt"] and cand["pt"]
                and dist_m(src["pt"], cand["pt"]) <= MAX_DIST_M)


def propagate_from(conn, source_id):
    """Copy the source sale's bedrooms/type onto other sales of the same dwelling.

    Fills empty fields only (a house guess may be upgraded to a specific house
    type); never touches 'address_apartment' types. Commits; returns rows changed.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(address_normalized, address), eircode, latitude, longitude,
               bedrooms, property_type, property_type_source
        FROM properties WHERE id = %s
    """, (source_id,))
    row = cur.fetchone()
    if not row:
        return 0
    addr, e, lat, lon, beds, ptype, tsrc = row
    if BULK_RE.search(addr or "") or (beds is None and not ptype):
        return 0
    if tsrc not in TYPE_SOURCES_OK:
        ptype = None  # only trusted types travel
    src = dict(addr=addr, eir=eir(e), pt=(lat, lon) if lat is not None else None)

    # Candidates: within 25 m (GIST on geog) or same Eircode (eircode_norm index)
    cur.execute("""
        SELECT id, COALESCE(address_normalized, address), eircode, latitude, longitude,
               bedrooms, property_type, property_type_source
        FROM properties
        WHERE id <> %(id)s AND (
            ST_DWithin(geog, (SELECT geog FROM properties WHERE id = %(id)s), %(d)s)
            OR (%(e)s IS NOT NULL AND REPLACE(UPPER(eircode), ' ', '') = %(e)s))
    """, {"id": source_id, "d": MAX_DIST_M, "e": src["eir"]})
    changed = 0
    for cid, caddr, ce, clat, clon, cbeds, cptype, ctsrc in cur.fetchall():
        cand = dict(addr=caddr, eir=eir(ce), pt=(clat, clon) if clat is not None else None)
        if BULK_RE.search(caddr or "") or not _same_dwelling(src, cand):
            continue
        sets, params = [], []
        if beds is not None and cbeds is None:
            sets.append("bedrooms = %s, bedrooms_source = 'propagated'")
            params.append(beds)
        if ptype and ctsrc in TYPE_TARGET_OK and (
                cptype is None or (ctsrc == "address_house_guess"
                                   and ptype not in ("house", "apartment"))):
            sets.append("property_type = %s, property_type_source = 'propagated'")
            params.append(ptype)
        if sets:
            cur.execute(f"UPDATE properties SET {', '.join(sets)} WHERE id = %s",
                        params + [cid])
            changed += 1
    conn.commit()
    return changed


def main():
    apply = "--apply" in sys.argv
    if not os.getenv("DATABASE_URL"):
        load_dotenv("backend/.env")
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor(name="prop_read")  # server-side, streamed
    cur.itersize = 20000
    cur.execute("""
        SELECT id, COALESCE(address_normalized, address), eircode,
               latitude, longitude, bedrooms, bedrooms_source,
               property_type, property_type_source
        FROM properties
    """)
    rows = {}
    by_text = defaultdict(list)
    by_eir = defaultdict(list)
    for (pid, addr, e, lat, lon, beds, bsrc, ptype, tsrc) in cur:
        if BULK_RE.search(addr or ""):
            continue
        r = dict(id=pid, addr=addr, eir=eir(e),
                 pt=(lat, lon) if lat is not None and lon is not None else None,
                 beds=beds, bsrc=bsrc, ptype=ptype, tsrc=tsrc)
        rows[pid] = r
        k = text_key(addr)
        if k and r["pt"]:
            by_text[k].append(pid)
        if r["eir"] and house_no(addr):
            by_eir[(r["eir"], house_no(addr))].append(pid)
    cur.close()
    print(f"Read {len(rows):,} rows; {len(by_text):,} address keys, "
          f"{len(by_eir):,} Eircode keys")

    # Same-dwelling neighbours for each row
    siblings = defaultdict(set)
    for ids in by_text.values():
        if len(ids) < 2:
            continue
        for i, a in enumerate(ids):
            ra = rows[a]
            for b in ids[i + 1:]:
                rb = rows[b]
                if ra["eir"] and rb["eir"] and ra["eir"] != rb["eir"]:
                    continue
                if dist_m(ra["pt"], rb["pt"]) <= MAX_DIST_M:
                    siblings[a].add(b)
                    siblings[b].add(a)
    for ids in by_eir.values():
        for a in ids:
            siblings[a].update(x for x in ids if x != a)

    bed_upd, type_upd = {}, {}
    conflicts_b = conflicts_t = 0
    for pid, sibs in siblings.items():
        r = rows[pid]
        if r["beds"] is None:
            vals = {rows[s]["beds"] for s in sibs
                    if rows[s]["beds"] is not None and rows[s]["bsrc"] in BED_SOURCES_OK}
            if len(vals) == 1:
                bed_upd[pid] = vals.pop()
            elif len(vals) > 1:
                conflicts_b += 1
        if r["tsrc"] in TYPE_TARGET_OK and (r["ptype"] is None or r["tsrc"] == "address_house_guess"):
            vals = {rows[s]["ptype"] for s in sibs
                    if rows[s]["ptype"] and rows[s]["tsrc"] in TYPE_SOURCES_OK}
            # A house guess may only be upgraded to a more specific house type
            if r["tsrc"] == "address_house_guess":
                vals = {v for v in vals if v not in ("house", "apartment")}
            if len(vals) == 1:
                v = vals.pop()
                if v != r["ptype"]:
                    type_upd[pid] = v
            elif len(vals) > 1:
                conflicts_t += 1

    print(f"Bedrooms to fill:      {len(bed_upd):,}  (skipped, sources disagree: {conflicts_b:,})")
    print(f"Property type to fill: {len(type_upd):,}  (skipped, sources disagree: {conflicts_t:,})")
    sample = list(set(bed_upd) | set(type_upd))[:15]
    for pid in sample:
        print(f"  {pid}: {rows[pid]['addr'][:60]:60} beds={bed_upd.get(pid)} type={type_upd.get(pid)}")
    for pid in (117536,):
        if pid in rows:
            print(f"  check {pid}: beds={bed_upd.get(pid)} type={type_upd.get(pid)}")

    if not apply:
        print("\nDRY RUN: nothing written. Re-run with --apply.")
        return

    w = conn.cursor()
    w.execute("SET statement_timeout = '60s'")
    items = list(bed_upd.items())
    for i in range(0, len(items), 1000):
        execute_values(w, """
            UPDATE properties p SET bedrooms = v.b, bedrooms_source = 'propagated'
            FROM (VALUES %s) v(id, b) WHERE p.id = v.id AND p.bedrooms IS NULL
        """, items[i:i + 1000])
        conn.commit()
    items = list(type_upd.items())
    for i in range(0, len(items), 1000):
        execute_values(w, """
            UPDATE properties p SET property_type = v.t, property_type_source = 'propagated'
            FROM (VALUES %s) v(id, t) WHERE p.id = v.id
              AND (p.property_type IS NULL OR p.property_type_source = 'address_house_guess')
              AND p.property_type_source IS DISTINCT FROM 'address_apartment'
        """, items[i:i + 1000])
        conn.commit()
    print(f"Wrote {len(bed_upd):,} bedrooms, {len(type_upd):,} types.")
    conn.close()


if __name__ == "__main__":
    main()
