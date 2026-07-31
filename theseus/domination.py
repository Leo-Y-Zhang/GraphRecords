"""Counting dominating sets of a rook graph.

By the support-collapse lemma (tested in tests/test_domination_lemma.py), a cell
subset S dominates iff every cell lies in a touched x-class or a touched y-class
-- i.e. iff (x-support(S), y-support(S)) is a vertex cover of the bipartite graph
whose edges are the cells. Domination therefore never depends on WHICH cells S
uses inside a class, only on which classes it touches.

That makes the sweep cheap. Going along the x-classes we carry two bits per live
y-class:

    hit  -- S has placed a cell in this y-class
    req  -- some x-class that meets this y-class was left empty, so the cover
            condition forces this y-class to be hit

Each x-class meets a contiguous y-interval, so once no later x-class can reach a
y-class it is finalised: `req` there must already imply `hit`, or the state is
dead. Finalised bits are then cleared, which merges states and is what keeps the
count small.
"""
from theseus.reduction import class_grid


def _dominating_run(n, colour):
    """Returns (number of dominating sets, peak live state count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 1, 0                     # empty set dominates the empty graph

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    full = (1 << ny) - 1
    states = {(0, 0): 1}                # (hit mask, required mask)
    peak = 1

    for i in range(nx):
        lo, hi = intervals[i]
        cols = [j for j in range(lo, hi + 1) if grid[i][j]]
        cols_mask = sum(1 << j for j in cols)

        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)
        live = full ^ ((1 << future_lo) - 1)     # y-classes still reachable
        done = full ^ live

        # Decide the y-classes of this x-class ONE AT A TIME rather than
        # enumerating all 2^|cols| subsets: the middle x-class of a large board
        # meets ~n y-classes, and 2^n options per state dominates the runtime
        # even though the state count itself stays small. The extra flag records
        # whether this x-class has placed anything, which is what decides
        # afterwards if it contributes requirements.
        partial = {(hit, req, False): count for (hit, req), count in states.items()}
        for j in cols:
            ways = (1 << grid[i][j]) - 1
            step = {}
            for (h, r, placed), count in partial.items():
                key = (h, r, placed)
                step[key] = step.get(key, 0) + count            # place nothing here
                key = (h | (1 << j), r, True)
                step[key] = step.get(key, 0) + count * ways     # place at least one
            partial = step

        nxt = {}
        for (h, r, placed), count in partial.items():
            if not placed:
                r |= cols_mask          # an empty x-class forces its y-classes
            if (r & done) & ~(h & done):    # a finalised requirement unmet
                continue
            key = (h & live, r & live)
            nxt[key] = nxt.get(key, 0) + count
        states = nxt
        peak = max(peak, len(states))

    total = 0
    for (hit, req), count in states.items():
        if req & ~hit:
            continue
        total += count
    return total, peak


def dominating_sets(n, colour):
    """Number of dominating sets of the n X n single-colour bishop graph."""
    return _dominating_run(n, colour)[0]


def dominating_state_peak(n, colour):
    return _dominating_run(n, colour)[1]


# --- total domination ------------------------------------------------------
#
# Total domination uses the OPEN neighbourhood, so a chosen cell does not cover
# itself. On a rook graph that turns the support-collapse into a statement about
# class POPULATIONS rather than mere occupancy:
#
#   cell (a,b) not in S  is covered iff cnt_x(a) >= 1 or cnt_y(b) >= 1
#   cell (a,b) in S      is covered iff cnt_x(a) >= 2 or cnt_y(b) >= 2
#
# so sweeping the x-classes, an x-class with no chosen cell forces every y-class
# it meets to reach 1, and an x-class with exactly one chosen cell, at (a,b),
# forces y-class b to reach 2. An x-class with two or more chosen cells forces
# nothing: every cell in it is already covered.
#
# Counts and requirements are held as two-bit saturating fields, one per
# y-class, packed into a pair of integers.


def _get2(v, j):
    return (v >> (2 * j)) & 3


def _inc2(v, j):
    """Increment field j, saturating at 2."""
    c = (v >> (2 * j)) & 3
    return v if c >= 2 else v + (1 << (2 * j))


def _set2(v, j, value):
    c = (v >> (2 * j)) & 3
    return v + ((value - c) << (2 * j))


# Requirements are stored as a DEFICIT (how far short of its requirement a
# y-class still is), never as the raw requirement. Once a class is saturated at
# count 2 every requirement on it is already met, so (count=2, req=0/1/2) are
# three keys that behave identically for the rest of the sweep. Recording the
# deficit merges them, cutting the per-class combinations from 9 to 6:
#   count 0 -> deficit 0,1,2   count 1 -> deficit 0,1   count 2 -> deficit 0


def _total_dominating_run(n, colour):
    """Returns (number of total dominating sets, peak live state count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 1, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    states = {(0, 0): 1}          # (packed counts, packed deficits)
    peak = 1

    for i in range(nx):
        lo, hi = intervals[i]
        cols = [j for j in range(lo, hi + 1) if grid[i][j]]

        # decide this x-class one y-class at a time, carrying how many cells it
        # has taken (saturating at 2) and, while that is exactly one, where
        partial = {(c, d, 0, -1): v for (c, d), v in states.items()}
        for j in cols:
            step = {}
            for (c, d, placed, single), count in partial.items():
                key = (c, d, placed, single)
                step[key] = step.get(key, 0) + count
                nc = _inc2(c, j)
                nd = d
                dj = _get2(d, j)
                if dj:                       # one more cell closes some deficit
                    nd = _set2(d, j, dj - 1)
                nplaced, nsingle = (1, j) if placed == 0 else (2, -1)
                key = (nc, nd, nplaced, nsingle)
                step[key] = step.get(key, 0) + count
            partial = step

        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)

        keep = 0
        for j in range(future_lo, ny):
            keep |= 3 << (2 * j)

        nxt = {}
        for (c, d, placed, single), count in partial.items():
            if placed == 0:
                for j in cols:               # every y-class here must reach 1
                    need = 1 - _get2(c, j)
                    if need > _get2(d, j):
                        d = _set2(d, j, need)
            elif placed == 1:                # its lone cell needs y-class at 2
                need = 2 - _get2(c, single)
                if need > _get2(d, single):
                    d = _set2(d, single, need)
            # a y-class no later x-class can reach must have no deficit left
            if d & ~keep:
                continue
            nxt_key = (c & keep, d & keep)
            nxt[nxt_key] = nxt.get(nxt_key, 0) + count
        states = nxt
        peak = max(peak, len(states))

    total = sum(count for (c, d), count in states.items() if d == 0)
    return total, peak


def total_dominating_sets(n, colour):
    """Number of total dominating sets of the n X n single-colour bishop graph."""
    return _total_dominating_run(n, colour)[0]


def total_dominating_state_peak(n, colour):
    return _total_dominating_run(n, colour)[1]
