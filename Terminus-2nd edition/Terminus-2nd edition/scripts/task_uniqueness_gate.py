#!/usr/bin/env python3
"""Task uniqueness gate — ideas (via idea_similarity_gate) and pack zip.

Policy: archive/terminus-rules-mdc/shared/task-uniqueness-gate.mdc

  python3 scripts/task_uniqueness_gate.py --pack-gate --task-dir tasks/<name>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jobs_local_paths import jobs_path  # noqa: E402
from task_uniqueness_policy import (  # noqa: E402
    UniquenessReport,
    audit_distinct_dimensions,
    audit_fabricated_synthetic_text,
    audit_similarity_rules,
    build_idea_uniqueness_report,
    format_uniqueness_table,
)

REPORT_JSON = jobs_path("task-uniqueness-gate-last.json")


def _read_instruction(task_dir: Path) -> str:
    for rel in ("instruction.md",):
        p = task_dir / rel
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    return ""


def _read_tags(task_dir: Path) -> tuple[str, ...]:
    toml = task_dir / "task.toml"
    if not toml.is_file():
        return ()
    text = toml.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"tags\s*=\s*\[(.*?)\]", text, re.DOTALL)
    if not m:
        return ()
    inner = m.group(1)
    return tuple(re.findall(r'"([^"]+)"', inner))


def _load_anti_spam_pack(slug: str) -> dict:
    for name in ("anti-spam-post-create-last.json", "anti-spam-last.json"):
        p = jobs_path(name)
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            if data.get("slug") == slug:
                return data
            results = data.get("results") or []
            for row in results:
                if row.get("slug") == slug:
                    return row
    return {}


def _load_unacceptable_classes(slug: str) -> list[str]:
    p = jobs_path("unacceptable-class-gate-last.json")
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if data.get("slug") != slug:
        return []
    failed = data.get("failed") or []
    return list(failed)


def pack_gate(task_dir: Path, *, quiet: bool = False) -> int:
    slug = task_dir.name
    instruction = _read_instruction(task_dir)
    tags = _read_tags(task_dir)
    spam = _load_anti_spam_pack(slug)
    failed_classes = _load_unacceptable_classes(slug)

    blockers = list(spam.get("blockers") or [])
    warnings = list(spam.get("warnings") or [])
    weighted = float(spam.get("weighted_score") or spam.get("similarity") or 0.0)
    unacceptable = list(spam.get("unacceptable_classes") or failed_classes)

    report = UniquenessReport()
    sim = audit_similarity_rules(
        unacceptable_classes=unacceptable,
        blockers=blockers,
        weighted=weighted,
        idea_threshold=0.85,
    )
    distinct = audit_distinct_dimensions(instruction=instruction, tags=tags)
    fab = audit_fabricated_synthetic_text(instruction.lower())

    for checks in (sim, fab, distinct):
        for check_id, status in checks.items():
            report.record(check_id, status, "" if status == "PASS" else check_id)
    report.finalize()

    payload = {
        "phase": "pack",
        "slug": slug,
        "verdict": report.verdict,
        "checks": report.checks,
        "violations": report.violations,
        "weighted_score": weighted,
        "unacceptable_classes": unacceptable,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if not quiet:
        print(f"Task uniqueness gate: {report.verdict} — {slug}")
        print(format_uniqueness_table(report))
        if report.violations:
            print("Violations:")
            for v in report.violations:
                print(f"  - {v}")
        print(f"Report: {REPORT_JSON}")

    return 0 if report.verdict == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Task uniqueness gate")
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument("--task-dir", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.pack_gate:
        if not args.task_dir or not args.task_dir.is_dir():
            print("ERROR: --pack-gate requires --task-dir", file=sys.stderr)
            return 2
        return pack_gate(args.task_dir.resolve(), quiet=args.quiet)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
