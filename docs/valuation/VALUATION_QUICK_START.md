# Property Valuation - Quick Start Guide

**Ready to build:** Phase 1 MVP can start immediately  
**Timeline:** 6 weeks to working valuation API + frontend  
**Prerequisites:** Existing infrastructure (Supabase + Railway + Vercel) ✅

---

## Week 1: Database Foundation

### Day 1-2: Schema Setup

```bash
# 1. Create SQL schema file
cat > db/phase1_valuation_schema.sql << 'EOF'
-- Price indices for temporal adjustment
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

-- Valuation requests tracking
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

-- Comparables junction table
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
EOF

# 2. Apply to Supabase
psql $DATABASE_URL -f db/phase1_valuation_schema.sql

# 3. Initial refresh
psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW county_monthly_price_indices;"
```

**Output:** Database ready for valuation system ✅

---

## Week 2-3: Backend Implementation

### Directory Structure

```bash
mkdir -p backend/valuation
cd backend/valuation

# Create Python module
touch __init__.py models.py geocoder.py comparable_search.py
touch adjustments.py calculator.py validator.py api.py
```

### Implementation Order

**Day 3-4: Models & Geocoder** (2 days)

```python
# backend/valuation/models.py - Pydantic schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ValuationRequest(BaseModel):
    address: str
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
    confidence_interval: dict
    confidence_level: str
    comparables: List[ComparableProperty]
    validation: dict
    metadata: dict
```

```python
# backend/valuation/geocoder.py - Address → coordinates
class ValuationGeocoder:
    async def geocode_address(self, address: str, eircode: str = None):
        """
        Priority:
        1. Eircode routing key lookup (routing_key_stats view)
        2. Nominatim API
        3. Database fuzzy address match
        
        Returns: {'latitude': float, 'longitude': float, 'confidence': float}
        """
```

**Day 5-7: Comparable Search** (3 days)

```python
# backend/valuation/comparable_search.py
class ComparableSearcher:
    async def find_comparables(
        self, 
        latitude: float, 
        longitude: float,
        max_radius_km: float = 20,
        min_count: int = 10
    ) -> List[Dict]:
        """
        Adaptive radius search: 1km → 2km → 5km → 10km → 20km
        Returns when >= min_count found
        
        SQL uses existing GIST index on geog for fast spatial queries
        """
```

**Key SQL Query:**
```sql
WITH subject_point AS (
    SELECT ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography AS geog
)
SELECT 
    p.id, p.address, p.price, p.sale_date, p.county,
    ST_Distance(p.geog, sp.geog) AS distance_m,
    1.0 - (EXTRACT(EPOCH FROM (NOW() - p.sale_date)) / (3 * 365 * 86400)) AS recency_score
FROM properties p
CROSS JOIN subject_point sp
WHERE 
    p.geog IS NOT NULL
    AND p.not_full_market_price = FALSE
    AND p.sale_date >= NOW() - INTERVAL '3 years'
    AND ST_DWithin(p.geog, sp.geog, $3)  -- Uses GIST index
ORDER BY distance_m ASC, recency_score DESC
LIMIT 30;
```

**Day 8-9: Adjustments** (2 days)

```python
# backend/valuation/adjustments.py
class MVPAdjuster:
    async def adjust_temporal(
        self, 
        sale_price: float, 
        sale_date: datetime, 
        target_date: datetime, 
        county: str
    ) -> Dict:
        """
        Lookup county monthly price index from materialized view
        Formula: adjusted_price = sale_price * (target_index / sale_index)
        """
    
    def calculate_weight(self, comparable: Dict, max_distance_m: float) -> float:
        """
        Distance + recency weighting:
        weight = (1 - distance/max_distance)^2 * recency_score
        """
```

**Day 10-11: Calculator & Validator** (2 days)

```python
# backend/valuation/calculator.py
class ValuationCalculator:
    def calculate_valuation(self, comparables: List[Dict], weights: List[float]) -> Dict:
        """
        Weighted average with confidence interval
        Returns: estimate, lower, upper, statistics
        """

# backend/valuation/validator.py
class MVPValidator:
    def validate(self, valuation: Dict, comparables: List[Dict]) -> Dict:
        """
        Quality checks:
        - Minimum comparables (>= 5)
        - Price dispersion (CV < 0.4)
        - Average distance (< 15km)
        
        Returns: is_valid, warnings[], quality_score, confidence_level
        """
```

