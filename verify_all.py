"""Re-check every claim in this repository from cold.

Exits 0 only if every verification level passes. Believe this over any prose,
here or anywhere else.

  L0  the reduction theorem, checked exhaustively
  L1  fast counter against exhaustive enumeration
  L2  fast counter against every published OEIS term, indexed by true n
  L3  two independent fast algorithms against each other
  L4  structural identities that hold for the problem, not just for our code
"""
import subprocess
import sys

from theseus.brute import (
    brute_connected_bishop,
    brute_dominating_bishop,
    brute_total_dominating_bishop,
)
from theseus.connected import frontier_connected, peeling_connected
from theseus.domination import dominating_sets, total_dominating_sets
from theseus.reduction import class_grid, verify_isomorphism
from theseus.targets import terms_by_n

# total domination is far more expensive than plain domination and cannot reach
# its own published ceiling; the gate checks it only as far as it stays cheap
TOTAL_LIMIT = 9

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
