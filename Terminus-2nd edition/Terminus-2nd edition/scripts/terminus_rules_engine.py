#!/usr/bin/env python3
"""Terminus rules engine — loads ONE consolidated .mdc per phase (full verbatim rules).

  python3 scripts/build_consolidated_rules.py   # rebuild bundles from archive
  python3 scripts/terminus_rules_engine.py --engine ENGINE_7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from terminus_engine_registry import (  # noqa: E402
    ENGINE_1_IDEAS,
    ENGINE_2_ANTI_SPAM,
    ENGINE_3_CREATE,
    ENGINE_4_AUDIT,
    ENGINE_5_VERIFY,
    ENGINE_6_ZIP,
    ENGINE_7_REVISE,
    PHASE_LABELS,
    detect_verify_zip,
    create_audit_loop_footer,
    idea_gate_footer,
    first_submit_engine_footer,
    unacceptable_class_footer,
    no_easy_upload_footer,
    standing_requirements_footer,
    submission_explanations_footer,
    platform_rubric_footer,
    task_generation_footer,
    mdc_path_for_engine,
    resolve_engine,
)

TERMINUS_ENGINE = "TERMINUS"

ANTI_SPAM_OUTPUT_FILES = {
    "hook_every_edit_prompt": "jobs-local/anti-spam-hook-last.txt",
    "ideas_batch": "jobs-local/anti-spam-ideas-last.json",
    "post_create_save": "jobs-local/anti-spam-post-create-last.json",
    "pack_zip": "jobs-local/anti-spam-last.txt",
    "corpus_index_cache": "jobs-local/anti-spam-index.json",
}


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip("\n")
    return text


def read_engine_policy(engine: str) -> str:
    """Full verbatim policy for one ENGINE (consolidated .mdc)."""
    path = mdc_path_for_engine(engine)
    if not path.is_file():
        return (
            f"**ERROR:** missing `{path.relative_to(REPO_ROOT)}`. "
            "Run: `python3 scripts/build_consolidated_rules.py`"
        )
    return _strip_frontmatter(path.read_text(encoding="utf-8", errors="replace"))


def anti_spam_policy_markdown() -> str:
    return read_engine_policy(ENGINE_2_ANTI_SPAM)


def build_route_context(
    *,
    engine: str,
    phase: str,
    router: str,
    case_file: str | None,
    reason: str,
    confidence: str,
    task: str | None,
    tagged: list[str],
    summary_note: str = "",
    ask: str | None = None,
    **_kwargs,
) -> str:
    mdc_rel = mdc_path_for_engine(engine).relative_to(REPO_ROOT)
    body = read_engine_policy(engine)

    lines = [
        f"## {TERMINUS_ENGINE} — phase `{PHASE_LABELS.get(engine, engine)}`",
        "",
        f"**Single policy file (full exact rules):** `{mdc_rel}`",
        "",
        "Only this phase bundle applies. Do **not** load other `engines/ENGINE_*.mdc` files.",
        "",
        body,
        "",
        "---",
        "",
        "### Routing",
        "",
        f"- **Phase label:** {phase}",
        f"- **Router:** `{router}`",
        f"- **Case:** `{case_file or '(router only)'}`",
        f"- **Reason:** {reason}",
        f"- **Confidence:** {confidence}",
        f"- **Policy file:** `{mdc_rel}`",
    ]
    if task:
        lines.append(f"- **Task:** `tasks/{task}/` or `pending/{task}/`")
    if tagged:
        lines.append(f"- **Hints:** {', '.join(tagged)} (summary wins)")
    if summary_note:
        lines.append(f"- **{summary_note}**")

    lines.append("")
    lines.append("### Prompts (Read when router names them)")
    lines.append("")
    lines.append(f"- `{router}`")
    if case_file:
        for part in case_file.replace("→", " ").split():
            part = part.strip()
            if part.startswith("prompts/"):
                lines.append(f"- `{part}`")
    if "trivial" in router.lower() or "easy" in router.lower():
        lines.extend(
            [
                "- `prompts/trivial-repo-wide.md`",
                "- `prompts/trivial-case-6.md`",
                "- `prompts/sp-hard-create-revise.md`",
            ]
        )
    if engine in (ENGINE_3_CREATE, ENGINE_5_VERIFY, ENGINE_6_ZIP, ENGINE_4_AUDIT):
        lines.extend(
            [
                "- `prompts/sp-hard-create-revise.md`",
                "- `revise/trivial-hardening-probes.mdc` (probe table before first zip)",
            ]
        )

    lines.extend(idea_gate_footer(engine))
    lines.extend(task_generation_footer(engine))
    lines.extend(create_audit_loop_footer(engine))
    lines.extend(first_submit_engine_footer(engine))
    lines.extend(unacceptable_class_footer(engine))
    lines.extend(no_easy_upload_footer(engine))
    lines.extend(submission_explanations_footer(engine))
    lines.extend(platform_rubric_footer(engine))
    lines.extend(standing_requirements_footer())

    lines.append("")
    lines.append(
        "**Do:** quote 2–3 summary facts · obey anti-spam FAIL/WARN · inspect task files · "
        "one clarifying question only if confidence=low."
    )

    if ask:
        lines.append("")
        lines.append(f"**Ask user:** {ask}")

    return "\n".join(lines)


def enrich_engine_from_prompt(
    phase: str,
    router: str,
    prompt: str,
    tagged: list[str],
) -> str:
    verify, zip_phase = detect_verify_zip(prompt)
    if "verify" in tagged and "zip" not in tagged:
        verify = True
    if "zip" in tagged:
        zip_phase = True
    if phase == "G" or phase == "F" or (zip_phase and not verify):
        return ENGINE_6_ZIP
    if phase == "E" or verify:
        return ENGINE_5_VERIFY
    if phase == "A" or "newidea" in tagged:
        return ENGINE_1_IDEAS
    if phase == "C" or "audit" in tagged:
        return ENGINE_4_AUDIT
    if (
        "create" in tagged
        or "b (create)" in phase.lower()
        or any(x in prompt.lower() for x in ("@create", "new-task-pipeline"))
    ):
        return ENGINE_3_CREATE
    return resolve_engine(phase, router, verify=verify, zip_phase=zip_phase)


def tail_report(path_key: str) -> str:
    rel = ANTI_SPAM_OUTPUT_FILES.get(path_key, "")
    if not rel:
        return ""
    p = REPO_ROOT / rel
    if not p.is_file():
        return f"(no report yet: `{rel}`)"
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > 4000:
        text = "…\n" + text[-4000:]
    return text


def cli() -> int:
    parser = argparse.ArgumentParser(description="Terminus consolidated .mdc engine")
    parser.add_argument("--anti-spam-policy", action="store_true")
    parser.add_argument("--list-engines", action="store_true")
    parser.add_argument("--engine", default=ENGINE_7_REVISE)
    parser.add_argument("--tail", choices=list(ANTI_SPAM_OUTPUT_FILES.keys()))
    parser.add_argument("--path-only", action="store_true")
    args = parser.parse_args()

    if args.anti_spam_policy:
        print(anti_spam_policy_markdown())
    elif args.list_engines:
        for k, v in PHASE_LABELS.items():
            p = mdc_path_for_engine(k)
            print(f"{k}: {v} → {p.relative_to(REPO_ROOT)}")
    elif args.tail:
        print(tail_report(args.tail))
    elif args.path_only:
        print(mdc_path_for_engine(args.engine).relative_to(REPO_ROOT))
    else:
        print(read_engine_policy(args.engine))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