**Day 12-14: API Endpoint** (3 days)

```python
# backend/valuation/api.py
from fastapi import APIRouter, HTTPException, BackgroundTasks

router = APIRouter(prefix="/api/valuation", tags=["valuation"])

@router.post("/estimate", response_model=ValuationResponse)
async def estimate_property_value(
    request: ValuationRequest,
    background_tasks: BackgroundTasks
):
    """
    Full valuation pipeline:
    1. Geocode → 2. Find comparables → 3. Adjust → 4. Calculate → 5. Validate
    """
```

```python
# backend/main.py - Add router
from valuation.api import router as valuation_router

app.include_router(valuation_router)
```

---

## Week 4: Testing

### Unit Tests

```bash
# Create test file
cat > tests/test_valuation.py << 'EOF'
import pytest
from valuation.geocoder import ValuationGeocoder
from valuation.comparable_search import ComparableSearcher

@pytest.mark.asyncio
async def test_geocoder_eircode():
    geocoder = ValuationGeocoder(db=test_db)
    result = await geocoder.geocode_address("Dublin", eircode="D02X285")
    assert result['latitude'] is not None
    assert result['confidence'] >= 0.7

@pytest.mark.asyncio
async def test_comparable_search_dublin():
    searcher = ComparableSearcher(db=test_db)
    comparables = await searcher.find_comparables(53.3498, -6.2603, min_count=10)
    assert len(comparables) >= 10
    assert all(c['distance_m'] <= 20000 for c in comparables)

# Add more tests...
EOF

# Run tests
pytest tests/test_valuation.py -v
```

### Accuracy Validation

```bash
# Validate on 100 recent sales
python3 scripts/validate_valuation_accuracy.py

# Expected output:
# Overall MAPE: 18-25%
# Urban MAPE: 15-20%
# Rural MAPE: 25-35%
```

---

## Week 5: Frontend

### Create Valuation Page

```bash
# Create React component
cat > frontend/src/pages/ValuationPage.tsx << 'EOF'
import React, { useState } from 'react';
import { api } from '../api';

export const ValuationPage: React.FC = () => {
  const [address, setAddress] = useState('');
  const [eircode, setEircode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.post('/valuation/estimate', {
        address,
        eircode: eircode || undefined
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => `€${price.toLocaleString('en-IE')}`;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Property Valuation</h1>
      
      {/* Input Form */}
      <form onSubmit={handleSubmit} className="space-y-4 mb-8">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Property Address"
          className="w-full border rounded px-3 py-2"
          required
        />
        <input
          type="text"
          value={eircode}
          onChange={(e) => setEircode(e.target.value.toUpperCase())}
          placeholder="Eircode (Optional)"
          className="w-full border rounded px-3 py-2"
          maxLength={8}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded"
        >
          {loading ? 'Calculating...' : 'Get Valuation'}
        </button>
      </form>
      
      {/* Results */}
      {result && (
        <>
          <div className="text-5xl font-bold text-blue-600 mb-4">
            {formatPrice(result.estimate)}
          </div>
          
          <div className="text-sm text-gray-600 mb-4">
            Range: {formatPrice(result.confidence_interval.lower)} - {formatPrice(result.confidence_interval.upper)}
          </div>
          
          <div className="text-sm font-medium">
            Confidence: {result.confidence_level.toUpperCase()}
          </div>
          
          {/* Comparables Table */}
          <h3 className="text-xl font-bold mt-8 mb-4">
            Comparable Sales ({result.comparables.length})
          </h3>
          
          <table className="min-w-full">
            <thead>
              <tr>
                <th>Address</th>
                <th>Sale Price</th>
                <th>Adjusted</th>
                <th>Distance</th>
              </tr>
            </thead>
            <tbody>
              {result.comparables.map((comp) => (
                <tr key={comp.id}>
                  <td>{comp.address}</td>
                  <td>{formatPrice(comp.price)}</td>
                  <td>{formatPrice(comp.adjusted_price)}</td>
                  <td>{(comp.distance_m / 1000).toFixed(2)} km</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};
EOF
```

