"""Minimal unified-diff applier for oracle patches (no GNU patch required)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_hunk(lines: list[str], hunk_lines: list[str], old_start: int) -> tuple[list[str], int]:
    idx = old_start - 1
    out = lines[:idx]
    deleted = 0
    added = 0
    i = 0
    while i < len(hunk_lines):
        row = hunk_lines[i]
        if row.startswith("\\"):
            i += 1
            continue
        tag = row[:1]
        body = row[1:] if tag in " +-" else row
        if tag == " ":
            if idx >= len(lines) or lines[idx] != body:
                raise ValueError(f"context mismatch at line {idx + 1}: expected {body!r} got {lines[idx] if idx < len(lines) else None!r}")
            out.append(lines[idx])
            idx += 1
        elif tag == "-":
            if idx >= len(lines) or lines[idx] != body:
                raise ValueError(f"delete mismatch at line {idx + 1}: expected {body!r}")
            idx += 1
            deleted += 1
        elif tag == "+":
            out.append(body)
            added += 1
        else:
            raise ValueError(f"bad hunk line: {row!r}")
        i += 1
    out.extend(lines[idx:])
    return out, added - deleted


def apply_patch(root: Path, patch_text: str) -> None:
    lines = patch_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("--- "):
            i += 1
            continue
        old_path = line[4:].split("\t", 1)[0].strip()
        i += 1
        if i >= len(lines) or not lines[i].startswith("+++ "):
            raise ValueError("missing +++ header")
        i += 1
        target = root / old_path
        if not target.is_file():
            raise FileNotFoundError(f"patch target missing: {target}")
        file_lines = target.read_text(encoding="utf-8").splitlines()
        offset = 0
        while i < len(lines) and lines[i].startswith("@@ "):
            m = HUNK_RE.match(lines[i])
            if not m:
                raise ValueError(f"bad hunk header: {lines[i]!r}")
            old_start = int(m.group(1)) + offset
            i += 1
            hunk: list[str] = []
            while i < len(lines) and not lines[i].startswith(("@@ ", "--- ")):
                hunk.append(lines[i])
                i += 1
            file_lines, delta = apply_hunk(file_lines, hunk, old_start)
            offset += delta
        text = "\n".join(file_lines)
        if not text.endswith("\n"):
            text += "\n"
        target.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: apply_unified_diff.py <root> <patch-file>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    patch_path = Path(sys.argv[2])
    apply_patch(root, patch_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
