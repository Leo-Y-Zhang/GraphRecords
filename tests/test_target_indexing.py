"""Synthetic snapshots keep offsets and large signed terms observable."""

import pytest

from graphrecords import targets


@pytest.mark.parametrize("offset", ["2,4", 2, "-2,1"])
def test_published_terms_use_the_first_offset_component(monkeypatch, offset):
    monkeypatch.setattr(targets, "load_targets", lambda: {
        "A000000": {"offset": offset, "terms": [11, 0, -9]},
    })
    start = -2 if offset == "-2,1" else 2
    assert targets.offset_start("A000000") == start
    assert targets.published_terms("A000000") == [11, 0, -9]
    assert targets.terms_by_n("A000000") == {start: 11, start + 1: 0, start + 2: -9}


def test_bfile_indices_and_values_are_integers(monkeypatch):
    monkeypatch.setattr(targets, "load_bfiles", lambda: {
        "A000000": {"values": {"10": "-123456789012345678901234567890", "2": "0"}},
    })
    assert targets.bfile_terms_by_n("A000000") == {
        10: -123456789012345678901234567890, 2: 0,
    }
