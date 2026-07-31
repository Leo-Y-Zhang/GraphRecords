"""Access to the committed snapshot of published OEIS terms."""
import functools
import json
import pathlib

SNAPSHOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets.json"


@functools.lru_cache(maxsize=1)
def load_targets():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def published_terms(aid):
    return load_targets()[aid]["terms"]
