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


def is_bare_place(query: str) -> bool:
    """A query that is only a place name: one part, no house number and no county
    ("Kenmare" yes; "Kenmare, Kerry", "Kenmare Parade, Dublin 3", "12 Main St" no)."""
    parts, hint = _query_parts(query, None)
    return (len(parts) == 1 and hint is None and not _is_numbered(parts[0])
            and county_of(parts[0]) is None)


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


# Share of a name's place sales one county needs to own it outright: Athlone
# (Westmeath 77%, Roscommon 23%) yes, "Church Road" or "Kilmore" (half in one) no.
DOMINANT_SHARE = 2 / 3
# ... and the most counties whose addresses use the name: towns on a border
# (Athlone 3, Ballinasloe 2) yes; "Main Street" (25, only Meath's clusters) no.
DOMINANT_MAX_COUNTIES = 3


def pick_dominant_place(rows: list, names: list) -> "Optional[tuple[float, float]]":
    """Fallback for a town outside the county being searched ("Ballinasloe" with the
    Dublin default): the name's busiest county, if it holds DOMINANT_SHARE of the
    sales in `places` rows for that name and the name is used in at most
    DOMINANT_MAX_COUNTIES counties. Dublin isn't preferred here: the caller
    has already tried it."""
    for name in names:
        cands = [r for r in rows if r["name"] == name]
        if not cands:
            continue
        best = max(cands, key=lambda r: r["sales"])
        if (best["counties"] <= DOMINANT_MAX_COUNTIES
                and best["sales"] >= DOMINANT_SHARE * sum(r["sales"] for r in cands)):
            return best["latitude"], best["longitude"]
    return None


# --- Searching beyond the Dublin default, and "did you mean" suggestions ---------

# A street/estate found outside Dublin (the search assumed Dublin and found nothing)
# is placed only if most of its sales sit together: share of the dominant county's
# matches that must lie within CLUSTER_RADIUS_KM of their median point.
CLUSTER_RADIUS_KM = 1.5
CLUSTER_SHARE = 0.5
_KM_PER_DEG_LAT = 111.0
_KM_PER_DEG_LON = 67.0     # at Irish latitudes (~53°N)


def _median(xs: list) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def dominant_cluster(rows: list) -> "Optional[tuple[float, float]]":
    """Centre of token-matched sales (dicts with county, latitude, longitude) found in
    any county: the median point of the busiest county's matches, if that county
    holds DOMINANT_SHARE of all matches and CLUSTER_SHARE of its own matches lie
    within CLUSTER_RADIUS_KM of the median. "Tipperstown" (33 sales, all Naas, a few
    mis-geocoded) -> Naas; "Chase" (estates all over Dublin) -> None."""
    if not rows:
        return None
    by_county: dict = {}
    for r in rows:
        by_county.setdefault(r["county"], []).append(r)
    county, cands = max(by_county.items(), key=lambda kv: len(kv[1]))
    if len(cands) < DOMINANT_SHARE * len(rows):
        return None
    lat = _median([float(r["latitude"]) for r in cands])
    lon = _median([float(r["longitude"]) for r in cands])
    near = sum(1 for r in cands
               if ((float(r["latitude"]) - lat) * _KM_PER_DEG_LAT) ** 2
               + ((float(r["longitude"]) - lon) * _KM_PER_DEG_LON) ** 2 <= CLUSTER_RADIUS_KM ** 2)
    if near < CLUSTER_SHARE * len(cands):
        return None
    return lat, lon


_HOUSE_PREFIX = re.compile(r"^(?:(?:apt|apartment|unit|flat|no)\.?\s*)?\d+[a-z]?\b[\s,]*", re.IGNORECASE)


def strip_house_number(part: str) -> str:
    """"6 Arkle Square" -> "Arkle Square", "Apt 10 Wellington Place" -> "Wellington Place"."""
    return _HOUSE_PREFIX.sub("", part.strip()).strip()


def _has_word(token: str, words: list) -> bool:
    """token in words, allowing a plural/singular or possessive ("george" ~ "georges")."""
    return any(w == token or w == token + "s" or token == w + "s" for w in words)


