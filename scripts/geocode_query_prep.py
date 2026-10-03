"""
Geocoding-specific address cleanup, applied on top of address_normalized.

address_normalized exists to make exact-match *search* consistent (casing,
Rd -> Road, Co.), so it must stay stable and is NOT changed here. These steps
only shape the query sent to the geocoder, removing PPR quirks that steer
Mapbox to the wrong place:

  1. Drop direction-noise components: "Near Cahir", "Opposite Church", "Beside ..."
     (the property is *not* in Cahir; Mapbox anchors on it anyway).
  2. Strip a leading "At " ("Grande Central, At Rockbrook" -> "Rockbrook").
  3. Drop trailing county components ("Co. Limerick", "Limerick") — the caller
     appends the county column, so these only duplicate it.
  4. Collapse repeated components ("Virginia, Virginia").
  5. Correct rare town-name typos against a gazetteer built from our own data
     ("Dughterard" -> "Oughterard" when Oughterard is common in the same county).

fold() is also used to compare Mapbox's answer against our input without
tripping on fadas or apostrophes (Ard Áilinn vs ARD ALAINN, Kineth's vs KINNETHS).
"""

import difflib
import re
import unicodedata
from typing import Dict, Optional, Set

NOISE_COMPONENT_RE = re.compile(r'^(NEAR|OPPOSITE|OPP\.?|BESIDE|BEHIND|ADJACENT TO)\b', re.IGNORECASE)
LEADING_AT_RE = re.compile(r'^AT\s+', re.IGNORECASE)
COUNTY_PREFIX_RE = re.compile(r'^(CO\.?|COUNTY)\s+', re.IGNORECASE)

# A component must appear this often in a county to count as a known town.
GAZETTEER_MIN_COUNT = 100
TYPO_MIN_RATIO = 0.9
TYPO_MIN_LEN = 6


def fold(text: str) -> str:
    """Upper-case, strip accents (fadas) and apostrophes for comparisons."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"['’`]", '', text).upper()


def _is_county_component(component: str, county: Optional[str]) -> bool:
    if not county:
        return False
    return fold(COUNTY_PREFIX_RE.sub('', component)).strip(' .') == fold(county)


def correct_town(component: str, county: Optional[str],
                 gazetteer: Optional[Dict[str, Set[str]]]) -> str:
    """Replace a rare component with the single known town it's a near-miss of."""
    if not gazetteer or not county:
        return component
    known = gazetteer.get(fold(county))
    key = fold(component)
    # Never touch components with digits: "Drumcondra Dublin 3" is one string-edit
    # from the common "Drumcondra Dublin 9", but the district is data, not a typo.
    if not known or key in known or len(key) < TYPO_MIN_LEN or re.search(r'\d', key):
        return component
    matches = [t for t in known
               if abs(len(t) - len(key)) <= 2
               and difflib.SequenceMatcher(None, key, t).ratio() >= TYPO_MIN_RATIO]
    return matches[0].title() if len(matches) == 1 else component


def prepare_geocode_address(address: str, county: Optional[str] = None,
                            gazetteer: Optional[Dict[str, Set[str]]] = None) -> str:
    """Clean an (already normalised) address for use as a geocoder query."""
    parts = [p.strip() for p in address.split(',') if p.strip()]
    if not parts:
        return address

    cleaned = [parts[0]]  # first component holds number + street: never altered
    for part in parts[1:]:
        if NOISE_COMPONENT_RE.match(part):
            continue
        part = LEADING_AT_RE.sub('', part).strip()
        if not part:
            continue
        cleaned.append(correct_town(part, county, gazetteer))

    while len(cleaned) > 1 and _is_county_component(cleaned[-1], county):
        cleaned.pop()

    deduped = [cleaned[0]]
    for part in cleaned[1:]:
        if fold(part) != fold(deduped[-1]):
            deduped.append(part)
    return ', '.join(deduped)


async def load_town_gazetteer(pool) -> Dict[str, Set[str]]:
    """Known town/locality names per county: non-first address components that
    appear at least GAZETTEER_MIN_COUNT times in that county."""
    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '600s'")
        rows = await conn.fetch("""
            SELECT county, TRIM(c) AS part
            FROM properties,
                 unnest(string_to_array(address_normalized, ',')) WITH ORDINALITY AS u(c, n)
            WHERE n > 1 AND county IS NOT NULL
            GROUP BY county, TRIM(c)
            HAVING COUNT(*) >= $1
        """, GAZETTEER_MIN_COUNT)
    gazetteer: Dict[str, Set[str]] = {}
    for r in rows:
        gazetteer.setdefault(fold(r['county']), set()).add(fold(r['part']))
    return gazetteer