### Add Routing

```typescript
// frontend/src/App.tsx
import { ValuationPage } from './pages/ValuationPage';

// Add to Routes:
<Route path="/valuation" element={<ValuationPage />} />
```

---

## Week 6: Deployment

### Deploy Backend (Railway)

```bash
# Update dependencies
pip freeze > backend/requirements.txt

# Commit and push
git add backend/
git commit -m "feat: add property valuation API (Phase 1 MVP)"
git push origin main

# Railway auto-deploys
```

### Deploy Frontend (Vercel)

```bash
git add frontend/
git commit -m "feat: add property valuation page"
git push origin main

# Vercel auto-deploys
```

### Enable Monitoring

```python
# backend/valuation/api.py
import sentry_sdk

@router.post("/estimate")
async def estimate_property_value(request: ValuationRequest):
    try:
        # ... valuation logic ...
        
        sentry_sdk.set_context("valuation", {
            "address": request.address,
            "n_comparables": len(comparables),
            "confidence_level": valuation['confidence_level']
        })
        
        return response
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
```

### Update SEO

```bash
# Add to sitemap
python3 scripts/generate_sitemap.py

# Submit to IndexNow
./scripts/submit_indexnow.sh https://homeiq.ie/valuation

# Announce on homepage
# "NEW: Free Property Valuation Tool - Get instant automated estimates"
```

---

## Testing Checklist

Before launch:

- [ ] Database schema applied
- [ ] Price indices materialized view populated
- [ ] Geocoder handles Eircode + addresses
- [ ] Comparable search returns 10+ results for Dublin
- [ ] Comparable search returns 5+ results for rural areas
- [ ] Temporal adjustment calculates correctly
- [ ] Weighted average produces sensible estimates
- [ ] Validator flags low-confidence cases
- [ ] API response time < 2 seconds (p95)
- [ ] Frontend form submits successfully
- [ ] Results display estimate + interval + comparables
- [ ] Error handling shows user-friendly messages
- [ ] Monitoring captures valuation requests in Sentry
- [ ] Unit tests pass (pytest)
- [ ] Accuracy validation: MAPE < 25% urban

---

## Quick Smoke Test

```bash
# 1. Test API directly
curl -X POST http://localhost:8000/api/valuation/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "28 Slane Road, Crumlin, Dublin 12",
    "eircode": "D12XY34"
  }'

# Expected response:
# {
#   "estimate": 425000,
#   "confidence_interval": {"lower": 380000, "upper": 470000},
#   "confidence_level": "medium",
#   "comparables": [...],
#   "validation": {"is_valid": true, "quality_score": 0.75}
# }

# 2. Test frontend
# Navigate to http://localhost:5173/valuation
# Enter address: "28 Slane Road, Crumlin, Dublin 12"
# Click "Get Valuation"
# Verify estimate displays with comparables table
```

---

## Post-Launch Monitoring

**Day 1:**
- [ ] Test 10 addresses across counties
- [ ] Verify response times < 2s
- [ ] Check Sentry for errors
- [ ] Monitor database query performance

**Week 1:**
- [ ] Track valuation request count
- [ ] Analyze MAPE by county
- [ ] Review user feedback (if any)
- [ ] Identify edge cases (no comparables, geocoding failures)

**Week 2-4:**
- [ ] Optimize slow queries (if any)
- [ ] Add missing counties to price indices
- [ ] Continue property enrichment (bedrooms, type)
- [ ] Plan Phase 2 improvements

---

## Phase 2 Preview

After Phase 1 stable, add feature-based adjustments:

1. **Train hedonic models** (2 weeks)
   - Bedroom adjustment: ~€40k per bedroom (county-specific)
   - Type adjustment: Apartments vs houses
   - BER adjustment: A-rated premium

2. **Enhanced confidence scoring** (1 week)
   - 5-tier system (very high → very low)
   - Feature similarity weighting

3. **Map visualization** (2 weeks)
   - Show subject property + comparables on map
   - Circle showing search radius

Expected accuracy improvement: 5-7% MAPE reduction

---

**Full Roadmap:** See `VALUATION_ALGORITHM_ROADMAP.md` (1,949 lines)  
**Executive Summary:** See `VALUATION_EXECUTIVE_SUMMARY.md`
