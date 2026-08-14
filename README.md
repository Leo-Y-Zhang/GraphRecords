# GraphRecords

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

The n-triangular honeycomb board reduces further still. Its cells are barycentric
`(x, y, z)` with `x + y + z = n - 1`, and a bishop moves along constant `x` and
constant `y`, so the cell already *is* its class pair: that graph is the rook
graph on the staircase `{(x, y) : x + y <= n - 1}` with no map needed. It is
connected, so unlike the square board there is no black-plus-white identity to
check against — an independent author's b-file does that job instead.

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

As of 2026-08-14 the gate is **292 checks + 607 tests, exit 0**, and takes about
seven minutes: most of that is re-deriving the claimed terms from cold, which is
the point of it.

## Layout

- `graphrecords/boards.py` - board cell sets and explicit graph construction,
  square, rectangular and triangular-honeycomb
- `graphrecords/reduction.py` - the bishop-to-rook map, with its proof and
  self-check, and the honeycomb staircase
- `graphrecords/brute.py` - exhaustive reference counters (verification level L0)
- `graphrecords/connected.py` - two independent fast counters: exact-support peeling,
  and the frontier partition DP used in production
- `graphrecords/targets.py` - offline snapshot of published OEIS terms
- `bench/measure_growth.py` - state-growth and timing measurement
- `bench/measure_honeycomb.py` - the same, for the honeycomb board, reporting
  peak RSS because memory rather than time is what ends these runs
- `verify_all.py` - the gate

## Status

The ten Phase 1 terms — A290719, A290769 and A291595 a(10)-a(11), A289145 and
A289169 a(9)-a(10) — were submitted to OEIS by the operator and **approved on
2026-08-13**, all five sequences the same day. `data/upstream_bfiles.json` is the
probe that measured each published b-file afterwards, and the staged files in
`OEIS-upload/` are now an archive of exactly what was sent.

Four honeycomb terms have since been computed and gated — A290783 a(10) and
A381795 a(8)-a(10), recorded in `data/honeycomb_new_terms.json`. Two of them rest
on a second independent algorithm and two do not; `PAPER.md` section 6 says which
and why, per term rather than in aggregate.

Nothing else here has been submitted, and nothing will be without explicit
per-submission authorisation.

## Verified from a clean clone

2026-08-01: cloned fresh from GitHub into an empty directory and run cold —
**189 gate checks + 301 tests, exit 0**, with no local state of any kind. The
staged b-files also come out of a fresh Windows checkout **LF-only**, which is
what `.gitattributes` is for: git would otherwise rewrite them to CRLF and
silently violate the OEIS b-file spec.

    git clone --branch phase1-bishop-family <repo> && cd GraphRecords && python verify_all.py
