#!/bin/bash
# Check enrichment progress

echo "==================================================================="
echo "Enrichment Progress Monitor"
echo "==================================================================="
echo ""

# Check if results file exists
if [ -f "enrichment_full_results.json" ]; then
    echo "📊 Results file found: enrichment_full_results.json"
    echo ""

    # Show statistics
    python3 -c "
import json
from datetime import datetime

with open('enrichment_full_results.json') as f:
    results = json.load(f)

total = len(results)
enriched = [r for r in results if r.get('bedrooms') or r.get('property_type')]
with_bedrooms = sum(1 for r in results if r.get('bedrooms'))
with_type = sum(1 for r in results if r.get('property_type'))
skipped = sum(1 for r in results if r.get('bedrooms') or r.get('property_type'))

print(f'Total properties processed: {total:,}')
print(f'Successfully enriched: {len(enriched):,} ({len(enriched)/total*100:.1f}%)')
print(f'  - With bedrooms: {with_bedrooms:,}')
print(f'  - With property type: {with_type:,}')
print(f'')

# Check if we have timestamps
if results and results[-1].get('enriched_at'):
    last_time = results[-1].get('enriched_at')
    print(f'Last updated: {last_time}')
    print(f'')

# Estimate remaining (assuming 8030 total)
target = 8030
if total < target:
    remaining = target - total
    print(f'⏳ Estimated remaining: {remaining:,} properties')
    # At 10 seconds per property + batch delays
    # ~10 sec/property = 600 properties/hour
    hours_remaining = remaining / 600
    print(f'   Estimated time: {hours_remaining:.1f} hours')
else:
    print('✅ All properties processed!')
"
else
    echo "⏳ Results file not created yet - enrichment starting..."
    echo ""
    echo "Expected file: enrichment_full_results.json"
fi

echo ""
echo "==================================================================="
echo "To view live output:"
echo "  tail -f enrichment_progress.log"
echo ""
echo "To check again:"
echo "  bash scripts/check_enrichment_progress.sh"
echo "==================================================================="
