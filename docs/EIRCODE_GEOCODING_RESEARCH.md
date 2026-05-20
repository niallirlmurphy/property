# Eircode & Geocoding Optimization Research
**Date:** 2026-05-20  
**Scope:** External sources + codebase analysis for HomeIQ.ie data enrichment

---

## Executive Summary

This research combines analysis of Ireland's Eircode system, Irish geocoding best practices, competitor approaches, and HomeIQ.ie's current implementation to identify optimization opportunities.

**Key findings:**
1. **Eircode system limitations** make it unsuitable for area-based clustering (unlike UK postcodes)
2. **Routing keys (3-char prefixes)** are the only hierarchical element — 139 total covering ~15k addresses each
3. **OSM/Nominatim** has incomplete Eircode coverage due to copyright restrictions
4. **Address normalization** is critical for Irish data due to rural address ambiguity
5. **Major property sites** (Daft, MyHome) rely on traditional geographic hierarchy over Eircodes

---

## 1. Eircode System Structure

### Official Specification
Source: Wikipedia, Eircode.ie, OSM Wiki

**Format:** 7 characters (3-char routing key + space + 4-char unique identifier)
- Example: `D02 AF30`, `H91 E2K0`, `V94 T2PX`
- First char: Always letter
- Second char: Always digit
- Third char: Digit OR 'W' only
- Last 4 chars: Random alphanumeric

### Routing Keys (First 3 Characters)

**Total:** 139 routing areas across Ireland

**Distribution:**
- Average: ~15,000 addresses per routing key
- Total: 2.2 million addresses (as of 2015)

**Geographic Logic:**
- **Dublin postal districts preserved:** D01, D02, D04, D06W → D06, D12, D22, etc.
- **Cork area:** Routing keys begin with 'T'
- **Rest of country:** No relationship to English/Irish place names (intentionally neutral)
- **Routing keys form contiguous geographic areas** on map (confirmed by OSM wiki)

### Critical Design Limitation

**Unlike UK/Dutch postcodes:**
- Each Eircode = **one address** (not a cluster)
- Last 4 characters are **randomized** (no geographic sequence)
- Cannot infer proximity from similar Eircodes
- **Only the 3-char routing key has geographic meaning**

**OSM Wiki Warning:**
> "Eircodes may superficially resemble UK postcodes, but they cannot be treated in the same way by geocoders. Crucially, each code represents a single delivery point, not a local area."

**Implication for HomeIQ.ie:**
- Cannot use full Eircode for area-based search/clustering
- Routing key is the unit for geographic analysis
- Need explicit coordinate lookup or routing key → boundary mapping

---

## 2. Current Eircode Coverage Status

### HomeIQ.ie Database
- **Total properties:** 781,501
- **With Eircodes:** ~165,000 (21%)
- **With coordinates:** 620,849 (79.4%)
- **Enrichment rate:** 500 addresses/day via Autoaddress API → ~200 Eircodes/day (40% success)

### National Context
**GeoDirectory (official database):**
- 3.5+ million addresses nationwide (includes commercial)
- Maintained by An Post + Tailte Éireann (OSI)
- Forms basis of ECAD (Eircode Address Database)

**Coverage gap:**
- PPR contains ~781k residential sales (2010-present)
- 79% left without Eircode in HomeIQ database
- 35% of Irish properties had non-unique addresses pre-Eircode (600k+ properties)

---

## 3. Eircode Enrichment Strategies

### Current Implementation (`db/eircode_enrich.py`)

**Method:** Autoaddress API (500 lookups/day)

**Prioritization:**
1. Urban counties (Dublin, Cork, Galway, Limerick, Waterford)
2. Addresses with house numbers (structured format)
3. Recent sales
4. Properties with existing coordinates

**Success rate:** 40% (improved from 24% after address normalization)

**Cost:** ~$6,000/year estimated for 500/day at commercial rates

### Optimization Option A: Reverse Geocoding (Coordinate → Eircode)

**Concept:** Use lat/lon to lookup Eircode instead of address string matching

**Advantages:**
- Higher accuracy for properties with good coordinates (620k properties)
- Bypasses address string ambiguity issues
- Works for rural properties with non-unique addresses

**Data sources:**
1. **Autoaddress Reverse API** (if available) — unknown cost
2. **ECAD Direct License** — €38M database, annual license required
3. **GeoDirectory products** — commercial licensing, partners with An Post

