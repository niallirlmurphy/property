#!/usr/bin/env python3
"""
Canonical geocoding and enrichment caching module.

Provides in-memory cache for property coordinates and enrichment data
to ensure consistency across multiple sales of the same address.
"""

from dataclasses import dataclass
from datetime import datetime
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
    Placeholder - will implement in Task 3.

    Raises:
        ValueError: If no sales with coordinates found
    """
    # Filter to sales with non-NULL coordinates
    sales_with_coords = [s for s in sales if s['latitude'] is not None and s['longitude'] is not None]

    if not sales_with_coords:
        raise ValueError("No sales with coordinates found")

    # For now, just return first sale's coordinates
    return (sales_with_coords[0]['latitude'], sales_with_coords[0]['longitude'])


def _select_canonical_enrichment(sales: List[dict]) -> dict:
    """
    Select canonical enrichment using frequency strategy.
    Placeholder - will implement in Task 4.
    """
    # For now, just return first sale's enrichment
    return {
        'bedrooms': sales[0]['bedrooms'],
        'property_type': sales[0]['property_type']
    }
