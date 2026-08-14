"""Re-check every claim in this repository from cold.

Exits 0 only if every verification level passes. Believe this over any prose,
here or anywhere else.

  L0  the reduction theorem, checked exhaustively
  L1  fast counter against exhaustive enumeration
  L2  fast counter against every published OEIS term, indexed by true n
  L3  two independent fast algorithms against each other
  L4  structural identities that hold for the problem, not just for our code
  L5  the terms this repo claims as new, re-derived and measured against the probe
"""
import json
import pathlib
import subprocess
import sys

from graphrecords.boards import (
    adjacency_masks,
    honeycomb_adjacent,
    honeycomb_cells,
)
from graphrecords.brute import (
    brute_connected_bishop,
    brute_dominating_bishop,
    brute_total_dominating_bishop,
    connected_dominating_count,
    connected_induced_count,
)
from graphrecords.cds_peeling import peeling_connected_dominating
from graphrecords.connected import frontier_connected, peeling_connected
from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.domination import dominating_sets, total_dominating_sets
from graphrecords.reduction import HONEYCOMB, class_grid, verify_isomorphism
from graphrecords.targets import bfile_terms_by_n, terms_by_n

# total domination is far more expensive than plain domination and cannot reach
# its own published ceiling; the gate checks it only as far as it stays cheap
TOTAL_LIMIT = 9

# How far the honeycomb sweeps are re-run from cold. n=10 is the reach of this
# work, and re-deriving it here costs about 90 s of the gate's runtime -- paid
# deliberately, because a claimed term that nothing re-derives is a number in a
# file rather than a result.
HONEYCOMB_LIMIT = 10

# A290941 counts dominating sets of the honeycomb bishop graph and an
# independent author published a b-file for it to n=50. Agreeing with that far
# past where brute force stops (n=6) is the strongest evidence available that
# the staircase really is this graph, so it is worth more than any DATA line.
# It is NOT a contribution target, and neither is A304553: both are already at
# n=50, which is exactly the misreading that wasted a day on A289164/A295898.
ANCHOR_LIMIT = 20

NEW_TERMS = pathlib.Path(__file__).resolve().parent / "data" / "honeycomb_new_terms.json"

CHECKS = []


def check(name, ok):
    CHECKS.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    sys.stdout.flush()


