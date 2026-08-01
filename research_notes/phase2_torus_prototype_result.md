# Phase 2 measured prototype — the torus family. **Verdict: not worth pursuing.**

**2026-08-01.** The Phase 2 spec said the torus family should be opened only as a
measured prototype, allowed to conclude "not worth it". This is that measurement,
and that is the conclusion.

Reproduce: `graphrecords/torus_profile.py`, validated against
`graphrecords/torus.py`'s brute force.

## 1. What was built

A broken-profile sweep over the n X n torus grid graph counting **plain dominating
sets** — deliberately the cheapest predicate available. Phase 1 established that
occupancy-only predicates collapse and population/privacy predicates do not, so
the cheapest one bounds what any richer predicate can achieve.

Validated exactly against brute force where both are feasible:

    n=3   421          brute 421          ok
    n=4   45707        brute 45707        ok

## 2. The measurement

| n | dominating sets | peak states | seconds | step growth |
|---|---|---|---|---|
| 3 | 421 | 57 | 0.00 | |
| 4 | 45707 | 479 | 0.00 | |
| 5 | 18935741 | 2,656 | 0.03 | |
| 6 | 30147126791 | 12,736 | 0.46 | x15.8 |
| 7 | 183429997068809 | 61,312 | 14.03 | x30.4 |

Growth is **x15 rising to x30 per step** and accelerating. Projected: n=8 about
7 minutes, n=9 about 3.5 hours, n=10 several days.

## 3. Why that kills it

**The cheapest predicate has no OEIS entry.** There is no "dominating sets in the
n X n torus grid graph" sequence. Every torus target that exists needs a *richer*
predicate:

| sequence | predicate | published to |
|---|---|---|
| A347723 | irredundant sets | n=6 |
| A295428 | minimal dominating sets | n=7 |
| A298106 | connected dominating sets | n=7 |
| A348000 | minimal total dominating sets | n=7 |
| A382530 | minimum connected dominating sets | n=7 |
| A298124 | connected induced subgraphs | n=8 |
| A303210 | total dominating sets | n=8 |

Phase 1 measured what those predicates cost: total domination needs 6 states per
class where plain domination needs 2, and privacy predicates (minimal, irredundant)
need more still. On a base already growing x30 per step, paying 3-6x more state
per class costs **one to two whole steps of reach**.

So the arithmetic is: the cheapest predicate reaches n=8 comfortably and n=9 with
hours. The predicates that actually have entries cost 1-2 steps more, and their
entries already stand at n=7-8. **The expected yield is zero to one term, for
hours of compute each.**

## 4. The honest caveat — this is a floor, not a ceiling

This prototype is not optimal. The torus penalty here is a `2^n` outer loop over
row 0's mask, which a transfer-matrix trace formulation would remove. That could
plausibly buy back roughly one step. Even so, one step against a 1-2 step deficit
leaves the margin at best marginal, and the compute per term still runs to hours.

The claim is therefore **not** "this is impossible". It is: **measured, the
expected return does not justify the work**, and a better implementation would
have to beat the deficit before it produced a single new term.

## 5. Recommendation

**Close the torus family. Do not open the other Phase 2 families on the strength
of the spec alone** — the same discipline applies. The spec already records that
93 of the 230 `keyword:more` targets are knight graphs (bandwidth 2n+1, so a
squared profile), that the easy grid-domination wins are already computed, and
that several tempting 3-term entries are 3-D grids. Each of those should get its
own cheap measurement before any engine is built for it.

Phase 1 succeeded because the bishop graph *is* a rook graph, and that gift does
not recur. This measurement is what that looks like when it is absent.
