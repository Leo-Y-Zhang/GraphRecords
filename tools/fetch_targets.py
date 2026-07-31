"""Snapshot every bishop-graph sequence from OEIS into data/targets.json.

Run once; the snapshot is committed and the tests read it offline so the suite
never depends on the network.
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (OEIS family snapshot; low volume)"}
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "targets.json"


def _fetch(url, attempts=3):
    """GET with backoff. Returns the body, or None if it could not be read."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60
            ) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:
            if attempt == attempts - 1:
                print(f"  giving up on {url}: {exc}")
                return None
            time.sleep(2 * (attempt + 1))


def search_all(query, cap=400):
    """Page an OEIS search 10 records at a time.

    A result count that is an exact multiple of the page size yields an empty
    body on the following request rather than a short page, so an unparseable or
    empty response is treated as the end of the results, not as an error.
    """
    out, start = [], 0
    while start < cap:
        url = (
            "https://oeis.org/search?q="
            + urllib.parse.quote(query)
            + f"&fmt=json&start={start}"
        )
        body = _fetch(url)
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
    for q in ('"bishop graph"', '"bishop graphs"'):
        for res in search_all(q):
            aid = "A%06d" % res["number"]
            records[aid] = {
                "name": res.get("name", ""),
                "offset": res.get("offset", ""),
                "keyword": res.get("keyword", ""),
                "author": res.get("author", ""),
                "terms": [int(x) for x in res.get("data", "").split(",") if x.strip()],
            }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT} with {len(records)} sequences")


if __name__ == "__main__":
    main()
