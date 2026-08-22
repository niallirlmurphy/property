#!/usr/bin/env python3
"""One-off: derive the dominant eircode routing keys for each area-guide area, so
frontend/src/areas.ts can carry accurate routing_keys for the area-page locality
filter. For each area we match properties whose address full-text-matches the
curated locality terms (same 'simple' tsquery the backend uses) within the parent
county, then report the routing keys covering >=5% of matched eircoded rows.

Not part of the pipeline; kept for re-running if areas change."""
import asyncio
import os
import re
import unicodedata
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")

# (slug, county, [locality terms]) — county scoping avoids e.g. Cork Blackrock
# polluting Dublin Blackrock's keys.
AREAS = [
    ("rathmines", "Dublin", ["Rathmines"]),
    ("ranelagh", "Dublin", ["Ranelagh"]),
    ("blackrock", "Dublin", ["Blackrock"]),
    ("dun-laoghaire", "Dublin", ["Dun Laoghaire", "Glasthule", "Sandycove", "Monkstown"]),
    ("clontarf", "Dublin", ["Clontarf"]),
    ("howth", "Dublin", ["Howth", "Sutton", "Baldoyle"]),
    ("malahide", "Dublin", ["Malahide"]),
    ("stillorgan", "Dublin", ["Stillorgan"]),
    ("sandymount", "Dublin", ["Sandymount"]),
    ("portobello", "Dublin", ["Portobello"]),
    ("galway-city", "Galway", ["Galway"]),
    ("salthill", "Galway", ["Salthill"]),
    ("oranmore", "Galway", ["Oranmore"]),
    ("athenry", "Galway", ["Athenry"]),
    ("tuam", "Galway", ["Tuam"]),
    ("connemara", "Galway", ["Clifden", "Connemara", "Roundstone", "Ballyconneely", "Letterfrack"]),
    ("cork-city", "Cork", ["Cork City", "Cork"]),
    ("douglas", "Cork", ["Douglas"]),
    ("ballincollig", "Cork", ["Ballincollig"]),
    ("carrigaline", "Cork", ["Carrigaline"]),
    ("cobh", "Cork", ["Cobh"]),
    ("midleton", "Cork", ["Midleton"]),
    ("kinsale", "Cork", ["Kinsale"]),
    ("skibbereen-baltimore", "Cork", ["Skibbereen", "Baltimore"]),
    ("limerick-city", "Limerick", ["Limerick"]),
    ("waterford-city", "Waterford", ["Waterford"]),
    ("kilkenny-city", "Kilkenny", ["Kilkenny"]),
    ("drogheda", "Louth", ["Drogheda"]),
    ("dundalk", "Louth", ["Dundalk"]),
    ("navan", "Meath", ["Navan"]),
    ("naas", "Kildare", ["Naas"]),
    ("bray", "Wicklow", ["Bray"]),
]


def tsquery(terms):
    parts = []
    for term in terms:
        norm = unicodedata.normalize("NFKD", term)
        norm = "".join(c for c in norm if not unicodedata.combining(c))
        words = [w for w in re.split(r"[^a-z0-9]+", norm.lower()) if w]
        if words:
            parts.append(" <-> ".join(words))
    return " | ".join(parts)


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=20)
    await conn.execute("SET statement_timeout = '120s'")
    for slug, county, terms in AREAS:
        ts = tsquery(terms)
        rows = await conn.fetch(
            """
            SELECT routing_key AS rk, COUNT(*) AS n
            FROM properties
            WHERE LOWER(county) = LOWER($1)
              AND to_tsvector('simple', address) @@ to_tsquery('simple', $2)
              AND routing_key IS NOT NULL AND routing_key <> ''
            GROUP BY routing_key
            ORDER BY n DESC
            """,
            county, ts,
        )
        total = sum(r["n"] for r in rows)
        # Also count matched rows lacking an eircode (so we know term-only reliance).
        no_ec = await conn.fetchval(
            """
            SELECT COUNT(*) FROM properties
            WHERE LOWER(county) = LOWER($1)
              AND to_tsvector('simple', address) @@ to_tsquery('simple', $2)
              AND (routing_key IS NULL OR routing_key = '')
            """,
            county, ts,
        )
        keep = [(r["rk"], r["n"]) for r in rows if total and r["n"] / total >= 0.05]
        keys = ",".join(k for k, _ in keep)
        detail = " ".join(f"{k}:{n}" for k, n in keep)
        print(f"{slug:22s} eircoded={total:6d} no_ec={no_ec:6d}  keys=[{keys}]   ({detail})")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
