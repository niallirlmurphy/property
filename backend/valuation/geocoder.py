"""
Geocoder service for property valuation.

Converts addresses to coordinates using multiple fallback methods:
1. Eircode routing key lookup (fast, accurate for Irish addresses)
2. Nominatim API (OpenStreetMap)
3. Database fuzzy address match (fallback for known addresses)

Returns coordinates with confidence score.
"""

import os
import re
import asyncio
import httpx
from typing import Dict, Optional, Tuple
from .models import GeocodingResult


class ValuationGeocoder:
    """Geocoder with multiple fallback methods."""

    def __init__(self, db_pool):
        """
        Initialize geocoder.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db = db_pool
        self.nominatim_url = os.getenv(
            'NOMINATIM_URL',
            'https://nominatim.openstreetmap.org/search'
        )
        self.user_agent = 'HomeIQ.ie Property Valuation/1.0'

    async def geocode_address(
        self,
        address: str,
        eircode: Optional[str] = None
    ) -> GeocodingResult:
        """
        Geocode an address using multiple methods.

        Priority:
        1. Eircode routing key (if provided)
        2. Nominatim API
        3. Database fuzzy match

        Args:
            address: Property address
            eircode: Optional Eircode (7 chars, no space)

        Returns:
            GeocodingResult with coordinates and confidence

        Raises:
            ValueError: If geocoding fails completely
        """

        # Method 1: Eircode routing key lookup
        if eircode:
            result = await self._geocode_by_eircode_routing_key(eircode)
            if result:
                return result

        # Method 2: Nominatim API
        result = await self._geocode_by_nominatim(address, eircode)
        if result:
            return result

        # Method 3: Database fuzzy match
        result = await self._geocode_by_db_fuzzy_match(address)
        if result:
            return result

        # All methods failed
        raise ValueError(
            f"Could not geocode address: {address}. "
            "Try providing an Eircode for better accuracy."
        )

    async def _geocode_by_eircode_routing_key(
        self,
        eircode: str
    ) -> Optional[GeocodingResult]:
        """
        Geocode using Eircode routing key (first 3 chars).

        Uses routing_key_stats materialized view for fast lookup.

        Args:
            eircode: 7-character Eircode (e.g., 'D02X285')

        Returns:
            GeocodingResult or None if routing key not found
        """
        routing_key = eircode[:3].upper()

        query = """
            SELECT
                centroid_lat,
                centroid_lon,
                property_count
            FROM routing_key_stats
            WHERE routing_key = $1;
        """

        row = await self.db.fetchrow(query, routing_key)

        if row and row['property_count'] >= 5:
            # Confidence based on property count
            # High count = more reliable centroid
            confidence = min(0.85, 0.70 + (row['property_count'] / 1000) * 0.15)

            return GeocodingResult(
                latitude=float(row['centroid_lat']),
                longitude=float(row['centroid_lon']),
                confidence=confidence,
                method="eircode_routing_key",
                address_matched=f"Routing key {routing_key}"
            )

        return None

    async def _geocode_by_nominatim(
        self,
        address: str,
        eircode: Optional[str] = None
    ) -> Optional[GeocodingResult]:
        """
        Geocode using Nominatim (OpenStreetMap) API.

        Args:
            address: Property address
            eircode: Optional Eircode to include in query

        Returns:
            GeocodingResult or None if no result found
        """
        # Construct search query
        if eircode:
            search_query = f"{address}, {eircode}, Ireland"
        else:
            search_query = f"{address}, Ireland"

        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'ie',
            'addressdetails': 1
        }

        headers = {
            'User-Agent': self.user_agent
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.nominatim_url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()

                results = response.json()

                if results and len(results) > 0:
                    result = results[0]

                    # Check if result is in Ireland
                    lat = float(result['lat'])
                    lon = float(result['lon'])

                    # Ireland bounding box
                    if not (51.4 <= lat <= 55.5 and -10.7 <= lon <= -5.4):
                        return None

                    # Confidence based on result quality
                    importance = float(result.get('importance', 0.5))
                    confidence = min(0.95, 0.60 + importance * 0.35)

                    return GeocodingResult(
                        latitude=lat,
                        longitude=lon,
                        confidence=confidence,
                        method="nominatim",
                        address_matched=result.get('display_name')
                    )

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            # Log error but don't fail - try next method
            print(f"Nominatim error: {e}")
            return None

        return None

    async def _geocode_by_db_fuzzy_match(
        self,
        address: str
    ) -> Optional[GeocodingResult]:
        """
        Geocode by fuzzy matching against known addresses in database.

        Uses normalized address column for matching.

        Args:
            address: Property address

        Returns:
            GeocodingResult or None if no match found
        """
        # Normalize address for matching
        address_norm = self._normalize_address(address)

        # Try exact prefix match first
        query = """
            SELECT
                latitude,
                longitude,
                address
            FROM properties
            WHERE
                address_normalized ILIKE $1 || '%'
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
            LIMIT 1;
        """

        row = await self.db.fetchrow(query, address_norm)

        if row:
            return GeocodingResult(
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                confidence=0.70,  # Lower confidence for fuzzy match
                method="database_fuzzy",
                address_matched=row['address']
            )

        return None

    @staticmethod
    def _normalize_address(address: str) -> str:
        """
        Normalize address for fuzzy matching.

        Applies same normalization as database import:
        - Title case
        - Remove punctuation
        - Standardize whitespace

        Args:
            address: Raw address string

        Returns:
            Normalized address
        """
        # Remove leading "No." or "Number"
        address = re.sub(r'^(No\.|Number)\s*', '', address, flags=re.IGNORECASE)

        # Title case
        address = address.title()

        # Remove extra punctuation
        address = re.sub(r'[,\.]', ' ', address)

        # Standardize whitespace
        address = ' '.join(address.split())

        return address
