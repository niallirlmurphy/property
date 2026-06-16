from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator
from collections import defaultdict, deque
import asyncio
import asyncpg
import os
import re
import time
import hashlib
import json
import httpx
import logging
from typing import Optional
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL    = os.environ["DATABASE_URL"]
MAPBOX_TOKEN    = os.environ.get("MAPBOX_TOKEN", "")
AUTOADDRESS_KEY = os.environ.get("AUTOADDRESS_KEY", "")
SENTRY_DSN      = os.environ.get("SENTRY_DSN", "")
USER_AGENT      = "PPR-webapp/1.0 (personal research)"

# Initialize Sentry for error tracking and performance monitoring
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            AsyncioIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% profiling
        environment=os.environ.get("RAILWAY_ENVIRONMENT", "development"),
        release=os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown"),
    )
    logger.info("Sentry initialized for error tracking")

AA_AUTOCOMPLETE = "https://api.autoaddress.com/3.0/autocomplete"

# Ireland geographic bounds for validation (prevents geocoding to UK/international locations)
# Coordinates: (min_lat, max_lat, min_lon, max_lon)
IRELAND_BOUNDS = (51.4, 55.5, -10.7, -5.4)

def _is_in_ireland(lat: float, lon: float) -> bool:
    """Check if coordinates fall within Ireland's bounding box."""
    min_lat, max_lat, min_lon, max_lon = IRELAND_BOUNDS
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

# Max concurrent Autoaddress lookups across all in-flight requests
_aa_semaphore: asyncio.Semaphore = None

db_pool: asyncpg.Pool = None
_last_activity: float = time.time()
_HEARTBEAT_INTERVAL = 6 * 24 * 3600  # ping if idle for 6 days


# ---------------------------------------------------------------------------
# Simple in-memory TTL cache
# ---------------------------------------------------------------------------

class TTLCache:
    def __init__(self):
        self._store: dict = {}

    def _key(self, namespace: str, params: dict) -> str:
        raw = namespace + json.dumps(params, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, namespace: str, params: dict):
        key = self._key(namespace, params)
        entry = self._store.get(key)
        if entry and time.time() < entry["expires"]:
            return entry["value"]
        return None

    def set(self, namespace: str, params: dict, value, ttl_seconds: int):
        key = self._key(namespace, params)
        self._store[key] = {"value": value, "expires": time.time() + ttl_seconds}

    def invalidate(self, namespace: str):
        keys = [k for k, v in self._store.items() if k.startswith(namespace)]
        for k in keys:
            del self._store[k]


cache = TTLCache()

# TTLs
TTL_COUNTIES = 3600        # 1 hour
TTL_TRENDS   = 3600        # 1 hour
TTL_EIRCODE  = 3600        # 1 hour
TTL_GEOCODE  = 86400       # 24 hours — addresses don't move
TTL_SEARCH   = 300         # 5 minutes — property results are stable enough


async def _heartbeat_loop():
    """Ping the DB if there has been no activity for _HEARTBEAT_INTERVAL seconds.
    Prevents Supabase from pausing the project due to inactivity."""
    while True:
        await asyncio.sleep(3600)  # check every hour
        if time.time() - _last_activity >= _HEARTBEAT_INTERVAL:
            try:
                async with db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                logger.info("Heartbeat ping sent to keep Supabase project alive")
            except Exception as e:
                logger.warning(f"Heartbeat ping failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, _aa_semaphore
    _aa_semaphore = asyncio.Semaphore(2)  # max 2 concurrent AA lookups
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
        statement_cache_size=0,   # required for Supabase PgBouncer compatibility
        server_settings={"application_name": "homeiq"},
        command_timeout=30,
    )
    # Warm up min_size connections immediately so the first request isn't slow
    async with db_pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    logger.info("DB pool warmed up")
    task = asyncio.create_task(_heartbeat_loop())
    yield
    task.cancel()
    await db_pool.close()

# ---------------------------------------------------------------------------
# Simple in-memory per-IP rate limiter
# ---------------------------------------------------------------------------

_rate_buckets: dict[str, deque] = defaultdict(deque)

def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _rate_limit_check(request: Request, limit_per_min: int, namespace: str) -> None:
    """Raise HTTPException(429) if this IP has exceeded its limit for the namespace."""
    key = f"{namespace}:{_client_ip(request)}"
    now = time.time()
    bucket = _rate_buckets[key]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= limit_per_min:
        raise HTTPException(status_code=429, detail="Too many requests")
    bucket.append(now)


app = FastAPI(
    title="Property Price Register API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

ALLOWED_ORIGINS = [
    "https://homeiq.ie",
    "https://www.homeiq.ie",
]
if os.environ.get("ENVIRONMENT") != "production":
    ALLOWED_ORIGINS.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def track_activity(request: Request, call_next):
    global _last_activity
    _last_activity = time.time()
    response = await call_next(request)
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Force HTTPS for 1 year (including subdomains)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# ---------------------------------------------------------------------------
# Geocode helper — resolve user input to (lat, lon)
# ---------------------------------------------------------------------------

def _looks_like_eircode(s: str) -> bool:
    return bool(re.match(r"^[A-Za-z]\d{1,2}\s?[A-Za-z0-9]{4}$", s.strip()))


def _looks_like_routing_key(s: str) -> bool:
    """Match 3-char routing keys like D04, H91, V94."""
    return bool(re.match(r"^[A-Za-z]\d{1,2}[A-Za-z]?$", s.strip()))


def _routing_key(eircode: str) -> str:
    parts = eircode.strip().upper().split()
    return parts[0] if parts else eircode.upper()


def _normalise_eircode(s: str) -> str:
    """Strip spaces and uppercase — matches all three storage formats."""
    return s.strip().upper().replace(" ", "")


MIN_DB_MATCHES = 3

_STARTS_WITH_NUMBER = re.compile(r"^\d+\s+\w")

# Abbreviation → full expansion for Irish addresses.
# Applied before sending to Mapbox so it can resolve correctly.
# Word-boundary anchored to avoid partial matches (e.g. "St" in "Stoneybatter").
_ADDR_ABBREVS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bRd\.?\b",          re.IGNORECASE), "Road"),
    (re.compile(r"\bAve?\.?\b",        re.IGNORECASE), "Avenue"),
    (re.compile(r"\bDr\.?\b",          re.IGNORECASE), "Drive"),
    (re.compile(r"\bTce\.?(?=\W|$)",    re.IGNORECASE), "Terrace"),
    (re.compile(r"\bTerr\.?(?=\W|$)",  re.IGNORECASE), "Terrace"),
    (re.compile(r"\bCres\.?\b",        re.IGNORECASE), "Crescent"),
    (re.compile(r"\bGdns?\.?\b",       re.IGNORECASE), "Gardens"),
    (re.compile(r"\bSq\.?\b",          re.IGNORECASE), "Square"),
    (re.compile(r"\bPk\.?\b",          re.IGNORECASE), "Park"),
    (re.compile(r"\bBlvd\.?\b",        re.IGNORECASE), "Boulevard"),
    (re.compile(r"\bMt\.?\b",          re.IGNORECASE), "Mount"),
    (re.compile(r"\bNth\.?\b",         re.IGNORECASE), "North"),
    (re.compile(r"\bSth\.?\b",         re.IGNORECASE), "South"),
    # "St." with a dot is unambiguous — expand to Street.
    # Bare "St" without a dot is left alone: it's more often Saint than Street
    # in Irish addresses (St Patrick's, St Brigid's etc).
    (re.compile(r"\bSt\.",             re.IGNORECASE), "Street"),
    # Strip "No." / "No " prefix from house numbers: "No. 11 Foo" → "11 Foo"
    (re.compile(r"^No\.?\s*",          re.IGNORECASE), ""),
    # Strip "Co." county qualifier — Mapbox doesn't need it
    (re.compile(r",?\s*Co\.?\s+",      re.IGNORECASE), ", "),
]


