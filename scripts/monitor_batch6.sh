#!/bin/bash
# Monitor batch 6 enrichment and report status hourly

LOG_FILE="logs/batch6_enrichment_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "Starting Batch 6 enrichment: $(date)" | tee -a "$LOG_FILE"
echo "Target: 702 properties from 2026" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Start enrichment in background and capture PID
python3 scripts/enrich_batch6_2026.py --batch-size 702 --rate-limit 10 2>&1 | tee -a "$LOG_FILE" &
ENRICH_PID=$!

echo "Enrichment PID: $ENRICH_PID" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Monitor progress and report hourly
LAST_REPORT=$(date +%s)
HOUR_COUNT=0

while kill -0 $ENRICH_PID 2>/dev/null; do
    sleep 300  # Check every 5 minutes

    NOW=$(date +%s)
    ELAPSED=$((NOW - LAST_REPORT))

    # Report every hour (3600 seconds)
    if [ $ELAPSED -ge 3600 ]; then
        HOUR_COUNT=$((HOUR_COUNT + 1))

        echo "" | tee -a "$LOG_FILE"
        echo "========================================" | tee -a "$LOG_FILE"
        echo "HOURLY STATUS REPORT #$HOUR_COUNT" | tee -a "$LOG_FILE"
        echo "Time: $(date)" | tee -a "$LOG_FILE"
        echo "========================================" | tee -a "$LOG_FILE"

        # Count progress from log
        FULLY_ENRICHED=$(grep -c "✅ Fully enriched" "$LOG_FILE")
        PARTIAL=$(grep -c "⚠️  Partial" "$LOG_FILE")
        FAILED=$(grep -c "❌" "$LOG_FILE")
        TOTAL_PROCESSED=$((FULLY_ENRICHED + PARTIAL + FAILED))

        echo "Progress: $TOTAL_PROCESSED / 702 properties" | tee -a "$LOG_FILE"
        echo "Fully enriched: $FULLY_ENRICHED" | tee -a "$LOG_FILE"
        echo "Partial: $PARTIAL" | tee -a "$LOG_FILE"
        echo "Failed: $FAILED" | tee -a "$LOG_FILE"

        if [ $TOTAL_PROCESSED -gt 0 ]; then
            SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($FULLY_ENRICHED / $TOTAL_PROCESSED) * 100}")
            echo "Success rate: $SUCCESS_RATE%" | tee -a "$LOG_FILE"
        fi

        echo "========================================" | tee -a "$LOG_FILE"
        echo "" | tee -a "$LOG_FILE"

        LAST_REPORT=$NOW
    fi
done

# Final report
wait $ENRICH_PID
EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "FINAL REPORT" | tee -a "$LOG_FILE"
echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

FULLY_ENRICHED=$(grep -c "✅ Fully enriched" "$LOG_FILE")
PARTIAL=$(grep -c "⚠️  Partial" "$LOG_FILE")
FAILED=$(grep -c "❌" "$LOG_FILE")
TOTAL_PROCESSED=$((FULLY_ENRICHED + PARTIAL + FAILED))

echo "Total processed: $TOTAL_PROCESSED / 702" | tee -a "$LOG_FILE"
echo "Fully enriched: $FULLY_ENRICHED" | tee -a "$LOG_FILE"
echo "Partial: $PARTIAL" | tee -a "$LOG_FILE"
echo "Failed: $FAILED" | tee -a "$LOG_FILE"

if [ $TOTAL_PROCESSED -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($FULLY_ENRICHED / $TOTAL_PROCESSED) * 100}")
    echo "Success rate: $SUCCESS_RATE%" | tee -a "$LOG_FILE"
fi

echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
