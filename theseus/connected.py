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


def _canonical(labels):
    """Relabel a sequence of block ids into restricted-growth form; 0 stays 0."""
    remap = {0: 0}
    out = []
    nxt = 1
    for v in labels:
        w = remap.get(v)
        if w is None:
            w = remap[v] = nxt
            nxt += 1
        out.append(w)
    return tuple(out)


def _frontier_run(n, colour):
    """Run the frontier partition DP. Returns (answer, peak_state_count).

    Sweep the x-classes in order carrying a partition of the y-classes into
    connected blocks, label 0 meaning untouched. At each x-class choose a
    non-empty subset of the y-classes it meets, weighted by the number of ways to
    pick at least one cell in each, and merge every block those y-classes belong
    to. Each x-class meets a contiguous y-interval, so a y-class below every
    remaining interval can never be touched again; a block confined to that
    finalised region can never merge with anything else, so any state carrying a
    stranded block is dropped.
    """
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    states = {(0,) * ny: 1}
    peak = 1
    for i in range(nx):
        lo, hi = intervals[i]
        cols = list(range(lo, hi + 1))
        options = [([], 1)]
        for bits in range(1, 1 << len(cols)):
            weight = 1
            chosen = []
            for k, j in enumerate(cols):
                if bits >> k & 1:
                    weight *= (1 << grid[i][j]) - 1
                    chosen.append(j)
            options.append((chosen, weight))

        # y-classes no later x-class can reach
        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)

        nxt = {}
        for labels, count in states.items():
            for chosen, weight in options:
                if chosen:
                    new = list(labels)
                    merged = {new[j] for j in chosen if new[j]}
                    if merged:
                        target = min(merged)
                        for idx, v in enumerate(new):
                            if v in merged:
                                new[idx] = target
                    else:
                        target = max(new) + 1
                    for j in chosen:
                        new[j] = target
                    key = _canonical(new)
                else:
                    key = labels

                closed = {key[j] for j in range(future_lo) if key[j]}
                active = {key[j] for j in range(future_lo, ny) if key[j]}
                stranded = closed - active
                if len(stranded) > 1 or (stranded and active):
                    continue
                nxt[key] = nxt.get(key, 0) + count * weight
        states = nxt
        peak = max(peak, len(states))

    answer = 0
    for labels, count in states.items():
        if len({v for v in labels if v}) == 1:
            answer += count
    return answer, peak


def frontier_connected(n, colour):
    """Connected non-empty cell subsets, via the frontier partition DP."""
    return _frontier_run(n, colour)[0]


def frontier_state_peak(n, colour):
    """Largest number of live DP states seen while running the frontier DP."""
    return _frontier_run(n, colour)[1]
