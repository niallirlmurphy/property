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
