"""Measure the honeycomb counters and confirm terms beyond the published data.

Prints, per n: peak live state count, wall time, peak resident set, and the value
-- tagged against the published snapshot so a disagreement is impossible to miss.

Peak RSS is reported because it, not time, is what ends these runs. The square
board's n=11 connected-dominating sweep died holding 4.6 GB; a run that is about
to do the same should say so while it still can.

    python bench/measure_honeycomb.py cis 10 --budget 1800

The predicates:

    cis       connected induced subgraphs   (A290783)
    cds       connected dominating sets     (A381795)
    dom       dominating sets               (A290941 -- an ANCHOR, not a target:
                                             already published to n=50)
    cis-peel  connected induced subgraphs, by exact-support peeling
    cds-peel  connected dominating sets, by exact-support peeling

The two `-peel` predicates are the independent second algorithm required by
PAPER.md section 4 before any term is believed. They share no code path with the
sweeps beyond the class grid, and they report no state count because they do not
sweep.
"""
import argparse
import ctypes
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.cds_peeling import peeling_connected_dominating
from graphrecords.connected import _frontier_run, peeling_connected
from graphrecords.connected_domination import _cds_run
from graphrecords.domination import _dominating_run
from graphrecords.memguard import start as memguard_start
from graphrecords.targets import terms_by_n

PREDICATES = {
    "cis": ("A290783", lambda n: _frontier_run(n, "honeycomb")),
    "cds": ("A381795", lambda n: _cds_run(n, "honeycomb")),
    "dom": ("A290941", lambda n: _dominating_run(n, "honeycomb")),
    "cis-peel": ("A290783", lambda n: (peeling_connected(n, "honeycomb"), None)),
    "cds-peel": ("A381795",
                 lambda n: (peeling_connected_dominating(n, "honeycomb"), None)),
}


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


def peak_rss_mb():
    """Peak resident set of this process in MB, or None where it cannot be read.

    Peak rather than current: the interpreter does not return freed blocks to
    the OS promptly, so the current figure understates what the run actually
    demanded of the machine, which is the number that decides whether the next n
    is safe to attempt.
    """
    try:
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
        # GetCurrentProcess returns a HANDLE. ctypes defaults a restype to
        # c_int, which truncates it on 64-bit Windows and makes the call below
        # fail silently -- reporting "?" for every row rather than an error.
        get_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype = ctypes.c_void_p
        if not ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.c_void_p(get_process()), ctypes.byref(counters), counters.cb
        ):
            return None
        return counters.PeakWorkingSetSize / (1024 ** 2)
    except Exception:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predicate", choices=sorted(PREDICATES))
    parser.add_argument("limit", type=int, help="largest n to attempt")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--budget", type=float, default=1800.0,
                        help="stop once a single n exceeds this many seconds")
    parser.add_argument("--floor-gb", type=float, default=1.5,
                        help="memguard floor: abort if free RAM falls below this")
    args = parser.parse_args(argv)

    aid, run = PREDICATES[args.predicate]
    published = terms_by_n(aid)
    memguard_start(floor_gb=args.floor_gb, label=f"{args.predicate} sweep")

    print(f"{args.predicate} -- {aid}, published to n={max(published)}")
    print(f"{'n':>3} {'peak states':>12} {'secs':>9} {'peak MB':>8}  value")
    sys.stdout.flush()

    for n in range(args.start, args.limit + 1):
        t0 = time.time()
        value, peak = run(n)
        dt = time.time() - t0
        known = published.get(n)
        if known is None:
            tag = "NEW"
        elif known == value:
            tag = "matches published"
        else:
            tag = f"*** MISMATCH published={known} ***"
        rss = peak_rss_mb()
        print(f"{n:>3} {'-' if peak is None else format(peak, ','):>12} {dt:>9.2f} "
              f"{'?' if rss is None else format(rss, '.0f'):>8}  {value}  [{tag}]")
        sys.stdout.flush()
        if known is not None and known != value:
            print("stopping: a published term did not reproduce")
            return 1
        if dt > args.budget:
            print(f"stopping: n={n} took {dt:.0f}s, over budget {args.budget:.0f}s")
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
