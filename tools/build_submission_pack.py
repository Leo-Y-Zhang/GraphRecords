"""Build paste-ready OEIS submission material for the staged Theseus terms.

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


def upstream_bfile_rows(aid):
    """How many rows the published b-file has, or 0 if there is none."""
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"https://oeis.org/{aid}/b{aid[1:]}.txt", headers=UA),
            timeout=45,
        ) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception:
        return 0
    if "<html" in body[:200].lower():
        return 0
    return sum(1 for ln in body.splitlines() if ln.strip() and not ln.startswith("#"))


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

        upstream = 0 if args.offline else upstream_bfile_rows(aid)
        if not args.offline:
            time.sleep(0.4)

        out.append({
            "id": aid,
            "first_n": first_n,
            "last_n": values[-1][0],
            "total": len(values),
            "data_terms": fit,
            "upstream_bfile_rows": upstream,
            "data_line": ", ".join(str(v) for _, v in values[:fit]),
            "extensions": f"a({values[0][0] + fit}) onwards from _{AUTHOR}_, "
                          f"<DATE ON SUBMISSION DAY>",
            "description": DESCRIPTIONS.get(aid, ""),
        })
        print(f"{aid}  terms {len(values):>3d} (n={first_n}..{values[-1][0]})  "
              f"DATA holds {fit}  upstream b-file rows: {upstream}")
        sys.stdout.flush()

    (ROOT / "data" / "submission_pack.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8"
    )
    print(f"\nwrote data/submission_pack.json ({len(out)} sequences)")
    print("\nNOTE: this prepares only. Submitting is the operator's act, from the")
    print("operator's own OEIS account, and queues behind A217058 acceptance.")


if __name__ == "__main__":
    main()
