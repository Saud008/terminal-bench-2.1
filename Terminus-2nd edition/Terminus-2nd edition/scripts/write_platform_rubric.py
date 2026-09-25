#!/usr/bin/env python3
"""Write platform upload rubric to rubrics/<slug>.md (never tasks/ or zip).

  python3 scripts/write_platform_rubric.py --slug my-task --lines-file rubric.txt
  python3 scripts/write_platform_rubric.py --slug my-task --text "Agent ..."

Each file starts with task slug header to avoid cross-task conflicts.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import RUBRICS_DIR, rubric_path  # noqa: E402
from rubric_policy import validate_rubric_text  # noqa: E402


def _validate_line(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if not s.startswith("Agent"):
        return f"not Agent-prefixed: {s[:60]}"
    from rubric_policy import parse_score

    if parse_score(s) is None:
        return f"bad score suffix (use ±1/2/3/5): {s[:60]}"
    return None


def _task_dir_for_slug(slug: str) -> Path | None:
    for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
        cand = base / slug
        if (cand / "task.toml").is_file():
            return cand
    return None


def write_rubric(slug: str, body_lines: list[str], *, milestone: bool = False, force: bool = False) -> Path:
    slug = slug.strip().strip("/")
    if not slug or "/" in slug or " " in slug:
        raise ValueError(f"Invalid slug for rubric filename: {slug!r}")

    task_dir = _task_dir_for_slug(slug)
    if not task_dir and not force:
        raise ValueError(
            f"No tasks/{slug}/ or pending/{slug}/ — rubric file must match the task slug from chat. "
            "Use --force only if the folder is not created yet."
        )
    errors = []
    clean: list[str] = []
    for ln in body_lines:
        err = _validate_line(ln)
        if err:
            errors.append(err)
        elif ln.strip():
            clean.append(ln.rstrip())

    if errors:
        raise ValueError("Invalid rubric lines:\n" + "\n".join(errors[:10]))

    RUBRICS_DIR.mkdir(parents=True, exist_ok=True)
    path = rubric_path(slug)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = [
        f"# Platform rubric — {slug}",
        "",
        f"**Task folder:** tasks/{slug}/",
        f"**Written:** {ts}",
        "**Upload:** copy lines below into Snorkel platform rubric form (not in zip).",
        "",
    ]
    if milestone:
        header.append("Use `# Rubric 1` / `# Rubric 2` headers per milestone on platform.")
        header.append("")

    content = "\n".join(header + clean) + "\n"
    validation = validate_rubric_text(content, slug, task_dir=task_dir)
    if not validation.ok:
        raise ValueError("Rubric policy failed:\n" + "\n".join(validation.errors[:12]))

    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--text", default="")
    parser.add_argument("--lines-file", type=Path, default=None)
    parser.add_argument("--milestone", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write even if tasks/<slug>/ missing (CREATE before task.toml exists)",
    )
    args = parser.parse_args()

    text = args.text
    if args.lines_file and args.lines_file.is_file():
        text = args.lines_file.read_text(encoding="utf-8")

    lines = text.splitlines()
    if not any(l.strip() for l in lines):
        print("ERROR: empty rubric body", file=sys.stderr)
        return 1
    try:
        path = write_rubric(args.slug, lines, milestone=args.milestone, force=args.force)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
