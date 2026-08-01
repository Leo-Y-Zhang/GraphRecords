from graphrecords.boards import adjacency_masks, bishop_adjacent, bishop_cells


def test_black_cells_are_even_parity():
    assert bishop_cells(3, "black") == [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]


def test_white_cells_are_odd_parity():
    assert bishop_cells(3, "white") == [(0, 1), (1, 0), (1, 2), (2, 1)]


def test_both_is_the_whole_board():
    assert len(bishop_cells(4, "both")) == 16


def test_adjacency_is_diagonal_only():
    assert bishop_adjacent((0, 0), (1, 1)) is True      # main diagonal
    assert bishop_adjacent((0, 2), (1, 1)) is True      # anti-diagonal
    assert bishop_adjacent((0, 0), (0, 1)) is False     # same row
    assert bishop_adjacent((0, 0), (0, 0)) is False     # not self-adjacent


def test_white_3x3_is_a_four_cycle():
    cells = bishop_cells(3, "white")
    nbr = adjacency_masks(cells, bishop_adjacent)
    assert [bin(m).count("1") for m in nbr] == [2, 2, 2, 2]
