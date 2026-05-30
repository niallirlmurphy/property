#!/bin/bash
# Wait for hybrid geocoding to complete, then immediately secure the database

echo "⏳ Waiting for hybrid geocoding to complete before securing database..."

while ps aux | grep "[c]reate_hybrid_geocoding.py --apply" >/dev/null 2>&1; do
    sleep 10
done

echo "✅ Hybrid geocoding complete!"
echo ""
echo "🔒 Securing database with Row-Level Security..."
echo ""

cd "/Users/nmurphy/claude/property price project"
export $(grep DATABASE_URL backend/.env | xargs)
python3 scripts/enable_rls_security.py

exit $?
