#!/usr/bin/env bash
# Re-geocode sweep in small resumable sub-batches.
# Each sub-batch geocodes + commits independently, then the next fetches the next
# highest-priority worklist rows. A crash costs at most one sub-batch's Mapbox spend.
# MapboxClient enforces the 50k/month cap and will stop the run if it is reached.
set -u
cd "$(dirname "$0")/.."
export $(grep '^DATABASE_URL=' backend/.env | xargs)

SUB=${SUB:-3000}          # rows per sub-batch
ROUNDS=${ROUNDS:-10}      # number of sub-batches (SUB*ROUNDS total target)
EXTRA_ARGS=${EXTRA_ARGS:-}  # extra filters, e.g. "--suspect --eircode-only --county Dublin"
LOGDIR=logs
mkdir -p "$LOGDIR"
STAMP=$(date +%Y%m%d_%H%M%S)

for i in $(seq 1 "$ROUNDS"); do
  echo "===== sub-batch $i/$ROUNDS ($SUB rows) at $(date) ====="
  python3 -u scripts/geocode_mapbox_batch.py --needs-geocoding --limit "$SUB" --apply $EXTRA_ARGS \
      > "$LOGDIR/regeocode_sweep_${STAMP}_b${i}.log" 2>&1
  rc=$?
  tail -8 "$LOGDIR/regeocode_sweep_${STAMP}_b${i}.log"
  if [ $rc -ne 0 ]; then
    echo "sub-batch $i exited rc=$rc — stopping sweep"
    break
  fi
  # Stop early if the cap was hit (client prints a limit message)
  if grep -qi "monthly limit\|quota\|cap reached" "$LOGDIR/regeocode_sweep_${STAMP}_b${i}.log"; then
    echo "Mapbox cap reached — stopping sweep"
    break
  fi
done
echo "===== sweep finished at $(date) ====="
