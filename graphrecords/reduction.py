"""The bishop-to-rook reduction.

Theorem. For cells of one colour on the rows X cols board, the map
    phi(r, c) = ((r + c) // 2, (r - c + cols) // 2)
is injective, and two distinct cells share a diagonal iff their images agree in
the first coordinate (anti-diagonal) or the second (main diagonal).

Proof. Within one colour r+c has fixed parity, so r-c does too. On values of one
parity both t -> t // 2 and t -> (t + cols) // 2 are strictly monotone, hence
injective. Cells share an anti-diagonal iff r+c matches, i.e. iff the first
coordinates agree; they share a main diagonal iff r-c matches, i.e. iff the
second coordinates agree. The pair (r+c, r-c) determines (r, c), giving
injectivity of phi. Nothing in that argument uses rows = cols; the offset cols
is there only to keep the second coordinate non-negative, since r - c is at
least -(cols - 1).

So the single-colour bishop graph IS the rook graph on the image cells: adjacent
iff sharing an x-class or a y-class.

The n-triangular honeycomb bishop graph reduces the same way, to a STAIRCASE
rather than to the square board's diamond -- see honeycomb_class_grid.
"""
from itertools import combinations

from graphrecords.boards import bishop_adjacent, bishop_cells

# `colour` selects which component's class structure to build. Alongside the two
# board colours it accepts this selector, which is not a colour at all: the
# honeycomb bishop graph is connected and has no colour split. It travels in the
# same argument so that every counter built on class_grid -- connectivity,
# domination, connected domination, peeling -- reaches the honeycomb board with
# no change at all, which is the point: the honeycomb terms are produced by the
# exact code the square-board terms were, differing only in the grid handed to
# it.
HONEYCOMB = "honeycomb"


def rook_coords(rows, colour, cols=None):
    """Map each cell of the given colour to its (x-class, y-class) pair."""
    if colour == "both":
        raise ValueError("the reduction applies per colour; 'both' is disconnected")
    if cols is None:
        cols = rows
    return {
        (r, c): ((r + c) // 2, (r - c + cols) // 2)
        for (r, c) in bishop_cells(rows, colour, cols=cols)
    }


def verify_isomorphism(rows, colour, cols=None):
    """Check the theorem exhaustively for this board. Raises on violation."""
    coords = rook_coords(rows, colour, cols=cols)
    shape = f"{rows}X{cols if cols is not None else rows}"
    if len(set(coords.values())) != len(coords):
        raise AssertionError(f"phi not injective for {shape} colour={colour}")
    for a, b in combinations(coords, 2):
        rook = coords[a][0] == coords[b][0] or coords[a][1] == coords[b][1]
        if bishop_adjacent(a, b) != rook:
            raise AssertionError(
                f"{shape} colour={colour}: {a} vs {b} bishop="
                f"{bishop_adjacent(a, b)} rook={rook}"
            )


def honeycomb_class_grid(n):
    """Class grid of the n-triangular honeycomb bishop graph: an n X n staircase.

    A honeycomb cell is (x, y, z) with x + y + z = n - 1, and it is adjacent to
    another exactly when the two agree in x or agree in y. Since z is determined
    by x and y, the cell IS its (x, y) pair and the graph IS the rook graph on
    the staircase {(x, y) : x, y >= 0, x + y <= n - 1}. No phi is needed: the
    barycentric coordinates are already the class coordinates.

    THE Y-CLASS ORDER IS REVERSED, AND THAT IS WORTH ABOUT 16x. Every counter
    built on a class grid sweeps the x-classes and prunes on the fact that each
    x-class meets a contiguous y-interval: once no later x-class can reach a
    y-class, that y-class is finalised, states merge, and blocks confined to the
    finalised region are dropped. In the natural y-order x-class i meets
    y-classes 0..n-1-i, so EVERY interval starts at 0, nothing is ever finalised
    and none of that pruning can fire. Reversing the y-order makes x-class i meet
    exactly i..n-1, so each step finalises one more y-class. Measured at n=9:

        connected induced subgraphs   115974 -> 33817 peak states
        connected dominating sets     839563 -> 51405 peak states

    Reversal only renames y-classes, so it is a graph isomorphism and cannot
    change any count; tests/test_honeycomb.py asserts both halves of that -- the
    shape of the intervals, and that the natural order returns the same answer.
    """
    return [[1 if i <= j else 0 for j in range(n)] for i in range(n)], n, n


def class_grid(rows, colour, cols=None):
    """Cell counts per (x-class, y-class), with classes renumbered from zero."""
    if colour == HONEYCOMB:
        if cols is not None:
            raise ValueError("the honeycomb board is triangular; cols does not apply")
        return honeycomb_class_grid(rows)
    coords = rook_coords(rows, colour, cols=cols)
    xs = sorted({x for x, _ in coords.values()})
    ys = sorted({y for _, y in coords.values()})
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: j for j, y in enumerate(ys)}
    grid = [[0] * len(ys) for _ in xs]
    for (x, y) in coords.values():
        grid[xi[x]][yi[y]] += 1
    return grid, len(xs), len(ys)
