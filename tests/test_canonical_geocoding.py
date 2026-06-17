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
