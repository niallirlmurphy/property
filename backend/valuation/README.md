# Valuation Module

Property valuation using comparable sales analysis.

## Components

### models.py (341 lines)
Pydantic schemas for request/response validation:
- `ValuationRequest` - Input schema (address, eircode, date)
- `ValuationResponse` - Output schema (estimate, interval, comparables)
- `ComparableProperty` - Individual comparable
- `ConfidenceInterval`, `ValidationResult`, `ValuationStatistics`

### geocoder.py
Address geocoding from our own data, most to least specific:
1. Exact address match (any PPR sale since 2010)
2. Development/street match for unsold units ("Apt 21, The Oak, Parkview" ->
   median of the block's sales), rejected if the matches are spread out
3. Locality match ("Stepaside")
4. Routing-key centroid (Eircode, or "Dublin N" in the address)
5. County centroid (always available)

Database levels must fall inside the routing key (10km for Dublin districts).
No Nominatim: OSM can't resolve Irish scheme names and returns wrong-town matches.

### comparable_search.py (194 lines)
Adaptive radius search for comparable properties:
- Start at 1km, expand to 2km, 5km, 10km, 20km as needed
- Uses `ST_DWithin` with GIST spatial index
- Filters: not_full_market_price = FALSE, last 3 years
- Orders by distance and recency

### adjustments.py (222 lines)
Price adjustments and weighting:
- `adjust_temporal()` - County price index adjustment
- `calculate_weight()` - Distance + recency weighting
- Formula: weight = distance_factor² × recency_score

### calculator.py (157 lines)
Valuation calculation:
- Weighted average from comparables
- Confidence interval (± k × weighted_std_dev)
- Statistics: mean, median, std_dev, CV, min, max

### validator.py (285 lines)
Quality validation and confidence scoring:
- Checks: min comparables, average distance, price dispersion
- Assigns confidence level (high/medium/low)
- Generates warnings for quality issues

### api.py (299 lines)
FastAPI endpoint:
- `POST /api/valuation/estimate`
- Orchestrates full pipeline (geocode → search → adjust → calculate → validate)
- Background logging to database
- Error handling + Sentry integration

## Total
**1,806 lines** of production-ready Python code.

## Usage

```python
from fastapi import FastAPI
from valuation.api import router as valuation_router

app = FastAPI()
app.include_router(valuation_router)
```

## Testing

See `tests/test_valuation.py` for unit tests.

## Phase 1 Status

✅ All core components implemented
✅ Database schema applied
✅ Ready for integration testing

Next: Add router to main.py, write tests, build frontend.
