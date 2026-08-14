"""The n-triangular honeycomb bishop graph, and the staircase it reduces to.

Everything here is checked against the graph built straight from barycentric
coordinates, never against the class grid, because a grid checked against itself
proves nothing. The published-term tests are the same idea one level up: an
independent author's counts, which a wrong grid cannot reproduce.
"""
import pytest

from graphrecords.boards import (
    adjacency_masks,
    bishop_adjacent,
    bishop_cells,
    honeycomb_adjacent,
    honeycomb_cells,
)
from graphrecords.brute import connected_dominating_count, connected_induced_count
from graphrecords.connected import frontier_connected, peeling_connected
from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.domination import dominating_sets, total_dominating_sets
from graphrecords.reduction import (
    class_grid,
    honeycomb_class_grid,
    rook_coords,
    verify_isomorphism,
)
from graphrecords.targets import terms_by_n

CIS = terms_by_n("A290783")     # connected induced subgraphs, honeycomb
CDS = terms_by_n("A381795")     # connected dominating sets, honeycomb
DOM = terms_by_n("A290941")     # dominating sets, honeycomb -- NOT a target
TOT = terms_by_n("A304553")     # total dominating sets, honeycomb -- NOT a target


def honeycomb_masks(n):
    """Neighbour bitmasks built from the honeycomb definition alone."""
    return adjacency_masks(honeycomb_cells(n), honeycomb_adjacent)


# --- the board itself ------------------------------------------------------


@pytest.mark.parametrize("n", range(1, 9))
def test_cells_are_the_barycentric_triangle(n):
    cells = honeycomb_cells(n)
    assert len(cells) == n * (n + 1) // 2
    assert len(set(cells)) == len(cells)
    for x, y, z in cells:
        assert x >= 0 and y >= 0 and z >= 0
        assert x + y + z == n - 1


def test_adjacency_is_the_two_sixty_degree_families():
    # the horizontal family (constant z) is not a bishop move
    assert honeycomb_adjacent((0, 0, 2), (0, 1, 1)) is True     # constant x
    assert honeycomb_adjacent((0, 0, 2), (1, 0, 1)) is True     # constant y
    assert honeycomb_adjacent((1, 0, 1), (0, 1, 1)) is False    # constant z
    assert honeycomb_adjacent((0, 0, 2), (0, 0, 2)) is False    # not self-adjacent


@pytest.mark.parametrize("n", range(1, 9))
def test_the_graph_has_exactly_one_component(n):
    """Unlike the square board there is no colour split here, so there is no
    black-plus-white identity available as a cross-check further down."""
    nbr = honeycomb_masks(n)
    seen = frontier = 1
    while frontier:
        reached = 0
        f = frontier
        while f:
            bit = f & -f
            reached |= nbr[bit.bit_length() - 1]
            f ^= bit
        frontier = reached & ~seen
        seen |= frontier
    assert seen == (1 << len(nbr)) - 1


# --- the class grid --------------------------------------------------------


@pytest.mark.parametrize("n", range(1, 13))
def test_class_grid_is_the_staircase(n):
    grid, nx, ny = honeycomb_class_grid(n)
    assert (nx, ny) == (n, n)
    assert len(grid) == nx and all(len(row) == ny for row in grid)
    assert all(v in (0, 1) for row in grid for v in row)
    assert sum(sum(row) for row in grid) == n * (n + 1) // 2


@pytest.mark.parametrize("n", range(1, 13))
def test_y_classes_are_swept_in_reverse(n):
    """The y-order is a deliberate choice worth about 16x -- see the docstring
    of honeycomb_class_grid. In the natural order x-class i meets y-classes
    0..n-1-i, so every interval starts at 0, the finalised region is always
    empty and the stranded-block pruning can never fire. Reversed, x-class i
    meets exactly i..n-1 and every step finalises one more y-class."""
    grid, _nx, ny = honeycomb_class_grid(n)
    for i, row in enumerate(grid):
        assert [j for j, v in enumerate(row) if v] == list(range(i, ny))


@pytest.mark.parametrize("n", range(1, 13))
def test_each_x_class_meets_a_contiguous_y_interval(n):
    # locality is what makes the frontier DP's pruning sound
    grid, _, _ = honeycomb_class_grid(n)
    for row in grid:
        used = [j for j, v in enumerate(row) if v]
        assert used == list(range(used[0], used[-1] + 1))


@pytest.mark.parametrize("n", range(1, 7))
def test_reversing_the_y_order_does_not_change_the_count(n):
    """Reversal only renames y-classes, so it is a graph isomorphism. If the
    counts moved, the sweep would be reading order as structure."""
    grid, nx, ny = honeycomb_class_grid(n)
    natural = [row[::-1] for row in grid]
    assert _connected_from_grid(natural, nx, ny) == frontier_connected(n, "honeycomb")


def _connected_from_grid(grid, nx, ny):
    """Count connected subsets of an arbitrary class grid, by brute force."""
    cells = [(i, j) for i in range(nx) for j in range(ny) if grid[i][j]]
    return connected_induced_count(
        adjacency_masks(cells, lambda a, b: a != b and (a[0] == b[0] or a[1] == b[1]))
    )


