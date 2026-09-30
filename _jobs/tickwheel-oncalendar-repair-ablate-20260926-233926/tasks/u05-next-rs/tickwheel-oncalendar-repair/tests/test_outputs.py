"""Checks tickwheel against output recorded from systemd-analyze calendar
(systemd 252.39, TZ=UTC, "From now:" rows removed)."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
TARGET = Path("/tmp/tickwheel-verify-target")
BINARY = TARGET / "release" / "tickwheel"
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["groups"]


def _hide_reference_tools():
    for name in ("systemd-analyze",):
        while True:
            path = shutil.which(name)
            if not path:
                break
            os.rename(path, path + ".hidden-by-verifier")


FORBIDDEN_CODE = {
    "unsafe": re.compile(r"\bunsafe\b"),
    "extern": re.compile(r"\bextern\b"),
    "#[link]": re.compile(r"#\s*!?\s*\[\s*link\b"),
    "process::Command": re.compile(r"\bprocess\s*::\s*(?:Command\b|\{[^}]*\bCommand\b)"),
    "Command::new": re.compile(r"\bCommand\s*::\s*new\b"),
}


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _source_policy_problems():
    problems = []
    lock = (APP / "Cargo.lock").read_text(encoding="utf-8")
    packages = re.findall(r'^name = "([^"]+)"', lock, flags=re.M)
    if packages != ["tickwheel"]:
        problems.append(f"Cargo.lock lists packages other than tickwheel: {packages}")
    for rs in sorted(APP.rglob("*.rs")):
        rel = rs.relative_to(APP)
        if rel.parts[0] == "target":
            continue
        code = _strip_comments(rs.read_text(encoding="utf-8"))
        for name, pattern in FORBIDDEN_CODE.items():
            if pattern.search(code):
                problems.append(f"{rel} uses {name}")
    return problems


@pytest.fixture(scope="session")
def tickwheel():
    _hide_reference_tools()
    problems = _source_policy_problems()
    assert not problems, "source policy: " + "; ".join(problems)
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    build = subprocess.run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=APP, env=env, capture_output=True, text=True, timeout=1800,
    )
    assert build.returncode == 0, "cargo build failed:\n" + build.stderr[-4000:]
    assert BINARY.is_file()
    return str(BINARY)


def _run_case(binary, case):
    cmd = [binary, "calendar", f"--base-time={case['base']} UTC", f"--iterations={case['iterations']}", *case["exprs"]]
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "TZ": "UTC", "LC_ALL": "C"}
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    stderr = [line for line in p.stderr.splitlines() if line.startswith("Failed")]
    return p.returncode, p.stdout, stderr


def _check_group(binary, group):
    failures = []
    for case in CASES[group]:
        rc, out, err = _run_case(binary, case)
        if (rc, out, err) != (case["rc"], case["stdout"], case["stderr"]):
            failures.append(
                f"--- {case['exprs']} base={case['base']} iterations={case['iterations']}\n"
                f"expected rc={case['rc']} stderr={case['stderr']}\n{case['stdout']}"
                f"got rc={rc} stderr={err}\n{out}"
            )
    assert not failures, f"{len(failures)} of {len(CASES[group])} cases differ:\n" + "\n".join(failures)


def test_dst_gap(tickwheel):
    """Wall times skipped by a spring-forward change (30-minute and midnight changes included)."""
    _check_group(tickwheel, "dst_gap")


def test_dst_overlap(tickwheel):
    """Wall times that occur twice when clocks go back resolve to the right occurrence."""
    _check_group(tickwheel, "dst_overlap")


def test_offset_folding(tickwheel):
    """Schedules whose candidate folds back to or before the starting point still advance."""
    _check_group(tickwheel, "offset_folding")


def test_field_rollover(tickwheel):
    """Out-of-range candidates (minute 75, day 31 in a short month) roll over without skipping elapses."""
    _check_group(tickwheel, "field_rollover")


def test_end_of_month(tickwheel):
    """`~` day fields, including ranges and repetitions counted from the end of the month."""
    _check_group(tickwheel, "end_of_month")


def test_normalized_forms(tickwheel):
    """Normalized form printing: range ends, repetitions, weekday runs, fractions."""
    _check_group(tickwheel, "normalized_forms")


def test_two_digit_years(tickwheel):
    """Two-digit years map to 1970-2069."""
    _check_group(tickwheel, "two_digit_years")


def test_rejected_expressions(tickwheel):
    """Expressions systemd rejects produce the same error and exit status."""
    _check_group(tickwheel, "rejected_expressions")


def test_far_future_rules(tickwheel):
    """Instants after the last stored transition use the zone's footer rule."""
    _check_group(tickwheel, "far_future_rules")


def test_multi_expression_reports(tickwheel):
    """Several expressions per call: separators, partial failures and exit status."""
    _check_group(tickwheel, "multi_expression_reports")
