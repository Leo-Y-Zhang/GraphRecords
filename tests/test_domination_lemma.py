"""The support-collapse lemma for domination on a rook graph.

In a rook graph N[(i,j)] is the whole of x-class i together with the whole of
y-class j. So a cell is dominated exactly when its x-class or its y-class
contains a member of S -- which depends only on WHICH CLASSES S touches, never on
which cells it uses.

Equivalently: S dominates iff (x-support(S), y-support(S)) is a vertex cover of
the bipartite graph whose edges are the cells.

Both statements are tested against brute force here before anything is built on
them.
"""
import pytest
from theseus.boards import bishop_cells
from theseus.brute import brute_dominating_bishop
from theseus.reduction import class_grid, rook_coords
from theseus.targets import terms_by_n

BLACK = terms_by_n("A289164")   # dominating sets, black bishop graph, 15 terms
WHITE = terms_by_n("A289170")   # dominating sets, white bishop graph, 14 terms
FULL = terms_by_n("A295898")    # dominating sets, full bishop graph


@pytest.mark.parametrize("n", range(1, 7))
def test_brute_matches_published_black(n):
    assert brute_dominating_bishop(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", range(2, 7))
def test_brute_matches_published_white(n):
    assert brute_dominating_bishop(n, "white") == WHITE[n]


@pytest.mark.parametrize("n", range(2, 7))
def test_components_multiply_for_domination(n):
    """Unlike connected subgraphs, which add, dominating sets multiply across
    the two components: a set dominates the union iff it dominates each part."""
    black = brute_dominating_bishop(n, "black")
    white = brute_dominating_bishop(n, "white")
    assert black * white == FULL[n]


def _supports_and_domination(n, colour):
    """Yield (x-support, y-support, dominates?) for every cell subset."""
    coords = rook_coords(n, colour)
    cells = bishop_cells(n, colour)
    grid, nx, ny = class_grid(n, colour)
    xs = sorted({x for x, _ in coords.values()})
    ys = sorted({y for _, y in coords.values()})
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: j for j, y in enumerate(ys)}
    classes = [(xi[coords[c][0]], yi[coords[c][1]]) for c in cells]

    from theseus.boards import adjacency_masks, bishop_adjacent
    nbr = adjacency_masks(cells, bishop_adjacent)
    closed = [nbr[i] | (1 << i) for i in range(len(cells))]
    full = (1 << len(cells)) - 1

    for mask in range(1 << len(cells)):
        R = C = 0
        covered = 0
        f = mask
        while f:
            bit = f & -f
            k = bit.bit_length() - 1
            R |= 1 << classes[k][0]
            C |= 1 << classes[k][1]
            covered |= closed[k]
            f ^= bit
        yield R, C, covered == full


@pytest.mark.parametrize("n", range(1, 6))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_domination_depends_only_on_support(n, colour):
    """Two subsets with the same support must agree on whether they dominate."""
    seen = {}
    for R, C, dominates in _supports_and_domination(n, colour):
        key = (R, C)
        if key in seen:
            assert seen[key] == dominates, (
                f"n={n} {colour}: support {key} both dominates and does not"
            )
        else:
            seen[key] = dominates


@pytest.mark.parametrize("n", range(1, 6))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_dominating_iff_support_is_a_vertex_cover(n, colour):
    """S dominates iff no cell lies outside both supports."""
    grid, nx, ny = class_grid(n, colour)
    for R, C, dominates in _supports_and_domination(n, colour):
        uncovered = any(
            grid[i][j]
            for i in range(nx) if not (R >> i & 1)
            for j in range(ny) if not (C >> j & 1)
        )
        assert dominates == (not uncovered)
