#!/usr/bin/env python3
"""Validate submission-explanations/<slug>.md before pack (platform upload form).

  python3 scripts/submission_explanations_gate.py --check --slug my-task
  python3 scripts/submission_explanations_gate.py --pack-gate --slug my-task
  python3 scripts/submission_explanations_gate.py --ensure --slug my-task
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from submission_explanations_paths import (  # noqa: E402
    explanations_path,
    parse_sections,
    prose_line_count,
    prose_style_issues,
    sentence_count,
    word_count,
)

MAX_SENTENCES = 2
MIN_SENTENCES = 1
MAX_PROSE_LINES = 3
MAX_WORDS_HINT = 80

BANNED_PHRASES = (
    "in conclusion",
    "furthermore",
    "it is important to note",
    "it is worth noting",
    "this task challenges",
    "as an ai",
    "delve into",
    "comprehensive overview",
    "leverage",
    "utilize",
    "plays a crucial role",
    "multifaceted",
    "in today's",
)

# Difficulty must answer *why hard* — not lead with verification/oracle/CI framing.
DIFFICULTY_BAD_LEADS = (
    "pytest",
    "the oracle",
    "oracle copies",
    "test.sh rebuilds",
    "ruff ",
    "docker verify",
    "we fixed",
    "tests verify",
    "verification explanation",
)

# Solution should not re-open the difficulty essay.
SOLUTION_DIFFICULTY_LEADS = (
    "this task is hard",
    "this task is marked",
    "agents struggle because",
    "agents tend to",
    "frontier models",
    "easy to miss",
)

# Verification must describe how tests prove behavior.
VERIFICATION_REQUIRED_HINTS = (
    "pytest",
    "test",
    "subprocess",
    "reference",
    "fixture",
    "harness",
    "oracle",
    "rebuild",
    "cli",
    "subprocess",
    "hidden",
    "mutat",
    "independent",
    "recomput",
)


def _section_fit_errors(title: str, body: str) -> list[str]:
    """Heuristic: each section answers its platform prompt."""
    errors: list[str] = []
    low = body.lower()
    lead = low[:120]

    if title == "Difficulty Explanation":
        for phrase in DIFFICULTY_BAD_LEADS:
            if lead.startswith(phrase) or f". {phrase}" in lead[:80]:
                errors.append(
                    f"## {title}: opens with verification/oracle/CI — explain why the task is "
                    f"difficult for humans/agents, not how you tested"
                )
                break
        if not re.search(
            r"\b(marked|feels)\s+(easy|medium|hard)\s+because\b",
            low,
        ) and not re.search(r"\b(easy|medium|hard)\s+because\b", low[:120]):
            errors.append(
                f"## {title}: open with '<difficulty> because ...' "
                f"(e.g. marked hard because ...)"
            )
        verify_hits = sum(1 for p in ("pytest", "test.sh", "ruff", "docker verify", "reward ") if p in low)
        if verify_hits >= 3:
            errors.append(
                f"## {title}: too much verification/CI language — move test details to Verification Explanation"
            )

    elif title == "Solution Explanation":
        for phrase in SOLUTION_DIFFICULTY_LEADS:
            if lead.startswith(phrase):
                errors.append(
                    f"## {title}: reads like Difficulty — describe high-level approach and key insight"
                )
                break

    elif title == "Verification Explanation":
        if not any(h in low for h in VERIFICATION_REQUIRED_HINTS):
            errors.append(
                f"## {title}: explain how tests verify correctness (reference, CLI, fixtures, anti-cheat)"
            )
        difficulty_hits = sum(
            1
            for p in (
                "agents struggle",
                "agents tend",
                "frontier models",
                "why this is hard",
                "marked hard because",
                "easy to miss when",
            )
            if p in low
        )
        if difficulty_hits >= 2:
            errors.append(
                f"## {title}: too much difficulty framing — focus on what pytest/CLI checks prove"
            )

    return errors


def validate_file(path: Path, slug: str) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"Missing {path.relative_to(REPO_ROOT)} — run write_submission_explanations.py --draft"]

    text = path.read_text(encoding="utf-8")
    if f"tasks/{slug}/" not in text and f"pending/{slug}/" not in text:
        errors.append(f"Header must name tasks/{slug}/ (or pending/{slug}/)")

    if "```" in text:
        errors.append("Remove fenced code blocks — platform wants plain paragraphs")

    sections = parse_sections(text)
    for title in ("Difficulty Explanation", "Solution Explanation", "Verification Explanation"):
        body = sections.get(title, "").strip()
        if not body:
            errors.append(f"Missing or empty section: ## {title}")
            continue
        n = sentence_count(body)
        if n < MIN_SENTENCES:
            errors.append(f"## {title}: need {MIN_SENTENCES}–{MAX_SENTENCES} sentences (found ~{n})")
        elif n > MAX_SENTENCES:
            errors.append(f"## {title}: max {MAX_SENTENCES} sentences (found ~{n}) — trim to one or two")
        lines = prose_line_count(body)
        if lines > MAX_PROSE_LINES:
            errors.append(
                f"## {title}: max {MAX_PROSE_LINES} prose lines (found {lines}) — one short paragraph"
            )
        words = word_count(body)
        if words > MAX_WORDS_HINT:
            errors.append(f"## {title}: ~{words} words — trim toward ≤{MAX_WORDS_HINT} per section")
        low = body.lower()
        for phrase in BANNED_PHRASES:
            if phrase in low:
                errors.append(f"## {title}: rewrite without template phrase “{phrase}”")
        for issue in prose_style_issues(body):
            errors.append(f"## {title}: {issue}")
        errors.extend(_section_fit_errors(title, body))

    return errors


def draft_explanations(slug: str) -> tuple[int, str]:
    script = REPO_ROOT / "scripts" / "write_submission_explanations.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--slug", slug, "--draft"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def ensure_explanations(slug: str) -> tuple[int, str]:
    """Auto-draft when file missing; re-validate. Invalid existing file → manual fix."""
    path = explanations_path(slug)
    errors = validate_file(path, slug)
    if not errors:
        return 0, f"already valid — {path.relative_to(REPO_ROOT)}"

    missing_only = all(
        e.startswith("Missing ") or e.startswith("Missing or empty")
        for e in errors
    )
    if path.is_file() and not missing_only:
        return 1, "file exists but invalid — edit manually:\n" + "\n".join(f"  - {e}" for e in errors)

    rc, out = draft_explanations(slug)
    if rc != 0:
        return rc, f"auto-draft failed\n{out}"

    errors = validate_file(explanations_path(slug), slug)
    if errors:
        return 1, "draft written but still invalid:\n" + "\n".join(f"  - {e}" for e in errors)
    return 0, out or f"wrote {explanations_path(slug).relative_to(REPO_ROOT)}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument(
        "--ensure",
        action="store_true",
        help="Auto-draft from task tree when file missing (pack_zip default)",
    )
    args = parser.parse_args()

    slug = args.slug.strip().strip("/")
    path = explanations_path(slug)

    if args.ensure or args.pack_gate:
        rc, msg = ensure_explanations(slug)
        if rc != 0:
            print(f"Submission explanations: FAIL — {slug}", file=sys.stderr)
            print(msg, file=sys.stderr)
            print(
                f"  Fix: python3 scripts/write_submission_explanations.py --slug {slug} --draft",
                file=sys.stderr,
            )
            return 1
        if args.ensure and not args.pack_gate:
            print(f"Submission explanations: ENSURE OK — {msg}")
            return 0

    errors = validate_file(path, slug)
    if errors:
        print(f"Submission explanations: FAIL — {slug}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            f"  Fix: python3 scripts/write_submission_explanations.py --slug {slug} --draft",
            file=sys.stderr,
        )
        return 1

    print(f"Submission explanations: PASS — {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
