"""
Data quality and enrichment progress tracking.

These tests report metrics on geocoding coverage, eircode enrichment, and
address ambiguity. They are designed to pass while surfacing a readable
snapshot each run so progress can be tracked over time.

Hard thresholds catch regressions (e.g. a re-import wiping geocodes).
Soft metrics are printed unconditionally so you can see trends across runs.
"""

import pytest


# ---------------------------------------------------------------------------
# Thresholds — update if dataset grows or enrichment targets change
# ---------------------------------------------------------------------------

MIN_ROWS             = 750_000
MIN_GEOCODED_PCT     = 75.0   # % of rows with lat/lon
MIN_EIRCODE_PPR_PCT  =  5.0   # % of rows with PPR-sourced eircode (conservative floor)
MAX_OUT_OF_BOUNDS    = 0      # rows with coordinates outside Ireland
MAX_CENTROID_COORDS  = 50     # max coordinates with 100+ distinct addresses (centroid fallback limit)
MAX_CENTROID_MEDIUM  = 200    # max coordinates with 10-99 distinct addresses (medium priority)
MIN_REGEOCODE_SUCCESS_RATE = 70.0  # % of re-geocoding attempts that should succeed


# ---------------------------------------------------------------------------
# Geocoding coverage
# ---------------------------------------------------------------------------

def test_geocoding_coverage(db):
    """Geocoding rate stays above threshold; prints a full coverage snapshot."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                                          AS total,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL)     AS geocoded,
            COUNT(*) FILTER (WHERE latitude IS NULL)         AS not_geocoded
        FROM properties
    """)
    total, geocoded, not_geocoded = cur.fetchone()
    pct = geocoded / total * 100 if total else 0

    print(f"\n--- Geocoding coverage ---")
    print(f"  Total rows:      {total:>10,}")
    print(f"  Geocoded:        {geocoded:>10,}  ({pct:.1f}%)")
    print(f"  Not geocoded:    {not_geocoded:>10,}  ({100-pct:.1f}%)")

    assert total >= MIN_ROWS, f"Only {total:,} rows — expected ≥{MIN_ROWS:,}"
    assert pct >= MIN_GEOCODED_PCT, (
        f"Geocoding rate {pct:.1f}% is below threshold {MIN_GEOCODED_PCT}%"
    )


