# GraphRecords — extending five OEIS bishop-graph sequences

Phase 1 complete; nothing submitted. Written retrospectively, from the code.
Where this document and the code disagree, the code wins and this document is
wrong. Technical design: [TDD](TDD.md).

## Static since 2017, and a fact nobody was using

The OEIS entries counting structures in the n X n bishop graph have not moved
since 2017. A290719, A290769 and A291595 (connected induced subgraphs) stop at
n=9; A289145 and A289169 (connected dominating sets) stop at n=8. None of the
five carries a program, a formula or a comment — each links only to MathWorld —
so there is no published method, and anyone wanting the next term starts from
nothing.

The counts are astronomically large (a(11) has 19 digits), so enumerating all
`2^60` cell subsets is not merely slow, it is impossible. That is presumably why
the entries stalled where they did.

The specific thing that was wrong: an exploitable structural fact about these
graphs — that a single-colour bishop graph *is* a rook graph in rotated
coordinates — was not being used by anybody, and it turns an intractable subset
count into a sweep over `O(n)` classes per side.

## The mistake that nearly happened

Three sequences were staged as contributions after reading the OEIS **DATA line**
as the term count. Their b-files already reached n=50.

The DATA line truncates near 260 characters. Reading it as the extent of what is
published cost a day and three sequences' worth of compute, and it would have put
an EXTENSIONS line on the record claiming credit for terms another author had
already published.

It is mechanical now. `tools/probe_upstream_bfiles.py` records the true published
extent, two tests refuse to let a staged file or an EXTENSIONS line over-claim,
and "could not tell" is never treated as "nothing is published".

## Requirements

**Must**

- Reproduce all published terms before extending anything, and on any
  disagreement abort and stage nothing. A disagreement means the algorithm is
  wrong, never that OEIS is.
- Index every comparison by true `n`. Offsets are not uniform in this family:
  A290719 starts at n=1 and A290769 at n=2, because a 1 X 1 board has no white
  cells.
- Exact integer arithmetic throughout. Counts exceed 64 bits at n=10, so Python
  ints only, never a fixed-width accumulator.
- b-files satisfying the OEIS spec byte for byte: LF only, no BOM, ASCII,
  trailing newline, first index equal to the sequence offset, no gaps.
- Independent confirmation for staged terms wherever brute force cannot reach — a
  second algorithm sharing no code path beyond the class grid, or a structural
  identity verified against published data.
- The tool must never submit. Preparation is automated; the paste is manual.

**Should**

- Survive an unattended overnight run without taking the machine down with it:
  memory guard, measured budgets, serial execution.
- Record negative results — predicates and graph families where the method
  provably does not pay — rather than quietly dropping them.

## Where it stops

**Submitting to OEIS.** The repository stages files into `OEIS-upload/` and stops.
Nothing is submitted automatically and no OEIS account credential is in the
repository, not ever. Submission is the operator's act from the operator's own
account, one sequence at a time, each explicitly authorised. Eight b-files
arriving at once from a new contributor is exactly the editor friction to avoid.

**n=12 for connected subgraphs.** Not attempted. States grow 2.5x to 15x per
step and n=12 needs several GB; the honest claim is "+3 to +4 terms per
sequence", not an order of magnitude.

**The fixed-width strip sequences** — `6 X n` bishop strips and similar. A
transfer matrix gives a linear recurrence and thousands of terms there, and those
entries already carry b-files of 200–500 terms from established contributors.
Competing there produces nothing and costs goodwill.

**The minimum-vertex-colouring sequences** A371202, A371203 and A371204. The same
reduction shows these are proper *edge* colourings of the bipartite cell graph,
hence by König that `chi` equals the longest diagonal, and hence that counting
Δ-edge-colourings is the Latin-square counting problem — where only eleven terms
are known to anyone. Understood, verified as far as `chi` and the published
A371202 values, and deliberately not attempted.

**Total domination.** The method reaches n=11 against 16 published terms of
A303145, so it cannot extend its own sequences. Kept in the gate as a correctness
check, never as a contribution.

**Phase 2, the torus and other local board graphs.** Opened as a measured
prototype and closed on the measurement; see the table below. Nothing outside
the bishop is supported — no grid, no king, no knight, no torus.

## Marks of done

- [x] `python verify_all.py` exits 0 from a **clean clone with no local state**,
      verified 2026-08-01: 189 gate checks plus 301 tests, and 372 tests as of
      2026-08-03.
- [x] Every published term of every target sequence is reproduced exactly,
      indexed by that sequence's **true offset** rather than by list position.
- [x] New terms exist and are staged: ten terms across five sequences.
- [x] Each staged term's confidence is recorded **per term** rather than in
      aggregate. "Confirmed by a second algorithm" and "confirmed by a structural
      identity" are stated separately, and neither is called the other.
