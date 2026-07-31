"""Record how far each target's PUBLISHED b-file already goes.

This exists because of a real mistake. OEIS truncates the DATA line at roughly
260 characters, so an entry can display 15 terms while its uploaded b-file holds
50. The bishop shortlist was checked for that; the domination sequences were
picked up later from a grouped listing and were NOT, and three of them turned out
to be known to n=50 already. Six hours of compute produced verification rather
than new terms.

The snapshot this writes is consumed by tests/test_staged_bfiles.py, which
refuses to let a staged file count as a contribution unless it actually goes
beyond what is already published. Run this before staging anything, ever.
"""
import json
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"
OUT = ROOT / "data" / "upstream_bfiles.json"
UA = {"User-Agent": "Mozilla/5.0 (upstream b-file probe; low volume)"}


def probe(aid):
    """Returns (rows, last_n) for the published b-file, or (0, None) if none."""
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"https://oeis.org/{aid}/b{aid[1:]}.txt", headers=UA),
            timeout=45,
        ) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"  {aid}: probe failed ({exc}) - treating as UNKNOWN, not as absent")
        return None, None
    if "<html" in body[:200].lower():
        # An HTML body is the server answering with a page instead of a b-file:
        # an error, a rate limit or an interstitial. It is not the sequence
        # saying it has no b-file. Reporting 0 here asserts "nothing is published
        # upstream", which is exactly the claim that lets a submission take
        # credit for terms someone else published, so it is UNKNOWN.
        print(f"  {aid}: server returned HTML, not a b-file - treating as UNKNOWN, "
              f"not as absent")
        return None, None
    idx = [int(ln.split()[0]) for ln in body.splitlines()
           if ln.strip() and not ln.startswith("#")]
    if not idx:
        # A 200 with a parseable but empty body is still not evidence of absence.
        print(f"  {aid}: b-file fetched but contained no index rows - UNKNOWN")
        return None, None
    return len(idx), max(idx)


def main():
    targets = sorted("A" + p.stem[1:] for p in STAGE.glob("b*.txt"))
    if not targets:
        print("nothing staged")
        return 0

    record = {}
    for aid in targets:
        rows, last_n = probe(aid)
        time.sleep(0.4)
        if rows is None:
            print(f"{aid}: UNKNOWN - rerun before trusting any staging decision")
            return 1
        record[aid] = {"rows": rows, "last_n": last_n}
        print(f"{aid}: published b-file has {rows} rows"
              + (f", up to n={last_n}" if last_n else " (no b-file)"))
        sys.stdout.flush()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
