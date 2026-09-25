#!/usr/bin/env python3
"""Post-create audit loop — static checks with High/Medium/Low severity (CREATE Phase E).

Runs after Phase D. Agent still runs semantic audit (prompts/audit.md trio).

  python3 scripts/post_create_audit_loop.py --task-dir tasks/<name> --round 1
  python3 scripts/post_create_audit_loop.py --task-dir tasks/<name> --pack-gate

Reports: jobs-local/post-create-audit-last.json, post-create-audit-last.txt
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
_SCRIPTS = REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

REPORT_JSON = jobs_path("post-create-audit-last.json")
REPORT_TXT = jobs_path("post-create-audit-last.txt")

from migrate_dockerfile_canonical_ecr import ensure_canonical_task  # noqa: E402
from terminus_ci_check import Check, run_all_checks  # noqa: E402


def _map_severity(check: Check) -> str:
    if check.passed:
        return "PASS"
    if check.severity == "block":
        return "High"
    if check.severity == "warn":
        return "Medium"
    return "Low"


def _issue_dict(check: Check) -> dict:
    return {
        "id": check.id,
        "severity": _map_severity(check),
        "message": check.message,
        "fix": check.fix,
        "passed": check.passed,
    }


def _run_anti_spam_post_create(task_dir: Path) -> tuple[int, str]:
    script = REPO_ROOT / "scripts" / "terminus_anti_spam_auto.py"
    proc = subprocess.run(
        [sys.executable, str(script), "post-create", "--task-dir", str(task_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def run_round(task_dir: Path, *, round_num: int, harbor: bool, ruff: bool) -> dict:
    task_dir = task_dir.resolve()
    slug = task_dir.name

    ensure_canonical_task(task_dir, quiet=True)

    checks = run_all_checks(task_dir, harbor_llmaj=harbor, ruff=ruff)
    issues = [_issue_dict(c) for c in checks if not c.passed]

    spam_rc, spam_out = _run_anti_spam_post_create(task_dir)
    if spam_rc != 0:
        issues.append(
            {
                "id": "anti_spam_post_create",
                "severity": "High",
                "message": "Anti-spam/templated post-create FAIL",
                "fix": "shared/anti-spam-templated-submissions.mdc § When FAIL → fix",
                "passed": False,
            }
        )

    counts = {"High": 0, "Medium": 0, "Low": 0, "PASS": 0}
    for iss in issues:
        sev = iss.get("severity", "Low")
        if sev in counts:
            counts[sev] += 1

    blocking = counts["High"] + counts["Medium"]
    verdict = "CLEAN" if blocking == 0 else "CONTINUE"

    payload = {
        "slug": slug,
        "task_dir": str(task_dir.relative_to(REPO_ROOT)) if task_dir.is_relative_to(REPO_ROOT) else str(task_dir),
        "round": round_num,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "counts": {k: v for k, v in counts.items() if k != "PASS"},
        "blocking": blocking,
        "anti_spam_rc": spam_rc,
        "issues": issues,
        "anti_spam_snippet": spam_out[:2000] if spam_out else "",
    }

    prev: dict = {}
    prev_path = resolve_jobs_path("post-create-audit-last.json")
    if prev_path.is_file():
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev = {}

    history = list(prev.get("history") or [])
    history.append(
        {
            "round": round_num,
            "verdict": verdict,
            "counts": payload["counts"],
            "blocking": blocking,
        }
    )
    payload["history"] = history[-8:]

    report_json = jobs_path("post-create-audit-last.json", mkdir=True)
    report_txt = jobs_path("post-create-audit-last.txt", mkdir=True)
    report_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Post-create audit loop — round {round_num} — {slug}",
        f"Verdict: **{verdict}** (blocking={blocking})",
        f"High={counts['High']} Medium={counts['Medium']} Low={counts['Low']}",
        "",
    ]
    if issues:
        lines.append("## Issues")
        for iss in issues:
            lines.append(f"- [{iss['severity']}] {iss['id']}: {iss['message']}")
            if iss.get("fix"):
                lines.append(f"  - Fix: {iss['fix']}")
    else:
        lines.append("No static issues.")
    lines.append("")
    lines.append(f"Full JSON: {report_json.relative_to(REPO_ROOT)}")
    report_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--task-name", type=str, default="")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--pack-gate", action="store_true", help="Exit 1 if any High/Medium")
    parser.add_argument("--no-harbor", action="store_true")
    parser.add_argument("--no-ruff", action="store_true")
    args = parser.parse_args()

    task_dir = args.task_dir
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / task_dir
    if args.task_name:
        for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
            cand = base / args.task_name
            if cand.is_dir():
                task_dir = cand
                break

    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1

    payload = run_round(
        task_dir,
        round_num=max(1, args.round),
        harbor=not args.no_harbor,
        ruff=not args.no_ruff,
    )

    if args.pack_gate and payload["blocking"] > 0:
        print(
            f"ERROR: post-create audit blocking issues={payload['blocking']} "
            f"(High={payload['counts']['High']} Medium={payload['counts']['Medium']})",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
