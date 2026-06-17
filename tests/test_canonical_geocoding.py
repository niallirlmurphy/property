import pytest
from datetime import datetime
from scripts.canonical_geocoding import PropertyData


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
