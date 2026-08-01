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
