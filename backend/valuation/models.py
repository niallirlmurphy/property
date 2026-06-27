"""
Pydantic models for valuation API.

Defines request/response schemas with validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level for valuation estimate."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WarningLevel(str, Enum):
    """Warning severity level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValuationRequest(BaseModel):
    """Request schema for property valuation."""

    address: str = Field(
        ...,
        min_length=5,
        max_length=500,
        example="28 Slane Road, Crumlin, Dublin 12",
        description="Full property address"
    )

    eircode: Optional[str] = Field(
        None,
        min_length=7,
        max_length=8,
        example="D12XY34",
        description="Irish Eircode (optional, improves geocoding accuracy)"
    )

    valuation_date: Optional[datetime] = Field(
        None,
        description="Valuation date (defaults to now)"
    )

    bedrooms: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Number of bedrooms (optional, helps find better comparables)"
    )

    ber_rating: Optional[str] = Field(
        None,
        max_length=2,
        example="B2",
        description="BER energy rating (optional, A1-G)"
    )

    @validator('ber_rating')
    def validate_ber_rating(cls, v):
        """Validate BER rating format."""
        if v is None:
            return v

        v_upper = v.upper()
        valid_ratings = [
            "A1", "A2", "A3", "B1", "B2", "B3",
            "C1", "C2", "C3", "D1", "D2",
            "E1", "E2", "F", "G"
        ]

        if v_upper not in valid_ratings:
            raise ValueError(f"Invalid BER rating. Must be one of: {', '.join(valid_ratings)}")

        return v_upper

    @validator('eircode')
    def validate_eircode_format(cls, v):
        """Validate Eircode format (3 chars + 4 chars, optional space)."""
        if v is None:
            return v

        # Remove spaces
        eircode_clean = v.replace(" ", "").upper()

        # Check length
        if len(eircode_clean) != 7:
            raise ValueError("Eircode must be 7 characters (e.g., D02X285)")

        # Check format: 3 alphanumeric + 4 alphanumeric
        if not (eircode_clean[:3].isalnum() and eircode_clean[3:].isalnum()):
            raise ValueError("Invalid Eircode format")

        return eircode_clean

    class Config:
        schema_extra = {
            "example": {
                "address": "28 Slane Road, Crumlin, Dublin 12",
                "eircode": "D12XY34",
                "valuation_date": "2026-06-23T12:00:00Z"
            }
        }


class ComparableProperty(BaseModel):
    """A single comparable property used in valuation."""

    id: int = Field(..., description="Property ID from database")

    address: str = Field(..., description="Property address")

    price: float = Field(..., gt=0, description="Original sale price (€)")

    adjusted_price: float = Field(
        ...,
        gt=0,
        description="Price adjusted to valuation date (€)"
    )

    sale_date: datetime = Field(..., description="Date of sale")

    distance_m: float = Field(
        ...,
        ge=0,
        description="Distance from subject property (meters)"
    )

    weight: float = Field(
        ...,
        ge=0,
        le=1,
        description="Weight in valuation calculation (0-1)"
    )

    # Optional features (Phase 2+)
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    property_type: Optional[str] = Field(None, description="Property type")
    ber_rating: Optional[str] = Field(None, description="BER energy rating")

    # Adjustment details
    temporal_adjustment_factor: Optional[float] = Field(
        None,
        description="Temporal price adjustment factor applied"
    )

    recency_score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Recency score (0-1, recent = higher)"
    )

    class Config:
        schema_extra = {
            "example": {
                "id": 123456,
                "address": "30 Slane Road, Crumlin, Dublin 12",
                "price": 380000,
                "adjusted_price": 405000,
                "sale_date": "2024-03-15T00:00:00Z",
                "distance_m": 150.5,
                "weight": 0.85,
                "bedrooms": 3,
                "property_type": "Semi-detached house",
                "temporal_adjustment_factor": 1.065,
                "recency_score": 0.78
            }
        }


class ConfidenceInterval(BaseModel):
    """Confidence interval for valuation estimate."""

    lower: int = Field(..., gt=0, description="Lower bound (€)")

    upper: int = Field(..., gt=0, description="Upper bound (€)")

    width_pct: float = Field(
        ...,
        ge=0,
        le=200,  # Can exceed 100% for very uncertain valuations
        description="Interval width as percentage of estimate"
    )

    @validator('upper')
    def upper_must_be_greater_than_lower(cls, v, values):
        """Ensure upper bound > lower bound."""
        if 'lower' in values and v <= values['lower']:
            raise ValueError("upper must be greater than lower")
        return v


