"""
Comparable property search for valuation.

Finds similar properties near the subject property using adaptive radius search.

Search strategy:
- Start at 1km radius
- Expand to 2km, 5km, 10km, 20km if needed
- Stop when min_count reached
- Order by distance and recency
"""

from typing import List, Dict
from datetime import datetime, timedelta


class ComparableSearcher:
    """Find comparable properties using adaptive radius search."""

    def __init__(self, db_pool):
        """
        Initialize comparable searcher.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db = db_pool

        # Adaptive search radii (meters)
        self.search_radii = [1000, 2000, 5000, 10000, 20000]

        # Time window for comparables
        self.lookback_years = 3

    async def find_comparables(
        self,
        latitude: float,
        longitude: float,
        min_count: int = 10,
        max_count: int = 30,
        exclude_property_id: int = None
    ) -> List[Dict]:
        """
        Find comparable properties using adaptive radius search.

        Searches in expanding radii until min_count comparables found.

        Args:
            latitude: Subject property latitude
            longitude: Subject property longitude
            min_count: Minimum number of comparables to find
            max_count: Maximum number of comparables to return
            exclude_property_id: Optional property ID to exclude (for accuracy testing)

        Returns:
            List of comparable property dicts with keys:
                id, address, price, sale_date, bedrooms, property_type,
                county, distance_m, recency_score

        Raises:
            ValueError: If no comparables found at all
        """

        # Try each radius until we get enough comparables
        for radius_m in self.search_radii:
            comparables = await self._search_at_radius(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
                max_count=max_count,
                exclude_property_id=exclude_property_id
            )

            if len(comparables) >= min_count:
                # Found enough comparables
                return comparables[:max_count]

        # If we get here, we didn't find enough comparables
        # Return whatever we found (might be < min_count)
        if comparables:
            return comparables[:max_count]

        raise ValueError(
            f"No comparable sales found within 20km. "
            f"This area may have very sparse sales data."
        )

    async def _search_at_radius(
        self,
        latitude: float,
        longitude: float,
        radius_m: float,
        max_count: int,
        exclude_property_id: int = None
    ) -> List[Dict]:
        """
        Search for comparables within a specific radius.

        Uses ST_DWithin with GIST index for fast spatial queries.

        Args:
            latitude: Subject property latitude
            longitude: Subject property longitude
            radius_m: Search radius in meters
            max_count: Maximum results to return
            exclude_property_id: Optional property ID to exclude

        Returns:
            List of comparable property dicts
        """

        # Calculate lookback date
        lookback_date = datetime.now() - timedelta(days=self.lookback_years * 365)

        query = """
            WITH subject_point AS (
                SELECT ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography AS geog
            )
            SELECT
                p.id,
                p.address,
                p.price,
                p.sale_date,
                p.bedrooms,
                p.property_type,
                p.county,
                ST_Distance(p.geog, sp.geog) AS distance_m,
                -- Recency score (0-1, recent = higher)
                1.0 - (EXTRACT(EPOCH FROM (NOW() - p.sale_date)) / ($4 * 365 * 86400)) AS recency_score
            FROM properties p
            CROSS JOIN subject_point sp
            WHERE
                p.geog IS NOT NULL
                AND p.not_full_market_price = FALSE
                AND p.price IS NOT NULL
                AND p.price BETWEEN 50000 AND 5000000
                AND p.sale_date >= $5
                AND ST_DWithin(p.geog, sp.geog, $3)  -- Uses GIST index
                AND ($6::INTEGER IS NULL OR p.id != $6)  -- Exclude property if specified
            ORDER BY distance_m ASC, recency_score DESC
            LIMIT $7;
        """

        rows = await self.db.fetch(
            query,
            longitude,  # $1 - Note: PostGIS uses (lon, lat) order
            latitude,   # $2
            radius_m,   # $3
            self.lookback_years,  # $4
            lookback_date,  # $5
            exclude_property_id,  # $6
            max_count   # $7
        )

        # Convert to list of dicts
        comparables = []
        for row in rows:
            comparable = {
                'id': row['id'],
                'address': row['address'],
                'price': row['price'],
                'sale_date': row['sale_date'],
                'bedrooms': row['bedrooms'],
                'property_type': row['property_type'],
                'county': row['county'],
                'distance_m': float(row['distance_m']),
                'recency_score': float(row['recency_score'])
            }
            comparables.append(comparable)

        return comparables

    def get_search_radius_used(self, n_comparables: int) -> str:
        """
        Estimate which radius was used based on comparable count.

        Useful for logging/debugging.

        Args:
            n_comparables: Number of comparables found

        Returns:
            Human-readable radius description
        """
        if n_comparables >= 30:
            return "< 1km (high density)"
        elif n_comparables >= 20:
            return "1-2km"
        elif n_comparables >= 10:
            return "2-5km"
        elif n_comparables >= 5:
            return "5-10km"
        else:
            return "10-20km (sparse data)"
