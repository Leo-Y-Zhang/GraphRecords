"""Independent cross-check of the connected-subgraph terms.

The frontier partition DP and the exact-support peeling counter share no code
path beyond the class grid, so agreement between them is genuine independence,
not mere reproducibility. a(10) already has it; a(11) does not, and this closes
that gap.

Peeling costs about 9^n, so n=11 takes on the order of an hour. Run it alone.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.connected import frontier_connected, peeling_connected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-n", type=int, default=10)
    ap.add_argument("--to-n", type=int, default=11)
    ap.add_argument("--colour", default="black")
    args = ap.parse_args()

    ok = True
    for n in range(args.from_n, args.to_n + 1):
        t0 = time.time()
        fast = frontier_connected(n, args.colour)
        t1 = time.time()
        slow = peeling_connected(n, args.colour)
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
