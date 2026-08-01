# GraphRecords Phase 1 — Bishop Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute and verify new terms for OEIS sequences defined on the n X n bishop graph, by exploiting the fact that the bishop graph is a rook graph in rotated coordinates.

**Architecture:** A small Python package. `boards.py` builds explicit graphs from board definitions; `reduction.py` implements and self-checks the 45-degree map to rook coordinates; `brute.py` is a deliberately naive exhaustive reference; `connected.py` holds two independent fast counters (exact-support peeling, then a frontier partition DP). Every fast result is gated against brute force, against published OEIS terms, against the other fast algorithm, and against cross-sequence identities.

**Tech Stack:** Python 3.13, stdlib only for the engine (arbitrary-precision ints are required and native). `pytest` for tests. `numba`/`csc.exe` only if profiling later shows a need — not used in Phase 1.

## Global Constraints

- Counts exceed 64 bits. Use Python `int` everywhere. Never introduce a fixed-width accumulator.
- No result is reported unless it passes every applicable verification level (L0-L4 in the spec).
- Published OEIS terms are fetched once into `data/targets.json` and committed. Tests read the committed snapshot, never the network.
- Submitting to OEIS is out of scope for this plan. Staged output only.
- Commit identity is the repo default (`GreenPandaTech` noreply). Hooks live at `C:\dev\Tools\githooks`; if a commit reports no gitleaks output, stop and restore the gate.
- Commit messages: plain ASCII, no backticks, no `$(...)`, no apostrophes.
- Board colour naming is exactly `"black"`, `"white"`, `"both"` throughout. Never `"full"` or `"all"`.

---

### Task 1: Board construction

**Files:**
- Create: `graphrecords/__init__.py` (empty)
- Create: `graphrecords/boards.py`
- Test: `tests/test_boards.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `bishop_cells(n: int, colour: str) -> list[tuple[int,int]]`
  - `bishop_adjacent(a: tuple[int,int], b: tuple[int,int]) -> bool`
  - `adjacency_masks(cells, adjacent) -> list[int]` — bitmask neighbours, index-aligned to `cells`

- [x] **Step 1: Write the failing test**

```python
# tests/test_boards.py
from graphrecords.boards import bishop_cells, bishop_adjacent, adjacency_masks


def test_black_cells_are_even_parity():
    assert bishop_cells(3, "black") == [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]


def test_white_cells_are_odd_parity():
    assert bishop_cells(3, "white") == [(0, 1), (1, 0), (1, 2), (2, 1)]


def test_both_is_the_whole_board():
    assert len(bishop_cells(4, "both")) == 16


def test_adjacency_is_diagonal_only():
    assert bishop_adjacent((0, 0), (1, 1)) is True      # main diagonal
    assert bishop_adjacent((0, 2), (1, 1)) is True      # anti-diagonal
    assert bishop_adjacent((0, 0), (0, 1)) is False     # same row
    assert bishop_adjacent((0, 0), (0, 0)) is False     # not self-adjacent


def test_white_3x3_is_a_four_cycle():
    cells = bishop_cells(3, "white")
    nbr = adjacency_masks(cells, bishop_adjacent)
    assert [bin(m).count("1") for m in nbr] == [2, 2, 2, 2]
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_boards.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'graphrecords'`

- [x] **Step 3: Write minimal implementation**

```python
# graphrecords/boards.py
"""Board cell sets and explicit graph construction.

Cells are (row, col) with 0 <= row, col < n. Bishop adjacency is "shares a
diagonal", which splits the board by colour: a bishop never changes the parity
of row+col, so the n X n bishop graph has exactly two components.
"""
from itertools import combinations

COLOURS = ("black", "white", "both")


def bishop_cells(n, colour):
    """Cells of the n X n board of the given colour, in row-major order."""
    if colour not in COLOURS:
        raise ValueError(f"colour must be one of {COLOURS}, got {colour!r}")
    if colour == "both":
        keep = lambda r, c: True
    elif colour == "black":
        keep = lambda r, c: (r + c) % 2 == 0
    else:
        keep = lambda r, c: (r + c) % 2 == 1
    return [(r, c) for r in range(n) for c in range(n) if keep(r, c)]


def bishop_adjacent(a, b):
    """True iff distinct cells a and b share a diagonal."""
    return a != b and (a[0] + a[1] == b[0] + b[1] or a[0] - a[1] == b[0] - b[1])