def _expand_abbreviations(query: str) -> str:
    """Expand common Irish address abbreviations for better Mapbox resolution."""
    for pattern, replacement in _ADDR_ABBREVS:
        query = pattern.sub(replacement, query)
    # Collapse any double spaces left by substitutions
    return re.sub(r"  +", " ", query).strip(", ").strip()


_STOP_WORDS = {"the", "a", "an", "of", "and", "co", "no", "st", "dublin", "ireland"}
_TOKEN_RE   = re.compile(r"[a-z0-9]+")

# Both directions so DB abbreviations (Rd, Ave) match expanded query tokens (Road, Avenue)
# Only include abbreviations that appear in actual PPR address data — avoid short tokens
# like "ct" (court) which match too many unrelated substrings and blow up clusters.
_ABBREV_TO_FULL = {"rd": "road", "ave": "avenue", "dr": "drive", "tce": "terrace",
                   "cres": "crescent", "gdns": "gardens", "sq": "square",
                   "pk": "park", "mt": "mount"}
_FULL_TO_ABBREV = {v: k for k, v in _ABBREV_TO_FULL.items()}


def _address_tokens(s: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(s.lower()) if t not in _STOP_WORDS and len(t) > 1]


def _token_condition(t: str, idx: int) -> "tuple[str, list]":
    """Return (SQL fragment, params) for a token, matching its abbreviation/expansion too.
    Also handles singular/plural variants (lawn/lawns, garden/gardens, etc.)."""
    patterns = [f"%{t}%"]

    # Check for abbreviation/expansion
    alt = _FULL_TO_ABBREV.get(t) or _ABBREV_TO_FULL.get(t)
    if alt:
        patterns.append(f"%{alt}%")

    # Handle plural/singular variants
    if t.endswith('s') and len(t) > 3:
        # Try singular: "lawns" → "lawn", "gardens" → "garden"
        singular = t[:-1]
        patterns.append(f"%{singular}%")
    elif not t.endswith('s'):
        # Try plural: "lawn" → "lawns", "garden" → "gardens"
        plural = t + 's'
        patterns.append(f"%{plural}%")

    if len(patterns) == 1:
        return f"LOWER(address) LIKE ${idx}", patterns
    else:
        # Build OR condition for all variants
        conditions = [f"LOWER(address) LIKE ${idx+i}" for i in range(len(patterns))]
        return f"({' OR '.join(conditions)})", patterns


async def _geocode_db_tokens(query: str) -> "tuple[float, float] | None":
    """Match query against DB by requiring all significant tokens to appear in the address.
    Each token also matches its abbreviated/expanded form (road↔rd, avenue↔ave, etc.)
    so DB entries like 'MERRION RD' match a query for 'Merrion Road'.
    Returns centroid if matching rows form a tight cluster.
    Single-token queries (e.g. "Rathmines") use a tighter stddev threshold to avoid
    false positives from common words.
    Requires a pg_trgm GIN index on LOWER(address) for acceptable performance.
    """
    tokens = _address_tokens(query)
    if not tokens:
        return None
    # Single-token queries need a tighter cluster to avoid false positives
    std_threshold = 0.02 if len(tokens) >= 2 else 0.01

    parts, params = [], []
    idx = 1
    for t in tokens:
        cond, p = _token_condition(t, idx)
        parts.append(cond)
        params.extend(p)
        idx += len(p)

    where = " AND ".join(parts)
    try:
        row = await asyncio.wait_for(
            db_pool.fetchrow(f"""
                SELECT AVG(latitude)              AS lat,
                       AVG(longitude)             AS lon,
                       COUNT(*)                   AS cnt,
                       COALESCE(STDDEV(latitude),  0) AS std_lat,
                       COALESCE(STDDEV(longitude), 0) AS std_lon
                FROM properties
                WHERE latitude IS NOT NULL AND {where}
            """, *params),
            timeout=2.0,
        )
    except Exception:
        return None

    if not row or not row["lat"] or (row["cnt"] or 0) < 1:
        return None
    if row["std_lat"] < std_threshold and row["std_lon"] < std_threshold:
        return float(row["lat"]), float(row["lon"])
    return None


async def _geocode_db(query: str) -> "tuple[float, float] | None":
    """Fuzzy match query against DB addresses/counties, return centroid if confident.
    Only tries plural/singular variants if no exact matches found first."""
    term = f"%{query.strip()}%"
    row = await db_pool.fetchrow("""
        SELECT
            COUNT(*)            AS match_count,
            AVG(latitude)       AS lat,
            AVG(longitude)      AS lon
        FROM properties
        WHERE latitude IS NOT NULL
          AND (address ILIKE $1 OR county ILIKE $1)
    """, term)

    # If we have enough matches with the original query, return those coordinates
    if row and row["match_count"] >= MIN_DB_MATCHES:
        return float(row["lat"]), float(row["lon"])

    # Only try plural → singular fallback if original query returned 0 results
    # This prevents "Elm Gardens" from matching "Elm Garden" if both exist
    if row and row["match_count"] == 0:
        # Try stripping trailing 's' for plural → singular (lawns → lawn)
        if query.lower().endswith('s') and not query.lower().endswith('ss'):
            singular_query = query[:-1]
            singular_term = f"%{singular_query.strip()}%"
            row = await db_pool.fetchrow("""
                SELECT
                    COUNT(*)            AS match_count,
                    AVG(latitude)       AS lat,
                    AVG(longitude)      AS lon
                FROM properties
                WHERE latitude IS NOT NULL
                  AND (address ILIKE $1 OR county ILIKE $1)
            """, singular_term)
            if row and row["match_count"] >= MIN_DB_MATCHES:
                return float(row["lat"]), float(row["lon"])

    return None


DUBLIN_COUNTIES = {"dublin", "co. dublin", "county dublin", "co dublin"}
COUNTY_KEYWORDS = re.compile(
    r"\b(cork|galway|limerick|waterford|kilkenny|wexford|wicklow|kildare|meath|louth|"
    r"cavan|monaghan|donegal|sligo|mayo|roscommon|leitrim|longford|westmeath|offaly|"
    r"laois|tipperary|clare|kerry)\b",
    re.IGNORECASE,
)
# Dublin city centre — used as proximity bias when no county is mentioned
DUBLIN_CENTER = "-6.2603,53.3498"


async def _proximity_hint_from_query(query: str) -> Optional[str]:
    """Extract a precise proximity hint by looking up the road/area part of the query
    in the property DB.

    For "27 Elm Court, Merrion Road" the trailing part "Merrion Road" has a tight
    cluster of DB records in Ballsbridge D4 — that centroid beats the generic Dublin
    centre as a Mapbox proximity hint.

    Returns a "lon,lat" string if a tight cluster (stddev < ~3km) is found with
    at least 5 matching records, otherwise None.
    """
    parts = [p.strip() for p in query.split(",") if p.strip()]
    if len(parts) < 2:
        return None

    # Try trailing parts: last part alone, then last two parts combined
    candidates = [parts[-1]]
    if len(parts) >= 3:
        candidates.append(f"{parts[-2]}, {parts[-1]}")

    for candidate in candidates:
        if len(candidate) < 4:
            continue
        try:
            row = await asyncio.wait_for(
                db_pool.fetchrow("""
                    SELECT AVG(longitude) AS lon, AVG(latitude) AS lat,
                           COUNT(*)       AS cnt,
                           STDDEV(longitude) AS std_lon,
                           STDDEV(latitude)  AS std_lat
                    FROM properties
                    WHERE latitude IS NOT NULL AND address ILIKE $1
                """, f"%{candidate}%"),
                timeout=2.0,
            )
        except Exception:
            return None
        if not row or (row["cnt"] or 0) < 5:
            continue
        std_lon = row["std_lon"] or 0
        std_lat = row["std_lat"] or 0
        # Accept only tight clusters (~3km radius at Irish latitudes)
        if std_lon < 0.05 and std_lat < 0.05:
            return f"{row['lon']:.6f},{row['lat']:.6f}"

    return None