def street_groups(rows: list, tokens: list, limit: int = 6) -> list:
    """Group token-matched sales (dicts with address_normalized, county, latitude,
    longitude) into the distinct streets/estates the query could mean, busiest first:
    "st george" -> "Saint George's Avenue, Killiney" (Dublin), ... The label is the
    first address part holding a query word, house number removed, plus the next
    locality part; it is also the query the suggestion searches for."""
    groups: dict = {}
    for r in rows:
        if r.get("latitude") is None:
            continue
        parts = [p.strip() for p in (r["address_normalized"] or "").split(",") if p.strip()]
        # One part must hold every query word ("Saint George's Avenue"), not two parts
        # one word each ("Saint Helens Court, Lower Georges Street").
        idx = next((i for i, p in enumerate(parts)
                    if all(_has_word(t, normalize_place(strip_house_number(p)).split()) for t in tokens)), None)
        if idx is None:
            continue
        street = strip_house_number(parts[idx])
        locality = next((loc for loc in (_DUBLIN_DISTRICT.sub("", p).strip() for p in parts[idx + 1:])
                         if loc and not _COUNTY_PREFIX.match(normalize_place(loc))
                         and county_of(normalize_place(loc)) is None
                         and not re.search(r"\d", loc)), "")
        label = f"{street}, {locality}" if locality else street
        key = (normalize_place(label), r["county"])
        g = groups.setdefault(key, {"label": label, "county": r["county"], "n": 0, "lat": 0.0, "lon": 0.0})
        g["n"] += 1
        g["lat"] += float(r["latitude"])
        g["lon"] += float(r["longitude"])
    ranked = sorted(groups.values(), key=lambda g: (-g["n"], g["county"] != "Dublin", g["label"]))
    return [{"label": g["label"], "query": g["label"], "county": g["county"], "kind": "street",
             "sales": g["n"], "lat": g["lat"] / g["n"], "lon": g["lon"] / g["n"]}
            for g in ranked[:limit]]


_DUBLIN_DISTRICT = re.compile(r"\s*\bdublin\s*\d{1,2}w?$", re.IGNORECASE)

_SUGGEST_STOP = {"the", "a", "an", "of", "and", "co", "county", "no", "st", "saint", "dublin", "ireland"}
# Street-type words: too generic to match alone ("chase"), fine in a run ("the chase").
_GENERIC = {"road", "street", "avenue", "drive", "lane", "court", "close", "grove", "view",
            "square", "place", "terrace", "hill", "green", "crescent", "gardens", "garden",
            "way", "walk", "lawn", "lawns", "heights", "manor", "wood", "woods", "park",
            "chase", "mews", "rise", "row", "vale", "glen", "upper", "lower", "north",
            "south", "east", "west", "new", "old", "main", "apartments", "house"}


def query_windows(query: str) -> list:
    """Word runs (1-3 words) of each query part, house numbers and county parts
    removed, to fuzzy-match against place names: "the chase lepperdstown" ->
    ["the chase lepperdstown", "the chase", "chase lepperdstown", "chase",
    "lepperdstown", ...]. Runs of only stop words, a lone street-type word
    ("chase", "road") and runs under 4 letters are dropped."""
    parts, _hint = _query_parts(query, None)
    out: list = []
    for p in parts:
        words = normalize_place(strip_house_number(p)).split()
        for n in range(min(3, len(words)), 0, -1):
            for i in range(len(words) - n + 1):
                w = words[i:i + n]
                s = " ".join(w)
                if (len(s) >= 4 and not set(w) <= _SUGGEST_STOP
                        and not (n == 1 and w[0] in _GENERIC) and s not in out):
                    out.append(s)
        full = " ".join(words)
        if len(words) > 3 and full not in out:
            out.insert(0, full)
    return out


def parse_word_runs(query: str, county: Optional[str] = None) -> "tuple[list, Optional[str]]":
    """Multi-word runs of the query as place names, longest first, house number
    dropped: "6 the chase" -> ["the chase"]; "the chase stillorgan" -> [..., "the
    chase", ...]. For an estate name typed with extra words or a number; single words
    are left out ("saint george" must not become "george")."""
    _parts, hint = _query_parts(query, county)
    return [w for w in query_windows(query) if len(w.split()) >= 2], hint