def test_coordinates_within_ireland(db):
    """No geocoded rows have coordinates outside Ireland's bounding box."""
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM properties
        WHERE latitude IS NOT NULL
          AND (latitude  < 51.4 OR latitude  > 55.4
            OR longitude < -10.5 OR longitude > -5.5)
    """)
    out_of_bounds = cur.fetchone()[0]
    print(f"\n--- Coordinate bounds ---")
    print(f"  Out-of-bounds rows: {out_of_bounds:,}")
    assert out_of_bounds <= MAX_OUT_OF_BOUNDS, (
        f"{out_of_bounds} rows have coordinates outside Ireland bounding box"
    )


def test_duplicate_geocodes_centroid_detection(db):
    """
    Check if too many addresses share identical coordinates.

    When geocoding falls back to county/town centroids, hundreds or thousands
    of distinct addresses get mapped to the same point. This test detects that
    pattern and fails if the problem is widespread.

    Threshold: Maximum 50 coordinates with 100+ distinct addresses.
    (Current baseline from 2025-05 assessment shows ~50 centroid coords)
    """
    cur = db.cursor()
    cur.execute("""
        SELECT
            latitude,
            longitude,
            COUNT(DISTINCT address) as distinct_addresses,
            COUNT(*) as total_sales,
            ARRAY_AGG(DISTINCT county) FILTER (WHERE county IS NOT NULL) as counties
        FROM properties
        WHERE latitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING COUNT(DISTINCT address) >= 100
        ORDER BY COUNT(DISTINCT address) DESC
    """)
    centroid_coords = cur.fetchall()
    count = len(centroid_coords)

    print(f"\n--- Duplicate geocode / centroid detection ---")
    print(f"  Coordinates with 100+ distinct addresses: {count:,}")

    if centroid_coords:
        print(f"\n  Top 10 worst offenders:")
        print(f"  {'Coordinate':<30} {'Addresses':<12} {'Sales':<10} {'Counties'}")
        print(f"  {'-'*30} {'-'*12} {'-'*10} {'-'*30}")
        for lat, lon, addrs, sales, counties in centroid_coords[:10]:
            coord = f"({lat:.6f}, {lon:.6f})"
            counties_str = ", ".join(counties[:3]) if counties else "None"
            if len(counties) > 3:
                counties_str += f" +{len(counties)-3}"
            print(f"  {coord:<30} {addrs:<12,} {sales:<10,} {counties_str}")

        if count > 10:
            print(f"  ... and {count - 10} more centroid coordinates")

        # Calculate total impact
        cur.execute("""
            WITH centroid_coords AS (
                SELECT latitude, longitude
                FROM properties
                WHERE latitude IS NOT NULL
                GROUP BY latitude, longitude
                HAVING COUNT(DISTINCT address) >= 100
            )
            SELECT
                COUNT(DISTINCT p.id) as affected_properties,
                COUNT(DISTINCT p.address) as affected_addresses
            FROM properties p
            INNER JOIN centroid_coords c
                ON ABS(p.latitude - c.latitude) < 0.000001
                AND ABS(p.longitude - c.longitude) < 0.000001
            WHERE p.latitude IS NOT NULL
        """)
        affected_props, affected_addrs = cur.fetchone()

        print(f"\n  Total impact:")
        print(f"    Affected properties: {affected_props:,}")
        print(f"    Affected addresses:  {affected_addrs:,}")

    assert count <= MAX_CENTROID_COORDS, (
        f"{count} centroid coordinates found (threshold: {MAX_CENTROID_COORDS}). "
        f"This indicates widespread geocoding fallback to county/town centroids. "
        f"Run: python3 scripts/identify_centroid_coordinates.py --export"
    )


def test_medium_priority_clusters(db):
    """
    Monitor medium-priority clustering issues (10-99 addresses per coordinate).
    These may be valid (e.g. apartment complexes) or geocoding artifacts.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT latitude, longitude, COUNT(DISTINCT address) as addrs
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) BETWEEN 10 AND 99
        ) sub
    """)
    count = cur.fetchone()[0]

    print(f"\n--- Medium-priority clusters (10-99 addresses) ---")
    print(f"  Coordinates with 10-99 distinct addresses: {count:,}")

    # This is informational - we expect some clustering (apartment buildings, etc)
    # but alert if it grows significantly
    if count > MAX_CENTROID_MEDIUM:
        print(f"  ⚠️  Exceeds monitoring threshold of {MAX_CENTROID_MEDIUM}")

    assert count <= MAX_CENTROID_MEDIUM, (
        f"{count} medium-priority clusters found (threshold: {MAX_CENTROID_MEDIUM}). "
        f"Review for potential geocoding issues."
    )


def test_regeocode_progress():
    """
    Track re-geocoding progress from regeocode_high_priority.py script.
    Ensures re-geocoding efforts are making progress and achieving good success rates.
    """
    import sqlite3
    import os

    progress_db = "regeocode_progress.db"

    if not os.path.exists(progress_db):
        print("\n--- Re-geocoding progress ---")
        print("  No re-geocoding runs yet (regeocode_progress.db not found)")
        print("  Run: python3 scripts/regeocode_high_priority.py --apply")
        return  # Skip test if no re-geocoding has been attempted

    print(f"\n--- Re-geocoding progress ---")

    conn = sqlite3.connect(progress_db)

    # Overall stats
    stats = conn.execute("""
        SELECT processed, succeeded, failed, skipped, started_at, last_update
        FROM session_stats WHERE id = 1
    """).fetchone()

    if stats and stats[0] > 0:  # processed > 0
        processed, succeeded, failed, skipped, started_at, last_update = stats
        success_rate = 100.0 * succeeded / processed if processed > 0 else 0

        print(f"  Started: {started_at}")
        print(f"  Last update: {last_update}")
        print(f"  Total processed: {processed:,}")
        print(f"  ✓ Succeeded: {succeeded:,} ({success_rate:.1f}%)")
        print(f"  ✗ Failed: {failed:,}")
        print(f"  ⊘ Skipped: {skipped:,}")

        # Method breakdown
        methods = conn.execute("""
            SELECT method, COUNT(*) as count
            FROM regeocode_log
            WHERE status = 'success'
            GROUP BY method
            ORDER BY count DESC
        """).fetchall()

        if methods:
            print(f"\n  Success by method:")
            for method, count in methods:
                print(f"    {method}: {count:,}")

        # Check success rate threshold
        assert success_rate >= MIN_REGEOCODE_SUCCESS_RATE, (
            f"Re-geocoding success rate {success_rate:.1f}% is below "
            f"threshold {MIN_REGEOCODE_SUCCESS_RATE}%. "
            f"Review failed geocoding attempts and adjust strategy."
        )
    else:
        print("  No properties processed yet")

    conn.close()


def test_known_problem_locations(db):
    """
    Test specific locations known to have had geocoding issues.
    Ensures fixes have been applied and are holding.
    """
    cur = db.cursor()

    print(f"\n--- Known problem locations ---")

    # Test 1: Nobber, Meath should be near (53.8217, -6.7479)
    # NOT at the wrong location (53.717143, -7.062706)
    cur.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE address ILIKE '%nobber%'
          AND latitude IS NOT NULL
          AND ABS(latitude - 53.717143) < 0.001
          AND ABS(longitude - (-7.062706)) < 0.001
    """)
    nobber_wrong = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE address ILIKE '%nobber%'
          AND latitude IS NOT NULL
    """)
    nobber_total = cur.fetchone()[0]

    print(f"  Nobber, Meath:")
    print(f"    Total properties: {nobber_total}")
    print(f"    At wrong coordinates: {nobber_wrong}")

    if nobber_wrong == 0:
        print(f"    ✓ All Nobber properties have correct coordinates")
    else:
        print(f"    ✗ {nobber_wrong} properties still at wrong location")

    assert nobber_wrong == 0, (
        f"{nobber_wrong} Nobber properties still at wrong coordinates. "
        f"Run: python3 scripts/fix_nobber_coordinates.py --apply"
    )


def test_geocoding_improvement_trend(db):
    """
    Track geocoding quality improvements over time.
    Compares current state to known baseline from 2025-05-18.
    """
    cur = db.cursor()

    print(f"\n--- Geocoding improvement trend ---")

    # Baseline from assessment on 2025-05-18
    BASELINE_CENTROID_COUNT = 50
    BASELINE_AFFECTED_PROPERTIES = 150000  # approximate

    # Current state
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= 100
        ) sub
    """)
    current_centroid_count = cur.fetchone()[0]

    # Count affected properties
    cur.execute("""
        WITH centroid_coords AS (
            SELECT latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY latitude, longitude
            HAVING COUNT(DISTINCT address) >= 100
        )
        SELECT COUNT(DISTINCT p.id)
        FROM properties p
        INNER JOIN centroid_coords c
            ON ABS(p.latitude - c.latitude) < 0.000001
            AND ABS(p.longitude - c.longitude) < 0.000001
        WHERE p.latitude IS NOT NULL
    """)
    current_affected = cur.fetchone()[0]

    print(f"  Baseline (2025-05-18):")
    print(f"    Centroid coordinates: {BASELINE_CENTROID_COUNT}")
    print(f"    Affected properties: ~{BASELINE_AFFECTED_PROPERTIES:,}")
    print(f"\n  Current:")
    print(f"    Centroid coordinates: {current_centroid_count}")
    print(f"    Affected properties: {current_affected:,}")

    if current_centroid_count < BASELINE_CENTROID_COUNT:
        improvement_coords = BASELINE_CENTROID_COUNT - current_centroid_count
        print(f"\n  ✓ Improvement: {improvement_coords} fewer centroid coordinates")
    elif current_centroid_count > BASELINE_CENTROID_COUNT:
        regression = current_centroid_count - BASELINE_CENTROID_COUNT
        print(f"\n  ✗ Regression: {regression} more centroid coordinates")
    else:
        print(f"\n  → No change in centroid count")

    if current_affected < BASELINE_AFFECTED_PROPERTIES:
        improvement = BASELINE_AFFECTED_PROPERTIES - current_affected
        pct = 100.0 * improvement / BASELINE_AFFECTED_PROPERTIES
        print(f"  ✓ Improvement: {improvement:,} fewer affected properties ({pct:.1f}%)")
    elif current_affected > BASELINE_AFFECTED_PROPERTIES:
        print(f"  ✗ Regression: More properties at centroid coordinates")

    # Informational only - don't fail on regression yet as we're still fixing things
    # In production, you might assert current_affected <= BASELINE_AFFECTED_PROPERTIES


