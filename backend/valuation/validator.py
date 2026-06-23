"""
Quality validator for valuations.

Checks valuation quality and generates warnings.
Assigns confidence levels based on multiple quality factors.
"""

from typing import List, Dict
from .models import (
    ValidationResult,
    ValidationWarning,
    ConfidenceLevel,
    WarningLevel
)


class MVPValidator:
    """Phase 1 MVP validator - basic quality checks."""

    # Quality thresholds
    MIN_COMPARABLES_HIGH = 10
    MIN_COMPARABLES_MEDIUM = 5
    MIN_COMPARABLES_LOW = 3

    MAX_DISTANCE_KM_HIGH = 3.0
    MAX_DISTANCE_KM_MEDIUM = 10.0
    MAX_DISTANCE_KM_LOW = 20.0

    MAX_CV_HIGH = 0.20  # 20% price variation
    MAX_CV_MEDIUM = 0.35  # 35% price variation
    MAX_CV_LOW = 0.50  # 50% price variation

    def validate(
        self,
        valuation: Dict,
        comparables: List[Dict]
    ) -> ValidationResult:
        """
        Validate valuation quality and assign confidence level.

        Checks:
        1. Number of comparables (more = better)
        2. Average distance to comparables (closer = better)
        3. Price dispersion / coefficient of variation (lower = better)

        Args:
            valuation: Valuation dict from calculator
            comparables: List of comparable property dicts

        Returns:
            ValidationResult with confidence level, warnings, quality score
        """

        warnings = []
        quality_factors = []

        # Check 1: Number of comparables
        n_comparables = len(comparables)
        comp_quality = self._check_comparable_count(n_comparables, warnings)
        quality_factors.append(comp_quality)

        # Check 2: Average distance
        avg_distance_m = sum(c['distance_m'] for c in comparables) / n_comparables
        avg_distance_km = avg_distance_m / 1000
        dist_quality = self._check_average_distance(avg_distance_km, warnings)
        quality_factors.append(dist_quality)

        # Check 3: Price dispersion
        cv = valuation['statistics']['coefficient_of_variation']
        cv_quality = self._check_price_dispersion(cv, warnings)
        quality_factors.append(cv_quality)

        # Check 4: Temporal adjustments used
        self._check_temporal_adjustments(comparables, warnings)

        # Overall quality score (0-1)
        quality_score = sum(quality_factors) / len(quality_factors)

        # Determine confidence level based on quality score
        confidence_level = self._determine_confidence_level(quality_score)

        # Determine if valuation is valid (passes minimum standards)
        is_valid = (
            n_comparables >= self.MIN_COMPARABLES_LOW
            and avg_distance_km <= self.MAX_DISTANCE_KM_LOW
            and cv <= self.MAX_CV_LOW
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence_level=confidence_level,
            quality_score=round(quality_score, 2),
            warnings=warnings,
            n_comparables=n_comparables,
            avg_distance_km=round(avg_distance_km, 2),
            price_dispersion_cv=round(cv, 3)
        )

    def _check_comparable_count(
        self,
        n_comparables: int,
        warnings: List[ValidationWarning]
    ) -> float:
        """
        Check number of comparables and add warnings if needed.

        Args:
            n_comparables: Number of comparables
            warnings: List to append warnings to

        Returns:
            Quality factor (0-1)
        """

        if n_comparables >= self.MIN_COMPARABLES_HIGH:
            return 1.0

        elif n_comparables >= self.MIN_COMPARABLES_MEDIUM:
            warnings.append(ValidationWarning(
                level=WarningLevel.INFO,
                message=f"Moderate number of comparables ({n_comparables}). "
                        "More data would increase confidence.",
                code="COMPARABLES_MODERATE"
            ))
            return 0.7

        elif n_comparables >= self.MIN_COMPARABLES_LOW:
            warnings.append(ValidationWarning(
                level=WarningLevel.WARNING,
                message=f"Low number of comparables ({n_comparables}). "
                        "Estimate may be less reliable.",
                code="COMPARABLES_LOW"
            ))
            return 0.4

        else:
            warnings.append(ValidationWarning(
                level=WarningLevel.ERROR,
                message=f"Very few comparables ({n_comparables}). "
                        "Estimate should be used with caution.",
                code="COMPARABLES_VERY_LOW"
            ))
            return 0.2

    def _check_average_distance(
        self,
        avg_distance_km: float,
        warnings: List[ValidationWarning]
    ) -> float:
        """
        Check average distance to comparables.

        Args:
            avg_distance_km: Average distance in kilometers
            warnings: List to append warnings to

        Returns:
            Quality factor (0-1)
        """

        if avg_distance_km <= self.MAX_DISTANCE_KM_HIGH:
            return 1.0

        elif avg_distance_km <= self.MAX_DISTANCE_KM_MEDIUM:
            warnings.append(ValidationWarning(
                level=WarningLevel.INFO,
                message=f"Some comparables are {avg_distance_km:.1f}km away on average. "
                        "Location differences may affect accuracy.",
                code="DISTANCE_MODERATE"
            ))
            return 0.7

        elif avg_distance_km <= self.MAX_DISTANCE_KM_LOW:
            warnings.append(ValidationWarning(
                level=WarningLevel.WARNING,
                message=f"Comparables are {avg_distance_km:.1f}km away on average. "
                        "Consider this a regional estimate rather than hyperlocal.",
                code="DISTANCE_HIGH"
            ))
            return 0.4

        else:
            warnings.append(ValidationWarning(
                level=WarningLevel.ERROR,
                message=f"Comparables are very far away ({avg_distance_km:.1f}km average). "
                        "Sparse data area - estimate may not reflect local market.",
                code="DISTANCE_VERY_HIGH"
            ))
            return 0.2

    def _check_price_dispersion(
        self,
        cv: float,
        warnings: List[ValidationWarning]
    ) -> float:
        """
        Check price dispersion (coefficient of variation).

        Args:
            cv: Coefficient of variation (std_dev / mean)
            warnings: List to append warnings to

        Returns:
            Quality factor (0-1)
        """

        if cv <= self.MAX_CV_HIGH:
            return 1.0

        elif cv <= self.MAX_CV_MEDIUM:
            warnings.append(ValidationWarning(
                level=WarningLevel.INFO,
                message=f"Moderate price variation among comparables (CV = {cv:.2f}). "
                        "Properties may have different characteristics.",
                code="PRICE_VARIATION_MODERATE"
            ))
            return 0.7

        elif cv <= self.MAX_CV_LOW:
            warnings.append(ValidationWarning(
                level=WarningLevel.WARNING,
                message=f"High price variation among comparables (CV = {cv:.2f}). "
                        "Consider this a rough estimate.",
                code="PRICE_VARIATION_HIGH"
            ))
            return 0.4

        else:
            warnings.append(ValidationWarning(
                level=WarningLevel.ERROR,
                message=f"Very high price variation (CV = {cv:.2f}). "
                        "Comparables may not be truly similar.",
                code="PRICE_VARIATION_VERY_HIGH"
            ))
            return 0.2

    def _check_temporal_adjustments(
        self,
        comparables: List[Dict],
        warnings: List[ValidationWarning]
    ):
        """
        Check if temporal adjustments were applied successfully.

        Args:
            comparables: List of comparable dicts
            warnings: List to append warnings to
        """

        # Count how many comparables used fallback (no temporal adjustment)
        fallback_count = 0

        for comp in comparables:
            # Check if adjustment metadata exists (Phase 1 might not store this)
            # This is a placeholder for future enhancement
            pass

        # If significant fallback rate, warn user
        if fallback_count > len(comparables) * 0.3:
            warnings.append(ValidationWarning(
                level=WarningLevel.WARNING,
                message="Some price adjustments used fallback methods. "
                        "Temporal accuracy may be reduced.",
                code="TEMPORAL_FALLBACK"
            ))

    def _determine_confidence_level(self, quality_score: float) -> ConfidenceLevel:
        """
        Determine confidence level from quality score.

        Args:
            quality_score: Overall quality score (0-1)

        Returns:
            ConfidenceLevel enum value
        """

        if quality_score >= 0.75:
            return ConfidenceLevel.HIGH

        elif quality_score >= 0.50:
            return ConfidenceLevel.MEDIUM

        else:
            return ConfidenceLevel.LOW
