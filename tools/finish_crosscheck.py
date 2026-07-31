"""Wait for the peeling cross-check, then record its verdict and commit it.

The operator should not have to sit and watch a 2-hour verification. This waits,
reads the result, writes it into SESSION_HANDOFF.md and PAPER.md, and commits and
pushes. It costs no Claude usage.

If the two algorithms DISAGREE it does not quietly carry on: it writes
CROSSCHECK-FAILED-READ-ME.txt into the repo root and into the home directory, and
leaves the staged b-files untouched for a human to judge.

Rewritten 2026-07-31. Review found three ways the previous version could publish
a claim the log does not support, and it commits and pushes unattended:

  1. crosscheck_running() failed OPEN. Any PowerShell hiccup produced stdout
     without "YES", which read as "finished", so a single failed poll ended the
     wait and published a verdict against a partial log. Now a poll that cannot
     answer returns None and the loop keeps waiting; only repeated confident
     NOs end it.
  2. The verdict was a substring grep. `"CROSSCHECK PASSED" in text` with the
     evidence block built as `"n=11" + (n11[0] if n11 else "")` would happily
     declare a(11) confirmed against an EMPTY evidence block. The log is now
     parsed structurally and a claim about a(n) requires that n's own block to
     be present and to say AGREE.
  3. The recorded sentence "Every staged term now rests on two independent
     algorithms" was hardcoded, not computed. This run covers n=10 and n=11 of
     ONE sequence; there are ten staged terms across five sequences, so that
     sentence was false regardless of what the computation returned. The verdict
     text is now generated from the blocks actually found, and says explicitly
     what the run does NOT cover.
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
BRANCH = "phase1-bishop-family"

# The n whose independent confirmation this run exists to establish.
TARGET_N = 11

BLOCK = re.compile(r"^n=(\d+)\s+(\S+)\s*$")


def crosscheck_running():
    """True / False / None. None means the question could not be answered.

    Returning None rather than False on failure is the whole point: the previous
    version treated "I could not tell" as "it has finished".
    """
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "if (Get-CimInstance Win32_Process -Filter \"Name LIKE '%python%'\" | "
             "Where-Object {$_.CommandLine -like '*crosscheck_peeling*'}) "
             "{ 'YES' } else { 'NO' }"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    s = out.stdout.strip()
    if "YES" in s:
        return True
    if "NO" in s:
        return False
    return None


def wait_for_finish():
    """Block until the cross-check is confidently gone.

    Requires two consecutive confident NOs so a one-off blip cannot end the wait.
    """
    confident_no = 0
    while confident_no < 2:
        state = crosscheck_running()
        if state is False:
            confident_no += 1
        else:
            # True, or None meaning we could not tell - either way, keep waiting.
            confident_no = 0
        time.sleep(30 if confident_no else 60)


def parse_log(text):
    """Return (blocks, terminal) from the cross-check output.

    blocks maps n -> {"colour": str, "agree": bool}
    terminal is "PASSED", "FAILED" or None when the run never reached its end.
    """
    blocks = {}
    current = None
    terminal = None
    for line in text.splitlines():
        m = BLOCK.match(line.strip())
        if m:
            current = int(m.group(1))
            blocks[current] = {"colour": m.group(2), "agree": None}
            continue
        if "CROSSCHECK PASSED" in line:
            terminal = "PASSED"
            continue
        if "CROSSCHECK FAILED" in line:
            terminal = "FAILED"
            continue
        if current is None:
            continue
        if "DISAGREE" in line:
            blocks[current]["agree"] = False
        elif "AGREE" in line:
            blocks[current]["agree"] = True
    return blocks, terminal


def git(*args):
    return subprocess.run(
        ["git", "-c", f"core.hooksPath={HOOKS}", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )


def commit_and_push(message):
    git("add", "-A")
    git("commit", "-m", message)
    return git("push", "-q", "origin", BRANCH)


def stop(kind, headline, detail, code):
    """Write the marker files for a non-confirming outcome, commit, push."""
    msg = f"{headline}\n\n{detail}\n"
    (ROOT / "CROSSCHECK-FAILED-READ-ME.txt").write_text(msg, encoding="utf-8")
    (HOME / f"THESEUS CROSSCHECK {kind} - READ ME.txt").write_text(msg, encoding="utf-8")
    commit_and_push(f"Cross check {kind.lower()} - a({TARGET_N}) is NOT confirmed")
    print(f"CROSS-CHECK {kind} - markers written")
    return code


def main():
    wait_for_finish()

    text = LOG.read_text(encoding="utf-8") if LOG.is_file() else ""
    blocks, terminal = parse_log(text)

    tail = "Full output:\n\n" + (text if text.strip() else "(the log file was empty or missing)")

    # The run never reached its own terminal line: it was killed, crashed, or is
    # still writing. Claim nothing either way.
    if terminal is None:
        return stop(
            "INCOMPLETE",
            "CROSS-CHECK DID NOT FINISH",
            "The cross-check process is gone but its output never reached the\n"
            "final CROSSCHECK line, so the run did not complete. No verdict has\n"
            f"been recorded in either direction: a({TARGET_N}) is NOT confirmed, and it is\n"
            "NOT refuted either. The staged b-files are untouched. Re-run\n"
            f"tools/crosscheck_peeling.py --from-n 10 --to-n {TARGET_N} to settle it.\n\n" + tail,
            2,
        )

    disagreed = [n for n, b in sorted(blocks.items()) if b["agree"] is False]
    if terminal == "FAILED" or disagreed:
        which = ", ".join(f"n={n}" for n in disagreed) or "an unreported n"
        return stop(
            "FAILED",
            "CROSS-CHECK DID NOT PASS",
            "The frontier partition DP and the exact-support peeling counter\n"
            f"DISAGREED at {which}. a({TARGET_N}) must NOT be treated as confirmed, and\n"
            "the staged b-files have been left exactly as they were for a human\n"
            "to judge.\n\n" + tail,
            1,
        )

    # Terminal says PASSED. Confirming a(TARGET_N) additionally requires that n's
    # own block to exist and to have agreed - a PASSED line alone is not evidence
    # about an n the run never reached.
    target = blocks.get(TARGET_N)
    if target is None or target["agree"] is not True:
        return stop(
            "INCOMPLETE",
            f"CROSS-CHECK PASSED BUT SAYS NOTHING ABOUT n={TARGET_N}",
            f"The run reported PASSED, but its output contains no agreeing n={TARGET_N}\n"
            f"block, so it cannot confirm a({TARGET_N}). Whatever it did verify may be\n"
            "sound; this specific claim is not established. The staged b-files\n"
            "are untouched.\n\n" + tail,
            2,
        )

    confirmed = [(n, b["colour"]) for n, b in sorted(blocks.items()) if b["agree"] is True]
    listed = "\n".join(f"  - n={n} ({colour})" for n, colour in confirmed)
    evidence = "\n".join(
        line for line in text.splitlines()
        if line.strip()
    )

    verdict = (
        "\n## Cross-check verdict (recorded automatically)\n\n"
        f"a({TARGET_N}) of A290719 is **independently confirmed**: the frontier partition\n"
        "DP and the exact-support peeling counter, which share no code path beyond\n"
        "the class grid, agree.\n\n"
        "This run compared the two algorithms at:\n\n"
        f"{listed}\n\n"
        "It establishes nothing about the other staged terms, which it did not\n"
        "cover; each of those rests on whatever verification is recorded for it\n"
        "separately.\n\n```\n" + evidence.strip() + "\n```\n"
    )
    for target_file in (ROOT / "SESSION_HANDOFF.md", ROOT / "PAPER.md"):
        target_file.write_text(
            target_file.read_text(encoding="utf-8") + verdict, encoding="utf-8"
        )

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
        f"Theseus: a({TARGET_N}) of A290719 independently confirmed by two independent\n"
        "algorithms (frontier partition DP vs exact-support peeling).\n\n"
        "Verified in this run:\n" + listed + "\n\n"
        "This says nothing about the other staged terms - it did not cover them.\n\n"
        + evidence,
        encoding="utf-8",
    )
    out = commit_and_push(f"Record the cross check verdict: a({TARGET_N}) independently confirmed")
    print("CROSS-CHECK PASSED - recorded, committed and pushed")
    print(out.stderr[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
