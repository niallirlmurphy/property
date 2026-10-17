"""Tests for scripts/development_pins.py (pure validation; SQL is checked live)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from development_pins import check_pin  # noqa: E402

PARKVIEW_MATCH = ("parkview & (ash | cedar | oak) & (stepaside | dublin <-> 18) & !belfry")


def test_accepts_pin_inside_its_county():
    check_pin("Dublin", PARKVIEW_MATCH, 53.2596962, -6.2247187)


def test_rejects_pin_outside_its_county():
    # A Mayo coordinate pinned to a Dublin development is a typo, not a pin.
    with pytest.raises(ValueError, match="outside County Dublin"):
        check_pin("Dublin", PARKVIEW_MATCH, 53.85, -9.30)


def test_rejects_unknown_county():
    with pytest.raises(ValueError, match="Unknown county"):
        check_pin("Dublinn", PARKVIEW_MATCH, 53.2596962, -6.2247187)


def test_rejects_single_term_match():
    # One word ("parkview") would pin every Parkview in the county onto one point.
    with pytest.raises(ValueError, match="at least two terms"):
        check_pin("Dublin", "parkview", 53.2596962, -6.2247187)


def test_rejects_like_style_wildcards():
    with pytest.raises(ValueError, match="full-text"):
        check_pin("Dublin", "parkview & stepaside%", 53.2596962, -6.2247187)


def test_rejects_silly_keep_radius():
    # A radius that covers half the county would leave wrong-town geocodes in place.
    with pytest.raises(ValueError, match="keep-within"):
        check_pin("Dublin", PARKVIEW_MATCH, 53.2596962, -6.2247187, keep_within_m=50000)
    check_pin("Dublin", PARKVIEW_MATCH, 53.2596962, -6.2247187, keep_within_m=800)