def main():
    # L0: the reduction itself
    for n in range(1, 13):
        for colour in ("black", "white"):
            try:
                verify_isomorphism(n, colour)
                check(f"L0 isomorphism n={n} {colour}", True)
            except AssertionError as exc:
                check(f"L0 isomorphism n={n} {colour}: {exc}", False)

    # L1: fast vs exhaustive
    for n in range(1, 7):
        for colour in ("black", "white"):
            check(
                f"L1 frontier == brute n={n} {colour}",
                frontier_connected(n, colour) == brute_connected_bishop(n, colour),
            )

    # L2: published terms, indexed by true n (offsets are not uniform)
    for aid, colour in (("A290719", "black"), ("A290769", "white")):
        for n, term in sorted(terms_by_n(aid).items()):
            check(f"L2 {aid} a({n})", frontier_connected(n, colour) == term)

    # L3: two independent fast algorithms
    for n in range(1, 9):
        for colour in ("black", "white"):
            check(
                f"L3 frontier == peeling n={n} {colour}",
                frontier_connected(n, colour) == peeling_connected(n, colour),
            )

    # L4: structural identities
    for n, term in sorted(terms_by_n("A291595").items()):
        check(
            f"L4 A291595 a({n}) == black + white",
            frontier_connected(n, "black") + frontier_connected(n, "white") == term,
        )
    for n in (2, 4, 6, 8):
        check(
            f"L4 colours isomorphic on even board n={n}",
            frontier_connected(n, "black") == frontier_connected(n, "white"),
        )

    # the class grid must be 0/1 -- the domination counters rely on it
    for n in range(1, 13):
        for colour in ("black", "white"):
            grid, _, _ = class_grid(n, colour)
            check(
                f"L0 class grid is 0/1 n={n} {colour}",
                all(v in (0, 1) for row in grid for v in row),
            )

    # domination: fast vs exhaustive, then against published terms
    for n in range(1, 7):
        for colour in ("black", "white"):
            check(
                f"L1 dominating == brute n={n} {colour}",
                dominating_sets(n, colour) == brute_dominating_bishop(n, colour),
            )
            check(
                f"L1 total dominating == brute n={n} {colour}",
                total_dominating_sets(n, colour)
                == brute_total_dominating_bishop(n, colour),
            )
    for aid, colour in (("A289164", "black"), ("A289170", "white")):
        for n, term in sorted(terms_by_n(aid).items()):
            check(f"L2 {aid} a({n})", dominating_sets(n, colour) == term)
    for aid, colour in (("A303145", "black"), ("A303147", "white")):
        for n, term in sorted(terms_by_n(aid).items()):
            if n <= TOTAL_LIMIT:
                check(f"L2 {aid} a({n})", total_dominating_sets(n, colour) == term)

    # L4: dominating sets MULTIPLY across the two components (connected ones add)
    for n, term in sorted(terms_by_n("A295898").items()):
        check(
            f"L4 A295898 a({n}) == black * white",
            dominating_sets(n, "black") * dominating_sets(n, "white") == term,
        )

    # --- the n-triangular honeycomb bishop board ---------------------------
    #
    # A different board reaching the same engines. Its bishop graph is the rook
    # graph on the staircase {(x,y) : x+y <= n-1}, so every counter above gets
    # there through the class grid alone and nothing downstream changed. The
    # graph is CONNECTED -- there is no colour split, so the black-plus-white
    # identity has no analogue here and its place is taken by the containment
    # inequalities at L4 and by an independent author's b-file at L2.
    hive_cis = {}
    hive_cds = {}
    hive_dom = {}
    for n in range(1, HONEYCOMB_LIMIT + 1):
        hive_cis[n] = frontier_connected(n, HONEYCOMB)
        hive_cds[n] = connected_dominating_sets(n, HONEYCOMB)
        hive_dom[n] = dominating_sets(n, HONEYCOMB)

    # L1: against brute force over the graph built from BARYCENTRIC COORDINATES,
    # never from the class grid. A grid checked against itself proves nothing;
    # this is the check that would catch a wrong grid.
    for n in range(1, 7):
        nbr = adjacency_masks(honeycomb_cells(n), honeycomb_adjacent)
        check(
            f"L1 honeycomb connected == brute n={n}",
            hive_cis[n] == connected_induced_count(nbr),
        )
        check(
            f"L1 honeycomb connected dominating == brute n={n}",
            hive_cds[n] == connected_dominating_count(nbr),
        )

    # L2: published terms of the two honeycomb sequences this work extends
    for n, term in sorted(terms_by_n("A290783").items()):
        check(f"L2 A290783 a({n})", hive_cis[n] == term)
    for n, term in sorted(terms_by_n("A381795").items()):
        check(f"L2 A381795 a({n})", hive_cds[n] == term)

    # L2: the anchor -- an independent author's b-file for this same graph
    anchor = bfile_terms_by_n("A290941")
    for n in range(1, ANCHOR_LIMIT + 1):
        check(f"L2 A290941 anchor a({n})", dominating_sets(n, HONEYCOMB) == anchor[n])
    for n, term in sorted(terms_by_n("A304553").items()):
        if n <= TOTAL_LIMIT:
            check(
                f"L2 A304553 anchor a({n})",
                total_dominating_sets(n, HONEYCOMB) == term,
            )

    # L3: the frontier sweeps against the exact-support peeling counters, which
    # share no code path with them beyond the class grid
    for n in range(1, 9):
        check(
            f"L3 honeycomb frontier == peeling n={n}",
            hive_cis[n] == peeling_connected(n, HONEYCOMB),
        )
        check(
            f"L3 honeycomb cds == cds peeling n={n}",
            hive_cds[n] == peeling_connected_dominating(n, HONEYCOMB),
        )

    # L4: containment, which relates three engines that share no counting logic.
    # A connected dominating set is in particular a non-empty connected induced
    # subgraph, and in particular a dominating set.
    for n in range(1, HONEYCOMB_LIMIT + 1):
        check(f"L4 honeycomb cds <= connected n={n}", hive_cds[n] <= hive_cis[n])
        check(f"L4 honeycomb cds <= dominating n={n}", hive_cds[n] <= hive_dom[n])

    # L5: the terms claimed as new. Each is re-derived from cold here, and each
    # is required to lie strictly beyond what the probe measured upstream --
    # claiming a term someone else already published is the failure this repo
    # has already made once, and it is now a gate rather than a memory.
    claimed = json.loads(NEW_TERMS.read_text(encoding="utf-8"))
    computed = {"A290783": hive_cis, "A381795": hive_cds}
    for aid, record in sorted(claimed.items()):
        published_to = bfile_terms_by_n(aid)
        check(
            f"L5 {aid} upstream reach still n={record['upstream_last_n']}",
            max(published_to) == record["upstream_last_n"],
        )
        for n_text, term in sorted(record["terms"].items(), key=lambda kv: int(kv[0])):
            n = int(n_text)
            check(f"L5 {aid} a({n}) re-derives", computed[aid][n] == term)
            check(f"L5 {aid} a({n}) is genuinely new", n > record["upstream_last_n"])

    # the test suite is part of the gate
    rc = subprocess.call([sys.executable, "-m", "pytest", "-q"])
    check("pytest suite", rc == 0)

    failed = [name for name, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)} passed / {len(failed)} failed")
    if failed:
        print("FAILURES:")
        for name in failed:
            print("  ", name)
        return 1
    print(f"verify_all: ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
