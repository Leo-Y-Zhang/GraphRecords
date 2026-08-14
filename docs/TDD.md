# GraphRecords — the bishop-to-rook engine as built

Phase 1 complete. Derived from the code, not from the README. This is an offline
computation with no server, no database and no authenticated surface; what it
does have is a **publication** trust boundary. Requirements: [PRD.md](PRD.md).

## A bishop graph is a rook graph

A bishop never changes the parity of `row + col`, so the n X n bishop graph is
the disjoint union of two components, one per colour. On a single colour the map

    phi(r, c) = ((r + c) // 2, (r - c + n) // 2)

is injective, and it sends "shares an anti-diagonal" to "agrees in x" and "shares
a main diagonal" to "agrees in y". So the single-colour bishop graph **is** the
rook graph on the image cells. That is the whole engine; everything else is a
consequence.

Two consequences do the work.

**Connectivity collapses.** All cells sharing a class are mutually adjacent, so a
cell subset is connected in the rook graph if and only if the bipartite graph it
induces between x-classes and y-classes is connected. Counting moves from
`O(2^|cells|)` to a sweep over `O(n)` classes per side.

**Domination collapses.** A cell's closed neighbourhood is the *whole* of its
x-class together with the *whole* of its y-class, so a set dominates if and only
if its `(x-support, y-support)` is a vertex cover of the cell bipartite graph.
Domination depends only on which classes are touched, never on how many cells are
used inside them.

## The rule that came out of it

The most transferable result in the repository, and the thing to carry to any
other board graph:

**Predicates that depend only on which classes are occupied collapse. Predicates
that need class populations do not.**

Total domination uses the open neighbourhood, so a chosen cell does not cover
itself and the sweep must distinguish "one cell here" from "two or more". That
single extra level costs seven terms of reach — n=18 down to n=11.

## Module map

| Module | Role |
|---|---|
| `graphrecords/boards.py` | Cell sets by colour, explicit bishop adjacency, adjacency bitmasks. The definitional layer everything else is checked against. |
| `graphrecords/reduction.py` | `phi`, an exhaustive self-check of the theorem, and `class_grid`. |
| `graphrecords/brute.py` | Exhaustive reference counters (verification level L0/L1). Correct by construction, useless beyond n=6. |
| `graphrecords/connected.py` | Two independent connected-subgraph counters: exact-support peeling, and the frontier partition DP used in production. |
| `graphrecords/domination.py` | Dominating sets (packed-integer sweep) and total dominating sets (saturating-deficit sweep). |
| `graphrecords/connected_domination.py` | Connected dominating sets — both collapses composed. Production counter for A289145/A289169. |
| `graphrecords/cds_peeling.py` | The independent second algorithm for connected dominating sets. |
| `graphrecords/targets.py` | Offline snapshot of published OEIS terms, keyed by **true n**. |
| `graphrecords/memguard.py` | In-process free-RAM guard for unattended runs. |
| `graphrecords/torus.py`, `torus_profile.py` | Phase 2 prototype and its brute-force reference. Kept as the evidence for a negative result. |
| `verify_all.py` | The gate. Believe it over any prose. |

## The class grid, and the encodings measurement chose

There is no database. What matters is two in-memory encodings chosen by
measurement, plus four persisted artefacts.

`class_grid(n, colour) -> (grid, nx, ny)`. Because `phi` is injective, each
(x-class, y-class) pair holds **at most one cell**, so the grid is 0/1. Every
downstream counter relies on that, so the gate asserts it independently for
n=1..12 in both colours rather than trusting the proof.

Each x-class meets a **contiguous** y-interval. That single fact is what all the
pruning rests on: once no later x-class can reach a y-class, that y-class is
finalised, and any state carrying a block or a requirement confined to the
finalised region is dead and can be dropped. The tests assert contiguity in both
directions, because the transposed sweep would be unsound otherwise.

| Counter | State | Why this encoding |
|---|---|---|
| `domination.py` | one Python int: bits `0..ny-1` hit mask, `ny..2ny-1` requirement mask, bit `2ny` "this x-class placed something" (transient) | A two-element tuple key costs ~60 bytes of object overhead on top of the ints it holds. At n=21 that overhead *was* the 5.6 GB that got the run killed. Packing gave identical state counts, all 15 published terms still reproduced, n=18 from 46.7 s to 34.6 s, and n=21 completing at ~4.35 GB in 617 s. |
| `connected_domination.py` | `bytes`: `key[0:ny]` block label per y-class (0 = untouched), `key[ny:ny+4]` requirement mask little-endian, `key[ny+4]` the block this x-class is building | Measured on a 12-y-class state: tuple+int ~556 B; packed int ~36 B, 0.493 us to unpack; `bytes` ~49 B, 0.079 us. The int is marginally smaller, but this sweep rebuilds a labels *list* every transition, so it paid in hand-rolled shifts and ran 2x slower. `bytes` keeps ~11x of the memory saving at C-speed conversion. |
| `total_dominating_sets` | pair of ints, two-bit saturating fields per y-class: counts, and **deficits** | Storing a deficit rather than a raw requirement merges states: once a class saturates at 2, `(count=2, req=0/1/2)` are three keys that behave identically forever. Per-class combinations drop 9 → 6 and n=10 goes 36 s → 6.6 s. |
| `connected.py` frontier DP | tuple of block labels in restricted-growth canonical form | Never hit a memory wall (peak 1.34M states at n=11); left alone. |

Two "legacy row" cases exist and both reach real runs: `nx == 0 or ny == 0`,
since the white board at n=1 has no cells, and the empty set. The counters
disagree deliberately — `frontier_connected` returns **0** there, because no
non-empty connected subgraph exists, while `dominating_sets` returns **1**,
because the empty set dominates the empty graph. Getting either backwards shifts
a whole sequence by one index, which is why the gate checks against published
data by true `n` and not by position.

## Persisted artefacts

| Path | Written by | Consumed by | Reversible? |
|---|---|---|---|
| `data/targets.json` | `tools/fetch_targets.py` | `graphrecords/targets.py`, the whole gate | Yes — regenerate, or `git revert`. Committed on purpose so the gate runs offline and CI needs no network. |
| `data/upstream_bfiles.json` | `tools/probe_upstream_bfiles.py` | `tests/test_staged_bfiles.py` | Yes, but **must be refreshed before staging anything**; a stale snapshot is how over-claiming happens. |
| `OEIS-upload/b*.txt` | `tools/extend.py`, `tools/extend_cds.py` | `tests/test_staged_bfiles.py`, `tools/build_submission_pack.py` | Yes while unsubmitted. Irreversible the moment one is pasted into OEIS. |
| `data/submission_pack.json` | `tools/build_submission_pack.py` | `tests/test_staged_bfiles.py` | Yes. |

`data/targets.json` stores each sequence's `offset` verbatim, and
`targets.terms_by_n` reads only the first component of it (`"2,1"` → 2). Offsets
are **not** uniform across this family, and nothing may assume otherwise.

## Interfaces

Pure functions, no I/O, no globals, no configuration. Every counter takes
`(n, colour)` where `colour` is `"black"` or `"white"`, and returns an exact
Python int.

```
reduction.rook_coords(n, colour)        -> {(r,c): (x,y)}      raises on "both"
reduction.verify_isomorphism(n, colour) -> None                raises AssertionError
reduction.class_grid(n, colour)         -> (grid, nx, ny)

connected.frontier_connected(n, colour, transpose=False) -> int    production
connected.peeling_connected(n, colour)                   -> int    ~9^n, cross-check
connected.peeling_machinery(n, colour)  -> (nx, ny, ncells, C)

domination.dominating_sets(n, colour)          -> int
domination.total_dominating_sets(n, colour)    -> int
connected_domination.connected_dominating_sets(n, colour) -> int   production
cds_peeling.peeling_connected_dominating(n, colour)       -> int   cross-check

targets.terms_by_n(aid) -> {n: term}     # published data, keyed by TRUE n
memguard.start(floor_gb=1.0, interval=5.0, label="run") -> Thread
```

Two contracts are load-bearing.

`frontier_connected(..., transpose=True)` sweeps the y-classes instead of the
x-classes. That is the *same* bipartite graph seen from the other side, so the
answer must be identical — but the sweep order, the intervals and every pruning
decision differ. A direction-dependent bug in the frontier logic shows up as a
disagreement, at a fraction of the cost of the `9^n` peeling counter.

`peeling_machinery` is exposed rather than kept private, so that `cds_peeling.py`
can reuse the *already cross-checked* peeling path instead of transcribing a
second copy that could drift from it. Its `C(X, Y)` is summed over the dominating
supports, which are exactly those with `ncells(complement X, complement Y) == 0`.

The tools in `tools/` are non-interactive batch scripts — argparse, no prompts,
no stdin. They print a running log and exit with a status; nothing about them is
a user interface.

## Trust boundaries

No authentication, no authorisation, no multi-tenancy, nothing to grant. Three
boundaries exist, and each has a defined failure direction.

**oeis.org, read-only.** `tools/probe_upstream_bfiles.py` and
`tools/build_submission_pack.py` fetch published b-files over HTTPS with a 45 s
timeout and 0.4 s between requests. Both fail **closed**: an HTML body, a rate
limit, a dropped connection or an empty parse is reported as **UNKNOWN, never as
absent**. This is the most important design decision in the repo's plumbing,
because "we could not tell whether anything is published" silently becoming
"nothing is published" is precisely what lets an EXTENSIONS line take credit for
another author's terms. `build_submission_pack.py` raises `SystemExit` rather
than writing a pack it cannot justify.

**b-file bytes.** The OEIS spec requires LF-only ASCII with no BOM and a trailing
newline. A Windows checkout will rewrite these to CRLF and silently violate it,
so `.gitattributes` pins `OEIS-upload/*.txt` to `eol=lf` and
`tests/test_staged_bfiles.py` asserts the bytes. A fresh clone was verified to
still produce LF-only files.

**Publication.** The only irreversible action in the system is a human pasting a
b-file into OEIS. Nothing in this repository can perform it, and there are no
credentials anywhere in it, by design.

There is no schema and nothing to migrate. The nearest equivalent is refreshing
`data/upstream_bfiles.json`, which is additive, idempotent and reversible by
`git revert` — and which carries one rule with the same force as "never edit an
applied migration": **run the probe before staging, never after**, and never
treat a stale snapshot as current.

## What breaks, and how a wrong term is stopped

| What breaks | Who notices | How it is detected | How it is undone |
|---|---|---|---|
| A counter is wrong | Nobody, until a wrong term is published | L1 against brute force (n<=6), L2 against every published term, L3 two independent algorithms (n<=8), L4 structural identities. `extend.py` recomputes all published terms first and **stages nothing** on any disagreement. | Nothing to undo while unsubmitted. |
| A staged term is wrong beyond brute-force reach | Only an editor, or nobody | Second algorithm sharing no code path beyond the class grid; `black(n) == white(n)` at even n by reflection; `A291595 = A290719 + A290769`; `A295898 = A289164 * A289170`. Recorded per term, never aggregated. | Delete the staged file. Irreversible only after submission. |
| Over-claiming: staged file does not actually extend the published b-file | An OEIS editor, publicly | `test_staged_file_actually_extends_the_published_bfile` and `test_extensions_line_claims_only_genuinely_new_terms` | Withdraw before pasting. This has already happened once, caught before submission. |
| Upstream probe cannot reach OEIS | The author, immediately | Probe prints UNKNOWN and `main()` returns 1; the pack builder raises `SystemExit` | Re-run when the network is available, or `--offline` for a pack with no EXTENSIONS lines. |
| b-files rewritten to CRLF by a Windows checkout | Nobody, until OEIS rejects the file | `.gitattributes` plus a byte-level test | Re-checkout; the test fails first. |
| An overnight run exhausts RAM and freezes the machine | The author, painfully | `memguard.start()` polls free physical RAM from a daemon thread and calls `os._exit(3)` on breach | Nothing to undo — losing the run is the intended outcome. Everything printed before the breach is valid. |
| A term takes longer than the session | The author | `--budget` stops a sequence once a single term exceeds it | Resume at a lower limit. |
| CI verdict changes with no code change | Whoever pushed | Happened: `48d1bf1` linted clean on ruff 0.15.16 and failed with 55 errors on 0.16.1. Fixed by stating the rule set in `ruff.toml` and pinning `ruff==0.16.1` in CI. Bump both together, never just the pin. | Revert the bump. |

`memguard` uses `os._exit` deliberately: a normal exception could be swallowed by
the computation's own error handling, and once memory is that tight there is no
safe work left to do. A poll that cannot read memory is treated as "keep going",
because killing a healthy job on a transient read error is the worse failure.

## Reverting, and why staged files are inert

Code and data revert with `git revert`. There is no deployed surface, no
consumer, and no state outside the repository, so rollback is seconds. Staged
b-files are deleted; they are inert until pasted.

The one irreversible step is submission, and it is outside this system by
construction. An accepted OEIS entry cannot be retracted the way a deploy can be
rolled back, and a wrong term propagates into a public reference other people
cite. That is why the paste is manual, one sequence at a time, each explicitly
authorised, with `verify_all.py` and the upstream probe re-run immediately
before. Accepting that irreversibility is the reason for every fail-closed
decision above.

## The gate, level by level

`python verify_all.py` is the gate and runs pytest as its last check: 189 gate
checks plus 372 tests, exit 0, measured locally 2026-08-03 with the 372 tests
taking 135 s.

| Level | What it would catch |
|---|---|
| **L0** | The reduction theorem, re-derived exhaustively for n=1..12 in both colours: every cell pair checked for agreement between diagonal-sharing and class-sharing, plus injectivity. Also asserts the class grid is 0/1, which three counters silently assume. |
| **L1** | Frontier DP, dominating sets and total dominating sets against brute-force enumeration over all cell subsets, n=1..6, both colours. The only genuinely independent correctness evidence that exists. |
| **L2** | Every published term of A290719, A290769, A289164, A289170 and (to n=9) A303145/A303147, indexed by true offset. An off-by-one in offset handling fails here and nowhere else. |
| **L3** | Frontier DP against the peeling counter, n=1..8, both colours — for connected subgraphs and, since 2026-08-01, connected dominating sets. Shares no code path beyond the class grid. |
| **L4** | Identities that follow from the problem rather than the code: `black + white = bishop` against all 9 published terms of A291595; `black == white` at even n by reflection; and `black * white = bishop` for **dominating** sets against A295898 — connected subgraphs add, dominating sets multiply, and getting the composition rule wrong per predicate fails here. |
| pytest | The support-collapse lemma against brute force before any counter uses it; the transposed sweep agreeing with the forward sweep; contiguity of intervals in both directions; b-file bytes, indices, offsets and unaltered published terms; the anti-over-claiming checks; and the assertion that no full-bishop connected-dominating-set sequence exists, because a connected set lies inside one component and can never dominate the other. |

CI runs the gate, a pinned lint and a gitleaks scan, each with a 20-minute
timeout, on every push and pull request.

## Known limits, stated rather than discovered later

`connected_domination.py` fixes `REQ_WIDTH = 4`, so the requirement mask holds 32
y-classes. The bishop board reaches ny ≈ n, and this counter's practical ceiling
is n=10–11, so the limit is far out of reach — but it is a hard limit rather than
a soft one, and it would raise `OverflowError` rather than return a wrong answer.

Everything here is **verified computation, not proof**. The strongest claim the
repo makes is that two structurally independent algorithms and five levels of
checking agree. Section 6 of `PAPER.md` says so and must not be softened.

The method is specific to bishop graphs, because a bishop graph *is* a rook
graph. That gift does not recur for grid, king, knight or torus graphs, and
`research_notes/phase2_torus_prototype_result.md` is the measurement showing what
happens when it is absent.

## Why there is no App Flow and no Design Brief

This repository ships the PRD and this TDD only. That is a decision, and it
belongs in writing next to the design rather than being left as a gap someone
later mistakes for carelessness.

An App Flow enumerates screens and the transitions between them, and there are no
screens. Everything here is either a pure function taking `(n, colour)` and
returning an exact integer — no I/O, no globals, no configuration — or a batch
script under `tools/` that takes argparse flags, prints a log, and exits with a
status. There is no state a user moves through, no empty state, and no error
state beyond an exception and a non-zero exit. The nearest thing to a flow is the
staging pipeline (`probe_upstream_bfiles.py` → `verify_all.py` → submission
pack), and that is a sequence of commands with a gate, documented where it is run
rather than as a screen flow.

A Design Brief sets visual and interaction intent and an accessibility floor. The
output of this repository is integers and b-files, whose form is fixed by the
OEIS submission format and not open to intent; nothing is rendered and nothing is
looked at while it runs. The one presentation decision that does matter is the
honesty of the claims in `PAPER.md` and the README — that verified computation is
never written up as proof — and that is a constraint on *content*, enforced by
`verify_all.py`, not a design brief.

If a viewer, a plot, or anything a person interacts with is ever added, both
documents get written before that code.

## The order, reference implementations first

1. `boards.py` and `brute.py` — definitions and a reference nothing else may
   contradict.
2. `reduction.py` with `verify_isomorphism` — the theorem, checked exhaustively
   before anything was built on it.
3. `connected.py` peeling counter — correct, slow, independent.
4. `connected.py` frontier DP with stranded-block pruning — the production
   engine.
5. `domination.py` — support-collapse lemma tested against brute force *first*,
   then the sweep. Later repacked into one integer when memory, not time, proved
   to be the wall.
6. `connected_domination.py` — the two collapses composed.
7. `total_dominating_sets` — the negative result, kept because knowing which
   predicates the method fails on is part of the result.
8. `tools/probe_upstream_bfiles.py` and the staging tests — added *after* the
   DATA-line mistake, to make the check mechanical instead of remembered.
9. `cds_peeling.py` — a second algorithm for the four terms that were resting on
   one.
10. `torus_profile.py` — Phase 2 measured, and closed on the measurement.
