"""The Phase 2 prototype must agree with brute force, or its measurement is worthless.

The whole point of the prototype was to decide Phase 2 on data. A profile DP that
quietly miscounts would have produced a confident wrong verdict, so it is pinned
against the independent exhaustive counter wherever both are affordable.
"""
import pytest

from graphrecords.torus import brute_dominating
from graphrecords.torus_profile import _row_neighbourhood, dominating_sets_torus


@pytest.mark.parametrize("n", [3, 4])
def test_profile_agrees_with_brute_force(n):
    count, _peak = dominating_sets_torus(n)
    assert count == brute_dominating(n)


def test_row_neighbourhood_wraps_horizontally():
    # on a 4-cycle, a single cell at position 0 covers 0, 1 and 3 (the wrap)
    assert _row_neighbourhood(0b0001, 4) == 0b1011


def test_rejects_degenerate_small_torus():
    for n in (1, 2):
        with pytest.raises(ValueError):
            dominating_sets_torus(n)


def test_known_measured_values_do_not_drift():
    """Pins the numbers the Phase 2 verdict was based on."""
    assert dominating_sets_torus(3)[0] == 421
    assert dominating_sets_torus(4)[0] == 45707
    assert dominating_sets_torus(5)[0] == 18935741
