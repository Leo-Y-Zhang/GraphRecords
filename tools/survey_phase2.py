"""Reconnaissance for Phase 2: the local board-graph families.

Phase 1 established a sharp rule -- predicates needing only class occupancy
collapse, predicates needing populations do not. That rule was derived on rook
graphs. Phase 2 targets graphs where adjacency is LOCAL under a row-major sweep
(grid, king, knight, triangular grid, torus), where the standard attack is a
broken-profile DP instead.

This script answers the only question that decides whether Phase 2 is worth
planning: how many terms do those entries actually have, and which predicates do
they use? Writes data/phase2_survey.json.
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

UA = {"User-Agent": "Mozilla/5.0 (OEIS family survey; low volume)"}
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "phase2_survey.json"

FAMILIES = [
    "grid graph",
    "king graph",
    "knight graph",
    "triangular grid graph",
    "torus grid graph",
]


def fetch(url, attempts=3):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60
            ) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:
            if attempt == attempts - 1:
                print(f"  giving up: {exc}")
                return None
            time.sleep(2 * (attempt + 1))


def search_all(query, cap=800):
    """Page an OEIS search. An exact multiple of the page size yields an empty
    body rather than a short page, so treat unparseable output as the end."""
    out, start = [], 0
    while start < cap:
        body = fetch(
            "https://oeis.org/search?q="
            + urllib.parse.quote(query)
            + f"&fmt=json&start={start}"
        )
        time.sleep(0.5)
        if not body or not body.strip():
            break
        try:
            doc = json.loads(body)
        except json.JSONDecodeError:
            break
        res = doc.get("results") if isinstance(doc, dict) else doc
        if not res:
            break
        out.extend(res)
        if len(res) < 10:
            break
        start += 10
    return out


def main():
    records = {}
    for fam in FAMILIES:
        print(f"searching {fam!r} keyword:more ...")
        sys.stdout.flush()
        for res in search_all(f'"{fam}" keyword:more'):
            aid = "A%06d" % res["number"]
            rec = records.setdefault(aid, {
                "name": res.get("name", ""),
                "offset": res.get("offset", ""),
                "keyword": res.get("keyword", ""),
                "nterms": len([x for x in res.get("data", "").split(",") if x.strip()]),
                "families": [],
            })
            rec["families"].append(fam)
        print(f"  running total {len(records)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=1, sort_keys=True), encoding="utf-8")

    # group by predicate so the cheap ones are visible
    groups = defaultdict(list)
    for aid, r in records.items():
        m = re.match(r"Number of (.+?) (?:in|on|of) ", r["name"])
        key = (m.group(1) if m else r["name"][:44]).lower()
        key = re.sub(r"\(.*?\)", "", key).strip()
        groups[key].append((aid, r["nterms"]))

    print(f"\n{len(records)} sequences with keyword:more across the local families\n")
    print(f"{'predicate':44s} {'seqs':>4s} {'fewest terms':>12s}")
    for key, v in sorted(groups.items(), key=lambda kv: (-len(kv[1]), min(x[1] for x in kv[1])))[:24]:
        print(f"{key[:44]:44s} {len(v):>4d} {min(x[1] for x in v):>12d}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