async def _geocode_mapbox(
    query: str,
    client: httpx.AsyncClient,
    proximity: Optional[str] = None,
) -> "tuple[float, float] | None":
    """Resolve query via Mapbox Geocoding API, restricted to Ireland.
    Uses a caller-supplied proximity hint when available, otherwise falls back
    to Dublin city centre for queries with no county indicator."""
    if not MAPBOX_TOKEN:
        return None
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    params: dict = {
        "access_token": MAPBOX_TOKEN,
        "country": "ie",
        "limit": 1,
        "types": "place,locality,neighborhood,address,postcode",
    }
    if proximity:
        params["proximity"] = proximity
    else:
        q_lower = query.lower()
        has_county = COUNTY_KEYWORDS.search(q_lower) or any(c in q_lower for c in DUBLIN_COUNTIES)
        if not has_county:
            params["proximity"] = DUBLIN_CENTER
    try:
        resp = await client.get(url, params=params, timeout=5.0)
        if resp.status_code != 200:
            return None
        features = resp.json().get("features", [])
        if not features:
            return None
        lon, lat = features[0]["center"]
        lat_f, lon_f = float(lat), float(lon)
        # Validate coordinates are in Ireland
        if _is_in_ireland(lat_f, lon_f):
            return lat_f, lon_f
        else:
            logger.warning(f"Mapbox returned out-of-bounds coordinates for {query!r}: {lat_f}, {lon_f}")
            return None
    except Exception as e:
        logger.warning(f"Mapbox geocoding failed: {type(e).__name__}: {e}")
        return None


async def _geocode_nominatim(
    query: str,
    client: httpx.AsyncClient,
) -> "tuple[float, float] | None":
    """Resolve query (address, place name, or eircode) via Nominatim.
    Returns (lat, lon) if successful, None otherwise.
    Nominatim returns results ordered by importance, so first result is usually correct."""
    try:
        # Nominatim search — add "Ireland" to avoid international matches
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{query.strip()} Ireland",
                "format": "json",
                "limit": 1,
                "addressdetails": 0,  # Faster response without full address breakdown
            },
            headers={"User-Agent": USER_AGENT},
            timeout=5.0,
        )
        if resp.status_code != 200:
            return None

        results = resp.json()
        if not results:
            return None

        lat = results[0].get("lat")
        lon = results[0].get("lon")

        if lat is not None and lon is not None:
            lat_f, lon_f = float(lat), float(lon)
            # Validate coordinates are in Ireland (prevents matching "Ireland" hamlet in UK)
            if _is_in_ireland(lat_f, lon_f):
                return lat_f, lon_f
            else:
                logger.warning(f"Nominatim returned out-of-bounds coordinates for {query!r}: {lat_f}, {lon_f}")
        return None
    except Exception as e:
        logger.debug(f"Nominatim geocoding failed for {query!r}: {e}")
        return None


async def _flag_bad_geocode(eircode: str):
    """Flag properties with this Eircode for priority re-geocoding.
    Fire-and-forget task to avoid blocking geocoding response."""
    try:
        await db_pool.execute("""
            UPDATE properties
            SET geocode_quality_issue = TRUE
            WHERE REPLACE(UPPER(eircode), ' ', '') = $1
              AND geocode_quality_issue = FALSE
        """, eircode.replace(' ', '').upper())
        logger.info(f"Flagged Eircode {eircode} for priority re-geocoding")
    except Exception as e:
        logger.error(f"Failed to flag bad geocode for {eircode}: {e}")