def adjacency_masks(cells, adjacent):
    """Neighbour bitmasks, index-aligned with cells."""
    index = {cell: i for i, cell in enumerate(cells)}
    nbr = [0] * len(cells)
    for a, b in combinations(cells, 2):
        if adjacent(a, b):
            nbr[index[a]] |= 1 << index[b]
            nbr[index[b]] |= 1 << index[a]
    return nbr
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_boards.py -v`
Expected: PASS, 5 passed

- [x] **Step 5: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/__init__.py graphrecords/boards.py tests/test_boards.py
git commit -m "Add board construction for bishop graphs"
```

---

### Task 2: The rook reduction, with an exhaustive self-check

**Files:**
- Create: `graphrecords/reduction.py`
- Test: `tests/test_reduction.py`

**Interfaces:**
- Consumes: `bishop_cells`, `bishop_adjacent` from Task 1
- Produces:
  - `rook_coords(n: int, colour: str) -> dict[tuple[int,int], tuple[int,int]]`
  - `verify_isomorphism(n: int, colour: str) -> None` — raises `AssertionError` on any violation
  - `class_grid(n: int, colour: str) -> tuple[list[list[int]], int, int]` — returns `(grid, nx, ny)` where `grid[i][j]` is the number of cells in x-class `i` and y-class `j`

- [x] **Step 1: Write the failing test**

```python
# tests/test_reduction.py
import pytest
from graphrecords.reduction import rook_coords, verify_isomorphism, class_grid


@pytest.mark.parametrize("n", range(1, 13))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_bishop_graph_is_a_rook_graph(n, colour):
    verify_isomorphism(n, colour)


def test_map_is_injective():
    for n in range(1, 13):
        for colour in ("black", "white"):
            image = list(rook_coords(n, colour).values())
            assert len(image) == len(set(image))


def test_class_grid_totals_match_cell_count():
    for n in range(1, 10):
        grid, nx, ny = class_grid(n, "black")
        assert sum(sum(row) for row in grid) == len(rook_coords(n, "black"))
        assert len(grid) == nx and all(len(r) == ny for r in grid)


def test_each_x_class_meets_a_contiguous_y_interval():
    # locality is what makes the frontier DP in Task 6 affordable
    grid, nx, ny = class_grid(9, "black")
    for row in grid:
        used = [j for j, v in enumerate(row) if v]
        assert used == list(range(used[0], used[-1] + 1))
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_reduction.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'graphrecords.reduction'`

- [x] **Step 3: Write minimal implementation**

```python
# graphrecords/reduction.py
"""The bishop-to-rook reduction.

Theorem. For cells of one colour on the n X n board, the map
    phi(r, c) = ((r + c) // 2, (r - c + n) // 2)
is injective, and two distinct cells share a diagonal iff their images agree in
the first coordinate (anti-diagonal) or the second (main diagonal).

Proof. Within one colour r+c has fixed parity, so r-c does too. On values of one
parity both t -> t // 2 and t -> (t + n) // 2 are strictly monotone, hence
injective. Cells share an anti-diagonal iff r+c matches, i.e. iff the first
coordinates agree; they share a main diagonal iff r-c matches, i.e. iff the
second coordinates agree. The pair (r+c, r-c) determines (r, c), giving
injectivity of phi.

So the single-colour bishop graph IS the rook graph on the image cells: adjacent
iff sharing an x-class or a y-class.
"""
from itertools import combinations

from graphrecords.boards import bishop_adjacent, bishop_cells


def rook_coords(n, colour):
    """Map each cell of the given colour to its (x-class, y-class) pair."""
    if colour == "both":
        raise ValueError("the reduction applies per colour; 'both' is disconnected")
    return {
        (r, c): ((r + c) // 2, (r - c + n) // 2)
        for (r, c) in bishop_cells(n, colour)
    }


def verify_isomorphism(n, colour):
    """Check the theorem exhaustively for this board. Raises on violation."""
    coords = rook_coords(n, colour)
    if len(set(coords.values())) != len(coords):
        raise AssertionError(f"phi not injective for n={n} colour={colour}")
    for a, b in combinations(coords, 2):
        rook = coords[a][0] == coords[b][0] or coords[a][1] == coords[b][1]
        if bishop_adjacent(a, b) != rook:
            raise AssertionError(
                f"n={n} colour={colour}: {a} vs {b} bishop="
                f"{bishop_adjacent(a, b)} rook={rook}"
            )


def class_grid(n, colour):
    """Cell counts per (x-class, y-class), with classes renumbered from zero."""
    coords = rook_coords(n, colour)
    xs = sorted({x for x, _ in coords.values()})
    ys = sorted({y for _, y in coords.values()})
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: j for j, y in enumerate(ys)}
    grid = [[0] * len(ys) for _ in xs]
    for (x, y) in coords.values():
        grid[xi[x]][yi[y]] += 1
    return grid, len(xs), len(ys)
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_reduction.py -v`
Expected: PASS, 28 passed

