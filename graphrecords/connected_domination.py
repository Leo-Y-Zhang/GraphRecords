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
from graphrecords.reduction import class_grid

# The DP state is a single `bytes` key:
#
#     key[0:ny]        one block label per y-class, 0 = untouched
#     key[ny:ny+4]     requirement mask, little-endian
#     key[ny+4]        the block this x-class is building, 0 = none (transient)
#
# Three representations were measured on a 12-y-class state before choosing:
#
#     tuple(labels) + int   ~556 bytes    unpack n/a
#     packed integer        ~ 36 bytes    unpack 0.493 us
#     bytes                 ~ 49 bytes    unpack 0.079 us
#
# The integer is marginally smaller, but this sweep rebuilds a labels LIST on
# every transition, so it paid for that with hand-rolled shift loops and ran 2x
# slower than the tuple version it replaced. `bytes` keeps ~11x of the tuple's
# memory saving while `list(key)` and `bytes(labels)` do the conversion at C
# speed, which is 6x faster than the shifts. Memory was the wall here (n=11 died
# holding 4.6 GB) but paying 2x in time to fix it was a bad trade.
REQ_WIDTH = 4


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
    return out, remap[cur] if cur else 0


def _cds_run(n, colour):
    """Returns (number of connected dominating sets, peak live state count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    zero_req = (0).to_bytes(REQ_WIDTH, "little")
    states = {bytes(ny) + zero_req: 1}
    peak = 1

    for i in range(nx):
        lo, hi = intervals[i]
        cols = [j for j in range(lo, hi + 1) if grid[i][j]]
        cols_mask = sum(1 << j for j in cols)

        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)
        keep_mask = ~((1 << future_lo) - 1)

        # Decide this x-class one y-class at a time rather than enumerating all
        # 2^|cols| subsets: the middle x-class of a large board meets ~n
        # y-classes, and that enumeration dominates the runtime even though the
        # state count stays modest.
        partial = {k + b"\x00": v for k, v in states.items()}
        for j in cols:
            step = {}
            get = step.get
            for key, count in partial.items():
                step[key] = get(key, 0) + count                 # skip this y-class

                labels = list(key[:ny])
                cur = key[ny + REQ_WIDTH]
                if cur == 0:
                    if labels[j]:
                        ncur = labels[j]
                    else:
                        ncur = max(labels) + 1
                        labels[j] = ncur
                else:
                    ncur = cur
                    if labels[j] and labels[j] != cur:
                        old = labels[j]
                        for idx, v in enumerate(labels):
                            if v == old:
                                labels[idx] = cur
                    else:
                        labels[j] = cur
                canon, ncur = _canonical_with(labels, ncur)
                nk = bytes(canon) + key[ny:ny + REQ_WIDTH] + bytes((ncur,))
                step[nk] = get(nk, 0) + count
            partial = step

        nxt = {}
        get = nxt.get
        for key, count in partial.items():
            labels = list(key[:ny])
            req = int.from_bytes(key[ny:ny + REQ_WIDTH], "little")
            r = req if key[ny + REQ_WIDTH] else req | cols_mask

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

            nk = key[:ny] + (r & keep_mask).to_bytes(REQ_WIDTH, "little")
            nxt[nk] = get(nk, 0) + count
        states = nxt
        peak = max(peak, len(states))

    total = 0
    for key, count in states.items():
        if int.from_bytes(key[ny:ny + REQ_WIDTH], "little"):
            continue
        if len({v for v in key[:ny] if v}) == 1:
            total += count
    return total, peak


def connected_dominating_sets(n, colour):
    """Non-empty cell subsets that dominate and induce a connected subgraph."""
    return _cds_run(n, colour)[0]


def connected_dominating_state_peak(n, colour):
    return _cds_run(n, colour)[1]