**Estimated cost for one-time enrichment:**
- Autoaddress reverse: ~$500-1,000 for 50k high-priority properties
- ECAD license: €thousands annually (enterprise only)

**Implementation complexity:** Medium — add reverse geocoding endpoint to enrichment script

### Optimization Option B: Bulk ECAD/GeoDirectory Integration

**Concept:** License full Eircode dataset for local matching

**ECAF (Eircode Address File):**
- 2.2M addresses with Eircodes
- Monthly/quarterly updates
- Product guides for database integration

**ECAD (Eircode Address Database):**
- ECAF + coordinates + boundary data + building info
- Distributed via secure portal
- Requires annual license

**Advantages:**
- Unlimited local lookups
- No API rate limits
- Includes coordinates for validation

**Disadvantages:**
- High upfront cost (€thousands)
- Must integrate bulk data pipeline
- Ongoing update management

**Estimated cost:** €5,000-15,000/year (small business tier speculation)

**Recommendation:** Only worthwhile if enrichment needs exceed 100k properties/year

### Optimization Option C: Scaling Autoaddress

**Current:** 500/day = 182,500/year

**Proposed:** 800/day = 292,000/year (cover all gaps in ~3 years)

**Required changes:**
- Increase daily limit in cron job
- Negotiate higher tier with Autoaddress
- Prioritize by search frequency (log-based priority queue)

**Estimated additional cost:** +$3,000-5,000/year for 300 extra lookups/day

---

## 4. Geocoding Quality Optimization

### OSM/Nominatim Best Practices for Ireland

Source: OSM Wiki Ireland page

**Address Structure (Republic of Ireland):**
```
1. House number/name, Street name
2. Townland (rural only — if no street name)
3. Town or City
4. County ("County Cork" rural / "Dublin 15" city)
5. Eircode
```

**Key challenges identified:**
- **Townlands:** Historical boundaries, critical for rural areas without street names
- **Non-unique addresses:** Common in rural Ireland (reason Eircode was created)
- **Municipality boundaries:** "Inferring is challenging" — no formal boundaries
- **County format variations:** "County Cork" vs "Cork" vs "Dublin 15"

**OSM Eircode Coverage:**
- **Copyright restrictions** prevent systematic OSM import
- Only "cleanly sourced individual Eircodes" allowed
- OSM has incomplete Eircode coverage
- **Recommendation:** Don't rely on Nominatim for Eircode → coordinate lookups

**Geocoding recommendations from OSM wiki:**
1. Prioritize street-level matching in urban areas
2. Fall back to townland + postal town in rural
3. Use first 3 chars of Eircode for area disambiguation
4. Account for non-unique addresses with additional context

### Current HomeIQ.ie Implementation

**Resolution order** (from `backend/main.py:493-507`):
```python
1. Raw coordinates passthrough
2. Cache hit (24h TTL)
3. Eircode → DB exact match (indexed lookup)
4. Eircode → Nominatim (OSM data)
5. Token-based DB lookup (developments)
6. Nominatim (general geocoder)
7. Mapbox Geocoding API (commercial fallback)
8. Fuzzy DB ILIKE (last resort)
```

**Strengths:**
- Multi-tier fallback strategy
- DB-first for known addresses (fast)
- Caching reduces API costs

**Weaknesses identified:**
- Step 4 (Nominatim Eircode lookup) has low success rate due to OSM copyright issues
- No reverse geocoding (coordinate → Eircode)
- No routing key clustering for "nearby properties" features

### Optimization Recommendations

#### 4A. Add Routing Key Generation & Indexing

**Implementation:**
```sql
-- Add generated column
ALTER TABLE properties 
ADD COLUMN routing_key VARCHAR(3) GENERATED ALWAYS AS (
  CASE 
    WHEN eircode IS NOT NULL 
    THEN SUBSTRING(REPLACE(UPPER(eircode), ' ', ''), 1, 3)
    ELSE NULL
  END
) STORED;

-- Index for fast routing key lookups
CREATE INDEX idx_properties_routing_key ON properties(routing_key) 
WHERE routing_key IS NOT NULL;
```

**Benefits:**
- Enable "properties in same routing area" queries (~15k address clusters)
- Support neighborhood discovery without full geocoding
- Fast Eircode prefix matching for autocomplete
- Analytics by routing key area

