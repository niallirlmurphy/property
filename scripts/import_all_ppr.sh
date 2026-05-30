#!/bin/bash
#
# Import all 781,000 PPR records to Salesforce in batches
#
# This will take approximately 6-8 hours due to Salesforce API limits
#

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     PPR DATA → SALESFORCE FULL IMPORT                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "This will import all 781,000 PPR records to Salesforce"
echo "Estimated time: 6-8 hours"
echo ""
echo "Press Ctrl+C to cancel or Enter to continue..."
read

TOTAL_RECORDS=781501
BATCH_SIZE=10000
BATCHES=$(( ($TOTAL_RECORDS + $BATCH_SIZE - 1) / $BATCH_SIZE ))

echo ""
echo "Processing $TOTAL_RECORDS records in $BATCHES batches of $BATCH_SIZE"
echo ""

for (( batch=0; batch<$BATCHES; batch++ )); do
    SKIP=$(( $batch * $BATCH_SIZE ))

    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║ Batch $(($batch + 1))/$BATCHES"
    echo "║ Records: $SKIP - $(($SKIP + $BATCH_SIZE))"
    echo "╚══════════════════════════════════════════════════════════════╝"

    python3 scripts/import_to_salesforce.py \
        --limit $BATCH_SIZE \
        --skip $SKIP \
        2>&1 | grep -E "✓|✗|Total|Batch|Success|Failed" || true

    echo ""
    echo "Batch $(($batch + 1))/$BATCHES complete"
    echo "Progress: $(( ($batch + 1) * 100 / $BATCHES ))%"
    echo ""

    # Brief pause between batches
    sleep 2
done

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     IMPORT COMPLETE                                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Verify total count:"
echo "  sf data query --query \"SELECT COUNT() FROM Account WHERE PPR_Import__c = '$(date +%Y-%m-%d)'\""