async def resolve_location(query: str, county: Optional[str] = None) -> "tuple[float, float, str]":
    """Return (lat, lon, source) for an address, eircode, or 'lat,lon' string.

    Resolution order:
      1. Raw coordinates passthrough
      2. Cache hit
      3. Routing key (D02, H91) → DB   (centroid of all properties with that Eircode prefix)
      4. Eircode → DB exact match      (fast indexed lookup with validation from properties table)
      5. Eircode → Reference table     (pre-computed Eircode centroids from 222k Eircodes)
      6. Token-based DB lookup         (tight clusters in known developments)
      7. Nominatim                     (OSM geocoder, importance-ranked results)
      8. Mapbox Geocoding API          (commercial fallback)
      9. Fuzzy DB ILIKE full-scan      (slow last resort)

    Source values: 'raw', 'cache', 'db_routing_key', 'db_exact', 'db_eircode_ref', 'nominatim', 'db_tokens', 'mapbox', 'db_fuzzy'
    """
    # 1. Raw coordinates
    coord_match = re.match(r"^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$", query.strip())
    if coord_match:
        return float(coord_match.group(1)), float(coord_match.group(2)), "raw"

    # 2. Cache hit (v3 namespace after prioritizing Nominatim for place names)
    cached = cache.get("geocode_v3", {"q": query})
    if cached is not None:
        return cached["lat"], cached["lon"], "cache"

    def _cache_and_return(lat: float, lon: float, source: str) -> "tuple[float, float, str]":
        cache.set("geocode_v3", {"q": query}, {"lat": lat, "lon": lon}, TTL_GEOCODE)
        return lat, lon, source

    # 3a. Routing key (3-char Eircode prefix like D02, H91) — return centroid of all properties with that prefix
    if _looks_like_routing_key(query):
        norm = query.strip().upper()
        rk_row = await db_pool.fetchrow("""
            SELECT AVG(latitude) AS lat, AVG(longitude) AS lon, COUNT(*) AS cnt
            FROM properties
            WHERE latitude IS NOT NULL
              AND REPLACE(UPPER(eircode), ' ', '') LIKE $1
        """, norm + "%")

        if rk_row and (rk_row["cnt"] or 0) >= 1:
            return _cache_and_return(float(rk_row["lat"]), float(rk_row["lon"]), "db_routing_key")

    # 3b. Eircode — fast indexed DB lookup with routing key validation
    if _looks_like_eircode(query):
        norm = _normalise_eircode(query)
        prefix = norm[:3]

        # Get routing key centroid for quality validation
        rk_row = await db_pool.fetchrow("""
            SELECT AVG(latitude) AS lat, AVG(longitude) AS lon, COUNT(*) AS cnt
            FROM properties
            WHERE latitude IS NOT NULL
              AND REPLACE(UPPER(eircode), ' ', '') LIKE $1
        """, prefix + "%")

        # Try exact eircode
        row = await db_pool.fetchrow("""
            SELECT AVG(latitude) AS lat, AVG(longitude) AS lon, COUNT(*) AS cnt
            FROM properties
            WHERE latitude IS NOT NULL
              AND REPLACE(UPPER(eircode), ' ', '') = $1
        """, norm)

        if row and (row["cnt"] or 0) >= 1:
            exact_lat, exact_lon = float(row["lat"]), float(row["lon"])
            # Validate: exact coordinates should be within ~5km of routing key centroid
            # Reject if too far away (indicates bad geocoding data)
            if rk_row and (rk_row["cnt"] or 0) >= 5:
                rk_lat, rk_lon = float(rk_row["lat"]), float(rk_row["lon"])
                # Rough distance check (0.05 degrees ≈ 5km at Irish latitudes)
                lat_diff = abs(exact_lat - rk_lat)
                lon_diff = abs(exact_lon - rk_lon)
                if lat_diff < 0.05 and lon_diff < 0.08:  # lon degrees are smaller at this latitude
                    return _cache_and_return(exact_lat, exact_lon, "db_exact")
                else:
                    logger.warning(f"Eircode {norm} coordinates ({exact_lat:.5f}, {exact_lon:.5f}) too far from routing key {prefix} centroid ({rk_lat:.5f}, {rk_lon:.5f}), using centroid instead")
                    # Flag properties with bad geocoding for priority re-geocoding
                    asyncio.create_task(_flag_bad_geocode(norm))
            else:
                # No routing key data to validate against, trust the exact match
                return _cache_and_return(exact_lat, exact_lon, "db_exact")

        # Exact match not in PPR or failed validation — try eircode_reference table
        # This table contains pre-computed Eircode centroids from all PPR properties with Eircodes
        ref_row = await db_pool.fetchrow("""
            SELECT latitude, longitude, property_count, source
            FROM eircode_reference
            WHERE eircode = $1
        """, norm)

        if ref_row:
            return _cache_and_return(float(ref_row["latitude"]), float(ref_row["longitude"]), "db_eircode_ref")

        # Still no match — use routing key centroid (already fetched above)
        if rk_row and (rk_row["cnt"] or 0) >= 1:
            return _cache_and_return(float(rk_row["lat"]), float(rk_row["lon"]), "db_routing_key")

    # 4. Token-based DB lookup — matches addresses by significant words.
    # Handles abbreviation mismatches (Rd vs Road) and finds tight clusters in known
    # Irish developments before falling through to external geocoders.
    result = await _geocode_db_tokens(query)
    if result:
        return _cache_and_return(*result, "db_tokens")

    # 5. Nominatim — free OSM geocoder with good Irish coverage. Returns results ordered
    # by importance, so first result is usually the primary settlement/address.
    # Better than Mapbox for place names (avoids sub-locality confusion like Barna).
    async with httpx.AsyncClient() as client:
        result = await _geocode_nominatim(query, client)
        if result:
            return _cache_and_return(*result, "nominatim")

    # 6. Mapbox — commercial geocoder, fallback if Nominatim fails.
    # Expand abbreviations first (Rd→Road, Ave→Avenue etc) so Mapbox resolves correctly.
    mapbox_query = _expand_abbreviations(query)
    q_lower = query.lower()
    has_county_context = COUNTY_KEYWORDS.search(q_lower) or any(c in q_lower for c in DUBLIN_COUNTIES)
    async with httpx.AsyncClient() as client:
        proximity = await _proximity_hint_from_query(mapbox_query)
        # Only append county context for street addresses (start with a number).
        # Bare area names like "Rathmines" must be sent as-is — appending ", Dublin"
        # causes Mapbox to misread them (e.g. "Rathmines, Dublin" → Dublin Road, Wicklow).
        is_street_address = bool(_STARTS_WITH_NUMBER.match(query.strip()))
        if not proximity and not has_county_context and is_street_address:
            mapbox_query = mapbox_query + (f", {county}" if county else ", Dublin")
        result = await _geocode_mapbox(mapbox_query, client, proximity=proximity)
        if result:
            return _cache_and_return(*result, "mapbox")

    # 7. Fuzzy DB ILIKE fallback — only reached if all external geocoders fail
    result = await _geocode_db(query)
    if result:
        return _cache_and_return(*result, "db_fuzzy")

    raise HTTPException(status_code=404, detail=f"Could not geocode: {query}")


# ---------------------------------------------------------------------------
# Background eircode enrichment — demand-driven via Autoaddress.com
# ---------------------------------------------------------------------------

async def _aa_lookup_one(client: httpx.AsyncClient, address: str, county: str) -> "str | None":
    """Single Autoaddress lookup: autocomplete → lookup → postcode."""
    query = f"{address}, {county}" if county else address
    headers = {
        "Authorization": f"Bearer {AUTOADDRESS_KEY}",
        "User-Agent": USER_AGENT,
    }
    try:
        r = await client.get(AA_AUTOCOMPLETE,
                             params={"key": AUTOADDRESS_KEY, "address": query},
                             headers=headers, timeout=8.0)
        if r.status_code != 200:
            return None
        options = r.json().get("options", [])
        if not options:
            return None
        lookup_href = options[0]["link"]["href"]
        r2 = await client.get(lookup_href, headers=headers, timeout=8.0)
        if r2.status_code != 200:
            return None
        postcode = r2.json().get("address", {}).get("postcode", {}).get("value", "").strip()
        return postcode or None
    except Exception as e:
        logger.debug(f"AA lookup failed for {query!r}: {e}")
        return None


async def _enrich_eircodes(props: list[dict]) -> None:
    """Fire-and-forget: enrich up to 5 eircode-less properties per search result."""
    if not AUTOADDRESS_KEY:
        return
    targets = [p for p in props if not p.get("eircode") and p.get("address")][:5]
    if not targets:
        return

    async def _enrich_one(prop: dict) -> None:
        async with _aa_semaphore:
            eircode = await _aa_lookup_one(client, prop["address"], prop.get("county") or "")
            if eircode:
                try:
                    await db_pool.execute(
                        "UPDATE properties SET eircode = $1 WHERE id = $2 AND eircode IS NULL",
                        eircode, prop["id"]
                    )
                    logger.info(f"Enriched eircode for ID {prop['id']}: {eircode}")
                except Exception as e:
                    logger.debug(f"Eircode DB write failed for ID {prop['id']}: {e}")

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[_enrich_one(p) for p in targets], return_exceptions=True)


async def _log_search_query(
    query: str,
    resolved_lat: float,
    resolved_lon: float,
    radius_km: float,
    result_count: int,
    elapsed_ms: int,
    county_filter: Optional[str],
    min_price: Optional[int],
    max_price: Optional[int],
    min_year: Optional[int],
    max_year: Optional[int],
    geocode_source: str,
    user_agent: Optional[str],
    ip_address: Optional[str],
) -> None:
    """Log search query to search_log table for analytics. Fire and forget — errors are ignored."""
    try:
        await db_pool.execute("""
            INSERT INTO search_log (
                query, resolved_lat, resolved_lon, radius_km, result_count, elapsed_ms,
                county_filter, min_price, max_price, min_year, max_year,
                geocode_source, user_agent, ip_address
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """, query, resolved_lat, resolved_lon, radius_km, result_count, elapsed_ms,
            county_filter, min_price, max_price, min_year, max_year,
            geocode_source, user_agent, ip_address)
    except Exception as e:
        logger.debug(f"Search query logging failed: {e}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/geocode")
async def geocode(
    request: Request,
    q: str = Query(..., description="Address, Eircode, or 'lat,lon'"),
    county: Optional[str] = None,
):
    """Resolve a query to (lat, lon) without running a property search."""
    _rate_limit_check(request, 60, "geocode")
    lat, lon, _source = await resolve_location(q, county=county)
    return {"lat": lat, "lon": lon}


