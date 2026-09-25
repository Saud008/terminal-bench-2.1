#!/usr/bin/env python3
"""Hard gate: all 8 unacceptable task classes must PASS before zip.

Policy: archive/terminus-rules-mdc/shared/unacceptable-task-classes.mdc
Zero tolerance — any class FAIL blocks pack (no partial allow).

  python3 scripts/unacceptable_class_gate.py --pack-gate --task-dir tasks/<name>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

REPORT_JSON = jobs_path("unacceptable-class-gate-last.json")
REPORT_TXT = jobs_path("unacceptable-class-gate-last.txt")

ALL_CLASSES = (
    "TEMPLATED",
    "COPY",
    "DUPLICATE",
    "FAMILY",
    "SAME_LANE",
    "SIBLING",
    "FABRICATED",
    "SYNTHETIC",
)

# Stricter than pack anti-spam alone — no WARN-only pass for similarity classes.
SIBLING_SIM_FAIL = 0.65
TEMPLATED_SIM_FAIL = 0.65
COPY_SIM_FAIL = 0.75
COPY_SIM_WARN = 0.50


@dataclass
class ClassResult:
    class_id: str
    status: str  # PASS | FAIL
    reason: str = ""


@dataclass
class GateReport:
    slug: str
    verdict: str
    classes: list[ClassResult] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def audit_line(self) -> str:
        if self.verdict == "PASS":
            return f"Unacceptable-class: PASS — all 8 classes clear — {self.slug}"
        fail_list = ",".join(self.failed)
        return f"Unacceptable-class: FAIL — {self.slug} — blocked: {fail_list}"


def _load_platform_slugs() -> set[str]:
    path = REPO_ROOT / "scripts" / "platform_submissions.txt"
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.split()[0])
    return out


def _first_submit_record(slug: str) -> dict | None:
    path = resolve_jobs_path(f"first-submit-{slug}.json")
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _is_milestone(task_dir: Path) -> bool:
    return (task_dir / "steps").is_dir() and (task_dir / "task.toml").is_file()


def _audit_solve_script(solve: Path, task_dir: Path) -> str | None:
    body = solve.read_text(encoding="utf-8", errors="replace")
    lower = body.lower()
    rel = solve.relative_to(task_dir)
    if re.search(r"\b(curl|wget|pip install|npm install|mix deps\.|cargo fetch)\b", lower):
        return f"{rel} uses network/install (oracle must be offline)"
    echo_out = len(re.findall(r"\becho\b[^;\n]*>\s*/", body))
    has_real_fix = bool(
        re.search(r"\b(cp|patch|apply|cargo build|go build|make\b|mix compile|npm run build)\b", lower)
    )
    if echo_out >= 2 and not has_real_fix:
        return f"{rel} appears echo-only golden output (no patch/build)"
    if echo_out >= 1 and not has_real_fix and "solve" in lower and len(body.splitlines()) < 15:
        return f"{rel} too thin — likely hardcoded artifact write"
    return None


def _audit_fabricated(task_dir: Path) -> str | None:
    if _is_milestone(task_dir):
        solves = sorted((task_dir / "steps").glob("milestone_*/solution/solve*.sh"))
        if not solves:
            return "milestone task missing steps/milestone_*/solution/solve*.sh"
        for solve in solves:
            err = _audit_solve_script(solve, task_dir)
            if err:
                return err
    else:
        solve = task_dir / "solution" / "solve.sh"
        if not solve.is_file():
            return "missing solution/solve.sh"
        err = _audit_solve_script(solve, task_dir)
        if err:
            return err

    env = task_dir / "environment"
    if env.is_dir():
        for path in env.rglob("*"):
            if not path.is_file() or path.suffix in (".png", ".jpg", ".gif", ".zip", ".tar", ".gz"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"\bBUG\s*:", text) or re.search(r"TODO:\s*fix", text, re.I):
                return f"environment leak/hint: {path.relative_to(task_dir)}"
            if re.search(r"expected[_\s-]?output|golden[_\s-]?json|answer[_\s-]?key", text, re.I):
                return f"ground truth in environment: {path.relative_to(task_dir)}"
    return None


DOC_PATH_RE = re.compile(r"/app/(?:docs|contracts|charter)/[^\s\)]+\.md")


def _count_doc_paths(text: str) -> int:
    return len(DOC_PATH_RE.findall(text))


def _audit_synthetic(task_dir: Path, slug: str, on_platform: bool) -> str | None:
    if _is_milestone(task_dir):
        doc_hits = 0
        for inst in sorted((task_dir / "steps").glob("milestone_*/instruction.md")):
            doc_hits += _count_doc_paths(inst.read_text(encoding="utf-8", errors="replace"))
        if doc_hits < 3:
            return f"milestone instructions cite {doc_hits} /app/docs, /app/contracts, or /app/charter paths (need ≥3 — decorative / shallow)"
        tests = sorted((task_dir / "steps").glob("milestone_*/tests/test_m*.py"))
        if not tests:
            return "milestone task missing steps/milestone_*/tests/test_m*.py"
        for test_py in tests:
            body = test_py.read_text(encoding="utf-8", errors="replace")
            if "reference_" not in body and "def reference" not in body.lower():
                return f"{test_py.relative_to(task_dir)} lacks independent reference_* (grep-only / shallow)"
            if "subprocess" not in body:
                return f"{test_py.relative_to(task_dir)} lacks subprocess CLI execution"
        return None

    inst = task_dir / "instruction.md"
    if inst.is_file():
        doc_hits = _count_doc_paths(inst.read_text(encoding="utf-8", errors="replace"))
        if doc_hits < 3:
            return f"instruction cites {doc_hits} /app/docs, /app/contracts, or /app/charter paths (need ≥3 — decorative / shallow)"

    tests = task_dir / "tests" / "test_outputs.py"
    if tests.is_file():
        body = tests.read_text(encoding="utf-8", errors="replace")
        if "reference_" not in body and "def reference" not in body.lower():
            return "tests lack independent reference_* (grep-only / shallow)"
        if body.count("def test_") >= 40 and "subprocess" not in body:
            return "high test count without subprocess CLI execution (inflated pytest)"
    else:
        return "missing tests/test_outputs.py"

    if not on_platform:
        rec = _first_submit_record(slug)
        if rec is None:
            return "no Phase F′ record (jobs-local/first-submit-<slug>.json) — synthetic risk unverified"
        if str(rec.get("verdict", "")).upper() != "PASS":
            return "Phase F′ record verdict not PASS"
        probes = rec.get("probes") or {}
        p1 = probes.get("1_single_file") or probes.get("1")
        status = p1.get("status", p1) if isinstance(p1, dict) else p1
        if str(status).upper() != "PASS":
            return "probe 1 (single-file patch depth) not PASS — synthetic / shallow bugs"
    return None


def run_gate(task_dir: Path) -> GateReport:
    try:
        from terminus_anti_spam_check import (
            build_all_fingerprints,
            build_all_metadata,
            check_one,
            load_all_submission_slugs,
        )
        from anti_spam_pipeline import classify_unacceptable_classes
    except ImportError:
        from scripts.terminus_anti_spam_check import (  # type: ignore[no-redef]
            build_all_fingerprints,
            build_all_metadata,
            check_one,
            load_all_submission_slugs,
        )
        from scripts.anti_spam_pipeline import classify_unacceptable_classes  # type: ignore[no-redef]

    slug = task_dir.name
    platform = load_all_submission_slugs(REPO_ROOT / "scripts" / "platform_submissions.txt")
    on_platform = slug in platform

    all_fps = build_all_fingerprints()
    all_meta = build_all_metadata()
    fp = all_fps.get(slug)
    spam = check_one(slug, all_fps, platform, all_meta=all_meta)

    shared_family = False
    if spam.nearest and fp and spam.nearest in all_fps:
        shared_family = bool(set(fp.families) & set(all_fps[spam.nearest].families))

    script_classes = set(
        classify_unacceptable_classes(
            blockers=spam.blockers,
            warnings=spam.warnings,
            similarity=spam.similarity,
            shared_family_neighbor=shared_family,
        )
    )

    fail_reasons: dict[str, str] = {}

    for c in script_classes:
        fail_reasons[c] = "; ".join(spam.blockers[:2]) or "anti-spam blocker"

    if spam.similarity >= TEMPLATED_SIM_FAIL:
        fail_reasons["TEMPLATED"] = f"similarity {spam.similarity} ≥ {TEMPLATED_SIM_FAIL}"
    if shared_family and spam.similarity >= SIBLING_SIM_FAIL:
        fail_reasons["SIBLING"] = (
            f"same-family neighbor tasks/{spam.nearest} sim {spam.similarity} ≥ {SIBLING_SIM_FAIL}"
        )
    if spam.similarity >= COPY_SIM_FAIL or (
        spam.similarity >= COPY_SIM_WARN and len(spam.structural_diffs) < 2
    ):
        fail_reasons["COPY"] = (
            f"similarity {spam.similarity} with <2 structural diffs vs tasks/{spam.nearest}"
        )
    for w in spam.warnings:
        wl = w.lower()
        if "moderate similarity" in wl or "high structural similarity" in wl:
            fail_reasons.setdefault("TEMPLATED", w)
            if shared_family:
                fail_reasons.setdefault("SIBLING", w)
        if "fewer than 2 structural diffs" in wl:
            fail_reasons.setdefault("COPY", w)

    if spam.status == "WARN":
        fail_reasons.setdefault(
            "TEMPLATED",
            f"anti-spam WARN not allowed — zero tolerance (nearest sim {spam.similarity})",
        )

    fab = _audit_fabricated(task_dir)
    if fab:
        fail_reasons["FABRICATED"] = fab

    syn = _audit_synthetic(task_dir, slug, on_platform)
    if syn:
        fail_reasons["SYNTHETIC"] = syn

    classes: list[ClassResult] = []
    failed: list[str] = []
    for class_id in ALL_CLASSES:
        if class_id in fail_reasons:
            classes.append(ClassResult(class_id, "FAIL", fail_reasons[class_id]))
            failed.append(class_id)
        else:
            classes.append(ClassResult(class_id, "PASS", "clear"))

    verdict = "PASS" if not failed else "FAIL"
    return GateReport(slug=slug, verdict=verdict, classes=classes, failed=failed)


def write_reports(report: GateReport) -> None:
    report_json = jobs_path("unacceptable-class-gate-last.json", mkdir=True)
    report_txt = jobs_path("unacceptable-class-gate-last.txt", mkdir=True)
    payload = {
        "slug": report.slug,
        "verdict": report.verdict,
        "failed_classes": report.failed,
        "classes": [asdict(c) for c in report.classes],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "policy": "shared/unacceptable-task-classes.mdc",
    }
    report_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [report.audit_line()]
    for c in report.classes:
        if c.status == "FAIL":
            lines.append(f"  FAIL {c.class_id}: {c.reason}")
    report_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_pack_gate(task_dir: Path, *, quiet: bool = False) -> int:
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1
    report = run_gate(task_dir)
    write_reports(report)
    if not quiet:
        print(report.audit_line())
        for c in report.classes:
            if c.status == "FAIL":
                print(f"  FAIL {c.class_id}: {c.reason}", file=sys.stderr)
    elif report.verdict == "FAIL":
        print(report.audit_line(), file=sys.stderr)
        for c in report.classes:
            if c.status == "FAIL":
                print(f"  FAIL {c.class_id}: {c.reason}", file=sys.stderr)
    if report.verdict == "FAIL":
        print(
            "  fix: redesign task — none of TEMPLATED,COPY,DUPLICATE,FAMILY,SAME_LANE,"
            "SIBLING,FABRICATED,SYNTHETIC may FAIL (see unacceptable-task-classes.mdc)",
            file=sys.stderr,
        )
        print(f"  report: {REPORT_JSON.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="All 8 unacceptable classes must PASS before zip")
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument("--task-dir", type=Path)
    parser.add_argument("--task-name", type=str)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    task_dir = args.task_dir
    if task_dir is None and args.task_name:
        for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
            candidate = base / args.task_name
            if candidate.is_dir():
                task_dir = candidate
                break
    if task_dir is None:
        parser.error("--task-dir or --task-name required")

    report = run_gate(task_dir.resolve())
    write_reports(report)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.verdict == "PASS" else 1
    if args.pack_gate:
        return cmd_pack_gate(task_dir.resolve(), quiet=args.quiet)
    print(report.audit_line())
    for c in report.classes:
        mark = "FAIL" if c.status == "FAIL" else "PASS"
        print(f"  {mark} {c.class_id}: {c.reason or 'clear'}")
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
