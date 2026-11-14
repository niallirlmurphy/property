"""Pure helpers behind the search fallbacks in backend/main.py (no DB needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/unused")
from main import _dublin_was_assumed, _find_eircode, _split_postal_address  # noqa: E402


def test_split_postal_address_strips_eircode_and_county():
    assert _split_postal_address("1 wellington place, trim, county meath, c15v6rt") == \
        ("1 wellington place, trim", "C15V6RT", "Meath")
    assert _split_postal_address("26 the chase, stillorgan, dublin, a94 fk68") == \
        ("26 the chase, stillorgan, dublin", "A94FK68", None)
    assert _split_postal_address("12 Main St, Co. Cork") == ("12 Main St", None, "Cork")


def test_split_postal_address_finds_eircode_anywhere():
    assert _split_postal_address(
        "9 st patrick's terrace, ballalease, donabate, co. dublin, k36 cf98, ireland") == \
        ("9 st patrick's terrace, ballalease, donabate", "K36CF98", "Dublin")
    assert _split_postal_address("K36 CF98, 9 St Patricks Terrace, Donabate") == \
        ("9 St Patricks Terrace, Donabate", "K36CF98", None)


def test_find_eircode_anywhere_in_query():
    assert _find_eircode("a92ek06 laytown") == ("A92EK06", "laytown")
    assert _find_eircode("laytown A92 EK06 meath") == ("A92EK06", "laytown, meath")
    assert _find_eircode("6 pelletstown avenue, dublin 15, d15c6he") == ("D15C6HE", "6 pelletstown avenue, dublin 15")
    assert _find_eircode("D6W Y123 rathfarnham") == ("D6WY123", "rathfarnham")


def test_find_eircode_ignores_road_numbers_and_plain_words():
    for q in ["N11 Dart station", "12 R132 Road, Swords", "Dublin 15", "1316857nh",
              "Apt 12 Block B, Main Street", "M50 Business Park"]:
        assert _find_eircode(q) == (None, q), q


def test_split_postal_address_leaves_bare_eircodes_and_street_names():
    assert _split_postal_address("F91P7Y7") == ("F91P7Y7", None, None)
    assert _split_postal_address("D6W Y123") == ("D6W Y123", None, None)
    assert _split_postal_address("25 Clare Road") == ("25 Clare Road", None, None)


def test_dublin_only_assumed_when_nobody_chose_it():
    assert _dublin_was_assumed("tipperstown", None)
    assert not _dublin_was_assumed("tipperstown", "Dublin")
    assert not _dublin_was_assumed("Swords, Dublin", None)
    assert not _dublin_was_assumed("Main St, Tuam, Co Galway", None)


def test_place_typos_corrected():
    from address_normalize import normalize_address as n
    assert n("12 Main St, Castlenock, Dublin 15") == "12 Main Street, Castleknock, Dublin 15"
    assert n("Apt 3, Harold Cross Road, Dublin 6W").startswith("Apt 3, Harolds Cross Road")
    assert n("2 Saint Georges Avenue, Kiliiney") == "2 Saint Georges Avenue, Killiney"
    assert n("Rathoath Road, Finglas") == "Ratoath Road, Finglas"
    assert (n("Apt 4 Charletown Centre, Charlsetown Place, St Margeret's Rd, Finglas")
            == "Apt 4 Charlestown Centre, Charlestown Place, Saint Margaret's Road, Finglas")
    assert n("Cahrlestown Centre, St Magaret's Road") == "Charlestown Centre, Saint Margaret's Road"
    assert n("12 St Margerets Road, Finglas") == "12 Saint Margarets Road, Finglas"


def test_real_lookalike_places_untouched():
    from address_normalize import normalize_address as n
    for a in ["Croghan, Offaly", "Carrigaloe, Cobh", "Kinsalebeg, Youghal", "Bagnalstown, Carlow",
              "Ballincrokig, Cork", "Milltown Malbay, Clare", "10 Tallaght Road"]:
        assert n(a) == a


def test_st_before_and_is_street():
    from address_normalize import normalize_address as n
    assert n("Clarence St and Georges Place, Dun Laoghaire") == "Clarence Street and Georges Place, Dun Laoghaire"
    assert n("5 St Mobhi Road, Dublin 9") == "5 Saint Mobhi Road, Dublin 9"