@app.get("/search")
async def search(
    request: Request,
    q: str = Query(..., description="Address, Eircode, or 'lat,lon'"),
    radius_km: float = Query(1.0, ge=0.1, le=20.0, description="Search radius in km"),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    county: Optional[str] = None,
    limit: int = Query(200, ge=1, le=500),
    sort: str = Query("date", regex="^(date|distance)$"),
):
    start_time = time.time()
    _rate_limit_check(request, 60, "search")
    cache_params = {"q": q, "radius_km": radius_km, "min_price": min_price,
                    "max_price": max_price, "min_year": min_year, "max_year": max_year,
                    "county": county, "limit": limit, "sort": sort}
    cached = cache.get("search", cache_params)
    if cached is not None:
        return cached

    lat, lon, geocode_source = await resolve_location(q, county=county)

    # Strategy: Try original radius with county filter first.
    # If no results at original radius AND county filter is set, retry without county filter before expanding radius.
    # This ensures Nobber (Meath) with county=Dublin gets Meath results, not distant Dublin results.
    MIN_RESULTS = 5
    MAX_RADIUS_KM = 20.0
    RADIUS_INCREMENTS = [radius_km, radius_km * 2, radius_km * 3, radius_km * 5, radius_km * 10, MAX_RADIUS_KM]

    rows = []
    actual_radius = radius_km
    radius_expanded = False
    county_filter_removed = False

    # Try with county filter first (if provided)
    if county:
        filters = ["ST_DWithin(geog, ST_MakePoint($2, $1)::geography, $3)"]
        params  = [lat, lon, radius_km * 1000]
        idx     = 4

        if min_price is not None:
            filters.append(f"price >= ${idx}"); params.append(min_price); idx += 1
        if max_price is not None:
            filters.append(f"price <= ${idx}"); params.append(max_price); idx += 1
        if min_year is not None:
            filters.append(f"EXTRACT(YEAR FROM sale_date) >= ${idx}"); params.append(min_year); idx += 1
        if max_year is not None:
            filters.append(f"EXTRACT(YEAR FROM sale_date) <= ${idx}"); params.append(max_year); idx += 1
        filters.append(f"LOWER(county) = LOWER(${idx})"); params.append(county); idx += 1

        where = " AND ".join(filters)
        params.append(limit)

        rows = await db_pool.fetch(f"""
            SELECT
                id, sale_date, address, county, eircode, price,
                not_full_market_price, vat_exclusive, description,
                size_description, latitude, longitude,
                routing_key, bedrooms, property_type,
                ST_Distance(geog, ST_MakePoint($2, $1)::geography) AS distance_m
            FROM properties
            WHERE {where}
            ORDER BY {("distance_m" if sort == "distance" else "sale_date DESC, distance_m")}
            LIMIT ${idx}
        """, *params)

        # If no results with county filter at original radius, remove filter and try again
        if len(rows) == 0:
            logger.info(f"No results at {radius_km}km with county filter '{county}' for query '{q}', removing county filter")
            county_filter_removed = True

    # Main search loop (with or without county filter)
    if len(rows) < MIN_RESULTS:
        for attempt_radius in RADIUS_INCREMENTS:
            if attempt_radius > MAX_RADIUS_KM:
                attempt_radius = MAX_RADIUS_KM

            filters = ["ST_DWithin(geog, ST_MakePoint($2, $1)::geography, $3)"]
            params  = [lat, lon, attempt_radius * 1000]
            idx     = 4

            if min_price is not None:
                filters.append(f"price >= ${idx}"); params.append(min_price); idx += 1
            if max_price is not None:
                filters.append(f"price <= ${idx}"); params.append(max_price); idx += 1
            if min_year is not None:
                filters.append(f"EXTRACT(YEAR FROM sale_date) >= ${idx}"); params.append(min_year); idx += 1
            if max_year is not None:
                filters.append(f"EXTRACT(YEAR FROM sale_date) <= ${idx}"); params.append(max_year); idx += 1
            # Only add county filter if not removed
            if county and not county_filter_removed:
                filters.append(f"LOWER(county) = LOWER(${idx})"); params.append(county); idx += 1

            where = " AND ".join(filters)
            params.append(limit)

            rows = await db_pool.fetch(f"""
                SELECT
                    id, sale_date, address, county, eircode, price,
                    not_full_market_price, vat_exclusive, description,
                    size_description, latitude, longitude,
                    routing_key, bedrooms, property_type,
                    ST_Distance(geog, ST_MakePoint($2, $1)::geography) AS distance_m
                FROM properties
                WHERE {where}
                ORDER BY {("distance_m" if sort == "distance" else "sale_date DESC, distance_m")}
                LIMIT ${idx}
            """, *params)

            actual_radius = attempt_radius

            # If we have enough results or reached max radius, stop expanding
            if len(rows) >= MIN_RESULTS or attempt_radius >= MAX_RADIUS_KM:
                if attempt_radius != radius_km:
                    radius_expanded = True
                    logger.info(f"Auto-expanded radius from {radius_km}km to {actual_radius}km for query '{q}' "
                              f"(found {len(rows)} results)")
                break

    result = {
        "center": {"lat": lat, "lon": lon},
        "radius_km": actual_radius,
        "radius_expanded": radius_expanded,
        "county_filter_removed": county_filter_removed,
        "requested_radius_km": radius_km,
        "count": len(rows),
        "results": [dict(r) for r in rows],
    }
    cache.set("search", cache_params, result, TTL_SEARCH)

    # Log search query for analytics (fire and forget)
    elapsed_ms = int((time.time() - start_time) * 1000)
    asyncio.create_task(_log_search_query(
        query=q,
        resolved_lat=lat,
        resolved_lon=lon,
        radius_km=radius_km,
        result_count=len(rows),
        elapsed_ms=elapsed_ms,
        county_filter=county,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        geocode_source=geocode_source,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    ))

    # Enrich missing eircodes in the background — does not block the response
    asyncio.create_task(_enrich_eircodes(result["results"]))

    return result


class PolygonSearchRequest(BaseModel):
    coordinates: list[list[float]] = Field(..., description="List of [lat, lon] coordinates forming a polygon")
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    limit: int = Field(50, ge=1, le=50)


@app.post("/search/polygon")
async def search_polygon(
    request: Request,
    search_request: PolygonSearchRequest,
):
    """Search properties within a polygon defined by coordinates."""
    _rate_limit_check(request, 30, "polygon_search")

    # Validate polygon has at least 3 points
    if len(search_request.coordinates) < 3:
        raise HTTPException(status_code=400, detail="Polygon must have at least 3 coordinates")

    # Build PostGIS polygon from coordinates
    # PostGIS expects lon,lat order, not lat,lon
    points_str = ", ".join([f"{lon} {lat}" for lat, lon in search_request.coordinates])
    polygon_wkt = f"POLYGON(({points_str}))"

    # Build query
    filters = [f"ST_Within(geog::geometry, ST_GeomFromText('{polygon_wkt}', 4326))"]
    params: list = []
    idx = 1

    if search_request.min_price is not None:
        filters.append(f"price >= ${idx}")
        params.append(search_request.min_price)
        idx += 1
    if search_request.max_price is not None:
        filters.append(f"price <= ${idx}")
        params.append(search_request.max_price)
        idx += 1
    if search_request.min_year is not None:
        filters.append(f"EXTRACT(YEAR FROM sale_date) >= ${idx}")
        params.append(search_request.min_year)
        idx += 1
    if search_request.max_year is not None:
        filters.append(f"EXTRACT(YEAR FROM sale_date) <= ${idx}")
        params.append(search_request.max_year)
        idx += 1

    where = " AND ".join(filters)
    params.append(search_request.limit)

    rows = await db_pool.fetch(f"""
        SELECT
            id, sale_date, address, county, eircode, price,
            not_full_market_price, vat_exclusive, description,
            size_description, latitude, longitude,
            routing_key, bedrooms, property_type
        FROM properties
        WHERE {where}
        ORDER BY sale_date DESC
        LIMIT ${idx}
    """, *params)

    results = [dict(r) for r in rows]

    logger.info(f"Polygon search: {len(results)} properties found within polygon")

    return {
        "count": len(results),
        "results": results,
    }


