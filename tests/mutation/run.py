"""Run isolated, targeted mutations without ever rewriting production files.

Usage: python tests/mutation/run.py --phase both
Each child imports one module, replaces exactly one source fragment in one
function, and runs pytest. The before phase uses existing relevant fast tests;
the after phase adds the new tests. This is a targeted sample, not exhaustive
mutation coverage. The full, unmutated gate is run separately.
"""

import argparse
import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "results.json"

# (module, function, original fragment, replacement). Keep stable IDs so the
# report can identify a mutation even when source line numbers move.
MUTANTS = [
    ("independent_check", "check_certificate", "if set(mapping) != set(source):", "if False:"),
    ("independent_check", "check_certificate", "set(mapping) != set(source)",
     "not set(source) <= set(mapping)"),
    ("independent_check", "check_certificate", "if len(set(images)) != len(images):", "if False:"),
    ("independent_check", "check_certificate", "if set(images) != set(target):", "if False:"),
    ("independent_check", "check_certificate", "if adjacent(a, b) != share_a_line(mapping[a], "
     "mapping[b]):", "if False:"),
    ("independent_check", "check_bishop_certificate", "if coords is None:", "if not coords:"),
    ("independent_check", "check_honeycomb_certificate", "if coords is None:", "if not coords:"),
    ("reduction", "verify_isomorphism", "if len(set(coords.values())) != len(coords):",
     "if False:"),
    ("reduction", "verify_isomorphism", "if bishop_adjacent(a, b) != rook:", "if False:"),
    ("reduction", "verify_isomorphism", "== coords[b][0] or", "== coords[b][0] and"),
    ("brute", "minimal_dominating_count", "if not dominates(mask):", "if False:"),
    ("brute", "minimal_dominating_count", "minimal = False", "minimal = True"),
    ("brute", "minimal_dominating_count", "if dominates(mask ^ bit):",
     "if not dominates(mask ^ bit):"),
    ("brute", "minimal_dominating_count", "dominates(mask ^ bit)", "dominates(mask | bit)"),
    ("torus", "_cover", "covered |=", "covered &="),
    ("torus", "_connected", "return False", "return True"),
    ("torus", "_connected", "return seen == mask", "return seen != mask"),
    ("torus", "_connected", "reached & mask & ~seen", "reached & ~seen"),
    ("torus", "brute_connected_dominating", "== full and _connected", "== full or _connected"),
    ("torus", "brute_minimal_dominating", "minimal = False", "minimal = True"),
    ("probe_upstream_bfiles", "probe", "return None, None, None", "return 0, None, {}"),
    ("probe_upstream_bfiles", "probe", 'if "<html" in body[:200].lower():', "if False:"),
    ("probe_upstream_bfiles", "probe", 'print(f"  {aid}: unreadable b-file row {ln!r} - UNKNOWN")\n'
     "            return None, None, None", "continue"),
    ("probe_upstream_bfiles", "probe",
     'print(f"  {aid}: b-file fetched but contained no index rows '
     '- UNKNOWN")\n        return None, None, None', "return 0, None, {}"),
    ("probe_upstream_bfiles", "probe", "max(values)", "min(values)"),
    ("probe_upstream_bfiles", "probe", "rows += 1", "rows += 0"),
    ("targets", "bfile_terms_by_n", "int(n): int(v)", "n: int(v)"),
    ("targets", "bfile_terms_by_n", "int(n): int(v)", "int(n): v"),
    ("targets", "terms_by_n", "start + i", "start - i"),
    ("targets", "offset_start", '.split(",")[0]', '.split(",")[-1]'),
    ("connected", "_canonical", "remap = {0: 0}", "remap = {0: 1}"),
    ("connected", "_frontier_run", "(stranded and active)", "(stranded or active)"),
    ("domination", "_dominating_run", "if (r & done) & ~(h & done):", "if False:"),
    ("domination", "_inc2", "c >= 2", "c > 2"),
]

