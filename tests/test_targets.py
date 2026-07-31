from theseus.targets import load_targets, published_terms


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
