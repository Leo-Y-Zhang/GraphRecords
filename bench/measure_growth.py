"""Measure frontier DP cost and confirm terms beyond the published data.

Prints, per n and colour: the peak live state count, the wall time, and the value
-- tagged against the published snapshot so a disagreement is impossible to miss.
"""
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from graphrecords.connected import _frontier_run          # noqa: E402
from graphrecords.targets import terms_by_n               # noqa: E402

PUBLISHED = {"black": terms_by_n("A290719"), "white": terms_by_n("A290769")}


def main(limit, budget):
    print(f"{'n':>3} {'colour':>6} {'peak states':>12} {'secs':>9}  value")
    for n in range(1, limit + 1):
        for colour in ("black", "white"):
            t0 = time.time()
            value, peak = _frontier_run(n, colour)
            dt = time.time() - t0
            known = PUBLISHED[colour].get(n)
            if known is None:
                tag = "NEW"
            elif known == value:
                tag = "matches published"
            else:
                tag = f"*** MISMATCH published={known} ***"
            print(f"{n:>3} {colour:>6} {peak:>12,} {dt:>9.2f}  {value}  [{tag}]")
            sys.stdout.flush()
            if dt > budget:
                print(f"stopping: {colour} n={n} took {dt:.0f}s, over budget {budget:.0f}s")
                return


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 16,
         float(sys.argv[2]) if len(sys.argv) > 2 else 900.0)
