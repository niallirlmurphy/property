# Property Valuation Algorithm - Executive Summary

**Date:** June 23, 2026  
**Source:** Multi-agent workflow research and design  
**Duration:** 9 hours 25 minutes  
**Full Report:** VALUATION_ALGORITHM_ROADMAP.md (1,949 lines)

---

## Overview

Comprehensive 3-phase roadmap to implement automated property valuation for Ireland's Property Price Register (PPR) data. Delivers working MVP in 6 weeks, achieving **15-25% MAPE accuracy** for urban properties, scaling to **8-15% MAPE** with advanced ML models.

---

## Phase 1: MVP (6 Weeks)

**Goal:** Comparable-sales valuation with basic temporal adjustment

**Core Algorithm:**
1. Geocode address → coordinates
2. Find 10+ comparable sales within 20km radius (adaptive search)
3. Adjust prices for time difference using county price indices
4. Calculate weighted average (distance + recency weights)
5. Return estimate with confidence interval

**Key Components:**
- `backend/valuation/` - Geocoder, comparable search, adjustments, calculator, validator
- Database schema: `valuation_requests`, `valuation_comparables`, `county_monthly_price_indices`
- API endpoint: `POST /api/valuation/estimate`
- Frontend page: `/valuation` - Simple form + results table

**Expected Accuracy:**
- Urban (Dublin/Cork/Galway): 15-25% MAPE
- Suburban: 20-30% MAPE
- Rural: 25-35% MAPE

**Data Requirements:**
- ✅ Works with existing 90.7% geocoded properties
- ✅ No additional enrichment needed
- Monthly refresh of price indices

**Performance:**
- API response time: <2 seconds (p95)
- Comparable search: <500ms (uses existing GIST index)

---

## Phase 2: Enhanced Adjustments (6 Weeks)

**Goal:** Feature-based adjustments using hedonic price models

**New Features:**
- Hedonic regression models per county (bedroom, type, BER adjustments)
- Enhanced confidence scoring (5-tier: very high → very low)
- Map visualization showing comparable locations
- Confidence interval chart

**Algorithm Improvements:**
- Bedroom adjustment: ~€30-50k per bedroom (county-specific)
- Property type adjustment: Apartments vs houses (~10-20% discount)
- BER adjustment: A-rated ~5-8% premium, F-rated ~8-12% discount
- Improved weighting incorporating feature similarity

**Expected Accuracy:**
- Urban: 12-20% MAPE (5-7% improvement)
- Suburban: 18-25% MAPE
- Rural: 22-28% MAPE

**Data Requirements:**
- ⚠️ Current enrichment: 4.7% bedrooms, 5.4% property_type
- 🎯 Target: 20-30% coverage for maximum accuracy
- Continue web scraping enrichment in parallel

---

## Phase 3: Advanced ML (12 Weeks)

**Goal:** Gradient boosting models with market trend predictions

**Features:**
- XGBoost/LightGBM models capturing non-linear patterns
- Market trend predictions (3/6/12 months ahead)
- Property type specialist models (apartments vs houses)
- Explainability dashboard (feature importance, market comparison)
- Bulk API endpoints for batch valuations

**Expected Accuracy:**
- Urban: 8-15% MAPE (production-grade)
- Suburban: 12-18% MAPE
- Rural: 15-22% MAPE

---

## Implementation Timeline

| Phase | Duration | Cumulative | Key Deliverable |
|-------|----------|------------|-----------------|
| Phase 1 MVP | 6 weeks | 6 weeks | Working valuation API + basic frontend |
| Phase 2 Enhanced | 6 weeks | 12 weeks | Feature adjustments + improved accuracy |
| Phase 3 Advanced | 12 weeks | 24 weeks | ML models + market insights |

**Recommended Launch Strategy:**
- Week 6: Public Beta (Phase 1 MVP)
- Week 12: Production Launch (Phase 2)
- Week 24: Premium Features (Phase 3)

---

## Technical Architecture

**Database Schema:**
```sql
-- Core tables
valuation_requests          -- Track all valuation requests
valuation_comparables       -- Junction table for analysis
county_monthly_price_indices -- Materialized view for temporal adjustment
hedonic_coefficients        -- Phase 2: Trained model coefficients
```

**Backend Structure:**
```
backend/valuation/
  geocoder.py          # Address → coordinates
  comparable_search.py # Adaptive radius search (1km → 20km)
  adjustments.py       # Phase 1: Temporal | Phase 2: +Feature
  calculator.py        # Weighted average + confidence intervals
  validator.py         # Quality checks + warnings
  models.py            # Pydantic schemas
  api.py               # FastAPI endpoints
```

**Performance Targets:**
- Phase 1: <2s response time (p95)
- Phase 2: <3s response time (p95)
- Phase 3: <4s response time (p95)

**Scaling Capacity:**
- Backend (Railway): 10k+ requests/day
- Database (Supabase): 5M queries/month
- Expected load: 100-500 valuations/day within 3 months

