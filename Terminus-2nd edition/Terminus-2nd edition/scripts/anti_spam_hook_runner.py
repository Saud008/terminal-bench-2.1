#!/usr/bin/env python3
"""Shared anti-spam + post-create audit auto-runner for Cursor hooks (debounced)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS = REPO_ROOT / "jobs-local"
STATE_PATH = JOBS / "anti-spam-hook-state.json"
HOOK_LAST = JOBS / "anti-spam-hook-last.txt"
IDEAS_DRAFT_NAME = "ideas-draft.json"
AUDIT_REPORT_NAME = "post-create-audit-last.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402


def _ideas_draft_path() -> Path:
    return resolve_jobs_path(IDEAS_DRAFT_NAME)


def _audit_report_path() -> Path:
    return resolve_jobs_path(AUDIT_REPORT_NAME)

DEBOUNCE_SEC = 45
POST_CREATE_TRIGGERS = frozenset(
    {
        "task.toml",
        "instruction.md",
        "tests/test.sh",
        "tests/test_outputs.py",
        "solution/solve.sh",
        "environment/dockerfile",
    }
)

TASK_FILE_SUFFIXES = (
    "task.toml",
    "instruction.md",
    "test.sh",
    "test_outputs.py",
    "solve.sh",
    "dockerfile",
    "test_m",
)

TASK_PATH_RE = re.compile(
    r"(?:tasks|pending|tasks/_accepted-tasks)/([a-zA-Z0-9][a-zA-Z0-9_-]*)/"
)

ORACLE_REMINDER = """**CREATE finish (automatic on save + agent must not skip):**
  ./scripts/create_finish_to_zip.sh <slug>
  Hook runs: audit → unacceptable-class → finish → zip (harbor cache or background)
