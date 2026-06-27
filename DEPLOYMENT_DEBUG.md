# Deployment Debug - June 27, 2026

## Issue
Production valuation API using Nominatim geocoding instead of database lookup for "44 Mount Carmel Road".

## Local Testing
✅ Geocoder query works correctly locally:
- Input: "44 Mount Carmel Road"
- Found: "44 Mount Carmel Road, Goatstown"
- Method: database_exact (as expected)

## Production Behavior
❌ Production using Nominatim instead:
- `"method": "nominatim"`
- Should be: `"method": "database_exact"`

## Latest Commits
- 92b56cf feat: add crowdsourced property enrichment via valuation requests
- 750d908 feat: improve geocoding UX for properties not in database
- b4bda2d fix: use same address matching logic as S1 page

## Hypothesis
Railway may not have deployed latest code or deployment failed.

## Next Steps
1. Trigger Railway redeploy
2. Check Railway deployment logs
3. Verify production endpoint returns database_exact method
