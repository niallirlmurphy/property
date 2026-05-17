# Production Observability

This document describes the observability infrastructure for the PPR web app.

## Sentry Integration

### Setup
1. Create a free Sentry account at https://sentry.io
2. Create a new Python/FastAPI project
3. Copy the DSN from Settings → Client Keys (DSN)
4. Add to Railway environment variables:
   ```
   SENTRY_DSN=https://xxxxxxxx@o000000.ingest.sentry.io/0000000
   ```

### What Sentry Captures
- **Unhandled exceptions** — automatic stack traces with context
- **Performance monitoring** — 10% sample of API requests with timing breakdown
- **Release tracking** — correlates errors to git commits via `RAILWAY_GIT_COMMIT_SHA`
- **Environment tagging** — separates dev/staging/production errors
- **Slow queries** — database queries >1s are flagged

### Viewing Errors
- Dashboard: https://sentry.io → Your Project
- Alerts: Configure notifications for error spikes or new issues
- Releases: See which deploy introduced a regression

## Search Query Analytics

Every `/search` request is logged to the `search_log` table with:
- Query text and resolved coordinates
- Geocoding source (`db_exact`, `nominatim`, `mapbox`, `cache`, etc.)
- Result count (detects "0 results" failures)
- Response time in milliseconds
- All filter parameters (price range, year range, county)
- User agent and IP address

### Useful Analytics Queries

#### Top searched addresses (for eircode enrichment prioritization)
```sql
SELECT 
    query,
    COUNT(*) as search_count,
    AVG(result_count) as avg_results,
    AVG(elapsed_ms) as avg_latency_ms
FROM search_log
WHERE ts > NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY search_count DESC
LIMIT 50;
```

#### Queries that return zero results (potential geocoding failures)
```sql
SELECT 
    query,
    geocode_source,
    resolved_lat,
    resolved_lon,
    COUNT(*) as failure_count
FROM search_log
WHERE result_count = 0
  AND ts > NOW() - INTERVAL '7 days'
GROUP BY query, geocode_source, resolved_lat, resolved_lon
ORDER BY failure_count DESC
LIMIT 20;
```

#### Geocoding source breakdown (is Nominatim working?)
```sql
SELECT 
    geocode_source,
    COUNT(*) as requests,
    AVG(result_count) as avg_results,
    AVG(elapsed_ms) as avg_latency_ms
FROM search_log
WHERE ts > NOW() - INTERVAL '24 hours'
GROUP BY geocode_source
ORDER BY requests DESC;
```

#### Slowest queries (performance regression detection)
```sql
SELECT 
    query,
    elapsed_ms,
    result_count,
    radius_km,
    ts
FROM search_log
WHERE ts > NOW() - INTERVAL '1 day'
ORDER BY elapsed_ms DESC
LIMIT 20;
```

#### Most popular counties/areas (content strategy insights)
```sql
SELECT 
    COALESCE(county_filter, 'All Counties') as county,
    COUNT(*) as searches,
    AVG(result_count) as avg_results
FROM search_log
WHERE ts > NOW() - INTERVAL '30 days'
GROUP BY county_filter
ORDER BY searches DESC
LIMIT 15;
```

#### Search volume by hour (traffic patterns)
```sql
SELECT 
    DATE_TRUNC('hour', ts) as hour,
    COUNT(*) as searches,
    AVG(elapsed_ms) as avg_latency_ms
FROM search_log
WHERE ts > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;
```

#### Failed geocoding attempts (addresses not found in any service)
```sql
SELECT 
    query,
    COUNT(*) as attempts,
    MAX(ts) as last_attempt
FROM search_log
WHERE resolved_lat IS NULL
  AND ts > NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY attempts DESC
LIMIT 20;
```

### Automated Monitoring

Set up scheduled queries (via cron/Supabase functions) to alert on:

1. **Zero-result spike**: >20% of searches returning 0 results in the last hour
   ```sql
   SELECT 
       COUNT(*) FILTER (WHERE result_count = 0)::FLOAT / COUNT(*) as zero_result_rate
   FROM search_log
   WHERE ts > NOW() - INTERVAL '1 hour';
   ```

2. **Latency regression**: p95 response time >2s
   ```sql
   SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY elapsed_ms) as p95_ms
   FROM search_log
   WHERE ts > NOW() - INTERVAL '1 hour';
   ```

3. **Geocoding failures**: Nominatim fallback rate >50%
   ```sql
   SELECT 
       COUNT(*) FILTER (WHERE geocode_source = 'nominatim')::FLOAT / COUNT(*) as nominatim_rate
   FROM search_log
   WHERE ts > NOW() - INTERVAL '1 hour';
   ```

## Benefits

### Caught by This System
- ✅ Wrong eircode geocoding (D14 XT52 → wrong coordinates) — visible in zero-result queries
- ✅ 24-hour cache serving stale results — visible in geocode_source="cache" with wrong coordinates
- ✅ Addresses resolving to wrong areas (Mount Carmel → Leitrim) — visible in low result counts for known-good addresses
- ✅ Performance regressions after deploy — visible in latency spikes correlated to Sentry releases

### Product Insights
- Which areas/counties to write content pages for (top searches)
- Which addresses need eircode enrichment most urgently (high search volume + missing eircode)
- User search patterns (time of day, mobile vs desktop via user-agent)
- Filter usage (price ranges, year ranges) for UX improvements

## Data Retention

Search logs grow at ~1KB per search. At 10K searches/day:
- 1 month = ~300MB
- 1 year = ~3.6GB

Consider archiving logs older than 90 days to S3/cold storage if needed.

To truncate old logs:
```sql
DELETE FROM search_log WHERE ts < NOW() - INTERVAL '90 days';
```
