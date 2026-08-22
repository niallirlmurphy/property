#!/bin/bash
# Quick command to check Mapbox quota
# Usage: ./scripts/check_mapbox_quota.sh

set -e

cd "$(dirname "$0")/.."

# Check if tracking is set up
if ! python3 -c "
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    exists = await conn.fetchval('''
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'mapbox_usage'
        )
    ''')
    await conn.close()
    return exists

if not asyncio.run(check()):
    print('Mapbox tracking not set up. Run: python3 scripts/setup_mapbox_tracking.py')
    exit(1)
" 2>/dev/null; then
    echo "❌ Mapbox tracking not set up"
    echo "Run: python3 scripts/setup_mapbox_tracking.py"
    exit 1
fi

# Display current month usage
python3 scripts/mapbox_usage_tracker.py --current-month
