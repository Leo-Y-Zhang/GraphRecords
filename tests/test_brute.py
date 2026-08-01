import pytest
from graphrecords.brute import brute_connected_bishop

# published OEIS DATA, snapshotted from oeis.org
A290719 = [1, 3, 22, 168, 5251, 194751]          # black bishop, n = 1..6
A291595 = [1, 6, 35, 336, 8095, 389502]          # full bishop, n = 1..6


@pytest.mark.parametrize("n,expected", list(enumerate(A290719, start=1)))
def test_matches_published_black(n, expected):
    assert brute_connected_bishop(n, "black") == expected


def test_components_sum_to_the_full_bishop_graph():
    for n in range(1, 7):
        black = brute_connected_bishop(n, "black")
        white = brute_connected_bishop(n, "white")
        assert black + white == A291595[n - 1]


def test_single_cell_board():
    assert brute_connected_bishop(1, "black") == 1
    assert brute_connected_bishop(1, "white") == 0
