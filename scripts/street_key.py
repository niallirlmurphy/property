"""Shared street-name extraction, used by analyze_top_streets.py and
generate_street_data.py so the two can never diverge."""
import re

LEAD_RE = re.compile(
    r"^(?:(?:apartment|apt|unit|no\.?|flat|site)\s*)?\d+[a-z]?\s*(?:-\s*\d+[a-z]?\s*)?",
    re.IGNORECASE,
)
GENERIC_FIRST = re.compile(
    r"^(the\s+)?(apartment|apartments|penthouse|ground floor|first floor|second floor|"
    r"third floor|top floor|floor)\b",
    re.IGNORECASE,
)
APT_PREFIX_RE = re.compile(
    r"^(?:the\s+)?(apartment|apt|penthouse|ground floor|first floor|second floor|"
    r"third floor|top floor|floor|flat)\b",
    re.IGNORECASE,
)
APT_NAME_RE = re.compile(r"\b(block|building|apartments?)\b", re.IGNORECASE)


def normalize(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def normalized_key_string(street_norm, area_norm, county_norm):
    return f"{street_norm}|{area_norm}|{county_norm}"


def street_key(addr, county):
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    if len(parts) < 2:
        return None
    first = parts[0]
    apt_flag = bool(APT_PREFIX_RE.match(first))
    stripped = LEAD_RE.sub("", first).strip()
    idx = 0
    if not stripped or GENERIC_FIRST.match(stripped) or len(stripped) < 3:
        if len(parts) >= 3:
            stripped = parts[1]
            idx = 1
        else:
            return None
    street = stripped
    if not re.search(r"[a-zA-Z]{3,}", street):
        return None
    area = parts[idx + 1] if len(parts) > idx + 1 else county
    return (
        (normalize(street), normalize(area), county.strip().lower()),
        (street.strip(), area.strip(), county.strip()),
        apt_flag,
    )
