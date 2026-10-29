"""Hand-counted tiny graphs distinguish the reference counters' predicates."""

import pytest

from graphrecords import brute, torus
from graphrecords.domination import _get2, _inc2, _set2


def test_population_fields_saturate_without_changing_neighbours():
    packed = 0b10_00_01
    assert _inc2(packed, 1) == 0b10_01_01
    packed = _inc2(_inc2(_inc2(packed, 1), 1), 1)
    assert packed == 0b10_10_01
    assert tuple(_get2(packed, j) for j in range(3)) == (1, 2, 2)
    assert _set2(packed, 1, 0) == 0b10_00_01


@pytest.mark.parametrize(
    "nbr,expected",
    [
        ([], (0, 1, 1, 1, 0)),
        ([0], (1, 1, 0, 1, 1)),
        ([0, 0], (2, 1, 0, 1, 0)),
        ([0b10, 0b01], (3, 3, 1, 2, 3)),
        ([0b010, 0b101, 0b010], (6, 5, 3, 2, 4)),
        ([0b110, 0b101, 0b011], (7, 7, 4, 3, 7)),
    ],
    ids=["empty", "singleton", "isolates", "edge", "path", "triangle"],
)
def test_reference_counters_on_hand_counted_graphs(nbr, expected):
    # On the three-vertex path the minimal dominating sets are {middle} and
    # {ends}; the latter is disconnected. Total domination instead requires
    # the middle and at least one end. These separate all five predicates.
    counters = (
        brute.connected_induced_count,
        brute.dominating_count,
        brute.total_dominating_count,
        brute.minimal_dominating_count,
        brute.connected_dominating_count,
    )
    assert tuple(counter(nbr) for counter in counters) == expected


@pytest.mark.parametrize(
    "mask,expected",
    [(0b000, False), (0b001, True), (0b011, True), (0b111, True), (0b101, False)],
)
def test_torus_connectivity_stays_inside_the_selected_vertices(mask, expected):
    # The two ends connect in the ambient graph, but not in their induced graph.
    assert torus._connected(mask, [0b010, 0b101, 0b010]) is expected


@pytest.mark.parametrize(
    "counter,expected",
    [
        (torus.brute_dominating, 421),
        (torus.brute_total_dominating, 334),
        (torus.brute_connected_dominating, 325),
        (torus.brute_minimal_dominating, 48),
        (torus.brute_connected_induced, 397),
    ],
)
def test_torus_counters_against_set_based_enumeration(counter, expected):
    # C3 square C3 is the rook graph on a 3x3 grid. Rebuild it with sets,
    # independently of torus_adjacent and the bitmask reference helpers.
    vertices = {(r, c) for r in range(3) for c in range(3)}
    neighbours = {
        v: {w for w in vertices - {v} if w[0] == v[0] or w[1] == v[1]}
        for v in vertices
    }
    order = sorted(vertices)
    counts = [0] * 5
    for mask in range(1 << len(order)):
        chosen = {v for i, v in enumerate(order) if mask & (1 << i)}
        covered = set().union(*(neighbours[v] for v in chosen))
        dominates = chosen | covered == vertices
        reached = set()
        pending = list(sorted(chosen)[:1])
        while pending:
            v = pending.pop()
            if v not in reached:
                reached.add(v)
                pending.extend((neighbours[v] & chosen) - reached)
        connected = bool(chosen) and reached == chosen
        minimal = dominates and all(
            (chosen - {v}) | set().union(*(neighbours[w] for w in chosen - {v}))
            != vertices
            for v in chosen
        )
        counts[0] += dominates
        counts[1] += covered == vertices
        counts[2] += dominates and connected
        counts[3] += minimal
        counts[4] += connected
    position = [
        torus.brute_dominating,
        torus.brute_total_dominating,
        torus.brute_connected_dominating,
        torus.brute_minimal_dominating,
        torus.brute_connected_induced,
    ].index(counter)
    assert counter(3) == counts[position] == expected
