#!/usr/bin/env python3
"""Zero-user EASY/TRIVIAL automation — hooks call this; user says nothing.

  - Detect slug from platform summary (test names → tasks/*/tests)
  - Auto-save trivial-easy-context + agent-smoke sync
  - Auto-set task.toml difficulty = hard on EASY/TRIVIAL
  - Report calibration + design gate status (informational on paste)

  python3 scripts/auto_easy_platform_automation.py --from-prompt --text-file /tmp/p.txt
  python3 scripts/auto_easy_platform_automation.py --slug foo --ensure-hard
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
TASK_ROOTS = (REPO_ROOT / "tasks", REPO_ROOT / "pending")


def _extract_test_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        m = re.search(r"\b(test_[a-z0-9_]+)\s*:", line, re.I)
        if m:
            names.append(m.group(1))
    return names


def detect_slug_from_summary(text: str) -> str | None:
    """Match Unit Tests rows to tasks/*/tests/test_outputs.py."""
    explicit = re.search(
        r"(?:tasks|pending)/([a-zA-Z0-9][a-zA-Z0-9_-]*)",
        text,
    )
    if explicit:
        return explicit.group(1)

    tests = _extract_test_names(text)
    if len(tests) < 3:
        return None

    best_slug = ""
    best_hits = 0
    for root in TASK_ROOTS:
        if not root.is_dir():
            continue
        for task_dir in root.iterdir():
            if not task_dir.is_dir() or task_dir.name.startswith("_"):
                continue
            tout = task_dir / "tests" / "test_outputs.py"
            if not tout.is_file():
                continue
            body = tout.read_text(encoding="utf-8", errors="replace")
            hits = sum(1 for t in tests if t in body)
            if hits > best_hits:
                best_hits = hits
                best_slug = task_dir.name

    if best_hits >= max(3, len(tests) // 2):
        return best_slug
    return None


def ensure_difficulty_hard(task_dir: Path) -> bool:
    """Set difficulty = hard when platform EASY/TRIVIAL — returns True if changed."""
    toml = task_dir / "task.toml"
    if not toml.is_file():
        return False
    text = toml.read_text(encoding="utf-8")
    if re.search(r'^\s*difficulty\s*=\s*"hard"', text, re.M):
        return False
    if not re.search(r'^\s*difficulty\s*=\s*"', text, re.M):
        return False
    new_text = re.sub(
        r'^(\s*difficulty\s*=\s*)"[^"]*"',
        r'\1"hard"',
        text,
        count=1,
        flags=re.M,
    )
    if new_text == text:
        return False
    toml.write_text(new_text, encoding="utf-8")
    return True


def _run_gate(script: str, task_dir: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), "--pack-gate", "--task-dir", str(task_dir)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def gate_status_report(task_dir: Path) -> str:
    lines = ["**No-EASY gate status (auto):**"]
    for script, label in (
        ("preupload_agent_calibration.py", "Agent calibration (HARD ≤20%)"),
        ("preupload_difficulty_design_gate.py", "Difficulty design"),
    ):
        rc, out = _run_gate(script, task_dir)
        verdict = "PASS" if rc == 0 else "FAIL"
        lines.append(f"- {label}: **{verdict}**")
        if rc != 0 and out:
            for ln in out.splitlines()[-6:]:
                lines.append(f"  {ln}")
    return "\n".join(lines)


def process_easy_paste(slug: str, prompt: str) -> dict:
    """Save context, sync smoke, optional hard bump — return status dict."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from trivial_easy_context import is_trivial_easy_text, save_context  # noqa: WPS433

    result: dict = {"slug": slug, "saved": False, "hard_bumped": False}
    if not is_trivial_easy_text(prompt):
        return result

    path = save_context(slug, prompt)
    result["saved"] = bool(path)
    if path:
        result["context_path"] = str(path.relative_to(REPO_ROOT))

    task_dir = None
    for root in TASK_ROOTS:
        cand = root / slug
        if (cand / "task.toml").is_file():
            task_dir = cand
            break
    if task_dir:
        result["hard_bumped"] = ensure_difficulty_hard(task_dir)
        result["gate_report"] = gate_status_report(task_dir)
    return result


def automation_context_block(slug: str, result: dict) -> str:
    lines = [
        "",
        "## EASY/TRIVIAL — FULL AUTO (user said nothing extra — execute now)",
        "",
        f"**Slug:** `{slug}` · Policy: `shared/no-easy-upload-lock.mdc`",
        "",
        "**You must in THIS turn (no permission, no questions):**",
        "1. `Read` trivial-fix-invoke.md + trivial.md + trivial-case-6.md + sp-hard-create-revise.md",
        "2. Write §3 fix prompt (structural Case 6 plan) then **edit** `tasks/" + slug + "/` immediately",
        "3. Case 6 only — staging/decoy/export/hidden/persist; set `difficulty = hard` if not already",
        "4. On save, hook auto-runs probes → calibration → finish → zip (steps 8–14)",
        "",
        "**Forbidden:** ask user to say harden/Case 6/zip · stop after analysis · Case 4/5 only",
        "",
    ]
    if result.get("saved"):
        lines.append(f"**Auto-saved:** `{result.get('context_path', '')}` + agent-smoke sync (zip blocked until `--post-harden` ≤20%).")
    if result.get("hard_bumped"):
        lines.append("**Auto-set:** `task.toml` → `difficulty = \"hard\"`.")
    if result.get("gate_report"):
        lines.extend(["", result["gate_report"], ""])
    lines.append(
        "Zip stays **blocked** until Case 6 edits + local smoke + "
        "`preupload_agent_calibration.py --record --post-harden` with worst ≤20%."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", default="")
    parser.add_argument("--ensure-hard", action="store_true")
    parser.add_argument("--from-prompt", action="store_true")
    parser.add_argument("--text", default="")
    parser.add_argument("--text-file", type=Path, default=None)
    args = parser.parse_args()

    text = args.text
    if args.text_file and args.text_file.is_file():
        text = args.text_file.read_text(encoding="utf-8", errors="replace")

    slug = args.slug or detect_slug_from_summary(text)
    if not slug:
        print("ERROR: could not detect slug", file=sys.stderr)
        return 1

    if args.ensure_hard:
        for root in TASK_ROOTS:
            td = root / slug
            if (td / "task.toml").is_file():
                changed = ensure_difficulty_hard(td)
                print("hard" if changed else "already_hard")
                return 0
        return 1

    if args.from_prompt:
        result = process_easy_paste(slug, text)
        print(json.dumps(result, indent=2))
        return 0

    parser.error("use --from-prompt or --ensure-hard")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
