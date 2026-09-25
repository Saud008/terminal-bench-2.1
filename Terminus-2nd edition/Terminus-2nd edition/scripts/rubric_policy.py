#!/usr/bin/env python3
"""Shared platform rubric validation (rubrics/<slug>.md — not in task zip).

Positive cumulative score per block: 10–40 (Snorkel / Terminus).
Scores: ±1, ±2, ±3, ±5 only. ≥3 negative criteria overall.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_SCORES = frozenset({1, 2, 3, 5})
SCORE_SUFFIX = re.compile(r",\s*([+-]?)(1|2|3|5)\s*$")
RUBRIC_HEADER = re.compile(r"^#\s*Rubric\s+(\d+)\s*$", re.IGNORECASE)


@dataclass
class RubricBlock:
    label: str
    lines: list[str] = field(default_factory=list)
    positive_total: int = 0
    negative_count: int = 0


@dataclass
class RubricValidation:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocks: list[RubricBlock] = field(default_factory=list)
    total_negatives: int = 0
    criterion_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_score(line: str) -> int | None:
    m = SCORE_SUFFIX.search(line.strip())
    if not m:
        return None
    sign, val = m.group(1), int(m.group(2))
    if sign == "-":
        return -val
    return val


def is_criterion_line(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#"):
        return False
    return s.startswith("Agent") and parse_score(s) is not None


def split_blocks(lines: list[str]) -> list[RubricBlock]:
    blocks: list[RubricBlock] = []
    current = RubricBlock(label="default")

    for raw in lines:
        stripped = raw.strip()
        m = RUBRIC_HEADER.match(stripped)
        if m:
            if current.lines:
                blocks.append(current)
            current = RubricBlock(label=f"Rubric {m.group(1)}")
            continue
        if is_criterion_line(raw):
            current.lines.append(raw.rstrip())

    if current.lines:
        blocks.append(current)

    for block in blocks:
        pos = 0
        neg = 0
        for ln in block.lines:
            score = parse_score(ln)
            if score is None:
                continue
            if score > 0:
                pos += score
            else:
                neg += 1
        block.positive_total = pos
        block.negative_count = neg

    return blocks


def read_milestone_count(task_dir: Path | None) -> int:
    if not task_dir or not (task_dir / "task.toml").is_file():
        return 0
    text = (task_dir / "task.toml").read_text(encoding="utf-8")
    m = re.search(r"number_of_milestones\s*=\s*(\d+)", text)
    if not m:
        return 0
    return int(m.group(1))


def validate_rubric_text(
    text: str,
    slug: str,
    *,
    task_dir: Path | None = None,
    milestone_count: int | None = None,
) -> RubricValidation:
    result = RubricValidation()
    if milestone_count is None:
        milestone_count = read_milestone_count(task_dir)

    if f"tasks/{slug}/" not in text and f"pending/{slug}/" not in text:
        result.errors.append(f"Header must name tasks/{slug}/ (or pending/{slug}/)")

    lines = text.splitlines()
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("**"):
            continue
        if s.startswith("Agent"):
            score = parse_score(s)
            if score is None:
                result.errors.append(f"Invalid rubric line (score must be ±1/2/3/5): {s[:72]}")
            elif abs(score) not in VALID_SCORES:
                result.errors.append(f"Forbidden score (never 4): {s[:72]}")
        elif s and not s.startswith("|") and not s.startswith("-"):
            # Allow markdown table rows in header only; stray prose is a warning
            if not s.startswith("```"):
                result.warnings.append(f"Non-criterion line ignored: {s[:60]}")

    blocks = split_blocks(lines)
    if not blocks or not any(b.lines for b in blocks):
        result.errors.append("No Agent …, ±N criterion lines found")
        return result

    result.blocks = blocks
    result.criterion_count = sum(len(b.lines) for b in blocks)
    result.total_negatives = sum(b.negative_count for b in blocks)

    if result.total_negatives < 3:
        result.errors.append(f"Need ≥3 negative criteria overall; found {result.total_negatives}")

    rubric_headers = [ln for ln in lines if RUBRIC_HEADER.match(ln.strip())]
    is_milestone_file = len(rubric_headers) > 0 or milestone_count > 0

    if milestone_count > 0 and not rubric_headers:
        result.errors.append(
            f"Milestone task (number_of_milestones={milestone_count}) — use "
            "# Rubric 1 / # Rubric 2 headers; each block positive total 10–40"
        )

    if rubric_headers and milestone_count > 0 and len(rubric_headers) != milestone_count:
        result.warnings.append(
            f"Found {len(rubric_headers)} # Rubric headers but task.toml "
            f"number_of_milestones={milestone_count}"
        )

    for block in blocks:
        label = block.label
        pos = block.positive_total
        if pos < 10:
            result.errors.append(f"{label}: positive cumulative score {pos} — need 10–40")
        elif pos > 40:
            result.errors.append(f"{label}: positive cumulative score {pos} — need 10–40")
        if is_milestone_file and milestone_count > 0 and block.negative_count < 1:
            result.errors.append(f"{label}: milestone rubrics need ≥1 negative criterion")

    return result


def validate_rubric_file(
    path: Path,
    slug: str,
    *,
    task_dir: Path | None = None,
) -> RubricValidation:
    result = RubricValidation()
    if not path.is_file():
        result.errors.append(f"Missing {path} — run write_platform_rubric.py --slug {slug}")
        return result
    text = path.read_text(encoding="utf-8")
    return validate_rubric_text(text, slug, task_dir=task_dir)


def format_report(slug: str, validation: RubricValidation) -> str:
    lines = [f"Platform rubric — {slug}"]
    for block in validation.blocks:
        lines.append(
            f"  {block.label}: +{block.positive_total} positive, "
            f"{block.negative_count} negative(s), {len(block.lines)} line(s)"
        )
    if validation.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {w}" for w in validation.warnings)
    if validation.errors:
        lines.append("Errors:")
        lines.extend(f"  - {e}" for e in validation.errors)
    else:
        lines.append("PASS — positive cumulative 10–40 per block, ≥3 negatives")
    return "\n".join(lines)