# ---------------------------------------------------------------------------
# Eircode enrichment progress
# ---------------------------------------------------------------------------

def test_eircode_coverage(db):
    """Eircode coverage stays above floor; prints enrichment snapshot."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                                        AS total,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL)    AS with_eircode,
            COUNT(*) FILTER (WHERE eircode IS NULL)        AS without_eircode
        FROM properties
    """)
    total, with_ec, without_ec = cur.fetchone()
    pct = with_ec / total * 100 if total else 0

    print(f"\n--- Eircode coverage ---")
    print(f"  Total rows:      {total:>10,}")
    print(f"  With eircode:    {with_ec:>10,}  ({pct:.1f}%)")
    print(f"  Without eircode: {without_ec:>10,}  ({100-pct:.1f}%)")

    assert pct >= MIN_EIRCODE_PPR_PCT, (
        f"Eircode coverage {pct:.1f}% dropped below floor {MIN_EIRCODE_PPR_PCT}%"
    )


def test_eircode_coverage_by_county(db):
    """Prints eircode coverage broken down by county — informational only."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            county,
            COUNT(*)                                        AS total,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL)    AS with_eircode,
            ROUND(
                COUNT(*) FILTER (WHERE eircode IS NOT NULL)::numeric
                / NULLIF(COUNT(*), 0) * 100, 1
            )                                              AS pct
        FROM properties
        WHERE county IS NOT NULL
        GROUP BY county
        ORDER BY total DESC
        LIMIT 15
    """)
    rows = cur.fetchall()

    print(f"\n--- Eircode coverage by county (top 15 by volume) ---")
    print(f"  {'County':<20} {'Total':>8}  {'With EC':>8}  {'%':>6}")
    print(f"  {'-'*20}  {'-'*8}  {'-'*8}  {'-'*6}")
    for county, total, with_ec, pct in rows:
        print(f"  {(county or 'Unknown'):<20} {total:>8,}  {with_ec:>8,}  {pct or 0:>5.1f}%")


