"""Wait for the peeling cross-check, then record its verdict and commit it.

The operator should not have to sit and watch a 2-hour verification. This waits,
reads the result, writes it into SESSION_HANDOFF.md and PAPER.md, and commits and
pushes. It costs no Claude usage.

If the two algorithms DISAGREE it does not quietly carry on: it writes
CROSSCHECK-FAILED-READ-ME.txt into the repo root and into the home directory, and
leaves the staged b-files untouched for a human to judge.
"""
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = ROOT / "bench" / "out" / "crosscheck.log"
HOME = pathlib.Path.home()
HOOKS = "C:/dev/Tools/githooks"


def crosscheck_running():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "if (Get-CimInstance Win32_Process -Filter \"Name LIKE '%python%'\" | "
         "Where-Object {$_.CommandLine -like '*crosscheck_peeling*'}) "
         "{ 'YES' } else { 'NO' }"],
        capture_output=True, text=True, timeout=60,
    )
    return "YES" in out.stdout


def git(*args):
    return subprocess.run(
        ["git", "-c", f"core.hooksPath={HOOKS}", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )


def main():
    while crosscheck_running():
        time.sleep(60)

    text = LOG.read_text(encoding="utf-8") if LOG.is_file() else ""
    n11 = [b for b in text.split("n=") if b.startswith("11 ")]
    passed = "CROSSCHECK PASSED" in text
    disagreed = "DISAGREE" in text

    if disagreed or not passed:
        msg = (
            "CROSS-CHECK DID NOT PASS\n\n"
            "The peeling counter and the frontier DP did not agree, or the run\n"
            "did not finish. a(11) must NOT be treated as confirmed, and the\n"
            "staged b-files have been left exactly as they were for a human to\n"
            "judge. Full output:\n\n" + text
        )
        (ROOT / "CROSSCHECK-FAILED-READ-ME.txt").write_text(msg, encoding="utf-8")
        (HOME / "THESEUS CROSSCHECK FAILED - READ ME.txt").write_text(msg, encoding="utf-8")
        git("add", "-A")
        git("commit", "-m", "Cross check did not pass - a(11) is NOT confirmed")
        git("push", "-q", "origin", "phase1-bishop-family")
        print("CROSS-CHECK FAILED - markers written")
        return 1

    block = "n=11" + (n11[0] if n11 else "")
    verdict = (
        "\n## Cross-check verdict (recorded automatically)\n\n"
        "a(11) of A290719 is **independently confirmed**: the frontier partition\n"
        "DP and the exact-support peeling counter, which share no code path beyond\n"
        "the class grid, agree. Every staged term now rests on two independent\n"
        "algorithms.\n\n```\n" + block.strip() + "\n```\n"
    )
    for target in (ROOT / "SESSION_HANDOFF.md", ROOT / "PAPER.md"):
        target.write_text(target.read_text(encoding="utf-8") + verdict, encoding="utf-8")

    # the paper's earlier caveat is now obsolete
    paper = ROOT / "PAPER.md"
    t = paper.read_text(encoding="utf-8")
    t = t.replace(
        "It is recorded here as computed, not as independently confirmed.",
        "It has since been independently confirmed - see the cross-check verdict "
        "at the end of this file.",
    )
    paper.write_text(t, encoding="utf-8")

    (HOME / "THESEUS CROSSCHECK PASSED - READ ME.txt").write_text(
        "Theseus: a(11) independently confirmed by two independent algorithms.\n"
        "All ten staged terms now rest on two algorithms each.\n\n" + block,
        encoding="utf-8",
    )
    git("add", "-A")
    git("commit", "-m", "Record the cross check verdict: a(11) independently confirmed")
    out = git("push", "-q", "origin", "phase1-bishop-family")
    print("CROSS-CHECK PASSED - recorded, committed and pushed")
    print(out.stderr[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