- [x] **Step 5: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/reduction.py tests/test_reduction.py
git commit -m "Add bishop to rook reduction with exhaustive isomorphism check"
```

---

### Task 3: Brute-force reference counter (verification level L0)

**Files:**
- Create: `graphrecords/brute.py`
- Test: `tests/test_brute.py`

**Interfaces:**
- Consumes: `bishop_cells`, `bishop_adjacent`, `adjacency_masks` from Task 1
- Produces:
  - `connected_induced_count(nbr: list[int]) -> int`
  - `brute_connected_bishop(n: int, colour: str) -> int`

- [x] **Step 1: Write the failing test**

```python
# tests/test_brute.py
import pytest
from graphrecords.brute import brute_connected_bishop

# published OEIS DATA, snapshotted from oeis.org
A290719 = [1, 3, 22, 168, 5251, 194751]          # black bishop, n = 1..6
A291595 = [1, 6, 35, 336, 8095, 389502]          # full bishop, n = 1..6


@pytest.mark.parametrize("n,expected", list(enumerate(A290719, start=1)))
def test_matches_published_black(n, expected):
    assert brute_connected_bishop(n, "black") == expected


def test_components_sum_to_the_full_bishop_graph():
    for n in range(1, 7):
        black = brute_connected_bishop(n, "black")
        white = brute_connected_bishop(n, "white")
        assert black + white == A291595[n - 1]


def test_single_cell_board():
    assert brute_connected_bishop(1, "black") == 1
    assert brute_connected_bishop(1, "white") == 0
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_brute.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'graphrecords.brute'`

- [x] **Step 3: Write minimal implementation**

```python
# graphrecords/brute.py
"""Exhaustive reference counters (verification level L0).

Deliberately naive: builds the graph straight from the definition and walks every
subset. Too slow to be useful beyond about 22 cells, which is the point -- it is
the independent check that the fast algorithms are counting the right thing.
"""
from graphrecords.boards import adjacency_masks, bishop_adjacent, bishop_cells


def connected_induced_count(nbr):
    """Number of non-empty vertex subsets inducing a connected subgraph."""
    m = len(nbr)
    total = 0
    for mask in range(1, 1 << m):
        low = mask & -mask
        seen = frontier = low
        while frontier:
            reached = 0
            f = frontier
            while f:
                bit = f & -f
                reached |= nbr[bit.bit_length() - 1]
                f ^= bit
            frontier = reached & mask & ~seen
            seen |= frontier
        if seen == mask:
            total += 1
    return total


def brute_connected_bishop(n, colour):
    cells = bishop_cells(n, colour)
    if not cells:
        return 0
    return connected_induced_count(adjacency_masks(cells, bishop_adjacent))
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_brute.py -v`
Expected: PASS, 9 passed

- [x] **Step 5: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/brute.py tests/test_brute.py
git commit -m "Add exhaustive reference counter for connected induced subgraphs"
```

---

### Task 4: Target list and published-term snapshot

**Files:**
- Create: `graphrecords/targets.py`
- Create: `tools/fetch_targets.py`
- Create: `data/targets.json` (generated, then committed)
- Test: `tests/test_targets.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `load_targets() -> dict[str, dict]` — keyed by A-number, each with `name`, `offset`, `keyword`, `terms` (list of `int`)
  - `published_terms(aid: str) -> list[int]`

- [x] **Step 1: Write the failing test**

```python
# tests/test_targets.py
from graphrecords.targets import load_targets, published_terms


def test_snapshot_contains_the_anchor_sequences():
    t = load_targets()
    for aid in ("A290719", "A291595", "A290769"):
        assert aid in t, f"{aid} missing from snapshot"


def test_black_bishop_terms_match_the_known_prefix():
    assert published_terms("A290719")[:6] == [1, 3, 22, 168, 5251, 194751]


def test_terms_are_ints_not_strings():
    for aid, rec in load_targets().items():
        assert all(isinstance(v, int) for v in rec["terms"]), aid


