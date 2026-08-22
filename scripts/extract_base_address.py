#!/usr/bin/env python3
"""
Extract base address from bulk sales for geocoding.

Bulk sales like "Units 1-35 Block F, Broadstone Court" should geocode to
"Broadstone Court" rather than the full address which confuses geocoders.
"""

import re


def is_bulk_sale(address: str) -> bool:
    """
    Detect if an address represents a bulk property sale.

    Patterns:
    - Multiple unit numbers: "1-76", "1 2 3 4", "53 76 78 85"
    - Keywords: "Units", "Apartments", "Apts", "Blocks", "Numbers"
    - Ranges: "1-35", "1 to 35", "1-3 6-9"
    """
    if not address:
        return False

    addr_lower = address.lower()

    # Check for bulk sale keywords
    bulk_keywords = [
        'units ', 'apartments ', 'apts ', ' blocks ', ' block ',
        ' to ', ' and others', ' & others', 'numbers only',
        'excluding certain', 'inclusive'
    ]

    if any(kw in addr_lower for kw in bulk_keywords):
        return True

    # Check for multiple numbers in a row (likely bulk sale)
    # Example: "53 76 78 85 97 99" or "1 2 3 4 5 6"
    numbers = re.findall(r'\b\d+\b', address)
    if len(numbers) >= 5:  # 5+ separate numbers likely indicates bulk
        return True

    # Check for ranges with dashes
    # Example: "1-76", "1-35", "7-22"
    ranges = re.findall(r'\b\d+-\d+\b', address)
    if len(ranges) >= 2:  # Multiple ranges
        return True

    return False


def extract_base_address(address: str) -> str:
    """
    Extract the base location from a bulk sale address.

    Examples:
        "1-76 Bridge Hall, Parkleigh" -> "Bridge Hall, Parkleigh"
        "Units 1 to 35 Block F, Broadstone Court" -> "Broadstone Court"
        "Apts 1 to 35 Rosemount Gate, Harolds Cross Road" -> "Rosemount Gate, Harolds Cross Road"
        "53 76 78 85 Fairview, Dublin" -> "Fairview, Dublin"

    Strategy:
    1. Remove unit prefixes (Units, Apartments, Apts, etc.)
    2. Remove number ranges and lists
    3. Remove block/phase identifiers
    4. Keep the core location name
    """
    if not address:
        return address

    original = address

    # Pattern 1: Remove "Units X to Y" or "Apartments X to Y" prefix
    address = re.sub(
        r'^(Units?|Apartments?|Apts?\.?)\s+[\d\s,&-]+\s+(to\s+[\d\s,&-]+\s+)?(Block\s+[A-Z0-9]+,?\s*)?',
        '',
        address,
        flags=re.IGNORECASE
    )

    # Pattern 2: Remove leading number sequences and ranges
    # "1-76 Bridge Hall" -> "Bridge Hall"
    # "53 76 78 85 Fairview" -> "Fairview"
    address = re.sub(r'^[\d\s,&-]+\s+', '', address)

    # Pattern 3: Remove block/phase identifiers in the middle
    # "Block F, Broadstone Court" -> "Broadstone Court"
    address = re.sub(
        r'\bBlock\s+[A-Z0-9]+,?\s*',
        '',
        address,
        flags=re.IGNORECASE
    )

    # Pattern 4: Remove trailing unit specifications
    # "Broadstone Court, Units 1-35" -> "Broadstone Court"
    address = re.sub(
        r',?\s*(Units?|Apartments?|Apts?\.?)\s+[\d\s,&-]+$',
        '',
        address,
        flags=re.IGNORECASE
    )

    # Clean up extra commas and whitespace
    address = re.sub(r'\s*,\s*,\s*', ', ', address)  # Remove double commas
    address = re.sub(r'^\s*,\s*', '', address)  # Remove leading comma
    address = re.sub(r'\s*,\s*$', '', address)  # Remove trailing comma
    address = re.sub(r'\s+', ' ', address)  # Normalize whitespace
    address = address.strip()

    # If we removed too much (address too short), return original
    if len(address) < 5:
        return original

    return address


if __name__ == '__main__':
    # Test cases
    test_cases = [
        "1-76 Bridge Hall, Parkleigh, Seven Mills",
        "Units 1 to 35 Block F, Broadstone Court, Hansfield Station Quarter",
        "Apts 1 to 35 Rosemount Gate, 153 to 155 Harolds Cross Road, Harolds Cross",
        "53 76 78 85 97 99 100 102 103 107, 110 114 115 117 118 120 121 122, 123 124 125 126 127 128 Fairview, Dublin",
        "Apartment Blocks E01-E06, The East Village, Clay Farm",
        "51 units at Claremont, Dublin Road, Howth",
        "2-4 13-15 and others The Gardens, 1-3 6 and others The Place, and 32 33 and others The Wood, Pelletstown",
        "52 Longview Park, Ballyvolane Cork",  # Not bulk - should return unchanged
    ]

    print("="*80)
    print("BULK ADDRESS EXTRACTION TEST")
    print("="*80 + "\n")

    for addr in test_cases:
        is_bulk = is_bulk_sale(addr)
        extracted = extract_base_address(addr)

        print(f"Original:  {addr[:60]}")
        print(f"Is Bulk:   {is_bulk}")
        print(f"Extracted: {extracted[:60]}")
        if extracted != addr:
            print(f"  ✓ Simplified")
        else:
            print(f"  = No change")
        print()
