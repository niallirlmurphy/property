#!/bin/bash
# Geocode 50,000 properties in batches of 1,000
# Uses Mapbox batch geocoding API

set -e

DATABASE_URL="${DATABASE_URL:-postgresql://postgres.jyezhkgevzejhundypxn:eboCukbtcBX0Ozyq@aws-0-eu-west-1.pooler.supabase.com:5432/postgres}"
LOG_DIR="logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="$LOG_DIR/mapbox_bulk_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "======================================================================" | tee -a "$MAIN_LOG"
echo "BULK GEOCODING: 50,000 properties" | tee -a "$MAIN_LOG"
echo "Started: $(date)" | tee -a "$MAIN_LOG"
echo "======================================================================" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# Check how many properties need geocoding
NEEDS_GEOCODING=$(python3 << 'EOF'
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE")
print(cur.fetchone()[0])
conn.close()
EOF
)

echo "Properties flagged for geocoding: $NEEDS_GEOCODING" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# Calculate number of batches (1000 per batch is Mapbox limit)
BATCHES=$(( ($NEEDS_GEOCODING + 999) / 1000 ))
echo "Will process in $BATCHES batches of up to 1,000 each" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

BATCH_NUM=1
TOTAL_SUCCESS=0
TOTAL_FAILED=0

while [ $BATCH_NUM -le $BATCHES ]; do
    echo "======================================================================" | tee -a "$MAIN_LOG"
    echo "BATCH $BATCH_NUM of $BATCHES" | tee -a "$MAIN_LOG"
    echo "Started: $(date)" | tee -a "$MAIN_LOG"
    echo "======================================================================" | tee -a "$MAIN_LOG"

    # Run geocoding
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --apply 2>&1 | tee -a "$MAIN_LOG"

    # Extract results from last run
    SUCCESS=$(grep "✓ Success:" "$MAIN_LOG" | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")
    FAILED=$(grep "✗ Failed:" "$MAIN_LOG" | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")

    TOTAL_SUCCESS=$((TOTAL_SUCCESS + SUCCESS))
    TOTAL_FAILED=$((TOTAL_FAILED + FAILED))

    echo "" | tee -a "$MAIN_LOG"
    echo "Batch $BATCH_NUM complete: $SUCCESS success, $FAILED failed" | tee -a "$MAIN_LOG"
    echo "Running totals: $TOTAL_SUCCESS success, $TOTAL_FAILED failed" | tee -a "$MAIN_LOG"
    echo "" | tee -a "$MAIN_LOG"

    # Check if there are more properties to process
    REMAINING=$(python3 << 'EOF'
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('backend/.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM properties WHERE needs_geocoding = TRUE")
print(cur.fetchone()[0])
conn.close()
EOF
    )

    if [ "$REMAINING" -eq 0 ]; then
        echo "No more properties to geocode. Done!" | tee -a "$MAIN_LOG"
        break
    fi

    echo "Remaining: $REMAINING properties" | tee -a "$MAIN_LOG"
    echo "" | tee -a "$MAIN_LOG"

    BATCH_NUM=$((BATCH_NUM + 1))

    # Small delay to avoid rate limiting
    sleep 2
done

echo "" | tee -a "$MAIN_LOG"
echo "======================================================================" | tee -a "$MAIN_LOG"
echo "BULK GEOCODING COMPLETE" | tee -a "$MAIN_LOG"
echo "======================================================================" | tee -a "$MAIN_LOG"
echo "Total batches processed: $((BATCH_NUM - 1))" | tee -a "$MAIN_LOG"
echo "Total success: $TOTAL_SUCCESS" | tee -a "$MAIN_LOG"
echo "Total failed: $TOTAL_FAILED" | tee -a "$MAIN_LOG"
echo "Success rate: $(python3 -c "print(f'{100*$TOTAL_SUCCESS/($TOTAL_SUCCESS+$TOTAL_FAILED):.1f}%')")" | tee -a "$MAIN_LOG"
echo "Finished: $(date)" | tee -a "$MAIN_LOG"
echo "======================================================================" | tee -a "$MAIN_LOG"
