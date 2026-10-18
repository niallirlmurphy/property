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


def parse_query(query: str, county: Optional[str] = None) -> "tuple[list, Optional[str]]":
    """(place names to look up, county hint) for a search query, or ([], None) when the
    query isn't a place name. "Swords, Dublin" -> (["swords"], "Dublin");
    "Limerick City" -> (["limerick city", "limerick"], None)."""
    parts = [normalize_place(p) for p in query.split(",")]
    parts = [p for p in parts if p]
    if not parts or re.search(r"\d", parts[0]) and not re.fullmatch(r"dublin \d{1,2}w?", parts[0]):
        return [], None                      # house-numbered address, not a place
    hint = county
    for p in parts[1:]:
        hint = county_of(p) or hint
    name = parts[0]
    names = [name]
    if name.endswith(" city"):
        names.append(name[: -len(" city")])
    return names, hint


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
