"""
Database health checks.

Tests the failure modes we have seen in production:
  - geog column not populated (caused no results from radius search)
  - geom/geog mismatch after re-import
  - Suspiciously low row counts after import
  - Coordinates outside Ireland bounding box
"""

import pytest

IRELAND_LAT = (51.4, 55.4)
IRELAND_LON = (-10.5, -5.5)
MIN_EXPECTED_ROWS = 750_000   # total PPR rows — update if dataset grows significantly
MIN_GEOCODED_ROWS = 600_000   # geocoded rows should not drop below this


def test_properties_row_count(db):
    """Total row count is in the expected range."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM properties")
    count = cur.fetchone()[0]
    assert count >= MIN_EXPECTED_ROWS, (
        f"Only {count:,} rows in properties — expected ≥{MIN_EXPECTED_ROWS:,}. "
        "Was there a failed import?"
    )


def test_geog_matches_geom_count(db):
    """Every row with a latitude should have geog populated.

    This was the root cause of the 'no results' bug — import.py was
    writing lat/lon but not geog, so ST_DWithin returned nothing.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE latitude IS NOT NULL)        AS with_lat,
            COUNT(*) FILTER (WHERE geog IS NOT NULL)            AS with_geog
        FROM properties
    """)
    row = cur.fetchone()
    with_lat, with_geog = row
    assert with_lat == with_geog, (
        f"{with_lat:,} rows have latitude but only {with_geog:,} have geog. "
        f"Run: UPDATE properties SET geog = ST_MakePoint(longitude, latitude)::geography "
        f"WHERE latitude IS NOT NULL AND geog IS NULL"
    )


def test_geocoded_row_count(db):
    """Enough rows are geocoded to make radius search useful."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM properties WHERE geog IS NOT NULL")
    count = cur.fetchone()[0]
    assert count >= MIN_GEOCODED_ROWS, (
        f"Only {count:,} geocoded rows — expected ≥{MIN_GEOCODED_ROWS:,}"
    )


def test_coordinates_within_ireland(db):
    """No geocoded rows have coordinates outside Ireland's bounding box.

    Out-of-bounds coordinates (e.g. Northern Ireland, mainland UK) produce
    searches that appear to succeed but return results in the wrong country.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM properties
        WHERE latitude  IS NOT NULL
          AND (latitude  < %s OR latitude  > %s
            OR longitude < %s OR longitude > %s)
    """, (IRELAND_LAT[0], IRELAND_LAT[1], IRELAND_LON[0], IRELAND_LON[1]))
    out_of_bounds = cur.fetchone()[0]
    assert out_of_bounds == 0, (
        f"{out_of_bounds} rows have coordinates outside Ireland bounding box "
        f"lat={IRELAND_LAT} lon={IRELAND_LON}"
    )


def test_no_future_sale_dates(db):
    """No sale dates in the future — likely a data parsing bug."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM properties WHERE sale_date > CURRENT_DATE")
    count = cur.fetchone()[0]
    assert count == 0, f"{count} rows have sale dates in the future"


def test_no_zero_or_negative_prices(db):
    """All prices are positive."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM properties WHERE price <= 0")
    count = cur.fetchone()[0]
    assert count == 0, f"{count} rows have zero or negative prices"


def test_submissions_table_exists(db):
    """submissions table was created (contact/feedback forms depend on it)."""
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'submissions'
    """)
    assert cur.fetchone()[0] == 1, "submissions table does not exist"


def test_spatial_index_exists(db):
    """GiST index on geog exists — without it radius search is a full table scan."""
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM pg_indexes
        WHERE tablename = 'properties' AND indexname = 'properties_geog_idx'
    """)
    assert cur.fetchone()[0] == 1, "properties_geog_idx is missing — radius search will be very slow"
