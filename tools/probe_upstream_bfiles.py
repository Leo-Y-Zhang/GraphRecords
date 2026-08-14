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

It records the b-file's VALUES as well as its extent, because once a submission
is approved the interesting question flips: not "does our file go further than
upstream" but "does upstream now serve exactly what we staged". Both questions
are answered from this one snapshot.
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

# Probed on every run in addition to whatever is staged, because the gate leans
# on them:
#
#   A290941  the ANCHOR. Dominating sets of the n-triangular honeycomb bishop
#            graph, published to n=50 back in 2017. verify_all.py
#            checks our class grid against it far past anything brute force can
#            reach, which is the strongest evidence available that the grid is
#            the right graph. It is emphatically NOT a contribution target, and
#            neither is A304553 next to it: both are already at n=50, which is
#            exactly the misreading that wasted a day on A289164 and A295898.
#   A290783  the two honeycomb sequences this repo does extend. Their upstream
#   A381795  extent is recorded here so that "how far is this published" stays a
#            measurement in the repo rather than something someone remembers.
ALWAYS_PROBE = ("A290783", "A290941", "A381795")


def probe(aid):
    """Returns (rows, last_n, values) for the published b-file.

    values maps index -> term, so a later run can be compared against a staged
    file term by term rather than only by how far it reaches. Anything this
    probe cannot read is (None, None, None) - UNKNOWN, never absence, including
    a 404: absence is a claim, and this probe deliberately never makes it.
    """
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"https://oeis.org/{aid}/b{aid[1:]}.txt", headers=UA),
            timeout=45,
        ) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"  {aid}: probe failed ({exc}) - treating as UNKNOWN, not as absent")
        return None, None, None
    if "<html" in body[:200].lower():
        # An HTML body is the server answering with a page instead of a b-file:
        # an error, a rate limit or an interstitial. It is not the sequence
        # saying it has no b-file. Reporting 0 here asserts "nothing is published
        # upstream", which is exactly the claim that lets a submission take
        # credit for terms someone else published, so it is UNKNOWN.
        print(f"  {aid}: server returned HTML, not a b-file - treating as UNKNOWN, "
              f"not as absent")
        return None, None, None
    rows, values = 0, {}
    for ln in body.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split()
        if len(parts) < 2:
            # A row we cannot read is a b-file we cannot vouch for, and half a
            # b-file compared against a staged file would silently skip terms.
            print(f"  {aid}: unreadable b-file row {ln!r} - UNKNOWN")
            return None, None, None
        rows += 1
        values[int(parts[0])] = int(parts[1])
    if not values:
        # A 200 with a parseable but empty body is still not evidence of absence.
        print(f"  {aid}: b-file fetched but contained no index rows - UNKNOWN")
        return None, None, None
    return rows, max(values), values


def main():
    staged = {"A" + p.stem[1:] for p in STAGE.glob("b*.txt")}
    targets = sorted(staged | set(ALWAYS_PROBE))

    record = {}
    for aid in targets:
        rows, last_n, values = probe(aid)
        time.sleep(0.4)
        if rows is None:
            print(f"{aid}: UNKNOWN - rerun before trusting any staging decision")
            return 1
        record[aid] = {
            "rows": rows,
            "last_n": last_n,
            "values": {str(n): v for n, v in sorted(values.items())},
        }
        print(f"{aid}: published b-file has {rows} rows"
              + (f", up to n={last_n}" if last_n else " (no b-file)"))
        sys.stdout.flush()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # No sort_keys: it would order the per-index values as strings, putting
    # "10" before "2". Both levels are already written in the order we want -
    # targets are sorted above, indices are sorted per sequence.
    OUT.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
