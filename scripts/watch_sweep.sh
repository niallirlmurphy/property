#!/usr/bin/env bash
# Watch the re-geocode sweep; exit (→ triggers a task notification) once cumulative
# properties-processed reaches TARGET, or the sweep has finished. Prints a one-line
# status the assistant relays to the user.
#   usage: watch_sweep.sh <target_processed>
set -u
cd "$(dirname "$0")/.."
TARGET=${1:-500}

processed() {
  # Sum across all sub-batch logs: completed batches use their "Processed: N" line;
  # the in-flight batch uses its latest "Progress: X/..." value.
  local total=0
  for f in logs/regeocode_sweep_*_b*.log; do
    [ -e "$f" ] || continue
    local done_n
    done_n=$(grep -Eo 'Processed: [0-9,]+' "$f" | tail -1 | tr -dc '0-9')
    if [ -n "$done_n" ]; then
      total=$((total + done_n))
    else
      local prog
      prog=$(grep -Eo 'Progress: [0-9]+' "$f" | tail -1 | grep -Eo '[0-9]+')
      [ -n "$prog" ] && total=$((total + prog))
    fi
  done
  echo "$total"
}

sweep_done() { grep -q "sweep finished" /tmp/regeo_sweep.log 2>/dev/null; }

while :; do
  p=$(processed)
  if sweep_done; then
    echo "SWEEP_DONE processed=${p}"
    exit 0
  fi
  if [ "${p:-0}" -ge "$TARGET" ]; then
    echo "CHECKPOINT processed=${p} target=${TARGET}"
    exit 0
  fi
  sleep 20
done