def test_offset_recorded_for_every_target():
    for aid, rec in load_targets().items():
        assert rec["offset"], aid
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_targets.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'graphrecords.targets'`

- [x] **Step 3: Write the fetcher and the loader**

```python
# tools/fetch_targets.py
"""Snapshot every bishop-graph sequence from OEIS into data/targets.json.

Run once; the snapshot is committed and the tests read it offline so the suite
never depends on the network.
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (OEIS family snapshot; low volume)"}
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets.json"


def search_all(query, cap=400):
    out, start = [], 0
    while start < cap:
        url = (
            "https://oeis.org/search?q="
            + urllib.parse.quote(query)
            + f"&fmt=json&start={start}"
        )
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            doc = json.loads(r.read().decode("utf-8", "replace"))
        time.sleep(0.5)
        res = doc.get("results") if isinstance(doc, dict) else doc
        if not res:
            break
        out.extend(res)
        if len(res) < 10:
            break
        start += 10
    return out


def main():
    records = {}
    for q in ('"bishop graph"', '"bishop graphs"'):
        for res in search_all(q):
            aid = "A%06d" % res["number"]
            records[aid] = {
                "name": res.get("name", ""),
                "offset": res.get("offset", ""),
                "keyword": res.get("keyword", ""),
                "author": res.get("author", ""),
                "terms": [int(x) for x in res.get("data", "").split(",") if x.strip()],
            }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT} with {len(records)} sequences")


if __name__ == "__main__":
    main()
```

```python
# graphrecords/targets.py
"""Access to the committed snapshot of published OEIS terms."""
import functools
import json
import pathlib

SNAPSHOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets.json"


@functools.lru_cache(maxsize=1)
def load_targets():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def published_terms(aid):
    return load_targets()[aid]["terms"]
```

- [x] **Step 4: Generate the snapshot**

Run: `cd /c/dev/GraphRecords && python tools/fetch_targets.py`
Expected: `wrote ...data/targets.json with 110 sequences` (a slightly larger count is fine if OEIS has grown; a much smaller one means the search failed, so stop and investigate)

- [x] **Step 5: Run tests to verify they pass**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_targets.py -v`
Expected: PASS, 4 passed

- [x] **Step 6: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/targets.py tools/fetch_targets.py data/targets.json tests/test_targets.py
git commit -m "Snapshot the bishop graph family and add offline target loader"
```

---

### Task 5: Exact-support peeling counter (first fast algorithm)

**Files:**
- Create: `graphrecords/connected.py`
- Test: `tests/test_connected_peeling.py`

**Interfaces:**
- Consumes: `class_grid` from Task 2; `brute_connected_bishop` from Task 3; `published_terms` from Task 4
- Produces: `peeling_connected(n: int, colour: str) -> int`

**Why this exists:** it is slow (about 9^n) but structurally different from the frontier DP in Task 6, so it serves as the independent cross-check at verification level L3.

- [x] **Step 1: Write the failing test**

```python
# tests/test_connected_peeling.py
import pytest
from graphrecords.brute import brute_connected_bishop
from graphrecords.connected import peeling_connected
from graphrecords.targets import published_terms


@pytest.mark.parametrize("n", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_brute_force(n, colour):
    assert peeling_connected(n, colour) == brute_connected_bishop(n, colour)


@pytest.mark.parametrize("n", range(1, 9))
def test_reproduces_published_black_bishop(n):
    assert peeling_connected(n, "black") == published_terms("A290719")[n - 1]
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_connected_peeling.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'graphrecords.connected'`

- [x] **Step 3: Write minimal implementation**

```python
# graphrecords/connected.py
"""Counting connected cell subsets of a rook graph.

