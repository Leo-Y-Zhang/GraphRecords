"""Extend the bishop connected-dominating-set sequences and stage them.

No derived third sequence here, unlike the other two drivers: a connected set
lies inside one component, so it can never dominate the other one, and there is
no full-bishop version of this count to derive.

Every published term is recomputed first, indexed by the sequence's true offset.
Any disagreement aborts without staging.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.memguard import start as memguard_start
from graphrecords.targets import offset_start, terms_by_n

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"

SEQUENCES = {"A289145": "black", "A289169": "white"}


def run(aid, colour, limit, budget):
    known = terms_by_n(aid)
    print(f"\n=== {aid} ({colour} bishop, offset {offset_start(aid)}, "
          f"{len(known)} published terms) ===")
    sys.stdout.flush()

    for n, term in sorted(known.items()):
        got = connected_dominating_sets(n, colour)
        if got != term:
            print(f"{aid}: a({n}) recomputed as {got}, published {term} - ABORT")
            return None
    print(f"{aid}: reproduced all {len(known)} published terms")
    sys.stdout.flush()

    values = dict(known)
    n = max(known) + 1
    while n <= limit:
        t0 = time.time()
        values[n] = connected_dominating_sets(n, colour)
        dt = time.time() - t0
        print(f"{aid}: a({n}) = {values[n]}   [{dt:.1f}s]  NEW")
        sys.stdout.flush()
        if dt > budget:
            print(f"{aid}: stopping, a({n}) took {dt:.0f}s (budget {budget:.0f}s)")
            break
        n += 1

    STAGE.mkdir(exist_ok=True)
    path = STAGE / f"b{aid[1:]}.txt"
    path.write_bytes(
        "".join(f"{i} {values[i]}\n" for i in sorted(values)).encode("ascii")
    )
    new = len(values) - len(known)
    print(f"{aid}: staged {len(values)} terms ({new} new) to {path.name}")
    return (aid, len(known), len(values), new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=14)
    ap.add_argument("--budget", type=float, default=900.0)
    ap.add_argument("--mem-floor", type=float, default=1.0,
                    help="abort if free RAM falls below this many GB")
    args = ap.parse_args()
    memguard_start(floor_gb=args.mem_floor, label="connected dominating extension")

    results = []
    for aid, colour in SEQUENCES.items():
        r = run(aid, colour, args.limit, args.budget)
        if r is None:
            print("ABORTING")
            return 1
        results.append(r)

    print("\n" + "=" * 52)
    print(f"{'sequence':10s} {'published':>10s} {'now':>6s} {'new':>5s}")
    for aid, pub, total, new in results:
        print(f"{aid:10s} {pub:>10d} {total:>6d} {new:>5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
