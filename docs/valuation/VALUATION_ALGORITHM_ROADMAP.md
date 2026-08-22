# Property Valuation Algorithm Implementation Roadmap

## Phase 1: MVP (Minimum Viable Product)
**Timeline:** 4-6 weeks  
**Accuracy Target:** 15-25% MAPE urban, 20-35% rural  
**Goal:** Deliver basic comparable-sales valuation with working API

---

### Phase 1.1: Database Foundation (Week 1)

**Database Schema Changes:**

```sql
-- 1. Price indices materialized view (for temporal adjustments)
CREATE MATERIALIZED VIEW county_monthly_price_indices AS
WITH monthly_sales AS (
    SELECT 
        county,
        DATE_TRUNC('month', sale_date) AS month,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
        COUNT(*) AS sale_count
    FROM properties
    WHERE 
        not_full_market_price = FALSE
        AND sale_date >= '2020-01-01'
        AND price BETWEEN 50000 AND 5000000
        AND county IS NOT NULL
    GROUP BY county, month
    HAVING COUNT(*) >= 10
)
SELECT 
    county,
    month,
    median_price,
    sale_count,
    median_price / FIRST_VALUE(median_price) OVER (
        PARTITION BY county 
        ORDER BY month
    ) AS price_index
FROM monthly_sales;

CREATE INDEX idx_price_indices_lookup 
ON county_monthly_price_indices (county, month);

-- 2. Valuation requests tracking table
CREATE TABLE valuation_requests (
    id SERIAL PRIMARY KEY,
    request_id UUID DEFAULT gen_random_uuid(),
    address TEXT NOT NULL,
    eircode VARCHAR(8),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    property_type VARCHAR(50),
    bedrooms INTEGER,
    valuation_date TIMESTAMP DEFAULT NOW(),
    estimate INTEGER,
    confidence_level VARCHAR(20),
    n_comparables INTEGER,
    quality_score NUMERIC(3, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_valuation_requests_created 
ON valuation_requests (created_at DESC);

-- 3. Valuation comparables junction table (for analysis)
CREATE TABLE valuation_comparables (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES valuation_requests(request_id),
    property_id INTEGER REFERENCES properties(id),
    distance_m NUMERIC(10, 2),
    weight NUMERIC(4, 3),
    original_price INTEGER,
    adjusted_price INTEGER,
    adjustment_factor NUMERIC(4, 3)
);

CREATE INDEX idx_valuation_comparables_request 
ON valuation_comparables (request_id);
```

**Effort:** 2 days  
**Dependencies:** None

---

### Phase 1.2: Core Backend Components (Weeks 2-3)

**File Structure:**
```
backend/
  valuation/
    __init__.py
    geocoder.py          # Address → coordinates
    comparable_search.py # Find similar properties
    adjustments.py       # Price adjustment logic (MVP: temporal only)
    calculator.py        # Weighted average calculation
    validator.py         # Quality checks and warnings
    models.py            # Pydantic request/response models
    api.py               # FastAPI endpoint
```

**Implementation Order:**

**1. Geocoder Service (`geocoder.py`)** - 2 days
```python
class ValuationGeocoder:
    async def geocode_address(self, address: str, eircode: str = None):
        """
        Priority: 1) Eircode routing key, 2) Nominatim, 3) DB fuzzy match
        Returns: {'latitude': float, 'longitude': float, 'confidence': float}
        """
```

**2. Comparable Search (`comparable_search.py`)** - 3 days
```python
class ComparableSearcher:
    async def find_comparables(
        self, 
        latitude: float, 
        longitude: float,
        max_radius_km: float = 20,
        min_count: int = 10
    ) -> List[Dict]:
        """
        Multi-radius adaptive search: 1km → 2km → 5km → 10km → 20km
        Returns when >= min_count found
        """
```

**SQL Query (Critical for Performance):**
```sql
-- Use existing GIST index on geog column
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
    1.0 - (EXTRACT(EPOCH FROM (NOW() - p.sale_date)) / (3 * 365 * 86400)) AS recency_score
FROM properties p
CROSS JOIN subject_point sp
WHERE 
    p.geog IS NOT NULL
    AND p.not_full_market_price = FALSE
    AND p.price IS NOT NULL
    AND p.sale_date >= NOW() - INTERVAL '3 years'
    AND ST_DWithin(p.geog, sp.geog, $3)  -- Radius parameter (uses index)
ORDER BY distance_m ASC, recency_score DESC
LIMIT 30;
```

**3. MVP Adjustments (`adjustments.py`)** - 2 days
```python
class MVPAdjuster:
    async def adjust_temporal(self, sale_price: float, sale_date: datetime, 
                             target_date: datetime, county: str) -> Dict:
        """
        Lookup county monthly price index, calculate ratio
        Formula: adjusted_price = sale_price * (target_index / sale_index)
        """
    
    def calculate_weight(self, comparable: Dict, max_distance_m: float) -> float:
        """
        Simple distance-based weighting:
        weight = (1 - distance/max_distance)^2 * recency_score
        Range: 0.0 to 1.0
        """
```

**4. Calculator (`calculator.py`)** - 2 days
```python
class ValuationCalculator:
    def calculate_valuation(self, comparables: List[Dict], weights: List[float]) -> Dict:
        """
        Returns: {
            'estimate': weighted_mean,
            'confidence_interval': {'lower': x, 'upper': y},
            'statistics': {...}
        }
        """
```

**5. Validator (`validator.py`)** - 1 day
```python
class MVPValidator:
    def validate(self, valuation: Dict, comparables: List[Dict]) -> Dict:
        """
        Checks:
        - Minimum comparables (>= 5)
        - Price dispersion (CV < 0.4)
        - Average distance (< 15km)
        Returns: {'is_valid': bool, 'warnings': [], 'quality_score': float}
        """
```

**Effort:** 10 days  
**Dependencies:** Phase 1.1 complete

---

### Phase 1.3: API Endpoint (Week 3)

**API Implementation (`api.py`):**

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/valuation", tags=["valuation"])

class ValuationRequest(BaseModel):
    address: str = Field(..., example="28 Slane Road, Crumlin, Dublin 12")
    eircode: Optional[str] = None
    valuation_date: Optional[datetime] = None

class ComparableProperty(BaseModel):
    id: int
    address: str
    price: int
    adjusted_price: int
    sale_date: datetime
    distance_m: float
    weight: float

class ValuationResponse(BaseModel):
    estimate: int
    confidence_interval: Dict
    confidence_level: str  # "high", "medium", "low"
    comparables: List[ComparableProperty]
    validation: Dict
    metadata: Dict

