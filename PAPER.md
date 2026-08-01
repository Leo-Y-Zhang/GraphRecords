# Connected induced subgraphs of the n X n bishop graph

**2026-07-31** · verify with `python verify_all.py`

## Summary

The n X n bishop graph is a rook graph in rotated coordinates. Using that, this
note extends five OEIS sequences on the bishop graph, untouched since 2017:

| sequence | counts | published to | now to | new |
|---|---|---|---|---|
| A290719 | connected induced subgraphs, black | n=9 | n=11 | +2 |
| A290769 | connected induced subgraphs, white | n=9 | n=11 | +2 |
| A291595 | connected induced subgraphs, bishop | n=9 | n=11 | +2 |
| A289145 | connected dominating sets, black | n=8 | n=10 | +2 |
| A289169 | connected dominating sets, white | n=8 | n=10 | +2 |

Measured against each entry's **published b-file**, not its DATA line — see the
correction below for why that distinction cost a day.

**Ten new terms.** None of these entries carried a program, a formula or a
comment; each linked only to MathWorld. So this also supplies the first published
method.

    A290719  a(10) = 1090550900687379      a(11) = 2265142469367980614
    A290769  a(10) = 1090550900687379      a(11) = 1134335726831043925
    A291595  a(10) = 2181101801374758      a(11) = 3399478196199024539
    A289145  a(9)  = 2014079802496         a(10) = 1073633875253120
    A289169  a(9)  = 1011850062768         a(10) = 1073633875253120

### A correction, and the process fix it forced

The dominating-set sequences A289164, A289170 and A295898 were also computed here,
to n=21, and are **not** contributions: their published b-files already reach
n=50. OEIS truncates the DATA line near 260 characters, so those entries *display*
12 to 15 terms while holding 50. The bishop shortlist was checked for exactly this;
the domination sequences were picked up later from a grouped listing and were not.

The check is now mechanical rather than remembered: `tools/probe_upstream_bfiles.py`
records how far every published b-file goes, and a test refuses to let a staged
file count as a contribution unless it exceeds that. Reading the DATA line as the
term count is the single easiest way to waste a day on this kind of work.

**What that computation did buy:** every one of the twenty overlapping terms
agrees with the published b-file exactly, including a(20) at 61 digits and a(21)
at 67. An independent author reached n=50 by an undisclosed method and we agree
throughout, which is far stronger evidence for the engine than the fifteen DATA
terms it was originally checked against.

## 1. The reduction

