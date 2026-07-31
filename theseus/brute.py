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
