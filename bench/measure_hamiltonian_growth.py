"""Measure plug-DP state growth for Hamiltonian paths on the bishop boards.

This exists to answer ONE question with data rather than argument, exactly as
`graphrecords/torus_profile.py` did for the torus family: can a plug DP with
matching states over the rook structure -- the approach section 5.3 of the design
spec names for Hamiltonian paths, and which was never implemented -- get past the
published terms of A307934/A234632 (black) and A308146/A234637 (white), which
stop at n=9?

The measurement is the STATE COUNT, not the answer. The answer is carried anyway
and tagged against the published snapshot, because a state-space measurement of a
DP that computes the wrong thing measures nothing; a wrong transition would
almost certainly show up as a wrong term.

## The DP

The single-colour bishop graph is a rook graph on the class grid (see
`graphrecords/reduction.py`): cells are adjacent iff they share an x-class or a
y-class. Both classes are therefore CLIQUES, which is what makes a plug DP
possible at all -- a column edge may join any two rows, not just adjacent ones,
so nothing is local in the grid-graph sense, but everything within a class is
interchangeable.

Sweep the cells row by row, left to right. Every cell has exactly two slots (a
Hamiltonian path gives it degree 2, or degree 1 if it is one of the two path
endpoints), and when its cell is swept each slot is committed to one of:

    MC  matched to an open end waiting in this cell's column   (edge to an earlier row)
    MR  matched to an open end waiting in this row             (edge to an earlier cell of the row)
    SC  left open in this cell's column                        (edge to a later row)
    SR  left open in this row                                  (edge to a later cell of the row)
    T   unused: this cell is a path endpoint

Each edge is committed exactly once, at whichever of its two ends is swept later,
so no path is counted twice.

The state is the set of path fragments built so far, each recorded only as its
two ends. An end is TERMINAL, ROWSTUB (open within the current row), or the
column it waits in. Nothing else survives the collapse: ends in a class are
mutually reachable, so which row an open end came from cannot matter.

One bit more is needed. A fragment of a single cell has both ends on the SAME
cell, so two later cells matching those two ends produce one edge set, not two,
while a longer fragment with both ends in one column has two DISTINCT extremity
cells and does produce two. So a fragment carries a singleton flag, which is only
meaningful (and only recorded) when its two ends coincide.

Pruning, all of it necessary-condition only:

    - at most 2 TERMINAL ends ever exist, since a path has 2 endpoints
    - a fragment with both ends TERMINAL is finished and can never merge, so it
      is legal only as the whole answer at the very last step
    - open ends in a column need future cells of that column to absorb them, and
      each such cell absorbs at most 2
    - row stubs need later cells of the same row, likewise at most 2 each
    - each remaining cell reduces the fragment count by at most 1, so the number
      of fragments cannot exceed the remaining cells plus 1

Run: `python bench/measure_hamiltonian_growth.py --from-n 4 --to-n 12`.
"""
import argparse
import ctypes
import sys
import time
from itertools import combinations, combinations_with_replacement

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from graphrecords.reduction import class_grid
from graphrecords.targets import terms_by_n

TERMINAL = -1
ROWSTUB = -2

PUBLISHED = {"black": terms_by_n("A307934"), "white": terms_by_n("A308146")}


class CapHit(Exception):
    """Raised when a run breaches the memory or time cap. That is a data point."""

    def __init__(self, kind, step, states, seconds, gb):
        super().__init__(f"{kind} cap hit at step {step}")
        self.kind = kind
        self.step = step
        self.states = states
        self.seconds = seconds
        self.gb = gb


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _memory_reader():
    """Bind GetProcessMemoryInfo once, or return None if it cannot be bound.

    The argtypes matter: left to guess, ctypes truncates the process handle and
    the call fails, which silently turns the memory cap off. It is bound once
    here so a per-step read is a plain call.
    """
    try:
        query = ctypes.windll.psapi.GetProcessMemoryInfo
        query.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_ProcessMemoryCounters),
            ctypes.c_ulong,
        ]
        query.restype = ctypes.c_int
        current = ctypes.windll.kernel32.GetCurrentProcess
        current.restype = ctypes.c_void_p
        handle = current()
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
        if not query(handle, ctypes.byref(counters), counters.cb):
            return None
    except (AttributeError, OSError):
        return None

    def read():
        if not query(handle, ctypes.byref(counters), counters.cb):
            return None
        return counters.WorkingSetSize / (1024 ** 3)

    return read


_READ_WORKING_SET = _memory_reader()


