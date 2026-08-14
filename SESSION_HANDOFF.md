# GraphRecords - session handoff

**Last updated:** 2026-08-14
**Branch:** `phase1-bishop-family`, pushed to the private repo
**Gate:** `python verify_all.py` -> exit 0 (**292 checks + 607 tests**, run
2026-08-14 after the honeycomb work; it was 189 + 372 immediately before it)

## NEXT STEP, EXACTLY

Two of the four new honeycomb terms have no independent second algorithm yet.
Close that before anything else is considered, and before anything is submitted:

    python bench/measure_honeycomb.py cds-peel 10 --start 10    # ~30 min
    python bench/measure_honeycomb.py cis-peel 10 --start 10    # ~30 min

Each must print the value already recorded in `data/honeycomb_new_terms.json`
(`A381795 a(10) = 34698803291940384`, `A290783 a(10) = 35157891412269342`). On
agreement, add the entry to that file's `second_algorithm` map and update the
per-term table in `PAPER.md` section 6. On disagreement, **stop** - that is a
defect in one of two engines and neither term may be believed until it is found.

These are single ~30 minute jobs and cannot be split; they were not run on
2026-08-14 because that session was capped at 10 minute foreground calls with a
SAT gate already holding memory on the machine.

## HONEYCOMB BOARD (2026-08-14)

The n-triangular honeycomb bishop graph is the rook graph on the staircase
`{(x,y) : x+y <= n-1}` - barycentric `(x,y,z)` with `x+y+z = n-1`, adjacency in
constant `x` or constant `y`. No new counter was written: `boards.py` and
`reduction.py` gained the board and the grid, and every existing engine reaches
it through `class_grid(n, "honeycomb")`. `connected.py`, `connected_domination.py`,
`cds_peeling.py` and `brute.py` are untouched.

**The y-class order is REVERSED and that is worth 16x.** In the natural order
every x-interval starts at 0, so the stranded-block pruning can never fire.
Measured at n=9: connected induced 115,974 -> 33,817 states, connected dominating
839,563 -> 51,405. Do not "tidy" it back to the natural order.

**A290941 is the anchor and NOT a target** - dominating sets of this same graph,
published to n=50 by an independent author, reproduced here for n=1..20. Same for
A304553. Staging either would repeat the A289164/A295898 mistake exactly.

Four new terms, none submitted, none authorised: A290783 a(10), A381795 a(8),
a(9), a(10). `PAPER.md` section 6 holds the per-term confidence table. n=11 was
deliberately not attempted.

## SUBMISSION STATUS (2026-08-13, all by the operator, verified off oeis.org)

| Sequence | Terms | Status |
|---|---|---|
| A290719 | a(10)-a(11) | **APPROVED** Aug 13 12:18 EDT (8 min after proposal) |
| A290769 | a(10)-a(11) | **APPROVED** Aug 13 12:30 EDT |
| A291595 | a(10)-a(11) | **APPROVED** Aug 13 12:39 EDT |
| A289145 | a(9)-a(10)  | **APPROVED** Aug 13 12:41 EDT |
| A289169 | a(9)-a(10)  | **APPROVED** Aug 13 12:41 EDT |

Every submission: DATA + one EXTENSIONS line (`from _Leo Y. Zhang_, Aug 13 2026`),
one-line discussion note, no comment, no b-file (none of the five has an uploaded
b-file upstream; OEIS regenerates from DATA — A290719's confirmed regenerated to
n=11 after approval). Pre-paste gate + `tools/probe_upstream_bfiles.py` were run
fresh the same day. **ALL FIVE RESOLVED SAME-DAY: Phase 1 is fully landed — all ten
terms APPROVED and live on 2026-08-13, verified off `fmt=text` (every %T line carries
the new terms, every %E line credits _Leo Y. Zhang_). Nothing remains in `OEIS-upload/`
to send. The only unmeasured seam left in this repo is the bishop Hamiltonian-path
predicate (A307934/A234632/A308146/A234637) — measure state growth BEFORE building
anything, per the standing discipline.**

## INDEPENDENT CONFIRMATION - ALL TEN staged terms (closed 2026-08-01)

**No cross-check is running and none is owed.** The white-board n=11 peeling job
finished 2026-08-01 16:27 and AGREED: `A290769 a(11) = 1134335726831043925`
(peeling vs frontier DP, 670 s vs 2737 s), which confirms `A291595 a(11)` through
the addition identity. `PAPER.md` section 4 holds the authoritative per-term
table: seven terms rest on a second algorithm sharing no code path beyond the
class grid, three on a structural identity verified against every published term
of the sequence it governs.

`graphrecords/cds_peeling.py` is the second algorithm for A289145/A289169 - exact
support inclusion-exclusion, with domination as a predicate on the support. Run it
with `python tools/crosscheck_cds.py --from-n 9 --to-n 10 --colour black|white`.

**Do not re-run the cross-checks - all of them already passed** (A290719 a(10)
and a(11), A290769 a(11), and the four CDS terms). They are recorded in
`PAPER.md` and cost hours.

## What this is

Extending OEIS sequences on board graphs. The n X n bishop graph is a rook graph
in rotated coordinates, which collapses subset counting from O(2^(n^2/2)) to a
frontier DP over O(n) classes per side. Full reasoning in
`docs/superpowers/specs/2026-07-31-oeis-board-graph-enumeration-design.md`.

## MEMORY IS THE WALL, NOT TIME

Both blow-ups were memory, not runtime: domination n=21 held 5.6 GB, connected
dominating n=11 held 4.6 GB. State counts grow only ~2.2x per step, so the fix is
a cheaper state, not a faster loop.

