# Valuation Office API Research - June 19, 2026

## Summary

Tailte Éireann (formerly Valuation Office) provides property valuation data through an **API Explorer web interface**, but REST API endpoints are **not publicly documented** for programmatic access.

## Official Sources

### 1. Data.gov.ie Dataset
- **URL:** https://data.gov.ie/dataset/valuation-office-api
- **Publisher:** Tailte Éireann
- **License:** Creative Commons Attribution 4.0
- **Status:** High Value Dataset, Continuous updates
- **Landing Page:** https://tailte.ie/home/api/

### 2. Coverage
**Post-Revaluation Areas (28 authorities):**
- Counties: Carlow, Cavan, Kildare, Kilkenny, Laois, Leitrim, Longford, Louth, Meath, Monaghan, Offaly, Roscommon, Sligo, Tipperary, Westmeath, Wexford, Wicklow
- Dublin: Dun Laoghaire-Rathdown, Fingal, South Dublin, Dublin City Council
- Cork City and County (limited pre-Revaluation data)
- Waterford City and County Council
- Limerick City and County Council

## Available Data Fields

### Query Parameters (via Web Interface)
- **Geographic:** County, X ITM, Y ITM coordinates, Address, Eircode
- **Property ID:** Property Number (max 8 digits)
- **Property Details:**
  - Category (11 types: Office, Fuel/Depot, Leisure, Industrial, Health, Hospitality, Minerals, Misc, Retail-Shops, Utility, Retail-Warehouse)
  - Use (specific usage)
  - Area Per Floor
  - Floor Use
  - Level
  - Car Park
- **Valuation:** NAV Total, Rateable Valuation, Publication Date

### Response Formats
- CSV (Comma-separated values)
- JSON (JavaScript Object Notation)
- GeoJSON (Geographic JSON)

### Data for Apartment Complexes
Based on available fields, Valuation Office holds:
- ✅ Property address
- ✅ Category (likely "Residential" or specific apartment type)
- ✅ Use description
- ✅ Floor areas
- ✅ Individual floor details
- ✅ Valuation figures
- ❓ Complex/development name (unclear if available)
- ❓ Total unit count (not explicitly listed)
- ❓ Year built (not in documentation)

## API Access Status

### ❌ REST API Not Publicly Accessible
**What we tested:**
- Common API endpoint patterns (https://api.tailte.ie, https://tailte.ie/api)
- Direct property queries
- Swagger/OpenAPI documentation
- JavaScript/AJAX endpoints in web interface

**Result:** No publicly exposed REST endpoints found.

### ✅ Web Interface Only
The API Explorer at https://tailte.ie/home/api/ is a **web-based query tool**, not a programmatic REST API.

Users can:
- Build queries through forms
- Download results in CSV/JSON/GeoJSON
- Generate reusable query URLs (unclear format)

## Limitations

### Cork City and County
Queries do NOT return:
- Category
- Use
- Validation Date
- Valuation Report

### Confidentiality Restrictions
Limited detail for:
- Hotels
- Pubs
- Cinemas
- Service stations
- Guesthouses

### API Status
- Described as "work in progress"
- Subject to change
- No completeness guarantees

## Integration Options

### Option 1: Manual Web Scraping (Not Recommended)
- Use Selenium/Puppeteer to automate web interface
- **Cons:** Fragile, slow, may violate ToS, no bulk access

### Option 2: Bulk Download + Local Database
- Download full datasets via web interface
- Build local SQLite/PostgreSQL database
- **Pros:** Fast queries, offline access
- **Cons:** One-time snapshot, manual updates

### Option 3: Contact Tailte Éireann
- Request programmatic API access
- Email: opendata@tailte.ie
- **Pros:** Official support, bulk access, documentation
- **Cons:** May require approval, potential fees

### Option 4: Alternative Data Sources
Since Valuation Office API is not readily accessible, consider:

#### GeoDirectory
- **URL:** https://www.geodirectory.ie
- **Coverage:** All Irish addresses with building data
- **Data:** Address, coordinates, building type, occupancy
- **Access:** Commercial license required

#### OSM (OpenStreetMap)
- **URL:** https://www.openstreetmap.org
- **Data:** Building footprints, addr:* tags, building:flats count
- **Access:** Free, Overpass API available
- **Limitations:** Crowdsourced, inconsistent apartment data

#### Eircodes Database
- **URL:** https://www.eircode.ie
- **Data:** Address-to-Eircode mappings
- **Access:** Eircode Finder API (limited free tier)

## Recommendations for Property Price Project

### Immediate Actions
1. **Contact Tailte Éireann** (opendata@tailte.ie)
   - Request REST API access for research/public benefit project
   - Explain use case: enriching PPR data with apartment complex details
   - Emphasize open data license (CC-BY 4.0)

2. **Test Bulk Download**
   - Use web interface to export sample county (e.g., Dublin)
   - Assess data quality for apartment enrichment
   - Check if complex names and unit counts are included

3. **Evaluate Alternatives**
   - OpenStreetMap for building footprints (free)
   - GeoDirectory for commercial access (if budget available)

### Integration Priority
Given current findings:
- **High Value:** If API access granted
- **Medium Value:** If bulk downloads contain complex names/unit counts
- **Low Value:** If only individual property valuations available

### Hybrid Approach
Continue current web scraping for individual houses, supplement with:
- Valuation Office data for apartment complexes (if accessible)
- OSM building data for footprints and context
- Manual curation for high-value developments

## Next Steps

1. **Email Tailte Éireann** requesting:
   - REST API endpoint documentation
   - Authentication method
   - Rate limits
   - Bulk access options
   - Sample response for apartment complex query

2. **Test Alternative:** OpenStreetMap Overpass API
   - Query by coordinates for building data
   - Check for `building:flats`, `addr:housename`, `building:levels`
   - Free, immediate access

3. **Evaluate ROI:**
   - Time investment vs data quality improvement
   - Coverage (28 counties vs nationwide)
   - Maintenance burden

## Contact Information
- **Tailte Éireann Open Data:** opendata@tailte.ie
- **General Inquiries:** info@tailte.ie
- **Website:** https://tailte.ie

---

**Research Date:** June 19, 2026  
**Researcher:** Claude Code  
**Status:** API endpoints not publicly accessible, contact required for programmatic access