---

## Data Collection Priorities

**Critical for Phase 2+:**

1. **Bedrooms** (currently 4.7%)
   - Target: 30% coverage
   - Method: Continue web scraping
   - Impact: +3-5% accuracy improvement

2. **Property Type** (currently 5.4%)
   - Target: 40% coverage
   - Method: Web scraping + ML classification
   - Impact: +2-4% accuracy improvement

3. **Floor Area** (currently 0%)
   - Target: 15% coverage
   - Method: MyHome/Daft historical listings
   - Impact: +2-3% accuracy improvement

4. **BER Rating** (currently low)
   - Target: 35% coverage
   - Method: SEAI database integration
   - Impact: +1-2% accuracy improvement

---

## Success Metrics

**Accuracy:**
- MAPE by county, property type, phase
- % within 10% accuracy (target: 40-50%)
- % within 20% accuracy (target: 70-80%)

**Usage:**
- Valuation requests per day
- Conversion to property searches
- User feedback (thumbs up/down)

**Technical:**
- API response time (p50, p95, p99)
- Error rate (target: <2%)
- Database query performance

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Insufficient rural comparables | Adaptive radius up to 20km, lower threshold to 5, show warnings |
| Inaccurate geocoding | Multi-source (Eircode → Nominatim → DB), manual override option |
| Sparse temporal data | Hierarchical fallback (county → region → national), interpolation |
| Low feature coverage | Phase 1 works without features, graceful degradation in Phase 2+ |

---

## Competitive Positioning

**Current Market:**
- **Daft/MyHome:** Asking prices + "sold in your area" (no specific valuation)
- **Property Price Register:** Raw sold prices search (no valuation)
- **Residential valuers:** Manual, expensive (€150-400), slow

**HomeIQ Advantage:**
- ✅ Free automated valuations
- ✅ Instant results (<2s)
- ✅ Transparent methodology (show comparables)
- ✅ Confidence scoring (honest about accuracy)
- ✅ Full coverage (26 counties, 784k sales)

**Phase 3 Differentiators:**
- Market trend predictions
- Explainability (feature importance)
- Bulk API for businesses (estate agents, mortgage advisors)

---

## Next Steps

**Immediate Actions:**

1. **Approve roadmap** - Decide on phase prioritization
2. **Start Phase 1.1** - Database schema changes (2 days)
3. **Continue enrichment** - Run `enrich_recent_properties.py` weekly
4. **Set up monitoring** - Sentry events for valuation requests

**Week 1 Tasks:**
1. Create `backend/valuation/` directory structure
2. Apply database schema (`db/phase1_schema.sql`)
3. Build geocoder service (Eircode → Nominatim → fuzzy)
4. Implement comparable search (adaptive radius)

**Week 2-3 Tasks:**
1. Build adjustment logic (temporal only for MVP)
2. Implement calculator (weighted average + confidence)
3. Add validator (quality checks + warnings)
4. Create API endpoint with Pydantic models

**Week 4 Tasks:**
1. Write unit tests (80% coverage target)
2. Run accuracy validation on 100 test properties
3. Optimize performance (<2s response time)

**Week 5 Tasks:**
1. Build frontend ValuationPage.tsx
2. Add routing to App.tsx
3. Style results display (estimate, interval, comparables table)

**Week 6 Tasks:**
1. Deploy to production (Railway + Vercel)
2. Set up monitoring (Sentry, analytics)
3. Update sitemap + SEO
4. Announce Beta launch

---

## Cost Estimates

**Development Time:**
- Phase 1: ~25 working days (solo developer)
- Phase 2: ~20 working days
- Phase 3: ~49 working days
- Total: ~94 working days (~4.5 months full-time)

**Infrastructure:**
- Database: Supabase (current plan, no additional cost)
- Backend: Railway (current plan, no additional cost)
- Frontend: Vercel (current plan, no additional cost)
- ML Hosting (Phase 3): Possibly $20-50/month for model serving

**Data Collection:**
- Web scraping: Current scripts, no additional cost
- SEAI BER data: Free API (rate-limited)
- Valuation Office data: Potentially free (pending approval)

---

## Conclusion

**Why This Approach Works:**

✅ **Pragmatic** - Phase 1 MVP delivers value in 6 weeks with existing data  
✅ **Incremental** - Each phase builds on previous, no wasted effort  
✅ **Data-realistic** - Doesn't depend on 100% feature coverage  
✅ **Transparent** - Shows comparables, confidence, warnings to users  
✅ **Scalable** - Architecture supports 10k+ requests/day  

**Competitive Advantage:**

This positions HomeIQ.ie as the **only free, automated property valuation tool in Ireland** with transparent methodology and full PPR coverage.

**Ready to Start:** Phase 1 database schema can be applied immediately. No blockers.

---

**Full Technical Specification:** See `VALUATION_ALGORITHM_ROADMAP.md` for complete implementation details, SQL queries, Python code examples, and testing strategies.
