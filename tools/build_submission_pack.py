"""Build paste-ready OEIS submission material for the staged GraphRecords terms.

Produces, per sequence: whether a b-file already exists upstream, the DATA line
truncated to what OEIS actually accepts, the EXTENSIONS line, and a comment in
the house style learned from the A217058 review.

House style, paid for once and applied here from the start:
  * US spelling
  * short comment written for a general reader, terms defined, roughly <= 600 chars
  * be ready to drop the comment entirely if an editor objects
  * full first names in LINKS, never initials
  * never alter an existing line
  * multi-paragraph comments use the (Start) / (End) wrapper
  * no GitHub link -- the operator does not want their legal name coupled to the
    handle in a permanent entry

This script PREPARES. It never submits: submitting is the operator's act, from
the operator's own OEIS account.
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "OEIS-upload"
UA = {"User-Agent": "Mozilla/5.0 (submission prep; low volume)"}

DATA_LIMIT = 260          # OEIS truncates the DATA line near this many chars
AUTHOR = "Leo Y. Zhang"

DESCRIPTIONS = {
    "A290719": "connected induced subgraphs of the black bishop graph",
    "A290769": "connected induced subgraphs of the white bishop graph",
    "A291595": "connected induced subgraphs of the bishop graph",
    "A289164": "dominating sets of the black bishop graph",
    "A289170": "dominating sets of the white bishop graph",
    "A295898": "dominating sets of the bishop graph",
    "A289145": "connected dominating sets of the black bishop graph",
    "A289169": "connected dominating sets of the white bishop graph",
}


def upstream_bfile(aid):
    """What OEIS already publishes: (rows, last_n), or (None, None) for UNKNOWN.

    Every failure here used to return 0, i.e. "there is no published b-file",
    i.e. "every staged term is new and ours". A dropped connection, a rate limit
    or an HTML error page therefore became positive evidence of absence, which
    is the single most dangerous direction for this script to be wrong in: it is
    what lets an EXTENSIONS line claim credit for terms somebody else published.
    Absence is now only reported when the server actually returns a parseable
    b-file that is empty of index rows; everything else is UNKNOWN and stops the
    run.
    """
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"https://oeis.org/{aid}/b{aid[1:]}.txt", headers=UA),
            timeout=45,
        ) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 0, None          # the server says there is no b-file
        print(f"  {aid}: HTTP {exc.code} - UNKNOWN, not absent")
        return None, None
    except Exception as exc:
        print(f"  {aid}: probe failed ({exc}) - UNKNOWN, not absent")
        return None, None
    if "<html" in body[:200].lower():
        print(f"  {aid}: server returned HTML, not a b-file - UNKNOWN, not absent")
        return None, None
    idx = [int(ln.split()[0]) for ln in body.splitlines()
           if ln.strip() and not ln.startswith("#")]
    if not idx:
        return 0, None
    return len(idx), max(idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="skip the upstream b-file probe")
    args = ap.parse_args()

    out = []
    for path in sorted(STAGE.glob("b*.txt")):
        aid = "A" + path.stem[1:]
        rows = [r.split() for r in path.read_text(encoding="ascii").split("\n") if r.strip()]
        values = [(int(a), int(b)) for a, b in rows]
        first_n = values[0][0]

        # how many terms fit in the DATA line
        fit, acc = 0, 0
        for _, v in values:
            piece = len(str(v)) + (2 if fit else 0)
            if acc + piece > DATA_LIMIT:
                break
            acc += piece
            fit += 1

        ours_last = values[-1][0]
        if args.offline:
            upstream, upstream_last = None, None
        else:
            upstream, upstream_last = upstream_bfile(aid)
            time.sleep(0.4)
            if upstream is None:
                raise SystemExit(
                    f"{aid}: could not establish what OEIS already publishes. "
                    f"Refusing to write a submission pack, because the only way to "
                    f"continue would be to assume nothing is published and claim "
                    f"credit for every staged term. Re-run when the network is "
                    f"available, or pass --offline to build a pack with no "
                    f"EXTENSIONS lines."
                )

        # The credit line names the terms this submission actually adds, so it is
        # derived from what is already published upstream. It used to be
        # `first_n + fit` -- the first index past the DATA line -- which is a
        # property of OEIS's 260-character DATA limit and says nothing whatever
        # about authorship. On a sequence whose published b-file already runs to
        # a(50), that wrote "a(16) onwards from <author>" and claimed 35 terms
        # somebody else had published.
        if args.offline:
            extensions = None
            note = "offline: upstream extent unknown, no EXTENSIONS line written"
        elif upstream_last is None:
            extensions = None
            note = ("no published b-file, so the published extent can only be read "
                    "off the OEIS DATA line by hand; do that before claiming credit")
        elif upstream_last >= ours_last:
            extensions = None
            note = (f"NOT A CONTRIBUTION: OEIS already publishes to n={upstream_last}, "
                    f"and the staged file stops at n={ours_last}")
        else:
            extensions = (f"a({upstream_last + 1})-a({ours_last}) from _{AUTHOR}_, "
                          f"<DATE ON SUBMISSION DAY>")
            note = f"adds a({upstream_last + 1})-a({ours_last})"

        out.append({
            "id": aid,
            "first_n": first_n,
            "last_n": ours_last,
            "total": len(values),
            "data_terms": fit,
            "upstream_bfile_rows": upstream,
            "upstream_last_n": upstream_last,
            "data_line": ", ".join(str(v) for _, v in values[:fit]),
            "extensions": extensions,
            "note": note,
            "description": DESCRIPTIONS.get(aid, ""),
        })
        print(f"{aid}  terms {len(values):>3d} (n={first_n}..{ours_last})  "
              f"DATA holds {fit}  upstream: "
              f"{'unknown' if upstream is None else upstream} rows"
              + (f", to n={upstream_last}" if upstream_last is not None else "")
              + f"  -> {note}")
        sys.stdout.flush()

    (ROOT / "data" / "submission_pack.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8"
    )
    print(f"\nwrote data/submission_pack.json ({len(out)} sequences)")
    print("\nNOTE: this prepares only. Submitting is the operator's act, from the")
    print("operator's own OEIS account, and queues behind A217058 acceptance.")


if __name__ == "__main__":
    main()
