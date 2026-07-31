# Theseus Phase 2 — local board graphs

**Date:** 2026-07-31
**Status:** design, not yet approved for execution
**Prerequisite:** Phase 1 complete — 28 new terms staged across 8 bishop sequences

## 1. Why Phase 2 is a different problem

Phase 1 rested on one structural fact: the bishop graph is a **rook** graph, whose
cliques are whole classes. That is what let domination collapse to a vertex-cover
condition on the support.

**That collapse does not transfer.** On a grid, king or knight graph a vertex's
closed neighbourhood is a handful of nearby cells, not an entire class. The
Phase 1 rule ("occupancy collapses, populations do not") was derived on rook
graphs and must not be assumed here.

What transfers instead is the *sweep discipline*: these graphs are **local** under
a row-major sweep, so a broken-profile DP applies, with a boundary window equal to
the graph's bandwidth:

| graph | bandwidth | profile states |
|---|---|---|
| grid | n | ~2^n |
| king | n+1 | ~2^(n+1) |
| knight | 2n+1 | ~2^(2n+1) |
| torus grid | n, plus a wrap | ~2^n per fixed boundary, ~4^n overall |

## 2. The seam

**230 sequences carry `keyword:more`** across grid, king, knight, triangular-grid
and torus-grid families (`data/phase2_survey.json`, surveyed 2026-07-31). By
predicate, the largest groups are paths (9), irredundant sets (8), maximal
matchings (8), maximal irredundant sets (8), minimum total dominating sets (8).

### The trap in the short entries

Many of the 3- and 4-term sequences are **`n X n X n`** — three-dimensional grid
graphs, with n^3 vertices. A profile there spans a whole n X n cross-section, so
the state is ~2^(n^2): n=4 is 65k and fine, n=5 is 33M and marginal, n=6 is out of
reach. They look like the easiest targets and are among the hardest. Do not open
Phase 2 with them.

## 3. First target: the 2-D torus domination family

| sequence | counts | terms | offset |
|---|---|---|---|
| A298106 | connected dominating sets, n X n torus | 5 | 3 |
| A295428 | minimal dominating sets, n X n torus | 5 | 3 |
| A348000 | minimal total dominating sets, n X n torus | 5 | 3 |
| A382530 | minimum connected dominating sets, n X n torus | 5 | 3 |

Chosen because: two-dimensional, only five published terms each, one engine
serves all four, and domination is the predicate Phase 1 showed to be cheapest.

The torus costs an extra factor. On C(n) square C(n) both wraps must be honoured:
fix the first row's contribution to the wrap, sweep, then require consistency at
the end — i.e. run the sweep once per boundary condition and sum. That is 2^n
sweeps of 2^n-ish states, ~4^n overall, which should reach n≈12 and give roughly
+5 terms per sequence.

**This is an estimate, not a measurement.** The first task must measure reachable
state growth and report it before any term is claimed, exactly as Phase 1 did.

## 4. Verification

Unchanged from Phase 1, and non-negotiable:

- **L0** brute force straight from the graph definition, small n
- **L1** fast counter equals brute force wherever both run
- **L2** every published term reproduced, indexed by the sequence's true offset
- **L3** two independent algorithms agree
- **L4** structural identities that follow from the problem

L4 needs new identities here, since the bishop-specific ones (two components,
even-n colour isomorphism) do not apply. Candidates: the torus is vertex-transitive,
so counts of "sets containing a given vertex" scale by n^2; and grid-graph counts
must match torus counts when the wrap adds no edges (n <= 2).

## 5. Honest expectations

- Weisstein reached the published terms by some undisclosed method that was not
  naive enumeration. Beating it is not guaranteed for any given predicate.
- Expect +3 to +6 terms where it works, and expect some predicates not to work at
  all. Phase 1 produced two such negative results (total domination, colourings);
  Phase 2 will produce more, and they get recorded.
- Knight graphs have bandwidth 2n+1, so their profile is squared relative to the
  grid. Treat them as a stretch target, not a first one.

## 6. Non-goals

Three-dimensional grids (see the trap above). Queen graphs, whose adjacency spans
whole rows, columns and diagonals so no bounded-width profile exists. Any
predicate needing full colour sets per boundary cell — Phase 1 proved that class
is Latin-square hard and no sweep fixes it.
