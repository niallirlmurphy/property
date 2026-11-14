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


# Misspelled place names in the register, checked against OpenStreetMap
# (name, name:ga, alt/old names) on 2026-11-08: OSM knows the right form and
# not the wrong one. Whole words only. Irish/English variants and look-alike
# real places (Croghan/Cloghan, Carrigane/Carrigaline...) are deliberately
# absent; see logs/spelling/. Keep this list reviewed: never generate it.
_PLACE_TYPOS = {
    "aitkens village": "aikens village",
    "asbourne": "ashbourne",
    "athone": "athlone",
    "bagnelstown": "bagenalstown",
    "baileborough": "bailieborough",
    "balbrigan": "balbriggan",
    "balgriffen": "balgriffin",
    "balinteer": "ballinteer",
    "ballaghadreen": "ballaghaderreen",
    "ballaghderreen": "ballaghaderreen",
    "ballbriggan": "balbriggan",
    "ballincurra": "ballinacurra",
    "ballingcollig": "ballincollig",
    "ballybritt": "ballybrit",
    "ballymackenny": "ballymakenny",
    "ballyraggett": "ballyragget",
    "beaumount": "beaumont",
    "beltutbet": "belturbet",
    "boreenmana": "boreenmanna",
    "buncranna": "buncrana",
    "buttervant": "buttevant",
    "cabinteeley": "cabinteely",
    "cahrlestown": "charlestown",
    "carrigtowhill": "carrigtwohill",
    "casteltroy": "castletroy",
    "castetroy": "castletroy",
    "castlecomber": "castlecomer",
    "castlenock": "castleknock",
    "castleroy": "castletroy",
    "celebridge": "celbridge",
    "cellbridge": "celbridge",
    "chaplestown": "chapelstown",
    "charlesetown": "charlestown",
    "charletown": "charlestown",
    "charlsetown": "charlestown",
    "clonakility": "clonakilty",
    "clongowan": "clongowen",
    "clongriffen": "clongriffin",
    "courttown": "courtown",
    "delganey": "delgany",
    "demense": "demesne",
    "distillary": "distillery",
    "donaghamede": "donaghmede",
    "donaghmeade": "donaghmede",
    "donneycarney": "donnycarney",
    "driminagh": "drimnagh",
    "drumshambo": "drumshanbo",
    "dun laoighaire": "dun laoghaire",
    "dun loaghaire": "dun laoghaire",
    "dunleek": "duleek",
    "dunsaughlin": "dunshaughlin",
    "dunshauglin": "dunshaughlin",
    "gerard griffin": "gerald griffin",
    "glengariff": "glengarriff",
    "glounthane": "glounthaune",
    "glouthaune": "glounthaune",
    "graiguemanagh": "graiguenamanagh",
    "harold cross": "harolds cross",
    "heynestown": "haynestown",
    "keshkerrigan": "keshcarrigan",
    "kilarney": "killarney",
    "kilcarberry": "kilcarbery",
    "kiliiney": "killiney",
    "killcullen": "kilcullen",
    "killmallock": "kilmallock",
    "killygordan": "killygordon",
    "kilorglin": "killorglin",
    "kilpeddar": "kilpedder",
    "knocknacara": "knocknacarra",
    "landsdowne": "lansdowne",
    "lehanaghbeg": "lehenaghbeg",
    "lehanaghmore": "lehenaghmore",
    "leixip": "leixlip",
    "lexlip": "leixlip",
    "magaret's": "margaret's",
    "margeret's": "margaret's",
    "margerets": "margarets",
    "marmocks": "marnocks",
    "newtownmtkennedy": "newtownmountkennedy",
    "phisboro": "phibsboro",
    "portabello": "portobello",
    "portlaois": "portlaoise",
    "portloaise": "portlaoise",
    "rathfarmham": "rathfarnham",
    "rathfarnam": "rathfarnham",
    "rathmoylon": "rathmolyon",
    "rathoath": "ratoath",
    "rochfordbridge": "rochfortbridge",
    "roscarbery": "rosscarbery",
    "shackelton": "shackleton",
    "shankhill": "shankill",
    "skibereen": "skibbereen",
    "stokestown": "strokestown",
    "tallagh": "tallaght",
    "thomandgate": "thomondgate",
    "tinahealy": "tinahely",
    "tyrrellstown": "tyrrelstown",
    "virgina": "virginia",
    "westminister": "westminster",
}
_PLACE_TYPO_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(_PLACE_TYPOS, key=len, reverse=True)) + r")\b", re.I)


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
                            or nxt.isdigit() or nxt in ('and', '&')) else 'Saint'
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
    7. Correct known place-name misspellings (_PLACE_TYPOS: Castlenock → Castleknock)
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

    result = re.sub(r'\s+', ' ', ' '.join(result_words)).strip()
    return _PLACE_TYPO_RE.sub(
        lambda m: _PLACE_TYPOS[m.group(1).lower()].title().replace("'S", "'s"), result)
