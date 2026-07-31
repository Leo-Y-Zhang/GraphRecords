# Theseus — an enumeration engine for OEIS board-graph sequences

**Date:** 2026-07-31
**Status:** design approved (scope: Phase 1 then Phase 2)
**Repo:** `C:\dev\Theseus` (private; visibility is the operator's decision, never mine)

## 1. Problem

A large, coherent block of OEIS counts subsets of chess and grid boards — independent
sets, dominating sets, matchings, irredundant sets, connected induced subgraphs,
Hamiltonian paths — on the n X n grid, king, knight, bishop, queen, torus-grid and
triangular-grid graphs. Most were contributed by Eric W. Weisstein in 2017-18 and by a
handful of others since. They stop after 5-11 terms and have never been revisited.

The goal is to compute new terms for as many of them as an honest algorithm allows,
with every claim machine-verified against the published data before it is believed.

## 2. Verified premises

Each of these was checked in this session, not assumed.

| Claim | How it was established |
|---|---|
| The seam is large | OEIS search: **462** sequences across the seven board-graph families carry `keyword:more` |
| The entries really are short | **30/30** sampled have `bfile_terms == data_terms` — no hidden b-file behind a truncated DATA line |
| No method is on record | **0/6** inspected carry any program, formula or comment; only MathWorld links |
| Our graph models are correct | An independent brute force reproduces the published A290719 for n=1..6 exactly |
| The bishop reduction is real | Verified exhaustively for n=1..11 (Section 4) |
| The reduction pays | Reproduces **all 8** published A290719 terms; a(8)=3852814320 in 3.5 s vs 2^32 brute-force subset checks |

### Negative result worth recording

The *fixed-width strip* shape (`6 X n`, `7 X (2n+1)`), where a transfer matrix yields a
linear recurrence and therefore unlimited terms, is **already harvested**. Alois P. Heinz
and Seiichi Manyama hold b-files of 501, 432, 226 and 200 terms on exactly those
sequences. We do not compete there. This is why the project targets square boards, and
why the honest yield is "+3 to +8 terms on many sequences" rather than "10x the terms":
square-board counts grow doubly exponentially, so no algorithm buys an order of magnitude
in n.

## 3. Scope

**Phase 1 — the bishop family.** Every sequence defined on the n X n bishop or black/white
bishop graph, attacked through the rook reduction. Known targets: A291595, A290719
(connected induced subgraphs), A289145 (connected dominating sets), A307934, A234632,
A308146, A234637 (Hamiltonian paths), A371202 (minimum vertex colourings). A full sweep
of the family is part of the work.

**Phase 2 — broken-profile DP for local board graphs.** Grid, king, knight, triangular
grid and torus-grid graphs, where adjacency has bounded reach under a row-major sweep.
Predicate families: independent / dominating / total dominating / minimal / maximal /
irredundant sets, matchings, and connectivity-aware variants via plug DP.

**Non-goals.** The queen graph (adjacency spans whole rows, columns and diagonals, so no
bounded-width profile exists — excluded unless a separate idea appears). Auto-generated
Hardin-style families (extending them would be OEIS spam). Authoring new sequences.

## 4. The bishop reduction

**Theorem.** Let `B_n = {(r,c) : 0 <= r,c < n, r+c even}` be the black cells of the n X n
board, and define `phi(r,c) = ((r+c) // 2, (r-c+n) // 2)`. Then `phi` is injective on
`B_n`, and for distinct `a, b` in `B_n`, `a` and `b` share a diagonal if and only if
`phi(a)` and `phi(b)` agree in their first or their second coordinate.

**Proof.** Cells `a, b` share an anti-diagonal iff `r_a + c_a = r_b + c_b`, which holds iff
the first coordinates agree, since `t -> t // 2` is injective on the even values taken by
`r+c`. They share a main diagonal iff `r_a - c_a = r_b - c_b`. On `B_n`, `r+c` even forces
`r-c` even, and on even values `t -> (t+n) // 2` is strictly monotone, hence injective; so
this holds iff the second coordinates agree. Injectivity of `phi` follows because the pair
`(r+c, r-c)` determines `(r,c)`. []

**Consequence.** The black bishop graph is exactly the *rook graph* on the image cell set
(a diamond region): two cells are adjacent iff they share an x-class or a y-class. The
white bishop graph is the same construction on the complementary colour, and the full
bishop graph is their disjoint union — it has exactly two components.

This converts "subset of cells" problems into problems on the bipartite incidence
structure between x-classes and y-classes, whose size is O(n) per side rather than
O(n^2/2) cells.

## 5. Algorithms

### 5.1 Reference counter — exact-support peeling (implemented, validated)

For connected cell subsets. Let `B(X,Y)` be the number of cell subsets whose x-support is
exactly `X` and y-support exactly `Y`, obtained from `2^cells(X',Y')` by Mobius inversion
over sub-masks. Let `C(X,Y)` be those that are also connected. Peeling the component that
contains the lowest x-class of `X`:

```
C(X,Y) = B(X,Y) - sum over (X1 containing lowx, Y1 nonempty, (X1,Y1) != (X,Y))
                       of C(X1,Y1) * B(X \ X1, Y \ Y1)
answer  = sum over nonempty X, Y of C(X,Y)
```

Cost is `O(3^|X| * 3^|Y|)`, i.e. roughly `9^n`. **Status: implemented and validated —
reproduces published A290719 for n=1..8 exactly.** This is the trusted reference, not the
production algorithm.

### 5.2 Production counter — frontier partition DP (to build)

Process x-classes in order, carrying a state that is a set partition of the y-classes into
connected groups. For each x-class choose a non-empty subset `T` of y-classes to place
cells in, weight `prod over j in T of (2^grid[i][j] - 1)`, and merge the blocks meeting
`T`. State count is bounded by the Bell number of the frontier width. Because each
x-class of the diamond meets a contiguous interval of y-classes, the live frontier is
bounded and far smaller than the worst case.

This is the algorithm that must beat n=9. Its reachable-state growth will be **measured**,
not estimated, and the measurement decides how many new terms Phase 1 yields.

### 5.3 Other Phase 1 predicates

Connected dominating sets add a per-y-class domination flag to the frontier state.
Hamiltonian paths use plug DP with matching states over the rook structure. Minimum
vertex colourings exploit the fact that a rook graph's chromatic number is governed by
the largest class.

### 5.4 Phase 2 — broken-profile DP

Row-major sweep with a window equal to the graph's bandwidth (n for grid, n+1 for king,
2n+1 for knight). Per boundary cell the state carries membership, domination count capped
at 2, and predicate-specific flags (private-neighbour secured, matched, component id).
Reachable state counts are measured per predicate and per board; predicates whose state
space explodes are reported as such rather than quietly dropped.

