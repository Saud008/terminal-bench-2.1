#!/usr/bin/env python3
"""Local LLMaJ-style checks (Python heuristics) + optional harbor tasks check JSON.

Snorkel LLMaJ uses GPT-5.5 via `harbor tasks check`. This module adds:
  1. Static proxies for all seven LLMaJ check names (no API key required)
  2. Parses harbor JSON output when stb/harbor is on PATH

Called automatically from terminus_ci_check.py — user does not run manually.
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from terminus_ci_check import REPO_ROOT, Check, JOBS_LOCAL  # noqa: E402
from jobs_local_paths import jobs_path  # noqa: E402

LLMAJ_REPORT = jobs_path("llmaj-check-last.txt")
HARBOR_JSON = jobs_path("harbor-llmaj-last.json")

LLMAJ_IDS = (
    "behavior_in_task_description",
    "behavior_in_tests",
    "informative_test_docstrings",
    "anti_cheating_measures",
    "structured_data_schema",
    "hardcoded_solution",
    "file_reference_mentioned",
)

APP_PATH_RE = re.compile(r'["\'](/app/[a-zA-Z0-9_./-]+)["\']')
DOC_PATH_RE = re.compile(r"/app/docs/[a-zA-Z0-9_./-]+\.md")
OUTPUT_PATH_RE = re.compile(r"/app/(?:output|state|data)/[a-zA-Z0-9_./-]+")

ECHO_ONLY_RE = re.compile(
    r"^\s*(?:echo|printf)\s+.*>\s*(/app/|/output/)",
    re.I | re.M,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _test_py_files(task_dir: Path) -> list[Path]:
    files: list[Path] = []
    tests = task_dir / "tests"
    if tests.is_dir():
        files.extend(tests.glob("test_*.py"))
        if (tests / "test_outputs.py").is_file() and tests / "test_outputs.py" not in files:
            files.append(tests / "test_outputs.py")
    steps = task_dir / "steps"
    if steps.is_dir():
        for step_tests in sorted(steps.glob("milestone_*/tests")):
            files.extend(step_tests.glob("test_*.py"))
    return files


def _collect_test_paths(test_files: list[Path]) -> set[str]:
    paths: set[str] = set()
    for tf in test_files:
        text = _read(tf)
        paths.update(APP_PATH_RE.findall(text))
        paths.update(re.findall(r'Path\(\s*["\'](/app/[^"\']+)["\']', text))
    return paths


def _instruction_and_docs_text(task_dir: Path) -> str:
    parts = []
    inst = task_dir / "instruction.md"
    if inst.is_file():
        parts.append(_read(inst))
        for doc_ref in DOC_PATH_RE.findall(parts[0]):
            doc = task_dir / "environment" / doc_ref.replace("/app/", "")
            if doc.is_file():
                parts.append(_read(doc))
    if (task_dir / "steps").is_dir():
        for step_inst in (task_dir / "steps").rglob("instruction.md"):
            parts.append(_read(step_inst))
    return "\n".join(parts)


def check_informative_test_docstrings(task_dir: Path) -> Check:
    test_files = _test_py_files(task_dir)
    if not test_files:
        return Check(
            "informative_test_docstrings",
            "warn",
            False,
            "No test_*.py found",
            "Add tests with docstrings per test function",
        )

    missing: list[str] = []
    total = 0
    for tf in test_files:
        try:
            tree = ast.parse(_read(tf))
        except SyntaxError:
            return Check(
                "informative_test_docstrings",
                "block",
                False,
                f"Syntax error in {tf.name}",
                "Fix Python syntax in tests",
            )
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            total += 1
            doc = ast.get_docstring(node)
            if not doc or len(doc.strip()) < 8:
                missing.append(node.name)

    if total == 0:
        return Check(
            "informative_test_docstrings",
            "warn",
            False,
            "No test_* functions found",
            "Add pytest tests with docstrings",
        )

    ratio = len(missing) / total
    passed = ratio <= 0.2
    sev = "block" if ratio > 0.5 else "warn"
    msg = (
        f"{total - len(missing)}/{total} tests have docstrings"
        if passed
        else f"Missing docstrings: {missing[:6]}{'…' if len(missing) > 6 else ''}"
    )
    return Check(
        "informative_test_docstrings",
        sev if not passed else "block",
        passed,
        msg,
        "Add docstrings explaining which instruction requirement each test verifies",
    )


def check_file_reference_mentioned(task_dir: Path) -> Check:
    test_files = _test_py_files(task_dir)
    test_paths = _collect_test_paths(test_files)
    output_paths = {p for p in test_paths if "/output/" in p or p.startswith("/app/output")}
    if not output_paths:
        return Check(
            "file_reference_mentioned",
            "block",
            True,
            "No /app/output paths asserted in tests (or none needed)",
            "",
        )

    corpus = _instruction_and_docs_text(task_dir)
    missing = [p for p in sorted(output_paths) if p not in corpus]
    passed = not missing
    return Check(
        "file_reference_mentioned",
        "block",
        passed,
        "All tested output paths mentioned in instruction/docs"
        if passed
        else f"Output paths in tests but not instruction/docs: {missing[:5]}",
        "Name every tested output file path in instruction.md or a cited /app/docs/ file",
    )


def check_structured_data_schema(task_dir: Path) -> Check:
    test_files = _test_py_files(task_dir)
    uses_json = any(
        "json" in _read(tf).lower() or "schema" in _read(tf).lower() for tf in test_files
    )
    if not uses_json:
        return Check(
            "structured_data_schema",
            "block",
            True,
            "No JSON/schema assertions detected in tests",
            "",
        )

    corpus = _instruction_and_docs_text(task_dir)
    has_schema_pointer = bool(
        DOC_PATH_RE.search(corpus)
        or re.search(r"(?i)schema|format\.md|export-format|report-format", corpus)
    )
    return Check(
        "structured_data_schema",
        "block",
        has_schema_pointer,
        "Instruction or /app/docs cites schema"
        if has_schema_pointer
        else "Tests use JSON/schema but instruction/docs lack schema reference",
        "Point instruction to /app/docs/*-format.md or similar with field definitions",
    )


def check_hardcoded_solution(task_dir: Path) -> Check:
    solve = task_dir / "solution" / "solve.sh"
    if not solve.is_file():
        return Check("hardcoded_solution", "warn", True, "No solve.sh", "")

    text = _read(solve)
    echo_hits = ECHO_ONLY_RE.findall(text)
    build_hits = re.findall(
        r"(cargo build|go build|npm run build|make\b|mix compile|cp .+/app/)",
        text,
        re.I,
    )
    suspicious = len(echo_hits) >= 2 and len(build_hits) == 0
    only_echo = bool(re.search(r"echo\s+.*>\s*/app/(?:output|state)/", text, re.I)) and not build_hits

    passed = not (suspicious or only_echo)
    return Check(
        "hardcoded_solution",
        "block",
        passed,
        "solve.sh patches/builds (not echo-only)"
        if passed
        else "solve.sh may hardcode outputs (echo-only without build)",
        "Patch /app source and rebuild; avoid writing final artifacts with echo only",
    )


def check_anti_cheating_measures(task_dir: Path) -> Check:
    issues: list[str] = []
    env = task_dir / "environment"
    if env.is_dir():
        for bad in ("expected", "golden", "answer", "ground_truth"):
            for hit in env.rglob(f"*{bad}*"):
                if hit.is_file() and "fixture" not in str(hit).lower():
                    issues.append(f"suspicious env file: {hit.relative_to(task_dir)}")
                    break

    test_text = "\n".join(_read(f) for f in _test_py_files(task_dir))
    if re.search(r"open\([^)]*solution/", test_text, re.I):
        issues.append("tests reference solution/ path")

    if not re.search(r"subprocess|reference_|/opt/verifier", test_text, re.I):
        issues.append("tests may not execute CLI or independent reference (grep-only risk)")

    passed = len(issues) <= 1
    sev = "block" if len(issues) >= 2 else "warn"
    return Check(
        "anti_cheating_measures",
        sev if not passed else "block",
        passed,
        "OK" if passed else "; ".join(issues[:4]),
        "Use subprocess + independent reference_*; no golden answers in environment/",
    )


def check_behavior_in_task_description(task_dir: Path) -> Check:
    """Heuristic: tested /app/output paths and cited docs appear in instruction contract."""
    corpus = _instruction_and_docs_text(task_dir)
    test_paths = _collect_test_paths(_test_py_files(task_dir))
    critical = {p for p in test_paths if "/output/" in p or "/state/" in p}
    if not critical:
        return Check(
            "behavior_in_task_description",
            "warn",
            True,
            "No output/state paths in tests to cross-check",
            "",
        )

    missing = [p for p in sorted(critical) if p not in corpus]
    return Check(
        "behavior_in_task_description",
        "block",
        not missing,
        "Tested paths covered in instruction/docs"
        if not missing
        else f"Tested paths not in instruction/docs: {missing[:5]}",
        "Add behaviors and output paths to instruction.md or cited /app/docs/",
    )


def check_behavior_in_tests(task_dir: Path) -> Check:
    corpus = _instruction_and_docs_text(task_dir)
    outputs = set(OUTPUT_PATH_RE.findall(corpus))
    if not outputs:
        return Check(
            "behavior_in_tests",
            "warn",
            True,
            "No explicit /app/output paths in instruction",
            "",
        )

    test_paths = _collect_test_paths(_test_py_files(task_dir))
    # instruction paths should be tested OR be intermediate docs-only
    missing_tests = [p for p in sorted(outputs) if p not in test_paths]
    passed = len(missing_tests) <= 1
    return Check(
        "behavior_in_tests",
        "warn" if not passed else "block",
        passed,
        "Instruction output paths have test coverage"
        if passed
        else f"Instruction mentions outputs not clearly tested: {missing_tests[:5]}",
        "Add pytest coverage for each output path named in instruction",
    )


def run_llmaj_local(task_dir: Path) -> list[Check]:
    return [
        check_behavior_in_task_description(task_dir),
        check_behavior_in_tests(task_dir),
        check_informative_test_docstrings(task_dir),
        check_anti_cheating_measures(task_dir),
        check_structured_data_schema(task_dir),
        check_hardcoded_solution(task_dir),
        check_file_reference_mentioned(task_dir),
    ]


def run_harbor_llmaj(task_dir: Path) -> list[Check]:
    try:
        rel = task_dir.relative_to(REPO_ROOT)
    except ValueError:
        rel = task_dir

    out_json = jobs_path("harbor-llmaj-last.json", mkdir=True)

    candidates = [
        ["stb", "harbor", "tasks", "check", str(rel), "-m", "openai/@openai/gpt-5.5", "-o", str(out_json)],
        ["harbor", "tasks", "check", str(rel), "-m", "openai/@openai/gpt-5.5", "-o", str(out_json)],
    ]

    for cmd in candidates:
        if not shutil.which(cmd[0]):
            continue
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return [
                Check(
                    "harbor_llmaj",
                    "info",
                    False,
                    str(exc),
                    "",
                )
            ]

        checks: list[Check] = []
        if out_json.is_file():
            try:
                data = json.loads(out_json.read_text(encoding="utf-8"))
                checks.extend(_parse_harbor_json(data))
            except (json.JSONDecodeError, OSError):
                pass

        if not checks:
            out = (proc.stdout or "") + (proc.stderr or "")
            checks.append(
                Check(
                    "harbor_llmaj",
                    "block" if proc.returncode != 0 else "info",
                    proc.returncode == 0,
                    out.strip()[:600] or f"harbor exit {proc.returncode}",
                    "Fix harbor tasks check / LLMaJ failures",
                )
            )
        return checks

    return [
        Check(
            "harbor_llmaj",
            "info",
            True,
            "skipped — stb/harbor not on PATH (local LLMaJ heuristics still ran)",
            "",
        )
    ]


def _parse_harbor_json(data: object) -> list[Check]:
    """Best-effort parse of harbor tasks check JSON."""
    checks: list[Check] = []
    if not isinstance(data, dict):
        return checks

    # Common shapes: {checks: [{name, passed, message}]}, or flat LLMaJ keys
    items: list = []
    if isinstance(data.get("checks"), list):
        items = data["checks"]
    elif isinstance(data.get("results"), list):
        items = data["results"]

    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("id") or item.get("check") or "harbor_check")
        passed = item.get("passed")
        if passed is None:
            passed = item.get("success", item.get("ok", True))
        msg = str(item.get("message") or item.get("detail") or item.get("reason") or "")[:300]
        checks.append(
            Check(
                f"harbor_{name}",
                "block",
                bool(passed),
                msg or name,
                "See harbor-llmaj-last.json",
            )
        )

    for key in LLMAJ_IDS:
        if key in data and isinstance(data[key], dict):
            sub = data[key]
            passed = sub.get("passed", sub.get("success", True))
            checks.append(
                Check(
                    key,
                    "block",
                    bool(passed),
                    str(sub.get("message", sub.get("reason", key)))[:300],
                    "Fix per LLMaJ Checks Reference",
                )
            )

    return checks


def format_llmaj_report(task_dir: Path, checks: list[Check]) -> str:
    lines = [
        f"# LLMaJ check — {task_dir.name}",
        f"Path: {task_dir}",
        "",
    ]
    for lid in LLMAJ_IDS:
        hit = next((c for c in checks if c.id == lid), None)
        if hit:
            mark = "PASS" if hit.passed else hit.severity.upper()
            lines.append(f"- [{mark}] **{lid}**: {hit.message[:200]}")
    harbor = [c for c in checks if c.id.startswith("harbor_")]
    if harbor:
        lines.append("")
        lines.append("## Harbor LLMaJ")
        for c in harbor:
            mark = "PASS" if c.passed else "BLOCK"
            lines.append(f"- [{mark}] {c.id}: {c.message[:200]}")
    return "\n".join(lines)


def run_all_llmaj(task_dir: Path, *, harbor: bool = False) -> list[Check]:
    """Local instruction/test heuristics only. Harbor GPT LLMaJ is opt-in (API keys)."""
    checks = run_llmaj_local(task_dir)
    if harbor or os.environ.get("TERMINUS_LLMaj_HARBOR") == "1":
        checks.extend(run_harbor_llmaj(task_dir))
    JOBS_LOCAL.mkdir(parents=True, exist_ok=True)
    out = jobs_path("llmaj-check-last.txt", mkdir=True)
    out.write_text(format_llmaj_report(task_dir, checks), encoding="utf-8")
    return checks


def main() -> int:
    import argparse
    import sys

    from terminus_ci_check import locate_task_dir

    parser = argparse.ArgumentParser(description="LLMaJ local + harbor checks")
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument("--no-harbor", action="store_true")
    args = parser.parse_args()

    task_dir = locate_task_dir(args.task_dir)
    if not task_dir:
        print(f"ERROR: task not found: {args.task_dir}", file=sys.stderr)
        return 1

    checks = run_all_llmaj(task_dir, harbor=not args.no_harbor)
    blocks = [c for c in checks if c.severity == "block" and not c.passed]
    print(format_llmaj_report(task_dir, checks))
    print(f"\nReport: {LLMAJ_REPORT}")

    if args.pack_gate and blocks:
        return 1
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
