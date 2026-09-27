"""
Price adjustment logic for valuation.

Phase 1: Temporal adjustments using county price indices
Phase 2: Feature-based adjustments (bedrooms, property type, BER)

Weighting formula: distance + recency
"""

from typing import Dict, Optional
from datetime import datetime


# Property-type buckets. Apartments and houses are effectively separate markets,
# so a comparable is only "type-matched" if it falls in the subject's bucket.
_APARTMENT_TYPES = {"apartment", "apartments", "flat", "duplex", "studio"}
_HOUSE_TYPES = {
    "house", "semi-detached", "semi detached", "detached", "terraced", "terrace",
    "end of terrace", "bungalow", "cottage", "townhouse", "town house",
}


def property_bucket(property_type: Optional[str]) -> Optional[str]:
    """Collapse a raw property_type string to 'apartment', 'house', or None.

    None means the type is unknown/unclassifiable (~69% of PPR rows have no
    property_type), which we treat as a soft down-weight rather than excluding.
    """
    if not property_type:
        return None
    p = property_type.strip().lower()
    if p in _APARTMENT_TYPES:
        return "apartment"
    if p in _HOUSE_TYPES:
        return "house"
    # Substring fallbacks for compound/enriched labels ("2 bed apartment",
    # "semi-detached house", "mid-terrace house", etc.).
    if "apart" in p or "duplex" in p or "flat" in p:
        return "apartment"
    if any(k in p for k in ("house", "detach", "terrac", "bungalow", "cottage", "town")):
        return "house"
    return None


# Type-match multipliers applied to a comparable's weight. Same-type comparables
# dominate; opposite-type (e.g. a house when valuing an apartment) are almost
# fully suppressed; unknown-type sit in between so they still contribute where
# same-type data is thin but never outweigh confirmed same-type sales.
_TYPE_FACTOR_SAME = 3.0
_TYPE_FACTOR_UNKNOWN = 0.35
_TYPE_FACTOR_DIFFERENT = 0.05


