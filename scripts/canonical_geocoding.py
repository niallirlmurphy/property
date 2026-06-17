#!/usr/bin/env python3
"""
Canonical geocoding and enrichment caching module.

Provides in-memory cache for property coordinates and enrichment data
to ensure consistency across multiple sales of the same address.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


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
