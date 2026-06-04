# Geocoding TODO

## 🗓️ Revisit Next Month (July 2026)

### Current Status (June 4, 2026)
- **Total properties:** 784,854
- **Geocoded:** 712,911 (90.8%)
- **Still missing:** 71,943 (9.2%)

### Recent Progress
1. **June 2, 2026:** Exact address matching → +1,544 properties
2. **June 4, 2026:** Street-level pattern matching → +33,756 properties
3. **Total improvement:** +35,300 properties (from 86.8% to 90.8%)

### Remaining 71,943 Properties
These are likely:
- **Unique addresses** - no similar properties in the database to match against
- **Rural properties** - isolated with no neighbors
- **New developments** - few sales recorded yet
- **Inconsistent formats** - addresses too different to pattern-match
- **Apartments in unique buildings** - need building-level coordinates

### Next Steps to Try (July 2026)

**1. Run Pattern Matching Again**
The 33,756 newly geocoded properties may enable more matches:
```bash
python3 scripts/geocode_street_level.py
```

**2. Mapbox Batch Geocoding**
Use remaining API quota (~100k requests/month, free tier):
```bash
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
```
- Expected success: 60-70% of remaining
- Cost: FREE (within monthly limit)
- Would geocode ~43-50k more properties → **95-96% total coverage**

**3. Analyze What's Left**
```bash
python3 scripts/analyze_missing_geocodes.py
```

**4. Consider Paid Options**
If pushing for 98%+ coverage:
- Google Geocoding API (more expensive but very accurate)
- Manual geocoding for high-value properties (recent sales, expensive areas)

### Cost-Benefit Analysis
- Current 90.8% coverage is excellent for most use cases
- Users can still search by county, area, price
- Remaining 9.2% are mostly rural/edge cases
- **Recommendation:** Run Mapbox batch in July to reach ~95%, then assess if further work is needed

### Files to Use
- `scripts/geocode_street_level.py` - Street pattern matching
- `scripts/geocode_mapbox_batch.py` - Mapbox batch geocoding
- `scripts/analyze_missing_geocodes.py` - Analyze what's missing
- `scripts/geocode_from_existing_fast.py` - Exact address matching

### Monitoring
Check geocoding status anytime:
```bash
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*), COUNT(latitude) FROM properties')
total, geocoded = cur.fetchone()
print(f'Geocoded: {geocoded:,}/{total:,} ({100*geocoded/total:.1f}%)')
conn.close()
"
```

---

**Set calendar reminder:** July 4, 2026 - "Revisit geocoding remaining 71,943 properties"
