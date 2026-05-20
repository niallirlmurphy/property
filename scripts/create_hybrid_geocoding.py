#!/usr/bin/env python3
"""
Create hybrid geocoding dataset by choosing the best coordinates from multiple sources.

For each address:
1. Score Nominatim/Mapbox coordinates
2. Score Salesforce coordinates
3. Choose the better one, or NULL if both are bad

Quality checks:
- Out of bounds (Ireland bbox)
- County validation
- Centroid detection
- Coordinate precision

Better to have no data than bad data.
"""

import asyncio
import asyncpg
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, '/Users/nmurphy/claude/property price project/scripts')
from county_validator import validate_county

# File paths
SALESFORCE_CSV = "Salesforce-geocoded-irish-properties.csv"
DATABASE_URL = os.environ.get("DATABASE_URL")

# Quality thresholds
IRELAND_BBOX = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon
CENTROID_THRESHOLD = 50  # Number of addresses at same coordinate to flag as centroid


class CoordinateQualityScorer:
    """Score coordinate quality based on multiple factors."""

    def __init__(self):
        self.centroid_coords = None

    def set_centroid_data(self, coord_counts):
        """Set known centroid coordinates."""
        self.centroid_coords = {
            coord for coord, count in coord_counts.items()
            if count >= CENTROID_THRESHOLD
        }

    def score_coordinates(self, lat, lon, county, source="unknown"):
        """
        Score coordinates from 0-100.
        100 = excellent, 0 = unusable

        Returns: (score, issues_list)
        """
        if not lat or not lon:
            return 0, ["Missing coordinates"]

        score = 100
        issues = []

        # 1. Check Ireland bounds (critical - auto fail)
        min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            return 0, ["Out of bounds"]

        # 2. Check if it's a known centroid (severe penalty)
        coord_key = (round(lat, 6), round(lon, 6))
        if self.centroid_coords and coord_key in self.centroid_coords:
            score -= 80
            issues.append("Known centroid coordinate")

        # 3. County validation (major penalty)
        if county:
            is_valid, reason = validate_county(lat, lon, county)
            if not is_valid:
                score -= 50
                issues.append(f"County mismatch: {reason}")

        # 4. Check precision (minor factor)
        lat_decimals = len(str(lat).split('.')[-1]) if '.' in str(lat) else 0
        lon_decimals = len(str(lon).split('.')[-1]) if '.' in str(lon) else 0

        # Prefer more precision (more specific geocoding)
        if lat_decimals >= 6 and lon_decimals >= 6:
            score += 5
            issues.append("High precision (good)")
        elif lat_decimals <= 3 or lon_decimals <= 3:
            score -= 10
            issues.append("Low precision")

        # Ensure score stays in bounds
        score = max(0, min(100, score))

        return score, issues


async def load_database_coordinates(pool):
    """Load existing coordinates from database."""
    print("Loading coordinates from database...")

    query = """
        SELECT id, address, county, eircode, latitude, longitude
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY id
    """

    rows = await pool.fetch(query)

    db_data = {}
    coord_counts = defaultdict(int)

    for row in rows:
        # Normalize address for matching
        address_key = row['address'].strip().upper()

        db_data[address_key] = {
            'id': row['id'],
            'address': row['address'],
            'county': row['county'],
            'eircode': row['eircode'],
            'lat': float(row['latitude']) if row['latitude'] else None,
            'lon': float(row['longitude']) if row['longitude'] else None,
            'source': 'database'
        }

        # Count coordinate frequency for centroid detection
        if row['latitude'] and row['longitude']:
            coord_key = (round(float(row['latitude']), 6), round(float(row['longitude']), 6))
            coord_counts[coord_key] += 1

    print(f"✓ Loaded {len(db_data):,} records from database")
    return db_data, coord_counts


