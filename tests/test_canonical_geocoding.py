import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from scripts.canonical_geocoding import PropertyData, initialize_cache
import psycopg2


def test_property_data_coordinates_only():
    """PropertyData stores coordinates without enrichment."""
    data = PropertyData(latitude=53.35, longitude=-6.26)

    assert data.latitude == 53.35
    assert data.longitude == -6.26
    assert data.bedrooms is None
    assert data.property_type is None


def test_property_data_with_enrichment():
    """PropertyData stores coordinates and enrichment."""
    data = PropertyData(
        latitude=53.35,
        longitude=-6.26,
        bedrooms=3,
        property_type='detached',
        last_geocoded=datetime(2025, 1, 1),
        last_enriched=datetime(2025, 2, 1)
    )

    assert data.latitude == 53.35
    assert data.longitude == -6.26
    assert data.bedrooms == 3
    assert data.property_type == 'detached'
    assert data.last_geocoded.year == 2025
    assert data.last_enriched.year == 2025


def test_property_data_validates_ireland_bounds():
    """PropertyData validates coordinates are within Ireland."""
    # Valid Ireland coordinates
    PropertyData(latitude=53.35, longitude=-6.26)  # Dublin - should work

    # Invalid latitude
    with pytest.raises(ValueError, match="outside Ireland bounds"):
        PropertyData(latitude=999, longitude=-6.26)

    # Invalid longitude
    with pytest.raises(ValueError, match="outside Ireland bounds"):
        PropertyData(latitude=53.35, longitude=-500)


def test_canonical_cache_structure():
    """Verify _canonical_cache exists and is correct type."""
    from scripts import canonical_geocoding
    assert hasattr(canonical_geocoding, '_canonical_cache')
    assert isinstance(canonical_geocoding._canonical_cache, dict)


def test_initialize_cache_success(monkeypatch):
    """Cache initialization loads properties from database."""
    # Mock database connection and cursor
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock query results: two sales of same address with same coords
    mock_cursor.fetchall.return_value = [
        {
            'address_normalized': 'main street, dublin',
            'latitude': 53.35,
            'longitude': -6.26,
            'bedrooms': 3,
            'property_type': 'detached',
            'sale_date': '2025-01-01',
            'price': 400000,
            'geocode_quality_issue': False
        },
        {
            'address_normalized': 'main street, dublin',
            'latitude': 53.35,
            'longitude': -6.26,
            'bedrooms': 3,
            'property_type': 'detached',
            'sale_date': '2024-01-01',
            'price': 380000,
            'geocode_quality_issue': False
        }
    ]

    with patch('psycopg2.connect', return_value=mock_conn):
        initialize_cache('postgresql://test')

        from scripts import canonical_geocoding
        assert 'main street, dublin' in canonical_geocoding._canonical_cache
        data = canonical_geocoding._canonical_cache['main street, dublin']
        assert data.latitude == 53.35
        assert data.longitude == -6.26
        assert data.bedrooms == 3
        assert data.property_type == 'detached'


def test_initialize_cache_db_connection_failure():
    """Cache initialization fails if database unreachable."""
    with patch('psycopg2.connect', side_effect=psycopg2.Error('Connection failed')):
        with pytest.raises(RuntimeError, match='Cannot initialize canonical cache'):
            initialize_cache('postgresql://invalid')


def test_select_canonical_coordinates_raises_on_all_null():
    """_select_canonical_coordinates raises error if all coordinates NULL."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': None, 'longitude': None, 'sale_date': '2025-01-01'},
        {'latitude': None, 'longitude': None, 'sale_date': '2024-01-01'},
    ]

    with pytest.raises(ValueError, match="No sales with coordinates found"):
        _select_canonical_coordinates(sales)


def test_select_coordinates_without_quality_issues():
    """Selects coordinates without quality issues over those with issues."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': '2025-01-01'},
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': True, 'sale_date': '2024-01-01'},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    assert lat == 53.35
    assert lon == -6.26