EXISTING = {
    "independent_check": ["tests/test_independent_check.py"],
    "reduction": ["tests/test_reduction.py", "tests/test_independent_check.py"],
    "brute": ["tests/test_brute.py::test_single_cell_board",
              "tests/test_brute.py::test_matches_published_black[3-22]"],
    "torus": ["tests/test_torus_profile.py::test_profile_agrees_with_brute_force[3]"],
    # No existing test imports the probe. Use an existing smoke test rather
    # than treating pytest's exit code 5 (nothing collected) as a kill.
    "probe_upstream_bfiles": ["tests/test_targets.py"],
    "targets": ["tests/test_targets.py",
                "tests/test_staged_bfiles.py::test_bfile_indices_and_published_terms",
                "tests/test_honeycomb.py::test_approved_terms_are_served_upstream_exactly_as_claimed"],
    "connected": [
        "tests/test_connected_frontier.py::test_agrees_with_the_peeling_counter[black-3]",
    ],
    "domination": ["tests/test_domination.py::test_agrees_with_brute_force[black-3]",
                   "tests/test_domination.py::test_total_agrees_with_brute_force[black-4]"],
}
ADDED = {
    "independent_check": "tests/test_certificate_boundaries.py",
    "reduction": "tests/test_certificate_boundaries.py",
    "brute": "tests/test_reference_counts.py",
    "torus": "tests/test_reference_counts.py",
    "probe_upstream_bfiles": "tests/test_upstream_probe.py",
    "targets": "tests/test_target_indexing.py",
    "domination": "tests/test_reference_counts.py",
}


def child(index, phase):
    # Imports below happen only in an isolated interpreter, before pytest
    # collects dependants with 'from module import function'.
    sys.path.insert(0, str(ROOT))
    import pytest

    name, function, old, new = MUTANTS[index]
    package = "tools" if name == "probe_upstream_bfiles" else "graphrecords"
    module = importlib.import_module(f"{package}.{name}")
    path = Path(module.__file__)
    source = path.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == function)
    lines = source.splitlines(keepends=True)
    fragment = "".join(lines[node.lineno - 1:node.end_lineno])
    # The exception-return mutation intentionally changes only the FIRST
    # return, i.e. the fetch-error branch; all other edits must be unique.
    expected = 4 if index == 20 else 1
    if fragment.count(old) != expected:
        raise RuntimeError(f"M{index + 1:02}: mutation anchor count changed")
    lines[node.lineno - 1:node.end_lineno] = [fragment.replace(old, new, 1)]
    exec(compile("".join(lines), str(path), "exec"), module.__dict__)
    selection = EXISTING[name] + ([ADDED[name]] if phase == "after" and name in ADDED else [])
    return int(pytest.main(["-q", "-x", "--tb=short", *selection]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["before", "after", "both"], default="both")
    parser.add_argument("--child", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child is not None:
        return child(args.child, args.phase)

    phases = ["before", "after"] if args.phase == "both" else [args.phase]
    records = json.loads(OUT.read_text()) if OUT.exists() else {}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    for phase in phases:
        for index, (module, function, old, new) in enumerate(MUTANTS):
            key = f"M{index + 1:02}"
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--phase", phase,
                 "--child", str(index)], cwd=ROOT, env=env,
                capture_output=True, text=True, timeout=60, check=False,
            )
            # Only a real test failure kills a mutant. Collection/import errors,
            # syntax errors, timeouts, and empty selections are audit failures.
            if result.returncode not in (0, 1) or (
                result.returncode == 1 and "FAILED " not in result.stdout
            ):
                print(result.stdout)
                print(result.stderr)
                raise RuntimeError(f"{key}: invalid mutation run, rc={result.returncode}")
            summary = [line for line in result.stdout.splitlines()
                       if " passed" in line or " failed" in line][-1]
            killed = result.returncode == 1
            record = records.setdefault(key, {
                "module": f"{'tools' if module == 'probe_upstream_bfiles' else 'graphrecords'}/"
                          f"{module}.py",
                "function": function, "original": old, "replacement": new,
            })
            record[phase] = {"killed": killed, "summary": summary,
                             "failures": [line for line in result.stdout.splitlines()
                                          if line.startswith("FAILED ")]}
            print(f"{key} {phase}: {'killed' if killed else 'survived'} — {summary}", flush=True)
        OUT.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
