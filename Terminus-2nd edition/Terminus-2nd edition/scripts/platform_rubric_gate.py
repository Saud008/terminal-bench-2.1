#!/usr/bin/env python3
"""Validate rubrics/<slug>.md before pack (platform upload form).

  python3 scripts/platform_rubric_gate.py --check --slug my-task
  python3 scripts/platform_rubric_gate.py --pack-gate --slug my-task

Positive cumulative score per rubric block: 10–40 (sum of +1/+2/+3/+5 lines only).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import RUBRICS_DIR, rubric_path  # noqa: E402
from rubric_policy import format_report, validate_rubric_file  # noqa: E402


def _task_dir_for_slug(slug: str) -> Path | None:
    for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
        cand = base / slug
        if (cand / "task.toml").is_file():
            return cand
    return None


def write_report(slug: str, validation, path: Path) -> None:
    payload = {
        "slug": slug,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pass": validation.ok,
        "errors": validation.errors,
        "warnings": validation.warnings,
        "blocks": [
            {
                "label": b.label,
                "positive_total": b.positive_total,
                "negative_count": b.negative_count,
                "lines": len(b.lines),
            }
            for b in validation.blocks
        ],
        "total_negatives": validation.total_negatives,
        "criterion_count": validation.criterion_count,
        "rubric_file": str(path.relative_to(REPO_ROOT)) if path.is_file() else "",
    }
    out = REPO_ROOT / "jobs-local" / "gates" / "platform-rubric-last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_check(slug: str) -> tuple[int, str]:
    slug = slug.strip().strip("/")
    path = rubric_path(slug)
    task_dir = _task_dir_for_slug(slug)
    validation = validate_rubric_file(path, slug, task_dir=task_dir)
    write_report(slug, validation, path)
    report = format_report(slug, validation)
    return (0 if validation.ok else 1), report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pack-gate", action="store_true")
    args = parser.parse_args()

    if not args.check and not args.pack_gate:
        parser.error("use --check or --pack-gate")

    rc, report = run_check(args.slug)
    print(report)
    if rc != 0:
        print(
            f"\nFix rubrics/{args.slug}.md — policy: shared/platform-rubric-gate.mdc",
            file=sys.stderr,
        )
        print(
            f"  python3 scripts/write_platform_rubric.py --slug {args.slug} --lines-file /tmp/rubric.txt",
            file=sys.stderr,
        )
        print("  Details: jobs-local/gates/platform-rubric-last.json", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
