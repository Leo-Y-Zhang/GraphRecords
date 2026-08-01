"""Verification level L4: structural identities.

L0-L3 could all share a modelling error. These are facts about the problem
rather than about our code, so they catch what the other levels cannot.
"""
import pytest
from graphrecords.connected import frontier_connected
from graphrecords.targets import terms_by_n

BISHOP = terms_by_n("A291595")


@pytest.mark.parametrize("n", sorted(BISHOP))
def test_black_plus_white_equals_full_bishop(n):
    """A bishop never changes the parity of row+col, so the bishop graph has
    exactly two components and connected subgraph counts add."""
    black = frontier_connected(n, "black")
    white = frontier_connected(n, "white")
    assert black + white == BISHOP[n]


@pytest.mark.parametrize("n", [2, 4, 6, 8])
def test_colours_are_isomorphic_on_even_boards(n):
    """For even n reflecting the board swaps the two colour classes, so the two
    single-colour bishop graphs are isomorphic and must give equal counts."""
    assert frontier_connected(n, "black") == frontier_connected(n, "white")


@pytest.mark.parametrize("n", [3, 5, 7])
def test_colours_differ_on_odd_boards(n):
    """For odd n the colour classes have different sizes, so the counts must
    differ -- a guard against an implementation that ignores colour."""
    assert frontier_connected(n, "black") != frontier_connected(n, "white")


def test_white_board_is_empty_at_n_equals_one():
    assert frontier_connected(1, "white") == 0
