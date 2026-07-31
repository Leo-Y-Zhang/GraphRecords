"""Snapshot the Phase 2 torus targets with their full published terms.

Kept separate from data/targets.json (the bishop family) so each phase has its
own offline snapshot and the test suites never touch the network.
"""
import json
import pathlib
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (OEIS target snapshot; low volume)"}
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets_phase2.json"

TARGETS = [
    "A298106",   # connected dominating sets, n X n torus
    "A295428",   # minimal dominating sets, n X n torus
    "A348000",   # minimal total dominating sets, n X n torus
    "A382530",   # minimum connected dominating sets, n X n torus
    "A303210",   # total dominating sets, n X n torus
    "A295429",   # connected minimal dominating sets, n X n torus
    "A347723",   # irredundant sets, n X n torus
    "A298124",   # connected induced subgraphs, n X n torus
]


def main():
    records = {}
    for aid in TARGETS:
        url = f"https://oeis.org/search?q=id:{aid}&fmt=json"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=60
        ) as r:
            doc = json.loads(r.read().decode("utf-8", "replace"))
        time.sleep(0.5)
        res = doc["results"][0] if isinstance(doc, dict) else doc[0]
        records[aid] = {
            "name": res.get("name", ""),
            "offset": res.get("offset", ""),
            "keyword": res.get("keyword", ""),
            "terms": [int(x) for x in res.get("data", "").split(",") if x.strip()],
        }
        r = records[aid]
        print(f"{aid} off={r['offset']:5s} n={len(r['terms']):2d} {r['name'][:56]}")
        print(f"      {r['terms']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=1, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {OUT} with {len(records)} sequences")


if __name__ == "__main__":
    main()
