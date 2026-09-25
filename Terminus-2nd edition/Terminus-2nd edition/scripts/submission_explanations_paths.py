"""Paths and parsing for submission-explanations/<slug>.md (platform form only)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPLANATIONS_DIR = REPO_ROOT / "submission-explanations"

REQUIRED_SECTIONS = (
    "Difficulty Explanation",
    "Solution Explanation",
    "Verification Explanation",
)

SECTION_RE = re.compile(
    r"^##\s+(Difficulty Explanation|Solution Explanation|Verification Explanation)\s*$",
    re.M,
)


def explanations_path(slug: str) -> Path:
    return EXPLANATIONS_DIR / f"{slug}.md"


def sentence_count(text: str) -> int:
    """Rough sentence count for paragraph validation."""
    t = re.sub(r"\s+", " ", text.strip())
    if not t:
        return 0
    parts = re.split(r"(?<=[.!?])(?=\S)", t)
    return len([p for p in parts if p.strip()])


def prose_line_count(text: str) -> int:
    """Non-empty lines in a section body (hard cap for platform paste)."""
    return sum(1 for line in text.splitlines() if line.strip())


def word_count(text: str) -> int:
    t = re.sub(r"\s+", " ", text.strip())
    return len(t.split()) if t else 0


def prose_style_issues(text: str) -> list[str]:
    """Heuristic: plain human prose — minimal punctuation spam and digits."""
    issues: list[str] = []
    if re.search(r"[.,]\s", text):
        issues.append(
            "no space after period or comma — write tight human prose like done.Next or a,b"
        )
    if ";" in text:
        issues.append("avoid semicolons — use full stops and and/but/so")
    colons = text.count(":")
    if colons > 0:
        issues.append(
            f"avoid colons (found {colons}) — rephrase without label lists or path dumps"
        )
    if "—" in text or "–" in text:
        issues.append("avoid em/en dashes — use commas or a new sentence")
    hyphenated = len(re.findall(r"\b\w+-\w+", text))
    if hyphenated > 2:
        issues.append(
            f"too many hyphenated compounds (found {hyphenated}) — use spaces or rephrase"
        )
    digits = len(re.findall(r"\d", text))
    if digits > 0:
        issues.append(
            f"avoid digits (found {digits}) — spell counts in words unless truly unavoidable"
        )
    slashes = text.count("/")
    if slashes > 1:
        issues.append(
            f"too many path slashes (found {slashes}) — describe fixtures in plain words"
        )
    return issues


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def task_dir_for_slug(slug: str) -> Path | None:
    for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
        cand = base / slug
        if (cand / "task.toml").is_file():
            return cand
    return None