## 6. Verification architecture

Nothing is claimed unless it survives all applicable levels.

- **L0 — brute force.** An independent implementation built straight from the graph
  definition, enumerating all subsets. Feasible to ~22 cells. Catches modelling errors.
- **L1 — agreement on overlap.** Fast algorithm must equal brute force wherever both run.
- **L2 — published terms.** Fast algorithm must reproduce **every** published term of
  every target sequence. For the Phase 1 bishop family that is of the order of a hundred
  terms; across the full 462-sequence seam addressed in Phase 2 it is a few thousand.
  The exact count is reported by the gate, never estimated in prose.
- **L3 — independent algorithms.** Reference peeling counter vs production frontier DP
  must agree wherever both run.
- **L4 — cross-sequence identities.** Structural relations that must hold, e.g. the full
  bishop graph has two components, so its connected-induced-subgraph count is the sum of
  the black and white counts. These catch errors that L0-L3 share.
- **Gate.** `verify_all.py` re-runs every level from cold and exits non-zero on any
  failure, in the style already used in MathRecords.

A new term is reported only if it comes from an algorithm that passed L1-L4 on that exact
sequence, and, where affordable, from two independent algorithms.

## 7. Deliverables

1. `theseus/` — the engine: board constructors, the bishop reduction, reference and
   production counters, predicate modules.
2. `verify_all.py` — the gate described above.
3. `bench/` — brute force vs reduction timing curves, demonstrating the complexity change.
4. `OEIS-upload/` — staged b-files and entry text, LF-normalised, **nothing submitted**.
5. `PAPER.md` — the reduction theorem with proof, the algorithms, the measured state
   growth, the results table, and an honest statement of the ceiling.

## 8. Submission policy

Computation and submission are decoupled. The operator's standing OEIS directives govern:
one submission at a time, zero editor friction, and **A217058 must be accepted first**.
Even a large batch of verified extensions will be staged and held. When A217058 clears, we
land one, confirm it is received well, and ask an editor how they would prefer the rest.
Submitting is the operator's act, never mine.

House style already learned from the A217058 review, to be applied here from the start:
US spelling; comments short and written for a general reader; define terms the entry does
not already define; full first names rather than initials in LINKS; never alter existing
lines; sign multi-paragraph comments with the `(Start)` / `(End)` wrapper.

## 9. Risks and honest ceilings

- **The frontier DP may not beat the published terms by much.** Weisstein reached
  a(8)=111452109386 on some of these, so his method was not naive. Mitigation: measure
  state growth early; if a predicate yields nothing, report that and move on.
- **The yield is terms, not orders of magnitude.** Stated plainly in the write-up. The
  contribution is new mathematical data plus a published method where none existed, not a
  1000x extension.
- **Big integers.** Counts exceed 64 bits; Python ints or `gmpy2` throughout, and any
  C# hot loop must not silently overflow. Explicit overflow checks required.
- **Machine limits.** ~5 GB free RAM and 16 cores. Long runs go to detached scripts with
  status files, following the MathRecords pattern, and never oversubscribe the box.
