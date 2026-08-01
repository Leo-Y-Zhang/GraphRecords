"""Phase 2 measured prototype: a profile DP on the n X n torus grid graph.

This exists to answer ONE question with data rather than argument: can a
broken-profile sweep on a torus beat the published terms of that family?

It counts plain dominating sets, which is the CHEAPEST predicate there is --
Phase 1 established that occupancy-only predicates collapse and population or
privacy predicates do not. If the cheapest one cannot reach the published
ceiling, the richer ones (total, minimal, connected, irredundant -- which is all
the torus family actually offers) certainly cannot, and Phase 2 should be closed
for this family rather than attempted.

The vertical wrap is what makes a torus expensive. Row 0's domination depends on
row n-1 and vice versa, so the sweep carries:

    mask   which cells of the current row are chosen
    undom  which cells of the current row are not yet dominated
    u0     which cells of ROW 0 still await domination from row n-1

and is run once per choice of row 0's mask. That is a 2^n outer loop over a
state space of roughly 3^n * 2^n, which is the cost this file is here to measure.
"""

def _row_neighbourhood(mask, n):
    """Cells dominated within a row by `mask`, including horizontal wrap."""
    left = ((mask << 1) | (mask >> (n - 1))) & ((1 << n) - 1)
    right = ((mask >> 1) | (mask << (n - 1))) & ((1 << n) - 1)
    return mask | left | right


def dominating_sets_torus(n, collect_states=False):
    """Number of dominating sets of C_n square C_n, and the peak state count.

    Returns (count, peak_states). Exact; validated against the brute force in
    `graphrecords.torus` for the n where both are feasible.
    """
    if n < 3:
        raise ValueError("the torus grid graph is simple only for n >= 3")
    full = (1 << n) - 1
    rows = list(range(1 << n))
    cover = {m: _row_neighbourhood(m, n) for m in rows}

    total = 0
    peak = 0

    for r0 in rows:
        # row 0 placed. Within-row domination only; rows 1 and n-1 may still help.
        states = {}
        u_after_r0 = full & ~cover[r0]
        # place row 1, which fixes u0 (what row 0 still needs from row n-1)
        for r1 in rows:
            u0 = u_after_r0 & ~r1                 # row 0's residue for row n-1
            undom1 = (full & ~cover[r1]) & ~r0    # row 1 not yet dominated
            key = (r1, undom1, u0)
            states[key] = states.get(key, 0) + 1
        peak = max(peak, len(states))

        # rows 2 .. n-1
        for _ in range(2, n):
            nxt = {}
            for (prev, undom, u0), count in states.items():
                for m in rows:
                    if undom & ~m:                # prev row's residue must be covered
                        continue
                    new_undom = (full & ~cover[m]) & ~prev
                    key = (m, new_undom, u0)
                    nxt[key] = nxt.get(key, 0) + count
            states = nxt
            peak = max(peak, len(states))

        # close the vertical wrap: row n-1 against row 0
        for (last, undom, u0), count in states.items():
            if undom & ~r0:                       # last row's residue needs row 0
                continue
            if u0 & ~last:                        # row 0's residue needs row n-1
                continue
            total += count

    return total, peak


def measure(n_from=3, n_to=7):
    """Yield (n, count, peak_states, seconds) so the ceiling is measured."""
    import time
    for n in range(n_from, n_to + 1):
        t0 = time.time()
        count, peak = dominating_sets_torus(n)
        yield n, count, peak, time.time() - t0
