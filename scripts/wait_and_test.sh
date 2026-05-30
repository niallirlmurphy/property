#!/bin/bash
# Wait for hybrid geocoding and Vercel deployment to complete, then run test suite

echo "════════════════════════════════════════════════════════════════"
echo "  Monitoring deployment and database update status"
echo "════════════════════════════════════════════════════════════════"
echo ""

FRONTEND_URL="https://homeiq.ie"
INITIAL_BUNDLE=$(curl -s "$FRONTEND_URL/" | grep -o 'index-[a-zA-Z0-9]*.js' | head -1)
echo "Initial frontend bundle: $INITIAL_BUNDLE"
echo ""

# Function to check if hybrid geocoding is still running
check_hybrid() {
    ps aux | grep "[c]reate_hybrid_geocoding.py --apply" >/dev/null 2>&1
    return $?
}

# Function to check current frontend bundle
check_bundle() {
    curl -s "$FRONTEND_URL/" | grep -o 'index-[a-zA-Z0-9]*.js' | head -1
}

# Monitor hybrid geocoding
echo "⏳ Waiting for hybrid geocoding to complete..."
while check_hybrid; do
    sleep 30
    echo "   Still running... ($(date '+%H:%M:%S'))"
done
echo "✅ Hybrid geocoding complete!"
echo ""

# Monitor Vercel deployment
echo "⏳ Waiting for Vercel deployment to complete..."
RETRY_COUNT=0
MAX_RETRIES=40  # 20 minutes max (40 * 30s)

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    CURRENT_BUNDLE=$(check_bundle)

    if [ "$CURRENT_BUNDLE" != "$INITIAL_BUNDLE" ]; then
        echo "✅ New deployment detected: $CURRENT_BUNDLE"
        break
    fi

    sleep 30
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Still waiting... attempt $RETRY_COUNT/$MAX_RETRIES ($(date '+%H:%M:%S'))"
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  Timeout waiting for deployment, running tests anyway..."
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Both processes complete - Starting test suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Run the test suite
cd "/Users/nmurphy/claude/property price project"
python3 tests/test_production_suite.py

exit $?
