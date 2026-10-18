"""
Geocoder service for property valuation.

Converts addresses to coordinates from our own data, in order:
1. Database match on the exact address (properties sold since 2010)
2. Database match on the development/street, for units that never sold
3. Routing-key centroid, from the Eircode or a "Dublin N" postal district

Nominatim is deliberately not used: OSM can't resolve Irish scheme/unit names
and its fuzzy answers land in the wrong town.

Returns coordinates with confidence score.
"""

import re
import unicodedata
import math
import logging

logger = logging.getLogger(__name__)
from typing import Dict, Optional, Tuple
from .models import GeocodingResult
from .cache import TTLCache


# Addresses don't move, so a resolved (address, eircode, county) -> location is
# stable. ValuationGeocoder is created per request, so this module-level cache is
# what lets repeated valuations of the same address skip the DB/Nominatim work
# entirely. 24h TTL, matching the search-layer geocode cache in main.py. Only
# successful results are cached.
_GEOCODE_CACHE = TTLCache(ttl_seconds=86400)


# A database coordinate further than this from the Eircode routing-key
# centroid is treated as wrong-area data (e.g. a mismatched fuzzy match in
# the wrong county) and discarded in favour of the routing-key centroid.
# Routing keys are geographically compact, so 30km comfortably clears any
# legitimate in-area address while catching gross county-level errors.
_ROUTING_KEY_MAX_KM = 30.0

# Dublin postal districts are far more compact: even including residual bad
# rows, every D-key's p95 member distance is under ~9km. 30km would accept a
# Stepaside (D18) address geocoded to Malahide, so D-keys get a tighter cap.
_DUBLIN_DISTRICT_MAX_KM = 10.0

# Recorded sales in one development (e.g. "The Oak, Parkview, Stepaside")
# should sit together; if they span more than this, some are mis-geocoded and
# their median can't be trusted.
_DEVELOPMENT_MAX_SPREAD_KM = 1.5

# A locality ("Stepaside", "Shrule") is a town or village, so its sales may
# spread wider — but a name matching sales across the county is no locality.
_LOCALITY_MAX_SPREAD_KM = 5.0

_AREA_CONFIDENCE = {"database_development": 0.70, "database_locality": 0.55}

# Leading unit designator stripped to find a development's other sales:
# "Apt 21, ...", "Unit 5B ...", "21 ...", "Flat 3, ...".
_UNIT_PREFIX = re.compile(
    r'^(?:(?:Apt|Apartment|Unit|Flat|No\.?)\s*)?\d+[A-Za-z]?\b\s*,?\s*', re.I
)

# An address part that is only a unit designator ("Apt 21", "Unit 5B").
_UNIT_PART = re.compile(r'^(?:(?:Apt|Apartment|Unit|Flat|No\.?)\s*)?\d+[A-Za-z]?$', re.I)

# Words that don't identify a place. Unit words are dropped too, since
# schemes are recorded inconsistently ("Parkview", "Parkview Apts").
_AREA_SKIP_WORDS = {
    'the', 'and', 'of', 'co', 'county', 'ireland', 'dublin',
    'apt', 'apts', 'apartment', 'apartments', 'unit', 'units', 'flat', 'flats', 'no',
}

_COUNTY_NAMES = {
    'carlow', 'cavan', 'clare', 'cork', 'donegal', 'dublin', 'galway', 'kerry',
    'kildare', 'kilkenny', 'laois', 'leitrim', 'limerick', 'longford', 'louth',
    'mayo', 'meath', 'monaghan', 'offaly', 'roscommon', 'sligo', 'tipperary',
    'waterford', 'westmeath', 'wexford', 'wicklow',
}

# "Dublin 18" / "Dublin 6W" -> routing key D18 / D6W.
_DUBLIN_DISTRICT = re.compile(r'\bDublin\s*(\d{1,2})(W)?\b', re.I)


