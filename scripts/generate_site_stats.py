"""Write frontend/src/data/site_stats.json: headline register figures (total
sales, mapped sales, date range, counties) shown in the homepage trust strip,
FAQ and Dataset structured data. Run after the PPR sync, then rebuild/redeploy
the frontend so the baked figures stay current."""
import json, os
from datetime import date
import psycopg2

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "frontend", "src", "data", "site_stats.json")


def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*), COUNT(geog), MIN(sale_date), MAX(sale_date), COUNT(DISTINCT county)
        FROM properties
    """)
    total, mapped, first, last, counties = cur.fetchone()
    conn.close()

    stats = {
        "total_sales": total,
        "mapped_sales": mapped,
        "first_sale_date": first.isoformat(),
        "last_sale_date": last.isoformat(),
        "counties": counties,
        "generated": date.today().isoformat(),
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)
        fh.write("\n")
    print(f"Wrote {OUT}: {stats}")


if __name__ == "__main__":
    main()
