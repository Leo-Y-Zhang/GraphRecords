"""Staged b-files must satisfy the OEIS b-file spec exactly.

LF-only, no BOM, trailing newline, first index equal to the sequence's own
offset, and every published term reproduced unchanged. A Windows checkout will
happily rewrite these to CRLF, which is how the MathRecords b-files went wrong,
so .gitattributes pins them and this test catches any regression.
"""
import pathlib

import pytest
from theseus.targets import offset_start, terms_by_n

STAGE = pathlib.Path(__file__).resolve().parents[1] / "OEIS-upload"
STAGED = sorted(STAGE.glob("b*.txt")) if STAGE.is_dir() else []


def _aid(path):
    return "A" + path.stem[1:]


@pytest.mark.skipif(not STAGED, reason="nothing staged yet")
@pytest.mark.parametrize("path", STAGED, ids=lambda p: p.name)
def test_bfile_bytes_are_spec_clean(path):
    raw = path.read_bytes()
    assert b"\r" not in raw, f"{path.name} contains CR - must be LF only"
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path.name} has a BOM"
    assert raw.endswith(b"\n"), f"{path.name} lacks a trailing newline"
    raw.decode("ascii")          # must be plain ASCII


@pytest.mark.skipif(not STAGED, reason="nothing staged yet")
@pytest.mark.parametrize("path", STAGED, ids=lambda p: p.name)
def test_bfile_indices_and_published_terms(path):
    aid = _aid(path)
    rows = [r for r in path.read_text(encoding="ascii").splitlines() if r.strip()]
    values = {}
    for r in rows:
        idx, val = r.split()
        values[int(idx)] = int(val)

    assert min(values) == offset_start(aid), (
        f"{path.name} starts at {min(values)}, sequence offset is {offset_start(aid)}"
    )
    assert sorted(values) == list(range(min(values), max(values) + 1)), (
        f"{path.name} has a gap in its indices"
    )
    for n, term in terms_by_n(aid).items():
        assert values[n] == term, (
            f"{path.name} altered published term a({n}): {values[n]} != {term}"
        )