def _normalize_address(address: str) -> str:
    """Normalize an address to match the address_normalized column.

    Same logic as the /search/exact endpoint (S1 page).
    """
    # Fold fadas (Slí → Sli) so input typed with or without them matches
    normalized = ''.join(c for c in unicodedata.normalize('NFKD', address)
                         if not unicodedata.combining(c)).strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'^No\.?\s+(\d+)', r'\1', normalized, flags=re.I)
    normalized = re.sub(r'\bApartment\b', 'Apt', normalized, flags=re.I)

    # Expand common abbreviations to match normalized format
    street_types = {
        r'\bSt\.?\b': 'Street', r'\bRd\.?\b': 'Road', r'\bAve\.?\b': 'Avenue',
        r'\bDr\.?\b': 'Drive', r'\bCl\.?\b': 'Close', r'\bCt\.?\b': 'Court',
        r'\bPk\.?\b': 'Park', r'\bSq\.?\b': 'Square',
    }
    for abbrev, full in street_types.items():
        normalized = re.sub(abbrev, full, normalized, flags=re.I)

    # Clean punctuation and apply title case
    normalized = re.sub(r',\s*,', ',', normalized)
    normalized = re.sub(r'\s+,', ',', normalized)
    normalized = re.sub(r',\s+', ', ', normalized)
    normalized = normalized.strip(', ')

    words = normalized.split()
    lower_exceptions = {'and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'}
    upper_exceptions = {'Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'}

    result_words = []
    for i, word in enumerate(words):
        if i == 0:
            result_words.append(word.capitalize())
        elif word in upper_exceptions:
            result_words.append(word)
        elif word.lower() in lower_exceptions:
            result_words.append(word.lower())
        else:
            result_words.append(word.capitalize())

    return ' '.join(result_words).strip()


def _max_km_for_routing_key(routing_key: str) -> float:
    return _DUBLIN_DISTRICT_MAX_KM if routing_key.upper().startswith('D') else _ROUTING_KEY_MAX_KM


def _routing_key_from_address(address: str) -> Optional[str]:
    """Routing key implied by a Dublin postal district in the address, if any."""
    m = _DUBLIN_DISTRICT.search(address or "")
    if not m:
        return None
    if m.group(2):
        return f"D{int(m.group(1))}W"
    return f"D{int(m.group(1)):02d}"


def _is_area_suffix(part: str) -> bool:
    """True for trailing parts that name a county/district, not a place:
    "Dublin 18", "Co. Meath", "County Cork", "Ireland"."""
    p = re.sub(r'^(?:Co\.?|County)\s+', '', part.strip(), flags=re.I).lower()
    return (
        p in _COUNTY_NAMES or p == 'ireland'
        or bool(re.fullmatch(r'dublin\s*\d{1,2}w?', p))
    )