def test_select_coordinates_most_common():
    """Selects most common coordinate pair."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': '2025-01-01'},
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': '2024-06-01'},
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': False, 'sale_date': '2024-01-01'},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    assert lat == 53.35
    assert lon == -6.26


def test_select_coordinates_tiebreaker_by_recency():
    """Breaks ties by most recent sale_date."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': '2025-01-01'},
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': False, 'sale_date': '2024-01-01'},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    assert lat == 53.35
    assert lon == -6.26


def test_select_coordinates_lexicographic_tiebreaker():
    """Breaks final ties with lexicographic sort."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': False, 'sale_date': '2025-01-01'},
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': '2025-01-01'},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    # Should pick lower latitude (lexicographic sort)
    assert lat == 53.35
    assert lon == -6.26


def test_select_coordinates_all_have_quality_issues():
    """Handles case where all coordinates have quality issues."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': True, 'sale_date': '2025-01-01'},
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': True, 'sale_date': '2024-06-01'},
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': True, 'sale_date': '2024-01-01'},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    # Should still pick most common
    assert lat == 53.35
    assert lon == -6.26


def test_select_coordinates_handles_date_objects():
    """Handles database date objects (not just strings)."""
    from scripts.canonical_geocoding import _select_canonical_coordinates

    sales = [
        {'latitude': 53.35, 'longitude': -6.26, 'geocode_quality_issue': False, 'sale_date': date(2025, 1, 1)},
        {'latitude': 53.36, 'longitude': -6.27, 'geocode_quality_issue': False, 'sale_date': date(2024, 1, 1)},
    ]

    lat, lon = _select_canonical_coordinates(sales)
    assert lat == 53.35
    assert lon == -6.26


