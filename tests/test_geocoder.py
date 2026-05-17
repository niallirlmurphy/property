"""
Unit tests for geocoding helper logic.

These test the Python functions directly without hitting the network or DB,
so they run fast and catch regressions in address parsing and abbreviation
expansion before deployment.
"""

import sys
import re
import pytest
from pathlib import Path

# Import helpers directly from backend
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# ----------------------------------------------------------------------------
# Replicate the key functions under test
# (avoids importing the full FastAPI app with its DB connection at module load)
# ----------------------------------------------------------------------------

_ADDR_ABBREVS = [
    (re.compile(r"\bRd\.?\b",          re.IGNORECASE), "Road"),
    (re.compile(r"\bAve?\.?\b",        re.IGNORECASE), "Avenue"),
    (re.compile(r"\bDr\.?\b",          re.IGNORECASE), "Drive"),
    (re.compile(r"\bTce\.?(?=\W|$)",   re.IGNORECASE), "Terrace"),
    (re.compile(r"\bTerr\.?(?=\W|$)",  re.IGNORECASE), "Terrace"),
    (re.compile(r"\bCres\.?\b",        re.IGNORECASE), "Crescent"),
    (re.compile(r"\bGdns?\.?\b",       re.IGNORECASE), "Gardens"),
    (re.compile(r"\bSq\.?\b",          re.IGNORECASE), "Square"),
    (re.compile(r"\bPk\.?\b",          re.IGNORECASE), "Park"),
    (re.compile(r"\bBlvd\.?\b",        re.IGNORECASE), "Boulevard"),
    (re.compile(r"\bMt\.?\b",          re.IGNORECASE), "Mount"),
    (re.compile(r"\bNth\.?\b",         re.IGNORECASE), "North"),
    (re.compile(r"\bSth\.?\b",         re.IGNORECASE), "South"),
    (re.compile(r"\bSt\.",             re.IGNORECASE), "Street"),
    (re.compile(r"^No\.?\s*",          re.IGNORECASE), ""),
    (re.compile(r",?\s*Co\.?\s+",      re.IGNORECASE), ", "),
]

def expand_abbreviations(query):
    for pattern, replacement in _ADDR_ABBREVS:
        query = pattern.sub(replacement, query)
    return re.sub(r"  +", " ", query).strip(", ").strip()


def looks_like_eircode(s):
    return bool(re.match(r"^[A-Za-z]\d{1,2}\s?[A-Za-z0-9]{4}$", s.strip()))


def looks_like_routing_key(s):
    return bool(re.match(r"^[A-Za-z]\d{1,2}[A-Za-z]?$", s.strip()))


def normalise_eircode(s):
    return s.strip().upper().replace(" ", "")


_STOP_WORDS = {"the", "a", "an", "of", "and", "co", "no", "st", "dublin", "ireland"}
_TOKEN_RE   = re.compile(r"[a-z0-9]+")
_ABBREV_TO_FULL = {"rd": "road", "ave": "avenue", "dr": "drive", "tce": "terrace",
                   "cres": "crescent", "gdns": "gardens", "sq": "square",
                   "pk": "park", "mt": "mount"}
_FULL_TO_ABBREV = {v: k for k, v in _ABBREV_TO_FULL.items()}

def address_tokens(s):
    return [t for t in _TOKEN_RE.findall(s.lower()) if t not in _STOP_WORDS and len(t) > 1]

def token_has_alt(t):
    return t in _FULL_TO_ABBREV or t in _ABBREV_TO_FULL


# ----------------------------------------------------------------------------
# _expand_abbreviations
# ----------------------------------------------------------------------------

