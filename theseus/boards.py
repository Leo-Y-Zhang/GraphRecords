"""Board cell sets and explicit graph construction.

Cells are (row, col) with 0 <= row, col < n. Bishop adjacency is "shares a
diagonal", which splits the board by colour: a bishop never changes the parity
of row+col, so the n X n bishop graph has exactly two components.
"""
from itertools import combinations

COLOURS = ("black", "white", "both")


def bishop_cells(n, colour):
    """Cells of the n X n board of the given colour, in row-major order."""
    if colour not in COLOURS:
        raise ValueError(f"colour must be one of {COLOURS}, got {colour!r}")
    if colour == "both":
        keep = lambda r, c: True
    elif colour == "black":
        keep = lambda r, c: (r + c) % 2 == 0
    else:
        keep = lambda r, c: (r + c) % 2 == 1
    return [(r, c) for r in range(n) for c in range(n) if keep(r, c)]


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
