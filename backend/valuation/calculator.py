"""
Valuation calculator.

Calculates weighted average property value with confidence intervals.
"""

import statistics
from typing import List, Dict, Tuple


class ValuationCalculator:
    """Calculate property valuation from weighted comparables."""

    def calculate_valuation(
        self,
        comparables: List[Dict],
        weights: List[float]
    ) -> Dict:
        """
        Calculate valuation using weighted average.

        Args:
            comparables: List of comparable property dicts with 'adjusted_price'
            weights: List of weights (same length as comparables)

        Returns:
            Dict with keys:
                - estimate: Weighted average price
                - confidence_interval: Dict with lower, upper, width_pct
                - statistics: Dict with mean, median, std_dev, cv, min, max

        Raises:
            ValueError: If inputs are invalid
        """

        if not comparables:
            raise ValueError("No comparables provided")

        if len(comparables) != len(weights):
            raise ValueError("Comparables and weights must have same length")

        # Extract adjusted prices
        prices = [c['adjusted_price'] for c in comparables]

        # Calculate weighted average (estimate)
        weighted_sum = sum(p * w for p, w in zip(prices, weights))
        estimate = int(weighted_sum)

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            prices,
            weights,
            estimate
        )

        # Calculate statistics
        stats = self._calculate_statistics(prices)

        return {
            'estimate': estimate,
            'confidence_interval': confidence_interval,
            'statistics': stats
        }

    def _calculate_confidence_interval(
        self,
        prices: List[int],
        weights: List[float],
        estimate: int
    ) -> Dict:
        """
        Calculate confidence interval for valuation estimate.

        Uses weighted standard deviation to estimate uncertainty.

        CI = estimate ± (k × weighted_std_dev)

        Where k depends on number of comparables:
        - n < 5: k = 2.0 (very wide)
        - n < 10: k = 1.5
        - n >= 10: k = 1.0

        Args:
            prices: List of adjusted prices
            weights: List of weights
            estimate: Valuation estimate (weighted average)

        Returns:
            Dict with keys: lower, upper, width_pct
        """

        n = len(prices)

        # Calculate weighted standard deviation
        weighted_variance = sum(
            w * (p - estimate) ** 2
            for p, w in zip(prices, weights)
        )
        weighted_std = weighted_variance ** 0.5

        # Choose k based on sample size (smaller n = wider interval)
        if n < 5:
            k = 2.0
        elif n < 10:
            k = 1.5
        else:
            k = 1.0

        # Calculate interval
        interval_width = k * weighted_std
        lower = int(max(0, estimate - interval_width))
        upper = int(estimate + interval_width)

        # Calculate width as percentage of estimate
        width_pct = (upper - lower) / estimate * 100 if estimate > 0 else 0

        return {
            'lower': lower,
            'upper': upper,
            'width_pct': round(width_pct, 1)
        }

    def _calculate_statistics(
        self,
        prices: List[int]
    ) -> Dict:
        """
        Calculate statistical measures for comparables.

        Args:
            prices: List of adjusted prices

        Returns:
            Dict with keys: mean_price, median_price, std_dev,
                           coefficient_of_variation, min_price, max_price
        """

        mean_price = statistics.mean(prices)
        median_price = statistics.median(prices)

        # Standard deviation
        if len(prices) > 1:
            std_dev = statistics.stdev(prices)
        else:
            std_dev = 0.0

        # Coefficient of variation (CV = std / mean)
        cv = std_dev / mean_price if mean_price > 0 else 0.0

        return {
            'mean_price': round(mean_price, 2),
            'median_price': round(median_price, 2),
            'std_dev': round(std_dev, 2),
            'coefficient_of_variation': round(cv, 3),
            'min_price': min(prices),
            'max_price': max(prices)
        }
