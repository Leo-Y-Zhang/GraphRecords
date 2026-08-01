"""Independent cross-check of the connected-dominating-set terms.

A289145 and A289169 are staged to n=10, two terms past what brute force can
reach, and until now both rested on `connected_domination.py` alone -- one
algorithm, never contradicted but never independently confirmed either.

`cds_peeling.py` counts the same sets by exact-support inclusion-exclusion, with
domination applied as a predicate on the support. It shares no code path with the
frontier DP beyond the class grid, and nothing whatever with that DP's
requirement-mask bookkeeping, so agreement is genuine independence rather than
reproducibility.

Peeling costs about 9^n: seconds at n=9, minutes at n=10. Unlike the
connected-subgraph cross-check at n=11 this is cheap, because the staged terms
for this family stop at n=10.

    python tools/crosscheck_cds.py --from-n 9 --to-n 10 --colour black
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.cds_peeling import peeling_connected_dominating
from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.memguard import start as memguard_start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-n", type=int, default=9)
    ap.add_argument("--to-n", type=int, default=10)
    ap.add_argument("--colour", default="black", choices=["black", "white"])
    ap.add_argument("--mem-floor", type=float, default=1.0,
                    help="abort if free RAM falls below this many GB")
    args = ap.parse_args()

    memguard_start(args.mem_floor)

    ok = True
    for n in range(args.from_n, args.to_n + 1):
        t0 = time.time()
        fast = connected_dominating_sets(n, args.colour)
        t1 = time.time()
        slow = peeling_connected_dominating(n, args.colour)
        t2 = time.time()
        agree = fast == slow
        ok &= agree
        print(f"n={n} {args.colour}")
        print(f"  frontier DP : {fast}   [{t1 - t0:.1f}s]")
        print(f"  peeling     : {slow}   [{t2 - t1:.1f}s]")
        print(f"  -> {'AGREE - independently confirmed' if agree else '*** DISAGREE ***'}")
        sys.stdout.flush()

    print("\nCROSSCHECK", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