**Query examples:**
```sql
-- Find properties in same routing area
SELECT * FROM properties 
WHERE routing_key = 'D02' 
  AND sale_date >= '2020-01-01'
ORDER BY sale_date DESC;

-- Compare routing key areas
SELECT routing_key, county, 
       COUNT(*) as total_sales,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
FROM properties
WHERE routing_key IS NOT NULL
GROUP BY routing_key, county
ORDER BY total_sales DESC;
```

**Estimated impact:** 
- 165k properties immediately queryable by routing key (21% coverage)
- Grows automatically as Eircodes enriched
- ~70% faster than coordinate-based queries for area searches

#### 4B. Create Routing Key → County Materialized View

**Problem:** Routing keys span county boundaries; need explicit mapping

**Implementation:**
```sql
CREATE MATERIALIZED VIEW routing_key_counties AS
SELECT 
  routing_key,
  MODE() WITHIN GROUP (ORDER BY county) as primary_county,
  COUNT(*) as property_count,
  ARRAY_AGG(DISTINCT county) as counties,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latitude) as centroid_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY longitude) as centroid_lon
FROM properties
WHERE routing_key IS NOT NULL 
  AND latitude IS NOT NULL
GROUP BY routing_key;

CREATE UNIQUE INDEX ON routing_key_counties(routing_key);

REFRESH MATERIALIZED VIEW routing_key_counties; -- Run after imports
```

**Use cases:**
- Eircode autocomplete with county context
- Routing key → coordinate lookup (fallback geocoding)
- Data quality validation (flag cross-county anomalies)
- User-facing routing key browser

**Maintenance:** Refresh after bulk imports or monthly

#### 4C. Implement Address Tokenization Improvements

**Current token-based matching** (`backend/main.py`):
- Splits address into significant words
- Requires all tokens present
- Standard deviation < 0.02° for cluster acceptance (~1.4km radius)

**Enhancement — Abbreviation Expansion:**
```python
ABBREVIATION_MAP = {
    'st': ['street', 'saint'],
    'rd': ['road'],
    'ave': ['avenue'],
    'mt': ['mount'],
    'apt': ['apartment'],
    'sq': ['square'],
    # Add Irish-specific
    'tce': ['terrace'],
    'pk': ['park'],
    'ct': ['court'],
    'dr': ['drive'],
    'bóthar': ['road'],  # Irish
    'sráid': ['street'],  # Irish
}
```

**Enhancement — Townland Handling:**
- Extract and tokenize townland names separately
- Weight townland matches higher in rural counties
- Use townlands.ie dataset for validation

**Enhancement — Coordinate Quality Scoring:**
- Current: Accept if stddev < 0.02°
- Proposed: Score by stddev and prefer tighter clusters
- Reject if coordinate falls outside county boundaries

---

## 5. Search Performance Optimization

### Current Architecture

**Radius search** (`backend/main.py` line ~320-325):
```sql
SELECT ..., ST_Distance(geog, ST_MakePoint($lon, $lat)::geography) AS distance_m
FROM properties
WHERE ST_DWithin(geog, ST_MakePoint($lon, $lat)::geography, $radius_metres)
ORDER BY sale_date DESC, distance_m
LIMIT 200
```

**Indexes:**
- `properties_geog_idx` — GiST spatial (76 MB)
- `properties_sale_date_idx` — btree (11 MB)

### Optimization Opportunities

#### 5A. Routing Key Pre-Filter

For queries in well-covered areas, pre-filter by routing key before spatial query:

```sql
-- If search center has known routing key (e.g., D02)
-- and radius < 5km, pre-filter candidates
WITH routing_filter AS (
  SELECT id FROM properties 
  WHERE routing_key IN ('D02', 'D01', 'D04')  -- Adjacent routing keys
)
SELECT p.*, ST_Distance(geog, ST_MakePoint($lon, $lat)::geography) AS distance_m
FROM properties p
WHERE p.id IN (SELECT id FROM routing_filter)
  AND ST_DWithin(geog, ST_MakePoint($lon, $lat)::geography, $radius_metres)
ORDER BY sale_date DESC, distance_m
LIMIT 200;
```

**Benefit:** Reduces spatial index scan size by ~93% in Dublin areas (D01-D24 = ~140k properties vs 781k total)

