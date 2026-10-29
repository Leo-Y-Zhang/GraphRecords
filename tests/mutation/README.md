# Mutation-guided regression tests

Production code and CI are unchanged. The existing CI gate already runs
`python verify_all.py`, whose last check runs `python -m pytest -q`.
No behavior-neutral seams or runtime dependencies were needed.

## Measurement

Run `python tests/mutation/run.py --phase both` with pytest installed.
The runner applies **one mutation per fresh interpreter**, in memory, before
pytest imports callers. Production files are never rewritten. It fails the
audit on syntax errors, import/collection errors, empty selections, or timeouts;
only an actual failing test counts as a kill.

These counts use the **fast existing pytest selections listed in `EXISTING`
in run.py**, followed by those same selections plus the new tests. They are a
targeted mutation sample, not exhaustive coverage or a separate full-gate run
for each mutant. The full unmutated suite and gate are checked separately below.
`results.json` records every replacement, verdict, and first failing test.

| Module | Mutants tried | Killed before | Killed after |
| --- | ---: | ---: | ---: |
| `graphrecords/independent_check.py` | 7 | 4 | 7 |
| `graphrecords/reduction.py` | 3 | 2 | 3 |
| `graphrecords/brute.py` | 4 | 0 | 4 |
| `graphrecords/torus.py` | 6 | 1 | 6 |
| `tools/probe_upstream_bfiles.py` | 6 | 0 | 6 |
| `graphrecords/targets.py` | 4 | 3 | 4 |
| `graphrecords/connected.py` | 2 | 2 | 2 |
| `graphrecords/domination.py` | 2 | 1 | 2 |
| **Total** | **34** | **13** | **34** |

The frontier and domination algorithms already have extensive comparison tests.
The useful gaps were certificate boundary conditions, upstream parsing,
previously unused reference counters, and the population-field encoding.

## Tests added and representative kills

- `tests/test_certificate_boundaries.py`: M08 removes the injectivity guard in
  `reduction.verify_isomorphism`. Two adjacent cells on a 2-by-2 board mapped to
  the same image still pass its adjacency comparison; the new collision test
  rejects them. M02 changes exact source coverage in
  `independent_check.check_certificate` to subset coverage; an extra key sharing
  an existing image exposes it. M06/M07 change `coords is None` to `not coords`
  in the bishop/honeycomb wrappers, silently replacing a supplied empty
  certificate with a correct one. Tests also cover valid inputs, missing
  vertices, collisions, wrong target cardinality, and added/deleted adjacency.
- `tests/test_reference_counts.py`: M12 leaves `minimal = True` when a smaller
  dominating subset exists in `brute.minimal_dominating_count`; the hand-counted
  single-edge graph distinguishes two minimal sets from three dominating sets.
  M16 accepts the empty selected graph in `torus._connected`; M19 swaps `and`
  for `or` in `torus.brute_connected_dominating`. A separate set-based oracle
  enumerates just 512 subsets of the 3-by-3 torus for all five counters. M34
  changes `c >= 2` to `c > 2` in `domination._inc2`; explicit packed constants
  expose the broken saturation invariant and check neighboring fields survive.
- `tests/test_upstream_probe.py`: M21 returns absence instead of UNKNOWN on a
  failed fetch in `probe_upstream_bfiles.probe`. M23 skips an incomplete row,
  allowing a truncated response to masquerade as a valid partial file. M25
  changes `max(values)` to `min(values)`, and M26 stops incrementing the row
  count. Every response is supplied through a mocked `urlopen`; no request is
  made. Valid signed/large terms, blank/comment lines, HTML, empty bodies,
  timeouts and 404s are exercised.
- `tests/test_target_indexing.py`: M28 removes integer conversion of b-file
  values in `targets.bfile_terms_by_n`. A tiny synthetic snapshot with string
  indices and signed, arbitrarily large string values catches it. Integer and
  comma-separated offsets, including a negative offset, check true indexing.

## Validation

Re-measured on a real checkout with Python 3.13 (the CI version) and pytest 8.4.2:

| Command | Result |
| --- | --- |
| `python tests/mutation/run.py --phase both` | 34 mutants: 13 killed before, 34 after (`results.json`) |
| `python -m pytest -q` | 770 passed, 2 skipped in 180 s (the new tests take under a second) |
| `python verify_all.py` | ALL 394 CHECKS PASSED |
| `ruff check .` | All checks passed |
| `git diff --check` | Clean |

## Remaining limitations

`verify_isomorphism` checks injectivity and adjacency only among the entries
supplied to it: an empty or singleton partial mapping is currently accepted
for a larger board. The independent checker checks exact source coverage and
rejects these cases. This existing limitation was confirmed and left unchanged
on purpose: no real caller passes `coords`, and `independent_check` is the
deliberate second check that rejects partial mappings.

Mutation sampling is bounded to the listed functions and fast test selections.
No SAT solving, network access, or large fixtures occur in the new tests.
