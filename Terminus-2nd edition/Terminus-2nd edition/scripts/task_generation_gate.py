#!/usr/bin/env python3
"""Hard gate: 7/7 acceptance checks — no debugging, no software-engineering (task-generation-mandatory.mdc).

Zip is blocked unless all checks PASS.

  python3 scripts/task_generation_gate.py --pack-gate --task-dir tasks/<name>

Override (user explicit only): TERMINUS_TASK_GENERATION_SKIP=1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jobs_local_paths import jobs_path  # noqa: E402
from task_generation_policy import (  # noqa: E402
    FAIL_FIX_RULE,
    FORBIDDEN_REPAIR_RULE,
    HARD_CHECK_LABELS,
    REPOSITORY_STATE_RULE,
    RULE,
    audit_idea_text,
    audit_task_dir,
)

REPORT_JSON = jobs_path("task-generation-gate-last.json")
REPORT_TXT = jobs_path("task-generation-gate-last.txt")


@dataclass
class GateReport:
    slug: str
    verdict: str  # PASS | FAIL | REGENERATE
    violations: list[str] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)
    context: str = "task"
    regenerate_required: bool = False
    regenerate_reasons: list[str] = field(default_factory=list)

    def audit_line(self) -> str:
        passed = sum(1 for v in self.checks.values() if v == "PASS")
        total = len(HARD_CHECK_LABELS)
        if self.verdict == "PASS":
            return (
                f"Task-generation: PASS — hard acceptance {passed}/{total} — "
                f"no debugging / no software-engineering — {self.slug or self.context}"
            )
        prefix = "REGENERATE" if self.verdict == "REGENERATE" else "FAIL"
        head = self.violations[0] if self.violations else "hard acceptance failed"
        extra = f" (+{len(self.violations) - 1} more)" if len(self.violations) > 1 else ""
        return (
            f"Task-generation: {prefix} — {passed}/{total} checks — "
            f"{self.slug or self.context} — {head}{extra}"
        )


def _audit_to_report(audit, *, slug: str, context: str) -> GateReport:
    if audit.passed:
        verdict = "PASS"
    elif audit.regenerate_required:
        verdict = "REGENERATE"
    else:
        verdict = "FAIL"
    return GateReport(
        slug=slug,
        verdict=verdict,
        violations=list(audit.violations),
        checks=dict(audit.checks),
        context=context,
        regenerate_required=audit.regenerate_required,
        regenerate_reasons=list(audit.regenerate_reasons),
    )


def write_reports(report: GateReport) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": report.slug,
        "verdict": report.verdict,
        "violations": report.violations,
        "checks": report.checks,
        "check_labels": HARD_CHECK_LABELS,
        "context": report.context,
        "policy": RULE,
        "repository_state_policy": REPOSITORY_STATE_RULE,
        "fail_fix_rule": FAIL_FIX_RULE,
        "forbidden_repair_rule": FORBIDDEN_REPAIR_RULE,
        "regenerate_required": report.regenerate_required,
        "regenerate_reasons": report.regenerate_reasons,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [report.audit_line(), "", "Hard acceptance checks:"]
    for cid, label in HARD_CHECK_LABELS.items():
        status = report.checks.get(cid, "FAIL: not run")
        lines.append(f"  {cid} {label}: {status}")
    for v in report.violations:
        lines.append(f"  - {v}")
    REPORT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_task_gate(task_dir: Path) -> GateReport:
    audit = audit_task_dir(task_dir)
    return _audit_to_report(audit, slug=task_dir.name, context="task")


def run_idea_gate(*, title: str, domain: str, summary: str, slug: str = "") -> GateReport:
    audit = audit_idea_text(title=title, domain=domain, summary=summary, slug=slug)
    label = slug or title[:40] or "idea"
    return _audit_to_report(audit, slug=label, context="idea")


def cmd_pack_gate(task_dir: Path, *, quiet: bool = False) -> int:
    if os.environ.get("TERMINUS_TASK_GENERATION_SKIP") == "1":
        if not quiet:
            print("Task-generation: SKIP (TERMINUS_TASK_GENERATION_SKIP=1)")
        return 0
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1
    report = run_task_gate(task_dir.resolve())
    write_reports(report)
    stream = sys.stderr if report.verdict == "FAIL" else sys.stdout
    if not quiet or report.verdict == "FAIL":
        print(report.audit_line(), file=stream)
        for cid, label in HARD_CHECK_LABELS.items():
            status = report.checks.get(cid, "FAIL")
            if status != "PASS":
                print(f"  {cid} {label}: {status}", file=stream)
        for v in report.violations:
            print(f"  - {v}", file=stream)
    if report.verdict in ("FAIL", "REGENERATE"):
        if report.verdict == "REGENERATE":
            print(
                f"  VERDICT: REGENERATE — repair/debug objective forbidden — "
                f"{FORBIDDEN_REPAIR_RULE}",
                file=sys.stderr,
            )
            print(
                "  Do not patch in place — new slug + build-on-working-baseline scenario.",
                file=sys.stderr,
            )
        print(
            f"  FAIL → fix in place: {FAIL_FIX_RULE}",
            file=sys.stderr,
        )
        print(
            "  fix: reframe — functional repo + NEW capability (security, provenance, "
            "scientific analysis, build governance). No debugging. No software-engineering. "
            f"Policy: {RULE}",
            file=sys.stderr,
        )
        print("  no zip until hard acceptance 7/7 PASS", file=sys.stderr)
        print(f"  report: {REPORT_JSON.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hard acceptance 7/7 — no debugging / no software-engineering"
    )
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument("--check-idea", action="store_true")
    parser.add_argument("--task-dir", type=Path)
    parser.add_argument("--task-name", type=str)
    parser.add_argument("--title", type=str, default="")
    parser.add_argument("--domain", type=str, default="")
    parser.add_argument("--summary", type=str, default="")
    parser.add_argument("--slug", type=str, default="")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.check_idea:
        report = run_idea_gate(
            title=args.title,
            domain=args.domain,
            summary=args.summary,
            slug=args.slug,
        )
        write_reports(report)
        if args.json:
            print(json.dumps(asdict(report), indent=2))
        else:
            print(report.audit_line())
            for cid, label in HARD_CHECK_LABELS.items():
                status = report.checks.get(cid, "FAIL")
                if status != "PASS":
                    print(f"  {cid} {label}: {status}")
        return 0 if report.verdict == "PASS" else 1

    task_dir = args.task_dir
    if task_dir is None and args.task_name:
        for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
            candidate = base / args.task_name
            if candidate.is_dir():
                task_dir = candidate
                break
    if task_dir is None:
        parser.error("--task-dir or --task-name required (or use --check-idea)")

    if args.pack_gate:
        return cmd_pack_gate(task_dir.resolve(), quiet=args.quiet)

    report = run_task_gate(task_dir.resolve())
    write_reports(report)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(report.audit_line())
        for v in report.violations:
            print(f"  - {v}")
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
