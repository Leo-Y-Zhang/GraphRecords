"""Counting connected dominating sets of a rook graph.

This composes the two collapses already established:

* connectivity, via the frontier partition DP over y-classes, and
* domination, via the support-collapse lemma.

The composition is cheaper than it looks. In the connectivity sweep a y-class
carries a non-zero block label exactly when it holds a chosen cell -- which is
precisely the condition domination cares about. So domination contributes only a
requirement bit per y-class, not a whole extra dimension: an x-class left empty
forces every y-class it meets to be occupied.

Since phi is injective the class grid is 0/1, so "place at least one cell in this
(x-class, y-class)" is a single choice and every transition weight is 1.
"""
from theseus.reduction import class_grid


def _canonical_with(labels, cur):
    """Restricted-growth relabelling that also translates a carried block id.

    `cur` is the block the current x-class is building; it must survive the
    relabelling or states that are genuinely equal would fail to merge.
    """
    remap = {0: 0}
    out = []
    nxt = 1
    for v in labels:
        w = remap.get(v)
        if w is None:
            w = remap[v] = nxt
            nxt += 1
        out.append(w)
    return tuple(out), (remap[cur] if cur is not None else None)


def _cds_run(n, colour):
    """Returns (number of connected dominating sets, peak live state count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    states = {((0,) * ny, 0): 1}          # (block labels, requirement mask)
    peak = 1

    for i in range(nx):
        lo, hi = intervals[i]
        cols = [j for j in range(lo, hi + 1) if grid[i][j]]
        cols_mask = sum(1 << j for j in cols)

        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)
        done_mask = (1 << future_lo) - 1

        # Decide this x-class one y-class at a time rather than enumerating all
        # 2^|cols| subsets: the middle x-class of a large board meets ~n
        # y-classes, and that enumeration dominates the runtime even though the
        # state count stays modest. `cur` is the block this x-class is building,
        # or None while it has placed nothing.
        partial = {(labels, req, None): c for (labels, req), c in states.items()}
        for j in cols:
            step = {}
            for (labels, req, cur), count in partial.items():
                key = (labels, req, cur)
                step[key] = step.get(key, 0) + count           # skip this y-class

                new = list(labels)
                if cur is None:
                    if new[j]:
                        ncur = new[j]
                    else:
                        ncur = max(new) + 1
                        new[j] = ncur
                else:
                    ncur = cur
                    if new[j] and new[j] != cur:
                        old = new[j]
                        for idx, v in enumerate(new):
                            if v == old:
                                new[idx] = cur
                    else:
                        new[j] = cur
                canon, ncur = _canonical_with(new, ncur)
                key = (canon, req, ncur)
                step[key] = step.get(key, 0) + count
            partial = step

        nxt = {}
        for (labels, req, cur), count in partial.items():
            r = req if cur is not None else req | cols_mask

            # a finalised y-class that was required must actually be occupied
            bad = False
            for j in range(future_lo):
                if (r >> j & 1) and labels[j] == 0:
                    bad = True
                    break
            if bad:
                continue

            # a block confined to the finalised region can never merge again
            closed = {labels[j] for j in range(future_lo) if labels[j]}
            active = {labels[j] for j in range(future_lo, ny) if labels[j]}
            stranded = closed - active
            if len(stranded) > 1 or (stranded and active):
                continue

            nxt_key = (labels, r & ~done_mask)
            nxt[nxt_key] = nxt.get(nxt_key, 0) + count
        states = nxt
        peak = max(peak, len(states))

    total = 0
    for (labels, req), count in states.items():
        if req:
            continue
        if len({v for v in labels if v}) == 1:
            total += count
    return total, peak


def connected_dominating_sets(n, colour):
    """Non-empty cell subsets that dominate and induce a connected subgraph."""
    return _cds_run(n, colour)[0]


def connected_dominating_state_peak(n, colour):
    return _cds_run(n, colour)[1]