def working_set_gb():
    """This process's working set in GB, or None where it cannot be read.

    Working set is what the machine actually feels, which is the quantity the
    repo's 4.4-5.6 GB walls were measured in. An unreadable counter disables the
    memory cap rather than aborting the run, and the caller says so out loud.
    """
    return None if _READ_WORKING_SET is None else _READ_WORKING_SET()


def board(n, colour):
    """The class grid, oriented so the swept axis is the longer one.

    The frontier is the y-classes, so sweeping the longer axis keeps the frontier
    as narrow as the board allows. At even n this also turns the white grid into
    the black one, which is the reflection isomorphism the repo already relies on
    and so a free check that the orientation logic is not scrambling the board.
    """
    grid, nx, ny = class_grid(n, colour)
    if ny > nx:
        grid = [[grid[i][j] for i in range(nx)] for j in range(ny)]
        nx, ny = ny, nx
    return grid, nx, ny


def _frag(a, b, singleton):
    """A fragment as an ordered end pair; the singleton bit only when ends tie."""
    if a > b:
        a, b = b, a
    return (a, b, 1 if (singleton and a == b) else 0)


def _offers(state, end):
    """(index, distinct cells offering this end, the fragment's other end)."""
    out = []
    for idx, (a, b, singleton) in enumerate(state):
        if a == end and b == end:
            # a one-cell fragment offers ONE cell twice; a longer one offers two
            out.append((idx, 1 if singleton else 2, end))
        elif a == end:
            out.append((idx, 1, b))
        elif b == end:
            out.append((idx, 1, a))
    return out


def _replace(state, drop, frag):
    out = [f for k, f in enumerate(state) if k not in drop]
    out.append(frag)
    out.sort()
    return tuple(out)


def _cell_options(state, col):
    """Every legal commitment of one cell's two slots: (dropped, merged, ways).

    Slots are unordered: the cell is a set of two half-edges, not a sequence, so
    each option is generated once. Matching two ends of the SAME fragment closes
    a cycle and is never generated. The caller prunes before it pays to build the
    successor state, so this yields the pieces rather than the state.
    """
    creations = (ROWSTUB, TERMINAL, col)
    for c1, c2 in combinations_with_replacement(creations, 2):
        if c1 == TERMINAL and c2 == TERMINAL:
            continue  # degree 0: an isolated cell, which no path of >1 cell has
        yield (), _frag(c1, c2, True), 1

    row_offers = _offers(state, ROWSTUB)
    col_offers = _offers(state, col)

    for offers in (row_offers, col_offers):
        for idx, mult, other in offers:
            for created in creations:
                yield (idx,), _frag(other, created, False), mult

    for offers in (row_offers, col_offers):
        for (i1, m1, o1), (i2, m2, o2) in combinations(offers, 2):
            yield (i1, i2), _frag(o1, o2, False), m1 * m2

    for i1, m1, o1 in row_offers:
        for i2, m2, o2 in col_offers:
            if i1 != i2:  # same fragment on both slots would close a cycle
                yield (i1, i2), _frag(o1, o2, False), m1 * m2


