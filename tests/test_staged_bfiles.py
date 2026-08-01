"""Staged b-files must satisfy the OEIS b-file spec exactly.

LF-only, no BOM, trailing newline, first index equal to the sequence's own
offset, and every published term reproduced unchanged. A Windows checkout will
happily rewrite these to CRLF, which is how the MathRecords b-files went wrong,
so .gitattributes pins them and this test catches any regression.
"""
import json
import pathlib
import re

import pytest
from graphrecords.targets import offset_start, terms_by_n

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"
STAGED = sorted(STAGE.glob("b*.txt")) if STAGE.is_dir() else []
UPSTREAM = ROOT / "data" / "upstream_bfiles.json"


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


@pytest.mark.skipif(not STAGED, reason="nothing staged yet")
@pytest.mark.parametrize("path", STAGED, ids=lambda p: p.name)
def test_staged_file_actually_extends_the_published_bfile(path):
    """A staged file must go beyond the PUBLISHED b-file, not just beyond DATA.

    OEIS truncates the DATA line near 260 characters, so an entry can show 15
    terms while its uploaded b-file holds 50. Three sequences were staged here on
    exactly that misreading and turned out to be known to n=50 already. Refresh
    the snapshot with tools/probe_upstream_bfiles.py before staging anything.
    """
    assert UPSTREAM.is_file(), (
        "data/upstream_bfiles.json missing - run tools/probe_upstream_bfiles.py"
    )
    upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    aid = _aid(path)
    assert aid in upstream, f"{aid} not probed - run tools/probe_upstream_bfiles.py"

    rows = upstream[aid].get("rows")
    last_published = upstream[aid]["last_n"]
    mine = [
        int(r.split()[0])
        for r in path.read_text(encoding="ascii").splitlines()
        if r.strip()
    ]

    # ABSENT and UNKNOWN both arrive as last_n = None and must NOT be conflated.
    # The probe reports rows=0 when the server actually said there is no b-file,
    # and rows=None when it could not tell (dropped connection, rate limit, HTML
    # error page). Treating "could not tell" as "nothing is published upstream"
    # is what lets a submission take credit for someone else's terms, so it fails
    # here rather than passing quietly.
    assert rows is not None, (
        f"{aid}: upstream extent is UNKNOWN, not absent - the probe could not "
        f"read a b-file. Re-run tools/probe_upstream_bfiles.py; do not stage on "
        f"an unverified absence."
    )
    if rows == 0:
        assert last_published is None
        return                      # genuinely no published b-file
    assert max(mine) > last_published, (
        f"{path.name} reaches n={max(mine)} but the published b-file already "
        f"reaches n={last_published} - this is not a contribution"
    )


PACK = ROOT / "data" / "submission_pack.json"
_EXT_FIRST = re.compile(r"a\((\d+)\)")


@pytest.mark.skipif(not PACK.is_file(), reason="no submission pack built yet")
def test_extensions_line_claims_only_genuinely_new_terms():
    """The EXTENSIONS line must start exactly one past the published b-file.

    This is the last artifact before an editor sees it, and it is where
    over-claiming would actually do harm: an EXTENSIONS line starting too low
    takes credit for terms somebody else published. Guarded end to end --
    probe -> staged b-file -> EXTENSIONS line.
    """
    upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    assert pack, "submission pack is empty"

    for rec in pack:
        aid = rec["id"]
        assert aid in upstream, f"{aid} in the pack but never probed"
        rows, last_published = upstream[aid].get("rows"), upstream[aid]["last_n"]
        assert rows is not None, f"{aid}: upstream extent UNKNOWN - re-probe"

        ext = rec.get("extensions")
        if not ext:
            continue                       # nothing claimed, nothing to check
        m = _EXT_FIRST.search(ext)
        assert m, f"{aid}: cannot read a starting term from {ext!r}"
        first_claimed = int(m.group(1))

        expected = 1 if last_published is None else last_published + 1
        assert first_claimed == expected, (
            f"{aid}: EXTENSIONS claims from a({first_claimed}) but the published "
            f"b-file reaches n={last_published}, so the first genuinely new term "
            f"is a({expected}). Claiming lower takes credit for someone else's work."
        )
