"""The one address normalizer: builds the address_normalized column (db/import.py,
scripts/sync_ppr_updates.py, scripts/normalize_addresses.py) and normalizes search
input (main.py), so a query and the row it should match always come out the same.

Lives in backend/ because Railway deploys only that directory; scripts import it
via sys.path.
"""
import html
import re
import unicodedata

# "St" is Saint unless it's the last word of its line ("11 Main St"), or the next
# word qualifies the street ("Main St Lower") or starts the town that should have
# followed a comma ("Thomas St Dublin 8"). A number never comes straight before a
# street type, so "12 St Mobhi Road" is Saint Mobhi Road.
_ST_RE = re.compile(r"\bSt\b\.?", re.I)
_STREET_QUALIFIERS = {
    "lower", "upper", "north", "south", "east", "west", "little", "great",
    "middle", "rear", "old", "new", "lr", "upr",
}
_COUNTIES = {
    "co", "county", "dublin", "carlow", "cavan", "clare", "cork", "donegal", "galway",
    "kerry", "kildare", "kilkenny", "laois", "leitrim", "limerick", "longford", "louth",
    "mayo", "meath", "monaghan", "offaly", "roscommon", "sligo", "tipperary",
    "waterford", "westmeath", "wexford", "wicklow",
}

# The dot goes after \b: in r'\bRd\.?\b' the second \b fails after "Rd." + space,
# so the dot was left behind ("Rd. X" -> "Road. X").
_STREET_TYPES = [
    (re.compile(rf"\b{abbrev}\b\.?", re.I), full) for abbrev, full in [
        ("Rd", "Road"), ("Ave", "Avenue"), ("Dr", "Drive"), ("Cl", "Close"),
        ("Ct", "Court"), ("Pk", "Park"), ("Sq", "Square"),
    ]
]

_LOWER_EXCEPTIONS = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
_UPPER_EXCEPTIONS = {'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}


def fold_accents(text: str) -> str:
    """Strip combining marks (á → a)."""
    decomposed = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in decomposed if not unicodedata.combining(c))


def _expand_st(line: str) -> str:
    def repl(m):
        rest = line[m.end():].split()
        if not rest:
            return 'Street'
        nxt = rest[0].strip('.').lower()
        word = 'Street' if (nxt in _STREET_QUALIFIERS or nxt in _COUNTIES
                            or nxt.isdigit()) else 'Saint'
        # "St.Marys" has no space after the dot
        return word if line[m.end():m.end() + 1] == ' ' else word + ' '
    return _ST_RE.sub(repl, line)


def normalize_address(address: str) -> str:
    """
    Normalize an Irish address for storage in address_normalized and for matching.

    1. Clean HTML entities (Tandy&#039;s → Tandy's)
    2. Fold Irish fadas (Slí → Sli); the raw address column keeps them for display
    3. Remove "No." prefix from house numbers; Apartment → Apt; Co. → Co
    4. St → Saint or Street (see _expand_st); Rd/Ave/Dr/Cl/Ct/Pk/Sq → full word
    5. Clean up punctuation and whitespace
    6. Title case with exceptions
    """
    if not address:
        return address

    normalized = html.unescape(address)
    normalized = normalized.replace('&amp;', '&')
    normalized = normalized.replace('&quot;', '"')
    normalized = normalized.replace('&lt;', '<')
    normalized = normalized.replace('&gt;', '>')

    normalized = fold_accents(normalized).strip()

    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r',\s*,+', ',', normalized)
    normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)
    normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)
    # "Co. Clare" and "Co Clare" are both common; store one form
    normalized = re.sub(r'\bCo\.\s*', 'Co ', normalized, flags=re.I)

    normalized = ','.join(_expand_st(line) for line in normalized.split(','))
    for pattern, full in _STREET_TYPES:
        normalized = pattern.sub(full, normalized)

    normalized = re.sub(r',\s*,', ',', normalized)
    normalized = re.sub(r'\s+,', ',', normalized)
    normalized = re.sub(r',\s+', ', ', normalized)
    normalized = normalized.strip(', ')

    result_words = []
    for i, word in enumerate(normalized.split()):
        if i == 0:
            result_words.append(word.capitalize())
        elif word in _UPPER_EXCEPTIONS:
            result_words.append(word)
        elif word.lower() in _LOWER_EXCEPTIONS:
            result_words.append(word.lower())
        else:
            result_words.append(word.capitalize())

    return re.sub(r'\s+', ' ', ' '.join(result_words)).strip()