class MVPAdjuster:
    """Phase 1 MVP adjuster - temporal adjustments only."""

    def __init__(self, db_pool):
        """
        Initialize adjuster.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db = db_pool

    async def adjust_temporal(
        self,
        sale_price: float,
        sale_date: datetime,
        target_date: datetime,
        county: str
    ) -> Dict:
        """
        Adjust price for time difference using county price indices.

        Formula:
            adjusted_price = sale_price × (target_index / sale_index)

        Args:
            sale_price: Original sale price
            sale_date: Date of original sale
            target_date: Target valuation date
            county: Property county

        Returns:
            Dict with keys:
                - adjusted_price: Price adjusted to target date
                - adjustment_factor: Ratio applied
                - sale_index: Price index at sale date
                - target_index: Price index at target date

        Raises:
            ValueError: If county price indices not available
        """

        # Get price index at sale date
        sale_index = await self._get_price_index(county, sale_date)

        # Get price index at target date
        target_index = await self._get_price_index(county, target_date)

        if sale_index is None or target_index is None:
            # Fallback: no adjustment if indices unavailable
            return {
                'adjusted_price': int(sale_price),
                'adjustment_factor': 1.0,
                'sale_index': None,
                'target_index': None,
                'fallback': True
            }

        # Calculate adjustment factor
        adjustment_factor = float(target_index) / float(sale_index)

        # Apply adjustment
        adjusted_price = int(float(sale_price) * adjustment_factor)

        return {
            'adjusted_price': adjusted_price,
            'adjustment_factor': adjustment_factor,
            'sale_index': sale_index,
            'target_index': target_index,
            'fallback': False
        }

    async def _get_price_index(
        self,
        county: str,
        target_date: datetime
    ) -> float:
        """
        Get county price index for a specific date.

        Looks up nearest month in county_monthly_price_indices view.

        Args:
            county: County name
            target_date: Date to get index for

        Returns:
            Price index (1.0 = baseline) or None if not available
        """

        query = """
            SELECT price_index
            FROM county_monthly_price_indices
            WHERE
                county = $1
                AND month = DATE_TRUNC('month', $2::timestamp)
            LIMIT 1;
        """

        row = await self.db.fetchrow(
            query,
            county,
            target_date
        )

        if row:
            return float(row['price_index'])

        # Fallback: try nearest available month
        query_fallback = """
            SELECT price_index
            FROM county_monthly_price_indices
            WHERE county = $1
            ORDER BY ABS(EXTRACT(EPOCH FROM (month - $2::timestamp)))
            LIMIT 1;
        """

        row = await self.db.fetchrow(
            query_fallback,
            county,
            target_date
        )

        if row:
            return float(row['price_index'])

        return None

    def calculate_weight(
        self,
        comparable: Dict,
        max_distance_m: float,
        subject_bedrooms: int = None,
        subject_property_type: Optional[str] = None
    ) -> float:
        """
        Calculate weight for a comparable property.

        Weight formula:
            weight = distance_factor² × recency_score × bedroom_factor × type_factor

        Where:
            distance_factor = (1 - distance / max_distance)
            recency_score = 0-1 (calculated in comparable search)
            bedroom_factor depends on bedroom difference:
                - Same bedrooms: 1.5× (50% bonus)
                - 1 bedroom difference: 0.7× (30% penalty)
                - 2+ bedroom difference: 0.2× (80% penalty)
            type_factor depends on property-type match (apartment vs house):
                - Same bucket: 3.0× (heavy bonus)
                - Unknown type: 0.35× (soft down-weight, keeps sparse areas valuable)
                - Different bucket: 0.05× (near-exclude — separate market)

        This ensures properties with significantly different sizes (e.g., 3-bed vs 5-bed)
        receive very low weight, and — crucially — that an apartment is valued off
        apartment sales rather than nearby (often far pricier) houses.

        Args:
            comparable: Comparable property dict with keys:
                - distance_m: Distance in meters
                - recency_score: Recency score (0-1)
                - bedrooms: Number of bedrooms (optional)
                - property_type: Property type string (optional)
            max_distance_m: Maximum distance among all comparables
            subject_bedrooms: Subject property bedroom count (optional)
            subject_property_type: Subject property type (optional). When set,
                comparables of a matching type (apartment vs house) are weighted
                far more heavily than mismatched ones.

        Returns:
            Weight value (0-1+, normalized later)
        """

        distance_m = float(comparable['distance_m'])
        recency_score = float(comparable.get('recency_score', 0.5))

        # Distance factor (1 = very close, 0 = max distance)
        if max_distance_m > 0:
            distance_factor = 1.0 - (distance_m / max_distance_m)
        else:
            distance_factor = 1.0

        # Square distance factor to penalize far properties more
        distance_weight = distance_factor ** 2

        # Combine distance and recency
        base_weight = distance_weight * recency_score

        # Bedroom matching factor
        bedroom_factor = 1.0
        if subject_bedrooms is not None:
            comp_bedrooms = comparable.get('bedrooms')
            if comp_bedrooms is not None:
                bedroom_diff = abs(comp_bedrooms - subject_bedrooms)

                if bedroom_diff == 0:
                    # Exact match: 50% bonus
                    bedroom_factor = 1.5
                elif bedroom_diff == 1:
                    # 1 bedroom difference: slight penalty
                    bedroom_factor = 0.7
                else:
                    # 2+ bedroom difference: heavy penalty
                    # 3-bed vs 5-bed should have very low weight
                    bedroom_factor = 0.2

        # Property-type matching factor (apartment vs house are separate markets)
        type_factor = 1.0
        subject_bucket = property_bucket(subject_property_type)
        if subject_bucket is not None:
            comp_bucket = property_bucket(comparable.get('property_type'))
            if comp_bucket is None:
                type_factor = _TYPE_FACTOR_UNKNOWN
            elif comp_bucket == subject_bucket:
                type_factor = _TYPE_FACTOR_SAME
            else:
                type_factor = _TYPE_FACTOR_DIFFERENT

        # Apply bedroom and type factors
        weight = base_weight * bedroom_factor * type_factor

        # Note: Not clamping to [0, 1] here since we normalize after
        return max(0.0, weight)

    def calculate_all_weights(
        self,
        comparables: list,
        subject_bedrooms: int = None,
        subject_property_type: Optional[str] = None
    ) -> list:
        """
        Calculate weights for all comparables.

        Args:
            comparables: List of comparable property dicts
            subject_bedrooms: Subject property bedroom count (optional)
            subject_property_type: Subject property type (optional); matching
                types (apartment vs house) are weighted far more heavily.

        Returns:
            List of weight values (same order as input)
        """

        if not comparables:
            return []

        # Find max distance
        max_distance = max(c['distance_m'] for c in comparables)

        # Calculate weight for each comparable
        weights = []
        for comparable in comparables:
            weight = self.calculate_weight(
                comparable, max_distance, subject_bedrooms, subject_property_type
            )
            weights.append(weight)

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            # Fallback: equal weights
            n = len(weights)
            weights = [1.0 / n] * n

        return weights
