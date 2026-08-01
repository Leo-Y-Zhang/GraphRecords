# Theseus

Extending OEIS sequences defined on board graphs, starting with the bishop graph.

## The idea

The n X n bishop graph is a rook graph in rotated coordinates. The map

    phi(r, c) = ((r + c) // 2, (r - c + n) // 2)

sends anti-diagonals to rows and main diagonals to columns, so two cells of one
colour share a diagonal exactly when their images share an x-class or a y-class.
That turns subset counting over O(n^2) cells into a problem on a bipartite
structure with O(n) classes per side.

A bishop never changes the parity of row+col, so the bishop graph has exactly two
components (the black cells and the white cells) and the reduction is applied to
each separately.

## Verifying

    python verify_all.py

This is the authoritative gate. It re-derives the isomorphism exhaustively,
checks the fast counters against brute-force enumeration, reproduces every
published OEIS term of every target indexed by its true offset, cross-checks two
structurally independent fast algorithms, and enforces identities that follow
from the problem rather than from the code. Believe it over any claim written in
prose.

Offsets are not uniform across this family: A290719 starts at n=1 but A290769
starts at n=2, because a 1 X 1 board has no white cells. Anything comparing
output to published data indexes by n, never by list position.

## Layout

- `theseus/boards.py` - board cell sets and explicit graph construction
- `theseus/reduction.py` - the bishop-to-rook map, with its proof and self-check
- `theseus/brute.py` - exhaustive reference counters (verification level L0)
- `theseus/connected.py` - two independent fast counters: exact-support peeling,
  and the frontier partition DP used in production
- `theseus/targets.py` - offline snapshot of published OEIS terms
- `bench/measure_growth.py` - state-growth and timing measurement
- `verify_all.py` - the gate

## Status

Nothing here has been submitted to OEIS, and nothing will be without explicit
per-submission authorisation.

## Verified from a clean clone

2026-08-01: cloned fresh from GitHub into an empty directory and run cold —
**189 gate checks + 301 tests, exit 0**, with no local state of any kind. The
staged b-files also come out of a fresh Windows checkout **LF-only**, which is
what `.gitattributes` is for: git would otherwise rewrite them to CRLF and
silently violate the OEIS b-file spec.

    git clone --branch phase1-bishop-family <repo> && cd Theseus && python verify_all.py
