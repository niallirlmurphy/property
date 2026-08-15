"""
Nearest-amenity lookup for the valuation results page.

Given a geocoded (lat, lon), returns the closest DART/rail station, Luas stop
(with line), primary school and secondary school from the `amenities` table.

The amenities dataset is tiny (~167 Dublin rows) and effectively static, so it
is loaded into memory once on first use and every subsequent lookup is an
in-memory nearest-neighbour scan — no per-request database round-trip. The
dataset is Dublin-only, so callers should only surface this for Dublin
locations (see is_dublin()).
"""

import math

# Dublin bounding box (generous — covers the whole county). Used to decide
# whether the amenities section is meaningful for a given point.
DUBLIN_LAT_MIN, DUBLIN_LAT_MAX = 53.15, 53.65
DUBLIN_LON_MIN, DUBLIN_LON_MAX = -6.55, -6.00

# Module-level cache of amenity rows, populated lazily on first lookup.
# Each entry: {kind_group, name, category, latitude, longitude}. None until loaded.
_CACHE = None


def is_dublin(lat: float, lon: float) -> bool:
    return (DUBLIN_LAT_MIN <= lat <= DUBLIN_LAT_MAX
            and DUBLIN_LON_MIN <= lon <= DUBLIN_LON_MAX)


def _haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in metres."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _classify(amenity_type, category, level):
    """Map a raw amenity row to the response slots it belongs to.

    A single amenity can serve more than one slot (a 'Secondary & Primary'
    school counts as both primary and secondary). Returns a list of slot keys.
    """
    groups = []
    if amenity_type == "transport":
        cat = (category or "")
        if "DART" in cat or "Train Station" in cat or "Commuter" in cat:
            groups.append("rail")
        if "Luas" in cat:
            groups.append("luas")
    elif amenity_type == "school":
        lvl = (level or "")
        if lvl in ("Primary", "Secondary & Primary"):
            groups.append("primary_school")
        if lvl in ("Secondary", "Secondary & Primary"):
            groups.append("secondary_school")
        if lvl == "Tertiary":
            groups.append("tertiary")
    return groups


# Human labels + display order for each slot. The optional max_m caps how far a
# slot may be before it is dropped: schools/transport are always shown as the
# single nearest, but a university/college is only relevant when genuinely close
# (proximity to tertiary institutions is not a property-value amenity), so it is
# omitted unless within 2km.
_SLOT_LABELS = [
    ("rail", "DART / rail", None),
    ("luas", "Luas", None),
    ("primary_school", "Primary school", None),
    ("secondary_school", "Secondary school", None),
    ("tertiary", "University / college", 2000),
]


async def _load_cache(db):
    """Load all amenities into the module cache. Called once, lazily."""
    global _CACHE
    rows = await db.fetch(
        "SELECT amenity_type, name, category, level, latitude, longitude "
        "FROM amenities WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    )
    cache = []
    for r in rows:
        groups = _classify(r["amenity_type"], r["category"], r["level"])
        if not groups:
            continue
        cache.append({
            "groups": groups,
            "name": r["name"],
            "category": r["category"],
            "latitude": float(r["latitude"]),
            "longitude": float(r["longitude"]),
        })
    _CACHE = cache


async def get_nearby_amenities(db, lat: float, lon: float):
    """Return a list of nearest-amenity dicts, or None if not a Dublin point.

    Each dict: {kind, label, name, category, distance_m}. A slot is omitted if
    no matching amenity exists. Never raises to the caller — on any error it
    returns None so a valuation still succeeds without the section.
    """
    if not is_dublin(lat, lon):
        return None

    try:
        if _CACHE is None:
            await _load_cache(db)

        # Nearest amenity per slot, computed in memory over the cached rows.
        best = {}  # slot key -> (distance_m, row)
        for row in _CACHE:
            d = _haversine_m(lat, lon, row["latitude"], row["longitude"])
            for g in row["groups"]:
                if g not in best or d < best[g][0]:
                    best[g] = (d, row)

        results = []
        for kind, label, max_m in _SLOT_LABELS:
            if kind in best:
                d, row = best[kind]
                if max_m is not None and d > max_m:
                    continue  # too far to be a relevant amenity for this slot
                results.append({
                    "kind": kind,
                    "label": label,
                    "name": row["name"],
                    "category": row["category"],
                    "distance_m": round(d),
                })
        return results
    except Exception:
        # Amenities are a nice-to-have; never fail the valuation over them.
        return None
