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
    ("Street Thomas Road", "Mount Merrion"): "St Thomas Road",
    ("the Burbidge", "Lansdowne Place"): "The Burbidge",
    ("the Links", "Elm Park"): "The Links",
}

# Optional 2-3 sentence factual commentary, keyed by slug. Only verifiable facts.
INFO = {
    "ailesbury-road-ballsbridge": "Ailesbury Road is a wide, tree-lined Victorian road in Ballsbridge, Dublin 4, long regarded as one of Dublin's most prestigious residential addresses. Its large detached red-brick and stucco houses date largely from the 1860s to 1880s, and a number serve as embassies and diplomatic residences.",
    "fitzwilliam-square-dublin-2": "Fitzwilliam Square is one of the last and best-preserved of Dublin's great Georgian squares, laid out in the early 19th century in Dublin 2. Its four terraces of red-brick townhouses surround a private garden that remains accessible only to residents and keyholders. Former residents include the painter Jack B. Yeats, who worked at No. 18 from 1930, the railway engineer William Dargan (No. 2), and the artist Mainie Jellett (No. 36).",
    "herbert-park-ballsbridge": "Herbert Park is a residential road in Ballsbridge, Dublin 4, running alongside the public park of the same name, which was laid out for the 1907 Irish International Exhibition. The road is lined with substantial Edwardian red-brick houses. No. 40 was the home of The O'Rahilly (1875–1916), a leader of the Irish Volunteers killed in the 1916 Easter Rising, and his wife Nancy O'Rahilly, a founding member of Cumann na mBan; the house was demolished in 2020.",
    "longford-terrace-monkstown": "Longford Terrace is a seafront Victorian terrace in Monkstown, south County Dublin, overlooking Dublin Bay. Its tall, stucco-fronted houses form one of the best-known 19th-century terraces on the coast. The astronomer and spectroscopist Margaret Lindsay Huggins (1848–1915) grew up at No. 23, where a commemorative plaque was installed in 1997.",
    "palmerston-road-rathmines": "Palmerston Road is a broad, tree-lined Victorian avenue in Rathmines, Dublin 6, developed largely in the second half of the 19th century. It is known for its large red-brick and granite houses set back behind mature front gardens. No. 97 was the childhood home of the Gifford sisters, among them Grace Gifford, who married the 1916 leader Joseph Plunkett, and Muriel Gifford, who married the executed signatory Thomas MacDonagh.",
    "clyde-road-ballsbridge": "Clyde Road is a Victorian residential road in Ballsbridge, Dublin 4, close to the River Dodder. It is characterised by large detached and semi-detached red-brick houses dating mainly from the 1860s and 1870s.",
    "merrion-square-dublin-2": "Merrion Square has been home to many of Ireland's most celebrated figures: Oscar Wilde grew up at No. 1, the poet W. B. Yeats lived at No. 82, and Daniel O'Connell lived at No. 58. Later residents included the writer Sheridan Le Fanu and the physicist Erwin Schrödinger.",
    "harcourt-terrace-dublin-2": "No. 4 Harcourt Terrace was for many years the home of the actor-directors Micheál Mac Liammóir and Hilton Edwards, founders of the Gate Theatre, and the artist Sarah Purser kept a studio at No. 11.",
    "wellington-road-ballsbridge": "No. 40 Wellington Road was the birthplace of the pioneering medical physicist Edith Anne Stoney (1869–1938), and No. 19 was later the home of P. J. Mara (1942–2016), the Fianna Fáil senator and adviser to Taoiseach Charles Haughey.",
    "anglesea-road-ballsbridge": "No. 5 Anglesea Road was the home of the artist Beatrice Behan, widow of the playwright Brendan Behan, and where their son, the actor Paudge Behan, grew up.",
    "lansdowne-road-ballsbridge": "No. 73 Lansdowne Road was the home of the architect George F. Beckett (1877–1961), president of the RIAI and a relative of the writer Samuel Beckett.",
    "raglan-road-ballsbridge": "Raglan Road gives its name to Patrick Kavanagh's celebrated song “On Raglan Road”, though the poet did not live on the street himself. The Celtic scholar Cecile O'Rahilly — the first woman appointed a full professor at the Dublin Institute for Advanced Studies — lived at No. 17 from 1951 until her death in 1980.",
    "brendan-road-donnybrook": "Brendan Road was built and named by Batt O'Connor (1870–1935), a builder, IRB member and later TD, who lived at No. 1 — Michael Collins was a frequent visitor during the War of Independence. Fellow republicans Diarmuid O'Hegarty (No. 9) and Sinéad Derrig (No. 23) also lived on the road.",
    "eglinton-road-donnybrook": "No. 75 Eglinton Road was the family home of Garret FitzGerald (1926–2011), who twice served as Taoiseach.",
    "greenfield-park-donnybrook": "No. 23 Greenfield Park, “The Pavilion”, was the final home of the newspaper magnate Cecil Harmsworth King (1901–1987), chairman of the Daily Mirror, who moved there from London in 1974.",
    "morehampton-road-dublin-4": "Morehampton Road has been home to several writers and artists, including the writer Kathleen Goodfellow (No. 4) and the artist and printer Cecil ffrench Salkeld (No. 43), who ran the Gayfield Press from a garden studio there in the 1930s and 1940s.",
    "sandymount-avenue-dublin-4": "The poet W. B. Yeats (1865–1939) was born in Sandymount in 1865, traditionally at a house called “Georgeville” on Sandymount Avenue.",
    "sydney-parade-avenue-sandymount": "14 Sydney Parade Avenue was the family home of the brothers Jack and Walter Peterson, who won silver in field hockey for Ireland at the 1908 London Olympics.",
    "sydney-parade-avenue-dublin-4": "14 Sydney Parade Avenue was the family home of the brothers Jack and Walter Peterson, who won silver in field hockey for Ireland at the 1908 London Olympics.",
    "orwell-park-rathgar": "The playwright J. M. Synge (1871–1909) grew up at 4 Orwell Park, his family home until 1890.",
    "highfield-road-rathgar": "28 Highfield Road was a childhood home of Dr Dorothy Price (1890–1954), the physician who pioneered tuberculosis control and BCG vaccination in Ireland.",
    "temple-road-dartry": "Temple Road was the final home of the Trinity College botanist Henry Horatio Dixon (1869–1953), co-author of the cohesion-tension theory of how water rises in plants.",
    "cowper-road-rathmines": "No. 12 Cowper Road was the birthplace, in 1884, of Muriel Gifford MacDonagh, the nationalist activist and widow of the executed 1916 leader Thomas MacDonagh.",
    "belgrave-road-rathmines": "No. 9 Belgrave Road was the home and medical practice of Dr Kathleen Lynn (1874–1955), the 1916 Rising figure and co-founder of St Ultan's children's hospital, who lived there with her partner Madeleine ffrench-Mullen for some fifty years.",
    "palmerston-park-rathmines": "Palmerston Park's residents have included Charles Dawson (1842–1917), Lord Mayor of Dublin, at No. 13, and the writer and soldier C. Morton Horne (1885–1916), killed in the First World War, at No. 16.",
    "dartmouth-square-ranelagh": "The geologist Grenville Cole (1859–1924), director of the Geological Survey of Ireland, lived at No. 3 Dartmouth Square around the turn of the 20th century.",
    "leeson-park-ranelagh": "The barrister and judge Michael Comyn lived on Leeson Park, where the republican leader Erskine Childers is said to have sheltered before his capture in 1922; the architectural historian Alistair Rowan and archivist Ann Martha Rowan lived at No. 22.",
    "leeson-park-dublin-6": "The barrister and judge Michael Comyn lived on Leeson Park, where the republican leader Erskine Childers is said to have sheltered before his capture in 1922; the architectural historian Alistair Rowan and archivist Ann Martha Rowan lived at No. 22.",
    "northbrook-road-ranelagh": "No. 21 Northbrook Road was the family home of Thomas Crean (1873–1923), an Irish rugby international who won the Victoria Cross in the Boer War; the botanist Henry Horatio Dixon also lived for a time at No. 23.",
    "waltham-terrace-blackrock": "The architect Patrick Byrne (d. 1864) lived at No. 3 Waltham Terrace, and the suffragette Norah Elam (1878–1961) was born at No. 13.",
    "coliemore-road-dalkey": "The actor Norman Rodway (1929–2001) was born at “Elsinore”, his family home on Coliemore Road.",
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
