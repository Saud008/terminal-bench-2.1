#!/usr/bin/env python3
"""Ideas intake gate — similarity block at 0.10; auto @CREATE when sim == 0.

Writes jobs-local/ideas-draft.json, runs terminus_anti_spam_auto.py ideas, prints verdict.

  python3 scripts/idea_similarity_gate.py \\
    --language go --domain "hospital lab" \\
    --title "serial-frame replay auditor" \\
    --summary "CLI replays instrument frames; checksum bugs break export."

Exit 0 + AUTO_CREATE=yes when weighted == 0 and no blockers.
Exit 0 + AUTO_CREATE=no when 0 < weighted <= 0.10 (PASS — user may confirm build).
Exit 1 when weighted > 0.10 or slug/family blockers.

Report: jobs-local/anti-spam-ideas-last.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS = REPO_ROOT / "jobs-local"
_SCRIPTS = REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

IDEAS_DRAFT = resolve_jobs_path("ideas-draft.json")
IDEAS_REPORT = resolve_jobs_path("anti-spam-ideas-last.json")
GATE_REPORT = jobs_path("idea-similarity-gate-last.json")

from anti_spam_pipeline import IDEA_AUTO_CREATE_SIM, IDEA_VERDICT_FAIL  # noqa: E402
from task_generation_policy import audit_idea_text  # noqa: E402
from task_uniqueness_policy import (  # noqa: E402
    build_idea_uniqueness_report,
    format_uniqueness_table,
)


def run_gate_from_draft(draft_path: Path | None = None) -> tuple[int, str]:
    """Hook entry: run gate when jobs-local/ideas-draft.json has language+domain+title."""
    path = draft_path or IDEAS_DRAFT
    if not path.is_file():
        return 0, "(skip idea gate — no ideas draft)"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return 1, f"ideas draft unreadable: {exc}"
    raw = data.get("ideas", data) if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        return 0, "(skip idea gate — empty ideas draft)"
    idea = raw[0] if isinstance(raw[0], dict) else {}
    language = str(idea.get("language") or "").strip()
    domain = str(idea.get("domain") or "").strip()
    title = str(idea.get("title") or "").strip()
    summary = str(idea.get("summary") or "").strip()
    if not language or not domain or not title:
        return 0, "(skip idea gate — draft missing language/domain/title)"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "idea_similarity_gate.py"),
        "--language",
        language,
        "--domain",
        domain,
        "--title",
        title,
    ]
    if summary:
        cmd.extend(["--summary", summary])
    slug = str(idea.get("slug") or "").strip()
    if slug:
        cmd.extend(["--slug", slug])
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--title", required=True, help="Short task title for slug + screen")
    parser.add_argument("--summary", default="", help="User idea text (1–3 sentences)")
    parser.add_argument("--slug", default="", help="Optional explicit slug")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    summary = args.summary.strip() or args.domain.strip() or args.title
    if summary.strip() == args.domain.strip():
        blob = f"{args.domain}\n{args.language}"
    else:
        blob = f"{args.domain}\n{summary}\n{args.language}"

    idea_audit = audit_idea_text(
        title=args.title,
        domain=args.domain,
        summary=blob,
        slug=args.slug.strip(),
    )
    if not idea_audit.passed:
        gate_out = jobs_path("idea-similarity-gate-last.json", mkdir=True)
        verdict_label = "REGENERATE" if idea_audit.regenerate_required else "BLOCKED_TASK_GENERATION"
        gate_out.write_text(
            json.dumps(
                {
                    "language": args.language,
                    "domain": args.domain,
                    "title": args.title,
                    "status": "FAIL",
                    "verdict": verdict_label,
                    "regenerate_required": idea_audit.regenerate_required,
                    "regenerate_reasons": idea_audit.regenerate_reasons,
                    "violations": idea_audit.violations,
                    "checks": idea_audit.checks,
                    "policy": "shared/task-generation-mandatory.mdc",
                    "repository_state_policy": "shared/repository-state-requirement.mdc",
                    "forbidden_repair_rule": "shared/forbidden-repair-objectives-gate.mdc",
                    "fail_fix_rule": "shared/repository-state-fail-fix.mdc",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if idea_audit.regenerate_required:
            print(
                "Idea similarity gate: REGENERATE — forbidden repair/debug objective",
                file=sys.stderr,
            )
            print("  Policy: shared/forbidden-repair-objectives-gate.mdc", file=sys.stderr)
            print(
                "  Do not @CREATE on this idea — regenerate with build-on-working-baseline goal.",
                file=sys.stderr,
            )
        else:
            print(
                "Idea similarity gate: FAIL (repository-state — functional repo + new capability; not find-and-fix)",
                file=sys.stderr,
            )
            print("  Policy: shared/repository-state-requirement.mdc", file=sys.stderr)
        print("  FAIL → fix: shared/repository-state-fail-fix.mdc", file=sys.stderr)
        for cid, status in idea_audit.checks.items():
            if status != "PASS":
                print(f"  {cid}: {status}", file=sys.stderr)
        for v in idea_audit.violations:
            print(f"  - {v}", file=sys.stderr)
        print("VERDICT: BLOCKED — hard acceptance failed; do not start @CREATE", file=sys.stderr)
        if idea_audit.regenerate_required:
            print("VERDICT: REGENERATE — regenerate idea (forbidden repair objective)", file=sys.stderr)
        return 1

    idea_entry = {
        "title": args.title,
        "language": args.language,
        "domain": args.domain,
        "summary": blob,
        "slug": args.slug,
    }
    JOBS.mkdir(parents=True, exist_ok=True)
    IDEAS_DRAFT.write_text(json.dumps({"ideas": [idea_entry]}, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "terminus_anti_spam_auto.py"),
        "ideas",
        "--json",
        str(IDEAS_DRAFT),
    ]
    if args.rebuild_index:
        cmd.append("--rebuild-index")

    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    result_row: dict = {}
    if IDEAS_REPORT.is_file():
        payload = json.loads(IDEAS_REPORT.read_text(encoding="utf-8"))
        rows = payload.get("results") or []
        if rows:
            result_row = rows[0]

    weighted = float(result_row.get("weighted_score", -1))
    status = result_row.get("status", "FAIL")
    auto_create = bool(result_row.get("auto_create", False))
    nearest = result_row.get("nearest")
    slug = result_row.get("slug", "")
    blockers = list(result_row.get("blockers") or [])
    warnings = list(result_row.get("warnings") or [])
    unacceptable = list(result_row.get("unacceptable_classes") or [])

    uniqueness = build_idea_uniqueness_report(
        unacceptable_classes=unacceptable,
        blockers=blockers,
        warnings=warnings,
        weighted=weighted if weighted >= 0 else 0.0,
        domain=args.domain,
        title=args.title,
        summary=blob,
        idea_threshold=IDEA_VERDICT_FAIL,
    )

    gate = {
        "language": args.language,
        "domain": args.domain,
        "title": args.title,
        "slug": slug,
        "nearest": nearest,
        "weighted_score": weighted,
        "status": status,
        "auto_create": auto_create,
        "thresholds": {
            "block_if_weighted_gt": IDEA_VERDICT_FAIL,
            "auto_create_if_weighted_eq": IDEA_AUTO_CREATE_SIM,
        },
        "blockers": blockers,
        "warnings": warnings,
        "unacceptable_classes": unacceptable,
        "uniqueness": {
            "verdict": uniqueness.verdict,
            "checks": uniqueness.checks,
            "violations": uniqueness.violations,
            "policy": "shared/task-uniqueness-gate.mdc",
        },
    }
    gate_out = jobs_path("idea-similarity-gate-last.json", mkdir=True)
    gate_out.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")

    print(f"Idea similarity gate: {status}")
    print(f"  weighted={weighted:.3f} nearest={nearest or 'none'}")
    print(f"  block if > {IDEA_VERDICT_FAIL} · auto-create if == {IDEA_AUTO_CREATE_SIM}")
    print(f"  AUTO_CREATE={'yes' if auto_create else 'no'}")
    if gate["blockers"]:
        print("  blockers:")
        for b in gate["blockers"]:
            print(f"    - {b}")
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    print(f"Report: {GATE_REPORT}")
    print()
    print("## Task uniqueness (similarity gate)")
    print(format_uniqueness_table(uniqueness))
    if uniqueness.violations:
        print("Uniqueness violations:")
        for v in uniqueness.violations:
            print(f"  - {v}")

    if uniqueness.verdict == "FAIL":
        print(
            "VERDICT: BLOCKED — task uniqueness failed; change domain/workflow/artifact",
            file=sys.stderr,
        )
        print("  Policy: shared/task-uniqueness-gate.mdc", file=sys.stderr)
        return 1

    if proc.returncode != 0 or status == "FAIL":
        print("VERDICT: BLOCKED — do not start @CREATE", file=sys.stderr)
        return 1
    if auto_create:
        print("VERDICT: PASS — start @CREATE Phase A immediately (sim == 0)")
        return 0
    print("VERDICT: PASS — similarity > 0 but <= 0.10; confirm build or revise domain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
