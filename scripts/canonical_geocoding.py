#!/usr/bin/env python3
"""
Canonical geocoding and enrichment caching module.

Provides in-memory cache for property coordinates and enrichment data
to ensure consistency across multiple sales of the same address.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Optional, Tuple, List
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from collections import defaultdict


@dataclass
class PropertyData:
    """Property coordinate and enrichment data."""
    latitude: float
    longitude: float
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    last_geocoded: Optional[datetime] = None
    last_enriched: Optional[datetime] = None

    def __post_init__(self):
        """Validate coordinate ranges for Ireland."""
        if not (51.4 <= self.latitude <= 55.5):
            raise ValueError(f"Latitude {self.latitude} outside Ireland bounds (51.4-55.5°N)")
        if not (-10.7 <= self.longitude <= -5.4):
            raise ValueError(f"Longitude {self.longitude} outside Ireland bounds (-10.7--5.4°W)")


# Global in-memory cache: address_normalized -> PropertyData
_canonical_cache: Dict[str, PropertyData] = {}


def initialize_cache(database_url: str) -> None:
    """
    Load all property coordinates and enrichment into memory cache.

    Args:
        database_url: PostgreSQL connection string

    Raises:
        RuntimeError: If database connection fails
    """
    global _canonical_cache
    _canonical_cache = {}

    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        raise RuntimeError(
            f"Cannot initialize canonical cache: database connection failed. "
            f"Refusing to run with empty cache. Error: {e}"
        )

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch all properties with coordinates
        # This is a coordinate cache; enrichment will be added by enrichment scripts
        cur.execute("""
            SELECT
                address_normalized,
                latitude,
                longitude,
                bedrooms,
                property_type,
                sale_date,
                price,
                geocode_quality_issue
            FROM properties
            WHERE address_normalized IS NOT NULL
              AND latitude IS NOT NULL
            ORDER BY address_normalized, sale_date DESC
        """)

        rows = cur.fetchall()

        # Group by address_normalized
        by_address: Dict[str, List[dict]] = defaultdict(list)
        for row in rows:
            by_address[row['address_normalized']].append(row)

        # Apply selection strategies for each address
        for address_normalized, sales in by_address.items():
            canonical_coords = _select_canonical_coordinates(sales)
            canonical_enrichment = _select_canonical_enrichment(sales)

            _canonical_cache[address_normalized] = PropertyData(
                latitude=canonical_coords[0],
                longitude=canonical_coords[1],
                bedrooms=canonical_enrichment['bedrooms'],
                property_type=canonical_enrichment['property_type']
            )

        # Log memory usage
        cache_size = sys.getsizeof(_canonical_cache)
        print(f"Cache initialized: {len(_canonical_cache)} addresses, "
              f"{cache_size / 1024 / 1024:.1f} MB")

    finally:
        conn.close()


def _select_canonical_coordinates(sales: List[dict]) -> Tuple[float, float]:
    """
    Select canonical coordinates using hybrid strategy.

    Algorithm:
    1. Filter to coordinates WITHOUT geocode_quality_issue
    2. If filtered list non-empty, use it; else use all coordinates
    3. Group by (lat, lon) and count occurrences
    4. Pick most common coordinate pair
    5. Tiebreaker: most recent sale_date
    6. Final tiebreaker: lexicographic sort on (lat, lon)

    Args:
        sales: List of sale dicts with lat/lon/quality/date fields

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If no sales with coordinates found
    """
    # Filter to sales with non-NULL coordinates
    sales_with_coords = [s for s in sales if s['latitude'] is not None and s['longitude'] is not None]

    if not sales_with_coords:
        raise ValueError("No sales with coordinates found")

    # Step 1: Filter to coordinates without quality issues
    candidates = [s for s in sales_with_coords if not s.get('geocode_quality_issue', False)]

    # Step 2: If all have quality issues, use all coordinates
    if not candidates:
        candidates = sales_with_coords

    # Step 3: Group by (lat, lon) and count occurrences
    coord_groups = {}
    for sale in candidates:
        coord_key = (sale['latitude'], sale['longitude'])
        if coord_key not in coord_groups:
            coord_groups[coord_key] = []
        coord_groups[coord_key].append(sale)

    # Step 4: Pick most common coordinate pair
    most_common_count = max(len(group) for group in coord_groups.values())
    most_common_coords = [
        (coords, group) for coords, group in coord_groups.items()
        if len(group) == most_common_count
    ]

    # Step 5: Tiebreaker by most recent sale_date
    if len(most_common_coords) > 1:
        def get_max_date(group):
            """Get max date from group, handling both date objects and strings."""
            dates = [s['sale_date'] for s in group]
            # Handle both datetime.date objects (from DB) and strings (from tests)
            if dates and isinstance(dates[0], str):
                return max(datetime.strptime(d, '%Y-%m-%d') for d in dates)
            return max(dates)  # date objects compare directly

        most_common_coords = sorted(
            most_common_coords,
            key=lambda x: get_max_date(x[1]),
            reverse=True
        )

    # Step 6: Final tiebreaker - lexicographic sort
    if len(most_common_coords) > 1:
        most_common_coords = sorted(most_common_coords, key=lambda x: (x[0][0], x[0][1]))

    chosen_coords = most_common_coords[0][0]
    return chosen_coords


def _select_canonical_enrichment(sales: List[dict]) -> dict:
    """
    Select canonical enrichment using frequency-based strategy.

    Algorithm for each field (bedrooms, property_type):
    1. Filter to non-NULL values
    2. Group by value and count occurrences
    3. Pick most common value
    4. Tiebreaker: most recent sale_date
    5. Final tiebreaker: highest price

    Args:
        sales: List of sale dicts with bedrooms/property_type/sale_date/price fields

    Returns:
        Dict with 'bedrooms' and 'property_type' keys (may be None if no data)
    """
    def select_field_value(field_name: str) -> Optional[any]:
        """Select canonical value for a single field using frequency strategy."""
        # Filter to sales with non-NULL values for this field
        non_null_sales = [s for s in sales if s.get(field_name) is not None]

        if not non_null_sales:
            return None

        # Group by value and count occurrences
        value_groups = {}
        for sale in non_null_sales:
            value = sale[field_name]
            if value not in value_groups:
                value_groups[value] = []
            value_groups[value].append(sale)

        # Find most common value(s)
        max_count = max(len(group) for group in value_groups.values())
        most_common_values = [
            (value, group) for value, group in value_groups.items()
            if len(group) == max_count
        ]

        # Tiebreaker 1: most recent sale_date
        def get_max_date(group):
            """Get max date from group, handling both date objects and strings."""
            dates = [s['sale_date'] for s in group]
            # Handle both datetime.date objects (from DB) and strings (from tests)
            if dates and isinstance(dates[0], str):
                return max(datetime.strptime(d, '%Y-%m-%d') for d in dates)
            return max(dates)  # date objects compare directly

        if len(most_common_values) > 1:
            most_common_values = sorted(
                most_common_values,
                key=lambda x: get_max_date(x[1]),
                reverse=True
            )

            # Keep only values with the most recent date for further tiebreaking
            max_date = get_max_date(most_common_values[0][1])
            most_common_values = [
                (value, group) for value, group in most_common_values
                if get_max_date(group) == max_date
            ]

        # Tiebreaker 2: highest price (only applied if still tied after recency)
        if len(most_common_values) > 1:
            most_common_values = sorted(
                most_common_values,
                key=lambda x: max(s.get('price') or 0 for s in x[1]),
                reverse=True
            )

        chosen_value = most_common_values[0][0]
        return chosen_value

    return {
        'bedrooms': select_field_value('bedrooms'),
        'property_type': select_field_value('property_type')
    }
