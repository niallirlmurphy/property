"""Unit tests for the shared address normalizer (no network/DB)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from address_normalize import normalize_address  # noqa: E402


def test_st_after_number_is_saint():
    assert normalize_address("12 St Mobhi Road") == "12 Saint Mobhi Road"
    assert normalize_address("12 ST. MOBHI ROAD, GLASNEVIN, DUBLIN 9") == \
        "12 Saint Mobhi Road, Glasnevin, Dublin 9"


def test_saint_typed_in_full_matches_abbreviation():
    assert normalize_address("12 saint mobhi road") == normalize_address("12 St. Mobhi Rd")


def test_st_at_end_of_line_is_street():
    assert normalize_address("11 Main St") == "11 Main Street"
    assert normalize_address("11 MAIN ST., NAVAN, CO MEATH") == "11 Main Street, Navan, Co Meath"


def test_st_before_qualifier_or_town_is_street():
    assert normalize_address("4 Main St Lower, Tuam") == "4 Main Street Lower, Tuam"
    assert normalize_address("5 Dorset St Upper") == "5 Dorset Street Upper"
    assert normalize_address("21 Thomas St Dublin 8") == "21 Thomas Street Dublin 8"
    assert normalize_address("3 Main St Co Cork") == "3 Main Street Co Cork"


def test_st_starting_later_line_is_saint():
    assert normalize_address("Apt 4, St. Helens, Booterstown") == "Apt 4, Saint Helens, Booterstown"
    assert normalize_address("9 The Haven, St Mobhi Boithirin") == "9 the Haven, Saint Mobhi Boithirin"


def test_st_without_space_after_dot():
    assert normalize_address("2 St.Marys Road") == "2 Saint Marys Road"


def test_other_abbreviations_drop_their_dot():
    assert normalize_address("3 Ashfield Rd. Ranelagh") == "3 Ashfield Road Ranelagh"
    assert normalize_address("7 Grove Ave., Malahide") == "7 Grove Avenue, Malahide"


def test_spelled_out_words_are_unchanged():
    assert normalize_address("1 Saint Agnes Road") == "1 Saint Agnes Road"
    assert normalize_address("1 Street Lane") == "1 Street Lane"
    assert normalize_address("2 Stoney Road") == "2 Stoney Road"


def test_county_dot_dropped():
    assert normalize_address("Shannagh, Raphoe, Co. Donegal") == "Shannagh, Raphoe, Co Donegal"
    assert normalize_address("Main Street, Co.Cork") == normalize_address("Main Street, Co Cork")


def test_existing_rules_kept():
    assert normalize_address("No. 5 Apartment 2, Slí an Chnocáin") == "5 Apt 2, Sli an Chnocain"
    assert normalize_address("Tandy&#039;s Lane,, Lucan") == "Tandy's Lane, Lucan"
    assert normalize_address("") == ""
