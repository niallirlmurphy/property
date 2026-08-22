# Resume Processes After Network Issue

Your enrichment and normalization processes stopped due to a network connectivity issue with Supabase.

## Quick Resume (Recommended)

When your network is back, simply run:

```bash
cd /Users/nmurphy/claude/property\ price\ project
./scripts/quick_resume.sh
```

This will:
- ✅ Test database connectivity
- ✅ Start enrichment if not running
- ✅ Start normalization if not running
- ✅ Show you the status

## Manual Resume

If you prefer to start processes manually:

```bash
cd /Users/nmurphy/claude/property\ price\ project

# Start batched enrichment (50 properties per batch, 3-min pauses)
nohup python3 scripts/enrich_multi_batch.py --months 3 --batch-size 50 --batch-delay 180 > logs/enrichment_batched.log 2>&1 &

# Start address normalization
nohup python3 scripts/normalize_addresses.py > logs/normalize.log 2>&1 &
```

## Monitor Progress

### Check status once:
```bash
python3 scripts/monitor_and_resume.py --status
```

### Continuous monitoring (checks every 5 minutes):
```bash
python3 scripts/monitor_and_resume.py --watch
```

### Auto-resume mode (checks every 5 min and auto-restarts if stopped):
```bash
python3 scripts/monitor_and_resume.py --watch
```

### Watch logs in real-time:
```bash
# Enrichment
tail -f logs/enrichment_batched.log

# Normalization
tail -f logs/normalize.log
```

## What the New Enrichment Does

The new **batched multi-source enrichment** (`enrich_multi_batch.py`):

- **Sources:** Google → Daft.ie → MyHome.ie (cascade until success)
- **Batch size:** 50 properties at a time
- **Pauses:** 3 minutes between batches
- **Rate limiting:** 4-5 seconds between requests
- **Goal:** Avoid triggering anti-bot blocks

### Expected Results:
- **Success rate:** 30-60% (much better than 0.7%)
- **Time:** ~10-12 hours for 8,668 properties
- **Coverage:** Best for recent high-value properties

### Batch Strategy:
- Small batches keep volume low per site
- Pauses between batches prevent pattern detection
- Spreads load across three sources
- Much more sustainable than bulk requests

## Last Known Progress (Before Network Issue)

**Address Normalization:**
- Completed: 446,886 / 784,854 (56.9%)
- Remaining: 337,968 properties

**Property Enrichment (last 3 months):**
- Total: 8,668 properties
- Enriched: ~148 with property type, ~59 with bedrooms
- Still needed: ~8,500 properties

## Troubleshooting

**If database connection fails:**
```bash
# Test connectivity
ping aws-0-eu-west-1.pooler.supabase.com

# Wait for network to stabilize, then run quick_resume.sh
```

**If processes won't start:**
- Check logs for errors: `tail -100 logs/enrichment_batched.log`
- Verify DATABASE_URL is set: `cat backend/.env | grep DATABASE_URL`

**If you need to stop processes:**
```bash
pkill -f enrich_multi_batch
pkill -f normalize_addresses
```

## Files Created

- `scripts/enrich_multi_batch.py` - New batched enrichment with Google + Daft + MyHome
- `scripts/monitor_and_resume.py` - Monitor and auto-resume processes
- `scripts/quick_resume.sh` - One-command resume script
- `RESUME.md` - This file
