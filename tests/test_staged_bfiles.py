"""Staged b-files must satisfy the OEIS b-file spec exactly.

LF-only, no BOM, trailing newline, first index equal to the sequence's own
offset, and every published term reproduced unchanged. A Windows checkout will
happily rewrite these to CRLF, which is how the MathRecords b-files went wrong,
so .gitattributes pins them and this test catches any regression.

The extent checks below have two modes, because the files have two lives. An
unsent file has to prove it goes beyond what OEIS already publishes, or it is
not a contribution. An approved file is an archive of what was sent, and has to
prove OEIS now serves exactly it. APPROVED_THROUGH says which sequences are in
which life; it is a record of something that happened, not a measurement, so a
sequence that quietly lost terms upstream still fails here.
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

# Submitted by the author and approved by OEIS on 2026-08-13, all ten terms
# the same day: the n each sequence is published through as a result.
APPROVED_THROUGH = {
    "A289145": 10,
    "A289169": 10,
    "A290719": 11,
    "A290769": 11,
    "A291595": 11,
}


def _aid(path):
    return "A" + path.stem[1:]


def _staged_values(path):
    """The staged b-file as {index: term}."""
    values = {}
    for row in path.read_text(encoding="ascii").splitlines():
        if not row.strip():
            continue
        idx, val = row.split()
        values[int(idx)] = int(val)
    return values


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
    values = _staged_values(path)

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
def test_staged_file_agrees_with_the_published_bfile(path):
    """A staged file is measured against the PUBLISHED b-file, never DATA.

    OEIS truncates the DATA line near 260 characters, so an entry can show 15
    terms while its uploaded b-file holds 50. Three sequences were staged here on
    exactly that misreading and turned out to be known to n=50 already. Refresh
    the snapshot with tools/probe_upstream_bfiles.py before staging anything.

    Not yet submitted: the file must go strictly beyond the published b-file, or
    it is not a contribution. Approved (see APPROVED_THROUGH): the published
    b-file must still reach the n we were approved through and must serve every
    staged index. Either way the shared indices must agree term for term - a
    disagreement means the archive and the sequence have drifted apart, and that
    is a defect whichever way it points.
    """
    assert UPSTREAM.is_file(), (
        "data/upstream_bfiles.json missing - run tools/probe_upstream_bfiles.py"
    )
    upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    aid = _aid(path)
    assert aid in upstream, f"{aid} not probed - run tools/probe_upstream_bfiles.py"

    rows = upstream[aid].get("rows")
    last_published = upstream[aid]["last_n"]
    mine = _staged_values(path)

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

    served = upstream[aid].get("values")
    assert served, (
        f"{aid}: the snapshot records how far the b-file goes but not what it "
        f"holds - re-run tools/probe_upstream_bfiles.py, which records values."
    )
    served = {int(n): int(v) for n, v in served.items()}

    for n in sorted(set(mine) & set(served)):
        assert served[n] == mine[n], (
            f"{path.name} holds a({n}) = {mine[n]}, but the published b-file "
            f"serves {served[n]}"
        )

    approved = APPROVED_THROUGH.get(aid)
    if approved is None:
        assert max(mine) > last_published, (
            f"{path.name} reaches n={max(mine)} but the published b-file already "
            f"reaches n={last_published} - this is not a contribution"
        )
        dropped = sorted(set(served) - set(mine))
        assert not dropped, (
            f"{path.name} omits published rows {dropped} - a staged file carries "
            f"every published term unchanged and adds to them"
        )
    else:
        assert last_published >= approved, (
            f"{aid} was approved through a({approved}) on 2026-08-13, but the "
            f"published b-file now reaches only n={last_published}"
        )
        unserved = sorted(set(mine) - set(served))
        assert not unserved, (
            f"{path.name} stages indices {unserved} that the published b-file "
            f"does not serve - what was submitted and what OEIS shows have diverged"
        )


PACK = ROOT / "data" / "submission_pack.json"
_EXT_FIRST = re.compile(r"a\((\d+)\)")


@pytest.mark.skipif(not PACK.is_file(), reason="no submission pack built yet")
def test_extensions_line_claims_only_genuinely_new_terms():
    """The EXTENSIONS line must claim exactly the terms that were new.

    This is the last artifact before an editor sees it, and it is where
    over-claiming would actually do harm: an EXTENSIONS line starting too low
    takes credit for terms somebody else published. Guarded end to end --
    probe -> staged b-file -> EXTENSIONS line.

    For an unsent sequence "new" is one past today's published b-file. Once the
    submission is approved the published b-file contains our own terms, and
    measuring against it would demand the line start past its own contribution;
    so for an approved sequence the same claim is measured against the reach the
    pack recorded when it was built - what OEIS published before we sent
    anything - and upstream must now carry every term the line claims.
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

        approved = APPROVED_THROUGH.get(aid)
        if approved is None:
            expected = 1 if last_published is None else last_published + 1
            assert first_claimed == expected, (
                f"{aid}: EXTENSIONS claims from a({first_claimed}) but the published "
                f"b-file reaches n={last_published}, so the first genuinely new term "
                f"is a({expected}). Claiming lower takes credit for someone else's "
                f"work."
            )
            continue

        was_published = rec.get("upstream_last_n")
        assert was_published is not None, (
            f"{aid}: approved, but the pack records no pre-submission reach to "
            f"measure its EXTENSIONS line against - rebuild the pack"
        )
        assert first_claimed == was_published + 1, (
            f"{aid}: EXTENSIONS claims from a({first_claimed}) but OEIS already "
            f"published to n={was_published} when the pack was built, so the first "
            f"genuinely new term was a({was_published + 1}). Claiming lower takes "
            f"credit for someone else's work."
        )
        assert last_published >= rec["last_n"], (
            f"{aid}: EXTENSIONS claims through a({rec['last_n']}) but the published "
            f"b-file now reaches only n={last_published}"
        )
