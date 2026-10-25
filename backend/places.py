"""Place-name lookup from our own sales data: towns, suburbs and localities ->
centre point. Replaces Nominatim, which ranked same-named roads above towns
("Swords, Dublin" -> Swords Road, Whitehall).

The `places` table is built by scripts/build_places.py from the comma-separated
parts of geocoded PPR addresses ("12 Main St, Swords, Co. Dublin" -> "swords").
This module holds the pure logic shared by the builder and the backend.
"""
import re
import unicodedata
from typing import Optional

COUNTIES = [
    "Carlow", "Cavan", "Clare", "Cork", "Donegal", "Dublin", "Galway", "Kerry",
    "Kildare", "Kilkenny", "Laois", "Leitrim", "Limerick", "Longford", "Louth",
    "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon", "Sligo", "Tipperary",
    "Waterford", "Westmeath", "Wexford", "Wicklow",
]
_COUNTY_BY_NORM = {c.lower(): c for c in COUNTIES}
_COUNTY_PREFIX = re.compile(r"^(co|county)\s+")
_COUNTY_SUFFIX = re.compile(r"\s(co|county)\s(" + "|".join(_COUNTY_BY_NORM) + r")$")


def normalize_place(s: str) -> str:
    """Lower-case, fadas folded, apostrophes dropped, other punctuation to spaces:
    "Dún Laoghaire" / "dun-laoghaire" -> "dun laoghaire", "Harold's Cross" -> "harolds cross"."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"['’]", "", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


def county_of(part: str) -> Optional[str]:
    """The county a normalized address/query part names ("co dublin", "county cork",
    "galway"), else None."""
    return _COUNTY_BY_NORM.get(_COUNTY_PREFIX.sub("", part))


def address_place_names(address: str) -> set:
    """Candidate place names in an address: every part after the first (which holds
    the house/unit), except "Co. X" / "County X" parts."""
    names = set()
    for part in address.split(",")[1:]:
        n = normalize_place(part)
        if len(n) >= 3 and not _COUNTY_PREFIX.match(n):
            names.add(n)
    return names


def _query_parts(query: str, county: Optional[str]) -> "tuple[list, Optional[str]]":
    """Normalized comma parts with county parts and trailing "co X" removed, and the
    county hint they give. "Redhills Co Cavan" -> (["redhills"], "Cavan")."""
    hint = county
    parts = []
    for p in (normalize_place(p) for p in query.split(",")):
        m = _COUNTY_SUFFIX.search(p)
        if m:
            hint = _COUNTY_BY_NORM[m.group(2)]
            p = p[:m.start()].strip()
        c = county_of(p) if parts else None    # a first part named "Carlow" is the town
        if c:
            hint = c
        elif p:
            parts.append(p)
    return parts, hint


def _is_numbered(part: str) -> bool:
    return bool(re.search(r"\d", part)) and not re.fullmatch(r"dublin \d{1,2}w?", part)


def parse_query(query: str, county: Optional[str] = None) -> "tuple[list, Optional[str]]":
    """(place names to look up, county hint) for a search query, or ([], None) when the
    query isn't a place name. "Swords, Dublin" -> (["swords"], "Dublin");
    "Limerick City" -> (["limerick city", "limerick"], None)."""
    parts, hint = _query_parts(query, county)
    if not parts or _is_numbered(parts[0]):
        return [], None                      # house-numbered address, not a place
    name = parts[0]
    names = [name]
    if name.endswith(" city"):
        names.append(name[: -len(" city")])
    return names, hint


def parse_localities(query: str, county: Optional[str] = None) -> "tuple[list, Optional[str]]":
    """The later parts of a query, as place names to fall back on when the first part
    can't be placed: "Drumlaney, Redhills" -> (["redhills"], None). The backend tries
    these last, after street-level lookups, so "Main Street, Tuam" stays on the street."""
    parts, hint = _query_parts(query, county)
    return [p for p in parts[1:] if not _is_numbered(p)], hint


def pick_place(rows: list, names: list, hint: Optional[str]) -> "Optional[tuple[float, float]]":
    """Choose among `places` rows (dicts with name, county, latitude, longitude, sales,
    counties). Earlier names win ("limerick city" before "limerick"). With a county hint
    only that county counts. Without one, Dublin wins (the site's default county), else
    a name used in a single county ("Tuam"); names shared across counties ("Main
    Street") return None and go to Mapbox."""
    for name in names:
        cands = [r for r in rows if r["name"] == name]
        if hint:
            cands = [r for r in cands if r["county"].lower() == hint.lower()]
        else:
            cands = ([r for r in cands if r["county"] == "Dublin"]
                     or [r for r in cands if r["counties"] == 1])
        if cands:
            best = max(cands, key=lambda r: r["sales"])
            return best["latitude"], best["longitude"]
    return None
