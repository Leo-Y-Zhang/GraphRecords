"""Counting connected cell subsets of a rook graph.

A cell subset is connected in the rook graph exactly when the bipartite graph it
induces between x-classes and y-classes is connected, because all cells sharing a
class are mutually adjacent. Both counters below work on that bipartite view.
"""
from functools import lru_cache

from theseus.reduction import class_grid


def _submasks(m):
    """Every submask of m, including m and 0."""
    s = m
    while True:
        yield s
        if s == 0:
            return
        s = (s - 1) & m


def peeling_connected(n, colour):
    """Connected non-empty cell subsets, by exact-support inclusion-exclusion.

    B(X, Y) counts subsets whose x-support is exactly X and y-support exactly Y.
    C(X, Y) counts those that are also connected, found by peeling off the
    component holding the lowest x-class of X. Cost is about 9^n.
    """
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0

    @lru_cache(maxsize=None)
    def ncells(X, Y):
        total = 0
        for i in range(nx):
            if X >> i & 1:
                row = grid[i]
                for j in range(ny):
                    if Y >> j & 1:
                        total += row[j]
        return total

    @lru_cache(maxsize=None)
    def B(X, Y):
        if X == 0 or Y == 0:
            return 1 if (X == 0 and Y == 0) else 0
        total = 0
        for X1 in _submasks(X):
            parity_x = bin(X ^ X1).count("1")
            for Y1 in _submasks(Y):
                sign = -1 if (parity_x + bin(Y ^ Y1).count("1")) & 1 else 1
                total += sign * (1 << ncells(X1, Y1))
        return total

    @lru_cache(maxsize=None)
    def C(X, Y):
        if X == 0 or Y == 0:
            return 1 if (X == 0 and Y == 0) else 0
        total = B(X, Y)
        lowx = X & -X
        for X1 in _submasks(X):
            if not X1 & lowx:
                continue
            for Y1 in _submasks(Y):
                if Y1 == 0 or (X1 == X and Y1 == Y):
                    continue
                total -= C(X1, Y1) * B(X ^ X1, Y ^ Y1)
        return total

    return sum(C(X, Y) for X in range(1, 1 << nx) for Y in range(1, 1 << ny))
