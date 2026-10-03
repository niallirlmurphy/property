#!/usr/bin/env python3
"""
Batch geocode properties using Mapbox Geocoding API with canonical cache.

Mapbox provides high-quality global geocoding with batch API support.
Best used for properties WITHOUT Eircodes (Autoaddress is better for Eircode properties).

API: https://docs.mapbox.com/api/search/geocoding/
- Batch API: Up to 1,000 queries per request
- Free tier: 100,000 requests/month
- Pricing: $0.75 per 1,000 after free tier

Validation:
- Ireland bounds check (51.4-55.5°N, -10.7--5.4°W)
- County boundary validation
- Coordinate precision check (accept only rooftop, parcel, point)
- Reject interpolated and approximate results

Usage:
    # Geocode high-priority properties (>€400k, recent sales first)
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --min-price 400000 --apply

    # Geocode properties WITHOUT Eircodes
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --no-eircode --apply

    # Re-geocode centroid coordinates (70k properties with generic coords)
    python3 scripts/geocode_mapbox_batch.py --centroid --limit 100 --apply

    # Test with small batch
    python3 scripts/geocode_mapbox_batch.py --needs-geocoding --limit 10

Flags:
    --needs-geocoding    Process properties with needs_geocoding=TRUE flag
    --centroid           Process properties at centroid coordinates (100+ addresses at same point)
    --no-eircode         Filter to properties WITHOUT Eircodes
    --min-price N        Filter to properties with price >= N
    --apply              Actually update database (default is dry-run)
    --limit N            Process at most N properties
    --county COUNTY      Filter to specific county
"""

import asyncio
import asyncpg
import httpx
import os
import sys
import difflib
import html
import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from county_validator import validate_county, normalize_county, COUNTY_BOUNDS
from canonical_geocoding import (
    initialize_cache,
    get_canonical_coordinates,
    cache_coordinates
)
from duplicate_handler import update_geocoding_for_duplicates
from mapbox_client import MapboxClient
from extract_base_address import is_bulk_sale, extract_base_address

load_dotenv("backend/.env")

DATABASE_URL = os.environ["DATABASE_URL"]
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")

# API endpoint
MAPBOX_BATCH_URL = "https://api.mapbox.com/search/geocode/v6/batch"

# Ireland bounding box
IRELAND_BBOX = (51.4, 55.5, -10.7, -5.4)  # min_lat, max_lat, min_lon, max_lon

# Acceptable precision levels (reject interpolated/approximate)
ACCEPTABLE_PRECISION = {'rooftop', 'parcel', 'point'}

# Persist geocode results to the database every this many properties, so an
# interruption loses at most one chunk instead of the whole run.
CHUNK_SIZE = 1000


