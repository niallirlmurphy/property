#!/bin/bash
# Quick progress report script

cd "/Users/nmurphy/claude/property price project"

python3 -c "
import json
from datetime import datetime

with open('scripts/batch_process_state.json', 'r') as f:
    state = json.load(f)

print('=' * 80)
print(f'PROGRESS REPORT - {datetime.now().strftime(\"%H:%M:%S\")}')
print('=' * 80)

norm = state['normalization']
print(f'📝 Normalization: {norm[\"completed\"]:,}/{norm[\"total\"]:,} ({norm[\"percent\"]}%) | Batches: {norm[\"batches_run\"]}')

enrich = state['enrichment']
print(f'🏠 Enrichment: {enrich[\"completed\"]:,}/{enrich[\"total\"]:,} ({enrich[\"percent\"]}%) | Batches: {enrich[\"batches_run\"]}')

# Calculate progress since start
start_norm = 337886
start_enrich = 39
gained_norm = norm['completed'] - start_norm
gained_enrich = enrich['completed'] - start_enrich

print(f'\n⚡ Since start: +{gained_norm:,} normalized, +{gained_enrich:,} enriched')
print('=' * 80)
"