class ValidationWarning(BaseModel):
    """A validation warning or quality issue."""

    level: WarningLevel = Field(..., description="Warning severity")

    message: str = Field(..., description="Human-readable warning message")

    code: Optional[str] = Field(None, description="Machine-readable warning code")


class ValidationResult(BaseModel):
    """Validation result for valuation quality."""

    is_valid: bool = Field(..., description="Whether valuation passes minimum standards")

    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Overall confidence level (high/medium/low)"
    )

    quality_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Quality score (0-1, higher = better)"
    )

    warnings: List[ValidationWarning] = Field(
        default_factory=list,
        description="List of warnings or quality issues"
    )

    n_comparables: int = Field(..., ge=0, description="Number of comparables used")

    avg_distance_km: float = Field(
        ...,
        ge=0,
        description="Average distance to comparables (km)"
    )

    price_dispersion_cv: Optional[float] = Field(
        None,
        ge=0,
        description="Coefficient of variation in comparable prices"
    )


class ValuationStatistics(BaseModel):
    """Statistical details about valuation calculation."""

    mean_price: float = Field(..., gt=0, description="Mean of adjusted comparable prices")

    median_price: float = Field(..., gt=0, description="Median of adjusted comparable prices")

    std_dev: float = Field(..., ge=0, description="Standard deviation of prices")

    coefficient_of_variation: float = Field(
        ...,
        ge=0,
        description="CV = std_dev / mean (price dispersion)"
    )

    min_price: float = Field(..., gt=0, description="Minimum comparable price")

    max_price: float = Field(..., gt=0, description="Maximum comparable price")


class GeocodingResult(BaseModel):
    """Geocoding result with confidence score."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    confidence: float = Field(..., ge=0, le=1, description="Geocoding confidence (0-1)")
    method: str = Field(..., description="Geocoding method used")
    address_matched: Optional[str] = Field(None, description="Matched address")


class ValuationResponse(BaseModel):
    """Response schema for property valuation."""

    # Core estimate
    estimate: int = Field(
        ...,
        gt=0,
        description="Estimated property value (€)"
    )

    # Confidence interval
    confidence_interval: ConfidenceInterval = Field(
        ...,
        description="Confidence interval (lower/upper bounds)"
    )

    # Quality assessment
    validation: ValidationResult = Field(
        ...,
        description="Validation result and warnings"
    )

    # Comparable properties used
    comparables: List[ComparableProperty] = Field(
        ...,
        min_items=1,
        description="List of comparable properties used"
    )

    # Statistical details
    statistics: ValuationStatistics = Field(
        ...,
        description="Statistical details about calculation"
    )

    # Metadata
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata (geocoding, algorithm version, etc.)"
    )

    class Config:
        schema_extra = {
            "example": {
                "estimate": 425000,
                "confidence_interval": {
                    "lower": 380000,
                    "upper": 470000,
                    "width_pct": 21.2
                },
                "validation": {
                    "is_valid": True,
                    "confidence_level": "medium",
                    "quality_score": 0.75,
                    "warnings": [
                        {
                            "level": "info",
                            "message": "Some comparables are more than 5km away",
                            "code": "DISTANCE_HIGH"
                        }
                    ],
                    "n_comparables": 12,
                    "avg_distance_km": 2.3,
                    "price_dispersion_cv": 0.18
                },
                "comparables": [
                    {
                        "id": 123456,
                        "address": "30 Slane Road, Crumlin, Dublin 12",
                        "price": 380000,
                        "adjusted_price": 405000,
                        "sale_date": "2024-03-15T00:00:00Z",
                        "distance_m": 150.5,
                        "weight": 0.85
                    }
                ],
                "statistics": {
                    "mean_price": 428500,
                    "median_price": 425000,
                    "std_dev": 45000,
                    "coefficient_of_variation": 0.105,
                    "min_price": 350000,
                    "max_price": 510000
                },
                "metadata": {
                    "geocoded_location": {
                        "latitude": 53.3217,
                        "longitude": -6.3167,
                        "confidence": 0.95,
                        "method": "eircode"
                    },
                    "valuation_date": "2026-06-23T12:00:00Z",
                    "algorithm_version": "1.0.0-mvp",
                    "processing_time_ms": 850
                }
            }
        }
