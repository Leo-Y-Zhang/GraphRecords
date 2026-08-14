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

All ten were submitted to OEIS and **approved on 2026-08-13**, every sequence the
same day. The "published to" column above is therefore the reach each entry had
*before* this work; all five now publish through the "now to" column, and
`data/upstream_bfiles.json` holds the probe that measured it afterwards.

### A correction, and the process fix it forced

The dominating-set sequences A289164, A289170 and A295898 were also computed here,
to n=21, and are **not** contributions: their published b-files already reach
n=50. OEIS truncates the DATA line near 260 characters, so those entries *display*
12 to 15 terms while holding 50. The bishop shortlist was checked for exactly this;
the domination sequences were picked up later from a grouped listing and were not.

The check is now mechanical rather than remembered: `tools/probe_upstream_bfiles.py`
records how far every published b-file goes and what it holds, and a test refuses
to let a staged file count as a contribution unless it exceeds that — and, once a
submission is approved, holds the same file to matching what OEIS serves, term for
term. Reading the DATA line as the term count is the single easiest way to waste a
day on this kind of work.

**What that computation did buy:** every one of the twenty overlapping terms
agrees with the published b-file exactly, including a(20) at 61 digits and a(21)
at 67. Someone reached n=50 in 2017 by an undisclosed method and we agree
throughout, which is far stronger evidence for the engine than the fifteen DATA
terms it was originally checked against.

*Precisely, because an earlier wording here overstated it:* that b-file is
independent of **this work** — a different method, computed years before this
repo existed, sharing no code with it — but not by a different **author**. Every
bishop and honeycomb sequence used here, target and anchor alike, was submitted
by Eric W. Weisstein. Calling it "an independent author" was wrong and is
corrected rather than quietly dropped, since the whole value of an anchor is
knowing exactly what it is independent of.

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
  the class grid, agree for n=1..8 in both colours — for connected subgraphs, and
  since 2026-08-01 for connected dominating sets as well.
- **L4** Structural identities that follow from the problem rather than the code:
  the two components give `black(n) + white(n) = bishop(n)` against all 9 published
  terms of A291595; reflection makes the colour classes congruent for even n, so
  `black(n) = white(n)` there; and they must differ for odd n.

### Confidence, stated per term rather than in aggregate

An earlier draft of the automation was going to record "every staged term now
rests on two independent algorithms". **That would have been false**, and it is
worth saying why: the peeling cross-check covers two terms of ONE sequence, while
the ten terms span five. Aggregate confidence claims hide exactly this.

| term(s) | rests on | independent second algorithm? |
|---|---|---|
| A290719 a(10) | peeling + frontier(black) + frontier(white), which must agree at even n | **yes, three ways** |
| A290769 a(10) | same value as A290719 a(10) by the even-n reflection isomorphism | **yes**, inherited |
| A290719 a(11) | frontier DP **and the peeling counter**, which agree (7.9 h for the peeling half) | **yes** — cross-check completed 2026-08-01 |
| A290769 a(11) | frontier DP **and the peeling counter**, which agree (670 s vs 2737 s) | **yes** — cross-check completed 2026-08-01 |
| A291595 a(10) | derived as black + white; the identity is verified against all 9 published terms | inherits — **both parents confirmed** |
| A291595 a(11) | as above | inherits — **both parents confirmed** |
| A289145, A289169 a(9) | frontier DP **and the CDS peeling counter**, which agree | **yes** — cross-check completed 2026-08-01 |
| A289145, A289169 a(10) | as above, and the two boards return the identical value as the even-n isomorphism requires | **yes** — cross-check completed 2026-08-01 |

**Seven of the ten new terms now carry genuine independent confirmation.** The
four connected-dominating-set terms were the largest block resting on a single
algorithm, and they no longer do. `cds_peeling.py` counts the same sets by
exact-support inclusion-exclusion, sharing no code path with the frontier DP
beyond the class grid — and in particular nothing with that DP's requirement-mask
bookkeeping, which is its subtlest part and the likeliest place for an error to
survive the tests. Domination enters it as a predicate on the support, which is
sound because a cell's closed neighbourhood in a rook graph is its whole x-class
together with its whole y-class, so whether a set dominates depends only on which
classes it occupies.

| cross-check | frontier DP | peeling | agreed value |
|---|---:|---:|---|
| A289145 a(9), black | 8.0 s | 147.0 s | 2014079802496 |
| A289169 a(9), white | 2.6 s | 10.6 s | 1011850062768 |
| A289169 a(10), white | 67.8 s | 559.0 s | 1073633875253120 |
| A289145 a(10), black | 28.1 s | 528.7 s | 1073633875253120 |

The two n=10 values are equal, which the even-n reflection isomorphism requires
and which two independent algorithms now both produce.

**Every one of the ten new terms now carries independent confirmation.** The
last gap closed 2026-08-01 16:27: the peeling counter on the white board at n=11
returned `1134335726831043925`, agreeing with the frontier DP (670 s vs 2737 s).
That confirms A290769 a(11) directly and A291595 a(11) by the addition identity,
whose two parents are now both confirmed.

Stated precisely, because the distinction is the point of this section: seven
terms are confirmed by a **second algorithm** sharing no code path beyond the
class grid, and three by a **structural identity** — the even-n reflection
isomorphism for A290769 a(10), and `black + white = bishop` for A291595 a(10) and
a(11) — each verified against every published term of the sequence it governs.
Neither kind is a re-run of the same code.

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

## 6. A second board: the triangular honeycomb

The same reduction reaches a different board, and this time no new counter was
written at all.