def _address_levels(address_norm: str):
    """Broader and broader searches for an address that isn't itself in the PPR.

    "Apt 21, the Oak, Parkview, Stepaside, Dublin 18" yields
        ("database_development", "Oak Parkview Stepaside", 1.5)
        ("database_development", "Parkview Stepaside", 1.5)
        ("database_locality", "Stepaside", 5.0)
    i.e. (method, full-text terms, max spread km), most specific first.
    """
    rest = _UNIT_PREFIX.sub('', address_norm, count=1)
    # "Navan Co Meath" -> "Navan"; a bare county word is kept, since it may be
    # part of a street or town name ("Kildare Road").
    rest = re.sub(r'\b(?:Co\.?|County)\s+\w+', '', rest, flags=re.I)
    parts = [
        p.strip() for p in rest.split(',')
        if p.strip() and not _is_area_suffix(p) and not _UNIT_PART.match(p.strip())
    ]

    levels, seen = [], set()
    for i in range(len(parts)):
        words = [
            w for w in re.findall(r'\w+', ' '.join(parts[i:]))
            if not w.isdigit() and w.lower() not in _AREA_SKIP_WORDS
        ]
        terms = ' '.join(words)
        if not terms:
            continue
        candidates = []
        if i < len(parts) - 1 or len(parts) == 1:
            candidates.append(("database_development", terms, _DEVELOPMENT_MAX_SPREAD_KM))
        if i == len(parts) - 1:
            # The last part is the locality; a lone part ("Ranelagh") may be
            # either, so it is tried tight first, then as a locality.
            candidates.append(("database_locality", terms, _LOCALITY_MAX_SPREAD_KM))
        for level in candidates:
            if (level[0], terms.lower()) not in seen:
                seen.add((level[0], terms.lower()))
                levels.append(level)
    return levels


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class ValuationGeocoder:
    """Geocoder with multiple fallback methods."""

    def __init__(self, db_pool):
        """
        Initialize geocoder.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db = db_pool

    async def geocode_address(
        self,
        address: str,
        eircode: Optional[str] = None,
        county: Optional[str] = None
    ) -> GeocodingResult:
        """
        Geocode an address using multiple methods (cached).

        Priority:
        1. Database lookup of the exact address
        2. Database lookup of the development/street (unsold units)
        3. Routing-key centroid (Eircode, else "Dublin N" in the address)

        Successful results are memoised per (address, eircode, county) for 24h;
        the resolution work itself lives in ``_geocode_address_uncached``.

        Args:
            address: Property address
            eircode: Optional Eircode (7 chars, no space)
            county: Optional county name (defaults to Dublin)

        Returns:
            GeocodingResult with coordinates and confidence

        Raises:
            ValueError: If geocoding fails completely
        """
        cache_key = (
            (address or "").strip().lower(),
            (eircode or "").strip().upper(),
            (county or "").strip().lower(),
        )
        hit, cached = _GEOCODE_CACHE.get(cache_key)
        if hit:
            return cached

        # A failed geocode raises ValueError and is deliberately not cached, so
        # it is retried once new sales are imported; only cache successes.
        result = await self._geocode_address_uncached(address, eircode, county)
        _GEOCODE_CACHE.set(cache_key, result)
        return result

    async def _geocode_address_uncached(
        self,
        address: str,
        eircode: Optional[str] = None,
        county: Optional[str] = None
    ) -> GeocodingResult:
        """Resolve an address to a GeocodingResult (see geocode_address).

        Falls back from the most to the least specific location we hold, so a
        valuation always gets a location for any county with sales data:
        exact address -> development/street -> locality -> routing key ->
        county centroid.
        """
        county_name = county or "Dublin"

        # The routing key (from the Eircode, else a "Dublin N" district in the
        # address) is both a fallback and a sanity check: a database-derived
        # location outside it is wrong-area data and is skipped.
        routing_key = None
        routing_key_result = None
        if eircode:
            routing_key = eircode[:3].upper()
        else:
            routing_key = _routing_key_from_address(address)
        if routing_key:
            try:
                routing_key_result = await self._geocode_by_eircode_routing_key(routing_key)
            except Exception as e:
                logger.warning(f"Routing key lookup failed: {e}")
            if routing_key_result and not eircode:
                routing_key_result.method = "postal_district_routing_key"
                routing_key_result.address_matched = f"Dublin postal district {routing_key}"

        def in_routing_key_area(result: GeocodingResult) -> bool:
            if not routing_key_result:
                return True
            km = _haversine_km(
                result.latitude, result.longitude,
                routing_key_result.latitude, routing_key_result.longitude
            )
            if km > _max_km_for_routing_key(routing_key):
                logger.warning(
                    f"{result.method} location for '{address}' is {km:.1f}km "
                    f"from routing key {routing_key}; skipping"
                )
                return False
            return True

        # Method 1: the exact property (any sale in the PPR since 2010).
        # Constrained to the requested county so an identical street/house
        # number elsewhere is never returned.
        try:
            result = await self._geocode_by_db_fuzzy_match(address, county)
            if result and in_routing_key_area(result):
                logger.info(f"✅ Geocoded via database: {result.address_matched}")
                return result
        except Exception as e:
            logger.warning(f"Database geocoding failed: {e}")

        # Method 2: progressively broader parts of the address — the
        # development/street the unit is in, then its locality — located by
        # the median of their recorded sales.
        for method, terms, max_spread_km in _address_levels(_normalize_address(address)):
            try:
                result = await self._geocode_by_db_area(terms, county_name, method, max_spread_km)
            except Exception as e:
                logger.warning(f"Database area lookup failed for '{terms}': {e}")
                continue
            if result and in_routing_key_area(result):
                logger.info(f"✅ Geocoded via {method}: '{terms}'")
                return result

        # Method 3: routing-key centroid.
        if routing_key_result:
            logger.info(f"✅ Geocoded via routing key: {routing_key}")
            return routing_key_result

        # Method 4: county centroid — always available for a county with data.
        try:
            result = await self._geocode_by_county_centroid(county_name)
            if result:
                logger.info(f"✅ Geocoded via county centroid: {county_name}")
                return result
        except Exception as e:
            logger.warning(f"County centroid lookup failed: {e}")

        if eircode:
            raise ValueError(
                f"Could not locate '{address}' (Eircode: {eircode}). "
                "Please verify the address, Eircode and county are correct."
            )
        raise ValueError(
            f"Could not locate '{address}' in County {county_name}. "
            "Please verify the county is correct."
        )

    async def _geocode_by_eircode_routing_key(
        self,
        eircode: str
    ) -> Optional[GeocodingResult]:
        """
        Geocode using Eircode routing key (first 3 chars).

        Uses routing_key_stats materialized view for fast lookup.

        Args:
            eircode: 7-character Eircode (e.g., 'D02X285')

        Returns:
            GeocodingResult or None if routing key not found
        """
        routing_key = eircode[:3].upper()

        query = """
            SELECT
                centroid_lat,
                centroid_lon,
                property_count
            FROM routing_key_stats
            WHERE routing_key = $1;
        """

        row = await self.db.fetchrow(query, routing_key)

        if row and row['property_count'] >= 5:
            # Confidence based on property count
            # High count = more reliable centroid
            confidence = min(0.85, 0.70 + (row['property_count'] / 1000) * 0.15)

            return GeocodingResult(
                latitude=float(row['centroid_lat']),
                longitude=float(row['centroid_lon']),
                confidence=confidence,
                method="eircode_routing_key",
                address_matched=f"Routing key {routing_key}"
            )

        return None

    async def _geocode_by_db_area(
        self,
        terms: str,
        county: str,
        method: str,
        max_spread_km: float
    ) -> Optional[GeocodingResult]:
        """
        Locate a development, street or locality by its recorded sales.

        Matches every term with full-text search (GIN-indexed, AND semantics),
        takes the median coordinate, and rejects it if the matches are spread
        out (p75 distance from the median > max_spread_km): a scattered set
        means mixed places or mis-geocoded rows, so its median is meaningless.

        Args:
            terms: Space-separated search terms, e.g. "Oak Parkview Stepaside"
            county: County to constrain the match to
            method: Method name for the result ("database_development"/"database_locality")
            max_spread_km: Maximum p75 distance of matches from their median

        Returns:
            GeocodingResult or None if no tight cluster of sales matches
        """
        query = """
            WITH m AS (
                SELECT latitude, longitude, address
                FROM properties
                WHERE
                    to_tsvector('simple', COALESCE(address_normalized, address))
                        @@ plainto_tsquery('simple', $1)
                    AND county ILIKE $2
                    AND latitude IS NOT NULL
                    AND longitude IS NOT NULL
                    AND geocode_suspect IS NOT TRUE
                    AND geocode_quality_issue IS NOT TRUE
                -- A sample is plenty for a median/spread, and bounds the heap
                -- fetches for big towns (Lucan has ~8k sales).
                LIMIT 500
            ),
            c AS (
                SELECT
                    percentile_cont(0.5) WITHIN GROUP (ORDER BY latitude) AS lat,
                    percentile_cont(0.5) WITHIN GROUP (ORDER BY longitude) AS lon
                FROM m
            )
            SELECT
                c.lat AS latitude,
                c.lon AS longitude,
                COUNT(*) AS n,
                percentile_cont(0.75) WITHIN GROUP (ORDER BY
                    ST_DistanceSphere(ST_MakePoint(m.longitude, m.latitude),
                                      ST_MakePoint(c.lon, c.lat))
                ) / 1000.0 AS spread_km,
                MIN(m.address) AS address
            FROM m, c
            GROUP BY c.lat, c.lon;
        """
        row = await self.db.fetchrow(query, terms, county)
        if not row or row['latitude'] is None:
            return None
        if row['spread_km'] > max_spread_km:
            logger.info(
                f"'{terms}' matches {row['n']} sales spread {row['spread_km']:.1f}km "
                f"(> {max_spread_km}km); skipping"
            )
            return None

        return GeocodingResult(
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            confidence=_AREA_CONFIDENCE[method],
            method=method,
            address_matched=f"{row['n']} sales matching '{terms}', e.g. {row['address']}"
        )

    async def _geocode_by_county_centroid(self, county: str) -> Optional[GeocodingResult]:
        """Median of the county's routing-key centroids (last-resort location)."""
        query = """
            SELECT
                percentile_cont(0.5) WITHIN GROUP (ORDER BY centroid_lat) AS latitude,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY centroid_lon) AS longitude
            FROM routing_key_stats
            WHERE primary_county ILIKE $1
              AND geocoded_count >= 20
              AND centroid_lat IS NOT NULL;
        """
        row = await self.db.fetchrow(query, county)
        if not row or row['latitude'] is None:
            return None

        return GeocodingResult(
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            confidence=0.30,
            method="county_centroid",
            address_matched=f"County {county}"
        )

    async def _geocode_by_db_fuzzy_match(
        self,
        address: str,
        county: Optional[str] = None
    ) -> Optional[GeocodingResult]:
        """
        Geocode by matching against known addresses in database.

        Uses EXACT same logic as /search/exact endpoint (S1 page), but
        constrained to a single county so a matching street/house number in a
        different county cannot be returned by mistake.

        Args:
            address: Property address
            county: County to constrain the match to. Defaults to Dublin when
                not supplied (most requests are Dublin, and an unscoped match
                across all counties produces wrong-area results).

        Returns:
            GeocodingResult or None if no match found
        """
        county_name = county or "Dublin"
        address_norm = _normalize_address(address)

        # Try exact prefix match first (fast, for S1 page compatibility).
        # Scope to county so e.g. a Cork "36 Fairfield Road" is not returned
        # for a Dublin request. Screen out bulk/multi-unit rows and coordinates
        # already flagged as low-quality so they can never win a match.
        query_exact = """
            SELECT
                latitude,
                longitude,
                address,
                bedrooms,
                property_type
            FROM properties
            WHERE
                -- Bare column (never NULL) so the text_pattern_ops index
                -- idx_properties_address_normalized_prefix serves the prefix.
                starts_with(address_normalized, $1)
                AND county ILIKE $2
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
                AND (address_normalized IS NULL
                     OR address_normalized !~* '[0-9]+ *(-|to) *[0-9]+')
                AND geocode_suspect IS NOT TRUE
                AND geocode_quality_issue IS NOT TRUE
            LIMIT 1;
        """

        row = await self.db.fetchrow(query_exact, address_norm, county_name)

        # If no exact prefix match, fall back to full-text search for partial
        # addresses, e.g. "28 Slane Road, Dublin 12" -> "28 Slane Road, Crumlin,
        # Dublin 12".
        #
        # We use plainto_tsquery (AND semantics) rather than a LIKE/ILIKE token
        # match. Per the project's query rules (CLAUDE.md "NEVER use LIKE" /
        # memory feedback_no_like_queries) this hits the GIN index
        # idx_properties_address_fts instead of seq-scanning, AND its AND
        # semantics keep the match precise: every significant token must be
        # present, so a partially-overlapping street (e.g. "Bath Avenue
        # Gardens" for "Richmond Gardens, Richmond Avenue") can't match, and a
        # scheme whose marketing name is absent from the PPR (e.g. "The
        # Marker") simply returns nothing here and falls through to the more
        # reliable Eircode routing-key centroid instead of a confident wrong
        # rooftop. Same bulk/quality screens as the exact query above.
        if not row:
            # Skip pure filler words; plainto_tsquery handles tokenising, but we
            # guard against a query so generic it would match half the county.
            words = re.findall(r'\w+', address_norm)
            skip_words = {'the', 'and', 'dublin', 'ireland', 'co', 'county'}
            tokens = [w for w in words if len(w) >= 2 and w.lower() not in skip_words]

            if len(tokens) >= 2:
                query_fts = """
                    SELECT
                        latitude,
                        longitude,
                        address,
                        bedrooms,
                        property_type
                    FROM properties
                    WHERE
                        to_tsvector('simple', COALESCE(address_normalized, address))
                            @@ plainto_tsquery('simple', $1)
                        AND county ILIKE $2
                        AND latitude IS NOT NULL
                        AND longitude IS NOT NULL
                        AND (address_normalized IS NULL
                             OR address_normalized !~* '[0-9]+ *(-|to) *[0-9]+')
                        AND geocode_suspect IS NOT TRUE
                        AND geocode_quality_issue IS NOT TRUE
                    ORDER BY LENGTH(COALESCE(address_normalized, address))  -- Prefer shorter (more specific) matches
                    LIMIT 1;
                """
                row = await self.db.fetchrow(query_fts, address_norm, county_name)

        if row:
            result = GeocodingResult(
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                confidence=0.80,  # High confidence for database match
                method="database_exact",
                address_matched=row['address']
            )
            # Store bedrooms and property type for later use (if available)
            result.bedrooms = row['bedrooms']
            result.property_type = row['property_type']
            return result

        return None

