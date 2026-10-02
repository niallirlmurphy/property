"""
Price adjustment logic for valuation.

Phase 1: Temporal adjustments using county price indices
Phase 2: Feature-based adjustments (bedrooms, property type, BER)

Weighting formula: distance + recency
"""

from typing import Dict, Optional
from datetime import datetime

from .cache import TTLCache


# County price indices change at most once a month, but adjust_temporal looks
# one up twice per comparable — up to ~60 sequential DB round-trips per
# valuation, all for a handful of distinct (county, year-month) values (and one
# repeated target month). This module-level cache collapses those to one fetch
# per distinct key, shared across requests. 6h TTL so a monthly index refresh
# is picked up without a restart.
_PRICE_INDEX_CACHE = TTLCache(ttl_seconds=6 * 3600)

# Local apartment-price ceiling is a 2km spatial aggregate that is identical for
# neighbouring points, so cache it per ~110m grid cell (lat/lon rounded to 3dp).
# Sales data changes only every couple of weeks, so a 6h TTL self-heals quickly.
_APT_CEILING_CACHE = TTLCache(ttl_seconds=6 * 3600)


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

# Bedroom price ladder --------------------------------------------------------
# Dublin apartment/duplex bedroom price ratios (relative to a 2-bed), derived
# from ~7,000 PPR sales 2022+ (median sale price by bedroom count):
#   1-bed 0.796 · 2-bed 1.000 · 3-bed 1.275 · 4-bed 1.500  (studio ≈ 0.62).
# These let us (a) normalise every comparable to a common "2-bed-equivalent" so
# sales of any size inform one base, and (b) re-expand that base to the subject's
# bedroom count. This guarantees a larger unit is never valued below a smaller
# one at the same location — a plain weighted average of raw sale prices does
# not, and in thin-data areas would occasionally invert (a lone pricey 1-bed
# sale outranking the local 2-beds).
_BEDROOM_RATIO = {0: 0.62, 1: 0.796, 2: 1.0, 3: 1.275, 4: 1.5}
_ANCHOR_BEDROOMS = 2
# Weight applied to a comparable whose bedroom count is unknown when building the
# normalised base: it can't be size-normalised, so it contributes only weakly.
_UNKNOWN_BEDROOM_SIZE_WEIGHT = 0.2


def bedroom_ratio(bedrooms: Optional[int]) -> Optional[float]:
    """Price of a `bedrooms`-bed apartment relative to a 2-bed, or None if the
    count is unknown/invalid. Counts above 4 clamp to the 4-bed ratio (data on
    larger apartments is thin)."""
    if bedrooms is None or bedrooms < 0:
        return None
    if bedrooms in _BEDROOM_RATIO:
        return _BEDROOM_RATIO[bedrooms]
    return _BEDROOM_RATIO[4] if bedrooms > 4 else _BEDROOM_RATIO[0]