A cell subset is connected in the rook graph exactly when the bipartite graph it
induces between x-classes and y-classes is connected, because all cells sharing a
class are mutually adjacent. Both counters below work on that bipartite view.
"""
from functools import lru_cache

from graphrecords.reduction import class_grid


def _submasks(m):
    """Every submask of m, including m and 0."""
    s = m
    while True:
        yield s
        if s == 0:
            return
        s = (s - 1) & m


def peeling_connected(n, colour):
    """Connected non-empty cell subsets, by exact-support inclusion-exclusion.

    B(X, Y) counts subsets whose x-support is exactly X and y-support exactly Y.
    C(X, Y) counts those that are also connected, found by peeling off the
    component holding the lowest x-class of X. Cost is about 9^n.
    """
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0

    @lru_cache(maxsize=None)
    def ncells(X, Y):
        total = 0
        for i in range(nx):
            if X >> i & 1:
                row = grid[i]
                for j in range(ny):
                    if Y >> j & 1:
                        total += row[j]
        return total

    @lru_cache(maxsize=None)
    def B(X, Y):
        if X == 0 or Y == 0:
            return 1 if (X == 0 and Y == 0) else 0
        total = 0
        for X1 in _submasks(X):
            parity_x = bin(X ^ X1).count("1")
            for Y1 in _submasks(Y):
                sign = -1 if (parity_x + bin(Y ^ Y1).count("1")) & 1 else 1
                total += sign * (1 << ncells(X1, Y1))
        return total

    @lru_cache(maxsize=None)
    def C(X, Y):
        if X == 0 or Y == 0:
            return 1 if (X == 0 and Y == 0) else 0
        total = B(X, Y)
        lowx = X & -X
        for X1 in _submasks(X):
            if not X1 & lowx:
                continue
            for Y1 in _submasks(Y):
                if Y1 == 0 or (X1 == X and Y1 == Y):
                    continue
                total -= C(X1, Y1) * B(X ^ X1, Y ^ Y1)
        return total

    return sum(C(X, Y) for X in range(1, 1 << nx) for Y in range(1, 1 << ny))
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_connected_peeling.py -v`
Expected: PASS, 20 passed. The n=8 case takes roughly 4 seconds.

- [x] **Step 5: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/connected.py tests/test_connected_peeling.py
git commit -m "Add exact support peeling counter validated to eight published terms"
```

---

### Task 6: Frontier partition DP (the production algorithm)

**Files:**
- Modify: `graphrecords/connected.py` (append; do not disturb `peeling_connected`)
- Test: `tests/test_connected_frontier.py`

**Interfaces:**
- Consumes: `class_grid` from Task 2
- Produces:
  - `frontier_connected(n: int, colour: str) -> int`
  - `frontier_state_peak(n: int, colour: str) -> int` — the largest number of live DP states, for the growth measurement the spec requires

**Algorithm.** Process x-classes in order, carrying a partition of the y-classes into connected blocks, with a distinguished label for "untouched". At x-class `i`, choose a non-empty subset `T` of the y-classes it meets, contributing `prod over j in T of (2**grid[i][j] - 1)` and merging every block meeting `T` into one; or place nothing, contributing 1. Because each x-class meets a contiguous y-interval (asserted in Task 2), a y-class below the current interval can never be touched again. If such a finalised y-class sits in a block separate from any still-active block, no future merge can join them, so that state can never reach a single component and is pruned. At the end, count states whose touched y-classes form exactly one block.

- [x] **Step 1: Write the failing test**

```python
# tests/test_connected_frontier.py
import pytest
from graphrecords.connected import frontier_connected, peeling_connected
from graphrecords.targets import published_terms


@pytest.mark.parametrize("n", range(1, 9))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_the_peeling_counter(n, colour):
    assert frontier_connected(n, colour) == peeling_connected(n, colour)


@pytest.mark.parametrize("n", range(1, 10))
def test_reproduces_every_published_black_bishop_term(n):
    assert frontier_connected(n, "black") == published_terms("A290719")[n - 1]


@pytest.mark.parametrize("n", range(1, 10))
def test_reproduces_every_published_white_bishop_term(n):
    assert frontier_connected(n, "white") == published_terms("A290769")[n - 1]
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_connected_frontier.py -v`
Expected: FAIL, `ImportError: cannot import name 'frontier_connected'`

- [x] **Step 3: Append the implementation**

```python
# appended to graphrecords/connected.py


def _canonical(labels):
    """Relabel a tuple of block ids into restricted-growth form; 0 stays 0."""
    remap = {0: 0}
    out = []
    nxt = 1
    for v in labels:
        if v not in remap:
            remap[v] = nxt
            nxt += 1
        out.append(remap[v])
    return tuple(out)


def _frontier_run(n, colour):
    """Run the DP, yielding (answer, peak_state_count)."""
    grid, nx, ny = class_grid(n, colour)
    if nx == 0 or ny == 0:
        return 0, 0

    intervals = []
    for i in range(nx):
        used = [j for j, v in enumerate(grid[i]) if v]
        intervals.append((used[0], used[-1]) if used else (0, -1))

    states = {(0,) * ny: 1}
    peak = 1
    for i in range(nx):
        lo, hi = intervals[i]
        cols = list(range(lo, hi + 1))
        # weights for every non-empty subset of this x-class's y-interval
        options = []
        for bits in range(1, 1 << len(cols)):
            weight = 1
            chosen = []
            for k, j in enumerate(cols):
                if bits >> k & 1:
                    weight *= (1 << grid[i][j]) - 1
                    chosen.append(j)
            options.append((chosen, weight))

        # y-classes that no later x-class can reach
        future_lo = min((intervals[k][0] for k in range(i + 1, nx)), default=ny)

        nxt = {}
        for labels, count in states.items():
            for chosen, weight in [([], 1)] + options:
                new = list(labels)
                if chosen:
                    merged = {new[j] for j in chosen if new[j]}
                    target = min(merged) if merged else max(new) + 1
                    for j in chosen:
                        new[j] = target
                    if merged:
                        for idx, v in enumerate(new):
                            if v in merged:
                                new[idx] = target
                key = _canonical(new)
                # prune: a finalised block that can never merge again
                closed = {key[j] for j in range(future_lo) if key[j]}
                active = {key[j] for j in range(future_lo, ny) if key[j]}
                if len(closed - active) > 1 or (closed - active and active):
                    continue
                nxt[key] = nxt.get(key, 0) + count * weight
        states = nxt
        peak = max(peak, len(states))

    answer = 0
    for labels, count in states.items():
        blocks = {v for v in labels if v}
        if len(blocks) == 1:
            answer += count
    return answer, peak


def frontier_connected(n, colour):
    return _frontier_run(n, colour)[0]


def frontier_state_peak(n, colour):
    return _frontier_run(n, colour)[1]
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_connected_frontier.py -v`
Expected: PASS, 34 passed

If any case fails, do NOT adjust the expected values — they are published data. Debug the DP against `peeling_connected` at the smallest failing n, where both are cheap.

- [x] **Step 5: Measure state growth and record it**

Run:
```bash
cd /c/dev/GraphRecords && python -c "
from graphrecords.connected import frontier_state_peak, frontier_connected
import time
for n in range(1, 15):
    t = time.time(); v = frontier_connected(n, 'black'); dt = time.time() - t
    print(n, frontier_state_peak(n, 'black'), f'{dt:.2f}s', v)
"
```
Expected: peak state counts and timings printed per n. Stop at whatever n exceeds about 10 minutes or 4 GB. Record the table in `PAPER.md` in Task 9.

- [x] **Step 6: Commit**

```bash
cd /c/dev/GraphRecords
git add graphrecords/connected.py tests/test_connected_frontier.py
git commit -m "Add frontier partition DP validated against peeling and published data"
```

---

### Task 7: Cross-sequence identity gate (verification level L4)

**Files:**
- Create: `tests/test_identities.py`

**Interfaces:**
- Consumes: `frontier_connected` from Task 6; `published_terms` from Task 4

**Why this exists:** L0-L3 could all share a modelling error. The bishop graph having exactly two components is a fact about the problem, not about our code, so it catches errors the other levels cannot.

- [x] **Step 1: Write the test**

```python
# tests/test_identities.py
import pytest
from graphrecords.connected import frontier_connected
from graphrecords.targets import published_terms


@pytest.mark.parametrize("n", range(1, 10))
def test_black_plus_white_equals_full_bishop(n):
    """The bishop graph has two components, so connected subgraph counts add."""
    black = frontier_connected(n, "black")
    white = frontier_connected(n, "white")
    assert black + white == published_terms("A291595")[n - 1]


def test_white_board_is_empty_at_n_equals_one():
    assert frontier_connected(1, "white") == 0
```

- [x] **Step 2: Run the test**

Run: `cd /c/dev/GraphRecords && python -m pytest tests/test_identities.py -v`
Expected: PASS, 10 passed

- [x] **Step 3: Commit**

```bash
cd /c/dev/GraphRecords
git add tests/test_identities.py
git commit -m "Add cross sequence identity gate for the two bishop components"
```

---

### Task 8: The verification gate

**Files:**
- Create: `verify_all.py`
- Create: `README.md`

**Interfaces:**
- Consumes: everything above
- Produces: an executable gate that exits non-zero on any failure

- [x] **Step 1: Write the gate**

```python
# verify_all.py
"""Re-check every claim in this repository from cold.

