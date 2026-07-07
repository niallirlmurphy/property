#!/bin/bash
# Railway cron job for daily security monitoring
# Add this to Railway as a scheduled task or use Railway's cron feature

set -e

echo "🔒 Railway Security Monitor - $(date)"
echo "================================================"

# Ensure we're in the project directory
cd "$(dirname "$0")/.."

# Run security checks
if python3 scripts/security_monitor.py; then
    echo "✅ Security checks passed"
    exit 0
else
    echo "⚠️ Security issues detected - attempting auto-fix..."

    # Attempt auto-fix
    if python3 scripts/security_monitor.py --fix; then
        echo "✅ Issues auto-fixed successfully"
        exit 0
    else
        echo "❌ Could not auto-fix all issues"

        # Send notification (if notification service is configured)
        # curl -X POST $WEBHOOK_URL -H "Content-Type: application/json" \
        #   -d '{"text":"🚨 Security monitoring failed on Railway"}'

        exit 1
    fi
fi
