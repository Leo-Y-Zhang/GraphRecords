# OEIS-upload — SUBMITTED 2026-08-13 (see SESSION_HANDOFF.md for live status)

All five submissions went in on 2026-08-13, each pasted by the operator from this
staging (DATA + EXTENSIONS + one-line note, nothing else), and ALL FIVE WERE APPROVED
THE SAME DAY — all ten terms are live, verified off the published entries. The
files below are retained as the record of exactly what was staged. The original
rule stands for anything future: nothing goes without explicit per-submission
authorisation from the operator, from the operator's own account.

## The gate, in order

1. ~~A217058 must be ACCEPTED first.~~ **SATISFIED: A217058 was accepted
   2026-08-06.** The van der Waerden campaign in MathRecords was ahead of this
   work in the queue and the standing rule is one submission at a time,
   optimising for zero editor friction.
2. Then the remaining vdW terms, per that campaign's own plan.
3. Only then these. Five extensions arriving at once from a new contributor is
   exactly the friction the standing directive exists to avoid — land ONE, see
   how it is received, and ask an editor how they would like the rest.
   Lesson from the A217058 approval: the reviewing editor deleted the entire
   comment on acceptance, so offer the terms and an EXTENSIONS line only, and
   add nothing else unless an editor asks.

## What is staged, and what is actually new

Measured against each entry's **published b-file**, never its DATA line. OEIS
truncates DATA near 260 characters, so an entry can display 15 terms while
holding 50 — three sequences were staged here on that misreading and had to be
withdrawn.

    file            terms   n range   published to   genuinely new
    b290719.txt      11     1..11     n=9            a(10), a(11)
    b290769.txt      10     2..11     n=9            a(10), a(11)
    b291595.txt      11     1..11     n=9            a(10), a(11)
    b289145.txt      10     1..10     n=8            a(9),  a(10)
    b289169.txt       9     2..10     n=8            a(9),  a(10)

Ten new terms across five sequences. A290719/A290769/A291595 count connected
induced subgraphs of the black / white / full bishop graph; A289145/A289169 count
connected dominating sets of the black / white bishop graph.

## Before ANY paste, run both

    python verify_all.py                   # must exit 0
    python tools/probe_upstream_bfiles.py  # refresh the upstream snapshot

The probe reports UNKNOWN — not zero — when it cannot read a b-file (rate limit,
HTML error page, dropped connection). A test refuses to treat UNKNOWN as "nothing
is published upstream", because that is precisely the error that lets a
submission claim credit for someone else's terms.

## EXTENSIONS lines

Generated into `data/submission_pack.json`, and a test asserts each one starts
exactly one past the published b-file. Date them on the day of submission:

    A290719 / A290769 / A291595   a(10)-a(11) from _Leo Y. Zhang_, <date>
    A289145 / A289169             a(9)-a(10)  from _Leo Y. Zhang_, <date>

## House style, learned from the A217058 review — apply from the start

* US spelling (color, not colour; labeling, not labelling).
* Comments short, for a general reader, terms defined, roughly <= 600 chars.
  Be ready to drop the comment entirely if an editor objects; one already said
  "either write nothing at all, or write something concise".
* Full first names in LINKS, never initials.
* NEVER alter an existing line — underscores in names are OEIS link markup and
  have been destroyed by careless box edits before.
* Multi-paragraph comments use the `(Start)` / `(End)` wrapper, signed.
* No GitHub link. The operator does not want their legal name coupled to the
  handle in a permanent entry.
* Once an editor edits the draft, their version stands — never re-paste over it.

## b-file format

LF-only, no BOM, trailing newline, first index equal to the sequence's own
offset. `.gitattributes` pins this so a Windows checkout cannot silently rewrite
them to CRLF, and `tests/test_staged_bfiles.py` checks every file. A fresh clone
was verified on 2026-07-31 to still produce LF-only files.

## Honest note on confidence

**All ten staged terms carry independent confirmation as of 2026-08-01** — but
not all of the same kind, and the distinction should be stated plainly if an
editor asks. Seven terms are confirmed by a second algorithm that shares no code
path with the first beyond the class grid (frontier DP vs exact-support peeling);
three inherit through a structural identity — the even-n reflection isomorphism
for A290769 a(10), and black + white = bishop for A291595 a(10) and a(11) — each
identity verified against every published term of the sequence it governs.
`PAPER.md` section 4 holds the authoritative per-term table. Never restate this
as an aggregate claim of one uniform kind of evidence.
