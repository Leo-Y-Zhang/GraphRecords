"""Cheap independent-path check on the connected-subgraph terms.

The peeling counter is the gold-standard second algorithm, but it costs about
9^n: at n=11 it has run for over eight hours and is still going. This is the
affordable alternative.

Sweeping the y-classes instead of the x-classes computes the SAME bipartite
graph from the other side, so the answer is forced -- but the sweep order, the
per-class intervals and every pruning decision are different. It therefore
catches direction-dependent bugs in the frontier logic, which is the class of
error most likely to survive the existing tests.

Being explicit about what this is NOT: it is the same ALGORITHM, so it is a
weaker check than the peeling counter. It does not make a(11) "independently
confirmed"; it makes a disagreement much cheaper to discover.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from theseus.connected import frontier_connected        # noqa: E402
from theseus.memguard import start as memguard_start    # noqa: E402
from theseus.targets import terms_by_n                  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=11)
    ap.add_argument("--colour", default="black")
    ap.add_argument("--mem-floor", type=float, default=1.0)
    args = ap.parse_args()
    memguard_start(floor_gb=args.mem_floor, label="transposed check")

    known = terms_by_n("A290719" if args.colour == "black" else "A290769")

    t0 = time.time()
    normal = frontier_connected(args.n, args.colour)
    t1 = time.time()
    flipped = frontier_connected(args.n, args.colour, transpose=True)
    t2 = time.time()

    print(f"n={args.n} {args.colour}")
    print(f"  x-sweep : {normal}   [{t1 - t0:.1f}s]")
    print(f"  y-sweep : {flipped}   [{t2 - t1:.1f}s]")
    agree = normal == flipped
    print(f"  -> {'AGREE' if agree else '*** DISAGREE ***'}")

    pub = known.get(args.n)
    if pub is not None:
        print(f"  published a({args.n}) = {pub} -> "
              f"{'matches' if pub == normal else '*** MISMATCH ***'}")
    else:
        print(f"  a({args.n}) is beyond the published data")

    print("\nNOTE: same algorithm, different sweep direction. This is a weaker check")
    print("than the peeling counter and does NOT establish independent confirmation.")
    return 0 if agree else 1


if __name__ == "__main__":
    raise SystemExit(main())
