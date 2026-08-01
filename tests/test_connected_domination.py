import pytest
from graphrecords.brute import brute_connected_dominating_bishop
from graphrecords.connected_domination import connected_dominating_sets
from graphrecords.targets import terms_by_n

BLACK = terms_by_n("A289145")   # connected dominating sets, black bishop
WHITE = terms_by_n("A289169")   # connected dominating sets, white bishop


@pytest.mark.parametrize("n", range(1, 7))
@pytest.mark.parametrize("colour", ["black", "white"])
def test_agrees_with_brute_force(n, colour):
    assert connected_dominating_sets(n, colour) == brute_connected_dominating_bishop(
        n, colour
    )


@pytest.mark.parametrize("n", sorted(BLACK))
def test_reproduces_every_published_black_term(n):
    assert connected_dominating_sets(n, "black") == BLACK[n]


@pytest.mark.parametrize("n", sorted(WHITE))
def test_reproduces_every_published_white_term(n):
    assert connected_dominating_sets(n, "white") == WHITE[n]


def test_no_full_bishop_version_can_exist():
    """The bishop graph has two components, so a connected set lives in one of
    them and cannot dominate the other. OEIS has black and white variants but no
    full-graph one, which is consistent with that."""
    from graphrecords.targets import load_targets

    names = [r["name"] for r in load_targets().values()]
    full = [
        nm for nm in names
        if "connected dominating sets" in nm.lower()
        and "black" not in nm.lower()
        and "white" not in nm.lower()
        and "honeycomb" not in nm.lower()
    ]
    assert full == [], f"unexpected full-bishop connected dominating sequence: {full}"
