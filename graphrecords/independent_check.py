"""The reduction certificates re-checked from first principles, independently.

verify_isomorphism in reduction.py is the reduction theorem's own exhaustive
check, and it had no second: mutation testing (audit/mutants/SAT_checkers.md,
GraphRecords M2) dropped its adjacency-equivalence half, kept only injectivity,
and the whole gate still passed, pytest suite included, because every caller
runs the same function body. This module is that second. It shares nothing with
verify_isomorphism beyond the certificate it is handed: no bishop_cells, no
bishop_adjacent, no honeycomb helpers -- both graphs are rebuilt here straight
from their definitions, the claimed mapping is applied, and it is held to

  (a) being a bijection onto the target vertex set, which is the set of
      occupied positions of the class grid the counters actually run on; and
  (b) for every pair of source vertices, adjacency in the source iff adjacency
      of the two images in the target (a common row or a common column).

What the certificates are. Nothing is stored on disk. The certificate for the
rows X cols board of one colour is the mapping the code commits to,
rook_coords(rows, colour, cols), a dict cell -> (x-class, y-class) built from
phi(r, c) = ((r + c) // 2, (r - c + cols) // 2). The certificate for the
n-triangular honeycomb board is the identification honeycomb_class_grid
documents, (x, y, z) -> (x, n - 1 - y): x-class i holds the cells with x = i,
and the y-classes are swept in reverse. class_grid renumbers the square board's
classes from zero, so onto the grid the mapping is phi followed by the rank of
each coordinate among the values phi takes. Rank is injective on each coordinate
separately, so which pairs agree in a coordinate -- all that rook adjacency
reads -- is exactly what it was under phi; the renumbering is redone here, not
borrowed.

What this cannot do. A re-derivation checks certificates, not checkers: a
broken verify_isomorphism whose certificate is right leaves nothing here to
notice. What it removes is verify_isomorphism as the single point of failure --
a wrong certificate now fails the gate whatever state that function is in --
and the two checkers are additionally held to agreeing on tampered
certificates, which is what makes a gutted verify_isomorphism visible here.
"""
from itertools import combinations

from graphrecords.reduction import HONEYCOMB, class_grid, rook_coords

# --- the graphs, by definition ---------------------------------------------


def bishop_vertices(rows, colour, cols):
    """Cells of one colour: (r, c) with 0 <= r < rows, 0 <= c < cols, and r + c
    even for black, odd for white."""
    parity = {"black": 0, "white": 1}[colour]
    return [(r, c) for r in range(rows) for c in range(cols) if (r + c) % 2 == parity]


def share_a_diagonal(a, b):
    """Bishop adjacency: distinct cells on a common anti-diagonal (r + c equal)
    or a common main diagonal (r - c equal)."""
    return a != b and (a[0] + a[1] == b[0] + b[1] or a[0] - a[1] == b[0] - b[1])


def honeycomb_vertices(n):
    """Barycentric (x, y, z), all non-negative, with x + y + z = n - 1."""
    return [(x, y, n - 1 - x - y) for x in range(n) for y in range(n - x)]


def share_a_honeycomb_line(a, b):
    """Honeycomb bishop adjacency: distinct cells agreeing in x or in y."""
    return a != b and (a[0] == b[0] or a[1] == b[1])


def share_a_line(p, q):
    """Rook adjacency: distinct positions in a common row or a common column."""
    return p != q and (p[0] == q[0] or p[1] == q[1])


def occupied(grid):
    """The vertex set of the rook graph a class grid stands for."""
    return {(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v}


# --- the certificates ------------------------------------------------------


def honeycomb_coords(n):
    """The honeycomb certificate: x-class i holds the cells with x = i, and
    within it the y-classes run in reverse (see honeycomb_class_grid)."""
    return {(x, y, z): (x, n - 1 - y) for (x, y, z) in honeycomb_vertices(n)}


def renumbered(coords):
    """phi followed by the rank of each coordinate among the values phi takes."""
    xs = {x: i for i, x in enumerate(sorted({x for x, _ in coords.values()}))}
    ys = {y: j for j, y in enumerate(sorted({y for _, y in coords.values()}))}
    return {v: (xs[x], ys[y]) for v, (x, y) in coords.items()}


# --- the check -------------------------------------------------------------


def check_certificate(name, source, adjacent, mapping, target):
    """Hold `mapping` to being an isomorphism from the graph (source, adjacent)
    onto the rook graph on `target`. Raises AssertionError on the first
    violation, naming which half of the claim failed."""
    if set(mapping) != set(source):
        raise AssertionError(f"{name}: certificate does not cover the vertex set exactly")
    images = [mapping[v] for v in source]
    if len(set(images)) != len(images):
        raise AssertionError(f"{name}: mapping is not injective")
    if set(images) != set(target):
        raise AssertionError(f"{name}: image is not the target vertex set")
    for a, b in combinations(source, 2):
        if adjacent(a, b) != share_a_line(mapping[a], mapping[b]):
            raise AssertionError(f"{name}: adjacency differs at {a} vs {b}")


def check_bishop_certificate(rows, colour, cols=None, coords=None):
    """The rows X cols board of one colour against the class grid it reduces to.

    `coords` substitutes a certificate for the committed one; the tamper checks
    use it, no real caller does.
    """
    if cols is None:
        cols = rows
    if coords is None:
        coords = rook_coords(rows, colour, cols=cols)
    grid, _, _ = class_grid(rows, colour, cols=cols)
    check_certificate(
        f"{rows}X{cols} {colour}",
        bishop_vertices(rows, colour, cols),
        share_a_diagonal,
        renumbered(coords),
        occupied(grid),
    )


def check_honeycomb_certificate(n, coords=None):
    """The n-triangular honeycomb board against the staircase it reduces to."""
    if coords is None:
        coords = honeycomb_coords(n)
    grid, _, _ = class_grid(n, HONEYCOMB)
    check_certificate(
        f"honeycomb n={n}",
        honeycomb_vertices(n),
        share_a_honeycomb_line,
        dict(coords),
        occupied(grid),
    )


# --- tampering, for the checks that prove the check can fail ---------------


def moved_certificate(coords):
    """One entry moved: the lowest-sorted vertex is sent one past the largest
    x-class and one past the largest y-class, a row and a column no vertex
    uses. Still injective, so injectivity cannot see it; the onto-the-target
    half is what reports it, and the vertex is now isolated in the rook graph
    while it keeps its bishop neighbours, so a checker with no notion of a
    target still has to reject it through adjacency."""
    cell = min(coords)
    x_max = max(x for x, _ in coords.values())
    y_max = max(y for _, y in coords.values())
    out = dict(coords)
    out[cell] = (x_max + 1, y_max + 1)
    return out


def swapped_certificate(coords):
    """Two entries exchanged: still a bijection onto the same image, so only
    the adjacency half can see it."""
    a, b = sorted(coords)[:2]
    out = dict(coords)
    out[a], out[b] = coords[b], coords[a]
    return out