@app.get("/trends")
async def trends(
    request: Request,
    q: Optional[str] = None,
    radius_km: float = Query(5.0, ge=0.5, le=50.0),
    county: Optional[str] = None,
):
    """Median price by year, with optional geographic or county filter."""
    _rate_limit_check(request, 60, "trends")
    # Cache county-only trends (used heavily by content pages)
    cache_params = {"q": q, "radius_km": radius_km, "county": county}
    if not q:
        cached = cache.get("trends", cache_params)
        if cached is not None:
            return cached

    filters = ["not_full_market_price = FALSE"]
    params: list = []
    idx = 1

    if q:
        lat, lon, _source = await resolve_location(q)
        filters.append(f"ST_DWithin(geog, ST_MakePoint(${idx+1}, ${idx})::geography, ${idx+2})")
        params.extend([lat, lon, radius_km * 1000])
        idx += 3
    elif county:
        filters.append(f"LOWER(county) = LOWER(${idx})")
        params.append(county)
        idx += 1

    where = " AND ".join(filters)

    rows = await db_pool.fetch(f"""
        SELECT
            EXTRACT(YEAR FROM sale_date)::int AS year,
            COUNT(*)                          AS count,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::numeric, 0) AS median_price,
            ROUND(AVG(price)::numeric, 0)     AS avg_price,
            MIN(price)                        AS min_price,
            MAX(price)                        AS max_price
        FROM properties
        WHERE {where}
        GROUP BY year
        ORDER BY year
    """, *params)

    result = {"data": [dict(r) for r in rows]}
    if not q:
        cache.set("trends", cache_params, result, TTL_TRENDS)
    return result


@app.get("/eircode")
async def eircode_search(
    request: Request,
    code: str = Query(..., description="Routing key (e.g. D04) or full Eircode (e.g. D04 XY12)"),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    limit: int = Query(500, ge=1, le=2000),
):
    """
    Return all sales matching an Eircode or routing key prefix, with summary stats.
    Routing key (3 chars): returns all sales whose eircode starts with that prefix.
    Full Eircode (7 chars): returns sales at that exact address code.
    """
    _rate_limit_check(request, 60, "eircode")
    norm = _normalise_eircode(code)
    if not norm:
        raise HTTPException(status_code=400, detail="code must not be empty")

    cache_params = {"code": norm, "min_price": min_price, "max_price": max_price,
                    "min_year": min_year, "max_year": max_year, "limit": limit}
    cached = cache.get("eircode", cache_params)
    if cached is not None:
        return cached

    is_full = len(norm) >= 5  # full eircode vs routing key prefix

    filters = [
        "REPLACE(UPPER(eircode), ' ', '') = $1" if is_full
        else "REPLACE(UPPER(eircode), ' ', '') LIKE $1"
    ]
    params = [norm if is_full else norm[:3] + "%"]
    idx = 2

    if min_price is not None:
        filters.append(f"price >= ${idx}"); params.append(min_price); idx += 1
    if max_price is not None:
        filters.append(f"price <= ${idx}"); params.append(max_price); idx += 1
    if min_year is not None:
        filters.append(f"EXTRACT(YEAR FROM sale_date) >= ${idx}"); params.append(min_year); idx += 1
    if max_year is not None:
        filters.append(f"EXTRACT(YEAR FROM sale_date) <= ${idx}"); params.append(max_year); idx += 1

    where = " AND ".join(filters)

    rows = await db_pool.fetch(f"""
        SELECT
            id, sale_date, address, county, eircode, price,
            not_full_market_price, vat_exclusive, description,
            size_description, latitude, longitude,
            routing_key, bedrooms, property_type
        FROM properties
        WHERE {where}
        ORDER BY sale_date DESC
        LIMIT ${idx}
    """, *params, limit)

    # Summary stats (unaffected by limit)
    stats_row = await db_pool.fetchrow(f"""
        SELECT
            COUNT(*)                                                          AS total_count,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::numeric, 0) AS median_price,
            ROUND(AVG(price)::numeric, 0)                                    AS avg_price,
            MIN(sale_date)                                                    AS earliest_sale,
            MAX(sale_date)                                                    AS latest_sale
        FROM properties
        WHERE {where}
          AND not_full_market_price = FALSE
    """, *params)

    result = {
        "code":       norm[:3] if not is_full else norm,
        "match_type": "full_eircode" if is_full else "routing_key",
        "stats":      dict(stats_row),
        "count":      len(rows),
        "results":    [dict(r) for r in rows],
    }
    cache.set("eircode", cache_params, result, TTL_EIRCODE)
    return result


@app.get("/routing-keys")
async def routing_keys_list(
    request: Request,
    limit: int = Query(100, ge=1, le=200),
    sort: str = Query("count", regex="^(count|name)$"),
):
    """
    List all Eircode routing keys with statistics and centroids.
    Used for autocomplete, area browse, and analytics.
    """
    _rate_limit_check(request, 60, "routing_keys")

    cache_params = {"limit": limit, "sort": sort}
    cached = cache.get("routing_keys", cache_params)
    if cached is not None:
        return cached

    order_by = "property_count DESC" if sort == "count" else "routing_key"

    rows = await db_pool.fetch(f"""
        SELECT
            routing_key,
            primary_county,
            property_count,
            counties,
            earliest_sale,
            latest_sale,
            median_price,
            centroid_lat,
            centroid_lon,
            geocoded_count,
            geocoded_pct
        FROM routing_key_stats
        ORDER BY {order_by}
        LIMIT $1
    """, limit)

    result = {
        "count": len(rows),
        "routing_keys": [dict(r) for r in rows],
    }
    cache.set("routing_keys", cache_params, result, TTL_EIRCODE)  # 1 hour cache
    return result


@app.get("/routing-keys/autocomplete")
async def routing_keys_autocomplete(
    request: Request,
    prefix: str = Query(..., min_length=1, max_length=3, description="Routing key prefix (1-3 chars)"),
):
    """
    Autocomplete Eircode routing keys as user types.
    Returns matching routing keys with county context and property counts.
    """
    _rate_limit_check(request, 120, "routing_keys_autocomplete")

    prefix_upper = prefix.upper().strip()
    cache_params = {"prefix": prefix_upper}
    cached = cache.get("routing_keys_autocomplete", cache_params)
    if cached is not None:
        return cached

    rows = await db_pool.fetch("""
        SELECT
            routing_key,
            primary_county,
            property_count,
            centroid_lat,
            centroid_lon,
            geocoded_pct
        FROM routing_key_stats
        WHERE routing_key LIKE $1 || '%'
        ORDER BY property_count DESC
        LIMIT 20
    """, prefix_upper)

    result = {
        "prefix": prefix_upper,
        "count": len(rows),
        "matches": [dict(r) for r in rows],
    }
    cache.set("routing_keys_autocomplete", cache_params, result, 3600)  # 1 hour
    return result


@app.get("/counties")
async def counties(request: Request):
    _rate_limit_check(request, 30, "counties")
    cached = cache.get("counties", {})
    if cached is not None:
        return cached

    rows = await db_pool.fetch("""
        SELECT county, COUNT(*) as count
        FROM properties
        WHERE county IS NOT NULL
        GROUP BY county
        ORDER BY county
    """)
    result = [dict(r) for r in rows]
    cache.set("counties", {}, result, TTL_COUNTIES)
    return result


# ---------------------------------------------------------------------------
# Manual geocoding endpoints — admin workflow for hard-to-geocode addresses
# ---------------------------------------------------------------------------


