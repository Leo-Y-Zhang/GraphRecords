import pytest

from graphrecords.brute import brute_dominating_bishop, brute_total_dominating_bishop
from graphrecords.domination import dominating_sets, total_dominating_sets
from graphrecords.targets import terms_by_n

BLACK = terms_by_n("A289164")   # 15 published terms
WHITE = terms_by_n("A289170")   # 14 published terms
FULL = terms_by_n("A295898")

TBLACK = terms_by_n("A303145")  # total dominating sets, black
TWHITE = terms_by_n("A303147")  # total dominating sets, white

# Total domination needs per-class populations rather than mere occupancy, so it
# is far more expensive than plain domination and cannot reach its own published
# ceiling. Tests stop where the computation stops being cheap.
TOTAL_LIMIT = 9


@pytest.mark.parametrize("n", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_brute_force(n, colour):
    assert dominating_sets(n, colour) == brute_dominating_bishop(n, colour)


@pytest.mark.parametrize("n", sorted(BLACK))
def test_reproduces_every_published_black_term(n):
    assert dominating_sets(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", sorted(WHITE))
def test_reproduces_every_published_white_term(n):
    assert dominating_sets(n, "white") == WHITE[n]


@pytest.mark.parametrize("n", sorted(FULL))
def test_components_multiply(n):
    """Dominating sets multiply across the two components, unlike connected
    subgraph counts which add."""
    assert dominating_sets(n, "black") * dominating_sets(n, "white") == FULL[n]


@pytest.mark.parametrize("n", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_total_agrees_with_brute_force(n, colour):
    assert total_dominating_sets(n, colour) == brute_total_dominating_bishop(n, colour)


@pytest.mark.parametrize("n", [n for n in sorted(TBLACK) if n <= TOTAL_LIMIT])
def test_total_reproduces_published_black(n):
    assert total_dominating_sets(n, "black") == TBLACK[n]


@pytest.mark.parametrize("n", [n for n in sorted(TWHITE) if n <= TOTAL_LIMIT])
def test_total_reproduces_published_white(n):
    assert total_dominating_sets(n, "white") == TWHITE[n]
