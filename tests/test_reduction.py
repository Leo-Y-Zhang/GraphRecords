import pytest
from graphrecords.reduction import rook_coords, verify_isomorphism, class_grid


@pytest.mark.parametrize("n", range(1, 13))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_bishop_graph_is_a_rook_graph(n, colour):
    verify_isomorphism(n, colour)


def test_map_is_injective():
    for n in range(1, 13):
        for colour in ("black", "white"):
            image = list(rook_coords(n, colour).values())
            assert len(image) == len(set(image))


def test_class_grid_totals_match_cell_count():
    for n in range(1, 10):
        grid, nx, ny = class_grid(n, "black")
        assert sum(sum(row) for row in grid) == len(rook_coords(n, "black"))
        assert len(grid) == nx and all(len(r) == ny for r in grid)


def test_each_x_class_meets_a_contiguous_y_interval():
    # locality is what makes the frontier DP affordable
    grid, nx, ny = class_grid(9, "black")
    for row in grid:
        used = [j for j, v in enumerate(row) if v]
        assert used == list(range(used[0], used[-1] + 1))


def test_both_is_rejected():
    with pytest.raises(ValueError):
        rook_coords(4, "both")


@pytest.mark.parametrize("n", range(1, 13))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_class_grid_is_zero_one(n, colour):
    """phi is injective, so an (x-class, y-class) pair holds at most one cell.

    The domination counters rely on this: it makes a cell subset the same thing
    as a subset of the occupied grid positions, so per-class counts are just
    populations rather than multiplicities.
    """
    grid, nx, ny = class_grid(n, colour)
    assert all(v in (0, 1) for row in grid for v in row)