**When to apply:** 
- Routing key coverage >50% in area
- Radius < 10km (routing key = ~15k addresses)
- Can map search center to routing key

#### 5B. Add Composite Index for Common Filters

**Current queries often filter by:**
- County (optional)
- Date range (optional)
- Price range (optional)
- Spatial (always)

**Proposed index:**
```sql
CREATE INDEX idx_properties_county_date_geog 
ON properties(county, sale_date DESC, geog)
WHERE geog IS NOT NULL;
```

**Benefit:** Postgres can use county+date for initial filter, then spatial component

**Trade-off:** 
- Index size: ~150-200 MB estimated
- Maintenance overhead on imports
- Benefits county-specific searches (majority of queries)

#### 5C. Materialized View for Popular Searches

**Concept:** Pre-compute results for high-frequency searches

**Implementation:**
```sql
CREATE MATERIALIZED VIEW popular_area_searches AS
SELECT 
  routing_key,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latitude) as center_lat,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY longitude) as center_lon,
  jsonb_agg(
    jsonb_build_object(
      'id', id,
      'address', address,
      'price', price,
      'sale_date', sale_date,
      'latitude', latitude,
      'longitude', longitude
    ) ORDER BY sale_date DESC
  ) FILTER (WHERE sale_date >= NOW() - INTERVAL '3 years') as recent_sales
FROM properties
WHERE routing_key IS NOT NULL
GROUP BY routing_key;
```

**Use case:** "Show me recent sales in routing key D02"

**Refresh strategy:** Nightly or weekly (sales data static)

---

## 6. User Experience Enhancements

### 6A. Eircode Autocomplete

**Concept:** As user types Eircode, suggest routing keys with context

**API endpoint:**
```python
@app.get("/eircode/autocomplete")
async def eircode_autocomplete(prefix: str):
    """Return routing keys matching prefix with counts and locations."""
    # Match D, D0, D02 progressively
    query = """
        SELECT routing_key, primary_county, property_count,
               centroid_lat, centroid_lon
        FROM routing_key_counties
        WHERE routing_key LIKE $1 || '%'
        ORDER BY property_count DESC
        LIMIT 10
    """
    # Return: [{"routing_key": "D02", "county": "Dublin", "count": 8234, ...}]
```

**Frontend integration:** Show dropdown with "D02 — Dublin (8,234 properties)"

### 6B. Neighborhood Discovery

**Concept:** "Properties in the same routing key area"

**Example user flow:**
1. User searches for specific address
2. Result shows property details + Eircode (if available)
3. Link: "View 1,523 other sales in D02 area"
4. Opens routing key browse page with map + list

**Implementation:**
```python
@app.get("/eircode/{routing_key}")
async def routing_key_properties(routing_key: str, ...filters...):
    """All properties in a routing key area with typical filters."""
    # Existing endpoint already supports this
    # Enhancement: Add "context" field with routing key stats
```

**SEO benefit:** Creates 139 browsable landing pages (one per routing key)

### 6C. Similar Properties Feature

**Current:** Search by radius from address

**Enhanced:** Search by routing key + property characteristics

**Query:**
```sql
-- Find similar properties in same routing area
SELECT * FROM properties
WHERE routing_key = $1  -- Same routing key
  AND description = $2  -- Same property type
  AND price BETWEEN $3 * 0.8 AND $3 * 1.2  -- ±20% price
  AND sale_date >= $4 - INTERVAL '2 years'  -- Recent comparables
ORDER BY ABS(price - $3), sale_date DESC
LIMIT 20;
```

**Use case:** Valuation research, market comparables

---

## 7. Competitor Analysis

### Daft.ie

**Approach:**
- Hierarchical location structure (county → city → district → neighborhood)
- Eircodes displayed but not primary search mechanism
- URL structure: `/property-for-sale/{area}-{county}`
- Extensive pre-built navigation (9 sections, 20+ districts, 40+ neighborhoods)

**Optimization insights:**
- Pre-categorized browse paths reduce query load
- Image CDN with real-time transformation
- Static asset versioning
- Seven-digit numeric property IDs (simple primary key)

**Eircode usage:** Minimal — shown in addresses but no Eircode-specific search

### MyHome.ie

**Approach:**
- Geographic hierarchy with Dublin postal districts (D1-D24) prominent
- County → sub-region → property type structure
- No visible Eircode search functionality
- Traditional Irish geographic divisions prioritized

