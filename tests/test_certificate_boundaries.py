"""Certificate boundary cases that valid-board sweeps cannot distinguish."""

import pytest

from graphrecords.independent_check import (
    check_bishop_certificate,
    check_certificate,
    check_honeycomb_certificate,
    honeycomb_coords,
)
from graphrecords.reduction import rook_coords, verify_isomorphism


@pytest.mark.parametrize("colour", ["black", "white"])
def test_smallest_edge_certificate_and_colliding_images(colour):
    coords = rook_coords(2, colour)
    verify_isomorphism(2, colour, coords=coords)
    a, b = coords
    coords[b] = coords[a]
    # Both cells are adjacent even after the collision. Only injectivity can
    # reject this certificate; the pairwise adjacency test cannot see it.
    with pytest.raises(AssertionError, match="not injective"):
        verify_isomorphism(2, colour, coords=coords)


@pytest.mark.parametrize("kind", ["bishop", "honeycomb"])
@pytest.mark.parametrize("corruption", ["empty", "missing", "extra", "collision"])
def test_independent_check_rejects_incomplete_or_extra_certificates(kind, corruption):
    if kind == "bishop":
        coords = rook_coords(3, "black")

        def check(mapping):
            check_bishop_certificate(3, "black", coords=mapping)
    else:
        coords = honeycomb_coords(3)

        def check(mapping):
            check_honeycomb_certificate(3, coords=mapping)

    check(coords)
    bad = dict(coords)
    a, b = sorted(coords)[:2]
    if corruption == "empty":
        bad.clear()
    elif corruption == "missing":
        del bad[a]
    elif corruption == "extra":
        # Reuse an existing image so that class renumbering cannot expose it.
        bad[tuple(-1 for _ in a)] = coords[a]
    else:
        bad[b] = coords[a]
    with pytest.raises(AssertionError):
        check(bad)


@pytest.mark.parametrize("edge", [False, True])
def test_generic_certificate_requires_both_directions_of_adjacency(edge):
    source = ["a", "b"]
    mapping = {"a": (0, 0), "b": (0, 1) if edge else (1, 1)}
    target = set(mapping.values())

    def adjacent(a, b):
        return a != b and edge

    check_certificate("two vertices", source, adjacent, mapping, target)
    # Same bijection, wrong source relation: test added AND deleted edges.
    with pytest.raises(AssertionError, match="adjacency differs"):
        check_certificate("wrong edge", source, lambda a, b: not edge, mapping, target)


def test_generic_certificate_rejects_a_wrong_target_count():
    mapping = {"a": (0, 0)}
    check_certificate("singleton", ["a"], lambda a, b: False, mapping, {(0, 0)})
    with pytest.raises(AssertionError, match="target vertex set"):
        check_certificate("wrong target", ["a"], lambda a, b: False,
                          mapping, {(0, 0), (0, 1)})
