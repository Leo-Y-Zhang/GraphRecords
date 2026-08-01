"""Extend the bishop dominating-set sequences and stage them.

Three sequences from two computations again, but the composition rule differs
from the connected case: a set dominates a disjoint union iff it dominates each
part, so counts MULTIPLY across the two colour components rather than adding.

Every published term is recomputed first, indexed by each sequence's true offset.
Any disagreement aborts without staging.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.domination import dominating_sets                 # noqa: E402
from graphrecords.memguard import start as memguard_start        # noqa: E402
from graphrecords.targets import offset_start, terms_by_n           # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"

COLOUR_SEQUENCES = {"A289164": "black", "A289170": "white"}
DERIVED = "A295898"          # full bishop graph = black * white


def compute(aid, colour, limit, budget):
    known = terms_by_n(aid)
    print(f"\n=== {aid} ({colour} bishop, offset {offset_start(aid)}, "
          f"{len(known)} published terms) ===")
    sys.stdout.flush()

    for n, term in sorted(known.items()):
        got = dominating_sets(n, colour)
        if got != term:
            print(f"{aid}: a({n}) recomputed as {got}, published {term} - ABORT")
            return None
    print(f"{aid}: reproduced all {len(known)} published terms")
    sys.stdout.flush()

    values = dict(known)
    n = max(known) + 1
    while n <= limit:
        t0 = time.time()
        values[n] = dominating_sets(n, colour)
        dt = time.time() - t0
        print(f"{aid}: a({n}) = {values[n]}   [{dt:.1f}s]  NEW")
        sys.stdout.flush()
        if dt > budget:
            print(f"{aid}: stopping, a({n}) took {dt:.0f}s (budget {budget:.0f}s)")
            break
        n += 1
    return values


def stage(aid, values):
    STAGE.mkdir(exist_ok=True)
    path = STAGE / f"b{aid[1:]}.txt"
    body = "".join(f"{i} {values[i]}\n" for i in sorted(values))
    path.write_bytes(body.encode("ascii"))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=22)
    ap.add_argument("--budget", type=float, default=900.0)
    ap.add_argument("--mem-floor", type=float, default=1.0,
                    help="abort if free RAM falls below this many GB")
    args = ap.parse_args()
    memguard_start(floor_gb=args.mem_floor, label="domination extension")

    computed = {}
    for aid, colour in COLOUR_SEQUENCES.items():
        vals = compute(aid, colour, args.limit, args.budget)
        if vals is None:
            print("ABORTING: nothing staged")
            return 1
        computed[aid] = vals

    black, white = computed["A289164"], computed["A289170"]

    print(f"\n=== {DERIVED} (full bishop graph, derived as black * white) ===")
    known = terms_by_n(DERIVED)
    derived = {}
    for n in sorted(set(black) & set(white)):
        derived[n] = black[n] * white[n]
    if 1 in black and 1 not in derived:
        derived[1] = black[1]          # n=1 has no white cells
    for n, term in sorted(known.items()):
        if n in derived and derived[n] != term:
            print(f"{DERIVED}: a({n}) derived {derived[n]}, published {term} - ABORT")
            return 1
    checked = len(set(derived) & set(known))
    print(f"{DERIVED}: agrees with all {checked} published terms in range")

    results = []
    for aid, vals in list(computed.items()) + [(DERIVED, derived)]:
        pub = len(terms_by_n(aid))
        path = stage(aid, vals)
        results.append((aid, pub, len(vals), len(vals) - pub))
        print(f"{aid}: staged {len(vals)} terms to {path.name}")

    print("\n" + "=" * 52)
    print(f"{'sequence':10s} {'published':>10s} {'now':>6s} {'new':>5s}")
    for aid, pub, total, new in results:
        print(f"{aid:10s} {pub:>10d} {total:>6d} {new:>5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
