# Hamiltonian paths on the bishop boards — measured plug-DP state growth. **Verdict: not worth pursuing.**

**2026-08-13.** SESSION_HANDOFF records the bishop Hamiltonian-path predicate as
the one unmeasured seam left in this repo, and the standing discipline is to
measure state growth before an engine is built — the discipline that closed the
torus family in `phase2_torus_prototype_result.md`. This is that measurement. It
reaches the same conclusion, by a much wider margin.

Reproduce: `python bench/measure_hamiltonian_growth.py --from-n 4 --to-n 9
--cap-gb 2.5 --budget 600`. Measured on the 15.37 GB Windows box, Python 3.13.14.

## 1. The targets

| sequence | predicate | published to |
|---|---|---|
| A307934 | undirected Hamiltonian paths, black bishop | n=9 |
| A234632 | directed, black bishop | n=9 |
| A308146 | undirected, white bishop | n=9 |
| A234637 | directed, white bishop | n=9 |

The directed terms are exactly twice the undirected ones at every published n
(checked, all 16 pairs), so ONE counter feeds all four sequences. That is what
makes the seam look attractive: four entries per term computed, and the first
term nobody has is n=10.

Published reach here is read from the committed DATA snapshot in
`data/targets.json`. `tools/probe_upstream_bfiles.py` was deliberately not run
for these four, because it rewrites a tracked file and this work was scoped to
add files only. That does not move the verdict: an upstream b-file reaching
further would only push the first unpublished term further out, and the finding
below is that n=10 is already out of reach by three orders of magnitude.

## 2. What was built

`bench/measure_hamiltonian_growth.py`: the plug DP with matching states over the
rook structure that section 5.3 of the design spec names and nobody implemented.

The single-colour bishop graph is a rook graph on the class grid, so x-classes
and y-classes are CLIQUES. Cells are swept row by row. Each cell has exactly two
slots, and when it is swept both are committed: matched to an open end waiting in
its column, matched to an open end waiting in its row, left open for a later row,
left open for a later cell of the same row, or left unused, which makes that cell
one of the path's two endpoints. Every edge is committed once, at whichever end
is swept later, so no path is counted twice.

The state is the set of path fragments built so far, each recorded only as its
two ends — TERMINAL, open-in-this-row, or the column it waits in. Which row an
open end came from cannot matter, because a class is a clique. One extra bit says
whether a fragment is a single cell, because a single cell offering two ends
offers one vertex twice while a longer fragment offers two distinct extremities.

**It counts as well as measures, on purpose.** A state-space measurement of a DP
that computes the wrong thing measures nothing. This one reproduces **every
published term it can reach — n=2..7 on both boards, twelve terms** — and at even
n the black and white boards produce byte-identical state profiles, which is the
reflection isomorphism the repo already relies on, arriving here for free.

## 3. The measurement

Caps: 2.5 GB working set, 600 s per n. A cap hit is a data point and is recorded
as one.

| n | board | cells | peak states | peak GB | secs | outcome |
|---|---|---|---|---|---|---|
| 4 | black | 8 | 78 | 0.03 | 0.00 | 96, matches published |
| 4 | white | 8 | 78 | 0.03 | 0.00 | 96, matches published |
| 5 | black | 13 | 2,431 | 0.03 | 0.05 | 25376, matches published |
| 5 | white | 12 | 1,186 | 0.03 | 0.03 | 12256, matches published |
| 6 | black | 18 | 45,399 | 0.04 | 1.62 | 32132352, matches published |
| 6 | white | 18 | 45,399 | 0.04 | 1.96 | 32132352, matches published |
| 7 | black | 25 | 3,196,491 | 1.36 | 273.4 | 1295557991168, matches published |
| 7 | white | 24 | 1,942,555 | 0.83 | 245.0 | 392007078912, matches published |
| 8 | black | 32 | > 4,717,390 | 2.50 | 220.4 | **MEMORY CAP, cell 13 of 32** |
| 8 | white | 32 | > 4,193,649 | 2.50 | 204.4 | **MEMORY CAP, cell 13 of 32** |
| 9 | black | 41 | > 4,193,649 | 2.50 | 214.3 | **MEMORY CAP, cell 13 of 41** |
| 9 | white | 40 | > 2,827,094 | 2.51 | 95.4 | **MEMORY CAP, cell 14 of 40** |

n=2 and n=3 also reproduce (`--from-n 2`); they are omitted only to keep the
table to one command's output.

