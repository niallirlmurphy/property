# Database Storage Cleanup Recommendations

**Date:** 2026-06-04  
**Current database size:** 537 MB (169 MB table + 349 MB indexes + 19 MB other)  
**Issue:** Database disk full error preventing address normalization backfill  

---

## Summary

The properties table has **349 MB of indexes** vs **169 MB of data** — a 2:1 ratio indicating over-indexing. Several indexes are unused or redundant and can be safely dropped to free up ~150 MB of disk space.

---

## Cleanup Opportunities

### 🔴 HIGH PRIORITY: Drop Unused Trigram Index (Saves ~107 MB)

**Index:** `properties_address_trgm_idx` (107 MB)  
**Purpose:** Fuzzy text search on addresses  
**Usage:** 198 scans total, but NOT actually used (sequential scan instead)  
**Evidence:** EXPLAIN ANALYZE shows `Seq Scan` instead of index scan for ILIKE queries

**Why it's not working:**
- Trigram indexes require `pg_trgm` GIN/GIST operator class
- Current ILIKE queries don't use trigram operators (%, LIKE, ILIKE alone won't trigger it)
- Would need similarity operators (`%`, `<->`, etc.) to use this index

**Backend usage:**
- Fuzzy geocoding fallback: `WHERE address ILIKE '%' || $1 || '%'`
- This is step 8 of 8 in geocoding cascade — rarely reached
- When reached, it's OK for it to be slow (last resort)

**Recommendation:** **DROP** this index
```sql
DROP INDEX properties_address_trgm_idx;
```

**Impact:** None. Backend already does sequential scan, so no performance change.

---

### 🟡 MEDIUM PRIORITY: Consolidate County Indexes (Saves ~8 MB)

**Indexes:**
- `properties_county_idx` (8.5 MB) - single column
- `properties_county_date_idx` (13 MB) - composite (county, sale_date)

**Usage:**
- County grouping: Uses either index
- Trends queries: Uses composite index (county + date range)

**Recommendation:** **DROP** single-column index, keep composite
```sql
DROP INDEX properties_county_idx;
```

**Impact:** PostgreSQL can use `properties_county_date_idx` for county-only queries (leftmost column). Slight performance hit on `GROUP BY county` but still fast.

---

### 🟢 LOW PRIORITY: Consider Dropping Eircode Normalization Index (Saves ~8 MB)

**Index:** `properties_eircode_norm_idx` (7.9 MB)  
**Column:** Normalized Eircode (spaces removed, uppercase)  

**Usage:** Backend uses `REPLACE(UPPER(eircode), ' ', '')` directly in queries

**Recommendation:** Keep for now, but if space is critical:
```sql
-- Option 1: Drop if not used
DROP INDEX properties_eircode_norm_idx;

-- Option 2: Create computed column + index instead (more efficient)
ALTER TABLE properties ADD COLUMN eircode_normalized TEXT 
    GENERATED ALWAYS AS (REPLACE(UPPER(eircode), ' ', '')) STORED;
CREATE INDEX properties_eircode_normalized_idx ON properties (eircode_normalized);
DROP INDEX properties_eircode_norm_idx;
```

---

### 🟢 LOW PRIORITY: Enrichment Columns (Saves ~1 MB)

**Columns:** `bedrooms`, `property_type`  
**Current population:** 0.00% (27 and 36 properties out of 784k)  
**Indexes:** `properties_bedrooms_idx` (5.4 MB), `properties_property_type_idx` (5.4 MB)

**Issue:** Indexes exist but data is <0.01% populated

**Recommendation:** **Keep** — these will fill over time
- Enrichment runs automatically with each PPR sync (100 properties per run)
- Indexes are needed for future filtering by bedroom count/type
- Even at 0% population, 5 MB per index is reasonable overhead

---

### ⚪ NO ACTION: Keep These Indexes

**Essential indexes (do NOT drop):**
- `properties_geog_idx` (90 MB) - **CRITICAL** for radius/polygon search
- `properties_pkey` (24 MB) - **REQUIRED** primary key
- `properties_price_idx` (31 MB) - Used for price filtering
- `properties_sale_date_idx` (9.5 MB) - Used for date range queries
- `properties_eircode_idx` (13 MB) - Used for Eircode search
- `idx_properties_address_normalized` (27 MB) - Will be heavily used once normalization completes
- `idx_properties_routing_key*` (7 MB total) - Used for Eircode validation

---

## Recommended Cleanup Script

```sql
-- Drop unused trigram index (saves 107 MB)
DROP INDEX IF EXISTS properties_address_trgm_idx;

-- Drop redundant single-column county index (saves 8 MB)
DROP INDEX IF EXISTS properties_county_idx;

-- Optional: Drop if space is critical (saves 8 MB)
-- DROP INDEX IF EXISTS properties_eircode_norm_idx;

-- Vacuum to reclaim space
VACUUM FULL properties;
```

**Expected savings:** 115 MB minimum (107 + 8), up to 123 MB if dropping eircode_norm_idx

---

## After Cleanup: Address Normalization

Once disk space is freed:

```bash
# Backfill remaining 483,000 addresses (62% of database)
python3 scripts/normalize_addresses.py

# This will take ~30-60 minutes
# Updates in batches of 1,000 properties
# No downtime required (non-blocking updates)
```

**Expected behavior:**
- Will populate `address_normalized` column for 483k properties
- `idx_properties_address_normalized` (27 MB) will become fully utilized
- Improves geocoding matching (street-level patterns rely on normalized addresses)

---

## Other Tables (No Cleanup Needed)

- `submissions`: 80 KB (23 rows) — keep
- `search_log`: 184 KB (232 rows) — keep for analytics
- `email_alerts`: 96 KB (5 rows) — keep
- `routing_key_stats` materialized view: 112 KB — **keep** (used for Eircode centroids)

---

## Disk Space Prevention

**Current state:**
- 784,854 properties
- 537 MB total database size
- Growing by ~2,000 properties per month (biweekly PPR imports)

**Growth projections:**
- 2026: +24k properties → +15 MB
- 2027: +24k properties → +15 MB

**Recommendation:** Monitor disk usage monthly. Supabase free tier has 500 MB limit — after cleanup (537 - 115 = 422 MB) there's 78 MB headroom (~5 years of growth).

---

## Implementation

1. **Backup first** (Supabase has automatic backups, but verify)
2. Run cleanup SQL script
3. Monitor query performance for 24-48 hours
4. Run address normalization script
5. Document any performance changes

---

## Questions?

- Trigram index: Safe to drop? **YES** — not being used, takes 107 MB
- County index: Safe to drop single-column? **YES** — composite index covers it
- Enrichment indexes: Drop until data is populated? **NO** — keep for future use
- Address normalized index: Keep? **YES** — will be heavily used once data is populated

**Next step:** Run the cleanup script, then retry address normalization.