**Observation:** Market leaders rely on **traditional geography over Eircode** for search/navigation

**Implication for HomeIQ.ie:** 
- Routing key search is differentiator (competitors don't offer)
- But must maintain traditional county/area search as primary
- Eircode as enhancement, not replacement

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Immediate, low-risk improvements**

- [x] Address normalization (COMPLETE — running)
- [ ] Add routing_key generated column + index
- [ ] Create routing_key_counties materialized view
- [ ] Add routing key to API responses (where available)
- [ ] Update ARCHITECTURE.md with routing key strategy

**Estimated effort:** 8-12 hours  
**Cost:** $0 (internal work only)

### Phase 2: Search Enhancement (Week 3-4)
**Backend optimizations**

- [ ] Implement routing key pre-filter for spatial queries (5A)
- [ ] Add composite county+date+geog index (5B)
- [ ] Create /eircode/autocomplete endpoint (6A)
- [ ] Enhance token-based geocoding with abbreviation map (4C)
- [ ] Add routing key filtering to /search endpoint

**Estimated effort:** 16-20 hours  
**Cost:** $0

### Phase 3: Data Enrichment (Month 2)
**Choose ONE approach based on budget:**

**Option A — Scale Current Approach (Budget: $0-3k/year):**
- Increase Autoaddress to 800/day
- Add search-frequency priority queue
- Projected: 292k enrichments/year

**Option B — Reverse Geocoding Pilot (Budget: $500-1k one-time):**
- One-time reverse geocode 50k high-value properties
- Focus on: Price >€1M, sold 2023+, Dublin/Cork
- Test Autoaddress reverse API or alternative

**Option C — ECAD License (Budget: €5-15k/year):**
- License full dataset if enrichment needs >100k/year
- Requires legal/procurement process
- Ongoing maintenance overhead

**Recommendation:** Start with Option A (scale current), pilot Option B if success rate >60%

### Phase 4: UX Features (Month 3)
**User-facing enhancements**

- [ ] Eircode autocomplete in search bar
- [ ] "Other sales in this area" routing key links
- [ ] Routing key browse pages (/eircode/D02)
- [ ] Similar properties feature (routing key + characteristics)
- [ ] Update frontend to display routing keys

**Estimated effort:** 24-32 hours  
**Cost:** $0

### Phase 5: Monitoring & Iteration (Ongoing)
**Success metrics**

- [ ] Track geocoding source distribution (dashboard)
- [ ] Monitor routing key coverage growth (target: 40% by Q4 2026)
- [ ] A/B test routing key vs radius search performance
- [ ] User engagement with Eircode-based features (analytics)
- [ ] Search success rate improvements (goal: +15% from token enhancements)

---

## 9. Cost-Benefit Analysis

### Current State Costs
- Autoaddress API: ~$6,000/year (500/day estimate)
- Railway backend hosting: ~$20/month
- Supabase database: Free tier

### Proposed Optimizations

| Option | Upfront Cost | Recurring Cost | Time to ROI | Benefit |
|--------|-------------|----------------|-------------|---------|
| **Routing key indexing** | $0 | $0 | Immediate | +70% faster area searches, new features |
| **Token geocoding enhancements** | $0 | $0 | 2-4 weeks | +15-20% search success rate |
| **Scale to 800/day Autoaddress** | $0 | +$3k/year | 12 months | 3-year coverage vs 4.5-year |
| **Reverse geocoding pilot** | $500-1k | $0 | 3 months | Test 60%+ success vs 40% current |
| **ECAD license** | €5-15k | €5-15k/year | 24+ months | Unlimited lookups, but high fixed cost |
| **Materialized views** | $0 | $0 | Immediate | Faster popular searches, SEO benefit |
| **Composite indexes** | $0 | +150MB storage | Immediate | Faster filtered searches |

### Recommended Priority

**High ROI, Low Cost:**
1. Routing key indexing — enables multiple features for zero cost
2. Token geocoding enhancements — improves core search accuracy
3. Materialized views — speeds up common queries

**Medium ROI, Low-Medium Cost:**
4. Scale Autoaddress to 800/day — incremental coverage improvement
5. Reverse geocoding pilot — test if better than address matching

**High Cost, Uncertain ROI:**
6. ECAD license — only if enrichment needs exceed 100k/year (not recommended yet)

---

## 10. Key Findings & Recommendations

### Critical Insights

1. **Eircode is address-level, not area-level**  
   Only the 3-character routing key has geographic meaning. Cannot cluster by full Eircode.

2. **OSM/Nominatim has poor Eircode coverage**  
   Copyright restrictions prevent systematic OSM imports. Don't rely on Nominatim for Eircode lookups.

3. **Routing keys are underutilized**  
   139 routing areas covering ~15k addresses each are perfect for neighborhood discovery features.

4. **Address normalization is critical**  
   Irish addresses have high ambiguity, especially rural. Normalization improved success rate from 24% to 40%.

5. **Competitors don't emphasize Eircode**  
   Daft and MyHome rely on traditional geography. Eircode integration is differentiator opportunity.

### Top 5 Recommendations

**1. Implement routing key indexing (Phase 1)**  
   - Zero cost, immediate benefit
   - Enables neighborhood discovery, autocomplete, area analytics
   - 165k properties immediately searchable by routing area

**2. Enhance token-based geocoding (Phase 2)**  
   - Add abbreviation expansion and townland handling
   - Expected +15-20% search success rate
   - Improves experience for rural addresses

**3. Create routing key UX features (Phase 4)**  
   - "Other sales in this area" links
   - Eircode autocomplete with context
   - SEO-friendly routing key browse pages
   - Differentiates from competitors

**4. Scale Autoaddress enrichment gradually (Phase 3)**  
   - Start with 500/day (current), monitor success rate
   - Add search-frequency priority queue
   - Scale to 800/day if budget allows (+$3k/year)

**5. Pilot reverse geocoding for high-value properties (Phase 3)**  
   - One-time $500-1k investment
   - Test on 50k properties (price >€1M, recent, urban)
   - If success rate >60%, expand program

### What NOT to Do

❌ **Don't license ECAD yet** — too expensive for current enrichment needs  
❌ **Don't rely on Nominatim for Eircode lookups** — OSM coverage is poor  
❌ **Don't treat full Eircode as area identifier** — only routing key has geographic meaning  
❌ **Don't abandon traditional search** — county/area search must remain primary  

---

## 11. Technical Resources

### Official Documentation
- **Eircode.ie** — https://www.eircode.ie/business/products-and-services  
  ECAF and ECAD product information, licensing
  
- **GeoDirectory** — https://www.geodirectory.ie  
  Address database (3.5M addresses), partnerships with An Post + Tailte Éireann

- **Autoaddress** — https://autoaddress.com, https://docs.autoaddress.com  
  Address validation and Eircode enrichment API

### Open Data & Standards
- **OSM Wiki: Ireland** — https://wiki.openstreetmap.org/wiki/Ireland  
  Irish address structure, geocoding best practices, Eircode limitations

- **Townlands.ie** — https://www.townlands.ie  
  Historical boundary data for rural address validation

- **Data.gov.ie** — https://data.gov.ie  
  Irish open data portal (no Eircode datasets found, but boundary data available)

### Competitor Implementations
- **Daft.ie** — Hierarchical location, minimal Eircode integration
- **MyHome.ie** — Dublin postal districts prominent, no Eircode search
- **PropertyPriceRegister.ie** — Official PPR site (TLS error prevented analysis)

### HomeIQ.ie Codebase
- `backend/main.py` — Geocoding resolution order, Eircode detection logic
- `db/eircode_enrich.py` — Current enrichment strategy (Autoaddress 500/day)
- `scripts/normalize_addresses.py` — Address cleaning for better matching
- `ARCHITECTURE.md` — System architecture documentation

---

## Appendix: Routing Key List (Current Coverage)

From previous analysis, HomeIQ.ie has 301 unique routing keys in the database. This exceeds the official 139 count, suggesting:
- Data quality issues (invalid Eircodes)
- Northern Ireland BT codes included
- Typos or malformed Eircodes

**Recommendation:** Run validation query:
```sql
-- Find potentially invalid routing keys
SELECT routing_key, COUNT(*) as count
FROM properties
WHERE routing_key IS NOT NULL
  AND routing_key !~ '^[A-Z][0-9][0-9W]$'  -- Invalid format
GROUP BY routing_key
ORDER BY count DESC;
```

Clean invalid routing keys before implementing Phase 1 indexing.

---

**End of Research Report**