A cell of the n-triangular honeycomb board is barycentric `(x, y, z)` with
`x + y + z = n - 1` and all three non-negative, so there are `n(n+1)/2` of them.
The triangular grid offers three line families, one per coordinate; a bishop
uses the two at +/-60 degrees, which are the constant-`x` and constant-`y`
families. The horizontal family (constant `z`) is a rook move here, not a
bishop's.

**No phi is needed.** Since `z` is determined by `x` and `y`, the cell *is* its
`(x, y)` pair, and "agrees in x or agrees in y" is already rook adjacency. The
honeycomb bishop graph is therefore the rook graph on the **staircase**
`S_n = {(x, y) : x, y >= 0, x + y <= n - 1}` — where the square board gave a
diamond, this board gives a triangle. Which two of the three families the bishop
uses does not matter: the cell set is symmetric under permuting the coordinates,
so all three choices give the same graph relabelled, and the suite measures that
rather than assuming it.

Unlike the square board this graph is **connected** — one component, no colour
split — so `black + white = bishop` has no analogue here and something else has
to take its place. Two things do: the containment inequalities in the gate, and
the anchor below.

### The y-class order is worth 16x

Every counter here sweeps the x-classes and prunes on the fact that each meets a
*contiguous* y-interval: once no later x-class can reach a y-class it is
finalised, states merge, and a block confined to the finalised region is dropped.

In the natural y-order, x-class `i` of the staircase meets y-classes `0..n-1-i`.
**Every interval starts at 0.** Nothing is ever finalised, and not one of those
prunings can fire. Reversing the y-order makes x-class `i` meet exactly
`i..n-1`, so each step finalises one more y-class. Measured at n=9:

| sweep | natural y-order | reversed y-order |
|---|---:|---:|
| connected induced subgraphs | 115,974 states, 14.5 s | 33,817 states, 6.8 s |
| connected dominating sets | 839,563 states, 26.3 s | 51,405 states, 2.8 s |

Reversal only renames y-classes, so it is a graph isomorphism and cannot change
a count — both orders return the identical value at every n measured, which is
asserted in the suite alongside the interval shape. It is recorded here because
it is the whole difference between reaching n=10 and not: a 16x state saving
bought entirely by choosing which end to sweep from.

### Four new terms

| sequence | counts | published to | now to | new |
|---|---|---|---|---|
| A290783 | connected induced subgraphs, honeycomb | n=9 | n=10 | +1 |
| A381795 | connected dominating sets, honeycomb | n=7 | n=10 | +3 |

    A290783  a(10) = 35157891412269342
    A381795  a(8)  = 60874901280
    A381795  a(9)  = 32870948178528
    A381795  a(10) = 34698803291940384

Measured against each entry's **published b-file**, refreshed by
`tools/probe_upstream_bfiles.py` on the day of the run: A290783 reaches n=9 and
A381795 reaches n=7. Neither has been submitted.

| n | A290783 states | secs | peak MB | A381795 states | secs | peak MB |
|---|---:|---:|---:|---:|---:|---:|
| 8 | 6,846 | 0.6 | 30 | 8,856 | 0.3 | 34 |
| 9 | 33,817 | 6.3 | 38 | 51,405 | 2.5 | 73 |
| 10 | 202,505 | 66.9 | 88 | 286,463 | 21.7 | 231 |

### The anchor, which is worth more than the DATA lines

`A290941` counts **dominating sets of this same honeycomb graph**, and a b-file
for it was published in 2017 reaching **n=50**. The domination engine, fed the
same staircase the new terms come from, reproduces it for **n=1..20** — a
61-digit agreement at n=20, reached by two methods with no shared code.

It is independent of *this work*, not of the *author*: A290941, A304553, A290783
and A381795 were all submitted by Eric W. Weisstein. What the anchor rules out is
an error in this repo's grid or engines, which is exactly what it is being asked
to rule out; it cannot rule out a shared misunderstanding of the board, and that
is left to the definition itself, checked pairwise against barycentric
coordinates for n=1..7.

Brute force over all subsets dies at n=6. So this single check validates the
class grid roughly fourteen steps past anything exhaustive enumeration can see,
and far past the nine and seven published terms of the target sequences. It is
the strongest evidence in this repo that the staircase is the right graph, and
it is the reason the honeycomb work needed no new counter to be believed.

`A290941` and `A304553` are **anchors only, never contributions** — both are
already published to n=50. This is the A289164/A295898 mistake from the square
board, and it is now prevented mechanically rather than remembered: the probe
records upstream extent for the targets on every run, and the gate fails if a
claimed term is not strictly beyond it.

### Confidence, stated per term

| term | rests on | independent second algorithm? |
|---|---|---|
| A381795 a(8) | frontier CDS sweep **and** the exact-support peeling counter, 11.7 s, re-run by the gate on every run | **yes** |
| A381795 a(9) | the same two, 145.6 s for the peeling half | **yes** — measured, too slow to re-run every time |
| A381795 a(10) | the frontier CDS sweep **only** | **no** — the peeling half is roughly a 30 min run and has not been done |
| A290783 a(10) | the frontier connectivity sweep **only** | **no** — same reason |

The two n=10 terms are the honest gap, and they are not being rounded up. What
they do carry: every published term of their own sequence reproduced, the n=20
anchor underneath the grid they share, and the containment inequalities
`cds(n) <= connected(n)` and `cds(n) <= dominating(n)`, which relate three
engines that share no counting logic and which both n=10 values satisfy. That is
real evidence and it is not a second algorithm. To close the gap:

    python bench/measure_honeycomb.py cds-peel 10 --start 10
    python bench/measure_honeycomb.py cis-peel 10 --start 10

## 7. Honest limits

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
