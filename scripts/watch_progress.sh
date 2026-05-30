#!/bin/bash
# Watch re-geocoding progress in real-time

echo "Re-geocoding Progress Monitor"
echo "Press Ctrl+C to exit"
echo ""

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           RE-GEOCODING PROGRESS MONITOR                      ║"
    echo "║           $(date '+%Y-%m-%d %H:%M:%S')                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if progress database exists
    if [ -f "regeocode_progress.db" ]; then
        sqlite3 regeocode_progress.db "
            SELECT
                '  Processed:     ' || processed || ' properties',
                '  ✓ Succeeded:   ' || succeeded || ' (' || ROUND(100.0 * succeeded / NULLIF(processed, 0), 1) || '%)',
                '  ✗ Failed:      ' || failed,
                '  ⊘ Skipped:     ' || skipped,
                '  ',
                '  Last Update:   ' || last_update
            FROM session_stats
            WHERE id = 1
        " | sed 's/|/\n/g'

        echo ""
        echo "  Recent successes:"
        sqlite3 regeocode_progress.db "
            SELECT '    ' || substr(timestamp, 12, 8) || ' - ' || substr(p.address, 1, 50)
            FROM regeocode_log l
            LEFT JOIN properties p ON p.id = l.property_id
            WHERE l.status = 'success'
            ORDER BY l.timestamp DESC
            LIMIT 5
        " 2>/dev/null || echo "    (loading...)"
    else
        echo "  No progress data yet..."
        echo "  Re-geocoding is starting up..."
    fi

    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "  Refreshing every 5 seconds..."
    echo "  Press Ctrl+C to exit"

    sleep 5
done
