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

from theseus.brute import brute_connected_bishop
from theseus.connected import frontier_connected, peeling_connected
from theseus.reduction import verify_isomorphism
from theseus.targets import terms_by_n

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
