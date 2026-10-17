"""Tests for the locality-consistency rule in scripts/flag_bad_geocodes.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from flag_bad_geocodes import address_places, locality_bad_ids  # noqa: E402

NAAS = (53.2159, -6.6669)
ALLENWOOD = (53.2853, -6.8597)   # village ~15km from Naas, postal town Naas


def _town(prefix, county, town, centre, n=30, start_id=1):
    """n numbered sales clustered within ~1km of a town centre."""
    lat, lon = centre
    return [(start_id + i, county, f"{i + 1} {prefix}, {town}",
             lat + (i % 5) * 0.002, lon + (i // 5) * 0.002, False)
            for i in range(n)]


def test_address_places_strips_area_suffixes():
    assert address_places("Apt 21, the Oak, Parkview, Stepaside Dublin 18") == ["parkview", "stepaside"]
    assert address_places("7 Gortonora, Dingle, Co.kerry") == ["dingle"]
    assert address_places("14 the Orchard, Crosshaven, Co. Cork") == ["crosshaven"]


def test_address_places_skips_unnumbered_and_roads():
    assert address_places("Lobinstown, Navan, Meath") == []          # rural townland
    assert address_places("12 Main Street, Navan") == ["navan"]
    assert address_places("4 Gortnaclogh, Ballinhassig Road") == []  # road, no town


def test_flags_numbered_row_far_from_its_town():
    rows = _town("Estate", "Kildare", "Naas", NAAS)
    rows.append((999, "Kildare", "52 Listoke Pines, Naas", 53.70, -6.35, False))  # ~55km off
    assert locality_bad_ids(rows) == {999}


def test_spares_village_named_before_postal_town():
    rows = _town("Estate", "Kildare", "Naas", NAAS)
    rows += _town("Village", "Kildare", "Allenwood", ALLENWOOD, n=6, start_id=100)
    rows.append((999, "Kildare", "48 Woodlawn, Allenwood, Naas", *ALLENWOOD, False))
    assert locality_bad_ids(rows) == set()


def test_suspect_rows_do_not_set_the_reference():
    # A town whose rows are mostly already-hidden wrong answers must not drag the
    # median away and get its correct rows flagged.
    rows = _town("Estate", "Kildare", "Naas", NAAS)
    rows += [(500 + i, "Kildare", f"{i} Far, Naas", 53.70, -6.35, True) for i in range(40)]
    assert locality_bad_ids(rows) == set()


def test_needs_enough_reference_sales():
    rows = _town("Estate", "Kildare", "Naas", NAAS, n=10)
    rows.append((999, "Kildare", "52 Listoke Pines, Naas", 53.70, -6.35, False))
    assert locality_bad_ids(rows) == set()


NENAGH = (52.8619, -8.1967)


def test_unverifiable_village_relaxes_to_ceiling():
    # Toomevara has no sales of its own to check against, so a row naming it is only
    # flagged if it's beyond the 30km ceiling from Nenagh, not the 5km floor.
    rows = _town("Estate", "Tipperary", "Nenagh", NENAGH)
    rows.append((998, "Tipperary", "1 Templedowney, Toomevara, Nenagh", 52.85, -8.03, False))  # ~11km
    rows.append((999, "Tipperary", "2 Templedowney, Toomevara, Nenagh", 53.30, -7.60, False))  # ~63km
    assert locality_bad_ids(rows) == {999}