**Theorem.** Let `B` be the cells of one colour on the n X n board and define

    phi(r, c) = ((r + c) // 2, (r - c + n) // 2).

Then `phi` is injective on `B`, and distinct cells of `B` share a diagonal if and
only if their images agree in the first coordinate or in the second.

*Proof.* Within one colour `r+c` has fixed parity, hence so does `r-c`. On values
of a single parity both `t -> t // 2` and `t -> (t + n) // 2` are strictly
monotone, therefore injective. Two cells share an anti-diagonal iff `r+c` agrees,
i.e. iff the first coordinates agree; they share a main diagonal iff `r-c` agrees,
i.e. iff the second coordinates agree. Since `(r+c, r-c)` determines `(r, c)`,
`phi` is injective. []

So the single-colour bishop graph **is** the rook graph on the image cells:
adjacent exactly when sharing an x-class or a y-class. A bishop cannot change the
parity of `r+c`, so the full bishop graph is the disjoint union of the black and
white ones and has exactly two components.

The consequence that matters: a cell subset is connected in a rook graph iff the
bipartite graph it induces between x-classes and y-classes is connected, because
all cells sharing a class are mutually adjacent. Counting moves from `O(2^|B|)`
subsets of cells to work over `O(n)` classes per side.

## 2. Two algorithms

**Exact-support peeling** (`peeling_connected`). Let `B(X, Y)` count cell subsets
whose x-support is exactly `X` and y-support exactly `Y`, obtained from
`2^cells(X',Y')` by Mobius inversion over sub-masks, and `C(X, Y)` those that are
also connected. Peeling off the component containing the lowest x-class of `X`:

    C(X,Y) = B(X,Y) - sum over X1 containing lowx, Y1 nonempty, (X1,Y1) != (X,Y)
                         of C(X1,Y1) * B(X \ X1, Y \ Y1)

Cost is about `9^n`. Kept as an independent reference, not for production.

**Frontier partition DP** (`frontier_connected`). Sweep the x-classes carrying a
partition of the y-classes into connected blocks, label 0 meaning untouched. At
each x-class choose a non-empty subset `T` of the y-classes it meets, weighted by
`prod over j in T of (2^grid[i][j] - 1)`, and merge every block meeting `T`.

Each x-class meets a *contiguous* y-interval, so a y-class below every remaining
interval can never be touched again. A block confined to that finalised region can
never merge with anything else, so any state carrying such a stranded block is
dropped. That pruning is what keeps the state count far below the Bell number of
the frontier width.

## 3. Measured cost

Peak live DP states and wall time, black board:

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| states | 2 | 2 | 10 | 11 | 101 | 151 | 1596 | 3136 | 39955 | 86321 | 1343614 |
| secs | 0 | 0 | 0 | 0 | 0 | 0.01 | 0.09 | 0.43 | 9.73 | 53.5 | 1604.7 |

White board: `0, 4, 4, 29, 38, 380, 660, 7529, 15923, 225187, 494815` states, with
n=11 in 691.9 s.

For scale, the peeling counter needs 510.7 s for n=10 where the frontier DP needs
53.5 s, and brute force over all `2^50` subsets is out of reach entirely.

**Ceiling.** States grow by roughly a factor of 2.5 to 15 per step, so n=12 needs
several GB and n=13 is out of reach on this machine. This work adds terms; it does
not add an order of magnitude, because these counts grow doubly exponentially in n
and no algorithm changes that.

## 4. Verification

Five levels, all re-run from cold by `verify_all.py`, plus the pytest suite.

- **L0** The reduction is re-derived exhaustively for n=1..12 in both colours: every
  cell pair is checked for agreement between diagonal-sharing and class-sharing.
- **L1** The frontier DP is checked against brute-force enumeration over all cell
  subsets for n=1..6, both colours.
- **L2** Every published term of A290719 (9) and A290769 (8) is reproduced exactly,
  indexed by each sequence's true offset. Offsets are **not** uniform here:
  A290719 begins at n=1, A290769 at n=2, since a 1 X 1 board has no white cells.
- **L3** The frontier DP and the peeling counter, which share no code path beyond
  the class grid, agree for n=1..8 in both colours.
- **L4** Structural identities that follow from the problem rather than the code:
  the two components give `black(n) + white(n) = bishop(n)` against all 9 published
  terms of A291595; reflection makes the colour classes congruent for even n, so
  `black(n) = white(n)` there; and they must differ for odd n.

### Confidence, stated per term rather than in aggregate

An earlier draft of the automation was going to record "every staged term now
rests on two independent algorithms". **That would have been false**, and it is
worth saying why: the peeling cross-check covers two terms of ONE sequence, while
ten terms are staged across five. Aggregate confidence claims hide exactly this.

| term(s) | rests on | independent second algorithm? |
|---|---|---|
| A290719 a(10) | peeling + frontier(black) + frontier(white), which must agree at even n | **yes, three ways** |
| A290769 a(10) | same value as A290719 a(10) by the even-n reflection isomorphism | **yes**, inherited |
| A290719 a(11) | frontier DP **and the peeling counter**, which agree (7.9 h for the peeling half) | **yes** — cross-check completed 2026-08-01 |
| A290769 a(11) | frontier DP on the white board, plus the same odd-n check. **The cross-check covered BLACK only** | **no** |
| A291595 a(10), a(11) | derived as black + white; the identity is verified against all 9 published terms | inherits the rows above |
| A289145, A289169 a(9) | the composed connectivity+domination DP; brute force to n=6, all published terms to n=8; the two boards differ as odd n requires | **no** |
| A289145, A289169 a(10) | as above, and **the two boards return the identical value**, as the even-n isomorphism requires | partial — same algorithm, independent input |

So: **three terms now carry genuine independent confirmation** — A290719 a(10) (three ways), A290769 a(10) (inherited by the even-n reflection isomorphism) and A290719 a(11) (peeling cross-check, completed 2026-08-01 after 7.9 hours). The remaining seven rest on a single algorithm that has never disagreed with brute force or with published data. That is good evidence. It is not the same thing as independent confirmation, and the two should not be blurred into one sentence.

## 5. A second collapse: domination

In a rook graph the closed neighbourhood of a cell is the **whole** of its
x-class together with the **whole** of its y-class. So a cell is dominated
exactly when its x-class or its y-class contains a chosen cell.

**Lemma.** A cell subset S dominates iff `(x-support(S), y-support(S))` is a
vertex cover of the bipartite graph whose edges are the cells. In particular
domination depends only on which classes S touches, never on which cells it uses
inside them.

Both statements are tested against brute force before use. The sweep then needs
only one bit per live y-class ("has S touched it") plus one requirement bit,
because an x-class left empty forces every y-class it meets to be touched.

Since `phi` is injective, each (x-class, y-class) pair holds at most one cell, so
the class grid is 0/1 and a cell subset is just a subset of occupied grid
positions.

### When the reduction pays, and when it does not

| predicate | what the state must record | states at ceiling | reaches |
|---|---|---|---|
| dominating sets | occupancy, 2 per class | 1125035 | **n = 21** |
| connected induced subgraphs | a partition of the frontier | 1343614 | n = 11 |
| total dominating sets | population capped at 2, 6 per class | 914611 | n = 11 |

The rule is sharp: **predicates that depend only on which classes are occupied
collapse; predicates that need class populations do not.** Total domination uses
the open neighbourhood, so a chosen cell does not cover itself, and the sweep
must distinguish "one chosen cell here" from "two or more". That single extra
level costs seven terms of reach.

Recording a *deficit* rather than a raw requirement matters: once a class
saturates at 2 every requirement on it is already met, so the three states
(count 2, requirement 0/1/2) behave identically forever. Merging them cuts the
per-class combinations from 9 to 6 and n=10 from 36 s to 6.6 s.

**Negative result.** Total domination reaches only n=11 against 16 published
terms of A303145, so this method cannot extend it. Recorded rather than hidden:
the reduction is not a universal win, and knowing which predicates it fails on is
part of the result.

### Composing both collapses

Connected dominating sets need connectivity *and* domination, and the two compose
more cheaply than they should. In the connectivity sweep a y-class carries a
non-zero block label exactly when it holds a chosen cell -- which is precisely
what domination asks. So domination contributes one requirement bit per y-class
rather than a whole extra dimension, and the combined counter still reaches n=10
against 8 published terms.

There is no full-bishop version of that sequence and there cannot be: a connected
set lies inside one component, so it can never dominate the other. OEIS has black
and white variants only, which the test suite asserts.

### Why the colouring sequences are out of reach

A cell is an edge between its x-class and its y-class, and two cells conflict
exactly when they share an endpoint. So **proper vertex colourings of the rook
graph are proper EDGE colourings of the bipartite cell graph**, and by Koenig's
edge colouring theorem the chromatic number is the maximum degree:

    chi(bishop graph) = largest diagonal length

Verified: chi equals the maximum class size for n=1..4, and counting proper
colourings that use exactly chi colours reproduces published A371202
(1, 2, 12, 528).

That reformulation also settles the feasibility question, negatively. Counting
Delta-edge-colourings of a bipartite graph is the same problem as counting Latin
squares in the regular case, where only eleven terms are known to anyone. A sweep
would have to carry the full SET of colours used at each y-class, so the state is
`(2^Delta)^ny` rather than a constant per class. A371202, A371203 and A371204 are
stuck at five or six terms for a real reason, and this reduction does not change
it. They are recorded here as understood, not attempted.

### Composition differs by predicate

The two colour components combine differently depending on the predicate, which
gives independent checks that cost nothing:

- connected subgraphs **add**: a connected subgraph lies in one component, so
  `A291595 = A290719 + A290769`
- dominating sets **multiply**: a set dominates a disjoint union iff it
  dominates each part, so `A295898 = A289164 * A289170`

Both are enforced by the gate against every published term.

## 6. Honest limits

- Nothing here is a proof of the counts; it is verified computation. The strongest
  claim is that two algorithms and five checks agree.
- The method is specific to bishop graphs. Local board graphs (grid, king, knight)
  need a different engine, planned separately.
- The fixed-width strip sequences, where a transfer matrix yields a linear
  recurrence and thousands of terms, are already well covered by Alois P. Heinz
  and Seiichi Manyama; this work deliberately does not compete there.

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
