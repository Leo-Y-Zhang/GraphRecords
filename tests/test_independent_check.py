"""The reduction certificates, re-checked without verify_isomorphism.

Every positive test here is a check the gate already makes through
verify_isomorphism, deliberately made a second time through code that shares
nothing with it; the negative tests are what verify_isomorphism never had --
proof that the checker rejects a wrong certificate, half by half.
"""
import pytest

from graphrecords.independent_check import (
    check_bishop_certificate,
    check_honeycomb_certificate,
    honeycomb_coords,
    moved_certificate,
    swapped_certificate,
)
from graphrecords.reduction import rook_coords, verify_isomorphism


@pytest.mark.parametrize("n", range(1, 13))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_square_certificate_is_an_isomorphism(n, colour):
    check_bishop_certificate(n, colour)


@pytest.mark.parametrize("rows", range(1, 7))
@pytest.mark.parametrize("cols", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_rectangular_certificate_is_an_isomorphism(rows, cols, colour):
    check_bishop_certificate(rows, colour, cols=cols)


@pytest.mark.parametrize("n", range(1, 13))
def test_honeycomb_certificate_is_an_isomorphism(n):
    check_honeycomb_certificate(n)


# --- each half of the claim, shown to discriminate --------------------------


def test_a_missing_vertex_is_rejected():
    coords = rook_coords(4, "black")
    del coords[min(coords)]
    with pytest.raises(AssertionError, match="does not cover the vertex set"):
        check_bishop_certificate(4, "black", coords=coords)


def test_a_collision_is_rejected_as_non_injective():
    coords = rook_coords(4, "black")
    a, b = sorted(coords)[:2]
    coords[a] = coords[b]
    with pytest.raises(AssertionError, match="not injective"):
        check_bishop_certificate(4, "black", coords=coords)


def test_one_moved_entry_is_rejected_by_the_onto_half():
    bad = moved_certificate(rook_coords(4, "black"))
    with pytest.raises(AssertionError, match="image is not the target vertex set"):
        check_bishop_certificate(4, "black", coords=bad)


def test_two_swapped_entries_are_rejected_by_the_adjacency_half():
    """A swap is still a bijection onto the same image, so bijectivity cannot
    see it; only the pairwise adjacency comparison can."""
    bad = swapped_certificate(rook_coords(4, "black"))
    with pytest.raises(AssertionError, match="adjacency differs"):
        check_bishop_certificate(4, "black", coords=bad)


def test_honeycomb_one_moved_entry_is_rejected_by_the_onto_half():
    bad = moved_certificate(honeycomb_coords(3))
    with pytest.raises(AssertionError, match="image is not the target vertex set"):
        check_honeycomb_certificate(3, coords=bad)


def test_honeycomb_two_swapped_entries_are_rejected_by_the_adjacency_half():
    bad = swapped_certificate(honeycomb_coords(3))
    with pytest.raises(AssertionError, match="adjacency differs"):
        check_honeycomb_certificate(3, coords=bad)


# --- the two checkers must agree ---------------------------------------------


@pytest.mark.parametrize("tamper", [moved_certificate, swapped_certificate])
def test_verify_isomorphism_rejects_what_the_independent_check_rejects(tamper):
    """Two checkers that share no code must return the same verdict on the same
    wrong certificate. verify_isomorphism has no onto-the-target half, so both
    tamperings -- a vertex isolated in the rook graph while it keeps its bishop
    neighbours, and a swap -- reach only its adjacency comparison: this is the
    test that a verify_isomorphism reduced to injectivity alone cannot pass."""
    bad = tamper(rook_coords(4, "black"))
    with pytest.raises(AssertionError):
        check_bishop_certificate(4, "black", coords=bad)
    with pytest.raises(AssertionError):
        verify_isomorphism(4, "black", coords=bad)
