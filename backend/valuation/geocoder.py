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
import logging
import httpx

logger = logging.getLogger(__name__)
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
        eircode: Optional[str] = None,
        county: Optional[str] = None
    ) -> GeocodingResult:
        """
        Geocode an address using multiple methods.

        Priority:
        1. Database lookup (check existing properties first!)
        2. Eircode routing key (if provided)
        3. Nominatim API (only if not in database)

        Args:
            address: Property address
            eircode: Optional Eircode (7 chars, no space)
            county: Optional county name (defaults to Dublin, used to bias Nominatim)

        Returns:
            GeocodingResult with coordinates and confidence

        Raises:
            ValueError: If geocoding fails completely
        """

        # Method 1: Database lookup (ALWAYS try this first!)
        # Works for any property in the Property Price Register (2010-present)
        try:
            result = await self._geocode_by_db_fuzzy_match(address)
            if result:
                logger.info(f"✅ Geocoded via database: {result.address_matched}")
                return result
        except Exception as e:
            logger.warning(f"Database geocoding failed: {e}")

        # Method 2: Eircode routing key lookup
        # Works for properties not in database if Eircode provided
        if eircode:
            try:
                result = await self._geocode_by_eircode_routing_key(eircode)
                if result:
                    logger.info(f"✅ Geocoded via Eircode routing key: {eircode[:3]}")
                    return result
            except Exception as e:
                logger.warning(f"Eircode geocoding failed: {e}")

        # Method 3: Nominatim API (last resort)
        # Works for new properties not in database, uses OpenStreetMap
        result = await self._geocode_by_nominatim(address, eircode, county)
        if result:
            logger.info(f"✅ Geocoded via Nominatim: {result.address_matched}")
            return result

        # All methods failed - provide helpful error message
        if eircode:
            raise ValueError(
                f"Could not locate '{address}' (Eircode: {eircode}). "
                "This property may not exist in our database or external geocoding services. "
                "Please verify the address and Eircode are correct."
            )
        else:
            raise ValueError(
                f"Could not locate '{address}'. "
                "Try adding the area name (e.g., 'Crumlin') or providing an Eircode for better accuracy. "
                "Note: Properties must have sold since 2010 to be in the Property Price Register."
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
        eircode: Optional[str] = None,
        county: Optional[str] = None
    ) -> Optional[GeocodingResult]:
        """
        Geocode using Nominatim (OpenStreetMap) API.

        Args:
            address: Property address
            eircode: Optional Eircode to include in query
            county: Optional county name to bias search results

        Returns:
            GeocodingResult or None if no result found
        """
        # Construct search query with county bias
        # Default to Dublin if no county specified
        county_name = county or "Dublin"

        if eircode:
            search_query = f"{address}, {eircode}, {county_name}, Ireland"
        else:
            search_query = f"{address}, {county_name}, Ireland"

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
            # Add retry logic for transient network errors
            for attempt in range(2):  # 2 attempts max
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:  # Increased timeout
                        response = await client.get(
                            self.nominatim_url,
                            params=params,
                            headers=headers
                        )

                        # Handle rate limiting (429) gracefully
                        if response.status_code == 429:
                            if attempt == 0:
                                await asyncio.sleep(1)  # Wait 1 second before retry
                                continue
                            else:
                                return None  # Give up, try next method

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

                        # Empty results, no need to retry
                        return None

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    # Network error - retry once
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        # Final attempt failed, fall through to next method
                        return None

        except httpx.HTTPStatusError as e:
            # HTTP error (4xx, 5xx) - don't retry
            print(f"Nominatim HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            # Unexpected error - log and continue to next method
            print(f"Nominatim unexpected error: {e}")
            return None

        return None

    async def _geocode_by_db_fuzzy_match(
        self,
        address: str
    ) -> Optional[GeocodingResult]:
        """
        Geocode by matching against known addresses in database.

        Uses EXACT same logic as /search/exact endpoint (S1 page).

        Args:
            address: Property address

        Returns:
            GeocodingResult or None if no match found
        """
        # Normalize address - EXACT copy from /search/exact endpoint
        normalized = address.strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)
        normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

        # Expand common abbreviations to match normalized format
        street_types = {
            r'\bSt\.?\b': 'Street', r'\bRd\.?\b': 'Road', r'\bAve\.?\b': 'Avenue',
            r'\bDr\.?\b': 'Drive', r'\bCl\.?\b': 'Close', r'\bCt\.?\b': 'Court',
            r'\bPk\.?\b': 'Park', r'\bSq\.?\b': 'Square',
        }
        for abbrev, full in street_types.items():
            normalized = re.sub(abbrev, full, normalized, flags=re.I)

        # Clean punctuation and apply title case
        normalized = re.sub(r',\s*,', ',', normalized)
        normalized = re.sub(r'\s+,', ',', normalized)
        normalized = re.sub(r',\s+', ', ', normalized)
        normalized = normalized.strip(', ')

        words = normalized.split()
        lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
        upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

        result_words = []
        for i, word in enumerate(words):
            if i == 0:
                result_words.append(word.capitalize())
            elif word in upper_exceptions:
                result_words.append(word)
            elif word.lower() in lower_exceptions:
                result_words.append(word.lower())
            else:
                result_words.append(word.capitalize())

        address_norm = ' '.join(result_words).strip()

        # Use starts_with() function - EXACT same as S1 page
        # Also fetch bedrooms if available for the subject property
        query = """
            SELECT
                latitude,
                longitude,
                address,
                bedrooms
            FROM properties
            WHERE
                starts_with(COALESCE(address_normalized, address), $1)
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
            LIMIT 1;
        """

        row = await self.db.fetchrow(query, address_norm)

        if row:
            result = GeocodingResult(
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                confidence=0.80,  # High confidence for database match
                method="database_exact",
                address_matched=row['address']
            )
            # Store bedrooms for later use (if available)
            result.bedrooms = row['bedrooms']
            return result

        return None

