"""Compute terms beyond the published data and stage them.

Every published term is recomputed first, indexed by the sequence's true offset.
If any disagrees, nothing is staged -- a disagreement means the algorithm is
wrong, not that the published data is.

Three sequences come out of two computations: the full bishop graph has exactly
two components, so its connected-subgraph count is the sum of the black and white
counts. That derived sequence is checked against its own published terms before
being staged, so it is a real cross-check and not just arithmetic.

b-files are written LF-only with no BOM and a trailing newline, as the OEIS
b-file spec requires. Staging is NOT submission.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from graphrecords.connected import frontier_connected            # noqa: E402
from graphrecords.memguard import start as memguard_start        # noqa: E402
from graphrecords.targets import offset_start, terms_by_n        # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"

COLOUR_SEQUENCES = {"A290719": "black", "A290769": "white"}
DERIVED = "A291595"          # full bishop graph = black + white


def compute(aid, colour, limit, budget):
    """Reproduce every published term, then extend. Returns {n: value} or None."""
    known = terms_by_n(aid)
    print(f"\n=== {aid} ({colour} bishop, offset {offset_start(aid)}, "
          f"{len(known)} published terms) ===")

    for n, term in sorted(known.items()):
        got = frontier_connected(n, colour)
        if got != term:
            print(f"{aid}: a({n}) recomputed as {got}, published {term} - ABORT")
            return None
    print(f"{aid}: reproduced all {len(known)} published terms")

    values = dict(known)
    n = max(known) + 1
    while n <= limit:
        t0 = time.time()
        values[n] = frontier_connected(n, colour)
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
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--budget", type=float, default=1800.0,
                    help="stop a sequence once a single term exceeds this many seconds")
    ap.add_argument("--mem-floor", type=float, default=1.0,
                    help="abort if free RAM falls below this many GB")
    args = ap.parse_args()
    memguard_start(floor_gb=args.mem_floor, label="connected subgraph extension")

    computed = {}
    for aid, colour in COLOUR_SEQUENCES.items():
        vals = compute(aid, colour, args.limit, args.budget)
        if vals is None:
            print("ABORTING: nothing will be staged")
            return 1
        computed[aid] = vals

    black, white = computed["A290719"], computed["A290769"]

    # derive the full bishop graph, then check it against its own published data
    print(f"\n=== {DERIVED} (full bishop graph, derived as black + white) ===")
    derived, known = {}, terms_by_n(DERIVED)
    for n in sorted(set(black) & set(white)):
        derived[n] = black[n] + white[n]
    # n=1 has no white cells, so white contributes 0 and is absent from its dict
    if 1 in black and 1 not in derived:
        derived[1] = black[1]
    for n, term in sorted(known.items()):
        if n in derived and derived[n] != term:
            print(f"{DERIVED}: a({n}) derived as {derived[n]}, published {term} - ABORT")
            return 1
    checked = len(set(derived) & set(known))
    print(f"{DERIVED}: derived values agree with all {checked} published terms in range")

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