def load_salesforce_coordinates():
    """Load Salesforce geocoded coordinates."""
    print(f"Loading coordinates from {SALESFORCE_CSV}...")

    sf_data = {}
    coord_counts = defaultdict(int)

    with open(SALESFORCE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Normalize address for matching
            address_key = row['Name'].strip().upper()

            lat = float(row['BillingLatitude']) if row['BillingLatitude'] else None
            lon = float(row['BillingLongitude']) if row['BillingLongitude'] else None

            sf_data[address_key] = {
                'address': row['Name'],
                'county': row['BillingCity'],
                'lat': lat,
                'lon': lon,
                'source': 'salesforce'
            }

            # Count coordinate frequency
            if lat and lon:
                coord_key = (round(lat, 6), round(lon, 6))
                coord_counts[coord_key] += 1

    print(f"✓ Loaded {len(sf_data):,} records from Salesforce")
    return sf_data, coord_counts


def choose_best_coordinates(db_record, sf_record, scorer):
    """
    Choose the best coordinates between database and Salesforce.

    Returns: dict with chosen coordinates and decision info
    """
    county = db_record.get('county') or sf_record.get('county')

    # Score database coordinates
    db_lat = db_record.get('lat')
    db_lon = db_record.get('lon')
    db_score, db_issues = scorer.score_coordinates(db_lat, db_lon, county, "database")

    # Score Salesforce coordinates
    sf_lat = sf_record.get('lat')
    sf_lon = sf_record.get('lon')
    sf_score, sf_issues = scorer.score_coordinates(sf_lat, sf_lon, county, "salesforce")

    # Decision logic
    decision = {
        'property_id': db_record['id'],
        'address': db_record['address'],
        'county': county,
        'db_lat': db_lat,
        'db_lon': db_lon,
        'db_score': db_score,
        'db_issues': db_issues,
        'sf_lat': sf_lat,
        'sf_lon': sf_lon,
        'sf_score': sf_score,
        'sf_issues': sf_issues,
        'chosen_lat': None,
        'chosen_lon': None,
        'chosen_source': None,
        'reason': None
    }

    # Minimum acceptable score
    MIN_SCORE = 20

    if db_score < MIN_SCORE and sf_score < MIN_SCORE:
        # Both are bad - use neither
        decision['chosen_source'] = 'NONE'
        decision['reason'] = f"Both sources have low quality (DB: {db_score}, SF: {sf_score})"
    elif db_score >= MIN_SCORE and sf_score < MIN_SCORE:
        # Only database is acceptable
        decision['chosen_lat'] = db_lat
        decision['chosen_lon'] = db_lon
        decision['chosen_source'] = 'database'
        decision['reason'] = f"Database better (score: {db_score} vs {sf_score})"
    elif sf_score >= MIN_SCORE and db_score < MIN_SCORE:
        # Only Salesforce is acceptable
        decision['chosen_lat'] = sf_lat
        decision['chosen_lon'] = sf_lon
        decision['chosen_source'] = 'salesforce'
        decision['reason'] = f"Salesforce better (score: {sf_score} vs {db_score})"
    else:
        # Both acceptable - choose higher score
        if sf_score > db_score + 10:  # SF significantly better
            decision['chosen_lat'] = sf_lat
            decision['chosen_lon'] = sf_lon
            decision['chosen_source'] = 'salesforce'
            decision['reason'] = f"Salesforce higher quality (score: {sf_score} vs {db_score})"
        elif db_score > sf_score + 10:  # DB significantly better
            decision['chosen_lat'] = db_lat
            decision['chosen_lon'] = db_lon
            decision['chosen_source'] = 'database'
            decision['reason'] = f"Database higher quality (score: {db_score} vs {sf_score})"
        else:
            # Scores similar - prefer Salesforce (newer data)
            decision['chosen_lat'] = sf_lat
            decision['chosen_lon'] = sf_lon
            decision['chosen_source'] = 'salesforce'
            decision['reason'] = f"Salesforce preferred (similar scores: {sf_score} vs {db_score})"

    return decision


async def create_hybrid_dataset(pool):
    """Create hybrid dataset choosing best coordinates from each source."""

    print("\n" + "="*70)
    print("CREATING HYBRID GEOCODING DATASET")
    print("="*70)
    print()

    # Load data from both sources
    db_data, db_coord_counts = await load_database_coordinates(pool)
    sf_data, sf_coord_counts = load_salesforce_coordinates()

    # Combine coordinate counts for centroid detection
    all_coord_counts = defaultdict(int)
    for coord, count in db_coord_counts.items():
        all_coord_counts[coord] += count
    for coord, count in sf_coord_counts.items():
        all_coord_counts[coord] += count

    # Initialize scorer with centroid data
    scorer = CoordinateQualityScorer()
    scorer.set_centroid_data(all_coord_counts)

    print(f"\nDetected {len([c for c, cnt in all_coord_counts.items() if cnt >= CENTROID_THRESHOLD])} centroid coordinates")
    print()

    # Process each address
    print("Comparing coordinates for each address...")
    decisions = []

    stats = {
        'total': 0,
        'database_chosen': 0,
        'salesforce_chosen': 0,
        'none_chosen': 0,
        'database_only': 0,
        'salesforce_only': 0,
        'both_available': 0
    }

    for address_key, db_record in db_data.items():
        stats['total'] += 1

        if address_key in sf_data:
            # Have both sources
            sf_record = sf_data[address_key]
            stats['both_available'] += 1

            decision = choose_best_coordinates(db_record, sf_record, scorer)
            decisions.append(decision)

            if decision['chosen_source'] == 'database':
                stats['database_chosen'] += 1
            elif decision['chosen_source'] == 'salesforce':
                stats['salesforce_chosen'] += 1
            else:
                stats['none_chosen'] += 1
        else:
            # Only have database
            stats['database_only'] += 1

            # Still score it
            db_score, db_issues = scorer.score_coordinates(
                db_record['lat'], db_record['lon'],
                db_record['county'], "database"
            )

            decision = {
                'property_id': db_record['id'],
                'address': db_record['address'],
                'county': db_record['county'],
                'db_lat': db_record['lat'],
                'db_lon': db_record['lon'],
                'db_score': db_score,
                'db_issues': db_issues,
                'sf_lat': None,
                'sf_lon': None,
                'sf_score': 0,
                'sf_issues': ['Not in Salesforce'],
                'chosen_lat': db_record['lat'] if db_score >= 20 else None,
                'chosen_lon': db_record['lon'] if db_score >= 20 else None,
                'chosen_source': 'database' if db_score >= 20 else 'NONE',
                'reason': f"Database only (score: {db_score})"
            }
            decisions.append(decision)

            if decision['chosen_source'] == 'database':
                stats['database_chosen'] += 1
            else:
                stats['none_chosen'] += 1

        if stats['total'] % 50000 == 0:
            print(f"  Processed {stats['total']:,} addresses...")

    print(f"✓ Processed {stats['total']:,} addresses")
    print()

    # Show statistics
    print("="*70)
    print("DECISION STATISTICS")
    print("="*70)
    print(f"Total addresses: {stats['total']:,}")
    print(f"  Both sources available: {stats['both_available']:,}")
    print(f"  Database only: {stats['database_only']:,}")
    print()
    print("Chosen coordinates:")
    print(f"  Database: {stats['database_chosen']:,} ({100*stats['database_chosen']/stats['total']:.1f}%)")
    print(f"  Salesforce: {stats['salesforce_chosen']:,} ({100*stats['salesforce_chosen']/stats['total']:.1f}%)")
    print(f"  None (rejected both): {stats['none_chosen']:,} ({100*stats['none_chosen']/stats['total']:.1f}%)")
    print()

    return decisions, stats


async def update_database(pool, decisions, dry_run=True):
    """Update database with hybrid coordinates."""

    print("="*70)
    print("UPDATING DATABASE")
    print("="*70)
    print()

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print()

    # Group decisions by action needed
    to_update = [d for d in decisions if d['chosen_source'] in ['database', 'salesforce']
                 and (d['chosen_lat'] != d['db_lat'] or d['chosen_lon'] != d['db_lon'])]
    to_nullify = [d for d in decisions if d['chosen_source'] == 'NONE' and (d['db_lat'] or d['db_lon'])]
    no_change = [d for d in decisions if d['chosen_source'] == 'database'
                 and d['chosen_lat'] == d['db_lat'] and d['chosen_lon'] == d['db_lon']]

    print(f"Actions required:")
    print(f"  Update coordinates: {len(to_update):,}")
    print(f"  Set to NULL (bad data): {len(to_nullify):,}")
    print(f"  No change needed: {len(no_change):,}")
    print()

    if dry_run:
        # Show sample of what would change
        print("Sample updates (first 10):")
        for decision in to_update[:10]:
            print(f"\n  {decision['address'][:60]}")
            print(f"    Old: ({decision['db_lat']}, {decision['db_lon']})")
            print(f"    New: ({decision['chosen_lat']}, {decision['chosen_lon']})")
            print(f"    Source: {decision['chosen_source']}")
            print(f"    Reason: {decision['reason']}")

        if to_nullify:
            print(f"\nSample rejections (first 5):")
            for decision in to_nullify[:5]:
                print(f"\n  {decision['address'][:60]}")
                print(f"    Current: ({decision['db_lat']}, {decision['db_lon']})")
                print(f"    Action: SET TO NULL")
                print(f"    Reason: {decision['reason']}")
                print(f"    DB issues: {', '.join(decision['db_issues'])}")
                print(f"    SF issues: {', '.join(decision['sf_issues'])}")

        return

    # Actually update database using BATCH updates for speed
    print("Applying updates...")

    updated_count = 0
    nullified_count = 0

    async with pool.acquire() as conn:
        # Method: Use executemany for batched updates (reliable and fast)

        if to_update:
            print(f"  Updating {len(to_update):,} coordinates in batches...")

            # Process in chunks to avoid timeout
            CHUNK_SIZE = 5000
            total_updated = 0

            for i in range(0, len(to_update), CHUNK_SIZE):
                chunk = to_update[i:i+CHUNK_SIZE]

                async with conn.transaction():
                    # Use executemany for batch efficiency
                    await conn.executemany("""
                        UPDATE properties
                        SET latitude = $1, longitude = $2,
                            geog = ST_MakePoint($2, $1)::geography
                        WHERE id = $3
                    """, [(d['chosen_lat'], d['chosen_lon'], d['property_id']) for d in chunk])

                total_updated += len(chunk)

                if total_updated % 50000 == 0 or total_updated == len(to_update):
                    print(f"    Updated {total_updated:,} / {len(to_update):,} coordinates...")

            updated_count = total_updated
            print(f"  ✓ Updated {updated_count:,} coordinates")

            # Nullify bad coordinates in batches
            if to_nullify:
                print(f"  Nullifying {len(to_nullify):,} bad coordinates...")

                # Batch nullify using IN clause (chunk into groups of 1000)
                BATCH_SIZE = 1000
                for i in range(0, len(to_nullify), BATCH_SIZE):
                    batch = to_nullify[i:i+BATCH_SIZE]
                    ids = [d['property_id'] for d in batch]

                    await conn.execute("""
                        UPDATE properties
                        SET latitude = NULL, longitude = NULL, geog = NULL
                        WHERE id = ANY($1::int[])
                    """, ids)

                    nullified_count += len(batch)

                    if nullified_count % 5000 == 0:
                        print(f"    Nullified {nullified_count:,} / {len(to_nullify):,}...")

    print(f"\n✓ Database updated!")
    print(f"  Coordinates updated: {updated_count:,}")
    print(f"  Set to NULL: {nullified_count:,}")


async def main():
    dry_run = "--apply" not in sys.argv

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     HYBRID GEOCODING DATASET CREATOR                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Strategy: Choose the best coordinates from multiple sources")
    print("  - Score each coordinate set for quality")
    print("  - Reject coordinates with low quality scores")
    print("  - Better to have no data than bad data")
    print()

    if not DATABASE_URL:
        print("✗ DATABASE_URL not set")
        sys.exit(1)

    # Create database pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

    try:
        # Create hybrid dataset
        decisions, stats = await create_hybrid_dataset(pool)

        # Update database
        await update_database(pool, decisions, dry_run=dry_run)

        if dry_run:
            print()
            print("="*70)
            print("To apply changes, run with --apply flag:")
            print("  python3 scripts/create_hybrid_geocoding.py --apply")

    finally:
        await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
