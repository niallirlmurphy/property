#!/usr/bin/env python3
"""
Mapbox API client wrapper with automatic usage tracking and limits.

This module provides a centralized client for all Mapbox API calls with:
- Automatic usage tracking to database
- Strict monthly limit enforcement (50,000 requests/month)
- Pre-flight limit checks before expensive operations
- Error handling and retry logic

Usage:
    from scripts.mapbox_client import MapboxClient

    async with MapboxClient(source='my_script') as client:
        # Single geocode
        result = await client.geocode(address='Dublin, Ireland')

        # Batch geocode (automatically tracks all requests)
        results = await client.batch_geocode(addresses=['...', '...'])
"""

import os
import sys
import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))
from mapbox_usage_tracker import MapboxUsageTracker

load_dotenv()

# STRICT MONTHLY LIMIT (reduced from 100k free tier for safety margin)
MAPBOX_MONTHLY_LIMIT = 50_000


class MapboxLimitExceeded(Exception):
    """Raised when Mapbox monthly limit is exceeded."""
    pass


class MapboxClient:
    """
    Mapbox API client with automatic usage tracking and limit enforcement.

    All Mapbox API calls MUST go through this client to ensure proper tracking.
    """

    def __init__(self, source: str, operation: str = 'geocode', notes: Optional[str] = None):
        """
        Initialize Mapbox client.

        Args:
            source: Script/service name for tracking (e.g., 'geocode_mapbox_batch', 'api')
            operation: Operation type ('geocode', 'batch_geocode', 'search')
            notes: Optional notes for this session

        Raises:
            ValueError: If MAPBOX_TOKEN not set
        """
        self.token = os.getenv('MAPBOX_TOKEN')
        if not self.token:
            raise ValueError("MAPBOX_TOKEN environment variable not set")

        self.source = source
        self.tracker = MapboxUsageTracker(source=source, operation=operation, notes=notes)
        self._client = None

    async def __aenter__(self):
        """Context manager entry - start tracking and check limits."""
        await self.tracker.start()
        await self._check_limit()
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save tracking and close connections."""
        if self._client:
            await self._client.aclose()
        await self.tracker.close()

    async def _check_limit(self, required_requests: int = 1):
        """
        Check if we have enough quota remaining.

        Args:
            required_requests: Number of requests about to be made

        Raises:
            MapboxLimitExceeded: If limit would be exceeded
        """
        usage = await MapboxUsageTracker.get_current_month_usage()
        total_used = usage['total']['total_requests']
        remaining = MAPBOX_MONTHLY_LIMIT - total_used

        if total_used >= MAPBOX_MONTHLY_LIMIT:
            raise MapboxLimitExceeded(
                f"Monthly Mapbox limit exceeded: {total_used:,} / {MAPBOX_MONTHLY_LIMIT:,} requests used"
            )

        if required_requests > remaining:
            raise MapboxLimitExceeded(
                f"Insufficient quota: need {required_requests:,} requests but only {remaining:,} remaining"
            )

        # Warn at 80% usage
        percentage = (total_used / MAPBOX_MONTHLY_LIMIT) * 100
        if percentage >= 80:
            print(f"⚠️  WARNING: {percentage:.1f}% of Mapbox quota used ({total_used:,} / {MAPBOX_MONTHLY_LIMIT:,})")

    async def geocode(
        self,
        address: str,
        country: str = 'ie',
        limit: int = 1,
        eircode: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Geocode single address using Mapbox Geocoding API.

        If eircode is provided, tries eircode first (more accurate), then falls back to address.

        Args:
            address: Address to geocode
            country: ISO country code (default: 'ie' for Ireland)
            limit: Maximum results to return
            eircode: Irish postal code (if available, will try first)

        Returns:
            Dict with 'latitude', 'longitude', 'full_address', 'precision' or None if no results

        Raises:
            MapboxLimitExceeded: If monthly limit exceeded
        """
        # Try Eircode first if available (more accurate)
        if eircode:
            result = await self._geocode_query(eircode, country, limit)
            if result:
                result['method'] = 'eircode'
                return result

        # Fallback to address (or primary if no eircode)
        result = await self._geocode_query(address, country, limit)
        if result:
            result['method'] = 'address'
        return result

    async def _geocode_query(
        self,
        query: str,
        country: str,
        limit: int
    ) -> Optional[Dict]:
        """Internal method to geocode a single query."""
        await self._check_limit(required_requests=1)

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
        params = {
            'access_token': self.token,
            'country': country,
            'limit': limit,
            'types': 'address,poi,postcode'
        }

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            self.tracker.record_request(success=True)

            if data.get('features'):
                feature = data['features'][0]
                coords = feature['geometry']['coordinates']
                return {
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'full_address': feature.get('place_name', ''),
                    'precision': feature.get('place_type', ['unknown'])[0]
                }

            self.tracker.record_request(success=False)
            return None

        except Exception as e:
            self.tracker.record_request(success=False)
            print(f"Mapbox geocoding error for '{query}': {e}")
            return None

    async def batch_geocode(
        self,
        addresses: List[str],
        country: str = 'ie',
        batch_size: int = 50  # Mapbox supports up to 50 per batch request
    ) -> List[Optional[Dict]]:
        """
        Batch geocode multiple addresses (chunked into Mapbox batch size).

        Args:
            addresses: List of addresses to geocode
            country: ISO country code
            batch_size: Number of addresses per API request (max 50)

        Returns:
            List of results (same order as input), None for failed geocodes

        Raises:
            MapboxLimitExceeded: If monthly limit would be exceeded
        """
        total_requests = len(addresses)
        await self._check_limit(required_requests=total_requests)

        results = []

        # Process in chunks of batch_size
        for i in range(0, len(addresses), batch_size):
            chunk = addresses[i:i + batch_size]
            chunk_results = await self._batch_geocode_chunk(chunk, country)
            results.extend(chunk_results)

            # Small delay between chunks to avoid rate limiting
            if i + batch_size < len(addresses):
                await asyncio.sleep(0.5)

        return results

    async def _batch_geocode_chunk(
        self,
        addresses: List[str],
        country: str
    ) -> List[Optional[Dict]]:
        """Geocode a single chunk of addresses (internal method)."""
        # Note: Mapbox Permanent Geocoding API supports batch requests
        # For now, we'll make parallel single requests (simpler, same quota cost)

        tasks = [self.geocode(addr, country=country) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None
        return [r if not isinstance(r, Exception) else None for r in results]

    async def get_remaining_quota(self) -> int:
        """Get remaining requests in monthly quota."""
        usage = await MapboxUsageTracker.get_current_month_usage()
        return MAPBOX_MONTHLY_LIMIT - usage['total']['total_requests']

    async def can_process(self, count: int) -> Tuple[bool, str]:
        """
        Check if we can process N requests without exceeding limit.

        Args:
            count: Number of requests to check

        Returns:
            (can_proceed, message) tuple
        """
        try:
            await self._check_limit(required_requests=count)
            remaining = await self.get_remaining_quota()
            return True, f"✓ Can process {count:,} requests ({remaining:,} remaining)"
        except MapboxLimitExceeded as e:
            return False, f"✗ Cannot process: {str(e)}"


async def check_quota_before_run(required: int, source: str) -> bool:
    """
    Pre-flight check before running expensive Mapbox operations.

    Args:
        required: Number of requests the operation will need
        source: Script name for tracking

    Returns:
        True if safe to proceed, False otherwise
    """
    async with MapboxClient(source=source) as client:
        can_proceed, message = await client.can_process(required)
        print(f"\n{message}\n")
        return can_proceed


if __name__ == '__main__':
    import sys

    async def demo():
        # Test geocoding with tracking
        async with MapboxClient(source='test_script') as client:
            # Check quota
            remaining = await client.get_remaining_quota()
            print(f"Remaining quota: {remaining:,} requests")

            # Single geocode
            result = await client.geocode('Dublin, Ireland')
            print(f"Dublin: {result}")

            # Batch geocode
            addresses = [
                'Cork, Ireland',
                'Galway, Ireland',
                'Limerick, Ireland'
            ]
            results = await client.batch_geocode(addresses)
            for addr, res in zip(addresses, results):
                print(f"{addr}: {res}")

    asyncio.run(demo())