@app.get("/geocoding-queue/next")
async def get_next_property_to_geocode(request: Request):
    """
    Return the next high-priority property that needs manual geocoding.
    Priority order: price (>€500k first), then recency.
    Returns properties without coordinates (latitude IS NULL).
    """
    _rate_limit_check(request, 60, "geocoding_queue")
    row = await db_pool.fetchrow("""
        SELECT id, sale_date, address, county, eircode, price,
               not_full_market_price, vat_exclusive, description,
               size_description, latitude, longitude
        FROM properties
        WHERE latitude IS NULL
        ORDER BY (price > 500000) DESC, sale_date DESC
        LIMIT 1
    """)
    if not row:
        return {"property": None}
    return {"property": dict(row)}


class GeocodeUpdatePayload(BaseModel):
    property_id: int = Field(..., description="Property ID to update")
    latitude: float = Field(..., ge=51.4, le=55.5, description="Latitude (Ireland bounds)")
    longitude: float = Field(..., ge=-10.7, le=-5.4, description="Longitude (Ireland bounds)")
    address: Optional[str] = Field(None, max_length=500, description="Updated address")
    eircode: Optional[str] = Field(None, max_length=10, description="Updated Eircode")


@app.post("/geocoding-queue/update")
async def update_property_geocode(request: Request, payload: GeocodeUpdatePayload):
    """
    Manually assign geocode coordinates to a property.
    Updates latitude, longitude, geography column, and optionally address/eircode.
    """
    _rate_limit_check(request, 10, "geocoding_queue_update")
    try:
        # Update coordinates always, plus optional address/eircode
        if payload.address and payload.eircode:
            # Update all fields
            result = await db_pool.execute("""
                UPDATE properties
                SET latitude = $1,
                    longitude = $2,
                    geog = ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    address = $3,
                    eircode = $4
                WHERE id = $5
            """, payload.latitude, payload.longitude, payload.address.strip(),
                 payload.eircode.strip().upper(), payload.property_id)
        elif payload.address:
            # Update coords + address
            result = await db_pool.execute("""
                UPDATE properties
                SET latitude = $1,
                    longitude = $2,
                    geog = ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    address = $3
                WHERE id = $4
            """, payload.latitude, payload.longitude, payload.address.strip(), payload.property_id)
        elif payload.eircode:
            # Update coords + eircode
            result = await db_pool.execute("""
                UPDATE properties
                SET latitude = $1,
                    longitude = $2,
                    geog = ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    eircode = $3
                WHERE id = $4
            """, payload.latitude, payload.longitude, payload.eircode.strip().upper(), payload.property_id)
        else:
            # Update coords only
            result = await db_pool.execute("""
                UPDATE properties
                SET latitude = $1,
                    longitude = $2,
                    geog = ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
                WHERE id = $3
            """, payload.latitude, payload.longitude, payload.property_id)

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Property not found")

        logger.info(f"Manual geocode applied to property {payload.property_id}: "
                   f"({payload.latitude}, {payload.longitude})"
                   f"{', address updated' if payload.address else ''}"
                   f"{', eircode updated' if payload.eircode else ''}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual geocode update failed: {e}")
        raise HTTPException(status_code=500, detail="Could not update property")


@app.post("/geocoding-queue/skip")
async def skip_property_geocode(request: Request, property_id: int = Query(...)):
    """
    Skip manual geocoding for this property — keeps needs_geocoding = TRUE
    but could be extended to flag as 'skipped' if needed.
    """
    _rate_limit_check(request, 10, "geocoding_queue_skip")
    row = await db_pool.fetchrow("SELECT id FROM properties WHERE id = $1", property_id)
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")
    logger.info(f"Skipped manual geocode for property {property_id}")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Contact / Feedback forms — stored in the submissions DB table
# ---------------------------------------------------------------------------


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def _validate_optional_email(v: str) -> str:
    """Allow blank; validate format when non-empty."""
    if v and not _EMAIL_RE.match(v):
        raise ValueError("Invalid email address")
    return v


class FeedbackPayload(BaseModel):
    datasets:  str = Field("", max_length=5000)
    comments:  str = Field("", max_length=5000)
    name:      str = Field("", max_length=200)
    email:     str = Field("", max_length=200)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v): return _validate_optional_email(v)


class ContactPayload(BaseModel):
    message:       str  = Field("", max_length=5000)
    price_updates: bool = False
    name:          str  = Field("", max_length=200)
    email:         str  = Field("", max_length=200)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v): return _validate_optional_email(v)


@app.post("/feedback")
async def submit_feedback(request: Request, payload: FeedbackPayload):
    _rate_limit_check(request, 5, "feedback")
    try:
        await db_pool.execute("""
            INSERT INTO submissions (kind, name, email, datasets, comments)
            VALUES ('feedback', $1, $2, $3, $4)
        """, payload.name or None, payload.email or None,
             payload.datasets or None, payload.comments or None)
        logger.info("Feedback submission saved")
    except Exception as e:
        logger.error(f"Feedback DB write failed: {e}")
        raise HTTPException(status_code=500, detail="Could not save feedback")
    return {"ok": True}


@app.post("/contact")
async def submit_contact(request: Request, payload: ContactPayload):
    _rate_limit_check(request, 5, "contact")
    try:
        await db_pool.execute("""
            INSERT INTO submissions (kind, name, email, message, price_updates)
            VALUES ('contact', $1, $2, $3, $4)
        """, payload.name or None, payload.email or None,
             payload.message or None, payload.price_updates)
        logger.info("Contact submission saved")
    except Exception as e:
        logger.error(f"Contact DB write failed: {e}")
        raise HTTPException(status_code=500, detail="Could not save message")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Email alerts — property notification subscriptions
# ---------------------------------------------------------------------------


class EmailAlertSubscription(BaseModel):
    email: str = Field(..., max_length=255)
    address: str = Field(..., max_length=500)
    radius_km: float = Field(2.0, ge=0.5, le=20.0)
    county: Optional[str] = Field(None, max_length=100)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError('Invalid email address')
        return v.lower().strip()


