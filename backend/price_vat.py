"""VAT-inclusive price for medians, trends and valuations.

New-home prices on the register are ex-VAT; second-hand prices carry no VAT.
Adding VAT back lets new and second-hand sales be compared like with like (as
the CSO does). Listings and filters keep the register price.

Rates: 13.5% on new homes; 9% on new apartments sold from 8 Oct 2025 to 31 Dec
2030 (Budget 2026). The register doesn't say house or apartment, so an apartment
is an enriched property_type or an apartment word in the address (the words of
_APARTMENT_ADDRESS_RE in valuation/adjustments.py).

Lives in backend/ because Railway deploys only that directory; scripts import it
via sys.path.
"""


def price_incl_vat_sql(alias: str = "") -> str:
    """SQL expression for the VAT-inclusive price; alias is a table alias ("p")."""
    a = f"{alias}." if alias else ""
    return (
        f"(CASE WHEN {a}vat_exclusive IS NOT TRUE THEN {a}price"
        f" WHEN {a}sale_date BETWEEN DATE '2025-10-08' AND DATE '2030-12-31'"
        f" AND (lower({a}property_type) IN ('apartment', 'apartments', 'flat', 'duplex', 'studio')"
        f" OR {a}address_normalized ~* '\\m(apartments?|apts?|flats?|duplex|penthouse)\\M')"
        f" THEN round({a}price * 1.09, 2)"
        f" ELSE round({a}price * 1.135, 2) END)"
    )


PRICE_INCL_VAT = price_incl_vat_sql()