def test_eircode_enrichment_recency(db):
    """Shows eircode coverage for the most recent sales — these matter most for search."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            EXTRACT(YEAR FROM sale_date)::int             AS year,
            COUNT(*)                                      AS total,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL)   AS with_eircode,
            ROUND(
                COUNT(*) FILTER (WHERE eircode IS NOT NULL)::numeric
                / NULLIF(COUNT(*), 0) * 100, 1
            )                                             AS pct
        FROM properties
        WHERE sale_date >= '2018-01-01'
        GROUP BY year
        ORDER BY year DESC
    """)
    rows = cur.fetchall()

    print(f"\n--- Eircode coverage for recent sales (2018–present) ---")
    print(f"  {'Year':>6}  {'Total':>8}  {'With EC':>8}  {'%':>6}")
    print(f"  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*6}")
    for year, total, with_ec, pct in rows:
        print(f"  {year:>6}  {total:>8,}  {with_ec:>8,}  {pct or 0:>5.1f}%")


# ---------------------------------------------------------------------------
# Address ambiguity
# ---------------------------------------------------------------------------

def test_ambiguous_address_count(db):
    """Reports number of addresses that appear in multiple counties — ambiguous geocoding risk."""
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT address
            FROM properties
            WHERE latitude IS NOT NULL
            GROUP BY address
            HAVING COUNT(DISTINCT county) > 1
        ) sub
    """)
    ambiguous = cur.fetchone()[0]

    print(f"\n--- Address ambiguity ---")
    print(f"  Addresses appearing in multiple counties: {ambiguous:,}")

    # Not a hard failure — ambiguous addresses are expected (e.g. "Main Street")
    # but a sudden large increase could indicate a bad import


def test_ambiguous_address_examples(db):
    """Prints the top 10 most ambiguous addresses — useful for geocoder QA."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            address,
            COUNT(DISTINCT county)  AS county_count,
            COUNT(*)                AS sale_count,
            STRING_AGG(DISTINCT county, ', ' ORDER BY county) AS counties
        FROM properties
        WHERE latitude IS NOT NULL
          AND address IS NOT NULL
        GROUP BY address
        HAVING COUNT(DISTINCT county) > 1
        ORDER BY county_count DESC, sale_count DESC
        LIMIT 10
    """)
    rows = cur.fetchall()

    print(f"\n--- Top 10 most ambiguous addresses ---")
    print(f"  {'Address':<45}  {'Counties':>4}  {'Sales':>6}  In")
    print(f"  {'-'*45}  {'-'*4}  {'-'*6}  {'-'*30}")
    for address, county_count, sale_count, counties in rows:
        addr_display = (address[:42] + "...") if len(address) > 45 else address
        print(f"  {addr_display:<45}  {county_count:>4}  {sale_count:>6}  {counties}")


# ---------------------------------------------------------------------------
# Overall data quality summary
# ---------------------------------------------------------------------------

def test_data_quality_summary(db):
    """Prints a one-page data quality dashboard. Always passes."""
    cur = db.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                                                AS total,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL)           AS geocoded,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL)            AS with_eircode,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL
                               AND eircode IS NOT NULL)            AS geocoded_and_eircode,
            COUNT(*) FILTER (WHERE latitude IS NULL)               AS not_geocoded,
            COUNT(*) FILTER (WHERE eircode IS NULL)                AS no_eircode,
            COUNT(*) FILTER (WHERE latitude IS NULL
                               AND eircode IS NULL)                AS neither,
            MIN(sale_date)                                         AS earliest_sale,
            MAX(sale_date)                                         AS latest_sale
        FROM properties
    """)
    row = cur.fetchone()
    (total, geocoded, with_ec, both, not_geocoded,
     no_ec, neither, earliest, latest) = row

    print(f"\n{'='*55}")
    print(f"  DATA QUALITY DASHBOARD")
    print(f"{'='*55}")
    print(f"  Total rows:                  {total:>10,}")
    print(f"  Date range:                  {earliest} → {latest}")
    print(f"")
    print(f"  Geocoded (lat/lon):          {geocoded:>10,}  ({geocoded/total*100:.1f}%)")
    print(f"  Not geocoded:                {not_geocoded:>10,}  ({not_geocoded/total*100:.1f}%)")
    print(f"")
    print(f"  With eircode:                {with_ec:>10,}  ({with_ec/total*100:.1f}%)")
    print(f"  Without eircode:             {no_ec:>10,}  ({no_ec/total*100:.1f}%)")
    print(f"")
    print(f"  Geocoded + eircode:          {both:>10,}  ({both/total*100:.1f}%)")
    print(f"  Neither geocoded nor eircode:{neither:>10,}  ({neither/total*100:.1f}%)")
    print(f"{'='*55}")