@app.post("/email-alerts/subscribe")
async def subscribe_email_alert(
    request: Request,
    subscription: EmailAlertSubscription,
):
    """
    Subscribe to email alerts for properties matching search criteria.
    Stores subscription in email_alerts table and sends confirmation email.
    """
    _rate_limit_check(request, 10, "email_alerts_subscribe")

    try:
        from email_service import send_confirmation_email

        unsubscribe_token = None

        # Check if email already has an active subscription for this address
        existing = await db_pool.fetchrow("""
            SELECT id, is_active, unsubscribe_token
            FROM email_alerts
            WHERE email = $1 AND address = $2
            ORDER BY created_at DESC
            LIMIT 1
        """, subscription.email, subscription.address)

        if existing:
            unsubscribe_token = existing['unsubscribe_token']
            if existing['is_active']:
                # Update existing active subscription
                await db_pool.execute("""
                    UPDATE email_alerts
                    SET radius_km = $1,
                        county = $2,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, subscription.radius_km, subscription.county, existing['id'])
                logger.info(f"Updated email alert subscription for {subscription.email}")
            else:
                # Reactivate inactive subscription
                await db_pool.execute("""
                    UPDATE email_alerts
                    SET is_active = TRUE,
                        radius_km = $1,
                        county = $2,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, subscription.radius_km, subscription.county, existing['id'])
                logger.info(f"Reactivated email alert subscription for {subscription.email}")
        else:
            # Create new subscription and get the token
            row = await db_pool.fetchrow("""
                INSERT INTO email_alerts (email, address, radius_km, county)
                VALUES ($1, $2, $3, $4)
                RETURNING unsubscribe_token
            """, subscription.email, subscription.address, subscription.radius_km,
                 subscription.county)
            unsubscribe_token = row['unsubscribe_token']
            logger.info(f"Created new email alert subscription for {subscription.email}")

        # Fetch recent properties to include in confirmation email
        recent_properties = []
        try:
            # Geocode the address to get lat/lon (use substring match to find properties containing the search term)
            geocode_result = await db_pool.fetchrow("""
                SELECT latitude, longitude
                FROM properties
                WHERE address ILIKE '%' || $1 || '%'
                  AND latitude IS NOT NULL
                LIMIT 1
            """, subscription.address)

            if geocode_result and geocode_result['latitude']:
                lat = geocode_result['latitude']
                lon = geocode_result['longitude']

                # Find recent 10 properties matching criteria
                query = """
                    SELECT id, address, price, sale_date, county
                    FROM properties
                    WHERE geog IS NOT NULL
                      AND ST_DWithin(geog, ST_MakePoint($1, $2)::geography, $3 * 1000)
                      AND not_full_market_price = FALSE
                """
                params = [lon, lat, subscription.radius_km]

                if subscription.county:
                    query += " AND county = $4"
                    params.append(subscription.county)

                query += " ORDER BY sale_date DESC LIMIT 10"

                rows = await db_pool.fetch(query, *params)

                for row in rows:
                    recent_properties.append({
                        "id": row['id'],
                        "address": row['address'],
                        "price": float(row['price']) if row['price'] else 0,
                        "sale_date": row['sale_date'].strftime("%Y-%m-%d") if row['sale_date'] else "",
                        "county": row['county'] or "",
                    })

        except Exception as geocode_error:
            logger.warning(f"Could not fetch recent properties for confirmation email: {geocode_error}")
            # Continue without properties

        # Send confirmation email (async, don't block on failure)
        try:
            send_confirmation_email(
                email=subscription.email,
                address=subscription.address,
                radius_km=subscription.radius_km,
                county=subscription.county,
                unsubscribe_token=unsubscribe_token,
                properties=recent_properties
            )
        except Exception as email_error:
            logger.error(f"Failed to send confirmation email (subscription still active): {email_error}")
            # Don't fail the subscription if email fails

        return {
            "ok": True,
            "message": "Successfully subscribed to email alerts"
        }

    except Exception as e:
        logger.error(f"Email alert subscription failed: {e}")
        raise HTTPException(status_code=500, detail="Could not create subscription")


@app.post("/email-alerts/unsubscribe/{token}")
async def unsubscribe_email_alert(
    request: Request,
    token: str,
):
    """
    Unsubscribe from email alerts using the unsubscribe token.
    """
    _rate_limit_check(request, 10, "email_alerts_unsubscribe")

    try:
        result = await db_pool.execute("""
            UPDATE email_alerts
            SET is_active = FALSE
            WHERE unsubscribe_token = $1::uuid AND is_active = TRUE
        """, token)

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Subscription not found or already unsubscribed")

        logger.info(f"Unsubscribed email alert with token {token[:8]}...")
        return {"ok": True, "message": "Successfully unsubscribed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email alert unsubscribe failed: {e}")
        raise HTTPException(status_code=500, detail="Could not unsubscribe")


@app.get("/email-alerts/active")
async def get_active_email_alerts(request: Request):
    """
    Get all active email alert subscriptions.
    For admin/cron use to send out alerts.
    """
    _rate_limit_check(request, 10, "email_alerts_active")

    rows = await db_pool.fetch("""
        SELECT id, email, address, radius_km, county,
               created_at, last_sent_at, unsubscribe_token
        FROM email_alerts
        WHERE is_active = TRUE
        ORDER BY created_at DESC
    """)

    return [dict(r) for r in rows]


@app.post("/cron/send-monthly-alerts")
async def cron_send_monthly_alerts(request: Request, authorization: Optional[str] = None):
    """
    Cron endpoint to send monthly property alerts.
    Protected by CRON_SECRET environment variable.
    Called by GitHub Actions on 1st of each month.
    """
    # Check authorization
    cron_secret = os.getenv("CRON_SECRET")
    if cron_secret:
        auth_header = request.headers.get("Authorization", "")
        provided_secret = auth_header.replace("Bearer ", "").strip()
        if provided_secret != cron_secret:
            logger.warning(f"Unauthorized cron attempt from {request.client.host}")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        from email_service import send_monthly_digest

        # Get all active subscriptions
        subscriptions = await db_pool.fetch("""
            SELECT id, email, address, radius_km, county, created_at, last_sent_at, unsubscribe_token
            FROM email_alerts
            WHERE is_active = TRUE
            ORDER BY created_at ASC
        """)

        logger.info(f"Processing {len(subscriptions)} active subscriptions")

        emails_sent = 0
        errors = 0
        skipped = 0

        for sub in subscriptions:
            try:
                # Geocode the address (use substring match to find properties containing the search term)
                geocode_result = await db_pool.fetchrow("""
                    SELECT latitude, longitude
                    FROM properties
                    WHERE address ILIKE '%' || $1 || '%'
                      AND latitude IS NOT NULL
                    LIMIT 1
                """, sub['address'])

                if not geocode_result or not geocode_result['latitude']:
                    logger.warning(f"Could not geocode address: {sub['address']}")
                    skipped += 1
                    continue

                lat = geocode_result['latitude']
                lon = geocode_result['longitude']

                # Find properties added since last_sent_at (or created_at if never sent)
                since_date = sub['last_sent_at'] or sub['created_at']

                query = """
                    SELECT id, address, price, sale_date, county, description
                    FROM properties
                    WHERE geog IS NOT NULL
                      AND ST_DWithin(geog, ST_MakePoint($1, $2)::geography, $3 * 1000)
                      AND created_at > $4
                      AND not_full_market_price = FALSE
                """

                params = [lon, lat, sub['radius_km'], since_date]

                if sub['county']:
                    query += " AND county = $5"
                    params.append(sub['county'])

                query += " ORDER BY sale_date DESC LIMIT 50"

                rows = await db_pool.fetch(query, *params)

                if rows:
                    properties = []
                    for row in rows:
                        properties.append({
                            "id": row['id'],
                            "address": row['address'],
                            "price": float(row['price']) if row['price'] else 0,
                            "sale_date": row['sale_date'].strftime("%Y-%m-%d") if row['sale_date'] else "",
                            "county": row['county'] or "",
                            "description": row['description'] or "",
                        })

                    # Send digest email
                    success = send_monthly_digest(
                        email=sub['email'],
                        address=sub['address'],
                        radius_km=sub['radius_km'],
                        county=sub['county'],
                        properties=properties,
                        unsubscribe_token=sub['unsubscribe_token']
                    )

                    if success:
                        # Update last_sent_at timestamp
                        await db_pool.execute("""
                            UPDATE email_alerts
                            SET last_sent_at = CURRENT_TIMESTAMP
                            WHERE id = $1
                        """, sub['id'])
                        emails_sent += 1
                        logger.info(f"✓ Sent digest to {sub['email']}: {len(properties)} properties")
                    else:
                        errors += 1
                        logger.error(f"✗ Failed to send digest to {sub['email']}")
                else:
                    skipped += 1
                    logger.info(f"No new properties for {sub['email']} ({sub['address']})")

            except Exception as e:
                logger.error(f"Error processing subscription {sub['id']} ({sub['email']}): {e}")
                errors += 1

        logger.info(f"Monthly alerts job complete: {emails_sent} sent, {skipped} skipped, {errors} errors")

        return {
            "ok": True,
            "subscriptions_processed": len(subscriptions),
            "emails_sent": emails_sent,
            "skipped": skipped,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Fatal error in monthly alerts cron: {e}")
        raise HTTPException(status_code=500, detail=str(e))