Exits 0 only if every verification level passes. Believe this over any prose.
"""
import subprocess
import sys

from graphrecords.brute import brute_connected_bishop
from graphrecords.connected import frontier_connected, peeling_connected
from graphrecords.reduction import verify_isomorphism
from graphrecords.targets import load_targets, published_terms

CHECKS = []


def check(name, ok):
    CHECKS.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}")


def main():
    # L0/L1: the reduction itself, and fast vs exhaustive
    for n in range(1, 13):
        for colour in ("black", "white"):
            try:
                verify_isomorphism(n, colour)
                check(f"isomorphism n={n} {colour}", True)
            except AssertionError as e:
                check(f"isomorphism n={n} {colour}: {e}", False)
    for n in range(1, 7):
        for colour in ("black", "white"):
            check(
                f"frontier == brute n={n} {colour}",
                frontier_connected(n, colour) == brute_connected_bishop(n, colour),
            )

    # L2: published terms
    for aid, colour in (("A290719", "black"), ("A290769", "white")):
        for i, term in enumerate(published_terms(aid), start=1):
            check(f"{aid} a({i})", frontier_connected(i, colour) == term)

    # L3: two independent fast algorithms
    for n in range(1, 9):
        for colour in ("black", "white"):
            check(
                f"frontier == peeling n={n} {colour}",
                frontier_connected(n, colour) == peeling_connected(n, colour),
            )

    # L4: structural identity
    for i, term in enumerate(published_terms("A291595"), start=1):
        check(
            f"A291595 a({i}) == black + white",
            frontier_connected(i, "black") + frontier_connected(i, "white") == term,
        )

    # the test suite is part of the gate
    rc = subprocess.call([sys.executable, "-m", "pytest", "-q"])
    check("pytest suite", rc == 0)

    failed = [n for n, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)} passed / {len(failed)} failed")
    if failed:
        print("FAILURES:")
        for n in failed:
            print("  ", n)
        return 1
    print(f"verify_all: ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 2: Write the README**

```markdown
# GraphRecords

Extending OEIS sequences defined on board graphs, starting with the bishop graph.

The n X n bishop graph is a rook graph in rotated coordinates: the map
`(r, c) -> ((r + c) // 2, (r - c + n) // 2)` sends diagonals to rows and columns.
That turns subset-counting over cells into a problem on a bipartite structure of
size O(n) per side rather than O(n^2) cells.

## Verifying

    python verify_all.py

This is the authoritative gate. It re-derives the isomorphism, checks the fast
counters against exhaustive enumeration, reproduces every published OEIS term of
every target, cross-checks two independent fast algorithms, and enforces the
identity that the bishop graph has exactly two components. Believe it over any
claim written in prose here or anywhere else.

## Layout

- `graphrecords/boards.py` - board cell sets and explicit graph construction
- `graphrecords/reduction.py` - the bishop-to-rook map, with its proof and self-check
- `graphrecords/brute.py` - exhaustive reference counters
- `graphrecords/connected.py` - the two fast counters
- `graphrecords/targets.py` - offline snapshot of published OEIS terms
- `verify_all.py` - the gate
```

- [x] **Step 3: Run the gate**

Run: `cd /c/dev/GraphRecords && python verify_all.py`
Expected: final line `verify_all: ALL <N> CHECKS PASSED`, exit code 0

- [x] **Step 4: Commit**

```bash
cd /c/dev/GraphRecords
git add verify_all.py README.md
git commit -m "Add the verification gate and repository README"
```

---

### Task 9: Extension run, staging, and write-up

**Files:**
- Create: `tools/extend.py`
- Create: `OEIS-upload/README.txt`
- Create: `PAPER.md`

**Interfaces:**
- Consumes: `frontier_connected`, `frontier_state_peak`, `published_terms`

- [x] **Step 1: Write the extension driver**

```python
# tools/extend.py
"""Compute terms beyond the published data and stage them.

