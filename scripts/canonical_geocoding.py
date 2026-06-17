#!/usr/bin/env python3
"""
Canonical geocoding and enrichment caching module.

Provides in-memory cache for property coordinates and enrichment data
to ensure consistency across multiple sales of the same address.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class PropertyData:
    """Property coordinate and enrichment data."""
    latitude: float
    longitude: float
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    last_geocoded: Optional[datetime] = None
    last_enriched: Optional[datetime] = None


# Global in-memory cache: address_normalized -> PropertyData
_canonical_cache: Dict[str, PropertyData] = {}
