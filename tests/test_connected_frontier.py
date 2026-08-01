import pytest
from theseus.connected import frontier_connected, peeling_connected
from theseus.targets import terms_by_n

BLACK = terms_by_n("A290719")   # offset 1
WHITE = terms_by_n("A290769")   # offset 2 -- a 1 X 1 board has no white cells


@pytest.mark.parametrize("n", range(1, 9))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_the_peeling_counter(n, colour):
    assert frontier_connected(n, colour) == peeling_connected(n, colour)


@pytest.mark.parametrize("n", sorted(BLACK))
def test_reproduces_every_published_black_bishop_term(n):
    assert frontier_connected(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", sorted(WHITE))
def test_reproduces_every_published_white_bishop_term(n):
    assert frontier_connected(n, "white") == WHITE[n]


@pytest.mark.parametrize("n", range(1, 10))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_transposed_sweep_agrees(n, colour):
    """Sweeping the y-classes must give the same count as sweeping the x-classes.

    It is the same bipartite graph seen from the other side, so the answer is
    forced; but the sweep order, the intervals and every pruning decision differ.
    A direction-dependent bug in the frontier logic shows up here, and this costs
    seconds where the peeling cross-check costs hours.
    """
    assert frontier_connected(n, colour) == frontier_connected(n, colour, transpose=True)


@pytest.mark.parametrize("n", [7, 9, 11, 12])
def test_contiguity_holds_in_both_directions(n):
    """The transposed sweep's pruning is only sound if y-classes also meet a
    contiguous x-interval. Asserted, not assumed."""
    from theseus.reduction import class_grid
    grid, nx, ny = class_grid(n, "black")
    for row in grid:
        used = [j for j, v in enumerate(row) if v]
        assert used == list(range(used[0], used[-1] + 1))
    for j in range(ny):
        used = [i for i in range(nx) if grid[i][j]]
        assert used == list(range(used[0], used[-1] + 1))
