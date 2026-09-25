"""Independent pipe-table parser per /app/docs/table-extension-contract.md."""

from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawCell:
    text: str
    colspan: int
    rowspan: int


@dataclass
class CellExport:
    text: str
    col: int
    colspan: int
    rowspan: int


def split_row(line: str) -> list[str]:
    trimmed = line.strip()
    inner = trimmed.strip("|") if trimmed.startswith("|") else trimmed
    cells: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner) and inner[i + 1] == "|":
            current.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(current).strip())
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    cells.append("".join(current).strip())
    return cells


def is_alignment_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-+:?", c.strip()) for c in cells)


def parse_colspan_prefix(text: str) -> tuple[str, int]:
    m = re.fullmatch(r">(\d+)<(.*)", text, re.DOTALL)
    if not m:
        return text, 1
    n = int(m.group(1))
    if n < 1:
        return text, 1
    return m.group(2).strip(), n


def parse_rowspan_suffix(text: str) -> tuple[str, int]:
    m = re.fullmatch(r"(.*)@(\d+)@", text, re.DOTALL)
    if not m:
        return text, 1
    n = int(m.group(2))
    if n < 1:
        return text, 1
    return m.group(1).strip(), n


def decode_cell(text: str) -> RawCell:
    body, colspan = parse_colspan_prefix(text)
    body, rowspan = parse_rowspan_suffix(body)
    return RawCell(text=body, colspan=colspan, rowspan=rowspan)


def parse_table_block(content: str) -> list[list[RawCell]] | None:
    lines: list[str] = []
    in_block = False
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("|"):
            in_block = True
            lines.append(trimmed)
        elif in_block:
            break
    if not lines:
        return None

    part_rows = [split_row(line) for line in lines]
    if len(part_rows) >= 2 and is_alignment_row(part_rows[1]):
        part_rows.pop(1)

    return [[decode_cell(c) for c in row] for row in part_rows]


def place_grid(rows: list[list[RawCell]]) -> tuple[list[list[CellExport]], int]:
    occupied: set[tuple[int, int]] = set()
    placed_rows: list[list[CellExport]] = []
    max_width = 0

    for row_index, row in enumerate(rows):
        col = 0
        placed: list[CellExport] = []
        for cell in row:
            while (row_index, col) in occupied:
                col += 1
            placed.append(
                CellExport(
                    text=cell.text,
                    col=col,
                    colspan=cell.colspan,
                    rowspan=cell.rowspan,
                )
            )
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    occupied.add((row_index + dr, col + dc))
            max_width = max(max_width, col + cell.colspan)
            col += cell.colspan
        placed_rows.append(placed)

    return placed_rows, max_width


def reference_export(source: Path) -> dict:
    content = source.read_text(encoding="utf-8")
    raw = parse_table_block(content)
    if raw is None:
        raise ValueError(f"no table in {source}")
    placed, column_count = place_grid(raw)
    rows = []
    for row_index, row in enumerate(placed):
        rows.append(
            {
                "row_index": row_index,
                "cells": [
                    {
                        "text": c.text,
                        "col": c.col,
                        "colspan": c.colspan,
                        "rowspan": c.rowspan,
                    }
                    for c in sorted(row, key=lambda x: x.col)
                ],
            }
        )
    return {
        "export_version": 1,
        "source": str(source).replace("\\", "/"),
        "column_count": column_count,
        "rows": rows,
    }


def html_row_slot_count(row_html: str) -> int:
    return len(re.findall(r"<td\b", row_html))


def parse_html_rows(html: str) -> list[str]:
    return re.findall(r"<tr>\s*(.*?)\s*</tr>", html, re.DOTALL)


def parse_html_td_cells(row_html: str) -> list[dict]:
    """Parse td elements from one HTML row into text and span attributes."""
    cells: list[dict] = []
    for part in re.findall(r"<td([^>]*)>(.*?)</td>", row_html, re.DOTALL):
        attrs, text = part
        colspan = 1
        rowspan = 1
        m = re.search(r'colspan="(\d+)"', attrs)
        if m:
            colspan = int(m.group(1))
        m = re.search(r'rowspan="(\d+)"', attrs)
        if m:
            rowspan = int(m.group(1))
        cells.append({"text": text, "colspan": colspan, "rowspan": rowspan})
    return cells


def reference_html(source: Path) -> str:
    """Build expected HTML from the independent reference grid model."""
    doc = reference_export(source)

    def escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = ["<table>"]
    for row in doc["rows"]:
        lines.append("  <tr>")
        for cell in row["cells"]:
            attrs = ""
            if cell["colspan"] > 1:
                attrs += f' colspan="{cell["colspan"]}"'
            if cell["rowspan"] > 1:
                attrs += f' rowspan="{cell["rowspan"]}"'
            lines.append(f"    <td{attrs}>{escape_html(cell['text'])}</td>")
        lines.append("  </tr>")
    lines.append("</table>")
    return "\n".join(lines) + "\n"


def build_seed_table(seed: str) -> tuple[Path, list[str]]:
    tag = hashlib.sha256(seed.encode()).hexdigest()[:8]
    tmp = Path(tempfile.mkdtemp(prefix=f"mdtable-{tag}-"))
    table = tmp / "seed.md"
    table.write_text(
        "\n".join(
            [
                "| Key | Val |",
                "| --- | --- |",
                f"| >2<{tag} | plain |",
                f"| {tag} | ok |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return table, [str(table)]