"""


def _load_state() -> dict:
    if not STATE_PATH.is_file():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _debounced(key: str) -> bool:
    state = _load_state()
    now = time.time()
    last = float(state.get(key, 0))
    if now - last < DEBOUNCE_SEC:
        return True
    state[key] = now
    _save_state(state)
    return False


def slug_from_path(path: str) -> str | None:
    if not path:
        return None
    norm = path.replace("\\", "/").lower()
    m = TASK_PATH_RE.search(norm)
    if not m:
        return None
    slug = m.group(1)
    if slug.startswith("_") or slug == "tasksss":
        return None
    return slug


def _is_post_create_trigger(path: str) -> bool:
    norm = path.replace("\\", "/").lower()
    if "/tasks/" not in norm and "/pending/" not in norm:
        return False
    if norm.endswith("environment/dockerfile"):
        return True
    if "/environment/" in norm or "/tests/" in norm or "/solution/" in norm or "/steps/" in norm:
        return True
    name = norm.rsplit("/", 1)[-1]
    if name == "dockerfile" and "/environment/" in norm:
        return True
    for trigger in POST_CREATE_TRIGGERS:
        if norm.endswith(trigger):
            return True
    for suffix in TASK_FILE_SUFFIXES:
        if name.startswith(suffix) or name.endswith(suffix):
            return True
    return False


def _is_ideas_draft_path(path: str) -> bool:
    norm = path.replace("\\", "/")
    return norm.endswith("jobs-local/ideas-draft.json") or norm.endswith("/ideas-draft.json")


def locate_task_dir(slug: str) -> Path | None:
    for base in ("tasks", "pending"):
        td = REPO_ROOT / base / slug
        if td.is_dir() and (td / "task.toml").is_file():
            return td
    return None


def _run(cmd: list[str], *, timeout: int = 120) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT after {timeout}s: {' '.join(cmd)}"
    except OSError as exc:
        return 1, str(exc)


def _audit_round_for(slug: str) -> int:
    """Next audit round per post-create-audit-loop.mdc (max 4)."""
    audit_report = _audit_report_path()
    if not audit_report.is_file():
        return 1
    try:
        data = json.loads(audit_report.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 1
    if data.get("slug") != slug:
        return 1
    if data.get("verdict") == "CONTINUE" and int(data.get("blocking", 0)) > 0:
        return min(int(data.get("round", 1)) + 1, 4)
    return 1


def _audit_summary_snippet() -> str:
    audit_report = _audit_report_path()
    if not audit_report.is_file():
        return ""
    try:
        data = json.loads(audit_report.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    counts = data.get("counts") or {}
    return (
        f"round={data.get('round')} verdict={data.get('verdict')} "
        f"High={counts.get('High', 0)} Medium={counts.get('Medium', 0)} "
        f"Low={counts.get('Low', 0)}"
    )


def run_post_create_audit(slug: str, task_dir: Path) -> tuple[int, str]:
    """Static Phase E half — post_create_audit_loop.py (includes anti-spam + CI checks)."""
    round_num = _audit_round_for(slug)
    script = REPO_ROOT / "scripts" / "post_create_audit_loop.py"
    code, out = _run(
        [
            sys.executable,
            str(script),
            "--task-dir",
            str(task_dir),
            "--round",
            str(round_num),
            "--no-harbor",
        ],
        timeout=300,
    )
    summary = _audit_summary_snippet()
    header = f"## Post-create audit (auto, round {round_num}) — `{slug}`"
    if summary:
        header += f"\n{summary}"
    block = f"{header}\n\n```\n{out}\n```\n"
    block += f"\nReport: `jobs-local/post-create-audit-last.json`\n"
    return code, block


def run_repository_state_gate(slug: str, task_dir: Path) -> tuple[int, str]:
    script = REPO_ROOT / "scripts" / "repository_state_gate.py"
    code, out = _run(
        [sys.executable, str(script), "--pack-gate", "--quiet", "--task-dir", str(task_dir)],
        timeout=120,
    )
    header = f"## Repository-state gate (auto, 7/7) — `{slug}`"
    block = f"{header}\n\n```\n{out}\n```\n"
    block += "Report: `jobs-local/repository-state-gate-last.json`\n"
    if code != 0:
        block += "\n**FAIL → fix in place:** `shared/repository-state-fail-fix.mdc` — no zip until PASS.\n"
    return code, block


def run_unacceptable_class(slug: str, task_dir: Path) -> tuple[int, str]:
    script = REPO_ROOT / "scripts" / "unacceptable_class_gate.py"
    code, out = _run(
        [sys.executable, str(script), "--pack-gate", "--task-dir", str(task_dir), "--quiet"],
        timeout=120,
    )
    block = f"## Unacceptable-class gate (auto, 8/8) — `{slug}`\n\n```\n{out}\n```\n"
    block += "Report: `jobs-local/unacceptable-class-gate-last.json`\n"
    return code, block


def run_create_finish(slug: str, task_dir: Path) -> tuple[int, str]:
    """Phases E(static) → F → F′ → G — automatic after audit/class gates."""
    script = REPO_ROOT / "scripts" / "create_finish_to_zip.py"
    code, out = _run(
        [
            sys.executable,
            str(script),
            "--task-dir",
            str(task_dir),
            "--hook-mode",
        ],
        timeout=600,
    )
    header = f"## CREATE finish → zip (auto) — `{slug}`"
    block = f"{header}\n\n```\n{out}\n```\n"
    block += f"\nReport: `jobs-local/create-finish-last.json`\n"
    if code == 0:
        block += f"\n**ZIP ready:** `tasksubmit/{slug}.zip`\n"
    elif code == 2:
        block += "\n**BLOCKED audit** — fix High/Medium in task tree; hook will re-run on next save.\n"
    elif code == 3:
        block += "\n**Harbor** — background finish spawned or fix Docker/WSL.\n"
    return code, block


def _trivial_easy_context_path(slug: str) -> Path:
    return resolve_jobs_path(f"trivial-easy-context-{slug}.json")


def has_trivial_easy_context(slug: str) -> bool:
    return _trivial_easy_context_path(slug).is_file()


def _reviewer_feedback_context_path(slug: str) -> Path:
    return resolve_jobs_path(f"reviewer-feedback-context-{slug}.json")


def has_reviewer_feedback_context(slug: str) -> bool:
    return _reviewer_feedback_context_path(slug).is_file()


def save_reviewer_feedback_from_prompt(slug: str, prompt: str) -> str | None:
    if not prompt.strip():
        return None
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from reviewer_feedback_gate import is_reviewer_feedback_text, save_context  # noqa: WPS433

    if not is_reviewer_feedback_text(prompt):
        return None
    path = save_context(slug, prompt)
    if path:
        return str(path.relative_to(REPO_ROOT))
    return None


def run_reviewer_feedback_gate(slug: str, task_dir: Path, *, context: bool = True) -> tuple[int, str]:
    script = REPO_ROOT / "scripts" / "reviewer_feedback_gate.py"
    cmd = [
        sys.executable,
        str(script),
        "--task-dir",
        str(task_dir),
        "--quiet",
    ]
    if context:
        cmd.append("--context")
    code, out = _run(cmd, timeout=180)
    header = f"## Reviewer feedback gate (accepted A-001…A-010 + trivial-risk) — `{slug}`"
    report = resolve_jobs_path("reviewer-feedback-gate-last.json")
    body = out
    if report.is_file():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            from reviewer_feedback_gate import format_report  # noqa: WPS433

            body = format_report(data)
        except Exception:
            body = out or "(see reviewer-feedback-gate-last.json)"
    block = f"{header}\n\n{body}\n"
    if code == 2:
        block += "\n**ROUTE Case 6** — do not zip after reviewer-only cosmetic fixes.\n"
    return code, block


def save_trivial_easy_context_from_prompt(slug: str, prompt: str) -> str | None:
    if not prompt.strip():
        return None
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from trivial_easy_context import is_trivial_easy_text, save_context  # noqa: WPS433

    if not is_trivial_easy_text(prompt):
        return None
    path = save_context(slug, prompt)
    if path:
        return str(path.relative_to(REPO_ROOT))
    return None


def run_trivial_easy_auto_finish(slug: str, task_dir: Path) -> tuple[int, str]:
    """TRIVIAL/EASY steps 8–14: probes → calibration record → create_finish → zip."""
    script = REPO_ROOT / "scripts" / "trivial_easy_auto_finish.py"
    code, out = _run(
        [
            sys.executable,
            str(script),
            "--task-dir",
            str(task_dir),
            "--hook-mode",
        ],
        timeout=3700,
    )
    header = f"## TRIVIAL/EASY auto pipeline (steps 8–14) — `{slug}`"
    block = f"{header}\n\n```\n{out}\n```\n"
    block += "\nReport: `jobs-local/trivial-easy-pipeline-last.json`\n"
    if code == 0:
        block += f"\n**ZIP ready:** `tasksubmit/{slug}.zip`\n"
    elif code == 2:
        block += "\n**BLOCKED audit** — fix High/Medium; hook re-runs on next save.\n"
    elif code == 3:
        block += "\n**Harbor** — background finish or fix Docker/WSL.\n"
    else:
        block += "\n**Probes or finish FAIL** — deepen Case 6; see report.\n"
    return code, block


def run_task_pipeline(
    slug: str, *, force: bool = False, skip_easy_finish: bool = False
) -> tuple[int, str | None]:
    """Full post-create hook pipeline: audit + unacceptable-class (debounced)."""
    key = f"task-pipeline:{slug}"
    if not force and _debounced(key):
        cached = HOOK_LAST.read_text(encoding="utf-8") if HOOK_LAST.is_file() else ""
        return 0, f"(debounced {DEBOUNCE_SEC}s — last pipeline below)\n{cached}"

    task_dir = locate_task_dir(slug)
    if not task_dir:
        return 0, f"(skip pipeline — no task.toml for `{slug}`)"

    parts: list[str] = []
    code = 0

    audit_code, audit_block = run_post_create_audit(slug, task_dir)
    parts.append(audit_block)
    code = max(code, audit_code)

    class_code, class_block = run_unacceptable_class(slug, task_dir)
    parts.append(class_block)
    code = max(code, class_code)

    repo_code, repo_block = run_repository_state_gate(slug, task_dir)
    parts.append(repo_block)
    code = max(code, repo_code)

    if has_reviewer_feedback_context(slug):
        gate_code, gate_block = run_reviewer_feedback_gate(slug, task_dir)
        parts.append(gate_block)
        code = max(code, gate_code)

    if has_trivial_easy_context(slug) and not skip_easy_finish:
        finish_code, finish_block = run_trivial_easy_auto_finish(slug, task_dir)
    else:
        finish_code, finish_block = run_create_finish(slug, task_dir)
    parts.append(finish_block)
    code = max(code, finish_code)

    combined = "\n".join(parts)
    JOBS.mkdir(parents=True, exist_ok=True)
    HOOK_LAST.write_text(combined, encoding="utf-8")

    if code != 0:
        combined += "\n**Fix High/Medium blockers in place before zip.**\n"
    return code, combined


def _maybe_populate_ideas_draft_from_prompt(prompt: str) -> None:
    """Write jobs-local/ideas-draft.json when intake fields appear in prompt."""
    if not prompt or len(prompt.strip()) < 50:
        return
    low = prompt.lower()
    lang = ""
    for token in (
        "rust",
        "golang",
        "go",
        "bash",
        "java",
        "typescript",
        "node",
        "python",
        "c++",
        "kotlin",
        "ruby",
        "php",
    ):
        if re.search(rf"\b{re.escape(token)}\b", low):
            lang = "go" if token == "golang" else token
            break
    domain = ""
    for pat in (r"domain\s*:\s*(.+)", r"industry\s*:\s*(.+)", r"scenario\s*:\s*(.+)"):
        m = re.search(pat, low, re.I)
        if m:
            domain = m.group(1).split("\n")[0].strip()[:200]
            break
    title = ""
    for pat in (r"title\s*:\s*(.+)", r"task idea\s*:\s*(.+)", r"idea\s*:\s*(.+)"):
        m = re.search(pat, prompt, re.I)
        if m:
            title = m.group(1).split("\n")[0].strip()[:200]
            break
    if not title and len(prompt) > 80:
        title = prompt.strip().split("\n")[0][:120]
    if not lang or not domain or not title:
        return
    JOBS.mkdir(parents=True, exist_ok=True)
    payload = {
        "ideas": [
            {
                "title": title,
                "language": lang,
                "domain": domain,
                "summary": prompt.strip()[:4000],
                "slug": "",
            }
        ]
    }
    draft = jobs_path(IDEAS_DRAFT_NAME, mkdir=True)
    draft.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_ideas_screen(*, force: bool = False, prompt: str = "") -> tuple[int, str]:
    key = "ideas-screen"
    if not force and _debounced(key):
        cached = HOOK_LAST.read_text(encoding="utf-8") if HOOK_LAST.is_file() else ""
        return 0, f"(debounced)\n{cached}"

    if prompt:
        _maybe_populate_ideas_draft_from_prompt(prompt)

    draft = _ideas_draft_path()
    if not draft.is_file():
        return 0, "(skip ideas — jobs-local/ideas-draft.json not found yet)"

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from idea_similarity_gate import run_gate_from_draft  # noqa: WPS433

    code, out = run_gate_from_draft(draft)
    if out.startswith("(skip idea gate"):
        auto = REPO_ROOT / "scripts" / "terminus_anti_spam_auto.py"
        code, out = _run(
            [
                sys.executable,
                str(auto),
                "ideas",
                "--json",
                str(draft),
                "--markdown-table",
            ]
        )

    block = f"## Idea similarity gate (auto)\n\n```\n{out}\n```\n"
    block += "Report: `jobs-local/idea-similarity-gate-last.json`\n"
    JOBS.mkdir(parents=True, exist_ok=True)
    HOOK_LAST.write_text(block, encoding="utf-8")
    return code, block


def extract_written_path(payload: dict) -> str | None:
    for key in ("file_path", "path", "target_file", "filePath"):
        if payload.get(key):
            return str(payload[key])
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "target_file", "filePath"):
            if tool_input.get(key):
                return str(tool_input[key])
    return None


def handle_file_event(path: str) -> tuple[int, str | None]:
    """Return (exit_code, additional_context or None)."""
    if _is_ideas_draft_path(path):
        code, block = run_ideas_screen()
        return code, block if block else None

    if not _is_post_create_trigger(path):
        return 0, None

    slug = slug_from_path(path)
    if not slug:
        return 0, None

    return run_task_pipeline(slug)


def handle_prompt_submit(
    task: str | None,
    *,
    is_ideas: bool,
    prompt: str = "",
    force_pipeline: bool = False,
) -> tuple[int, str | None]:
    parts: list[str] = []
    code = 0

    if is_ideas:
        c, block = run_ideas_screen(force=False, prompt=prompt)
        if block:
            code = max(code, c)
            parts.append(block)

    # Auto-detect slug from platform summary when user only pastes eval block
    resolved_task = task
    if not resolved_task and prompt.strip():
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        try:
            from auto_easy_platform_automation import detect_slug_from_summary  # noqa: WPS433

            resolved_task = detect_slug_from_summary(prompt)
        except Exception:
            resolved_task = None

    if resolved_task and locate_task_dir(resolved_task):
        skip_easy_finish = False
        skip_reviewer_finish = False
        task_dir = locate_task_dir(resolved_task)
        if prompt:
            reviewer_saved = save_reviewer_feedback_from_prompt(resolved_task, prompt)
            if reviewer_saved and task_dir:
                skip_reviewer_finish = True
                skip_easy_finish = True
                gate_code, gate_block = run_reviewer_feedback_gate(
                    resolved_task, task_dir, context=True
                )
                code = max(code, gate_code)
                parts.append(
                    f"**Reviewer context (auto-saved):** `{reviewer_saved}` — "
                    "triage vs accepted-feedback A-001…A-010 **before** edits.\n"
                )
                parts.append(gate_block)
            saved = save_trivial_easy_context_from_prompt(resolved_task, prompt)
            if saved:
                skip_easy_finish = True
                parts.append(
                    f"**TRIVIAL/EASY context (auto-saved):** `{saved}` — "
                    "Case 6 edits **this turn**; probes/finish run on **save** (not before edits).\n"
                )
                try:
                    from auto_easy_platform_automation import (  # noqa: WPS433
                        automation_context_block,
                        process_easy_paste,
                    )

                    auto_result = process_easy_paste(resolved_task, prompt)
                    parts.append(automation_context_block(resolved_task, auto_result))
                except Exception:
                    pass
        if skip_reviewer_finish and task_dir:
            audit_code, audit_block = run_post_create_audit(resolved_task, task_dir)
            parts.append(audit_block)
            code = max(code, audit_code)
            class_code, class_block = run_unacceptable_class(resolved_task, task_dir)
            parts.append(class_block)
            code = max(code, class_code)
            parts.append(
                "**Reviewer paste:** audit + gate only — apply triage fixes, **save**, "
                "then hook runs full `create_finish_to_zip` (sim **0.0** required).\n"
            )
        else:
            c, block = run_task_pipeline(
                resolved_task,
                force=force_pipeline,
                skip_easy_finish=skip_easy_finish,
            )
            if block:
                code = max(code, c)
                parts.append(block)

    if not parts:
        return 0, None
    return code, "\n".join(parts)


def write_ideas_draft_template() -> None:
    """Ensure ideas draft exists for hook when starting idea generation."""
    JOBS.mkdir(parents=True, exist_ok=True)
    draft = jobs_path(IDEAS_DRAFT_NAME, mkdir=True)
    if not draft.is_file():
        draft.write_text('{"ideas": []}\n', encoding="utf-8")
