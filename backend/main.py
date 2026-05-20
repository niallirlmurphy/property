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
    """Return (SQL fragment, params) for a token, matching its abbreviation/expansion too."""
    alt = _FULL_TO_ABBREV.get(t) or _ABBREV_TO_FULL.get(t)
    if alt:
        return f"(LOWER(address) LIKE ${idx} OR LOWER(address) LIKE ${idx+1})", [f"%{t}%", f"%{alt}%"]
    return f"LOWER(address) LIKE ${idx}", [f"%{t}%"]


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
    """Fuzzy match query against DB addresses/counties, return centroid if confident."""
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
      3. Eircode → DB exact match      (fast indexed lookup)
      4. Eircode → Nominatim           (OSM eircode data, address-level precision)
      5. Token-based DB lookup         (tight clusters in known developments)
      6. Nominatim                     (OSM geocoder, importance-ranked results)
      7. Mapbox Geocoding API          (commercial fallback)
      8. Fuzzy DB ILIKE full-scan      (slow last resort)

    Source values: 'raw', 'cache', 'db_exact', 'nominatim', 'db_tokens', 'mapbox', 'db_fuzzy', 'db_routing_key'
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

    # 3. Eircode — fast indexed DB lookup with routing key validation
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

        # Exact match not in PPR or failed validation — use routing key centroid (already fetched above)
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

    # Auto-expand radius if too few results found
    # Try original radius, then incrementally expand until we have at least 5 results
    MIN_RESULTS = 5
    MAX_RADIUS_KM = 20.0
    RADIUS_INCREMENTS = [radius_km, radius_km * 2, radius_km * 3, radius_km * 5, radius_km * 10, MAX_RADIUS_KM]

    rows = []
    actual_radius = radius_km
    radius_expanded = False

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
        if county:
            filters.append(f"LOWER(county) = LOWER(${idx})"); params.append(county); idx += 1

        where = " AND ".join(filters)
        params.append(limit)

        rows = await db_pool.fetch(f"""
            SELECT
                id, sale_date, address, county, eircode, price,
                not_full_market_price, vat_exclusive, description,
                size_description, latitude, longitude,
                routing_key,
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
            routing_key
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