Writes an LF-only b-file per sequence (OEIS requires LF, no BOM, trailing LF) and
prints the new terms. Recomputes every published term first: if any disagrees,
nothing is staged for that sequence.
"""
import argparse
import pathlib
import time

from graphrecords.connected import frontier_connected
from graphrecords.targets import published_terms

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"

SEQUENCES = {"A290719": "black", "A290769": "white"}


def run(aid, colour, limit, budget):
    known = published_terms(aid)
    for i, term in enumerate(known, start=1):
        got = frontier_connected(i, colour)
        if got != term:
            raise SystemExit(f"{aid}: a({i}) recomputed as {got}, published {term} - ABORT")
    print(f"{aid}: reproduced all {len(known)} published terms")

    terms = list(known)
    n = len(known) + 1
    while n <= limit:
        t0 = time.time()
        value = frontier_connected(n, colour)
        dt = time.time() - t0
        terms.append(value)
        print(f"{aid}: a({n}) = {value}   [{dt:.1f}s]  NEW")
        if dt > budget:
            print(f"{aid}: stopping, last term took {dt:.0f}s")
            break
        n += 1

    STAGE.mkdir(exist_ok=True)
    path = STAGE / f"b{aid[1:]}.txt"
    body = "".join(f"{i} {v}\n" for i, v in enumerate(terms, start=1))
    path.write_bytes(body.encode("ascii"))
    print(f"{aid}: staged {len(terms)} terms to {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--budget", type=float, default=1800.0,
                    help="stop after a term takes longer than this many seconds")
    args = ap.parse_args()
    for aid, colour in SEQUENCES.items():
        run(aid, colour, args.limit, args.budget)


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Run the extension**

Run: `cd /c/dev/GraphRecords && python tools/extend.py --limit 20 --budget 1800`
Expected: every published term reproduced, then `NEW` lines for each term beyond the published data, then staged b-file paths. If it aborts on a published term, stop and debug — do not stage.

- [x] **Step 3: Verify the staged b-files are LF-only**

Run:
```bash
cd /c/dev/GraphRecords && python -c "
import pathlib
for p in sorted(pathlib.Path('OEIS-upload').glob('b*.txt')):
    raw = p.read_bytes()
    print(p.name, 'lines', raw.count(b'\n'),
          'CRLF' if b'\r' in raw else 'LF-ok',
          'BOM' if raw[:3] == b'\xef\xbb\xbf' else 'no-BOM',
          'trailing-LF' if raw.endswith(b'\n') else 'NO-TRAILING-LF')
"
```
Expected: every file reports `LF-ok no-BOM trailing-LF`

- [x] **Step 4: Write PAPER.md**

Record, with the actual numbers produced in Task 6 Step 5 and Task 9 Step 2:
the reduction theorem and its proof (copy from `graphrecords/reduction.py`); the two
algorithms and their costs; the measured peak-state table; a results table of old
term count versus new term count per sequence; the verification levels and what
each rules out; and an explicit statement of the ceiling — which n became
infeasible and why. State plainly that this extends terms, and does not achieve
an order-of-magnitude increase, because square-board counts grow doubly
exponentially.

- [x] **Step 5: Write the staging README**

```
# OEIS-upload

Staged, NOT submitted. Nothing here goes to OEIS until A217058 is accepted and
the operator authorises each submission individually, one at a time.

b-files are LF-only, no BOM, with a trailing newline, as the OEIS b-file spec
requires.

House style already learned from the A217058 review and to be applied here:
US spelling; comments short and aimed at a general reader; define any term the
entry does not already define; full first names rather than initials in LINKS;
never alter existing lines; wrap multi-paragraph comments with (Start) / (End).
```

- [x] **Step 6: Re-run the gate and commit**

Run: `cd /c/dev/GraphRecords && python verify_all.py`
Expected: `verify_all: ALL <N> CHECKS PASSED`, exit code 0

```bash
cd /c/dev/GraphRecords
git add tools/extend.py OEIS-upload PAPER.md
git commit -m "Extend the bishop connected subgraph sequences and stage b-files"
```

---

## Self-review notes

- **Spec coverage.** Section 4 (reduction) is Task 2; 5.1 is Task 5; 5.2 is Task 6;
  section 6 levels L0-L4 map to Tasks 3, 5, 6, 7 and the gate in Task 8; section 7
  deliverables map to Tasks 8 and 9. Section 5.3 (other predicates) and section 5.4
  (Phase 2) are deliberately **not** in this plan — they need the measured state growth
  from Task 6 Step 5 before they can be planned honestly, and will get their own plan.
- **Naming.** `frontier_connected` / `peeling_connected` / `brute_connected_bishop` are
  used consistently across Tasks 5-9. Colour strings are `"black"`, `"white"`, `"both"`.
- **Known risk.** Task 6's pruning rule is the subtle part. If `frontier_connected`
  disagrees with `peeling_connected`, the prune is the first suspect: it must reject a
  state only when a finalised block can never again merge with an active one.
