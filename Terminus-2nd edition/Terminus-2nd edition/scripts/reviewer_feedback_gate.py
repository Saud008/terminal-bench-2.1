#!/usr/bin/env python3
"""Reviewer feedback triage vs accepted-feedback gates (A-001…A-010) + trivial-risk.

Runs automatically when user pastes reviewer line comments (hook + agent Step 0).

  python3 scripts/reviewer_feedback_gate.py --task-dir tasks/<name> --feedback-file /tmp/paste.txt
  python3 scripts/reviewer_feedback_gate.py --task-dir tasks/<name> --context   # load saved context

Report: jobs-local/reviewer-feedback-gate-last.json

Exit codes:
  0  SAFE — apply ACCEPT/PARTIAL only; no aggregate trivial risk
  2  ROUTE_CASE6 — applying accepted comments would still leave task shallow / probes fail
  1  missing task or no feedback text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

def report_json_path(*, mkdir: bool = False) -> Path:
    return jobs_path("reviewer-feedback-gate-last.json", mkdir=mkdir)


@dataclass
class CommentTriage:
    line: str
    verdict: str  # APPLY | PARTIAL | REJECT | DEFER
    trivial_risk: str  # none | low | medium | high
    accepted_gates: list[str]
    reason: str
    safe_alternative: str = ""


# Reviewer asks that conflict with accepted corpus / would trivialize
TRIVIALIZING_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"patch\s+/app/",
        "high",
        "Fix behavior via tests + /app/docs/ — do not name bug files in instruction",
    ),
    (
        r"\b(bug|fix)\s+(in|file)\s+[`'\"]?\w+\.(go|rs|py|ts|java|cpp|c)",
        "high",
        "Triage REJECT — solution leak; fix verifier/docs alignment only",
    ),
    (
        r"\b(golden|expected)\s+(output|json|csv|answer)",
        "high",
        "Never add golden answers to environment/ — independent reference in pytest",
    ),
    (
        r"\b(drop|remove|delete|weaken)\s+.*(test|hidden|probe)",
        "high",
        "Reject unless test is unfair — add contract to /app/docs/ instead",
    ),
    (
        r"\bBUG\b|\bTODO:\s*fix",
        "high",
        "Remove hint comments from environment — not reviewer-compliant leak",
    ),
    (
        r"\b(step[- ]by[- ]step|fix order|change .+ then .+ then)",
        "high",
        "Move contract to /app/docs/ — no solve recipe in instruction.md",
    ),
    (
        r"\b(lower|reduce)\s+difficulty|\bmark\s+as\s+medium\b|\beasier\b",
        "high",
        "Do not relabel difficulty to pass — structural Case 6 if agents ≥3/5",
    ),
    (
        r"\badd\s+(hint|checklist)\s+to\s+instruction",
        "high",
        "Expand /app/docs/ schema — instruction stays concise",
    ),
    (
        r"\b(simplify|shorten)\s+instruction.*(pass|easier|agent)",
        "medium",
        "Align instruction↔tests via docs — do not delete tested behaviors",
    ),
    (
        r"\bexact(ly)?\s+(operator|function|line|constant)",
        "high",
        "Contract-level doc fix only — no implementation hint in instruction",
    ),
]

# Reviewer asks that map to accepted-feedback hygiene (apply when valid)
ACCEPTED_ALIGN_PATTERNS: list[tuple[str, list[str], str]] = [
    (r"pip\s+install|uvx|runtime\s+install", ["A-001_runtime_verifier"], "Deps in Dockerfile /opt/verifier-venv only"),
    (r"reward\.txt|ctrf|verifier_did_not_run|tmux|asciinema", ["A-001_runtime_verifier"], "Harness bootstrap per accepted corpus"),
    (r"rebuild|stale\s+binary|cargo\s+build|go\s+build", ["A-004_rebuild_test_sh"], "test.sh rebuild before pytest"),
    (r"reference|subprocess|anti[- ]cheat", ["A-003_reference_subprocess"], "Independent reference in pytest"),
    (r"hidden|TB3|verifier-fixtures", ["A-005_hidden_fixtures"], "Hidden traps under /opt/verifier-fixtures/"),
    (r"instruction.*(test|align)|behavior.*instruction", ["A-010_instruction_docs"], "Cite /app/docs/ — no test checklist in instruction"),
    (r"echo.*output|hardcoded|oracle", ["A-009_oracle_no_echo"], "Oracle patches source + rebuild"),
    (r"subcategories|debugging|software-engineering", ["A-007_difficulty_sync"], "category allow-list + subcategories []"),
    (r"timeout|build_timeout|metadata", ["A-007_difficulty_sync"], "task.toml metadata only — RF1"),
]


def is_reviewer_feedback_text(text: str) -> bool:
    if not text or len(text.strip()) < 30:
        return False
    low = text.lower()
    signals = (
        r"reviewer feedback",
        r"needs_revision",
        r"needs revision",
        r"per reviewer",
        r"line comment",
        r"feedback:",
        r"@prompts/reviewer",
        r"reviewer-feedback",
        r"rf[1-6]\b",
    )
    if any(re.search(p, low) for p in signals):
        return True
    # Bulleted review without explicit header
    if re.search(r"tasks/[a-z0-9_-]+", low) and re.search(
        r"(instruction|test\.sh|dockerfile|oracle|fairness|alignment|hint|trivial)",
        low,
    ):
        return True
    return False


def context_path(slug: str) -> Path:
    return jobs_path(f"reviewer-feedback-context-{slug}.json", mkdir=False)


def save_context(slug: str, feedback: str) -> Path | None:
    if not is_reviewer_feedback_text(feedback):
        return None
    path = jobs_path(f"reviewer-feedback-context-{slug}.json", mkdir=True)
    payload = {
        "slug": slug,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "feedback_snippet": feedback[:12000],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_context(slug: str) -> dict | None:
    path = resolve_jobs_path(f"reviewer-feedback-context-{slug}.json")
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def split_comments(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        s = re.sub(r"^[-*•]\s+", "", s)
        s = re.sub(r"^\d+[.)]\s+", "", s)
        if len(s) >= 12:
            lines.append(s)
    if not lines and text.strip():
        lines = [text.strip()[:500]]
    return lines[:40]


def classify_comment(comment: str) -> CommentTriage:
    low = comment.lower()
    risk = "none"
    reasons: list[str] = []
    safe = ""
    gates: list[str] = []

    for pat, level, alt in TRIVIALIZING_PATTERNS:
        if re.search(pat, comment, re.I):
            if level == "high" or (level == "medium" and risk != "high"):
                risk = level
            reasons.append(f"trivializing:{pat[:40]}")
            safe = alt

    for pat, gate_ids, hint in ACCEPTED_ALIGN_PATTERNS:
        if re.search(pat, comment, re.I):
            gates.extend(gate_ids)
            if not safe:
                safe = hint

    gates = list(dict.fromkeys(gates))

    if risk == "high":
        verdict = "REJECT"
    elif risk == "medium":
        verdict = "PARTIAL"
    elif gates:
        verdict = "APPLY"
    elif re.search(r"\b(consider|maybe|optional|nit)\b", low):
        verdict = "DEFER"
    else:
        verdict = "PARTIAL"

    reason = "; ".join(reasons) if reasons else ("accepted-gate align" if gates else "default careful apply")

    return CommentTriage(
        line=comment[:240],
        verdict=verdict,
        trivial_risk=risk,
        accepted_gates=gates,
        reason=reason,
        safe_alternative=safe,
    )


def run_accepted_gates(task_dir: Path) -> tuple[list, list]:
    from terminus_accepted_feedback_gates import run_all_gates  # noqa: WPS433

    gates = run_all_gates(task_dir)
    blocks = [g for g in gates if g.severity == "block" and not g.passed]
    warns = [g for g in gates if g.severity == "warn" and not g.passed]
    return blocks, warns


def probe_trivial_shape(task_dir: Path) -> tuple[bool, str]:
    script = REPO_ROOT / "scripts" / "terminus_auto_probes.py"
    if not script.is_file():
        return True, "probes script missing — skip"
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(script), "--task-dir", str(task_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or proc.stderr or "")[-800:]
    return ok, tail


def anti_spam_sim_line(slug: str) -> str:
    script = REPO_ROOT / "scripts" / "terminus_anti_spam_check.py"
    if not script.is_file():
        return "anti-spam: unknown"
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(script), "--pack-gate", "--task-name", slug],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=90,
    )
    for line in (proc.stdout or "").splitlines():
        if "Anti-spam/templated:" in line:
            return line.strip()
    return f"anti-spam exit {proc.returncode}"


def run_gate(task_dir: Path, feedback: str, *, slug: str | None = None) -> dict:
    slug = slug or task_dir.name
    comments = split_comments(feedback)
    triage = [classify_comment(c) for c in comments]

    reject = sum(1 for t in triage if t.verdict == "REJECT")
    partial = sum(1 for t in triage if t.verdict == "PARTIAL")
    apply_n = sum(1 for t in triage if t.verdict == "APPLY")
    high_risk = sum(1 for t in triage if t.trivial_risk == "high")

    blocks, warns = run_accepted_gates(task_dir)
    probes_ok, probes_tail = probe_trivial_shape(task_dir)
    sim_line = anti_spam_sim_line(slug)

    aggregate_trivial = high_risk > 0 and apply_n == 0 and reject >= max(1, len(triage) // 2)
    if not probes_ok:
        route_case6 = True
    elif aggregate_trivial:
        route_case6 = True
    elif high_risk >= 2:
        route_case6 = True
    else:
        route_case6 = False

    if "sim 0.0" in sim_line.lower() or "nearest none" in sim_line.lower():
        sim_ok = True
    elif "PASS" in sim_line and "sim" in sim_line.lower():
        sim_ok = "sim 0" in sim_line.replace(" ", "") or "sim0.0" in sim_line.replace(" ", "")
    else:
        sim_ok = False

    verdict = "SAFE_APPLY"
    if route_case6:
        verdict = "ROUTE_CASE6"
    elif reject > 0 and apply_n == 0:
        verdict = "PARTIAL_ONLY"

    payload = {
        "slug": slug,
        "path": str(task_dir),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "route_case6": route_case6,
        "similarity_line": sim_line,
        "similarity_ok": sim_ok,
        "probes_ok": probes_ok,
        "accepted_gates_blocking": [asdict(g) for g in blocks],
        "accepted_gates_warnings": [asdict(g) for g in warns],
        "comment_counts": {
            "total": len(triage),
            "apply": apply_n,
            "partial": partial,
            "reject": reject,
            "high_trivial_risk": high_risk,
        },
        "triage": [asdict(t) for t in triage],
        "agent_rules": [
            "Triage each comment — APPLY/PARTIAL only; REJECT trivializing items (RF6)",
            "Compare failing A-001…A-010 with reviewer ask — fix via accepted corpus shape",
            "If verdict ROUTE_CASE6 — load trivial-fix-invoke + Case 6 before zip",
            "CREATE: audit automatic on save; pack only when sim 0.0 + create-finish PASS",
        ],
        "probes_tail": probes_tail[-400:] if probes_tail else "",
    }

    out = report_json_path(mkdir=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def format_report(payload: dict) -> str:
    lines = [
        f"## Reviewer feedback gate — `{payload['slug']}`",
        "",
        f"**Verdict:** `{payload['verdict']}`"
        + (" → **Case 6** before zip" if payload.get("route_case6") else ""),
        f"**Accepted gates blocking:** {len(payload.get('accepted_gates_blocking', []))}",
        f"**Probes OK:** {payload.get('probes_ok')}",
        f"**Similarity:** {payload.get('similarity_line', 'n/a')}",
        "",
        "| Verdict | Risk | Comment | Safe alternative |",
        "|---------|------|---------|------------------|",
    ]
    for row in payload.get("triage", [])[:15]:
        lines.append(
            f"| {row['verdict']} | {row['trivial_risk']} | {row['line'][:80]}… | "
            f"{(row.get('safe_alternative') or '')[:60]} |"
        )
    lines.append("")
    lines.append("Report: `jobs-local/reviewer-feedback-gate-last.json`")
    lines.append("")
    lines.append(
        "**Agent:** Fix APPLY/PARTIAL only · REJECT hints in instruction · "
        "re-run gate after edits · then `create_finish_to_zip.sh` (sim **0.0** required)."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--feedback-file", type=Path)
    parser.add_argument("--feedback-text", default="")
    parser.add_argument("--context", action="store_true", help="Load jobs-local reviewer-feedback-context JSON")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / task_dir
    task_dir = task_dir.resolve()
    if not (task_dir / "task.toml").is_file():
        print(f"ERROR: not a task dir: {task_dir}", file=sys.stderr)
        return 1

    feedback = args.feedback_text
    if args.context:
        ctx = load_context(task_dir.name)
        if ctx:
            feedback = ctx.get("feedback_snippet", "")
    if args.feedback_file:
        feedback = args.feedback_file.read_text(encoding="utf-8", errors="replace")
    if not feedback.strip():
        print("ERROR: no reviewer feedback text", file=sys.stderr)
        return 1

    payload = run_gate(task_dir, feedback, slug=task_dir.name)
    if not args.quiet:
        print(format_report(payload))
    if payload["verdict"] == "ROUTE_CASE6":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
