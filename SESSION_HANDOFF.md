# Theseus - session handoff

**Last updated:** 2026-07-31, session b0ad5ff3
**Branch:** `phase1-bishop-family`, pushed to private `GreenPandaTech/Theseus`
**Gate:** `python verify_all.py` -> exit 0 (count printed by the run itself)

## What this is

Extending OEIS sequences on board graphs. The n X n bishop graph is a rook graph
in rotated coordinates, which collapses subset counting from O(2^(n^2/2)) to a
frontier DP over O(n) classes per side. Full reasoning in
`docs/superpowers/specs/2026-07-31-oeis-board-graph-enumeration-design.md`.

## MEMORY IS THE WALL, NOT TIME

Both blow-ups were memory, not runtime: domination n=21 held 5.6 GB, connected
dominating n=11 held 4.6 GB. State counts grow only ~2.2x per step, so the fix is
a cheaper state, not a faster loop.

**Done for `theseus/domination.py`:** the DP state is packed into ONE integer
(hit mask | requirement mask << ny | placed bit << 2ny). A two-element tuple key
carries ~60 bytes of object overhead on top of the ints it holds, and with
millions of live states that overhead was the entire problem. Identical state
counts, all 15 published terms still reproduced, and n=18 went 46.7s -> 34.6s.

**Result:** packing worked. n=21 completed in 617 s at ~4.35 GB, where the tuple
version was killed at 5.6 GB. It also ran ~1.6x faster throughout. It bought
exactly ONE term, as predicted - growth is 2.2x per step, so a 2-3x memory saving
moves the wall one step and no further.

**Still to do:** `theseus/connected_domination.py` carries tuple keys AND a labels
tuple per state, so it has more overhead to reclaim than domination did. Expect
one more term (n=10 -> n=11) on A289145/A289169, not more.

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

**A289164, A289170 and A295898 are NOT contributions — do not recompute them.**
Their published b-files already reach n=50; the DATA line shows only 12-15 terms
because OEIS truncates it near 260 characters. Everything computed for them here,
to n=21, was already known.

What that did buy: all twenty overlapping terms agree with the published b-file
exactly, including a(21) at 67 digits, so the domination engine is validated
against an independent author who reached n=50 by an undisclosed method.

**The check is now mechanical.** `tools/probe_upstream_bfiles.py` records how far
every published b-file goes into `data/upstream_bfiles.json`, and a test refuses
to let a staged file count as a contribution unless it exceeds that. Run it before
staging anything. Never read the DATA line as the term count.

Composition still differs by predicate: domination **multiplies** across the two
colour components, connected subgraphs **add**.

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

**TEN new terms across FIVE sequences** (not 28 across 8 - see the correction
above). Measured against published b-files, not DATA lines:

    A290719  a(10), a(11)      A290769  a(10), a(11)      A291595  a(10), a(11)
    A289145  a(9),  a(10)      A289169  a(9),  a(10)

Staged in `OEIS-upload/`, LF-only, offsets correct, no published term altered.

**A290719 a(10) = 1090550900687379** - a term not in OEIS. Confirmed three ways:

1. exact-support peeling algorithm (510.7 s)
2. frontier partition DP on the black board (53.5 s)
3. frontier partition DP on the **white** board (118.3 s) - a different board that
   must give the same value at even n by the reflection isomorphism, and does

All 17 published terms across A290719 (9) and A290769 (8) are reproduced exactly,
and the two-component identity holds for all 9 published terms of A291595.

## Exactly what to do next

Phase 1 is COMPLETE and written up. Nothing is half-done. If you pick this up:

1. **Before anything else**, run `python verify_all.py` and confirm exit 0.
   (Verified 2026-07-31 from a CLEAN CLONE: 189 checks + 300 tests, exit 0, no
   local state, and the staged b-files come out of a fresh checkout LF-only.)
2. **Before staging any new sequence**, run `tools/probe_upstream_bfiles.py`.
   Reading the DATA line as the term count already cost a day once.
3. The ten staged terms wait on A217058 being accepted, then one submission at a
   time, each explicitly authorised by the operator. Submitting is never mine.
4. If extending further: pack `theseus/connected_domination.py` the way
   `theseus/domination.py` was packed (one integer per state). It still uses tuple
   keys plus a labels tuple and died at 4.6 GB on n=11. Packing bought exactly one
   term for domination (n=20 -> n=21), so expect one here too, not more.
5. Phase 2 is designed in `docs/superpowers/specs/2026-07-31-phase2-*.md` but is a
   thinner seam than Phase 1 - read its section 1 before committing to it.

## Measured state growth (black board)

    n      1   2    3    4    5    6     7     8      9      10
    peak   2   2   10   11  101  151  1596  3136  39955  86321
    secs   0   0    0    0    0    0   0.09  0.43   9.73   53.5

Roughly x2.5 to x12 per step. Projects to n = 12-13 as the practical ceiling,
i.e. +3 to +4 terms per sequence. Do not promise more than that.

## Standing constraints

- **Nothing is submitted to OEIS.** Staged only, in `OEIS-upload/`. A217058 must
  be accepted first, then one submission at a time, each explicitly authorised.
- The repo is private on GitHub. Making it PUBLIC is the operator's decision,
  never mine.
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