async def fetch_properties_needing_geocoding(pool: asyncpg.Pool, limit: int = None,
                                             county: str = None, no_eircode: bool = False,
                                             min_price: int = None, suspect: bool = False,
                                             eircode_only: bool = False,
                                             since: str = None,
                                             before: str = None) -> List[Dict]:
    """Fetch properties flagged as needing geocoding (priority order)."""
    print("Fetching properties needing geocoding...")

    where_clauses = ["needs_geocoding = TRUE"]
    params = []
    idx = 1

    if county:
        where_clauses.append(f"LOWER(county) = LOWER(${idx})")
        params.append(county)
        idx += 1

    if no_eircode:
        where_clauses.append("(eircode IS NULL OR eircode = '')")

    if eircode_only:
        # Only rows with an eircode — these carry a routing key we can use as a
        # proximity bias, so they benefit most from the proximity-steered geocode.
        where_clauses.append("eircode IS NOT NULL AND eircode <> ''")

    if suspect:
        # Only rows currently flagged as bad geocodes (hidden from search). These
        # are the mislocated/wrong-town rows users actually see leaking into area
        # pages, so they are the highest-impact target for a budget-limited run.
        # Combined with needs_geocoding = TRUE (always required), this naturally
        # EXCLUDES rows we already attempted: a failed geocode now sets
        # needs_geocoding = FALSE (see the write phase below), so an address is
        # never re-fetched or re-billed on a later sub-batch/run. To deliberately
        # retry a failed row, re-flag it (needs_geocoding = TRUE) first.
        where_clauses.append("geocode_suspect = TRUE")
    else:
        # Exclude rows a prior run already tried and failed (geocode_suspect = TRUE).
        # Failed rows stay needs_geocoding = TRUE but are marked suspect on failure,
        # so this keeps the worklist to genuinely un-attempted rows and stops the
        # same failing addresses being re-geocoded (and re-billed) every run.
        where_clauses.append("geocode_suspect = FALSE")

    if min_price:
        where_clauses.append(f"price >= ${idx}")
        params.append(min_price)
        idx += 1

    if since:
        # Scope to sales on/after this date — used to geocode only a fresh import
        # window rather than the whole needs_geocoding backlog.
        where_clauses.append(f"sale_date >= ${idx}")
        params.append(datetime.strptime(since, "%Y-%m-%d").date())
        idx += 1

    if before:
        # Scope to sales strictly before this date — used to work the needs_geocoding
        # backlog while a separate run handles the fresh import window (>= that date),
        # so the two runs target disjoint rows.
        where_clauses.append(f"sale_date < ${idx}")
        params.append(datetime.strptime(before, "%Y-%m-%d").date())
        idx += 1

    where = " AND ".join(where_clauses)
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT id, address, address_normalized, county, price, sale_date,
               eircode, routing_key
        FROM properties
        WHERE {where}
        ORDER BY
            -- Budget-limited sweeps must maximise fixes-per-credit, so geocode the
            -- rows Mapbox can actually resolve FIRST. Addresses that start with a
            -- house number are street-level (e.g. "17 Dun Aengus") and geocode
            -- reliably; rural named houses / townlands ("Sea Breeze, Shrule") have no
            -- resolvable street and are near-uniformly rejected by validation, so
            -- they sink to the end where a capped run simply won't reach them.
            (address ~ '^[0-9]') DESC,
            -- Then eircode-holders (steerable via routing-key proximity + validatable).
            (eircode IS NOT NULL AND eircode <> '') DESC,
            price DESC,
            sale_date DESC
        {limit_clause}
    """

    rows = await pool.fetch(query, *params)
    return [dict(row) for row in rows]


async def fetch_centroid_properties(pool: asyncpg.Pool, limit: int = None,
                                    county: str = None) -> List[Dict]:
    """Fetch un-attempted properties at centroid coordinates (100+ addresses at same point).

    Ordered numbered-street-addresses first: rural named houses / townlands at a
    town centroid almost always come back from Mapbox as that same town centre, so
    a budget-limited run should reach the resolvable rows first.
    """
    print("Identifying centroid coordinates...")
    params = []
    county_clause = ""
    if county:
        county_clause = "AND LOWER(p.county) = LOWER($1)"
        params.append(county)
    limit_clause = f"LIMIT {int(limit)}" if limit else ""

    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '600s'")
        rows = await conn.fetch(f"""
            WITH centroids AS (
                SELECT latitude, longitude
                FROM properties
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                GROUP BY latitude, longitude
                HAVING COUNT(DISTINCT address) >= 100
            )
            SELECT p.id, p.address, p.address_normalized, p.county, p.eircode, p.routing_key,
                   p.latitude, p.longitude, p.price, p.sale_date
            FROM properties p
            JOIN centroids c ON ABS(p.latitude - c.latitude) < 0.000001
                            AND ABS(p.longitude - c.longitude) < 0.000001
            -- Skip rows already attempted: failures keep their centroid coords, so
            -- without this every sub-batch would re-select (and re-bill) them.
            WHERE p.geocode_attempts = 0 {county_clause}
            ORDER BY
                (p.address ~ '^[0-9]') DESC,
                (p.eircode IS NOT NULL AND p.eircode <> '') DESC,
                p.sale_date DESC
            {limit_clause}
        """, *params)
    print(f"Found {len(rows):,} centroid properties to process")
    return [dict(r) for r in rows]

    return properties


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Hard-reject a geocode whose eircode routing key sits this far from the coordinate.
# A routing key is an AREA, not a point: rural keys sprawl (a legitimate address can
# sit ~20km from its key's centroid — e.g. Nobber is 19km from the A82/Kells centroid
# at its CORRECT coordinates). A tight 10km threshold therefore rejects legitimate
# rural matches. 40km only fires on confident cross-region errors. The precise
# wrong-town signal is the county-box check below.
ROUTING_KEY_MAX_KM = 40.0

# Adaptive per-key threshold (same formula as scripts/flag_bad_geocodes.py):
# clamp(p75 of the key's member distances * RK_MULT, RK_FLOOR_KM, RK_CEIL_KM).
# A flat 40km let compact urban keys accept wrong-district matches (D04 → Baldoyle
# is only ~10km); used in place of ROUTING_KEY_MAX_KM when a key's extent is known.
RK_MULT = 2.0
RK_FLOOR_KM = 8.0
RK_CEIL_KM = 45.0

# Dublin postal district ("Dublin 4", "DUBLIN 6W"). Mapbox parses this as house
# number + street, e.g. "..., Dublin 4" → "4 Dublin Street, Baldoyle" (rooftop!).
DUBLIN_DISTRICT_RE = re.compile(r'\bDUBLIN\s+\d{1,2}[A-Z]?\b', re.IGNORECASE)

# Generic street-type words ignored when checking a match's street name against
# the input address (only the distinctive part, e.g. "SHELBOURNE", must match).
STREET_GENERIC_WORDS = {
    'STREET', 'ST', 'ROAD', 'RD', 'AVENUE', 'AVE', 'DRIVE', 'DR', 'LANE', 'PARK',
    'CLOSE', 'COURT', 'CRESCENT', 'GROVE', 'PLACE', 'SQUARE', 'TERRACE', 'WAY',
    'VIEW', 'HILL', 'UPPER', 'LOWER', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'THE',
    'GREEN', 'GARDENS', 'WALK', 'ROW', 'QUAY', 'MEWS', 'LAWN', 'LAWNS', 'RISE',
    'HEIGHTS', 'VALE', 'WOOD', 'WOODS', 'MANOR', 'DOWNS', 'GLEN', 'OF', 'AND',
    'APARTMENTS', 'APTS', 'APT',
}


def strip_dublin_district(address: str) -> str:
    """Remove the 'Dublin N' postal district from an address for querying."""
    cleaned = DUBLIN_DISTRICT_RE.sub('', address)
    cleaned = re.sub(r'\s*,\s*(,\s*)+', ', ', cleaned)   # collapse empty components
    return re.sub(r'\s+', ' ', cleaned).strip(' ,')


def street_matches(full_address: Optional[str], input_address: str) -> bool:
    """True if the matched street's distinctive words all appear in the input.

    Catches Mapbox matching a different street entirely (e.g. "4 Dublin Street,
    Baldoyle" for "... South Lotts Road, Dublin 4"). Compares against the input
    with the Dublin district already stripped, so "DUBLIN" can't match itself.
    """
    if not full_address:
        return True  # nothing to compare -> don't reject on this check
    street = full_address.split(',')[0].upper()
    tokens = [t for t in re.findall(r'[A-Z]+', street)
              if t not in STREET_GENERIC_WORDS and len(t) > 1]
    if not tokens:
        return True
    inp = input_address.upper()
    words = set(re.findall(r'[A-Z]+', inp))
    # Normalisation expands "St" to "Street", so "Mount St Annes" is stored as
    # "Mount Street Annes" — let a matched "Saint" accept either form.
    if words & {'ST', 'STREET'}:
        words.add('SAINT')
    compact = re.sub(r'[^A-Z0-9]', '', inp)   # "MC AULEY" vs "MCAULEY"

    def found(t: str) -> bool:
        if t in words or t in compact:
            return True
        # Tolerate small spelling variants (Anglesa/Anglesea, Charlemount/
        # Charlemont) but not different names (Hook/Cook, Burton/Barton,
        # Kilross/Kinross): short words must match exactly, longer ones >= 0.9.
        return len(t) >= 6 and any(
            difflib.SequenceMatcher(None, t, w).ratio() >= 0.9 for w in words)

    return all(found(t) for t in tokens)

# County bounding boxes are tight; pad them by this margin before treating "outside
# the box" as a wrong-county rejection, so genuine edge-of-county towns (e.g. Fingal
# reaches ~53.63N, above County Dublin's 53.50 box) are not rejected.
COUNTY_MARGIN_DEG = 0.2


def _outside_county_box(lat: float, lon: float, county: str) -> bool:
    """True if (lat, lon) is outside the stored county's margin-padded box.

    Conservative, low-false-positive wrong-county signal: a Kerry-county address that
    Mapbox matched to a Dublin street is wrong regardless of precision/distance.
    """
    norm = normalize_county(county) if county else ""
    bounds = COUNTY_BOUNDS.get(norm)
    if not bounds:
        return False  # unknown county -> cannot judge
    min_lat, max_lat, min_lon, max_lon = bounds
    m = COUNTY_MARGIN_DEG
    return not (min_lat - m <= lat <= max_lat + m and min_lon - m <= lon <= max_lon + m)


def validate_coordinates(lat: float, lon: float, county: str, feature_type: str,
                         precision: Optional[str], routing_key: Optional[str] = None,
                         rk_centroids: Optional[dict] = None,
                         rk_thresholds: Optional[dict] = None) -> Tuple[bool, str, int]:
    """
    Validate Mapbox coordinates.

    Returns: (is_valid, reason, quality_score)
    - quality_score: 100=rooftop, 90=parcel, 80=point, 75=address/street, 70=locality
    """

    # Validation 1: Ireland bounds (CRITICAL)
    min_lat, max_lat, min_lon, max_lon = IRELAND_BBOX
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return False, f"out_of_bounds({lat:.2f},{lon:.2f})", 0

    # Validation 1b: Routing-key distance (CRITICAL, hard reject).
    # The eircode's routing key is an independent ground truth for location.
    # If the geocoded point is far from that key's centroid, the geocoder matched
    # the wrong place (e.g. a generic street name in the wrong town) -> reject.
    if routing_key and rk_centroids:
        centroid = rk_centroids.get(routing_key)
        if centroid:
            dist_km = _haversine_km(lat, lon, centroid[0], centroid[1])
            max_km = (rk_thresholds or {}).get(routing_key, ROUTING_KEY_MAX_KM)
            if dist_km > max_km:
                return False, f"routing_key_far({routing_key}:{dist_km:.0f}km)", 0

    # Validation 1c: Wrong county (CRITICAL, hard reject).
    # If the coordinate lands outside the stored county's (padded) box, Mapbox matched
    # a same-named street/place in a different county -> reject.
    if county and _outside_county_box(lat, lon, county):
        return False, f"wrong_county({county})", 0

    # Validation 2: Feature type and precision level
    # v6 API returns feature_type (address, postcode, street, place, locality) and a
    # separate coordinate accuracy in `precision` (rooftop, parcel, point, interpolated, …).
    quality_score = 70  # Default

    if feature_type == 'address':
        # Address-level results - good quality. Reward exact accuracy tiers.
        if precision in ACCEPTABLE_PRECISION:
            quality_map = {
                'rooftop': 100,
                'parcel': 90,
                'point': 80
            }
            quality_score = quality_map.get(precision, 80)
        else:
            # interpolated/approximate/unknown accuracy - still an address match,
            # treat as baseline address quality.
            quality_score = 80

    elif feature_type == 'postcode':
        # Postcode/Eircode - good quality for Irish addresses
        quality_score = 85

    elif feature_type == 'poi':
        # Point of interest - acceptable
        quality_score = 75

    elif feature_type in ('locality', 'place'):
        # Rural areas without street addresses - acceptable but lower quality
        quality_score = 70

    elif feature_type == 'street':
        # Street-level results - acceptable
        quality_score = 75

    else:
        # Other feature types - may be too imprecise
        return False, f"feature_type_{feature_type}", 0

    # Validation 3: County boundary (optional, downgrades quality but doesn't reject)
    if county:
        is_valid, reason = validate_county(lat, lon, county)
        if not is_valid:
            quality_score = min(quality_score, 70)  # Downgrade for county mismatch

    return True, "validated", quality_score


async def _close_pool(pool: asyncpg.Pool, timeout_s: float = 30.0) -> None:
    """Close a pool without hanging: graceful close can wait forever on a stalled
    connection (batch 6 sat 9h after its writes had committed), so fall back to terminate."""
    try:
        await asyncio.wait_for(pool.close(), timeout=timeout_s)
    except (asyncio.TimeoutError, OSError, asyncpg.PostgresError):
        pool.terminate()


async def _create_pool_with_retry(attempts: int = 10, delay_s: float = 30.0) -> asyncpg.Pool:
    """Open a DB pool, retrying through transient network/DNS drops.

    The write phase runs after a chunk's Mapbox lookups are already paid for, so a
    momentary outage here must not discard them (a DNS blip lost a whole batch).
    """
    for attempt in range(1, attempts + 1):
        try:
            return await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
        except (OSError, asyncpg.PostgresError) as e:
            if attempt == attempts:
                raise
            print(f"  ⚠️  DB connect failed ({e}); retry {attempt}/{attempts - 1} in {delay_s:.0f}s")
            await asyncio.sleep(delay_s)


async def batch_geocode_mapbox(properties: List[Dict], pool: asyncpg.Pool,
                                client: httpx.AsyncClient,
                                rk_centroids: Optional[dict] = None,
                               rk_thresholds: Optional[dict] = None,
                               centroid_mode: bool = False) -> List[Tuple[int, Optional[float], Optional[float], int]]:
    """
    Batch geocode using Mapbox API with improved logic:
    - HTML entity cleaning (Tandy&#039;s → Tandy's)
    - Eircode-first strategy (try postal code before address)
    - Bulk sale extraction (Units 1-76 Bridge Hall → Bridge Hall)
    - Canonical cache

    Returns list of (property_id, lat, lon, quality_score)
    """
    if not MAPBOX_TOKEN:
        print("❌ MAPBOX_TOKEN not set in backend/.env")
        return []

    # Process all properties (cache is too large to load)
    print(f"Geocoding {len(properties)} properties with improved logic:")
    print(f"  - HTML entity cleaning (Tandy&#039;s → Tandy's)")
    print(f"  - Eircode-first strategy (try postal code before address)")
    print(f"  - Bulk sale extraction (Units 1-76 → base address)")

    results = []

    # Use MapboxClient for tracking and eircode-first strategy
    async with MapboxClient(source='geocode_mapbox_batch', operation='needs_geocoding') as mapbox:
        # Process individually to use eircode-first and bulk extraction logic
        bulk_count = 0
        eircode_count = 0

        for i, prop in enumerate(properties):
            if i % 100 == 0 and i > 0:
                print(f"  Progress: {i}/{len(properties)} properties...")

            # Get address and clean HTML entities
            address = prop.get('address_normalized') or prop['address']
            address = html.unescape(address)

            # Check if bulk sale and extract base address
            if is_bulk_sale(address):
                address = extract_base_address(address)
                bulk_count += 1

            # If the property has an eircode routing key with a known centroid, bias
            # Mapbox toward it. This is the key fix for generic street names
            # ("Main Street", "Harbour Road"): without a bias Mapbox picks whichever
            # matching street ranks highest and lands in the wrong district (e.g.
            # "Main Street, Donnybrook D04" resolving to D11, 8km away). Passing the
            # routing-key centroid as proximity snaps the match back to the right area.
            proximity = None
            if rk_centroids:
                proximity = rk_centroids.get(prop.get('routing_key'))

            # Drop "Dublin N" when proximity already carries the district — Mapbox
            # otherwise reads it as "N Dublin Street" (e.g. Baldoyle). Without a
            # routing key it's our only district signal, so keep it.
            if proximity:
                address = strip_dublin_district(address)

            # Build query with county
            query = f"{address}, {prop['county']}, Ireland" if prop['county'] else f"{address}, Ireland"

            try:
                # Geocode by ADDRESS only. Mapbox cannot resolve Irish unit-level
                # eircodes (proprietary An Post data) — the pre-lookup returns
                # nothing (or coarse routing-key level) and wastes a request. The
                # eircode's routing key is instead used as a proximity bias here and
                # for the hard distance check in validate_coordinates below.
                result = await mapbox.geocode(query, country='ie', proximity=proximity)

                if result:
                    lat = result['latitude']
                    lon = result['longitude']
                    # v6 API returns feature_type (address/street/postcode/…) and a
                    # separate coordinate accuracy (rooftop/parcel/point/…) as 'precision'.
                    feature_type = result.get('feature_type', 'unknown')
                    precision = result.get('precision', 'unknown')

                    if result.get('method') == 'eircode':
                        eircode_count += 1

                    # Validate with real feature_type + precision so rooftop (100) /
                    # parcel (90) / point (80) score distinctly. Pass routing key +
                    # centroids for the hard distance check.
                    is_valid, reason, quality_score = validate_coordinates(
                        lat, lon, prop['county'], feature_type, precision,
                        routing_key=prop.get('routing_key'), rk_centroids=rk_centroids,
                        rk_thresholds=rk_thresholds
                    )
                    if (is_valid and feature_type in ('address', 'street')
                            and not street_matches(result.get('full_address'),
                                                   strip_dublin_district(address))):
                        is_valid, reason = False, f"street_mismatch({result.get('full_address', '')[:40]})"

                    # Centroid mode: a town-level answer (or one that lands back on the
                    # row's current point) can't fix a town-level centroid — it just
                    # re-saves the same pile as a "success" (Donegal town, batch 3).
                    if is_valid and centroid_mode:
                        if feature_type in ('locality', 'place', 'postcode', 'region',
                                            'district', 'neighborhood'):
                            is_valid, reason = False, f"centroid_level({feature_type})"
                        elif prop.get('latitude') is not None and _haversine_km(
                                lat, lon, prop['latitude'], prop['longitude']) < 0.1:
                            is_valid, reason = False, "same_point"

                    if is_valid and quality_score >= 70:
                        results.append((prop['id'], lat, lon, quality_score))
                    else:
                        # Log every rejection so batch reports can tally reasons.
                        print(f"  ⚠️  Rejected {prop['address'][:40]}: {reason}")
                        results.append((prop['id'], None, None, 0))
                else:
                    print(f"  ⚠️  Rejected {prop['address'][:40]}: no_result")
                    results.append((prop['id'], None, None, 0))

            except Exception as e:
                if len(results) < 5:
                    print(f"  ❌ Error geocoding {prop['address'][:40]}: {e}")
                # quality -1 = request error (e.g. network drop), not a rejection:
                # the row was never really tried, so don't record an attempt.
                results.append((prop['id'], None, None, -1))

    print(f"\n✓ Geocoding complete:")
    print(f"  Bulk sales extracted: {bulk_count}")
    print(f"  Eircode-first hits: {eircode_count}")
    print(f"  Total geocoded: {sum(1 for r in results if r[1] is not None)}/{len(results)}")

    return results


async def geocode_with_mapbox(limit: int = None, dry_run: bool = True,
                               county: str = None, needs_geocoding: bool = False,
                               no_eircode: bool = False, min_price: int = None,
                               centroid: bool = False, suspect: bool = False,
                               eircode_only: bool = False, since: str = None,
                               before: str = None, ids_file: str = None):
    """
    Batch geocode properties using Mapbox.

    Args:
        limit: Max number of properties to process
        dry_run: If True, don't update database
        county: Filter to specific county
        needs_geocoding: If True, process properties flagged as needs_geocoding
        no_eircode: If True (with needs_geocoding), only process properties WITHOUT Eircodes
        min_price: If set, only process properties >= this price
        centroid: If True, process properties at centroid coordinates
    """
    if not MAPBOX_TOKEN:
        print("❌ MAPBOX_TOKEN not set in backend/.env")
        print("\nGet your API key from: https://www.mapbox.com/")
        print("Add to backend/.env: MAPBOX_TOKEN=your_token_here")
        return

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    try:
        # Fetch properties
        if ids_file:
            # Exact rows from a file (one id per line) — used to re-run a specific
            # batch so before/after results can be compared like-for-like.
            ids = [int(x) for x in open(ids_file).read().split()]
            rows = await pool.fetch("""
                SELECT id, address, address_normalized, county, eircode, routing_key,
                       latitude, longitude, price, sale_date
                FROM properties WHERE id = ANY($1::bigint[]) ORDER BY id
            """, ids)
            properties = [dict(r) for r in rows]
        elif centroid:
            properties = await fetch_centroid_properties(
                pool, limit=limit, county=county
            )
        else:
            properties = await fetch_properties_needing_geocoding(
                pool, limit=limit, county=county, no_eircode=no_eircode,
                min_price=min_price, suspect=suspect, eircode_only=eircode_only,
                since=since, before=before
            )

        print(f"\n{'='*70}")
        print(f"MAPBOX BATCH GEOCODING")
        print(f"{'='*70}")
        if centroid:
            print(f"Mode: CENTROID RE-GEOCODING")
        elif needs_geocoding:
            filters = []
            if no_eircode:
                filters.append("WITHOUT Eircodes")
            if min_price:
                filters.append(f"Price >= €{min_price:,}")
            if since:
                filters.append(f"Sale date >= {since}")
            if before:
                filters.append(f"Sale date < {before}")
            if filters:
                print(f"Filters: {', '.join(filters)}")
        print(f"Properties to process: {len(properties):,}")
        print(f"Batch size: Up to 1,000 per API call")
        print(f"Database updates: {'DRY RUN (no changes)' if dry_run else 'APPLY'}")
        print()

        if dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made\n")

        # Load routing-key centroids once for the hard distance validation.
        rk_centroids = {}
        try:
            rk_rows = await pool.fetch(
                "SELECT routing_key, centroid_lat, centroid_lon FROM routing_key_stats "
                "WHERE geocoded_count >= 20 AND centroid_lat IS NOT NULL"
            )
            rk_centroids = {r['routing_key']: (r['centroid_lat'], r['centroid_lon']) for r in rk_rows}
            print(f"Loaded {len(rk_centroids):,} routing-key centroids for validation")
        except Exception as e:
            print(f"⚠️  Could not load routing_key_stats centroids ({e}); skipping distance validation")

        # Adaptive per-key distance thresholds (p75 extent formula, as in
        # flag_bad_geocodes.py). Keys missing here fall back to ROUTING_KEY_MAX_KM.
        rk_thresholds = {}
        try:
            async with pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '600s'")
                ext_rows = await conn.fetch("""
                    SELECT p.routing_key,
                           percentile_cont(0.75) WITHIN GROUP (ORDER BY
                             ST_Distance(
                               ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
                               ST_SetSRID(ST_MakePoint(k.centroid_lon, k.centroid_lat), 4326)::geography
                             ) / 1000.0) AS p75_km
                    FROM properties p
                    JOIN routing_key_stats k ON k.routing_key = p.routing_key
                    WHERE p.latitude IS NOT NULL
                      AND k.geocoded_count >= 20 AND k.centroid_lat IS NOT NULL
                    GROUP BY p.routing_key
                """)
            rk_thresholds = {
                r['routing_key']: max(RK_FLOOR_KM, min(RK_CEIL_KM, r['p75_km'] * RK_MULT))
                for r in ext_rows
            }
            print(f"Loaded {len(rk_thresholds):,} adaptive routing-key thresholds")
        except Exception as e:
            print(f"⚠️  Could not compute adaptive thresholds ({e}); using flat {ROUTING_KEY_MAX_KM:.0f}km")

        # Release the DB pool during the (potentially long) geocoding phase. Holding
        # idle connections open across a multi-minute Mapbox run lets Supabase close
        # them server-side, so the later write phase would fail with
        # ConnectionDoesNotExistError and lose the whole batch's results. We reopen a
        # fresh pool for the writes below.
        await _close_pool(pool)
        pool = None

        # Geocode and persist in chunks. Previously the whole batch was geocoded into
        # memory and written only at the very end, so any interruption (crash, Supabase
        # disconnect, machine sleep) threw away EVERY geocode — and the Mapbox spend with
        # it. Persisting each chunk as it completes caps the loss to at most one chunk.
        success_count = 0
        failed_count = 0
        error_count = 0
        written = 0
        quality_scores = []
        total = len(properties)
        n_chunks = (total + CHUNK_SIZE - 1) // CHUNK_SIZE

        async with httpx.AsyncClient() as client:
            for ci, start in enumerate(range(0, total, CHUNK_SIZE), 1):
                chunk = properties[start:start + CHUNK_SIZE]
                print(f"\n--- Chunk {ci}/{n_chunks}: properties {start + 1:,}–{start + len(chunk):,} of {total:,} ---")
                results = await batch_geocode_mapbox(chunk, None, client, rk_centroids=rk_centroids,
                                                   rk_thresholds=rk_thresholds,
                                                   centroid_mode=centroid)

                # Tally this chunk and collect the rows to persist.
                chunk_updates = []
                failed_ids = []
                for prop_id, lat, lon, quality_score in results:
                    if lat and lon and quality_score >= 70:
                        success_count += 1
                        quality_scores.append(quality_score)
                        chunk_updates.append((lat, lon, prop_id))
                    elif quality_score == -1:
                        error_count += 1  # left untouched -> retried next run
                    else:
                        failed_count += 1
                        failed_ids.append(prop_id)

                # Mark failures as geocode_suspect so they leave the worklist and are
                # not re-attempted next run (the sweep previously re-billed the same
                # failing rows every sub-batch). Skipped for centroid mode: those rows
                # keep their existing (centroid) coordinates and flipping suspect would
                # hide them from search rather than just de-queue them.
                keep_coords = centroid or bool(ids_file)
                mark_failed = failed_ids and not keep_coords

                # Persist immediately with a short-lived pool (opened only for the write
                # so no idle connection is held across the next chunk's long geocode).
                if not dry_run and (chunk_updates or failed_ids):
                    pool = await _create_pool_with_retry()
                    try:
                        if chunk_updates:
                            await pool.executemany("""
                                UPDATE properties
                                SET latitude = $1, longitude = $2,
                                    geog = ST_MakePoint($2, $1)::geography,
                                    needs_geocoding = FALSE,
                                    geocode_suspect = FALSE,
                                    geocode_attempts = geocode_attempts + 1,
                                    geocode_last_attempt = now()
                                WHERE id = $3
                            """, chunk_updates)
                            written += len(chunk_updates)
                            print(f"  💾 Saved {len(chunk_updates):,} geocodes this chunk "
                                  f"(total saved: {written:,})")
                        if mark_failed:
                            # De-queue failures: set needs_geocoding = FALSE so NO worklist
                            # fetch re-selects them — including the --suspect path, which
                            # requires geocode_suspect = TRUE and previously re-billed the
                            # same failing addresses every sub-batch. Record the attempt so
                            # we have a persistent, auditable trail of what we've tried.
                            await pool.executemany(
                                """
                                UPDATE properties
                                SET geocode_suspect = TRUE,
                                    needs_geocoding = FALSE,
                                    geocode_attempts = geocode_attempts + 1,
                                    geocode_last_attempt = now()
                                WHERE id = $1
                                """,
                                [(fid,) for fid in failed_ids]
                            )
                            print(f"  🚩 Flagged {len(failed_ids):,} failed rows "
                                  f"(needs_geocoding=FALSE, attempt recorded — not re-billed)")
                        elif failed_ids and keep_coords:
                            # Centroid failures keep their coords and visibility; just
                            # record the attempt so the centroid fetch skips them.
                            await pool.executemany(
                                """
                                UPDATE properties
                                SET geocode_attempts = geocode_attempts + 1,
                                    geocode_last_attempt = now()
                                WHERE id = $1
                                """,
                                [(fid,) for fid in failed_ids]
                            )
                            print(f"  📝 Recorded {len(failed_ids):,} failed centroid attempts "
                                  f"(coords kept, not re-billed)")
                    except Exception as e:
                        # Don't let one failed write abort the whole run — later chunks
                        # can still save. These properties stay flagged for a re-run.
                        print(f"  ⚠️  Chunk write failed ({e}); {len(chunk_updates):,} "
                              f"geocodes not saved, will remain flagged for re-run")
                    finally:
                        await _close_pool(pool)
                        pool = None

        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Processed: {total:,}")
        print(f"✓ Success: {success_count:,} ({100*success_count/total:.1f}%)" if total else "✓ Success: 0")
        print(f"✗ Failed: {failed_count:,}")
        print(f"⚠ Request errors (not attempted, will retry): {error_count:,}")
        if not dry_run:
            print(f"💾 Saved to database: {written:,}")

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"\nQuality Score Average: {avg_quality:.1f}/100")
            print(f"  Rooftop (100): {sum(1 for q in quality_scores if q == 100)} properties")
            print(f"  Parcel (90): {sum(1 for q in quality_scores if q == 90)} properties")
            print(f"  Point (80): {sum(1 for q in quality_scores if q == 80)} properties")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to commit.")

    finally:
        if pool is not None:
            await _close_pool(pool)


async def main():
    # Skip canonical cache for batch operations (too large to load into memory)
    # Cache will be checked per-address during geocoding
    print("Starting batch geocoding with improved logic...\n")

    dry_run = "--apply" not in sys.argv
    needs_geocoding = "--needs-geocoding" in sys.argv
    no_eircode = "--no-eircode" in sys.argv
    centroid = "--centroid" in sys.argv
    suspect = "--suspect" in sys.argv
    eircode_only = "--eircode-only" in sys.argv
    limit = None
    county = None
    min_price = None
    since = None
    before = None
    ids_file = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == "--county" and i + 1 < len(sys.argv):
            county = sys.argv[i + 1]
        elif arg == "--min-price" and i + 1 < len(sys.argv):
            min_price = int(sys.argv[i + 1])
        elif arg == "--since" and i + 1 < len(sys.argv):
            since = sys.argv[i + 1]
        elif arg == "--before" and i + 1 < len(sys.argv):
            before = sys.argv[i + 1]
        elif arg == "--ids-file" and i + 1 < len(sys.argv):
            ids_file = sys.argv[i + 1]

    await geocode_with_mapbox(
        limit=limit,
        dry_run=dry_run,
        county=county,
        needs_geocoding=needs_geocoding,
        no_eircode=no_eircode,
        min_price=min_price,
        centroid=centroid,
        suspect=suspect,
        eircode_only=eircode_only,
        since=since,
        before=before,
        ids_file=ids_file
    )


if __name__ == "__main__":
    asyncio.run(main())
