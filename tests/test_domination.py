import pytest
from theseus.brute import brute_dominating_bishop
from theseus.domination import dominating_sets
from theseus.targets import terms_by_n

BLACK = terms_by_n("A289164")   # 15 published terms
WHITE = terms_by_n("A289170")   # 14 published terms
FULL = terms_by_n("A295898")


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