**Done for `graphrecords/domination.py`:** the DP state is packed into ONE integer
(hit mask | requirement mask << ny | placed bit << 2ny). A two-element tuple key
carries ~60 bytes of object overhead on top of the ints it holds, and with
millions of live states that overhead was the entire problem. Identical state
counts, all 15 published terms still reproduced, and n=18 went 46.7s -> 34.6s.

**Result:** packing worked. n=21 completed in 617 s at ~4.35 GB, where the tuple
version was killed at 5.6 GB. It also ran ~1.6x faster throughout. It bought
exactly ONE term, as predicted - growth is 2.2x per step, so a 2-3x memory saving
moves the wall one step and no further.

**Done for `graphrecords/connected_domination.py` too - and it was NOT enough.**
The state is now a packed `bytes` key (556 -> 49 bytes per state, 11x), yet both
n=11 attempts still died near 4.4 GB, because at that size the memory is dict
entry overhead and big-integer counts, not key bytes. **CDS n=11 is OUT OF REACH
on this machine; do not retry it by shrinking keys again.** A289145/A289169 stop
at a(10). Any future attempt needs a different memory model entirely (flat arrays
with modular counts, off-heap), not a smaller key.

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

`graphrecords/connected_domination.py`. Composes both collapses. Connectivity gives
the frontier partition; domination costs only a requirement bit, because a
y-class carries a non-zero block label exactly when it holds a chosen cell, which
is what domination already asks. Reproduces all 8 published terms of A289145 and
all 7 of A289169; reaches n=10.

There is deliberately no full-bishop version: a connected set lies in one
component and cannot dominate the other, and OEIS has no such sequence, which the
test suite asserts.

## Second predicate: domination (2026-07-31, later)

`graphrecords/domination.py`. Support-collapse lemma: a set dominates iff its support
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
   (Last verified 2026-08-10 from a FRESH CLONE: 189 checks + 372 tests, exit 0,
   no local state, and the staged b-files come out of a fresh checkout LF-only.)
2. **Before staging any new sequence**, run `tools/probe_upstream_bfiles.py`.
   Reading the DATA line as the term count already cost a day once.
   (Last probed 2026-08-13 after the approvals: A289145/A289169 now published to
   n=10, A290719/A290769/A291595 to n=11 - i.e. upstream carries all ten of our
   terms, and `tests/test_staged_bfiles.py` now holds the staged files to
   matching what it serves.)
3. **The queue gate is satisfied: A217058 was ACCEPTED 2026-08-06.** The
   remaining van der Waerden submissions went next, per that campaign's own
   plan; these five followed on 2026-08-13, one at a time, each explicitly
   authorised by the operator. Submitting is never mine. Lesson from that approval: the reviewing editor
   deleted the entire comment on acceptance, so keep any submission here to the
   terms and an EXTENSIONS line unless an editor asks for more.
4. There is NO further computation left in Phase 1. The last candidate (CDS
   n=11 via a packed state) was built and measured to death twice at ~4.4 GB -
   see MEMORY IS THE WALL above. Do not reopen it by shrinking keys.
5. Phase 2 is designed in `docs/superpowers/specs/2026-07-31-phase2-*.md` but is a
   thinner seam than Phase 1 - read its section 1 before committing to it.

## Measured state growth (black board)

    n      1   2    3    4    5    6     7     8      9      10
    peak   2   2   10   11  101  151  1596  3136  39955  86321
    secs   0   0    0    0    0    0   0.09  0.43   9.73   53.5

Roughly x2.5 to x12 per step. Projects to n = 12-13 as the practical ceiling,
i.e. +3 to +4 terms per sequence. Do not promise more than that.

## Standing constraints

- **Phase 1's ten terms were submitted and APPROVED 2026-08-13** (table at the
  top). Nothing else here goes to OEIS: any future submission is one at a time,
  each explicitly authorised by the operator, and submitting is never mine.
- The repo is private on GitHub. Making it PUBLIC is the operator's decision,
  never mine.
- Offsets are NOT uniform across this family (A290719 starts at n=1, A290769 at
  n=2). Always index by true n via `graphrecords.targets.terms_by_n`.
- Counts exceed 64 bits. Python ints only; never a fixed-width accumulator.

## Traps already hit, do not repeat

- `stripped.gz` holds only the DATA line, so term counts there can understate a
  sequence that has a b-file. Always confirm against the live entry.
- An OEIS search whose result count is an exact multiple of 10 returns an empty
  body on the next page rather than a short page. Treat that as end-of-results.
- The fixed-width-strip seam (`6 X n` etc.) is already harvested by Alois Heinz
  and Seiichi Manyama, with b-files of 200-500 terms. Do not compete there.

## Cross-check verdict (recorded automatically)

a(11) of A290719 is **independently confirmed**: the frontier partition
DP and the exact-support peeling counter, which share no code path beyond
the class grid, agree.

This run compared the two algorithms at:

  - n=10 (black)
  - n=11 (black)

It establishes nothing about the other staged terms, which it did not
cover; each of those rests on whatever verification is recorded for it
separately.

```
n=10 black
  frontier DP : 1090550900687379   [60.6s]
  peeling     : 1090550900687379   [742.6s]
  -> AGREE - independently confirmed
n=11 black
  frontier DP : 2265142469367980614   [1527.2s]
  peeling     : 2265142469367980614   [28482.6s]
  -> AGREE - independently confirmed
CROSSCHECK PASSED
```
