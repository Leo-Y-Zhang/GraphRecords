"""Board cell sets and explicit graph construction.

Cells are (row, col) with 0 <= row < rows, 0 <= col < cols. Bishop adjacency is
"shares a diagonal", which splits the board by colour: a bishop never changes
the parity of row+col, so the bishop graph has exactly two components.

The triangular honeycomb board at the bottom of this file is the exception that
motivated the rectangular generalisation. Its bishop graph is connected -- there
is no colour split and so no black-plus-white identity to check against.
"""
from itertools import combinations

COLOURS = ("black", "white", "both")


def bishop_cells(rows, colour, cols=None):
    """Cells of the given colour on the rows X cols board, in row-major order.

    `cols` defaults to `rows`, so the two-argument call is the n X n board and
    means exactly what it always did. The rectangular case exists because the
    n-triangular honeycomb bishop graph is the black bishop graph of the
    n X (n+1) board (Wagon 2014), which the suite checks.
    """
    if colour not in COLOURS:
        raise ValueError(f"colour must be one of {COLOURS}, got {colour!r}")
    if cols is None:
        cols = rows
    if colour == "both":
        return [(r, c) for r in range(rows) for c in range(cols)]
    # A bishop never changes the parity of row+col, so a colour IS a parity class.
    parity = 0 if colour == "black" else 1
    return [(r, c) for r in range(rows) for c in range(cols) if (r + c) % 2 == parity]


def bishop_adjacent(a, b):
    """True iff distinct cells a and b share a diagonal."""
    return a != b and (a[0] + a[1] == b[0] + b[1] or a[0] - a[1] == b[0] - b[1])


def adjacency_masks(cells, adjacent):
    """Neighbour bitmasks, index-aligned with cells."""
    index = {cell: i for i, cell in enumerate(cells)}
    nbr = [0] * len(cells)
    for a, b in combinations(cells, 2):
        if adjacent(a, b):
            nbr[index[a]] |= 1 << index[b]
            nbr[index[b]] |= 1 << index[a]
    return nbr


# --- the n-triangular honeycomb board --------------------------------------


def honeycomb_cells(n):
    """Vertices of the n-triangular honeycomb board, in barycentric coordinates.

    A cell is (x, y, z) with x + y + z = n - 1 and all three non-negative, so
    there are n(n+1)/2 of them arranged in a triangle of side n.
    """
    return [(x, y, n - 1 - x - y) for x in range(n) for y in range(n - x)]


def honeycomb_adjacent(a, b):
    """True iff distinct honeycomb cells a and b lie on a common bishop line.

    The triangular grid offers three line families, one per barycentric
    coordinate. A bishop uses the two at +/-60 degrees to the horizontal, which
    are the constant-x and constant-y families; the horizontal family (constant
    z) is a rook-like move on this board and is NOT a bishop move.

    Which two families are chosen does not matter up to isomorphism: the cell
    set is symmetric under permuting the three coordinates, so any pair gives
    the same graph relabelled. The published counts decide the rest, and the
    suite reproduces them.
    """
    return a != b and (a[0] == b[0] or a[1] == b[1])
