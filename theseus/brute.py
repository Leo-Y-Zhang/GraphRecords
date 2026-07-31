"""Exhaustive reference counters (verification level L0).

Deliberately naive: builds the graph straight from the definition and walks every
subset. Too slow to be useful beyond about 22 cells, which is the point -- it is
the independent check that the fast algorithms are counting the right thing.
"""
from theseus.boards import adjacency_masks, bishop_adjacent, bishop_cells


def connected_induced_count(nbr):
    """Number of non-empty vertex subsets inducing a connected subgraph."""
    m = len(nbr)
    total = 0
    for mask in range(1, 1 << m):
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
        if seen == mask:
            total += 1
    return total


def brute_connected_bishop(n, colour):
    cells = bishop_cells(n, colour)
    if not cells:
        return 0
    return connected_induced_count(adjacency_masks(cells, bishop_adjacent))


def dominating_count(nbr):
    """Number of vertex subsets S such that every vertex is in S or adjacent to it."""
    m = len(nbr)
    closed = [nbr[i] | (1 << i) for i in range(m)]
    full = (1 << m) - 1
    total = 0
    for mask in range(1 << m):
        covered = 0
        f = mask
        while f:
            bit = f & -f
            covered |= closed[bit.bit_length() - 1]
            f ^= bit
        if covered == full:
            total += 1
    return total


def brute_dominating_bishop(n, colour):
    cells = bishop_cells(n, colour)
    if not cells:
        return 1          # the empty set vacuously dominates the empty graph
    return dominating_count(adjacency_masks(cells, bishop_adjacent))


def total_dominating_count(nbr):
    """Subsets S where every vertex has a neighbour in S.

    Open neighbourhood, so a vertex does not dominate itself.
    """
    m = len(nbr)
    full = (1 << m) - 1
    total = 0
    for mask in range(1 << m):
        covered = 0
        f = mask
        while f:
            bit = f & -f
            covered |= nbr[bit.bit_length() - 1]
            f ^= bit
        if covered == full:
            total += 1
    return total


def brute_total_dominating_bishop(n, colour):
    cells = bishop_cells(n, colour)
    if not cells:
        return 1
    return total_dominating_count(adjacency_masks(cells, bishop_adjacent))


def minimal_dominating_count(nbr):
    """Dominating sets no proper subset of which dominates.

    Domination is upward closed, so it suffices to check that dropping any one
    element breaks it.
    """
    m = len(nbr)
    closed = [nbr[i] | (1 << i) for i in range(m)]
    full = (1 << m) - 1

    def dominates(mask):
        covered = 0
        f = mask
        while f:
            bit = f & -f
            covered |= closed[bit.bit_length() - 1]
            f ^= bit
        return covered == full

    total = 0
    for mask in range(1 << m):
        if not dominates(mask):
            continue
        f = mask
        minimal = True
        while f:
            bit = f & -f
            if dominates(mask ^ bit):
                minimal = False
                break
            f ^= bit
        if minimal:
            total += 1
    return total


def brute_minimal_dominating_bishop(n, colour):
    cells = bishop_cells(n, colour)
    if not cells:
        return 1
    return minimal_dominating_count(adjacency_masks(cells, bishop_adjacent))
