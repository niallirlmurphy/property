"""One-time authoring aid: read data/top_streets_analysis.csv, apply display
overrides, compute slugs + normalizedKey, and write the registry JSON.
Re-runnable and deterministic. After this, streets_registry.json is the
hand-maintained source of truth."""
import csv, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from street_key import normalize, normalized_key_string

ROOT = os.path.join(os.path.dirname(__file__), "..")
CSV = os.path.join(ROOT, "data", "top_streets_analysis.csv")
OUT = os.path.join(ROOT, "frontend", "src", "data", "streets_registry.json")

COUNTY_SLUG = lambda c: c.strip().lower().replace(" ", "-")

# Hand-corrected display names, keyed by (raw street, area) from the CSV.
NAME_FIX = {
    ("Street Kevins Park", "Dartry"): "St Kevin's Park",
    ("Street Marys Road", "Ballsbridge"): "St Mary's Road",
    ("the Burbidge", "Lansdowne Place"): "The Burbidge",
    ("the Links", "Elm Park"): "The Links",
}

# Optional 2-3 sentence factual commentary, keyed by slug. Only verifiable facts.
INFO = {
    "ailesbury-road-ballsbridge": "Ailesbury Road is a wide, tree-lined Victorian road in Ballsbridge, Dublin 4, long regarded as one of Dublin's most prestigious residential addresses. Its large detached red-brick and stucco houses date largely from the 1860s to 1880s, and a number serve as embassies and diplomatic residences.",
    "fitzwilliam-square-dublin-2": "Fitzwilliam Square is one of the last and best-preserved of Dublin's great Georgian squares, laid out in the early 19th century in Dublin 2. Its four terraces of red-brick townhouses surround a private garden that remains accessible only to residents and keyholders.",
    "herbert-park-ballsbridge": "Herbert Park is a residential road in Ballsbridge, Dublin 4, running alongside the public park of the same name, which was laid out for the 1907 Irish International Exhibition. The road is lined with substantial Edwardian red-brick houses.",
    "longford-terrace-monkstown": "Longford Terrace is a seafront Victorian terrace in Monkstown, south County Dublin, overlooking Dublin Bay. Its tall, stucco-fronted houses form one of the best-known 19th-century terraces on the coast.",
    "palmerston-road-rathmines": "Palmerston Road is a broad, tree-lined Victorian avenue in Rathmines, Dublin 6, developed largely in the second half of the 19th century. It is known for its large red-brick and granite houses set back behind mature front gardens.",
    "clyde-road-ballsbridge": "Clyde Road is a Victorian residential road in Ballsbridge, Dublin 4, close to the River Dodder. It is characterised by large detached and semi-detached red-brick houses dating mainly from the 1860s and 1870s.",
}

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

def main():
    rows = list(csv.DictReader(open(CSV)))
    # base slug from name+area; resolve collisions by appending county slug
    base = []
    for r in rows:
        raw_name, area, county = r["street"], r["area"], r["county"]
        name = NAME_FIX.get((raw_name, area), raw_name)
        # title-case a leading lowercase "the"
        name = re.sub(r"^the\b", "The", name)
        base.append({"raw_name": raw_name, "name": name, "area": area, "county": county, "row": r})
    slug_counts = {}
    for b in base:
        s = slugify(f"{b['name']} {b['area']}")
        slug_counts[s] = slug_counts.get(s, 0) + 1
    out = []
    for b in base:
        r = b["row"]
        s = slugify(f"{b['name']} {b['area']}")
        if slug_counts[s] > 1:
            s = slugify(f"{b['name']} {b['area']} {b['county']}")
        median = int(r["median_price"]); count = int(r["tx_count"])
        cat = r["rank_type"]
        if cat == "value":
            desc = (f"One of Ireland's highest-value streets, with a median sale price of "
                    f"€{median:,} across {count} recorded sales on the Property Price Register.")
        else:
            desc = (f"One of Ireland's most active streets, with {count} recorded sales on the "
                    f"Property Price Register and a median price of €{median:,}.")
        entry = {
            "slug": s,
            "name": b["name"],
            "area": b["area"],
            "county": b["county"],
            "countySlug": COUNTY_SLUG(b["county"]),
            "category": cat,
            "rank": int(r["rank"]),
            "normalizedKey": normalized_key_string(
                normalize(b["raw_name"]), normalize(b["area"]), b["county"].strip().lower()),
            "description": desc,
        }
        if s in INFO:
            entry["info"] = INFO[s]
        out.append(entry)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"wrote {OUT} with {len(out)} streets")

if __name__ == "__main__":
    main()
