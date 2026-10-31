"""Addresses that name several homes: one bulk sale, not a single-dwelling price.

A bulk sale is filed as one row with the price of the whole lot (a €3.9M "Apt 1-10"
pushes an area's median to ~€1M), so medians, trends, the heatmap and valuation
comparables leave these rows out. Search still lists them.

Matches a unit range ("Units 1-76", "1 to 10"), "and others" ("APT 1 AND OTHERS",
"9 The Avenue (and Others)") or two or more homes counted out ("48 Units at
Cronins Wood", "8 HOUSES AT", "35 APTS"). "Block 5" and lists of numbers are not
included: thousands of single flats read "Apt 4, Block A" or "Apt 5, 12 Main St".

Written to work as both a Postgres regex (with ~* / !~*, so no \\m word
boundaries) and a Python re pattern (with re.IGNORECASE). Lives in backend/
because Railway deploys only that directory; scripts import it via sys.path.
"""

BULK_ADDR_RE = (
    r"[0-9]+ *(-|to) *[0-9]+"
    r"|(^|[^a-z])(and|&) *(others|ors)([^a-z]|$)"
    r"|(^|[^0-9])([2-9]|[1-9][0-9]+) *(apartments|apts|units|houses|dwellings|homes)([^a-z]|$)"
)

# Over this price, a new dwelling or an apartment/unit/block is a bulk sale too:
# a whole scheme or building ("Glenconnor, Clonmel" €7.9M new; "APT 1, Shaw Court"
# €5.4M). A single house can sell for more (Ailesbury Road, Dalkey), so second-hand
# houses stay in. Checked on 2026-10-31: 188 of the 411 sales over €5M not caught above.
BULK_PRICE = 5_000_000
BULK_DESC_RE = r"new|nua"   # "New Dwelling house /Apartment", Irish "Nua"
BULK_FLAT_RE = r"(^|[^a-z])(apt|apts|apartments?|blocks?|units?|flats?)([^a-z]|$)"
