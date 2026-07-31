import pytest
from theseus.connected import frontier_connected, peeling_connected
from theseus.targets import terms_by_n

BLACK = terms_by_n("A290719")   # offset 1
WHITE = terms_by_n("A290769")   # offset 2 -- a 1 X 1 board has no white cells


@pytest.mark.parametrize("n", range(1, 9))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_the_peeling_counter(n, colour):
    assert frontier_connected(n, colour) == peeling_connected(n, colour)


@pytest.mark.parametrize("n", sorted(BLACK))
def test_reproduces_every_published_black_bishop_term(n):
    assert frontier_connected(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", sorted(WHITE))
def test_reproduces_every_published_white_bishop_term(n):
    assert frontier_connected(n, "white") == WHITE[n]
