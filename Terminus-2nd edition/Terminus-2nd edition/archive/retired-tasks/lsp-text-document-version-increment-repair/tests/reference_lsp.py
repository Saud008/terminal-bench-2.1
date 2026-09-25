"""Independent reference for DocLint LSP document sync and diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Position:
    line: int
    character: int


@dataclass
class Range:
    start: Position
    end: Position


@dataclass
class StagedEdit:
    range: Range
    text: str


@dataclass
class Document:
    uri: str
    text: str
    version: int = 0
    staging: list[StagedEdit] = field(default_factory=list)
    last_change_version: int | None = None


def byte_offset(text: str, line: int, character: int) -> int:
    """Map LSP (line, UTF-16 character) to a UTF-8 byte offset."""
    lines = text.split("\n")
    if line >= len(lines):
        return len(text.encode("utf-8"))
    prefix = "\n".join(lines[:line])
    line_start = len(prefix.encode("utf-8")) + (len("\n") if line > 0 else 0)
    line_str = lines[line]
    utf16 = 0
    byte = line_start
    for ch in line_str:
        if utf16 == character:
            break
        utf16 += len(ch.encode("utf-16-le")) // 2
        byte += len(ch.encode("utf-8"))
    return byte


def apply_edits(base: str, edits: list[StagedEdit]) -> str:
    ordered = sorted(
        edits,
        key=lambda e: (e.range.start.line, e.range.start.character),
        reverse=True,
    )
    out = base
    for edit in ordered:
        start = byte_offset(out, edit.range.start.line, edit.range.start.character)
        end = byte_offset(out, edit.range.end.line, edit.range.end.character)
        raw = out.encode("utf-8")
        out = (raw[:start] + edit.text.encode("utf-8") + raw[end:]).decode("utf-8")
    return out


def working_text(doc: Document) -> str:
    if not doc.staging:
        return doc.text
    return apply_edits(doc.text, doc.staging)


def merge_staging(doc: Document) -> None:
    if not doc.staging:
        return
    doc.text = working_text(doc)
    doc.staging.clear()


def full_range(text: str) -> Range:
    lines = text.split("\n")
    line = max(len(lines) - 1, 0)
    character = len(lines[-1].encode("utf-16-le")) // 2 if lines else 0
    return Range(Position(0, 0), Position(line, character))


def changes_to_edits(changes: list[dict[str, Any]], full_text: str) -> list[StagedEdit]:
    edits: list[StagedEdit] = []
    for change in changes:
        raw = change.get("range")
        if raw is None:
            rng = full_range(full_text)
        else:
            rng = Range(
                Position(raw["start"]["line"], raw["start"]["character"]),
                Position(raw["end"]["line"], raw["end"]["character"]),
            )
        edits.append(StagedEdit(rng, change.get("text", "")))
    return edits


def handle_did_change(doc: Document, new_version: int, changes: list[dict[str, Any]]) -> None:
    if doc.last_change_version == new_version:
        return
    if new_version <= doc.version:
        return
    base = working_text(doc)
    doc.staging.extend(changes_to_edits(changes, base))
    doc.version = new_version
    doc.last_change_version = new_version


def handle_did_close(doc: Document) -> None:
    merge_staging(doc)


def compute_diagnostics(text: str) -> dict[str, int]:
    todo_count = 0
    i = 0
    while i + 3 < len(text):
        if text[i : i + 4] == "TODO":
            before_ok = i == 0 or not text[i - 1].isalnum()
            after_ok = i + 4 >= len(text) or not text[i + 4].isalnum()
            if before_ok and after_ok:
                todo_count += 1
        i += 1
    paren_delta = text.count("(") - text.count(")")
    wide_char_lines = sum(
        1 for line in text.splitlines() if any(len(ch.encode("utf-16-le")) // 2 > 1 for ch in line)
    )
    total = todo_count + abs(paren_delta) + wide_char_lines
    return {
        "todo_count": todo_count,
        "paren_delta": paren_delta,
        "wide_char_lines": wide_char_lines,
        "total": total,
    }


def export_snapshot(doc: Document) -> dict[str, Any]:
    merge_staging(doc)
    diag = compute_diagnostics(doc.text)
    return {
        "uri": doc.uri,
        "version": doc.version,
        "text": doc.text,
        "diagnostics": diag,
        "staging_pending": len(doc.staging),
    }


def replay_steps(uri: str, initial: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    doc = Document(uri=uri, text=initial)
    last_export: dict[str, Any] | None = None
    for step in steps:
        op = step["op"]
        if op == "open":
            doc = Document(uri=uri, text=initial)
        elif op == "change":
            handle_did_change(doc, int(step["version"]), step.get("changes", []))
        elif op == "close":
            handle_did_close(doc)
        elif op == "export":
            last_export = export_snapshot(doc)
    if last_export is None:
        last_export = export_snapshot(doc)
    return last_export


def load_batch_line(line: str) -> list[dict[str, Any]]:
    payload = json.loads(line)
    return payload["steps"]


def mutate_changes(changes: list[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    suffix = {"alpha01": "", "beta22": " // probe", "gamma99": " /* x */"}.get(seed, "")
    out = []
    for change in changes:
        c = json.loads(json.dumps(change))
        if suffix and c.get("text"):
            c["text"] = c["text"] + suffix
        out.append(c)
    return out
