"""The bishop-to-rook reduction.

Theorem. For cells of one colour on the n X n board, the map
    phi(r, c) = ((r + c) // 2, (r - c + n) // 2)
is injective, and two distinct cells share a diagonal iff their images agree in
the first coordinate (anti-diagonal) or the second (main diagonal).

Proof. Within one colour r+c has fixed parity, so r-c does too. On values of one
parity both t -> t // 2 and t -> (t + n) // 2 are strictly monotone, hence
injective. Cells share an anti-diagonal iff r+c matches, i.e. iff the first
coordinates agree; they share a main diagonal iff r-c matches, i.e. iff the
second coordinates agree. The pair (r+c, r-c) determines (r, c), giving
injectivity of phi.

So the single-colour bishop graph IS the rook graph on the image cells: adjacent
iff sharing an x-class or a y-class.
"""
from itertools import combinations

from theseus.boards import bishop_adjacent, bishop_cells


def rook_coords(n, colour):
    """Map each cell of the given colour to its (x-class, y-class) pair."""
    if colour == "both":
        raise ValueError("the reduction applies per colour; 'both' is disconnected")
    return {
        (r, c): ((r + c) // 2, (r - c + n) // 2)
        for (r, c) in bishop_cells(n, colour)
    }


def verify_isomorphism(n, colour):
    """Check the theorem exhaustively for this board. Raises on violation."""
    coords = rook_coords(n, colour)
    if len(set(coords.values())) != len(coords):
        raise AssertionError(f"phi not injective for n={n} colour={colour}")
    for a, b in combinations(coords, 2):
        rook = coords[a][0] == coords[b][0] or coords[a][1] == coords[b][1]
        if bishop_adjacent(a, b) != rook:
            raise AssertionError(
                f"n={n} colour={colour}: {a} vs {b} bishop="
                f"{bishop_adjacent(a, b)} rook={rook}"
            )


def class_grid(n, colour):
    """Cell counts per (x-class, y-class), with classes renumbered from zero."""
    coords = rook_coords(n, colour)
    xs = sorted({x for x, _ in coords.values()})
    ys = sorted({y for _, y in coords.values()})
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: j for j, y in enumerate(ys)}
    grid = [[0] * len(ys) for _ in xs]
    for (x, y) in coords.values():
        grid[xi[x]][yi[y]] += 1
    return grid, len(xs), len(ys)
