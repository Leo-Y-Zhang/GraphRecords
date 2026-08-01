"""The independent second algorithm for connected dominating sets.

`connected_domination.py` counts these with a frontier partition DP. Nothing else
in the repository could confirm it: brute force dies at n=6, so the staged terms
a(9) and a(10) of A289145/A289169 rested on one algorithm and one algorithm only.

The peeling counter here shares no code path with that DP beyond the class grid.
It reaches the same numbers by exact-support inclusion-exclusion, and domination
enters as a predicate on the support rather than as a sweep invariant -- so a
mistake in the DP's requirement-mask bookkeeping, which is the subtlest part of
it, cannot be reproduced here.
"""
import pytest

from graphrecords.brute import brute_connected_dominating_bishop
from graphrecords.cds_peeling import peeling_connected_dominating
from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.targets import terms_by_n

BLACK = terms_by_n("A289145")
WHITE = terms_by_n("A289169")


@pytest.mark.parametrize("n", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_brute_force(n, colour):
    assert peeling_connected_dominating(n, colour) == (
        brute_connected_dominating_bishop(n, colour)
    )


@pytest.mark.parametrize("n", sorted(BLACK))
def test_reproduces_every_published_black_term(n):
    assert peeling_connected_dominating(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", sorted(WHITE))
def test_reproduces_every_published_white_term(n):
    assert peeling_connected_dominating(n, "white") == WHITE[n]


@pytest.mark.parametrize("n", range(1, 9))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_the_frontier_dp(n, colour):
    """The cross-check property itself, at sizes cheap enough for the gate.

    n=9 and n=10 are the staged terms and are far too slow for a test run; they
    are checked by tools/crosscheck_cds.py and recorded in PAPER.md.
    """
    assert peeling_connected_dominating(n, colour) == (
        connected_dominating_sets(n, colour)
    )


def test_domination_is_decided_by_the_support_alone():
    """Why this counter is allowed to filter on (X, Y) at all.

    In a rook graph a cell's closed neighbourhood is its whole x-class plus its
    whole y-class, so whether a set dominates depends only on WHICH classes it
    occupies, never on how many cells it puts in them. If that were false the
    filter here would be unsound, and every number this module produces would be
    wrong in the same direction.
    """
    from itertools import combinations

    from graphrecords.boards import adjacency_masks, bishop_adjacent, bishop_cells
    from graphrecords.reduction import rook_coords

    n, colour = 5, "black"
    cells = bishop_cells(n, colour)
    nbr = adjacency_masks(cells, bishop_adjacent)
    coords = rook_coords(n, colour)
    full = (1 << len(cells)) - 1

    # Group every small subset by its (x-class, y-class) support and assert the
    # whole group agrees about domination. A single disagreement would make the
    # filter unsound and every number this module produces wrong.
    verdict = {}
    for size in range(1, 4):
        for sub in combinations(range(len(cells)), size):
            mask = 0
            for i in sub:
                mask |= 1 << i
            covered = mask
            for i in sub:
                covered |= nbr[i]
            dominated = covered & full == full
            support = (frozenset(coords[cells[i]][0] for i in sub),
                       frozenset(coords[cells[i]][1] for i in sub))
            if support in verdict:
                assert verdict[support] == dominated, (
                    f"two subsets share support {support} but disagree about "
                    f"domination -- the peeling filter would be unsound"
                )
            else:
                verdict[support] = dominated
    assert verdict