Two things to read carefully in that table. **Memory is the wall, not time** —
every failure is a memory cap, reached in 95-220 s of a 600 s budget, which is
what SESSION_HANDOFF already says about this machine. And the cap-hit counts are
not state-space measurements: n=8 white and n=9 black both died at exactly
4,193,649 states because that is where a Python dict last doubled below 2^22, so
those numbers say where the run died, not how big the state space is. The true
peaks for n>=8 are far above them — n=8 died at cell 13 of 32, before the first
of the two widest rows was even finished, whereas the n=7 peak sat at cell 13 of
25, halfway.

## 4. Growth, and what it projects to

Per-step growth in peak states:

    black   x31.2 (4->5)   x18.7 (5->6)   x70.4 (6->7)
    white   x15.2 (4->5)   x38.3 (5->6)   x42.8 (6->7)

The frontier width alternates with parity — even n gives an n X (n-1) class grid,
odd n an n X n one — so the like-for-like comparison is two steps at a time:

    even  n=4 -> n=6    x582     (x24.1 per step)
    odd   n=5 -> n=7    x1315    (x36.3 per step)

Measured cost per live state: **457 bytes** (black n=7: 1.36 GB / 3,196,491) and
459 bytes (white n=7). So the capacity of this machine, in states:

    2.5 GB  (this measurement's cap)      5.9 M
    4.4 GB  (the CDS wall, measured)     10.3 M
    5.6 GB  (the domination wall)        13.2 M
    15.37 GB (the entire machine)        36.1 M

And the projection, at the measured x24 per step:

    n=8    26 M states      11 GB      (77 M / 33 GB at the single-step rate)
    n=9    4.2 G states     1.7 TB
    n=10   15 G states      6.4 TB     <- the first term nobody has

## 5. Why that kills it

**Zero new terms.** The first unpublished term is n=10 and it projects to 6.4 TB
of live state, about 426x the whole machine and 1,169x its practical ceiling.
Even n=8, which is published and therefore worthless, is 2x to 6x past that
ceiling. The DP dies three full steps short of contributing anything.

The reason is the sharp rule this repo already found and wrote down: predicates
needing only *occupancy* of a class collapse under the bishop-to-rook reduction;
predicates needing class *populations* do not. Hamiltonicity is the extreme end of
that rule — it constrains the DEGREE of every individual cell, so the class
collapse, which is the entire reason the bishop family was cheap, buys almost
nothing here. Concretely, the connected-subgraph DP's frontier state is a
partition of at most n classes; this frontier state is a matching over open
half-edges whose count is bounded not by the frontier width but by the remaining
capacity of each column, which is Theta(n^2) in the middle of the board.
Partitions of n things against matchings over Theta(n^2) half-edges is the whole
difference, and it is structural rather than an implementation detail.

The comparison that makes it vivid: the connected-subgraph frontier DP — the
engine that produced this repo's ten approved terms — held 1,343,614 states at
**n=11**. The Hamiltonian plug DP passes that at **n=7**. It starts four steps
behind and then grows ten to thirty times faster per step.

## 6. The honest caveat — this is a floor, not a ceiling

This is one formulation in unpacked Python: a dict from a tuple of end-pairs to a
Python int, at 457 bytes per state. The obvious objection is that a better
implementation would go further, and the repo has already measured what that is
worth. Packing the connected-dominating state into a `bytes` key cut it from 556
to 49 bytes — 11x — and still did not reach n=11. Packing the domination state
into one integer bought exactly one step, because growth there is 2.2x per step
and 2-3x of memory moves the wall once.

Here growth is 24-36x per step. **An 11x memory win does not buy one whole step.**
A different sweep order, a tighter invariant or a C rewrite each shave a constant;
the deficit to the first new term is a factor of about 10^3 in memory after the
projection above. Nothing representational covers that.

So the claim is not "this is impossible". It is: measured, the plug-DP route named
in section 5.3 is not the way in, and no amount of tuning it changes that. A new
term would need a different algorithm — a closed form, or a transfer matrix over a
far coarser invariant. Nothing here says one exists. The committed snapshot keeps
only names, offsets, keywords and terms, so this note makes no claim about what
those four entries contain; what it can say is that all four carry `more`, the two
undirected ones carry `hard`, and the design spec's sampled check of this seam
found 0 of 6 entries carrying any program, formula or comment.

## 7. Recommendation

**Close the Hamiltonian seam.** Do not build the counting engine. There is no
partial win to bank: a 32-64 GB machine could plausibly finish n=8, and n=8 has
been published since 2019.

With this measured, every predicate this repo opened on the bishop family is now
either landed (connected subgraphs, domination, connected domination — ten terms
approved on 2026-08-13) or measured to death and written down (total domination in
PAPER.md, the torus family in `phase2_torus_prototype_result.md`, Hamiltonian
paths here). Phase 1 has nothing computational left in it.
