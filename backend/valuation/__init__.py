"""
Property Valuation Module

Provides automated property valuation using comparable sales analysis.

Phase 1: Temporal adjustments (distance + recency weighting)
Phase 2: Feature-based adjustments (bedrooms, property type, BER)
Phase 3: ML models (XGBoost/LightGBM)

Components:
- geocoder: Address → coordinates
- comparable_search: Find similar properties
- adjustments: Price adjustments (temporal, features)
- calculator: Weighted average + confidence intervals
- validator: Quality checks + warnings
- api: FastAPI endpoints
"""

__version__ = "1.0.0-mvp"

from .models import (
    ValuationRequest,
    ValuationResponse,
    ComparableProperty,
    ConfidenceInterval,
    ValidationResult
)

__all__ = [
    "ValuationRequest",
    "ValuationResponse",
    "ComparableProperty",
    "ConfidenceInterval",
    "ValidationResult",
]
