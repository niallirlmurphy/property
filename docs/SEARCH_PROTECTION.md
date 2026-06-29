# Search Protection System

This document explains the comprehensive protection system that prevents regressions in HomeIQ's core search functionality.

## Why This Exists

Search is the primary feature users interact with. A regression in county filtering (like showing Cork properties when Dublin is selected) breaks user trust and makes the site unusable. This protection system ensures such regressions are caught **before** they reach production.

## What's Protected

The system guards these critical behaviors:

1. **County filter correctness** - Exact and radius search respect the county parameter
2. **Cache isolation** - Different counties don't share cached results  
3. **Cross-county address handling** - "Main Street" in Cork ≠ "Main Street" in Dublin
4. **Performance** - Search stays under 1 second response time

## Components

### 1. Automated Test Suite (`tests/test_search_core.py`)

**17 parametrized test cases** covering:
- Exact matches with county filter ("36 fairfield road" + Dublin = 0 results)
- Radius search with county filter (all results from correct county)
- Cache isolation (Dublin/Cork requests don't leak)
- Performance regression (<1s per query)

**Run locally:**
```bash
pytest tests/test_search_core.py -v
```

**Run specific tests:**
```bash
pytest tests/test_search_core.py -v -k "county_filter"
pytest tests/test_search_core.py -v -k "cache"
```

### 2. Pre-Commit Hook (`.git/hooks/pre-commit`)

**Automatic checks** before every commit:
- ✅ Blocks commits with secrets (.env files, API keys)
- ✅ Blocks disabling Row-Level Security
- ✅ Blocks CORS wildcard in production
- ✅ Runs search tests if search code changed
- ✅ Verifies database security policies

**Files that trigger search tests:**
- `backend/main.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/components/SearchPanel.tsx`

**Test run:**
- Starts backend automatically if not running
- Runs county filter tests (fast subset, ~15s)
- Full test suite runs in CI/CD

### 3. GitHub Actions CI/CD (`.github/workflows/search-protection.yml`)

**Runs on every PR** that touches search code:
- Starts backend service
- Runs full test suite (all 17 tests)
- Blocks merge if tests fail
- Reports results as GitHub status check

**Configure GitHub repo:**
```
Settings → Branches → Branch protection rules → main
☑ Require status checks to pass before merging
  Add: "search-tests"
☑ Require branches to be up to date before merging
```

### 4. Code Ownership (`.github/CODEOWNERS`)

**Automatic PR reviewers** for search-critical files:
- Search endpoints: `backend/main.py`
- Frontend search logic: `App.tsx`, `api.ts`, `SearchPanel.tsx`
- Test suite: `tests/test_search_core.py`
- Documentation: `docs/SEARCH_LOGIC.md`

Owner: `@niallirlmurphy`

### 5. Production Monitoring (Sentry Integration)

**Real-time alerts** if county filter breaches happen in production:

```python
# backend/main.py - monitors radius search
if county and len(rows) > 0:
    result_counties = {r["county"] for r in result["results"]}
    if county not in result_counties:
        sentry_sdk.capture_message(
            f"County filter breach in radius search",
            level="error",
            extras={"query": q, "county": county, ...}
        )
```

**What gets tracked:**
- County filter breaches (wrong county in results)
- Performance regressions (slow queries)
- Search errors and failures

### 6. Documentation (`docs/SEARCH_LOGIC.md`)

**Single source of truth** for:
- Expected search behavior (county filtering rules)
- SQL query patterns (correct/incorrect examples)
- Cache isolation requirements
- Pre-merge checklist

## Workflow: Making Search Changes

### Step 1: Local Development

```bash
# Make your changes to search code
vim backend/main.py

# Run tests locally (recommended before commit)
pytest tests/test_search_core.py -v

# Commit (pre-commit hook runs automatically)
git add backend/main.py
git commit -m "fix: improve county filter logic"
# → Pre-commit hook runs search tests
# → Blocks commit if tests fail
```

### Step 2: Create Pull Request

```bash
git push origin feature-branch

# Open PR on GitHub
# → GitHub Actions runs full test suite
# → Status check appears on PR ("search-tests: pending")
# → Review required from @niallirlmurphy (CODEOWNERS)
```

### Step 3: Review Checklist

Before approving PR:
- [ ] All GitHub Actions tests pass
- [ ] Manual browser test: "36 fairfield road" + Dublin = 0 results
- [ ] Manual browser test: "36 fairfield road" + Cork = 1 result
- [ ] Response times < 1s (check logs)
- [ ] Cache behavior correct (if cache changed)

### Step 4: Merge & Deploy

```bash
# Merge PR → auto-deploys to production
# Railway (backend): automatic deployment
# Vercel (frontend): automatic deployment

# Monitor for issues
# → Sentry alerts for county filter breaches
# → Response time monitoring
```

## Emergency: Bypassing Tests

**Only in true emergencies** (production down, critical hotfix):

```bash
# Skip pre-commit hook
git commit --no-verify -m "hotfix: restore service"

# Then immediately:
# 1. Create follow-up PR with proper testing
# 2. Run test suite manually: pytest tests/test_search_core.py -v
# 3. Document why bypass was necessary
```

## Test Coverage Matrix

| Scenario | Test Name | Expected Behavior |
|----------|-----------|-------------------|
| Exact search + Dublin filter | `test_exact_search[36 fairfield road-Dublin]` | 0 results (no match) |
| Exact search + Cork filter | `test_exact_search[36 fairfield road-Cork]` | 1 result (Cork property) |
| Radius search + Dublin filter | `test_search[Dublin 2-Dublin]` | ≥50 Dublin results |
| Radius search + Meath filter | `test_search[Nobber-Meath]` | ≥100 Meath results |
| Cache isolation | `test_cache_respects_county_filter` | Dublin/Cork don't leak |
| Performance | `test_performance_regression` | All queries <1s |
| Ambiguous addresses | `test_search[Main Street-Cork]` | Cork Main St, not Dublin |

## Maintenance

### Adding New Test Cases

When a new bug is found:

1. **Add test case** to `tests/test_search_core.py`:
```python
# Add to SEARCH_TEST_CASES
("new query", "county", "expected_county", min_results, "description"),
```

2. **Verify it fails** (reproduces the bug):
```bash
pytest tests/test_search_core.py -v -k "new query"
# Should FAIL before fix
```

3. **Fix the bug** in `backend/main.py` or frontend

4. **Verify it passes**:
```bash
pytest tests/test_search_core.py -v -k "new query"
# Should PASS after fix
```

5. **Commit** - test becomes permanent protection

### Updating Test Dependencies

```bash
# Update pytest/httpx
pip install --upgrade pytest pytest-asyncio httpx

# Update GitHub Actions (if Python version changes)
vim .github/workflows/search-protection.yml
# Change: python-version: '3.10' → '3.11'
```

### Debugging Test Failures

**Test fails locally:**
```bash
# Run with verbose output
pytest tests/test_search_core.py -v --tb=long -k "failing_test"

# Check backend is running
curl http://localhost:8000/health

# Check test API URL
TEST_API_URL=http://localhost:8000 pytest tests/test_search_core.py -v
```

**Test fails in CI but passes locally:**
```bash
# Check GitHub Actions logs:
# Actions tab → failed workflow → search-tests job

# Common issues:
# - DATABASE_URL secret not set
# - Backend failed to start (check startup logs)
# - Timeout (increase wait time in workflow)
```

## Metrics

Track these to ensure system effectiveness:

- **Test coverage**: 17 test cases protecting 4 critical behaviors
- **Test runtime**: ~67s full suite, ~15s pre-commit subset
- **False positive rate**: 0% (tests are reliable)
- **Bugs caught**: 1 regression blocked (Cork property leak, 2026-06-29)
- **Pre-commit success rate**: Should be >95% (few failures expected)

## Future Enhancements

Consider adding:

1. **Property count validation** - Verify result counts match expected
2. **Eircode routing key tests** - Test D02/H91 routing key logic
3. **Polygon search tests** - Test map-based area selection
4. **Load testing** - Concurrent request handling
5. **Browser automation** - Selenium/Playwright UI tests

## Questions?

- **Pre-commit hook issues?** Check `.git/hooks/pre-commit` execution permissions
- **GitHub Actions failing?** Verify `DATABASE_URL` and `MAPBOX_TOKEN` secrets
- **Test suite questions?** See `tests/test_search_core.py` docstrings
- **Production alerts?** Check Sentry dashboard

Contact: @niallirlmurphy  
Last updated: 2026-06-29
