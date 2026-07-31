# Theseus - session handoff

**Last updated:** 2026-07-31, session b0ad5ff3
**Branch:** `phase1-bishop-family` (no remote yet - creating one is the operator's act)
**Gate:** `python verify_all.py` -> 83 checks + 115 pytest tests, exit 0

## What this is

Extending OEIS sequences on board graphs. The n X n bishop graph is a rook graph
in rotated coordinates, which collapses subset counting from O(2^(n^2/2)) to a
frontier DP over O(n) classes per side. Full reasoning in
`docs/superpowers/specs/2026-07-31-oeis-board-graph-enumeration-design.md`.

## LOAD DISCIPLINE — read before launching anything

**Run extension jobs ONE AT A TIME.** Three concurrent jobs took free RAM from
5.8 GB to 0.9 GB and the guards started firing. Use the serial chain:

    python -u tools/extend_domination.py --limit 20 --budget 900
    python -u tools/extend_cds.py        --limit 10 --budget 900

Known-safe limits, from where the blow-ups actually happened:
`extend_domination --limit 20` (a(21) ballooned to 5.6 GB),
`extend_cds --limit 10` (a(11) reached 4.6 GB),
`extend.py --limit 11` for connected subgraphs (n=12 is the wall).

**Guard bug fixed 2026-07-31:** a watchdog triggering on low free RAM alone kills
whatever it is watching, not whatever caused the shortage -- it killed a job
holding 0.86 GB while the 4.58 GB hog survived. `ram_guard.ps1` now requires
free RAM low AND the target itself large (`-MinTargetGB`).

## Third predicate: connected dominating sets

`theseus/connected_domination.py`. Composes both collapses. Connectivity gives
the frontier partition; domination costs only a requirement bit, because a
y-class carries a non-zero block label exactly when it holds a chosen cell, which
is what domination already asks. Reproduces all 8 published terms of A289145 and
all 7 of A289169; reaches n=10.

There is deliberately no full-bishop version: a connected set lies in one
component and cannot dominate the other, and OEIS has no such sequence, which the
test suite asserts.

## Second predicate: domination (2026-07-31, later)

`theseus/domination.py`. Support-collapse lemma: a set dominates iff its support
is a vertex cover of the cell bipartite graph, so domination depends only on
which classes are occupied. Reaches **n=18** where connected subgraphs reach 11.

Extending A289164 (15 published terms), A289170 (14), A295898 (12, derived as the
**product** -- domination multiplies across components where connected subgraphs
add). Run in `bench/out/extend_dom.log`.

**Sharp rule found, and it is the interesting part of the write-up:** predicates
needing only *occupancy* collapse; predicates needing class *populations* do not.
Total domination (open neighbourhood, so a chosen cell must not cover itself)
needs 6 states per class and stalls at n=11 against 16 published terms -- it
**cannot** extend its own sequences. That negative result is recorded in PAPER.md
on purpose.

Two performance lessons, both worth reusing:
- Enumerating all `2^|cols|` subsets per state is the trap. Deciding y-classes
  one at a time cut n=13 from 30.67 s to 0.39 s (79x).
- Store a *deficit*, never a raw requirement. Once a class saturates, several
  requirement values behave identically; merging them cut n=10 from 36 s to 6.6 s.

## Confirmed result

**A290719 a(10) = 1090550900687379** - a term not in OEIS. Confirmed three ways:

1. exact-support peeling algorithm (510.7 s)
2. frontier partition DP on the black board (53.5 s)
3. frontier partition DP on the **white** board (118.3 s) - a different board that
   must give the same value at even n by the reflection isomorphism, and does

All 17 published terms across A290719 (9) and A290769 (8) are reproduced exactly,
and the two-component identity holds for all 9 published terms of A291595.

## Exactly what to do next

1. Check `bench/out/extend.log` and `bench/out/growth.log`. Both were running at
   session end (n=11, then n=12 if it fits the budget).
2. When they finish, write `PAPER.md`: the reduction theorem and proof (copy from
   `theseus/reduction.py`), both algorithms and their costs, the measured
   peak-state table from `growth.log`, the results table, and an explicit
   statement of which n became infeasible and why.
3. Re-run `python verify_all.py` and confirm exit 0.
4. Phase 2 needs its own plan, written only after the state-growth numbers are in.

## Measured state growth (black board)

    n      1   2    3    4    5    6     7     8      9      10
    peak   2   2   10   11  101  151  1596  3136  39955  86321
    secs   0   0    0    0    0    0   0.09  0.43   9.73   53.5

Roughly x2.5 to x12 per step. Projects to n = 12-13 as the practical ceiling,
i.e. +3 to +4 terms per sequence. Do not promise more than that.

## Standing constraints

- **Nothing is submitted to OEIS.** Staged only, in `OEIS-upload/`. A217058 must
  be accepted first, then one submission at a time, each explicitly authorised.
- The repo is local-only and private. Creating a GitHub remote or making it
  public is the operator's decision, never mine.
- Offsets are NOT uniform across this family (A290719 starts at n=1, A290769 at
  n=2). Always index by true n via `theseus.targets.terms_by_n`.
- Counts exceed 64 bits. Python ints only; never a fixed-width accumulator.

## Traps already hit, do not repeat

- `stripped.gz` holds only the DATA line, so term counts there can understate a
  sequence that has a b-file. Always confirm against the live entry.
- An OEIS search whose result count is an exact multiple of 10 returns an empty
  body on the next page rather than a short page. Treat that as end-of-results.
- The fixed-width-strip seam (`6 X n` etc.) is already harvested by Alois Heinz
  and Seiichi Manyama, with b-files of 200-500 terms. Do not compete there.