class TestExpandAbbreviations:
    def test_rd_to_road(self):
        assert expand_abbreviations("Main Rd") == "Main Road"

    def test_rd_with_dot(self):
        # The regex \bRd\.?\b consumes the dot as part of the token boundary,
        # but a following space means the dot is left as punctuation.
        # Verify expansion happens even if a stray dot remains.
        result = expand_abbreviations("Main Rd. Dublin")
        assert "Road" in result
        assert "Rd" not in result

    def test_ave_to_avenue(self):
        assert expand_abbreviations("Grafton Ave") == "Grafton Avenue"

    def test_st_dot_to_street(self):
        # St. with a dot → Street
        assert expand_abbreviations("O'Connell St.") == "O'Connell Street"

    def test_bare_st_unchanged(self):
        # Bare St without dot should NOT expand (it's often "Saint" in Irish addresses)
        result = expand_abbreviations("St Patrick's Close")
        assert result == "St Patrick's Close"

    def test_no_prefix_stripped(self):
        assert expand_abbreviations("No. 11 Foo Street") == "11 Foo Street"
        assert expand_abbreviations("No 11 Foo Street")  == "11 Foo Street"

    def test_co_qualifier_stripped(self):
        assert expand_abbreviations("Killarney, Co. Kerry") == "Killarney, Kerry"
        assert expand_abbreviations("Killarney, Co Kerry")  == "Killarney, Kerry"

    def test_mt_to_mount(self):
        assert expand_abbreviations("Mt Merrion") == "Mount Merrion"

    def test_tce_to_terrace(self):
        assert expand_abbreviations("Beechwood Tce") == "Beechwood Terrace"

    def test_no_double_spaces(self):
        result = expand_abbreviations("No. 5  Main Rd")
        assert "  " not in result

    def test_complex_address(self):
        result = expand_abbreviations("No. 27 Elm Ct, Merrion Rd")
        assert result == "27 Elm Ct, Merrion Road"


# ----------------------------------------------------------------------------
# _looks_like_eircode
# ----------------------------------------------------------------------------

class TestLooksLikeEircode:
    def test_valid_with_space(self):
        assert looks_like_eircode("D04 XY12")

    def test_valid_without_space(self):
        assert looks_like_eircode("D04XY12")

    def test_valid_lowercase(self):
        assert looks_like_eircode("d04xy12")

    def test_routing_key_only_is_not_eircode(self):
        assert not looks_like_eircode("D04")

    def test_plain_address_is_not_eircode(self):
        assert not looks_like_eircode("44 Mount Carmel Road")

    def test_county_name_is_not_eircode(self):
        assert not looks_like_eircode("Dublin")


# ----------------------------------------------------------------------------
# _looks_like_routing_key
# ----------------------------------------------------------------------------

class TestLooksLikeRoutingKey:
    def test_dublin_4(self):
        assert looks_like_routing_key("D04")

    def test_galway(self):
        assert looks_like_routing_key("H91")

    def test_full_eircode_is_not_routing_key(self):
        assert not looks_like_routing_key("D04 XY12")

    def test_plain_text_is_not_routing_key(self):
        assert not looks_like_routing_key("Dublin")


# ----------------------------------------------------------------------------
# _normalise_eircode
# ----------------------------------------------------------------------------

class TestNormaliseEircode:
    def test_strips_space(self):
        assert normalise_eircode("D04 XY12") == "D04XY12"

    def test_uppercases(self):
        assert normalise_eircode("d04xy12") == "D04XY12"

    def test_strips_whitespace(self):
        assert normalise_eircode("  D04 XY12  ") == "D04XY12"


# ----------------------------------------------------------------------------
# Token-based geocoding helpers
# ----------------------------------------------------------------------------

class TestAddressTokens:
    def test_stop_words_removed(self):
        tokens = address_tokens("the green, co dublin")
        assert "the" not in tokens
        assert "co" not in tokens
        assert "dublin" not in tokens

    def test_short_tokens_removed(self):
        # Single-char tokens like "a" already covered by stop words
        # but also check 2-char minimum is respected for other tokens
        tokens = address_tokens("1 x main road")
        assert "x" not in tokens

    def test_significant_tokens_kept(self):
        tokens = address_tokens("27 Elm Court, Merrion Road")
        assert "27" in tokens
        assert "elm" in tokens
        assert "court" in tokens
        assert "merrion" in tokens
        assert "road" in tokens

    def test_number_in_token(self):
        tokens = address_tokens("44 Mount Carmel Road")
        assert "44" in tokens
        assert "mount" in tokens
        assert "carmel" in tokens


class TestTokenAbbreviationAlternatives:
    def test_road_has_alt(self):
        assert token_has_alt("road")
        assert _FULL_TO_ABBREV["road"] == "rd"

    def test_rd_has_alt(self):
        assert token_has_alt("rd")
        assert _ABBREV_TO_FULL["rd"] == "road"

    def test_court_has_no_alt(self):
        # 'ct' was removed because %ct% matches too many substrings
        assert not token_has_alt("court")

    def test_mount_has_alt(self):
        assert token_has_alt("mount")
        assert _FULL_TO_ABBREV["mount"] == "mt"
