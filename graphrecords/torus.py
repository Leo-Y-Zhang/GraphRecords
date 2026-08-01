"""The n X n torus grid graph C_n square C_n, and exhaustive references.

Vertices are (row, col) with wraparound in both directions, so every vertex has
degree 4 for n >= 3. At n = 2 the wrap makes r+1 and r-1 the same vertex, which
would give a multigraph rather than a simple one -- which is why the OEIS entries
for this family all have offset 3.

Nothing here is fast. These are the L0 references that the sweep in Phase 2 must
agree with.
"""

def torus_cells(n):
    return [(r, c) for r in range(n) for c in range(n)]


def torus_adjacent(n):
    """Neighbour bitmasks for C_n square C_n, index-aligned with torus_cells."""
    if n < 3:
        raise ValueError("the torus grid graph is simple only for n >= 3")
    cells = torus_cells(n)
    index = {cell: i for i, cell in enumerate(cells)}
    nbr = [0] * len(cells)
    for (r, c) in cells:
        i = index[(r, c)]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            j = index[((r + dr) % n, (c + dc) % n)]
            if j != i:
                nbr[i] |= 1 << j
    return nbr


def _closed(nbr):
    return [nbr[i] | (1 << i) for i in range(len(nbr))]


def _cover(mask, table):
    covered = 0
    f = mask
    while f:
        bit = f & -f
        covered |= table[bit.bit_length() - 1]
        f ^= bit
    return covered


def _connected(mask, nbr):
    if mask == 0:
        return False
    low = mask & -mask
    seen = frontier = low
    while frontier:
        reached = 0
        f = frontier
        while f:
            bit = f & -f
            reached |= nbr[bit.bit_length() - 1]
            f ^= bit
        frontier = reached & mask & ~seen
        seen |= frontier
    return seen == mask


def brute_dominating(n):
    nbr = torus_adjacent(n)
    closed = _closed(nbr)
    full = (1 << len(nbr)) - 1
    return sum(1 for m in range(1 << len(nbr)) if _cover(m, closed) == full)


def brute_total_dominating(n):
    nbr = torus_adjacent(n)
    full = (1 << len(nbr)) - 1
    return sum(1 for m in range(1 << len(nbr)) if _cover(m, nbr) == full)


def brute_connected_dominating(n):
    nbr = torus_adjacent(n)
    closed = _closed(nbr)
    full = (1 << len(nbr)) - 1
    return sum(
        1
        for m in range(1, 1 << len(nbr))
        if _cover(m, closed) == full and _connected(m, nbr)
    )


def brute_minimal_dominating(n):
    nbr = torus_adjacent(n)
    closed = _closed(nbr)
    full = (1 << len(nbr)) - 1
    total = 0
    for m in range(1 << len(nbr)):
        if _cover(m, closed) != full:
            continue
        f, minimal = m, True
        while f:
            bit = f & -f
            if _cover(m ^ bit, closed) == full:
                minimal = False
                break
            f ^= bit
        if minimal:
            total += 1
    return total


def brute_connected_induced(n):
    nbr = torus_adjacent(n)
    return sum(1 for m in range(1, 1 << len(nbr)) if _connected(m, nbr))