def test_select_enrichment_most_common_bedrooms():
    """Selects most common bedroom count."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': 3, 'property_type': None, 'sale_date': '2025-01-01', 'price': 400000},
        {'bedrooms': 3, 'property_type': None, 'sale_date': '2024-06-01', 'price': 380000},
        {'bedrooms': 4, 'property_type': None, 'sale_date': '2023-01-01', 'price': 420000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    assert enrichment['bedrooms'] == 3
    assert enrichment['property_type'] is None


def test_select_enrichment_most_common_property_type():
    """Selects most common property type."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': None, 'property_type': 'detached', 'sale_date': '2025-01-01', 'price': 400000},
        {'bedrooms': None, 'property_type': 'detached', 'sale_date': '2024-06-01', 'price': 380000},
        {'bedrooms': None, 'property_type': 'semi-detached', 'sale_date': '2023-01-01', 'price': 420000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    assert enrichment['bedrooms'] is None
    assert enrichment['property_type'] == 'detached'


def test_select_enrichment_tiebreaker_by_recency_bedrooms():
    """Breaks ties by most recent sale_date for bedrooms."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': 3, 'property_type': None, 'sale_date': '2025-01-01', 'price': 400000},
        {'bedrooms': 4, 'property_type': None, 'sale_date': '2024-01-01', 'price': 420000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    assert enrichment['bedrooms'] == 3


def test_select_enrichment_tiebreaker_by_price():
    """Breaks ties by highest price (better listing data)."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': 3, 'property_type': None, 'sale_date': '2025-01-01', 'price': 400000},
        {'bedrooms': 4, 'property_type': None, 'sale_date': '2025-01-01', 'price': 420000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    # Tied on frequency (each appears once), tied on recency (same date), so pick by price
    assert enrichment['bedrooms'] == 4


def test_select_enrichment_all_null_returns_none():
    """Returns None values if all enrichment fields are NULL."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': None, 'property_type': None, 'sale_date': '2025-01-01', 'price': 400000},
        {'bedrooms': None, 'property_type': None, 'sale_date': '2024-06-01', 'price': 380000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    assert enrichment['bedrooms'] is None
    assert enrichment['property_type'] is None


def test_select_enrichment_handles_null_prices():
    """Handles NULL prices in price tiebreaker gracefully."""
    from scripts.canonical_geocoding import _select_canonical_enrichment

    sales = [
        {'bedrooms': 3, 'property_type': None, 'sale_date': date(2025, 1, 1), 'price': None},
        {'bedrooms': 4, 'property_type': None, 'sale_date': date(2025, 1, 1), 'price': 420000},
    ]

    enrichment = _select_canonical_enrichment(sales)
    # Should pick 4 bedrooms (highest price, treating None as 0)
    assert enrichment['bedrooms'] == 4


# ============================================================================
# TASK 5: Getter Functions Tests
# ============================================================================

class TestGetterFunctions:
    """Test cache getter functions."""

    def test_get_canonical_coordinates_cache_hit(self, monkeypatch):
        """get_canonical_coordinates returns cached coordinates."""
        from scripts.canonical_geocoding import get_canonical_coordinates, _canonical_cache, PropertyData

        # Setup cache
        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26
        )

        # Should return coordinates
        coords = get_canonical_coordinates('main street, dublin')
        assert coords == (53.35, -6.26)

    def test_get_canonical_coordinates_cache_miss(self):
        """get_canonical_coordinates returns None for missing address."""
        from scripts.canonical_geocoding import get_canonical_coordinates, _canonical_cache

        _canonical_cache.clear()

        # Should return None
        coords = get_canonical_coordinates('nonexistent address')
        assert coords is None

    def test_get_canonical_property_data_full_hit(self):
        """get_canonical_property_data returns full PropertyData."""
        from scripts.canonical_geocoding import get_canonical_property_data, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type='detached'
        )

        # Should return PropertyData
        data = get_canonical_property_data('main street, dublin')
        assert data is not None
        assert data.latitude == 53.35
        assert data.longitude == -6.26
        assert data.bedrooms == 3
        assert data.property_type == 'detached'

    def test_get_canonical_property_data_partial_enrichment(self):
        """get_canonical_property_data returns PropertyData with partial enrichment."""
        from scripts.canonical_geocoding import get_canonical_property_data, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type=None  # No property type
        )

        data = get_canonical_property_data('main street, dublin')
        assert data is not None
        assert data.bedrooms == 3
        assert data.property_type is None

    def test_get_canonical_property_data_cache_miss(self):
        """get_canonical_property_data returns None for missing address."""
        from scripts.canonical_geocoding import get_canonical_property_data, _canonical_cache

        _canonical_cache.clear()

        data = get_canonical_property_data('nonexistent address')
        assert data is None

    def test_should_geocode_returns_true_when_not_cached(self):
        """should_geocode returns True when address not in cache."""
        from scripts.canonical_geocoding import should_geocode, _canonical_cache

        _canonical_cache.clear()

        # Address not in cache → should geocode
        assert should_geocode('new address') is True

    def test_should_geocode_returns_false_when_cached(self):
        """should_geocode returns False when address in cache with coordinates."""
        from scripts.canonical_geocoding import should_geocode, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26
        )

        # Address in cache → should NOT geocode
        assert should_geocode('main street, dublin') is False

    def test_should_enrich_returns_true_when_no_enrichment_data(self):
        """should_enrich returns True when address has no enrichment."""
        from scripts.canonical_geocoding import should_enrich, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=None,
            property_type=None
        )

        # No enrichment data → should enrich
        assert should_enrich('main street, dublin') is True

    def test_should_enrich_returns_false_when_has_enrichment(self):
        """should_enrich returns False when address has enrichment data."""
        from scripts.canonical_geocoding import should_enrich, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type='detached'
        )

        # Has enrichment → should NOT enrich
        assert should_enrich('main street, dublin') is False

    def test_should_enrich_returns_true_even_with_partial_enrichment(self):
        """should_enrich returns True if ANY enrichment field is missing."""
        from scripts.canonical_geocoding import should_enrich, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type=None  # Missing property_type
        )

        # Partial enrichment → should enrich
        assert should_enrich('main street, dublin') is True

    def test_should_enrich_returns_true_when_not_cached(self):
        """should_enrich returns True when address not in cache."""
        from scripts.canonical_geocoding import should_enrich, _canonical_cache

        _canonical_cache.clear()

        # Not in cache → should enrich
        assert should_enrich('nonexistent address') is True


# ============================================================================
# TASK 6: Setter Functions Tests
# ============================================================================

class TestSetterFunctions:
    """Test cache setter functions."""

    def test_cache_coordinates_creates_new_entry(self):
        """cache_coordinates creates new PropertyData if address not in cache."""
        from scripts.canonical_geocoding import cache_coordinates, _canonical_cache

        _canonical_cache.clear()

        # Cache new coordinates
        cache_coordinates('new address', 53.35, -6.26)

        # Should be in cache now
        assert 'new address' in _canonical_cache
        assert _canonical_cache['new address'].latitude == 53.35
        assert _canonical_cache['new address'].longitude == -6.26

    def test_cache_coordinates_updates_existing_entry(self):
        """cache_coordinates updates coordinates for existing address."""
        from scripts.canonical_geocoding import cache_coordinates, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.30,
            longitude=-6.20,
            bedrooms=3
        )

        # Update coordinates
        cache_coordinates('main street, dublin', 53.35, -6.26)

        # Should be updated
        assert _canonical_cache['main street, dublin'].latitude == 53.35
        assert _canonical_cache['main street, dublin'].longitude == -6.26
        # Enrichment should persist
        assert _canonical_cache['main street, dublin'].bedrooms == 3

    def test_cache_enrichment_data_creates_new_entry_with_coordinates(self):
        """cache_enrichment_data creates new entry if address not cached but has coords."""
        from scripts.canonical_geocoding import cache_enrichment_data, _canonical_cache

        _canonical_cache.clear()

        # Cache enrichment (without coordinates - should handle gracefully)
        cache_enrichment_data('new address', 3, 'detached')

        # Should be in cache (with default/placeholder coordinates)
        assert 'new address' in _canonical_cache
        assert _canonical_cache['new address'].bedrooms == 3
        assert _canonical_cache['new address'].property_type == 'detached'

    def test_cache_enrichment_data_updates_existing_entry(self):
        """cache_enrichment_data updates enrichment for existing address."""
        from scripts.canonical_geocoding import cache_enrichment_data, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=None,
            property_type=None
        )

        # Cache enrichment
        cache_enrichment_data('main street, dublin', 4, 'semi-detached')

        # Should be updated
        assert _canonical_cache['main street, dublin'].bedrooms == 4
        assert _canonical_cache['main street, dublin'].property_type == 'semi-detached'
        # Coordinates should persist
        assert _canonical_cache['main street, dublin'].latitude == 53.35

    def test_cache_enrichment_data_handles_partial_updates(self):
        """cache_enrichment_data updates only provided fields."""
        from scripts.canonical_geocoding import cache_enrichment_data, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type='detached'
        )

        # Update only bedrooms
        cache_enrichment_data('main street, dublin', 4, None)

        # Bedrooms updated, property_type unchanged
        assert _canonical_cache['main street, dublin'].bedrooms == 4
        assert _canonical_cache['main street, dublin'].property_type == 'detached'

    def test_cache_enrichment_data_with_none_values(self):
        """cache_enrichment_data treats None as 'no update' for existing entries."""
        from scripts.canonical_geocoding import cache_enrichment_data, _canonical_cache, PropertyData

        _canonical_cache.clear()
        _canonical_cache['main street, dublin'] = PropertyData(
            latitude=53.35,
            longitude=-6.26,
            bedrooms=3,
            property_type='detached'
        )

        # Pass None for both - should not change existing values
        cache_enrichment_data('main street, dublin', None, None)

        # Should be unchanged (None means "don't update")
        assert _canonical_cache['main street, dublin'].bedrooms == 3
        assert _canonical_cache['main street, dublin'].property_type == 'detached'

    def test_cache_coordinates_validates_ireland_bounds(self):
        """cache_coordinates validates coordinates are within Ireland."""
        from scripts.canonical_geocoding import cache_coordinates

        # Invalid latitude should raise error
        with pytest.raises(ValueError, match="outside Ireland bounds"):
            cache_coordinates('bad address', 999, -6.26)

        # Invalid longitude should raise error
        with pytest.raises(ValueError, match="outside Ireland bounds"):
            cache_coordinates('bad address', 53.35, -500)