def trim_price_outliers(
    comparables: list,
    price_key: str = "adjusted_price",
    k: float = 1.5,
    min_pool: int = 8,
    min_keep: int = 5,
) -> list:
    """Drop comparables whose price is a Tukey outlier relative to the local
    pool — outside ``[Q1 − k·IQR, Q3 + k·IQR]``.

    A single very large sale (e.g. a €2m apartment or €4.3m house recorded amid a
    cluster of €300–500k sales) would otherwise dominate the weighted average and
    inflate the estimate. Only trims when there are enough comparables to define a
    stable fence (``min_pool``) and always keeps at least ``min_keep``.
    """
    comps = list(comparables)
    if len(comps) < min_pool:
        return comps
    prices = sorted(c[price_key] for c in comps)
    n = len(prices)
    q1 = prices[n // 4]
    q3 = prices[(3 * n) // 4]
    iqr = q3 - q1
    lo = q1 - k * iqr
    hi = q3 + k * iqr
    kept = [c for c in comps if lo <= c[price_key] <= hi]
    return kept if len(kept) >= min_keep else comps


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

        # Memoised by (county, year-month): the index is constant within a month,
        # so this turns the per-comparable lookups into one fetch per distinct
        # month. A cached None (county/month with no index) is a valid hit and
        # still short-circuits the query.
        cache_key = (county, target_date.year, target_date.month)
        hit, cached = _PRICE_INDEX_CACHE.get(cache_key)
        if hit:
            return cached

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

        if not row:
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

        result = float(row['price_index']) if row else None
        _PRICE_INDEX_CACHE.set(cache_key, result)
        return result

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
            else:
                # Unknown bedroom count: soft down-weight (mirrors unknown type).
                # Without this an unlabelled unit — which may be a huge, pricey
                # one — competes at full strength against a small subject and can
                # dominate the estimate. Not a free pass at 1.0.
                bedroom_factor = 0.35

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

    async def apartment_price_ceiling(
        self,
        latitude: float,
        longitude: float,
        radius_m: float = 2000.0,
        min_n: int = 15,
        k: float = 3.0,
    ) -> Optional[float]:
        """Local ceiling for a plausible apartment price, in 2-bed-equivalent €.

        Built from *confirmed* apartment/duplex sales near (latitude, longitude)
        since 2022, each normalised to a 2-bed-equivalent via ``bedroom_ratio``.
        Returns the Tukey far-outlier upper fence ``Q3 + k·IQR`` of that local
        apartment distribution, or None when there aren't enough confirmed
        apartment sales (``min_n``) to trust the band.

        This is our "understanding of apartment prices across Dublin": in a house-
        heavy area, a comparable pool is dominated by houses that are far pricier
        than any apartment — and many of them carry no (or a wrong) property_type,
        so the type filter alone can't suppress them. Anything above this ceiling
        is priced like a house, not an apartment, whatever its label, so callers
        exclude it from an apartment valuation. Because the fence scales with local
        variance it stays tight in uniform low-priced areas yet generous in premium
        central districts (Grand Canal Dock, Clontarf) where €1m+ apartments are
        genuinely normal — so it removes contamination without over-trimming.
        """
        # Cache per ~110m grid cell: the 2km pool (and hence the ceiling) is
        # effectively identical for neighbouring subjects, so nearby apartment
        # valuations reuse one spatial aggregation instead of re-running it.
        cache_key = (round(latitude, 3), round(longitude, 3), radius_m, min_n, k)
        hit, cached = _APT_CEILING_CACHE.get(cache_key)
        if hit:
            return cached

        rows = await self.db.fetch(
            """
            SELECT price, bedrooms
            FROM properties
            WHERE geog IS NOT NULL
              AND geocode_suspect IS NOT TRUE
              AND ST_DWithin(geog, ST_MakePoint($2, $1)::geography, $3)
              AND sale_date >= '2022-01-01'
              AND lower(property_type) = ANY($4::text[])
            """,
            latitude, longitude, radius_m, sorted(_APARTMENT_TYPES),
        )
        if len(rows) < min_n:
            _APT_CEILING_CACHE.set(cache_key, None)
            return None
        vals = []
        for r in rows:
            r_ratio = bedroom_ratio(r["bedrooms"])
            # Unknown bedroom count among confirmed apartments: use the raw price
            # (already an apartment, so it belongs in the band as ~a 2-bed).
            factor = (_BEDROOM_RATIO[_ANCHOR_BEDROOMS] / r_ratio) if r_ratio else 1.0
            vals.append(float(r["price"]) * factor)
        vals.sort()
        n = len(vals)
        q1 = vals[n // 4]
        q3 = vals[(3 * n) // 4]
        ceiling = q3 + k * (q3 - q1)
        _APT_CEILING_CACHE.set(cache_key, ceiling)
        return ceiling

    def bedroom_ladder_valuation(
        self,
        comparables: list,
        subject_bedrooms: Optional[int],
        subject_property_type: Optional[str],
        max_2bed_equiv: Optional[float] = None,
    ) -> Optional[Dict]:
        """Estimate value via a bedroom-normalised base (see ``bedroom_ratio``).

        Each comparable is normalised to a "2-bed-equivalent" price by dividing
        out its own bedroom ratio, so sales of any size inform a single base;
        that base is then re-expanded to the subject's bedroom count. Because the
        final figure is ``base × ratio[subject]``, a larger unit can never be
        valued below a smaller one at the same location.

        Only applies to apartment-type subjects with a known bedroom count (the
        ratios are apartment-specific). Returns None otherwise, so callers fall
        back to the plain weighted average.

        Returns dict with:
            - estimate: subject-bedroom estimate (int)
            - base_2bed: the location's 2-bed-equivalent base (int)
            - weights: per-comparable normalised weights (same order as input)
        """
        subj_ratio = bedroom_ratio(subject_bedrooms)
        if subj_ratio is None or not comparables:
            return None
        if property_bucket(subject_property_type) != "apartment":
            return None

        # Per-comparable 2-bed-equivalent price (used both for the base and for the
        # apartment-price ceiling below).
        normalised_prices = []
        for c in comparables:
            r = bedroom_ratio(c.get("bedrooms"))
            if r is not None:
                normalised_prices.append(
                    float(c["adjusted_price"]) * (_BEDROOM_RATIO[_ANCHOR_BEDROOMS] / r)
                )
            else:
                # Unknown size: can't normalise; treat the raw price as ~a 2-bed.
                normalised_prices.append(float(c["adjusted_price"]))

        # Apartment-price ceiling: drop comparables whose 2-bed-equivalent is
        # priced like a house, not an apartment (see ``apartment_price_ceiling``).
        # In house-heavy areas these are the pricey houses — often unlabelled, so
        # the type factor alone can't suppress them — that otherwise inflate the
        # base. Only apply the ceiling if at least ``min_keep`` comparables survive,
        # so we never over-trim a genuinely sparse or uniformly-premium pool.
        excluded = [False] * len(comparables)
        if max_2bed_equiv is not None:
            min_keep = 5
            survivors = sum(1 for p in normalised_prices if p <= max_2bed_equiv)
            if survivors >= min(min_keep, len(comparables)):
                excluded = [p > max_2bed_equiv for p in normalised_prices]

        max_distance = max(c["distance_m"] for c in comparables)
        raw_weights = []
        weighted_sum = 0.0
        for c, normalised, is_excluded in zip(comparables, normalised_prices, excluded):
            if is_excluded:
                raw_weights.append(0.0)
                continue
            if max_distance > 0:
                distance_factor = 1.0 - (float(c["distance_m"]) / max_distance)
            else:
                distance_factor = 1.0
            base = (distance_factor ** 2) * float(c.get("recency_score", 0.5))

            comp_bucket = property_bucket(c.get("property_type"))
            if comp_bucket == "apartment":
                type_factor = _TYPE_FACTOR_SAME
            elif comp_bucket is None:
                type_factor = _TYPE_FACTOR_UNKNOWN
            else:
                type_factor = _TYPE_FACTOR_DIFFERENT

            size_weight = 1.0 if bedroom_ratio(c.get("bedrooms")) is not None \
                else _UNKNOWN_BEDROOM_SIZE_WEIGHT

            w = max(0.0, base * type_factor * size_weight)
            raw_weights.append(w)
            weighted_sum += w * normalised

        total = sum(raw_weights)
        if total <= 0:
            return None
        base_2bed = weighted_sum / total
        estimate = base_2bed * subj_ratio / _BEDROOM_RATIO[_ANCHOR_BEDROOMS]
        return {
            "estimate": int(estimate),
            "base_2bed": int(base_2bed),
            "weights": [w / total for w in raw_weights],
        }

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