@pytest.mark.parametrize("n", range(1, 9))
def test_class_grid_dispatches_on_the_honeycomb_selector(n):
    assert class_grid(n, "honeycomb") == honeycomb_class_grid(n)


# --- the grid against the board, not against itself ------------------------


@pytest.mark.parametrize("n", range(1, 8))
def test_grid_reproduces_the_honeycomb_adjacency_exactly(n):
    """Rebuild the graph from the grid and compare it with the graph built from
    barycentric coordinates, pair by pair, under an explicit isomorphism."""
    grid, nx, ny = honeycomb_class_grid(n)
    positions = [(i, j) for i in range(nx) for j in range(ny) if grid[i][j]]
    cells = honeycomb_cells(n)
    assert len(positions) == len(cells)

    # x-class i holds the cells with x = i; within it, y-class n-1-y
    mapping = {(x, y, z): (x, n - 1 - y) for (x, y, z) in cells}
    assert sorted(mapping.values()) == sorted(positions)
    for a in cells:
        for b in cells:
            board = honeycomb_adjacent(a, b)
            pa, pb = mapping[a], mapping[b]
            rook = pa != pb and (pa[0] == pb[0] or pa[1] == pb[1])
            assert board == rook, f"n={n}: {a} vs {b}"


# --- Wagon 2014: the same graph as the black bishop of the n X (n+1) board ---


@pytest.mark.parametrize("n", range(1, 9))
def test_equals_the_black_bishop_graph_of_the_n_by_n_plus_one_board(n):
    """Equal class grids (up to renaming classes) means isomorphic rook graphs,
    so this settles the equivalence rather than sampling it."""
    rect, _, _ = class_grid(n, "black", cols=n + 1)
    hive, _, _ = honeycomb_class_grid(n)
    assert _normalised(rect) == _normalised(hive)


def _normalised(grid):
    """A class grid up to renaming and reordering classes."""
    rows = sorted(tuple(row) for row in grid)
    return sorted(tuple(col) for col in zip(*rows, strict=True))


@pytest.mark.parametrize("n", range(1, 5))
def test_explicit_isomorphism_to_the_rectangular_black_bishop_board(n):
    """The class-grid argument above is the proof; this is the direct check that
    the two graphs really do have the same edge count and degree sequence."""
    hive = honeycomb_masks(n)
    cells = bishop_cells(n, "black", cols=n + 1)
    rect = adjacency_masks(cells, bishop_adjacent)
    assert len(hive) == len(rect)
    assert sorted(bin(m).count("1") for m in hive) == sorted(
        bin(m).count("1") for m in rect
    )


@pytest.mark.parametrize("rows", range(1, 7))
@pytest.mark.parametrize("cols", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_the_reduction_holds_on_rectangular_boards(rows, cols, colour):
    verify_isomorphism(rows, colour, cols=cols)


@pytest.mark.parametrize("n", range(1, 9))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_square_boards_are_unchanged_by_the_generalisation(n, colour):
    assert bishop_cells(n, colour) == bishop_cells(n, colour, cols=n)
    assert rook_coords(n, colour) == rook_coords(n, colour, cols=n)


# --- counters against brute force over the honeycomb graph -----------------


@pytest.mark.parametrize("n", range(1, 7))
def test_connected_induced_agrees_with_brute_force(n):
    assert frontier_connected(n, "honeycomb") == connected_induced_count(
        honeycomb_masks(n)
    )


@pytest.mark.parametrize("n", range(1, 7))
def test_connected_dominating_agrees_with_brute_force(n):
    assert connected_dominating_sets(n, "honeycomb") == connected_dominating_count(
        honeycomb_masks(n)
    )


@pytest.mark.parametrize("n", range(1, 7))
def test_peeling_agrees_with_the_frontier_dp(n):
    assert peeling_connected(n, "honeycomb") == frontier_connected(n, "honeycomb")


# --- counters against published terms --------------------------------------


@pytest.mark.parametrize("n", sorted(CIS))
def test_reproduces_every_published_connected_induced_term(n):
    assert frontier_connected(n, "honeycomb") == CIS[n]


@pytest.mark.parametrize("n", sorted(CDS))
def test_reproduces_every_published_connected_dominating_term(n):
    assert connected_dominating_sets(n, "honeycomb") == CDS[n]


@pytest.mark.parametrize("n", sorted(DOM)[:12])
def test_reproduces_every_published_dominating_term(n):
    """A290941 is NOT a contribution target -- it is published to n=50 already.
    It is here as an anchor: an independent author's counts for this exact
    graph, reaching far past anything brute force can see."""
    assert dominating_sets(n, "honeycomb") == DOM[n]


@pytest.mark.parametrize("n", sorted(TOT)[:9])
def test_reproduces_every_published_total_dominating_term(n):
    """A304553 is likewise published to n=50 and is not a target. Total
    domination needs class populations rather than mere occupancy, so it is the
    expensive one and the suite only takes it as far as it stays cheap."""
    assert total_dominating_sets(n, "honeycomb") == TOT[n]
