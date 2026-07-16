# PPR Import, Normalisation & Geocoding — Runbook

Consolidated step-by-step instructions for a biweekly PPR data update: import new sales,
normalise addresses, geocode, and enrich. This is the single source of truth that pulls
together `scripts/README_PIPELINE.md`, `docs/GEOCODING_IMPROVEMENTS_2026-07-09.md`,
`docs/MAPBOX_USAGE_TRACKING.md`, and the CLAUDE.md architecture notes.

**Cadence:** 1st and 15th of each month (whenever a fresh PPR snapshot is published).

---

## 0. Prerequisites (once per machine)

- Python 3.10+ with deps installed: `pip install -r backend/requirements.txt`
- `backend/.env` populated with:
  - `DATABASE_URL` — Supabase connection string (postgres/service role, **not** anon)
  - `MAPBOX_TOKEN` — `pk.xxx` token
- Load env before running scripts:
  ```bash
  export $(grep -v '^#' backend/.env | xargs)
  ```

---

## 1. Get the latest PPR snapshot

1. Download the newest `PPR-ALL.csv` from the Property Price Register (gov.ie).
2. Place it at: `source data/PPR-ALL.csv` (overwrite the old file).
3. Record the snapshot date — row counts are snapshot-specific.

```bash
wc -l "source data/PPR-ALL.csv"   # sanity check row count, do NOT cat the file
```

---

## 2. Dry run first (always)

Preview what the pipeline will do without touching the database or spending Mapbox quota.

```bash
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv" --dry-run
```

Confirm the "new sales found" count is sane before proceeding.

---

## 3. Run the full pipeline (recommended path)

One command runs all three stages (import → geocode → enrich) with the 2026-07-09
enhancements applied automatically.

```bash
python3 scripts/ppr_full_pipeline.py --csv "source data/PPR-ALL.csv"
```

Expected wall-clock:
- 100 new sales → ~10–15 min
- 500 new sales → ~40–50 min
- 1,000 new sales → ~1.5 hr

If the run is large or you want tighter control / smaller failure blast radius, use the
manual stage-by-stage path in Section 4 instead.

---

## 4. Manual stage-by-stage (when you need control)

### 4a. Import + normalise
```bash
python3 scripts/sync_ppr_updates.py --skip-geocoding
```
What it does:
- Reads the CSV **backward** (most recent first); imports only sales newer than the latest
  `sale_date` already in the DB (skips 700k+ existing rows efficiently).
- **Normalises addresses** on the way in and writes `address_normalized`:
  - HTML entity cleaning (`Tandy&#039;s` → `Tandy's`, `&amp;` → `&`)
  - Remove "No." prefix; expand abbreviations (Rd→Road, St→Street, Ave→Avenue, Dr→Drive, Apt→Apartment)
  - Title case with exceptions (Dublin, Cork, Co.); punctuation + whitespace cleanup
- Flags each new row `needs_geocoding = TRUE`.
- Logs to `logs/ppr_sync.log`.

### 4b. Geocode
```bash
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply
# Stay under quota on big backlogs:
python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 500 --apply
```
What it does (per property):
1. Clean HTML entities.
2. Extract base address for **bulk sales** (`Units 1-76 Bridge Hall` → `Bridge Hall`).
3. **Eircode-first**: geocode the Eircode if present, else fall back to the address.
4. Validate: Ireland bounds (hard reject) → county boundary (soft) → routing-key distance
   (hard reject if >5km). Minimum acceptable quality score: 70.
5. Write coordinates + quality score; usage tracked in the `mapbox_usage` table.

Expected: ~95% overall success (~98% with Eircode), avg quality ~78/100.
Cost: 1 Mapbox request per property.

> Tip: test with `--limit 10` (omit `--apply`) before a large `--apply` run.

### 4c. Enrich
```bash
python3 scripts/enrich_batch6_2026.py --batch-size 100 --rate-limit 5
```
What it does:
- Fetches recent properties missing `bedrooms` / `property_type` (prioritises recent,
  high-value).
- DuckDuckGo full-page text scraping to extract bedroom count and property type.
- Rate-limits (default 5s) to avoid blocking.

Expected: ~90% for 2025–2026 properties. Recommended batch: 100–200 per run.

---

## 5. Verify & monitor

```bash
# Mapbox usage this month (reserve headroom under the 50k/month cap)
python3 scripts/mapbox_usage_tracker.py --current-month

# Remaining geocoding backlog
psql $DATABASE_URL -c "SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE"

# Recent imports sanity check
psql $DATABASE_URL -c "SELECT COUNT(*), MIN(sale_date), MAX(sale_date) FROM properties WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'"

# End-to-end production checks
python3 tests/test_production_suite.py
```

Also tail logs during long runs:
```bash
tail -f logs/ppr_sync.log
tail -f logs/enrichment_batch6_*.log
```

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Geocoding "No route to host" | DB connection timeout on long runs | Run in smaller batches with `--limit` |
| Enrichment 0% success | DuckDuckGo blocking | Raise `--rate-limit` to 10–15s |
| "Mapbox limit exceeded" | Hit 50k this month | Wait for reset, or split across months |
| HTML entities in old addresses | Pre-fix data | Re-import via `sync_ppr_updates.py` |
| Few/no search results after import | NULL geometry / not geocoded | Confirm step 4b ran with `--apply` |

Monthly Mapbox allocation guide: 2k for PPR sync, 5k for API, 43k for batch/backlog.

---

## 7. Related docs

- `scripts/README_PIPELINE.md` — pipeline component reference & benchmarks
- `docs/GEOCODING_IMPROVEMENTS_2026-07-09.md` — why the enhancements exist
- `docs/MAPBOX_USAGE_TRACKING.md` — quota system
- `docs/GEOCODING_QUEUE.md` — `needs_geocoding` flagging & priority
- `docs/GEOCODING_QUALITY_MONITORING.md` — validation framework
- `CLAUDE.md` — address normalisation spec (authoritative rules)