- [x] A staged file cannot be counted as a contribution unless it provably goes
      beyond the **published b-file**, enforced by a test rather than by memory.
- [x] An EXTENSIONS line cannot claim a term somebody else already published,
      enforced by a test on the generated submission pack.
- [ ] Terms accepted into OEIS. **Deliberately not achieved yet** — this queues
      behind an unrelated submission, and each paste needs its own authorisation.

## Three readers

**The operator**, who wants to make a genuine, checkable contribution to a public
mathematical reference under their own OEIS account, without ever submitting a
term they cannot defend to an editor.

**An OEIS editor**, who will see a b-file and an EXTENSIONS line and must decide
whether to trust it. Editors do not re-run code; they judge whether the claim is
stated honestly and whether the author knows the failure modes of their own
method.

**A future maintainer** — realistically the same person months later, or an agent
picking the repo up cold — who needs to know what has been proved, what has
merely been computed, and what has been measured and abandoned.

Not for general graph-theory users. This is not a library anyone else installs.

## One personal datum, and no undo

No third-party personal data at all: no user accounts, no network service, no
database, no input from anyone. The only network traffic is an outbound read of
public `oeis.org` b-files, rate-limited to one request per 0.4 s.

The one personal datum is the operator's own name. An accepted OEIS entry carries
the contributor's real name permanently and publicly. That is why the repository
is private, why no GitHub link goes into any entry — it would couple the legal
name to the anonymous handle — and why submission is manual: it is the one
irreversible, identity-attaching step in the whole workflow.

Revocation has no analogue here, and that is precisely the risk. There is no
access to revoke, and there is also no undo. An accepted OEIS entry cannot be
retracted the way a deploy can be rolled back, and a wrong term corrupts a public
reference work other people will cite. Everything upstream of the paste is
therefore designed to fail closed, and the paste itself is gated on a human.

Worst outcomes, in order of severity. A false term enters OEIS — mitigated by
five verification levels, two independent algorithms, and structural identities
checked against every published term. An EXTENSIONS line claims credit for terms
another author already published — the near-miss described above, now mechanical.
An overnight job pages the machine into a freeze — mitigated by an in-process
memory guard that terminates its own process on a free-RAM breach.

## Closed on the measurement, not the argument

| What was tried | What the measurement said |
|---|---|
| **Brute force over cell subsets** | `2^50` at n=10. Kept as the L0/L1 reference for n<=6, where it is the only thing that can independently establish correctness at all. |
| **Exact-support peeling as the production counter** | Correct and genuinely independent, but ~`9^n`: 510.7 s at n=10 where the frontier DP takes 53.5 s, and 28,482 s at n=11 against 1,527 s. Kept precisely *because* it is slow and independent — it is the cross-check, not the engine. |
| **Packing `connected_domination.py` into one integer**, as `domination.py` was | Measured three encodings first. The integer is marginally smaller than `bytes`, but this sweep rebuilds a labels list per transition, so it paid in hand-rolled shift loops and ran 2x slower. `bytes` keeps ~11x of the memory saving at 6x the unpack speed. Memory was the wall; paying 2x in time to fix it was a bad trade. |
| **Chasing n=12 for connected subgraphs** | State growth is doubly exponential in the counts and ~2.2x per step in the states. Packing `domination.py` bought exactly one term (n=20 → n=21), as predicted. A 2–3x memory saving moves the wall one step and no further; that is arithmetic, not pessimism. |
| **Phase 2: the torus family** | Prototyped and measured rather than argued about. The *cheapest* predicate (plain domination) grows x15 rising to x30 per step and has no OEIS entry at all; every torus entry that exists needs a richer predicate costing 1–2 further steps of reach, against entries already standing at n=7–8. Expected yield: zero to one term for hours of compute each. Recorded in `research_notes/phase2_torus_prototype_result.md`, including the honest caveat that a transfer-matrix formulation could buy back roughly one step and still not close the deficit. |
| **An external RAM watchdog alone** (`tools/ram_guard.ps1`) | It has to be handed a PID, and capturing that PID races the process it protects; twice it silently failed to arm while a job climbed to 4.4 GB. A guard that is only *usually* armed is not a guard. Replaced by an in-process guard that cannot fail to arm. The external one also had to learn to require free RAM low **and** the target itself large — the first version killed a job holding 0.86 GB while the 4.58 GB hog survived. |
| **Trusting the OEIS DATA line as the term count** | It truncates near 260 characters. This is the near-miss above; now a test. |

## One live dependency, and it is social

Nothing is blocking. The submission queue is deliberately serialised behind an
unrelated OEIS draft, and the first paste should be followed by asking an editor
how they would like the remaining four handled.
