"""Unit tests for geocoding query cleanup and Mapbox answer checks (no network/DB)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from geocode_query_prep import fold, prepare_geocode_address  # noqa: E402
from geocode_mapbox_batch import result_routing_key, street_matches  # noqa: E402

GAZETTEER = {'GALWAY': {'OUGHTERARD', 'GALWAY', 'ORANMORE'},
             'WEXFORD': {'ENNISCORTHY', 'NEW ROSS'}}


def test_fold_strips_fadas_and_apostrophes():
    assert fold("Ard Áilinn") == "ARD AILINN"
    assert fold("Saint Kineth's View") == "SAINT KINETHS VIEW"


def test_drops_near_component():
    assert prepare_geocode_address("1 Mount Anglesby, Clogheen, Near Cahir", "Tipperary") \
        == "1 Mount Anglesby, Clogheen"


def test_strips_leading_at():
    assert prepare_geocode_address("166 Grande Central, At Rockbrook, Sandyford", "Dublin") \
        == "166 Grande Central, Rockbrook, Sandyford"


def test_drops_trailing_county_components():
    assert prepare_geocode_address("30 Orchard Avenue, Rathkeale, Co. Limerick", "Limerick") \
        == "30 Orchard Avenue, Rathkeale"
    assert prepare_geocode_address("63 Domnic Street, Cork, Cork", "Cork") == "63 Domnic Street"


def test_keeps_non_trailing_county_named_town():
    # "Galway" here is the city, followed by more detail — not a trailing duplicate.
    assert prepare_geocode_address("5 Main Street, Galway, Knocknacarra", "Galway") \
        == "5 Main Street, Galway, Knocknacarra"


def test_collapses_repeated_components():
    assert prepare_geocode_address("14 The Mews, Virginia, Virginia", "Cavan") \
        == "14 The Mews, Virginia"


def test_corrects_rare_town_typo():
    assert prepare_geocode_address("22 Creig na Coille, Dughterard, Galway", "Galway", GAZETTEER) \
        == "22 Creig na Coille, Oughterard"


def test_never_corrects_postal_districts():
    gaz = {'DUBLIN': {'DRUMCONDRA DUBLIN 9', 'CRUMLIN'}}
    assert prepare_geocode_address("5 Home Farm Road, Drumcondra Dublin 3", "Dublin", gaz) \
        == "5 Home Farm Road, Drumcondra Dublin 3"
    assert prepare_geocode_address("5 Sundrive Road, Crumin", "Dublin", gaz) == "5 Sundrive Road, Crumlin"


def test_leaves_known_or_short_components_alone():
    assert prepare_geocode_address("5 The Green, Oranmore", "Galway", GAZETTEER) == "5 The Green, Oranmore"
    assert prepare_geocode_address("5 The Green, Oran", "Galway", GAZETTEER) == "5 The Green, Oran"


def test_first_component_never_altered():
    assert prepare_geocode_address("Near The Church, Oranmore", "Galway") == "Near The Church, Oranmore"


def test_result_routing_key():
    assert result_routing_key("42 Park Court, Cork, T23 R9W7, Ireland") == "T23"
    assert result_routing_key("Church Road, Cork, T12, Ireland") == "T12"
    assert result_routing_key("42 Pine Court, Blackrock, County Dublin A94 TP49, Ireland") == "A94"
    assert result_routing_key("1 Main St, Ranelagh, Dublin 6W D6W XY12, Ireland") == "D6W"
    assert result_routing_key("Main Street, Ireland") is None


def test_street_match_accepts_fada_and_saint_variants():
    assert street_matches("16 Ard Áilinn, New Ross, Wexford Y34 PX86", "16 Ard Alainn, New Ross")
    assert street_matches("69 Cúil Na Canálacht, Ballinasloe, County Galway", "69 Cuil Na Canalach, Pollboy, Ballinasloe")
    assert street_matches("3 Saint Kineth's View, Ballivor, Meath", "3 Saint Kinneths View, Ballivor")
    assert street_matches("10 Saint Bernadette's Avenue, Enniscorthy, Wexford", "10 Bernadette Avenue, Glenbrien, Enniscorthy")
    assert street_matches("7 Cius Glaisin Green, Navan, Meath C15", "7 Cois Glaisin Green, Johnstown, Navan")


def test_street_match_still_rejects_different_streets():
    assert not street_matches("4 Dublin Street, Baldoyle, County Dublin", "4 South Lotts Road, Ringsend")
    assert not street_matches("2 Killbrae, Dunfanaghy, Donegal", "2 Cill An Dun, Muineagh, Linsfort")
    assert not street_matches("166 Grange Park, Foxrock, County Dublin", "166 Grande Central, Rockbrook, Sandyford")
    # Consonant-skeleton match needs the same number AND locality.
    assert not street_matches("9 Barton Road, Rathfarnham, Dublin", "9 Burton Road, Clontarf")
    # A county is not a corroborating locality, and Y counts as a consonant.
    assert not street_matches("23 Kells Road, Dublin, D12 C7X6, Ireland", "23 Kellys Court, Kellys Row")


def test_locality_components_skip_county_and_districts():
    from geocode_query_prep import locality_components
    assert locality_components("10 The Ashes, Elmfield, Leopardstown, Co. Dublin", "Dublin") \
        == ["ELMFIELD", "LEOPARDSTOWN"]
    assert locality_components("5 Main Street, Dublin 15", "Dublin") == []
    assert locality_components("63 Domnic Street, Cork City", "Cork") == []


def test_locality_distance_rejects_same_named_estate_elsewhere():
    from geocode_query_prep import locality_centroid, locality_distance_km
    cents = {("DUBLIN", "LEOPARDSTOWN"): (53.267, -6.195)}
    addr = "10 The Ashes, Elmfield, Leopardstown"
    assert locality_centroid(addr, "Dublin", cents) == (53.267, -6.195)
    assert locality_distance_km(53.574, -6.107, addr, "Dublin", cents) > 30   # Malahide
    assert locality_distance_km(53.270, -6.190, addr, "Dublin", cents) < 1
    assert locality_distance_km(53.270, -6.190, "5 Main Street, Dublin 15", "Dublin", cents) is None


def test_locality_components_skip_roads():
    from geocode_query_prep import locality_components
    assert locality_components("5 Elm Park, Malahide Road, Artane", "Dublin") == ["ARTANE"]
