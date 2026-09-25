#!/usr/bin/env python3
"""Repository state + task-generation gate — 7/7 hard acceptance before zip.

Functional · buildable · consistent baseline; agent adds NEW capability (not find-and-fix).

Policy: shared/repository-state-requirement.mdc
On FAIL: shared/repository-state-fail-fix.mdc (LOCKED fix procedure)

  python3 scripts/repository_state_gate.py --pack-gate --task-dir tasks/<name>
  python3 scripts/repository_state_gate.py --check-idea --title "..." --domain "..." --summary "..."

Override (user explicit only): TERMINUS_TASK_GENERATION_SKIP=1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jobs_local_paths import jobs_path  # noqa: E402
from task_generation_gate import (  # noqa: E402
    GateReport,
    run_idea_gate,
    run_task_gate,
    write_reports as write_tg_reports,
)
from task_generation_policy import (  # noqa: E402
    FAIL_FIX_RULE,
    FORBIDDEN_REPAIR_RULE,
    HARD_CHECK_LABELS,
    REPOSITORY_STATE_RULE,
    RULE,
)

REPORT_JSON = jobs_path("repository-state-gate-last.json")
REPORT_TXT = jobs_path("repository-state-gate-last.txt")


def format_checks_table(report: GateReport) -> str:
    lines = ["| Check | PASS / FAIL |", "|-------|-------------|"]
    for cid, label in HARD_CHECK_LABELS.items():
        raw = report.checks.get(cid, "FAIL: not run")
        status = "PASS" if raw == "PASS" else "FAIL"
        lines.append(f"| {cid} — {label} | {status} |")
    lines.append(f"| **Verdict** | **{report.verdict}** |")
    return "\n".join(lines)


def write_repository_reports(report: GateReport) -> None:
    write_tg_reports(report)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": report.slug,
        "verdict": report.verdict,
        "violations": report.violations,
        "checks": report.checks,
        "check_labels": HARD_CHECK_LABELS,
        "context": report.context,
        "policy": REPOSITORY_STATE_RULE,
        "task_generation_policy": RULE,
        "fail_fix_rule": FAIL_FIX_RULE,
        "forbidden_repair_rule": FORBIDDEN_REPAIR_RULE,
        "regenerate_required": report.regenerate_required,
        "regenerate_reasons": report.regenerate_reasons,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        report.audit_line().replace("Task-generation:", "Repository-state:"),
        "",
        "Hard acceptance (repository state + no debugging/SE):",
    ]
    for cid, label in HARD_CHECK_LABELS.items():
        status = report.checks.get(cid, "FAIL: not run")
        lines.append(f"  {cid} {label}: {status}")
    if report.verdict == "FAIL":
        lines.extend(
            [
                "",
                f"FAIL → fix in place per {FAIL_FIX_RULE}",
                f"Report: {REPORT_JSON.relative_to(REPO_ROOT)}",
            ]
        )
        for v in report.violations:
            lines.append(f"  - {v}")
    REPORT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_fail_guidance(report: GateReport, *, stream) -> None:
    if report.verdict == "REGENERATE":
        print(
            f"  VERDICT: REGENERATE — {FORBIDDEN_REPAIR_RULE}",
            file=stream,
        )
        print(
            "  Repair/debug primary objective — regenerate task (new slug, new scenario).",
            file=stream,
        )
    print(
        f"  FAIL → fix: {FAIL_FIX_RULE}",
        file=stream,
    )
    print(
        "  Reframe: functional /app + NEW capability (build subsystem, workflow, "
        "analysis). Not find-and-fix.",
        file=stream,
    )
    print(f"  report: {REPORT_JSON.relative_to(REPO_ROOT)}", file=stream)


def cmd_pack_gate(task_dir: Path, *, quiet: bool = False) -> int:
    if os.environ.get("TERMINUS_TASK_GENERATION_SKIP") == "1":
        if not quiet:
            print("Repository-state: SKIP (TERMINUS_TASK_GENERATION_SKIP=1)")
        return 0
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1
    report = run_task_gate(task_dir.resolve())
    write_repository_reports(report)
    stream = sys.stderr if report.verdict in ("FAIL", "REGENERATE") else sys.stdout
    if not quiet or report.verdict in ("FAIL", "REGENERATE"):
        line = report.audit_line().replace("Task-generation:", "Repository-state:")
        print(line, file=stream)
        for cid, label in HARD_CHECK_LABELS.items():
            status = report.checks.get(cid, "FAIL")
            if status != "PASS":
                print(f"  {cid} {label}: {status}", file=stream)
        for v in report.violations:
            print(f"  - {v}", file=stream)
        if not quiet and report.verdict == "PASS":
            print(format_checks_table(report))
    if report.verdict in ("FAIL", "REGENERATE"):
        _print_fail_guidance(report, stream=sys.stderr)
        return 1
    return 0


def cmd_check_idea(
    *,
    title: str,
    domain: str,
    summary: str,
    slug: str = "",
    quiet: bool = False,
    as_json: bool = False,
) -> int:
    report = run_idea_gate(title=title, domain=domain, summary=summary, slug=slug)
    write_repository_reports(report)
    if as_json:
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.verdict == "PASS" else 1
    if not quiet:
        print(report.audit_line().replace("Task-generation:", "Repository-state (idea):"))
        if report.verdict == "FAIL":
            _print_fail_guidance(report, stream=sys.stderr)
        else:
            print(format_checks_table(report))
    return 0 if report.verdict == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Repository state gate — 7/7 hard acceptance")
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
        return cmd_check_idea(
            title=args.title,
            domain=args.domain,
            summary=args.summary,
            slug=args.slug,
            quiet=args.quiet,
            as_json=args.json,
        )

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
    write_repository_reports(report)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(report.audit_line())
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
