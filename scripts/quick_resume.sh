#!/bin/bash
# Quick resume script - checks connectivity and restarts processes if needed

cd "/Users/nmurphy/claude/property price project"

echo "================================================================================"
echo "QUICK RESUME SCRIPT"
echo "================================================================================"
echo ""

# Test database connectivity
echo "Testing database connection..."
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), connect_timeout=5)
    conn.close()
    print('✅ Database connection successful')
    exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Cannot connect to database. Check your network connection."
    echo "   Try again in a few minutes when network is stable."
    exit 1
fi

echo ""

# Check if enrichment is running
echo "Checking enrichment process..."
if pgrep -f "python3.*enrich_multi_batch.py" > /dev/null 2>&1; then
    echo "✅ Enrichment already running"
else
    echo "🚀 Starting enrichment..."
    nohup python3 scripts/enrich_multi_batch.py --months 3 --batch-size 50 --batch-delay 180 > logs/enrichment_batched.log 2>&1 &
    sleep 2
    if pgrep -f "python3.*enrich_multi_batch.py" > /dev/null 2>&1; then
        echo "✅ Enrichment started (PID: $(pgrep -f 'python3.*enrich_multi_batch.py'))"
    else
        echo "❌ Failed to start enrichment - check logs/enrichment_batched.log"
    fi
fi

echo ""

# Check if normalization is running
echo "Checking normalization process..."
if pgrep -f "python3.*normalize_addresses.py" > /dev/null 2>&1; then
    echo "✅ Normalization already running"
else
    echo "🚀 Starting normalization..."
    nohup python3 scripts/normalize_addresses.py > logs/normalize.log 2>&1 &
    sleep 2
    if pgrep -f "python3.*normalize_addresses.py" > /dev/null 2>&1; then
        echo "✅ Normalization started (PID: $(pgrep -f 'python3.*normalize_addresses.py'))"
    else
        echo "❌ Failed to start normalization - check logs/normalize.log"
    fi
fi

echo ""
echo "================================================================================"
echo "Resume complete!"
echo ""
echo "To monitor progress:"
echo "  tail -f logs/enrichment_batched.log"
echo "  tail -f logs/normalize.log"
echo ""
echo "To check status:"
echo "  python3 scripts/monitor_and_resume.py --status"
echo "================================================================================"