@router.post("/estimate", response_model=ValuationResponse)
async def estimate_property_value(
    request: ValuationRequest,
    background_tasks: BackgroundTasks
):
    """
    MVP valuation endpoint.
    
    Algorithm:
    1. Geocode address → (lat, lon)
    2. Find comparables within 20km
    3. Adjust prices for time difference
    4. Calculate weighted average
    5. Validate and return
    """
    
    try:
        # Step 1: Geocode
        geocoder = ValuationGeocoder(db=db)
        location = await geocoder.geocode_address(request.address, request.eircode)
        
        # Step 2: Find comparables
        searcher = ComparableSearcher(db=db)
        comparables = await searcher.find_comparables(
            latitude=location['latitude'],
            longitude=location['longitude']
        )
        
        if len(comparables) < 5:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient comparable sales found ({len(comparables)})"
            )
        
        # Step 3: Adjust prices
        adjuster = MVPAdjuster(db=db)
        target_date = request.valuation_date or datetime.now()
        
        for comp in comparables:
            # Temporal adjustment
            temporal = await adjuster.adjust_temporal(
                sale_price=comp['price'],
                sale_date=comp['sale_date'],
                target_date=target_date,
                county=comp['county']
            )
            comp['adjusted_price'] = temporal['adjusted_price']
            
            # Calculate weight
            max_distance = max(c['distance_m'] for c in comparables)
            comp['weight'] = adjuster.calculate_weight(comp, max_distance)
        
        # Step 4: Calculate valuation
        calculator = ValuationCalculator()
        weights = [c['weight'] for c in comparables]
        valuation = calculator.calculate_valuation(comparables, weights)
        
        # Step 5: Validate
        validator = MVPValidator()
        validation = validator.validate(valuation, comparables)
        
        # Log request (background task)
        background_tasks.add_task(
            log_valuation_request,
            request=request,
            location=location,
            valuation=valuation,
            comparables=comparables
        )
        
        return ValuationResponse(
            estimate=valuation['estimate'],
            confidence_interval=valuation['confidence_interval'],
            confidence_level=validation['confidence_level'],
            comparables=[
                ComparableProperty(
                    id=c['id'],
                    address=c['address'],
                    price=c['price'],
                    adjusted_price=c['adjusted_price'],
                    sale_date=c['sale_date'],
                    distance_m=c['distance_m'],
                    weight=c['weight']
                )
                for c in comparables
            ],
            validation=validation,
            metadata={
                'geocoded_location': location,
                'valuation_date': target_date.isoformat(),
                'algorithm_version': '1.0.0-mvp'
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log to Sentry
        raise HTTPException(status_code=500, detail="Valuation failed")

async def log_valuation_request(request, location, valuation, comparables):
    """Background task: Log request to database for analytics."""
    pass  # Implementation in Phase 1.4
```

**New Routes to Add to `backend/main.py`:**
```python
from valuation.api import router as valuation_router

app.include_router(valuation_router)
```

**Effort:** 3 days  
**Dependencies:** Phase 1.2 complete

---

### Phase 1.4: Testing & Validation (Week 4)

**Unit Tests (`tests/test_valuation.py`):**

```python
import pytest
from valuation.geocoder import ValuationGeocoder
from valuation.comparable_search import ComparableSearcher
from valuation.adjustments import MVPAdjuster
from valuation.calculator import ValuationCalculator

@pytest.mark.asyncio
async def test_geocoder_eircode_lookup():
    """Test Eircode routing key geocoding."""
    geocoder = ValuationGeocoder(db=test_db)
    result = await geocoder.geocode_address("Dublin", eircode="D02X285")
    
    assert result['latitude'] is not None
    assert result['longitude'] is not None
    assert result['confidence'] >= 0.7

@pytest.mark.asyncio
async def test_comparable_search_dublin():
    """Test comparable search in high-density area."""
    searcher = ComparableSearcher(db=test_db)
    comparables = await searcher.find_comparables(
        latitude=53.3498,
        longitude=-6.2603,
        min_count=10
    )
    
    assert len(comparables) >= 10
    assert all(c['distance_m'] <= 20000 for c in comparables)
    assert all(c['price'] is not None for c in comparables)

@pytest.mark.asyncio
async def test_comparable_search_rural():
    """Test comparable search in sparse rural area."""
    searcher = ComparableSearcher(db=test_db)
    comparables = await searcher.find_comparables(
        latitude=53.8217,  # Nobber, Co. Meath
        longitude=-6.7479,
        min_count=5
    )
    
    # Should find at least some comparables even in rural areas
    assert len(comparables) >= 5

def test_temporal_adjustment():
    """Test price index temporal adjustment."""
    adjuster = MVPAdjuster(db=test_db)
    
    # Test 1 year growth at 5% annual
    result = adjuster.adjust_temporal(
        sale_price=400000,
        sale_date=datetime(2025, 1, 1),
        target_date=datetime(2026, 1, 1),
        county="Dublin"
    )
    
    # Should be roughly 420k (5% growth)
    assert 410000 <= result['adjusted_price'] <= 430000

def test_weight_calculation():
    """Test distance-based weighting."""
    adjuster = MVPAdjuster(db=test_db)
    
    # Close property = high weight
    close_weight = adjuster.calculate_weight(
        {'distance_m': 100, 'recency_score': 0.9},
        max_distance_m=5000
    )
    assert close_weight > 0.8
    
    # Distant property = low weight
    far_weight = adjuster.calculate_weight(
        {'distance_m': 4800, 'recency_score': 0.5},
        max_distance_m=5000
    )
    assert far_weight < 0.3

def test_valuation_calculator():
    """Test weighted average calculation."""
    calculator = ValuationCalculator()
    
    comparables = [
        {'adjusted_price': 400000},
        {'adjusted_price': 420000},
        {'adjusted_price': 410000}
    ]
    weights = [0.8, 0.6, 0.7]
    
    result = calculator.calculate_valuation(comparables, weights)
    
    assert 405000 <= result['estimate'] <= 415000
    assert 'confidence_interval' in result
    assert result['confidence_interval']['lower'] < result['estimate']
    assert result['confidence_interval']['upper'] > result['estimate']

@pytest.mark.asyncio
async def test_valuation_endpoint_integration(test_client):
    """Integration test for full valuation endpoint."""
    response = await test_client.post("/api/valuation/estimate", json={
        "address": "28 Slane Road, Crumlin, Dublin 12",
        "eircode": "D12XY34"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['estimate'] > 0
    assert len(data['comparables']) >= 5
    assert data['validation']['is_valid'] is True
    assert data['confidence_level'] in ['high', 'medium', 'low']
```

**Accuracy Validation Script (`scripts/validate_valuation_accuracy.py`):**

```python
"""
Validate valuation accuracy on known recent sales.

Method:
1. Sample 100 properties sold in last 6 months
2. Run valuation on each (excluding the property itself)
3. Calculate MAPE (Mean Absolute Percentage Error)
4. Analyze by county and property type

Target: MAPE < 25% for MVP
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta

async def validate_valuation_accuracy():
    # Fetch test properties
    query = """
        SELECT id, address, eircode, price, sale_date, county, property_type
        FROM properties
        WHERE 
            sale_date >= NOW() - INTERVAL '6 months'
            AND not_full_market_price = FALSE
            AND price BETWEEN 100000 AND 1000000
            AND latitude IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 100
    """
    
    test_properties = await db.fetch(query)
    
    results = []
    
    for prop in test_properties:
        # Run valuation
        try:
            valuation = await estimate_property_value_internal(
                address=prop['address'],
                eircode=prop['eircode'],
                valuation_date=prop['sale_date'],
                exclude_property_id=prop['id']  # Important: don't use itself as comparable
            )
            
            actual_price = prop['price']
            estimated_price = valuation['estimate']
            
            error_pct = abs(estimated_price - actual_price) / actual_price * 100
            
            results.append({
                'property_id': prop['id'],
                'address': prop['address'],
                'county': prop['county'],
                'property_type': prop['property_type'],
                'actual_price': actual_price,
                'estimated_price': estimated_price,
                'error_pct': error_pct,
                'confidence_level': valuation['confidence_level'],
                'n_comparables': len(valuation['comparables'])
            })
            
        except Exception as e:
            print(f"Failed for {prop['address']}: {e}")
            continue
    
    # Analyze results
    df = pd.DataFrame(results)
    
    print("\n=== VALUATION ACCURACY REPORT ===")
    print(f"Sample size: {len(df)}")
    print(f"\nOverall MAPE: {df['error_pct'].mean():.1f}%")
    print(f"Median Error: {df['error_pct'].median():.1f}%")
    print(f"Error Std Dev: {df['error_pct'].std():.1f}%")
    
    print("\n--- By County ---")
    print(df.groupby('county')['error_pct'].agg(['count', 'mean', 'median']))
    
    print("\n--- By Confidence Level ---")
    print(df.groupby('confidence_level')['error_pct'].agg(['count', 'mean', 'median']))
    
    print("\n--- Error Distribution ---")
    print(f"<10% error: {(df['error_pct'] < 10).sum()} ({(df['error_pct'] < 10).mean()*100:.1f}%)")
    print(f"<20% error: {(df['error_pct'] < 20).sum()} ({(df['error_pct'] < 20).mean()*100:.1f}%)")
    print(f"<30% error: {(df['error_pct'] < 30).sum()} ({(df['error_pct'] < 30).mean()*100:.1f}%)")
    print(f">50% error: {(df['error_pct'] > 50).sum()} ({(df['error_pct'] > 50).mean()*100:.1f}%)")
    
    # Save detailed results
    df.to_csv('valuation_accuracy_results.csv', index=False)
    print("\nDetailed results saved to valuation_accuracy_results.csv")

if __name__ == "__main__":
    asyncio.run(validate_valuation_accuracy())
```

**Effort:** 5 days  
**Dependencies:** Phase 1.3 complete

---

### Phase 1.5: Basic Frontend (Week 5)

**New Component: Valuation Page (`frontend/src/pages/ValuationPage.tsx`)**

```typescript
import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { api } from '../api';

interface ValuationResult {
  estimate: number;
  confidence_interval: {
    lower: number;
    upper: number;
    width_pct: number;
  };
  confidence_level: string;
  comparables: Array<{
    id: number;
    address: string;
    price: number;
    adjusted_price: number;
    distance_m: number;
    weight: number;
  }>;
  validation: {
    is_valid: boolean;
    warnings: Array<{level: string; message: string}>;
    quality_score: number;
  };
}

export const ValuationPage: React.FC = () => {
  const [address, setAddress] = useState('');
  const [eircode, setEircode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/valuation/estimate', {
        address,
        eircode: eircode || undefined
      });
      
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Valuation failed');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => 
    `€${price.toLocaleString('en-IE')}`;

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Property Valuation</h1>
      
      {/* Input Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Address *
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g., 28 Slane Road, Crumlin, Dublin 12"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              Eircode (Optional)
            </label>
            <input
              type="text"
              value={eircode}
              onChange={(e) => setEircode(e.target.value.toUpperCase())}
              placeholder="e.g., D12 XY34"
              className="w-full border rounded px-3 py-2"
              maxLength={8}
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Calculating...' : 'Get Valuation'}
          </button>
        </form>
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
            {error}
          </div>
        )}
      </div>
      
      {/* Results */}
      {result && (
        <>
          {/* Valuation Summary */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">Estimated Value</h2>
            
            <div className="text-5xl font-bold text-blue-600 mb-4">
              {formatPrice(result.estimate)}
            </div>
            
            <div className="text-sm text-gray-600 mb-4">
              Confidence Range: {formatPrice(result.confidence_interval.lower)} - {formatPrice(result.confidence_interval.upper)}
              <span className="ml-2 text-xs">
                (±{result.confidence_interval.width_pct.toFixed(1)}%)
              </span>
            </div>
            
            <div className={`text-sm font-medium ${getConfidenceColor(result.confidence_level)}`}>
              Confidence: {result.confidence_level.toUpperCase()}
              <span className="ml-2 text-gray-600">
                (Quality Score: {(result.validation.quality_score * 100).toFixed(0)}/100)
              </span>
            </div>
            
            {/* Warnings */}
            {result.validation.warnings.length > 0 && (
              <div className="mt-4 space-y-2">
                {result.validation.warnings.map((warning, idx) => (
                  <div 
                    key={idx}
                    className={`text-sm p-2 rounded ${
                      warning.level === 'warning' 
                        ? 'bg-yellow-50 text-yellow-800' 
                        : 'bg-blue-50 text-blue-800'
                    }`}
                  >
                    {warning.message}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Comparables Table */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h3 className="text-xl font-bold mb-4">
              Comparable Sales ({result.comparables.length})
            </h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Address</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Sale Price</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Adjusted Price</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Distance</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Weight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.comparables.map((comp) => (
                    <tr key={comp.id}>
                      <td className="px-4 py-2 text-sm">{comp.address}</td>
                      <td className="px-4 py-2 text-sm text-right">{formatPrice(comp.price)}</td>
                      <td className="px-4 py-2 text-sm text-right font-medium">{formatPrice(comp.adjusted_price)}</td>
                      <td className="px-4 py-2 text-sm text-right">{(comp.distance_m / 1000).toFixed(2)} km</td>
                      <td className="px-4 py-2 text-sm text-right">{(comp.weight * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Map (placeholder for Phase 1) */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold mb-4">Comparable Locations</h3>
            <div className="bg-gray-100 h-64 rounded flex items-center justify-center text-gray-500">
              Map visualization coming in Phase 2
            </div>
          </div>
        </>
      )}
      
      {/* Disclaimer */}
      <div className="mt-8 p-4 bg-gray-50 rounded text-sm text-gray-600">
        <strong>Disclaimer:</strong> This valuation is an automated estimate based on comparable sales data. 
        It should not be used as the sole basis for property transactions. For official valuations, 
        consult a qualified property valuer.
      </div>
    </div>
  );
};
```

**Add Route (`frontend/src/App.tsx`):**
```typescript
import { ValuationPage } from './pages/ValuationPage';

// In Routes:
<Route path="/valuation" element={<ValuationPage />} />
```

**Effort:** 4 days  
**Dependencies:** Phase 1.3 complete

---

### Phase 1.6: Deployment & Monitoring (Week 6)

**Deployment Checklist:**

1. **Database Migration (Production):**
```bash
# Apply schema changes on Supabase
psql $DATABASE_URL < db/phase1_schema.sql

# Refresh materialized view
psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW county_monthly_price_indices;"
```

2. **Backend Deployment (Railway):**
```bash
# Ensure dependencies updated
pip freeze > backend/requirements.txt

# Railway will auto-deploy on push
git add backend/
git commit -m "Add valuation API MVP"
git push origin main
```

3. **Frontend Deployment (Vercel):**
```bash
# Add valuation page
git add frontend/src/pages/ValuationPage.tsx
git commit -m "Add valuation page MVP"
git push origin main

# Vercel auto-deploys
```

4. **Monitoring Setup:**

Add to `backend/valuation/api.py`:
```python
import sentry_sdk
from datetime import datetime

@router.post("/estimate")
async def estimate_property_value(request: ValuationRequest):
    start_time = datetime.now()
    
    try:
        # ... existing code ...
        
        # Track metrics
        sentry_sdk.set_context("valuation", {
            "address": request.address,
            "n_comparables": len(comparables),
            "confidence_level": valuation['confidence_level'],
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        })
        
        return response
    
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
```

5. **Create Monthly Refresh Cron:**

Add to `backend/cron_jobs.py`:
```python
@cron.job(schedule="0 3 1 * *")  # 3 AM on 1st of month
async def refresh_price_indices():
    """Refresh county price indices monthly."""
    await db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY county_monthly_price_indices;")
    print("Price indices refreshed")
```

**Effort:** 2 days  
**Dependencies:** Phase 1.5 complete

---

## Phase 1 Summary

**Total Timeline:** 6 weeks  
**Total Effort:** ~25 working days

**Deliverables:**
- ✅ Working valuation API endpoint
- ✅ Basic web interface for valuations
- ✅ Temporal price adjustment (county-level)
- ✅ Distance-based weighting
- ✅ Confidence scoring
- ✅ Unit tests (80% coverage)
- ✅ Accuracy validation (target: MAPE < 25%)
- ✅ Production deployment
- ✅ Monitoring and logging

**Expected Accuracy:**
- **Urban (Dublin, Cork, Galway):** 15-25% MAPE
- **Suburban/Large Towns:** 20-30% MAPE
- **Rural:** 25-35% MAPE

**Data Requirements:**
- ✅ No additional data needed (works with existing 90.7% geocoded properties)
- ✅ Uses existing database indexes
- ✅ Monthly refresh of price indices

**Performance Targets:**
- API response time: <2 seconds (p95)
- Comparable search: <500ms (with GIST index)
- Database load: Minimal (read-only queries)

---

## Phase 2: Enhanced Adjustments & Confidence

**Timeline:** 4-6 weeks  
**Accuracy Target:** 12-20% MAPE urban, 18-28% rural  
**Goal:** Add feature-based adjustments and improve confidence scoring

---

### Phase 2.1: Hedonic Price Model Training (Weeks 1-2)

**Objective:** Train statistical models to quantify bedroom, property type, and BER value adjustments.

**New Database Schema:**

```sql
-- Store trained hedonic coefficients
CREATE TABLE hedonic_coefficients (
    id SERIAL PRIMARY KEY,
    county VARCHAR(50),
    property_type VARCHAR(50),
    
    -- Coefficients (log-linear model)
    intercept NUMERIC(12, 4),
    bedroom_value NUMERIC(10, 2),  -- € per bedroom
    apartment_discount NUMERIC(5, 4),  -- % discount vs houses
    ber_a_premium NUMERIC(5, 4),  -- % premium for A-rated
    ber_b_premium NUMERIC(5, 4),
    ber_c_baseline NUMERIC(5, 4),  -- baseline = 0
    ber_d_discount NUMERIC(5, 4),  -- % discount
    ber_e_discount NUMERIC(5, 4),
    ber_f_discount NUMERIC(5, 4),
    
    -- Model quality metrics
    r_squared NUMERIC(5, 4),
    sample_size INTEGER,
    train_start_date DATE,
    train_end_date DATE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_hedonic_coefficients_county 
ON hedonic_coefficients (county, updated_at DESC);
```

**Training Script (`scripts/train_hedonic_models.py`):**

```python
"""
Train county-level hedonic price models.

Method: Log-linear regression
Formula: log(price) = β₀ + β₁·bedrooms + β₂·type + β₃·BER + ε

Run monthly to update coefficients.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import asyncpg

async def train_hedonic_models():
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Fetch training data (2022+ sales with features)
    query = """
        SELECT 
            county,
            property_type,
            bedrooms,
            ber_rating,
            price,
            sale_date
        FROM properties
        WHERE 
            not_full_market_price = FALSE
            AND sale_date >= '2022-01-01'
            AND bedrooms IS NOT NULL
            AND property_type IS NOT NULL
            AND price BETWEEN 50000 AND 5000000
    """
    
    df = pd.DataFrame(await conn.fetch(query))
    print(f"Training data: {len(df):,} properties")
    
    # Log-transform price (normalize distribution)
    df['log_price'] = np.log(df['price'])
    
    # One-hot encode categorical variables
    df = pd.get_dummies(df, columns=['property_type', 'ber_rating'], drop_first=True)
    
    # Train model per county
    coefficients = []
    
    for county in df['county'].unique():
        county_data = df[df['county'] == county]
        
        if len(county_data) < 100:
            print(f"Skipping {county} (only {len(county_data)} properties)")
            continue
        
        # Separate features and target
        feature_cols = [c for c in county_data.columns if c.startswith(('bedrooms', 'property_type_', 'ber_rating_'))]
        X = county_data[feature_cols]
        y = county_data['log_price']
        
        # Train Ridge regression (regularized to prevent overfitting)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = Ridge(alpha=1.0)
        model.fit(X_scaled, y)
        
        # Cross-validation R²
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')
        r_squared = cv_scores.mean()
        
        # Extract coefficients
        coef_dict = {
            'county': county,
            'intercept': model.intercept_,
            'bedroom_value': model.coef_[0] * scaler.scale_[0],  # Unscale
            'r_squared': r_squared,
            'sample_size': len(county_data),
            'train_start_date': county_data['sale_date'].min(),
            'train_end_date': county_data['sale_date'].max()
        }
        
        # Extract property type coefficients (if available)
        type_cols = [c for c in feature_cols if c.startswith('property_type_')]
        if type_cols:
            coef_dict['apartment_discount'] = model.coef_[feature_cols.index(type_cols[0])]
        
        # Extract BER coefficients
        ber_cols = [c for c in feature_cols if c.startswith('ber_rating_')]
        for ber_col in ber_cols:
            rating = ber_col.replace('ber_rating_', '').lower()
            coef_dict[f'ber_{rating}_premium'] = model.coef_[feature_cols.index(ber_col)]
        
        coefficients.append(coef_dict)
        
        print(f"{county}: R²={r_squared:.3f}, n={len(county_data):,}")
    
    # Save to database
    await save_coefficients(conn, coefficients)
    await conn.close()
    
    print(f"\nTrained models for {len(coefficients)} counties")

async def save_coefficients(conn, coefficients):
    """Insert coefficients into database."""
    for coef in coefficients:
        await conn.execute("""
            INSERT INTO hedonic_coefficients 
            (county, intercept, bedroom_value, apartment_discount, 
             ber_a_premium, ber_b_premium, ber_c_baseline, ber_d_discount,
             r_squared, sample_size, train_start_date, train_end_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, 
        coef['county'], coef['intercept'], coef['bedroom_value'],
        coef.get('apartment_discount', 0),
        coef.get('ber_a_premium', 0), coef.get('ber_b_premium', 0),
        0.0,  # baseline
        coef.get('ber_d_discount', 0),
        coef['r_squared'], coef['sample_size'],
        coef['train_start_date'], coef['train_end_date']
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(train_hedonic_models())
```

**Run Initial Training:**
```bash
python3 scripts/train_hedonic_models.py
```

**Expected Output:**
```
Training data: 215,432 properties
Dublin: R²=0.687, n=87,342
Cork: R²=0.645, n=24,156
Galway: R²=0.612, n=12,847
...
Trained models for 26 counties
```

**Effort:** 5 days (includes model experimentation)

---

### Phase 2.2: Enhanced Adjustment Classes (Week 2)

**Update `backend/valuation/adjustments.py`:**

```python
class EnhancedAdjuster:
    """
    Phase 2: Add feature-based adjustments (bedrooms, type, BER).
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.coefficients_cache = {}
    
    async def load_coefficients(self, county: str) -> Dict:
        """Load pre-trained hedonic coefficients for county."""
        if county in self.coefficients_cache:
            return self.coefficients_cache[county]
        
        query = """
            SELECT 
                intercept, bedroom_value, apartment_discount,
                ber_a_premium, ber_b_premium, ber_c_baseline, 
                ber_d_discount, ber_e_discount, ber_f_discount
            FROM hedonic_coefficients
            WHERE county = $1
            ORDER BY updated_at DESC
            LIMIT 1
        """
        
        result = await self.db.fetchrow(query, county)
        
        if not result:
            # Fallback to national average
            result = await self.db.fetchrow(
                query.replace("WHERE county = $1", "WHERE county = 'National'")
            )
        
        coef = dict(result) if result else {}
        self.coefficients_cache[county] = coef
        return coef
    
    async def adjust_for_bedrooms(
        self,
        comp_price: float,
        comp_bedrooms: int,
        input_bedrooms: int,
        county: str
    ) -> Dict:
        """
        Adjust comparable price for bedroom difference.
        
        Formula: adjusted_price = comp_price * exp(β_bedrooms * bedroom_diff)
        """
        if not comp_bedrooms or not input_bedrooms:
            return {'adjusted_price': comp_price, 'factor': 1.0, 'reason': 'Missing bedroom data'}
        
        bedroom_diff = input_bedrooms - comp_bedrooms
        
        if bedroom_diff == 0:
            return {'adjusted_price': comp_price, 'factor': 1.0, 'reason': 'Same bedrooms'}
        
        # Load coefficients
        coef = await self.load_coefficients(county)
        bedroom_value = coef.get('bedroom_value', 40000)  # Default €40k/bed
        
        # Multiplicative adjustment
        adjustment_factor = 1.0 + (bedroom_diff * bedroom_value / comp_price)
        
        # Cap at ±30% to avoid extreme adjustments
        adjustment_factor = max(0.7, min(1.3, adjustment_factor))
        
        adjusted_price = comp_price * adjustment_factor
        
        return {
            'adjusted_price': adjusted_price,
            'factor': adjustment_factor,
            'reason': f'{input_bedrooms} vs {comp_bedrooms} bedrooms',
            'bedroom_diff': bedroom_diff
        }
    
    async def adjust_for_property_type(
        self,
        comp_price: float,
        comp_type: str,
        input_type: str,
        county: str
    ) -> Dict:
        """
        Adjust for property type difference (apartment vs house).
        """
        if not comp_type or not input_type:
            return {'adjusted_price': comp_price, 'factor': 1.0}
        
        if comp_type == input_type:
            return {'adjusted_price': comp_price, 'factor': 1.0, 'reason': 'Same type'}
        
        # Load coefficient
        coef = await self.load_coefficients(county)
        apartment_discount = coef.get('apartment_discount', -0.12)  # Default -12%
        
        if input_type == 'apartment' and comp_type != 'apartment':
            # Input is apartment, comp is house → discount comp
            factor = 1 + apartment_discount
        elif input_type != 'apartment' and comp_type == 'apartment':
            # Input is house, comp is apartment → increase comp
            factor = 1 / (1 + apartment_discount)
        else:
            factor = 1.0
        
        return {
            'adjusted_price': comp_price * factor,
            'factor': factor,
            'reason': f'{input_type} vs {comp_type}'
        }
    
    async def adjust_for_ber(
        self,
        comp_price: float,
        comp_ber: str,
        input_ber: str,
        county: str
    ) -> Dict:
        """
        Adjust for BER rating difference.
        Uses trained coefficients from hedonic model.
        """
        if not comp_ber or not input_ber:
            return {'adjusted_price': comp_price, 'factor': 1.0}
        
        BER_SCALE = {
            'A1': 9, 'A2': 8, 'A3': 7,
            'B1': 6, 'B2': 5, 'B3': 4,
            'C1': 3, 'C2': 2, 'C3': 1,
            'D1': 0, 'D2': -1,
            'E1': -2, 'E2': -3,
            'F': -4, 'G': -5
        }
        
        comp_score = BER_SCALE.get(comp_ber[:2], 0)
        input_score = BER_SCALE.get(input_ber[:2], 0)
        steps_diff = input_score - comp_score
        
        if steps_diff == 0:
            return {'adjusted_price': comp_price, 'factor': 1.0}
        
        # 1.5% per BER step (research-backed estimate)
        adjustment_pct = steps_diff * 1.5
        adjustment_pct = max(-15, min(15, adjustment_pct))  # Cap at ±15%
        
        factor = 1.0 + (adjustment_pct / 100)
        
        return {
            'adjusted_price': comp_price * factor,
            'factor': factor,
            'reason': f'BER: {input_ber} vs {comp_ber}',
            'steps_diff': steps_diff
        }
```

**Update API Endpoint to Use Enhanced Adjustments:**

```python
# In backend/valuation/api.py

# Replace MVPAdjuster with EnhancedAdjuster
adjuster = EnhancedAdjuster(db=db)

for comp in comparables:
    # Temporal
    temporal = await adjuster.adjust_temporal(...)
    comp['adjusted_price'] = temporal['adjusted_price']
    comp['adjustments'] = [temporal]
    
    # Bedrooms
    if request.bedrooms and comp.get('bedrooms'):
        bedroom_adj = await adjuster.adjust_for_bedrooms(
            comp_price=comp['adjusted_price'],
            comp_bedrooms=comp['bedrooms'],
            input_bedrooms=request.bedrooms,
            county=county
        )
        comp['adjusted_price'] = bedroom_adj['adjusted_price']
        comp['adjustments'].append(bedroom_adj)
    
    # Property Type
    if request.property_type and comp.get('property_type'):
        type_adj = await adjuster.adjust_for_property_type(
            comp_price=comp['adjusted_price'],
            comp_type=comp['property_type'],
            input_type=request.property_type,
            county=county
        )
        comp['adjusted_price'] = type_adj['adjusted_price']
        comp['adjustments'].append(type_adj)
    
    # BER
    if request.ber_rating and comp.get('ber_rating'):
        ber_adj = await adjuster.adjust_for_ber(
            comp_price=comp['adjusted_price'],
            comp_ber=comp['ber_rating'],
            input_ber=request.ber_rating,
            county=county
        )
        comp['adjusted_price'] = ber_adj['adjusted_price']
        comp['adjustments'].append(ber_adj)
```

**Effort:** 3 days

---

### Phase 2.3: Improved Confidence Scoring (Week 3)

**Update `backend/valuation/validator.py`:**

```python
class EnhancedValidator:
    """
    Phase 2: More sophisticated confidence scoring.
    """
    
    def calculate_confidence_level(
        self,
        n_comparables: int,
        cv: float,  # Coefficient of variation
        avg_distance_km: float,
        avg_days_ago: float,
        feature_coverage: Dict,
        adjustment_confidence: float  # New: how confident in adjustments
    ) -> str:
        """
        Multi-factor confidence classification.
        
        Score (0-100):
        - Sample size: 0-25 points
        - Price dispersion: 0-20 points
        - Proximity: 0-20 points
        - Recency: 0-15 points
        - Feature completeness: 0-10 points
        - Adjustment confidence: 0-10 points
        
        High: 75+, Medium: 50-74, Low: <50
        """
        
        score = 0
        
        # 1. Sample size (0-25 points)
        if n_comparables >= 25:
            score += 25
        elif n_comparables >= 15:
            score += 20
        elif n_comparables >= 10:
            score += 15
        elif n_comparables >= 5:
            score += 10
        else:
            score += 5
        
        # 2. Price dispersion (0-20 points)
        if cv < 0.10:
            score += 20
        elif cv < 0.15:
            score += 15
        elif cv < 0.25:
            score += 10
        else:
            score += 5
        
        # 3. Proximity (0-20 points)
        if avg_distance_km < 1:
            score += 20
        elif avg_distance_km < 3:
            score += 15
        elif avg_distance_km < 7:
            score += 10
        elif avg_distance_km < 15:
            score += 5
        
        # 4. Recency (0-15 points)
        avg_months_ago = avg_days_ago / 30.44
        if avg_months_ago < 6:
            score += 15
        elif avg_months_ago < 12:
            score += 12
        elif avg_months_ago < 24:
            score += 8
        else:
            score += 4
        
        # 5. Feature completeness (0-10 points)
        avg_coverage = (
            feature_coverage.get('bedrooms', 0) + 
            feature_coverage.get('property_type', 0)
        ) / 2
        score += int(avg_coverage * 10)
        
        # 6. Adjustment confidence (0-10 points)
        score += int(adjustment_confidence * 10)
        
        # Classify
        if score >= 75:
            return 'high'
        elif score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def calculate_adjustment_confidence(self, comparables: List[Dict]) -> float:
        """
        How confident are we in the adjustments applied?
        
        Factors:
        - % of comparables requiring adjustments
        - Magnitude of adjustments (smaller = more confident)
        
        Returns: 0.0 to 1.0
        """
        if not comparables:
            return 0.0
        
        adjustment_factors = []
        
        for comp in comparables:
            # Extract all adjustment factors
            adjustments = comp.get('adjustments', [])
            total_factor = 1.0
            for adj in adjustments:
                if 'factor' in adj:
                    total_factor *= adj['factor']
            adjustment_factors.append(total_factor)
        
        # Calculate average distance from 1.0 (no adjustment)
        avg_adjustment_magnitude = np.mean([abs(f - 1.0) for f in adjustment_factors])
        
        # Convert to confidence (0-1)
        # Small adjustments (<10%) = high confidence
        # Large adjustments (>30%) = low confidence
        if avg_adjustment_magnitude < 0.10:
            confidence = 1.0
        elif avg_adjustment_magnitude < 0.20:
            confidence = 0.8
        elif avg_adjustment_magnitude < 0.30:
            confidence = 0.6
        else:
            confidence = 0.4
        
        return confidence
```

**Effort:** 2 days

---

### Phase 2.4: Frontend Enhancements (Week 4)

**Add Map Visualization:**

```typescript
// frontend/src/pages/ValuationPage.tsx

// Add after comparables table:

{/* Map with Comparables */}
{result.metadata.geocoded_location && (
  <div className="bg-white rounded-lg shadow p-6 mb-8">
    <h3 className="text-xl font-bold mb-4">Comparable Locations</h3>
    
    <MapContainer
      center={[
        result.metadata.geocoded_location.latitude,
        result.metadata.geocoded_location.longitude
      ]}
      zoom={13}
      style={{ height: '400px', borderRadius: '8px' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      
      {/* Subject property marker (blue) */}
      <Marker
        position={[
          result.metadata.geocoded_location.latitude,
          result.metadata.geocoded_location.longitude
        ]}
        icon={L.divIcon({
          html: '<div class="bg-blue-600 w-4 h-4 rounded-full border-2 border-white"></div>',
          className: ''
        })}
      >
        <Popup>
          <strong>Subject Property</strong><br />
          {address}
        </Popup>
      </Marker>
      
      {/* Comparable properties markers (green, sized by weight) */}
      {result.comparables.map((comp, idx) => (
        <Marker
          key={comp.id}
          position={[comp.latitude, comp.longitude]}
          icon={L.divIcon({
            html: `<div class="bg-green-600 rounded-full border-2 border-white" style="width: ${8 + comp.weight * 12}px; height: ${8 + comp.weight * 12}px;"></div>`,
            className: ''
          })}
        >
          <Popup>
            <strong>{comp.address}</strong><br />
            Sale Price: {formatPrice(comp.price)}<br />
            Adjusted: {formatPrice(comp.adjusted_price)}<br />
            Distance: {(comp.distance_m / 1000).toFixed(2)} km<br />
            Weight: {(comp.weight * 100).toFixed(0)}%
          </Popup>
        </Marker>
      ))}
      
      {/* Search radius circle */}
      <Circle
        center={[
          result.metadata.geocoded_location.latitude,
          result.metadata.geocoded_location.longitude
        ]}
        radius={Math.max(...result.comparables.map(c => c.distance_m))}
        pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.05 }}
      />
    </MapContainer>
  </div>
)}
```

**Add Confidence Interval Chart:**

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

// After valuation summary:

{/* Confidence Interval Visualization */}
<div className="mt-6">
  <h3 className="text-sm font-medium mb-2">Price Range Distribution</h3>
  <LineChart width={600} height={200} data={[
    { x: result.confidence_interval.lower, y: 0, label: 'Lower' },
    { x: result.estimate, y: 1, label: 'Estimate' },
    { x: result.confidence_interval.upper, y: 0, label: 'Upper' }
  ]}>
    <XAxis 
      dataKey="x" 
      type="number"
      domain={['dataMin', 'dataMax']}
      tickFormatter={(val) => formatPrice(val)}
    />
    <YAxis hide />
    <CartesianGrid strokeDasharray="3 3" />
    <Tooltip 
      formatter={(value, name) => [formatPrice(value as number), name]}
    />
    <Line type="monotone" dataKey="y" stroke="#3B82F6" strokeWidth={2} dot={{ r: 6 }} />
    <ReferenceLine x={result.estimate} stroke="#059669" strokeWidth={2} label="Estimate" />
  </LineChart>
</div>
```

**Effort:** 4 days

---

### Phase 2.5: Testing & Validation (Weeks 5-6)

**Update Accuracy Validation:**

```bash
# Re-run validation with Phase 2 improvements
python3 scripts/validate_valuation_accuracy.py
```

**Expected Improvement:**
- **Before (Phase 1):** 15-25% MAPE urban
- **After (Phase 2):** 12-20% MAPE urban (20-30% improvement)

**Add A/B Test:**

```python
# scripts/ab_test_phase2.py

"""
Compare Phase 1 (no feature adjustments) vs Phase 2 (with feature adjustments)
on properties with complete feature data.
"""

async def run_ab_test():
    # Sample properties with bedrooms + property_type
    query = """
        SELECT id, address, eircode, price, sale_date, county,
               bedrooms, property_type, ber_rating, latitude, longitude
        FROM properties
        WHERE 
            sale_date >= NOW() - INTERVAL '6 months'
            AND bedrooms IS NOT NULL
            AND property_type IS NOT NULL
            AND price BETWEEN 100000 AND 1000000
        ORDER BY RANDOM()
        LIMIT 100
    """
    
    test_properties = await db.fetch(query)
    
    phase1_errors = []
    phase2_errors = []
    
    for prop in test_properties:
        # Phase 1: No feature adjustments
        valuation_v1 = await estimate_with_version(prop, version='phase1')
        error_v1 = abs(valuation_v1['estimate'] - prop['price']) / prop['price'] * 100
        phase1_errors.append(error_v1)
        
        # Phase 2: With feature adjustments
        valuation_v2 = await estimate_with_version(prop, version='phase2')
        error_v2 = abs(valuation_v2['estimate'] - prop['price']) / prop['price'] * 100
        phase2_errors.append(error_v2)
    
    print("=== A/B TEST RESULTS ===")
    print(f"Phase 1 MAPE: {np.mean(phase1_errors):.1f}%")
    print(f"Phase 2 MAPE: {np.mean(phase2_errors):.1f}%")
    print(f"Improvement: {(np.mean(phase1_errors) - np.mean(phase2_errors)):.1f} percentage points")
```

**Effort:** 6 days

---

## Phase 2 Summary

**Total Timeline:** 6 weeks  
**Total Effort:** ~20 working days

**Deliverables:**
- ✅ Hedonic price models trained (26 counties)
- ✅ Bedroom adjustment logic
- ✅ Property type adjustment logic
- ✅ BER adjustment logic (when available)
- ✅ Enhanced confidence scoring
- ✅ Map visualization with comparables
- ✅ Confidence interval chart
- ✅ A/B testing framework
- ✅ Accuracy improvement validation

**Expected Accuracy:**
- **Urban (Dublin, Cork, Galway):** 12-20% MAPE (was 15-25%)
- **Suburban/Large Towns:** 18-25% MAPE (was 20-30%)
- **Rural:** 22-28% MAPE (was 25-35%)

**Data Requirements:**
- ✅ Works best with enriched properties (bedrooms, property_type, BER)
- ⚠️ Current enrichment: 4.7% bedrooms, 5.4% property_type
- 🎯 **Priority:** Continue enrichment to 20-30% coverage for maximum accuracy

---

## Phase 3: Advanced Features & ML

**Timeline:** 8-12 weeks  
**Accuracy Target:** 8-15% MAPE urban, 12-20% rural  
**Goal:** Machine learning models, market trends, type-specific models

### Phase 3.1: Gradient Boosting Model (Weeks 1-4)

**Objective:** Train XGBoost/LightGBM model to capture non-linear patterns.

**Features:**
- Spatial: latitude, longitude, distance to city center, routing key median price
- Temporal: sale_date, days_since_sale, county monthly price index
- Property: bedrooms, property_type, ber_rating, floor_area (if enriched)
- Market: local sale density, price trends, seasonality

**Model Architecture:**
```python
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

# Train separate models per county (or national with county feature)
# Use time-series cross-validation (train on past, test on future)
```

**Expected Accuracy:** 8-12% MAPE urban

**Effort:** 15 days

---

### Phase 3.2: Market Trend Predictions (Weeks 5-6)

**Objective:** Predict future price movements (3, 6, 12 months ahead).

**Method:**
- ARIMA or Prophet time series models per county
- Feed predictions into valuation confidence intervals

**Effort:** 8 days

---

### Phase 3.3: Property Type Specialist Models (Weeks 7-8)

**Objective:** Train separate models for apartments, houses, etc.

**Why:** Apartments value differently (floor level, building age matter more).

**Effort:** 8 days

---

### Phase 3.4: Explainability Dashboard (Weeks 9-10)

**Objective:** Show users WHY a valuation is what it is.

**Features:**
- Feature importance chart (bedrooms contributed +€50k)
- Market comparison (similar properties in area sold for X)
- Trend indicator (prices rising/falling)

**Effort:** 10 days

---

### Phase 3.5: API Enhancements (Weeks 11-12)

**New Endpoints:**
- `POST /api/valuation/bulk` - batch valuations
- `GET /api/valuation/trends/{address}` - price history for address
- `GET /api/valuation/market/{routing_key}` - market overview

**Effort:** 8 days

---

## Phase 3 Summary

**Total Timeline:** 12 weeks  
**Total Effort:** ~49 working days

**Deliverables:**
- ✅ XGBoost/LightGBM models
- ✅ Market trend predictions
- ✅ Property type specialist models
- ✅ Explainability dashboard
- ✅ Bulk valuation API
- ✅ Market trends API

**Expected Accuracy:**
- **Urban (Dublin, Cork, Galway):** 8-15% MAPE
- **Suburban/Large Towns:** 12-18% MAPE
- **Rural:** 15-22% MAPE

---

## Data Collection Priorities

### Critical for Phase 2+:
1. **Bedrooms:** Target 30% coverage (currently 4.7%)
   - Method: Continue web scraping recent sales
   - Impact: +3-5% accuracy improvement

2. **Property Type:** Target 40% coverage (currently 5.4%)
   - Method: Web scraping + ML classification from address patterns
   - Impact: +2-4% accuracy improvement

3. **Floor Area (m²):** Target 15% coverage (currently 0%)
   - Method: Web scraping MyHome/Daft historical listings
   - Impact: +2-3% accuracy improvement

4. **BER Rating:** Target 35% coverage (currently low)
   - Method: SEAI BER database integration
   - Impact: +1-2% accuracy improvement

### Nice-to-Have:
- Property age/build year
- Number of bathrooms
- Garage/parking availability
- Garden size

---

## Performance Considerations

### Database Optimization:
- **Indexes:** Already have GIST on geog (critical)
- **Materialized Views:** Refresh monthly (county price indices)
- **Query Caching:** 5-minute cache for valuations (in-memory)
- **Connection Pooling:** Use asyncpg connection pool (max 20 connections)

### API Response Times:
- **Phase 1 Target:** <2 seconds (p95)
- **Phase 2 Target:** <3 seconds (p95, with feature adjustments)
- **Phase 3 Target:** <4 seconds (p95, with ML inference)

### Scaling:
- **Current Load:** 0 requests/day (new feature)
- **Expected Growth:** 100-500 valuations/day within 3 months
- **Backend Capacity:** Railway can handle 10k+ requests/day
- **Database Capacity:** Supabase free tier supports 5M queries/month

---

## Testing Strategy

### Unit Tests (80% coverage target):
- Geocoder: Test Eircode, Nominatim, fuzzy matching
- Comparable Search: Test urban, suburban, rural
- Adjustments: Test temporal, bedroom, type, BER logic
- Calculator: Test weighted average, confidence intervals
- Validator: Test warning generation, quality scoring

### Integration Tests:
- End-to-end API tests (50 properties across counties)
- Performance tests (response time <2s)
- Error handling (bad addresses, no comparables)

### Accuracy Validation:
- Hold-out test set: 100 properties per quarter
- Track MAPE over time (dashboard)
- User feedback loop (report incorrect valuations)

---

## Deployment Checklist

### Phase 1 Launch:
- [ ] Database schema migrated
- [ ] Price indices materialized view created
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Monitoring configured (Sentry)
- [ ] Documentation updated
- [ ] SEO: Add `/valuation` page to sitemap
- [ ] Analytics: Track valuation requests (Google Analytics event)
- [ ] Announce feature (blog post, social media)

### Phase 2 Launch:
- [ ] Hedonic models trained
- [ ] Coefficients loaded into database
- [ ] A/B test completed (validate improvement)
- [ ] Frontend updated with map visualization
- [ ] Performance tested (response time acceptable)

### Phase 3 Launch:
- [ ] ML models trained and deployed
- [ ] Bulk API endpoints tested
- [ ] Explainability dashboard complete
- [ ] Market trends API documented

---

## Success Metrics

### Accuracy Metrics:
- **MAPE (Mean Absolute Percentage Error):** Track by phase, county, property type
- **Within 10% accuracy:** % of valuations within 10% of actual price
- **Within 20% accuracy:** % of valuations within 20% of actual price

### Usage Metrics:
- **Valuation requests per day**
- **Conversion rate:** % of valuations leading to property searches
- **User feedback:** Thumbs up/down on valuation quality

### Technical Metrics:
- **API response time (p50, p95, p99)**
- **Error rate:** % of failed valuations
- **Database query performance:** Monitor slow queries

---

## Risk Mitigation

### Risk: Insufficient comparables in rural areas
**Mitigation:** 
- Expand search radius automatically (up to 20km)
- Lower minimum comparable threshold (5 instead of 10)
- Show clear warnings to user

### Risk: Inaccurate geocoding
**Mitigation:**
- Multi-source geocoding (Eircode → Nominatim → DB fuzzy)
- Manual override option for users
- Track geocoding confidence in logs

### Risk: Temporal price indices unreliable (sparse data)
**Mitigation:**
- Hierarchical fallback (county → region → national)
- Interpolation for missing months
- Flag low-confidence adjustments

### Risk: Feature data too sparse (<10% coverage)
**Mitigation:**
- Phase 1 works without features (location + temporal only)
- Phase 2+ gracefully degrades when features missing
- Continue enrichment efforts (target 30%+ coverage)

---

## Total Project Timeline

| Phase | Duration | Cumulative | Deliverables |
|-------|----------|------------|--------------|
| **Phase 1: MVP** | 6 weeks | 6 weeks | Basic comparable valuation API + frontend |
| **Phase 2: Enhanced** | 6 weeks | 12 weeks | Feature adjustments, hedonic models, improved confidence |
| **Phase 3: Advanced** | 12 weeks | 24 weeks | ML models, market trends, explainability |

**Total:** ~6 months from start to advanced ML-powered valuation system

**Recommended Launch Strategy:**
1. **Week 6:** Launch Phase 1 MVP publicly (Beta label)
2. **Week 12:** Launch Phase 2 (remove Beta label)
3. **Week 24:** Launch Phase 3 (Premium feature?)

---

## Conclusion

This roadmap provides a **pragmatic, phased approach** to building a property valuation system that:

✅ **Works with current data** (Phase 1 requires no enrichment)  
✅ **Improves with enrichment** (Phase 2+ leverage bedrooms/type/BER when available)  
✅ **Delivers value quickly** (6 weeks to MVP)  
✅ **Scales to advanced ML** (Phase 3 for maximum accuracy)  

**Next Steps:**
1. Approve roadmap and prioritize phases
2. Begin Phase 1.1 (database schema) immediately
3. Continue property enrichment in parallel (target 20-30% feature coverage)
4. Track accuracy metrics from Day 1 (validate assumptions)
