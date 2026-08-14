"""Access to the committed snapshot of published OEIS terms.

Offsets are NOT uniform across the family: A290719 (black bishop) starts at n=1,
but A290769 (white bishop) starts at n=2, because a 1 X 1 board has no white
cells. Anything comparing our output to published data must index by n, never by
position in the list.
"""
import functools
import json
import pathlib

SNAPSHOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets.json"
BFILES = pathlib.Path(__file__).resolve().parents[1] / "data" / "upstream_bfiles.json"


@functools.lru_cache(maxsize=1)
def load_targets():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def load_bfiles():
    return json.loads(BFILES.read_text(encoding="utf-8"))


def bfile_terms_by_n(aid):
    """Published b-file terms keyed by n, from tools/probe_upstream_bfiles.py.

    The b-file is the authority and the DATA line is not: OEIS truncates DATA
    near 260 characters, so an entry can display 15 terms while its b-file holds
    50. A290941 is exactly such an entry, and reading its DATA line as the term
    count is the mistake this repo has already paid for once.
    """
    return {int(n): int(v) for n, v in load_bfiles()[aid]["values"].items()}


def published_terms(aid):
    """Published terms in order, without any indexing information."""
    return load_targets()[aid]["terms"]


def offset_start(aid):
    """The n that the first published term belongs to."""
    offset = load_targets()[aid]["offset"]
    return int(str(offset).split(",")[0])


def terms_by_n(aid):
    """Published terms keyed by their true n, honouring the sequence offset."""
    start = offset_start(aid)
    return {start + i: v for i, v in enumerate(published_terms(aid))}
