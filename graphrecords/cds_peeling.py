"""An independent count of connected dominating sets, for cross-checking.

`connected_domination.py` counts these with a frontier partition DP that carries
a requirement mask through the sweep. It reproduces brute force to n=6 and every
published term to n=8, but brute force cannot reach further, so the staged terms
a(9) and a(10) of A289145 and A289169 rested on that one algorithm.

This reaches the same numbers a different way. Two facts make it a two-line
counter rather than a second sweep:

* In a rook graph a cell's closed neighbourhood is the whole of its x-class
  together with the whole of its y-class. So whether a set dominates depends only
  on WHICH classes it occupies -- never on how many cells it puts in them.
  Domination is therefore a predicate on the *support*, and the exact-support
  peeling counter already enumerates supports.
* A set dominates exactly when no board cell avoids it on both sides: there must
  be no cell whose x-class is outside X and whose y-class is outside Y. That is
  `ncells(complement X, complement Y) == 0`.

So the answer is the peeling counter's C(X, Y) summed over the dominating
supports. It shares no code path with the frontier DP beyond the class grid, and
in particular nothing at all with that DP's requirement-mask bookkeeping, which
is its subtlest part and the likeliest place for an error to hide.

Cost is the peeling cost, about 9^n: seconds at n=9, minutes at n=10. That is
affordable exactly where it is needed, because the staged terms stop at n=10.
"""
from graphrecords.connected import peeling_machinery


def peeling_connected_dominating(n, colour):
    """Non-empty cell subsets that dominate and induce a connected subgraph."""
    nx, ny, ncells, C = peeling_machinery(n, colour)
    if C is None:
        return 0

    full_x = (1 << nx) - 1
    full_y = (1 << ny) - 1
    total = 0
    for X in range(1, 1 << nx):
        rest_x = full_x ^ X
        for Y in range(1, 1 << ny):
            # Every cell outside both supports is undominated, so one is enough
            # to rule the whole support out -- before paying for C(X, Y).
            if ncells(rest_x, full_y ^ Y) == 0:
                total += C(X, Y)
    return total
