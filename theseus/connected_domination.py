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


# The DP state is packed into ONE integer, the same fix that let the domination
# sweep reach n=21 after the tuple-keyed version was killed holding 5.6 GB:
#
#     bits [0, LBITS*ny)              block label per y-class, 0 = untouched
#     bits [LBITS*ny, LBITS*ny+ny)    requirement mask
#     bits above that                 the block this x-class is building, 0 = none
#
# A tuple key costs ~60 bytes of object overhead and a labels TUPLE costs another
# 56 + 8*ny on top of that, so this sweep was carrying more overhead per state
# than the domination one did. Five bits per label allows 31 blocks, comfortably
# above the at-most-ny that the stranded-block prune permits.
LBITS = 5
LMASK = (1 << LBITS) - 1


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


def _pack_labels(labels):
    v = 0
    for j, x in enumerate(labels):
        v |= x << (LBITS * j)
    return v


def _unpack_labels(packed, ny):
    return [(packed >> (LBITS * j)) & LMASK for j in range(ny)]


def _cds_run(n, colour):
    """Returns (number of connected dominating sets, peak live state count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    RSH = LBITS * ny                      # where the requirement mask starts
    CSH = RSH + ny                        # where the carried block id starts
    req_mask_all = (1 << ny) - 1

    states = {0: 1}                       # packed: labels | req << RSH
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
        partial = dict(states)            # carried block id starts at 0 = none
        for j in cols:
            step = {}
            get = step.get
            for key, count in partial.items():
                step[key] = get(key, 0) + count                 # skip this y-class

                labels = _unpack_labels(key, ny)
                cur = (key >> CSH) & LMASK
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
                nk = (_pack_labels(canon)
                      | (((key >> RSH) & req_mask_all) << RSH)
                      | (ncur << CSH))
                step[nk] = get(nk, 0) + count
            partial = step

        nxt = {}
        for key, count in partial.items():
            labels = _unpack_labels(key, ny)
            req = (key >> RSH) & req_mask_all
            cur = (key >> CSH) & LMASK
            r = req if cur else req | cols_mask

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

            nxt_key = _pack_labels(labels) | ((r & ~done_mask) << RSH)
            nxt[nxt_key] = nxt.get(nxt_key, 0) + count
        states = nxt
        peak = max(peak, len(states))

    total = 0
    for key, count in states.items():
        if (key >> RSH) & req_mask_all:
            continue
        labels = _unpack_labels(key, ny)
        if len({v for v in labels if v}) == 1:
            total += count
    return total, peak


def connected_dominating_sets(n, colour):
    """Non-empty cell subsets that dominate and induce a connected subgraph."""
    return _cds_run(n, colour)[0]


def connected_dominating_state_peak(n, colour):
    return _cds_run(n, colour)[1]
