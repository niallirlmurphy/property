"""Limit baked page-data regeneration to once per calendar month.

Every refresh of the static landing-page data (area/eircode/county, street,
development and homepage site-stats JSON) produces a large diff and a redeploy.
The underlying figures barely move week to week, so each generator runs at most
once per calendar month. The date of each generator's last run is kept in
frontend/src/data/page_data_generated.json (committed, so it holds across
machines and CI). Pass --force to regenerate anyway, e.g. for a brand-new page
type that has no data yet.

Usage inside a generator:
    from page_data_schedule import skip_if_generated_this_month, record_generated
    if skip_if_generated_this_month("streets", force=args.force):
        return 0
    ... write the files ...
    record_generated("streets")
"""
import json
import os
from datetime import date
from typing import Optional

STAMP = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "data",
                     "page_data_generated.json")


def _load() -> dict:
    try:
        with open(STAMP, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def last_generated(name: str) -> Optional[date]:
    value = _load().get(name)
    return date.fromisoformat(value) if value else None


def generated_this_month(name: str, today: Optional[date] = None) -> bool:
    today = today or date.today()
    last = last_generated(name)
    return last is not None and (last.year, last.month) == (today.year, today.month)


def skip_if_generated_this_month(name: str, force: bool = False) -> bool:
    """True (and prints why) if `name` already ran this month and force is off."""
    if force or not generated_this_month(name):
        return False
    print(f"⏭️  {name} page data already generated on {last_generated(name)}; "
          f"limit is once per month. Use --force to regenerate anyway.")
    return True


def record_generated(name: str, today: Optional[date] = None) -> None:
    stamps = _load()
    stamps[name] = (today or date.today()).isoformat()
    with open(STAMP, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(stamps.items())), fh, indent=2)
        fh.write("\n")