def hamiltonian_profile(n, colour, cap_gb=2.5, budget_s=600.0, check_every=5_000):
    """Sweep the board and record the live state count after every cell.

    Returns (profile, answer, seconds, peak_gb) where profile is the list of live
    state counts, one per cell. Raises CapHit if the memory or time cap is
    breached, which is itself a measurement and is recorded by the caller.
    """
    grid, nx, ny = board(n, colour)
    cells = [(i, j) for i in range(nx) for j in range(ny) if grid[i][j]]
    ncells = len(cells)
    if ncells < 2:
        return [], 0, 0.0, 0.0  # OEIS counts no Hamiltonian path on a lone cell

    # after cell k: cells left overall, left in that cell's row, left per column
    rem_cells = [ncells - k - 1 for k in range(ncells)]
    rem_row = [0] * ncells
    for k in range(ncells - 2, -1, -1):
        if cells[k + 1][0] == cells[k][0]:
            rem_row[k] = rem_row[k + 1] + 1
    rem_col = [None] * ncells
    running = [0] * ny
    for k in range(ncells - 1, -1, -1):
        rem_col[k] = tuple(running)
        running[cells[k][1]] += 1

    states = {(): 1}
    profile = []
    peak_gb = 0.0
    started = time.time()
    since_check = 0

    for k, (_i, j) in enumerate(cells):
        left, row_left, col_left = rem_cells[k], rem_row[k], rem_col[k]
        nxt = {}
        for state, count in states.items():
            # the parent's end census, taken once; each option's is a delta of it
            terminals = 0
            rowstubs = 0
            cols = {}
            for a, b, _singleton in state:
                for end in (a, b):
                    if end == TERMINAL:
                        terminals += 1
                    elif end == ROWSTUB:
                        rowstubs += 1
                    else:
                        cols[end] = cols.get(end, 0) + 1

            for drop, frag, mult in _cell_options(state, j):
                a, b, _singleton = frag
                if len(state) + 1 - len(drop) > left + 1:
                    continue  # each later cell merges away at most one fragment
                if a == TERMINAL and b == TERMINAL and (left or len(state) != len(drop)):
                    continue  # a finished path that can never absorb what is left
                gone_t = gone_r = 0
                gone_cols = []
                for idx in drop:
                    for end in state[idx][:2]:
                        if end == TERMINAL:
                            gone_t += 1
                        elif end == ROWSTUB:
                            gone_r += 1
                        else:
                            gone_cols.append(end)
                if terminals - gone_t + (a == TERMINAL) + (b == TERMINAL) > 2:
                    continue  # a path has exactly two endpoints
                stubs = rowstubs - gone_r + (a == ROWSTUB) + (b == ROWSTUB)
                if stubs > 2 * row_left:
                    continue  # nothing later in this row could absorb them
                # only columns this option touches can newly breach; the rest were
                # checked against a capacity that has not shrunk since
                blocked = False
                for c in (a, b, j):
                    if c < 0:
                        continue
                    open_ends = (cols.get(c, 0) + (a == c) + (b == c)
                                 - gone_cols.count(c))
                    if open_ends > 2 * col_left[c]:
                        blocked = True
                        break
                if blocked:
                    continue
                new_state = _replace(state, drop, frag)
                nxt[new_state] = nxt.get(new_state, 0) + count * mult
            since_check += 1
            if since_check >= check_every:
                since_check = 0
                elapsed = time.time() - started
                gb = working_set_gb()
                peak_gb = max(peak_gb, gb or 0.0)
                if gb is not None and gb > cap_gb:
                    raise CapHit("memory", k, len(nxt), elapsed, gb)
                if elapsed > budget_s:
                    raise CapHit("time", k, len(nxt), elapsed, gb or 0.0)
        states = nxt
        profile.append(len(states))
        gb = working_set_gb()
        peak_gb = max(peak_gb, gb or 0.0)
        elapsed = time.time() - started
        if gb is not None and gb > cap_gb:
            raise CapHit("memory", k, len(states), elapsed, gb)
        if elapsed > budget_s:
            raise CapHit("time", k, len(states), elapsed, gb or 0.0)

    answer = states.get(((TERMINAL, TERMINAL, 0),), 0)
    return profile, answer, time.time() - started, peak_gb


def main(from_n, to_n, cap_gb, budget_s, colours):
    if working_set_gb() is None:
        print("WARNING: process memory is unreadable here, so the memory cap is OFF")
    print(f"caps: {cap_gb:.2f} GB working set, {budget_s:.0f} s per n\n")
    print(f"{'n':>3} {'colour':>6} {'cells':>6} {'peak states':>13} {'secs':>8} "
          f"{'peak GB':>8}  value")
    for n in range(from_n, to_n + 1):
        for colour in colours:
            try:
                profile, answer, secs, peak_gb = hamiltonian_profile(
                    n, colour, cap_gb=cap_gb, budget_s=budget_s
                )
            except CapHit as hit:
                print(f"{n:>3} {colour:>6} {'':>6} {hit.states:>13,} {hit.seconds:>8.1f} "
                      f"{hit.gb:>8.2f}  *** {hit.kind.upper()} CAP HIT at cell "
                      f"{hit.step}, stopping this n ***")
                sys.stdout.flush()
                continue
            known = PUBLISHED[colour].get(n)
            if known is None:
                tag = "NEW"
            elif known == answer:
                tag = "matches published"
            else:
                tag = f"*** MISMATCH published={known} ***"
            peak = max(profile) if profile else 0
            print(f"{n:>3} {colour:>6} {len(profile):>6} {peak:>13,} "
                  f"{secs:>8.2f} {peak_gb:>8.2f}  {answer}  [{tag}]")
            print(f"        profile: {','.join(str(v) for v in profile)}")
            sys.stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-n", type=int, default=4)
    parser.add_argument("--to-n", type=int, default=12)
    parser.add_argument("--cap-gb", type=float, default=2.5)
    parser.add_argument("--budget", type=float, default=600.0)
    parser.add_argument("--colour", choices=("black", "white", "both"), default="both")
    args = parser.parse_args()
    main(
        args.from_n,
        args.to_n,
        args.cap_gb,
        args.budget,
        ("black", "white") if args.colour == "both" else (args.colour,),
    )
